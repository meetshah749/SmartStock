import logging
import re
import statistics
import asyncio
from datetime import datetime, timezone
from typing import Any, Literal

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.market_data import get_market_provider
from app.services.symbol_mapper import INSTRUMENT_CATALOG, SYMBOL_ALIASES
from app.services.stock_universe import INDIAN_EQUITY_UNIVERSE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assistant", tags=["AI Stock Assistant"])

RiskProfile = Literal["conservative", "balanced", "growth"]
InvestmentHorizon = Literal["short", "medium", "long"]


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1000)


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    conversation: list[ConversationTurn] = Field(default_factory=list, max_length=8)
    risk_profile: RiskProfile | None = None
    investment_horizon: InvestmentHorizon | None = None


def _symbols_in_text(text: str) -> list[str]:
    normalized_text = re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()
    matches: list[tuple[int, int, str]] = []
    aliases = dict(SYMBOL_ALIASES)
    aliases.update({info["company_name"].upper(): symbol for symbol, info in INSTRUMENT_CATALOG.items()})

    for alias, canonical in aliases.items():
        if canonical not in INSTRUMENT_CATALOG and canonical not in INDIAN_EQUITY_UNIVERSE:
            continue
        normalized_alias = re.sub(r"[^A-Z0-9]+", " ", alias.upper()).strip()
        if not normalized_alias:
            continue
        pattern = rf"(?<![A-Z0-9]){re.escape(normalized_alias)}(?![A-Z0-9])"
        match = re.search(pattern, normalized_text)
        if match:
            matches.append((match.start(), -(match.end() - match.start()), canonical))

    matches.sort()
    found: list[str] = []
    for _, _, symbol in matches:
        if symbol not in found:
            found.append(symbol)
    return found[:2]


async def _market_call(awaitable, label: str, timeout_seconds: float = 12.0):
    try:
        return await asyncio.wait_for(awaitable, timeout=timeout_seconds)
    except Exception as exc:
        logger.info("Market lookup %s did not complete: %s", label, exc)
        return None


_NON_TICKER_WORDS = {
    "A", "AN", "AND", "ABOUT", "AFTER", "ANALYSE", "ANALYZE", "ARE", "AS", "AT", "BANK", "BETWEEN",
    "BUY", "CAN", "COMPARE", "COMPANY", "COULD", "CURRENT", "DATA", "DETAILS", "DIFFERENCE", "DO", "DOES",
    "EXPLAIN", "FOR", "FROM", "GIVE", "GOOD", "HELP", "HDFC", "HOW", "I", "ICICI", "INFO", "INFORMATION",
    "IS", "IT", "LATEST", "LOOK", "MARKET", "ME", "NEWS", "OF", "ON", "OR", "PLEASE", "PRICE", "PROS",
    "RECOMMEND", "REPORT", "RISK", "RSI", "SEARCH", "SHOULD", "SHOW", "STOCK", "STOCKS", "SUGGEST", "TELL",
    "THE", "THIS", "TO", "TODAY", "WHAT", "WHICH", "WHO", "WHY", "WITH", "WOULD", "YESTERDAY",
}


def _stock_query_parts(message: str) -> list[str]:
    text = message.strip()
    if re.search(r"\b(compare|versus|vs\.?|between)\b", text, re.IGNORECASE):
        parts = re.split(r"\b(?:and|versus|vs\.?|with)\b", text, flags=re.IGNORECASE)
    else:
        parts = [text]

    cleaned: list[str] = []
    for part in parts:
        query = re.sub(
            r"^\s*(?:(?:please\s+)?(?:compare|between|tell\s+me\s+about|what\s+about|what\s+is|who\s+is|show\s+me|give\s+me|find|search(?:\s+for)?|look\s+up|report\s+on|details\s+on|analy[sz]e|review)\s+)+",
            "",
            part,
            flags=re.IGNORECASE,
        )
        query = re.sub(r"\b(?:stock|share|ticker|report|reports|company|details|please|financials?|fundamentals?|quote|price|performance|analysis|overview|news)\b", " ", query, flags=re.IGNORECASE)
        query = re.sub(r"[^A-Za-z0-9.$-]+", " ", query).strip()
        query = re.sub(r"\s+", " ", query)
        if query:
            cleaned.append(query)
    return cleaned[:2]


def _looks_like_stock_lookup(message: str) -> bool:
    if _symbols_in_text(message):
        return True
    if re.search(r"\b(stock|stocks|share|shares|ticker|quote|company|report|reports|compare|versus|\bvs\b|find|market price|price|valuation|fundamentals?|financials?|listed|equity|analy[sz]e|invest|return|earnings|revenue|dividend|volatility|news|outlook)\b|\b(?:tell me about|who is|what about|look up)\b|^\s*(?:please\s+)?search(?:\s+for)?\s+", message, re.IGNORECASE):
        return True
    return len(message.strip().split()) == 1


async def _resolve_stock_symbols(message: str, conversation: list[ConversationTurn]) -> tuple[list[str], bool, list[str]]:
    """Resolve catalog aliases, explicit tickers, or company names via provider search."""
    current_parts = _stock_query_parts(message)
    if not _looks_like_stock_lookup(message):
        return [], False, []

    provider = get_market_provider()
    resolved: list[str] = []

    async def resolve_part(part: str) -> str | None:
        known = _symbols_in_text(part)
        if known:
            return known[0]

        # Explicit all-caps tickers, and a single lower-case ticker typed in isolation.
        raw_candidates = re.findall(r"(?<![A-Za-z0-9])\$?([A-Z][A-Z0-9.-]{0,14})(?![A-Za-z0-9])", part)
        if len(part.split()) == 1 and not raw_candidates:
            raw_candidates = [part.upper()]
        for candidate in raw_candidates:
            candidate = candidate.lstrip("$")
            if candidate in _NON_TICKER_WORDS or len(candidate) < 2:
                continue
            try:
                quote = await _market_call(provider.get_stock_quote(candidate), f"quote {candidate}", 8.0)
            except Exception:
                quote = None
            if quote:
                return str(quote.get("symbol") or candidate).upper()

        search = getattr(provider, "search_stocks", None)
        if callable(search) and part:
            try:
                results = await _market_call(search(part), f"search {part}", 10.0)
                if results:
                    return str(results[0].get("symbol") or "").upper() or None
            except Exception as exc:
                logger.info("Stock search did not resolve %r: %s", part, exc)
        return None

    unresolved: list[str] = []
    for part in current_parts:
        symbol = await resolve_part(part)
        if symbol and symbol not in resolved:
            resolved.append(symbol)
        elif not symbol:
            unresolved.append(part)
        if len(resolved) == 2:
            break

    if resolved:
        return resolved, True, unresolved

    # Keep context for follow-ups such as "what about the annual return?" by
    # reusing only the latest user's symbols, never symbols echoed by the bot.
    for turn in reversed(conversation):
        if turn.role != "user":
            continue
        prior_symbols = _symbols_in_text(turn.content)
        if prior_symbols:
            return prior_symbols, True, unresolved
        prior_parts = _stock_query_parts(turn.content)
        if prior_parts and _looks_like_stock_lookup(turn.content):
            for part in prior_parts:
                symbol = await resolve_part(part)
                if symbol and symbol not in resolved:
                    resolved.append(symbol)
            if resolved:
                return resolved, True, unresolved
        break
    return [], True, unresolved


async def _get_stock_snapshot(symbol: str, include_fundamentals: bool = True) -> dict[str, Any] | None:
    provider = get_market_provider()
    fundamentals_method = getattr(provider, "get_fundamental_data", None)
    quote, company, bars, annual_bars = await asyncio.gather(
        _market_call(provider.get_stock_quote(symbol), f"quote {symbol}"),
        _market_call(provider.get_company_info(symbol), f"company {symbol}"),
        _market_call(provider.get_historical_prices(symbol, timeframe="1M"), f"1M history {symbol}"),
        _market_call(provider.get_historical_prices(symbol, timeframe="1Y"), f"1Y history {symbol}"),
    )
    if not quote:
        return None

    bars = bars or []
    annual_bars = annual_bars or []

    price = float(quote.get("price") or 0)
    ordered_bars = sorted(bars or [], key=lambda bar: str(bar.get("timestamp", "")))
    closes = [float(bar["close"]) for bar in ordered_bars if bar.get("close") is not None]
    annual_closes = [
        float(bar["close"])
        for bar in sorted(annual_bars or [], key=lambda bar: str(bar.get("timestamp", "")))
        if bar.get("close") is not None
    ]
    returns = [
        (closes[index] / closes[index - 1] - 1) * 100
        for index in range(1, len(closes))
        if closes[index - 1]
    ]
    one_month_change = ((closes[-1] / closes[0]) - 1) * 100 if len(closes) > 1 and closes[0] else None
    daily_volatility = statistics.pstdev(returns) if len(returns) > 1 else None
    recent_closes = closes[-15:]
    gains = [max(recent_closes[index] - recent_closes[index - 1], 0.0) for index in range(1, len(recent_closes))]
    losses = [max(recent_closes[index - 1] - recent_closes[index], 0.0) for index in range(1, len(recent_closes))]
    average_gain = sum(gains) / len(gains) if gains else 0.0
    average_loss = sum(losses) / len(losses) if losses else 0.0
    rsi_14 = (
        100.0 if average_loss == 0 and average_gain > 0
        else 50.0 if average_loss == 0
        else round(100 - (100 / (1 + average_gain / average_loss)), 2)
    )
    sma20 = round(sum(annual_closes[-20:]) / 20, 2) if len(annual_closes) >= 20 else None
    sma50 = round(sum(annual_closes[-50:]) / 50, 2) if len(annual_closes) >= 50 else None
    info = company or {}
    fundamentals = None
    if include_fundamentals and callable(fundamentals_method):
        try:
            fundamentals = await asyncio.wait_for(fundamentals_method(symbol), timeout=8)
        except Exception as exc:
            logger.info("Optional fundamentals lookup unavailable for %s: %s", symbol, exc)
    if daily_volatility is None:
        volatility_band = "not enough recent history"
    elif daily_volatility < 1:
        volatility_band = "lower observed volatility"
    elif daily_volatility < 2.5:
        volatility_band = "moderate observed volatility"
    else:
        volatility_band = "higher observed volatility"

    return {
        "symbol": symbol,
        "company_name": info.get("company_name", symbol),
        "sector": info.get("sector", "Unknown"),
        "industry": info.get("industry"),
        "description": info.get("description"),
        "fundamentals": fundamentals,
        "exchange": info.get("exchange"),
        "price": price,
        "currency": quote.get("currency", "INR"),
        "change_percent": float(quote.get("change_percent") or 0),
        "open": quote.get("open"),
        "high": quote.get("high"),
        "low": quote.get("low"),
        "prev_close": quote.get("prev_close"),
        "volume": quote.get("volume"),
        "market_status": quote.get("market_status"),
        "rsi_14": rsi_14 if len(closes) >= 15 else None,
        "sma20": sma20,
        "sma50": sma50,
        "data_status": quote.get("data_status", "UNKNOWN"),
        "source": quote.get("source", "Market data provider"),
        "timestamp": quote.get("timestamp"),
        "one_month_change_percent": round(one_month_change, 2) if one_month_change is not None else None,
        "one_year_change_percent": (
            round(((annual_closes[-1] / annual_closes[0]) - 1) * 100, 2)
            if len(annual_closes) > 1 and annual_closes[0] else None
        ),
        "observed_one_year_high": round(max(annual_closes), 2) if annual_closes else None,
        "observed_one_year_low": round(min(annual_closes), 2) if annual_closes else None,
        "annual_history_points": len(annual_closes),
        "daily_volatility_percent": round(daily_volatility, 2) if daily_volatility is not None else None,
        "volatility_band": volatility_band,
        "history_points": len(closes),
    }


def _build_comparison(snapshots: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(snapshots) != 2:
        return None
    first, second = snapshots
    performance = [item for item in (first, second) if item["one_month_change_percent"] is not None]
    annual_performance = [item for item in (first, second) if item["one_year_change_percent"] is not None]
    less_volatile = [item for item in (first, second) if item["daily_volatility_percent"] is not None]
    comparable_currency = first["currency"] == second["currency"]
    return {
        "symbols": [first["symbol"], second["symbol"]],
        "period": "1 month of available daily history",
        "currency_comparable": comparable_currency,
        "one_month_performance_leader": (
            max(performance, key=lambda item: item["one_month_change_percent"])["symbol"]
            if len(performance) == 2 else None
        ),
        "one_year_performance_leader": (
            max(annual_performance, key=lambda item: item["one_year_change_percent"])["symbol"]
            if len(annual_performance) == 2 else None
        ),
        "lower_observed_volatility": (
            min(less_volatile, key=lambda item: item["daily_volatility_percent"])["symbol"]
            if len(less_volatile) == 2 else None
        ),
        "price_difference": round(abs(first["price"] - second["price"]), 2) if comparable_currency else None,
        "note": "These are separate historical measures, not a personalized suitability or buy recommendation. Past performance and lower observed volatility do not guarantee future results.",
    }


def _risk_guidance(profile: RiskProfile | None, horizon: InvestmentHorizon | None) -> str:
    if profile is None:
        return "No risk profile was selected. Ask the user to choose conservative, balanced, or growth and share their time horizon before tailoring the educational discussion."

    profile_copy = {
        "conservative": "The user selected conservative. Emphasize capital preservation, diversification, lower observed volatility, and the possibility that shares can still lose value.",
        "balanced": "The user selected balanced. Explain the trade-off between growth and drawdowns, diversification, and reviewing both business and market risks.",
        "growth": "The user selected growth. Acknowledge a greater stated tolerance for swings, while highlighting concentration, liquidity, and loss risks; do not equate risk tolerance with ability to absorb losses.",
    }[profile]
    horizon_copy = {
        "short": "Their selected horizon is under one year; emphasize that stocks can be unsuitable for money needed soon.",
        "medium": "Their selected horizon is one to five years; explain that the horizon does not eliminate drawdown risk.",
        "long": "Their selected horizon is over five years; explain that longer horizons do not guarantee gains and diversification still matters.",
    }.get(horizon, "No investment horizon was provided; do not assume one.")
    return f"{profile_copy} {horizon_copy} This is self-reported context, not a suitability assessment."


def _is_recommendation_request(message: str) -> bool:
    lowered = message.lower()
    return any(term in lowered for term in ("recommend", "suggest", "which stock", "what should i buy", "stocks for me"))


async def _build_risk_watchlist(profile: RiskProfile) -> list[dict[str, Any]]:
    """Build research candidates ranked only by recent realized volatility and sector variety."""
    symbols = list(INSTRUMENT_CATALOG.keys())
    snapshots = await asyncio.gather(*(_get_stock_snapshot(symbol, include_fundamentals=False) for symbol in symbols))
    available = [item for item in snapshots if item and item["daily_volatility_percent"] is not None]
    available.sort(key=lambda item: item["daily_volatility_percent"])

    if profile == "growth":
        ranked = list(reversed(available))
    elif profile == "balanced" and available:
        median_vol = statistics.median(item["daily_volatility_percent"] for item in available)
        ranked = sorted(available, key=lambda item: abs(item["daily_volatility_percent"] - median_vol))
    else:
        ranked = available

    candidates: list[dict[str, Any]] = []
    seen_sectors: set[str] = set()
    for item in ranked:
        if item["sector"] in seen_sectors:
            continue
        candidates.append(item)
        seen_sectors.add(item["sector"])
        if len(candidates) == 3:
            break
    return candidates


def _market_context(snapshots: list[dict[str, Any]]) -> str:
    if not snapshots:
        return "No stock-specific market data could be identified from this message. Do not invent prices, company facts, or performance."
    return "Verified market-data snapshots (cite the source/status and timestamp when useful):\n" + "\n".join(
        f"- {item['symbol']} / {item['company_name']}, sector {item['sector']}: "
        f"{item['currency']} {item['price']:.2f}, today's change {item['change_percent']:+.2f}%, "
        f"exchange {item['exchange']}, industry {item['industry']}, company description {item['description']}, "
        f"vendor-reported fundamentals {item.get('fundamentals')}, "
        f"RSI-14 {item['rsi_14']}, SMA-20 {item['sma20']}, SMA-50 {item['sma50']}, "
        f"one-month change {item['one_month_change_percent']}%, one-year change {item['one_year_change_percent']}%, "
        f"observed one-year high/low {item['observed_one_year_high']}/{item['observed_one_year_low']}, "
        f"open/high/low/previous close {item['open']}/{item['high']}/{item['low']}/{item['prev_close']}, "
        f"volume {item['volume']}, recent daily volatility "
        f"{item['daily_volatility_percent']}% ({item['volatility_band']}), "
        f"data status {item['data_status']}, source {item['source']}, timestamp {item['timestamp']}."
        for item in snapshots
    )


def _fallback_reply(message: str, profile: RiskProfile | None, horizon: InvestmentHorizon | None, snapshots: list[dict[str, Any]]) -> str:
    risk = {
        "conservative": "Since you selected conservative, pay particular attention to drawdowns, diversification, and whether you may need the money soon. A lower observed volatility is not a guarantee of lower future risk.",
        "balanced": "Since you selected balanced, compare both the potential for growth and the size of losses you could tolerate. Diversification and time horizon matter alongside a stock's recent trend.",
        "growth": "Since you selected growth, remember that accepting more price swings does not mean you can afford every loss. Avoid concentrating money you need for essential expenses.",
    }.get(profile, "Set a risk profile above if you want the discussion framed around conservative, balanced, or growth preferences.")
    horizon_text = {
        "short": " Your selected short horizon also means money needed within a year may not belong in volatile shares.",
        "medium": " Your selected medium horizon does not prevent short-term losses.",
        "long": " Your selected long horizon does not guarantee a positive return.",
    }.get(horizon, "")

    if len(snapshots) >= 3 and _is_recommendation_request(message) and profile:
        candidates = ", ".join(
            f"{item['symbol']} ({item['volatility_band']}, {item['daily_volatility_percent']:.2f}% recent daily volatility)"
            for item in snapshots
        )
        risk_label = {"conservative": "lower", "balanced": "middle-range", "growth": "higher"}[profile]
        return (
            f"I screened the supported-stock catalog for a small research watchlist with {risk_label} recent volatility "
            f"and different sectors: {candidates}. This is a volatility-based starting point only—not a suitability ranking or buy recommendation. "
            f"{risk}{horizon_text} Compare each company's fundamentals, valuation, and business risks before making any decision."
        )

    if len(snapshots) == 2:
        first, second = snapshots
        comparable = first["one_month_change_percent"] is not None and second["one_month_change_percent"] is not None
        performance = (
            f"Over the available one-month history, {first['symbol']} changed {first['one_month_change_percent']:+.2f}% and "
            f"{second['symbol']} changed {second['one_month_change_percent']:+.2f}%. "
            if comparable
            else "There is not enough recent history to compare their one-month performance reliably. "
        )
        risk_line = (
            f"Observed volatility was {first['volatility_band']} for {first['symbol']} and "
            f"{second['volatility_band']} for {second['symbol']}. "
        )
        annual_performance = (
            f"One-year history: {first['symbol']} {first['one_year_change_percent']:+.2f}% vs "
            f"{second['symbol']} {second['one_year_change_percent']:+.2f}%. "
            if first["one_year_change_percent"] is not None and second["one_year_change_percent"] is not None
            else "One-year comparison is unavailable from the current history feed. "
        )
        comparison_note = (
            f"By one-month return alone, {max((first, second), key=lambda item: item['one_month_change_percent'])['symbol']} had the stronger observed month; "
            f"{min((first, second), key=lambda item: item['daily_volatility_percent'] if item['daily_volatility_percent'] is not None else float('inf'))['symbol']} had lower observed daily volatility. "
            if first["one_month_change_percent"] is not None and second["one_month_change_percent"] is not None
            and first["daily_volatility_percent"] is not None and second["daily_volatility_percent"] is not None
            else "The available history is incomplete for a complete relative comparison. "
        )
        return (
            f"Here is a data-based snapshot of {first['symbol']} and {second['symbol']}. "
            f"Current quotes: {first['symbol']} {first['currency']} {first['price']:.2f} "
            f"({first['change_percent']:+.2f}% today); {second['symbol']} {second['currency']} {second['price']:.2f} "
            f"({second['change_percent']:+.2f}% today). {performance}{annual_performance}{risk_line}{comparison_note}{risk}{horizon_text} "
            "This is a comparison of recent market data, not a buy instruction or personalized financial advice. "
            "For a fuller comparison, ask about business fundamentals, valuation, or a specific risk."
        )
    if len(snapshots) == 1:
        stock = snapshots[0]
        one_month = (
            f" Its one-month price change was {stock['one_month_change_percent']:+.2f}%."
            if stock["one_month_change_percent"] is not None
            else " I could not calculate a one-month return from the available history."
        )
        one_year = (
            f" One-year change: {stock['one_year_change_percent']:+.2f}%; observed one-year close range: "
            f"{stock['observed_one_year_low']:.2f}–{stock['observed_one_year_high']:.2f}."
            if stock.get("one_year_change_percent") is not None
            and stock.get("observed_one_year_low") is not None
            and stock.get("observed_one_year_high") is not None
            else " One-year performance/range is unavailable from the current history feed."
        )
        day_range = (
            f" Day range: {stock['low']:.2f}–{stock['high']:.2f}; open {stock['open']:.2f}; "
            f"previous close {stock['prev_close']:.2f}; volume {stock['volume']:,}."
            if all(stock.get(key) is not None for key in ("low", "high", "open", "prev_close", "volume"))
            else " Some intraday quote details are not available."
        )
        indicator_values = []
        if stock.get("rsi_14") is not None:
            indicator_values.append(f"RSI-14 {stock['rsi_14']:.1f}")
        if stock.get("sma20") is not None:
            indicator_values.append(f"SMA-20 {stock['sma20']:.2f}")
        if stock.get("sma50") is not None:
            indicator_values.append(f"SMA-50 {stock['sma50']:.2f}")
        if stock.get("daily_volatility_percent") is not None:
            indicator_values.append(f"observed daily volatility {stock['daily_volatility_percent']:.2f}%")
        technicals = (
            f" Technical overview from available daily history: {', '.join(indicator_values)}."
            if indicator_values
            else " There are not enough recent candles for technical measures."
        )
        fundamental_metrics = (stock.get("fundamentals") or {}).get("metrics", {})
        fundamental_labels = {
            "market_cap": "market cap",
            "trailing_pe": "trailing P/E",
            "forward_pe": "forward P/E",
            "earnings_per_share": "EPS",
            "book_value_per_share": "book value/share",
            "price_to_book": "price/book",
            "dividend_yield": "dividend yield",
            "beta": "beta",
            "revenue": "revenue",
            "revenue_growth": "revenue growth",
            "net_income": "net income",
            "profit_margin": "profit margin",
            "debt_to_equity": "debt/equity",
            "return_on_equity": "return on equity",
        }
        formatted_metrics = []
        for key, label in fundamental_labels.items():
            value = fundamental_metrics.get(key)
            if value is None:
                continue
            if key in {"dividend_yield", "revenue_growth", "profit_margin", "return_on_equity"}:
                formatted_value = f"{float(value) * 100:.2f}%"
            elif key in {"market_cap", "revenue", "net_income"}:
                formatted_value = f"{stock['currency']} {float(value):,.0f}"
            else:
                formatted_value = f"{float(value):.2f}"
            formatted_metrics.append(f"{label}: {formatted_value}")
        fundamentals_text = (
            f" Vendor-reported fundamentals ({stock['fundamentals']['source']}): "
            f"{'; '.join(formatted_metrics)}. Retrieved {stock['fundamentals']['retrieved_at']}."
            if formatted_metrics and stock.get("fundamentals") else
            " Vendor fundamentals were not returned by the current market-data provider."
        )
        return (
            f"{stock['company_name']} ({stock['symbol']}) is listed on {stock['exchange']} in {stock['sector']} "
            f"({stock['industry']}). {stock['description']} The latest quote is "
            f"{stock['currency']} {stock['price']:.2f}, {stock['change_percent']:+.2f}% today "
            f"(market status: {stock['market_status']}; data status: {stock['data_status']}; source: {stock['source']}; "
            f"timestamp: {stock['timestamp']}).{day_range}{one_month}{one_year}{technicals}{fundamentals_text} "
            f"Recent volatility is {stock['volatility_band']}. {risk}{horizon_text} "
            "Historical performance and indicators do not predict future returns. Company profile is catalog information; fundamentals are vendor-reported and can be incomplete or stale. Current news is not included unless separately sourced."
        )

    lowered = message.lower()
    if _looks_like_stock_lookup(message) and not snapshots:
        return (
            "I couldn't verify that stock from the connected market-data provider, so I won't make up a quote or report. "
            "Try its exact exchange ticker (for example NVDA, RELIANCE.NS, or a Yahoo Finance symbol), or search the company name in Explore Stocks. "
            "Coverage varies by exchange and data provider."
        )
    if _is_recommendation_request(message) or "buy" in lowered:
        if profile is None:
            return "I can build a small research watchlist from the supported stocks using recent volatility, but first select a risk lens above (conservative, balanced, or growth) and optionally a time horizon. This is not a personal suitability assessment."
        return (
            "I can build a research watchlist from supported stocks using recent volatility and sector variety, but that is not a personal suitability assessment. "
            "Tell me one or two ticker symbols if you want a direct comparison, and share your time horizon and the risks you want to understand. "
            f"{risk}{horizon_text} Consider diversified investments and independent research; this assistant is educational, not a personal financial adviser."
        )
    if any(term in lowered for term in ("compare", "versus", " vs ", " vs.", "difference")):
        return "Which two ticker symbols would you like to compare? I can summarize available live quotes, recent performance, and observed volatility without treating that as a guaranteed forecast."
    if "rsi" in lowered:
        return "RSI (Relative Strength Index) is a momentum indicator that ranges from 0 to 100. Traders often watch readings near 30 or 70, but RSI can remain extreme in a strong trend and should not be used alone as a buy or sell signal."
    if "diversif" in lowered:
        return "Diversification spreads exposure across companies, sectors, or asset types so one holding has less influence on the overall portfolio. It can reduce concentration risk but cannot eliminate market losses."
    return (
        "I can explain stock-market terms, read an available quote, summarize recent price movement, or compare two supported tickers. "
        "Try asking ‘Explain RSI’, ‘What are the risks of TCS?’, or ‘Compare RELIANCE and TCS’. "
        f"{risk}{horizon_text}"
    )


async def _ask_configured_model(
    message: str,
    conversation: list[ConversationTurn],
    risk_profile: RiskProfile | None,
    horizon: InvestmentHorizon | None,
    snapshots: list[dict[str, Any]],
    comparison: dict[str, Any] | None,
) -> str | None:
    if not settings.AI_API_KEY:
        return None

    system_prompt = (
        "You are SmartStock AI, a capable, friendly general-purpose conversational assistant embedded in a stock-market education app. "
        "Answer the user's actual question across ordinary topics, explanations, writing, reasoning, and programming; do not reject a question merely because it is not about finance. "
        "Be clear about uncertainty and knowledge limits. You have no web-browsing tool: never claim to have checked the web or present changing facts as current unless they appear in the verified snapshots below. "
        "For stock questions, use the supplied app/company/quote/history context and cite its source/status when relevant; never invent current prices, financial statements, news, or company facts. "
        "If three or more snapshots are supplied for a risk-profile request, they are research candidates screened only by recent volatility and sector variety; describe them as a watchlist, never as personally suitable stocks. "
        "Treat a self-reported risk profile and horizon only as discussion context, not a suitability assessment. Never promise returns, give urgent buy/sell instructions, or claim that a stock is suitable for the user. "
        "Explain that technical indicators describe historical prices, not future results. For medical, legal, financial, or safety-critical questions, be careful and encourage qualified professional help where appropriate. "
        "Keep answers conversational and proportionate to the question; use helpful structure where useful, and do not output markdown tables.\n\n"
        f"Self-reported risk context: {_risk_guidance(risk_profile, horizon)}\n\n"
        f"{_market_context(snapshots)}\n\n"
        f"Computed side-by-side comparison (describe only the measured differences; do not call either stock the best buy): {comparison}"
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend({"role": turn.role, "content": turn.content} for turn in conversation[-8:])
    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(
                f"{settings.AI_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
                json={"model": settings.AI_MODEL, "messages": messages, "temperature": 0.3, "max_tokens": 450},
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
            return answer.strip() if isinstance(answer, str) and answer.strip() else None
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning("Configured assistant model request failed: %s", exc)
        return None


@router.post("/chat")
async def chat_with_assistant(payload: AssistantChatRequest) -> dict[str, Any]:
    """Answer general questions and ground supported-stock questions in available quote data."""
    symbols, stock_lookup_requested, unresolved_stocks = await _resolve_stock_symbols(payload.message, payload.conversation)
    try:
        if symbols:
            snapshot_results = await asyncio.gather(
                *(_get_stock_snapshot(symbol) for symbol in symbols),
                return_exceptions=True,
            )
            snapshots = [
                item for item in snapshot_results
                if isinstance(item, dict)
            ]
        elif payload.risk_profile and _is_recommendation_request(payload.message):
            snapshots = await _build_risk_watchlist(payload.risk_profile)
        else:
            snapshots = []
    except Exception as exc:
        logger.warning("Could not fetch stock context for assistant: %s", exc)
        snapshots = []

    comparison = _build_comparison(snapshots)
    available_symbols = {str(item.get("symbol", "")).upper() for item in snapshots}
    unavailable_stocks = [symbol for symbol in symbols if symbol.upper() not in available_symbols]
    answer = await _ask_configured_model(
        payload.message,
        payload.conversation,
        payload.risk_profile,
        payload.investment_horizon,
        snapshots,
        comparison,
    )
    mode = "llm" if answer else "market-aware"
    if not answer:
        answer = _fallback_reply(payload.message, payload.risk_profile, payload.investment_horizon, snapshots)
    if stock_lookup_requested and not snapshots:
        answer = _fallback_reply(payload.message, payload.risk_profile, payload.investment_horizon, snapshots)
    elif unresolved_stocks:
        missing = ", ".join(unresolved_stocks)
        answer += f" I could not verify {missing} with the current market-data provider, so its comparison data is unavailable. Check the exact company name or exchange ticker."
    if unavailable_stocks and snapshots:
        missing = ", ".join(unavailable_stocks)
        answer += f" I could not retrieve a current quote for {missing} from the connected provider, so I have not included it in the comparison."
    return {
        "reply": answer,
        "mode": mode,
        "llm_configured": bool(settings.AI_API_KEY),
        "stocks": snapshots,
        "stock_lookup_requested": stock_lookup_requested,
        "unresolved_stocks": unresolved_stocks,
        "unavailable_stocks": unavailable_stocks,
        "comparison": comparison,
        "risk_profile": payload.risk_profile,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Educational market information only—not personalized financial advice. Quotes may be delayed; stocks can lose value.",
    }

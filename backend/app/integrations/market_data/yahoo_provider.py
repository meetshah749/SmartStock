import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import yfinance as yf

from app.core.config import settings
from app.integrations.market_data.base import BaseMarketDataProvider
from app.services.market_status import format_ist_timestamp, get_ist_now, get_market_status
from app.services.symbol_mapper import INDICES_CATALOG, INSTRUMENT_CATALOG, normalize_symbol
from app.services.stock_universe import INDIAN_EQUITY_UNIVERSE

logger = logging.getLogger(__name__)


class YahooFinanceProvider(BaseMarketDataProvider):
    """Live public market-data provider backed by Yahoo Finance."""

    def is_live_provider(self) -> bool:
        return True

    def provider_name(self) -> str:
        return "Yahoo Finance"

    def provider_status(self) -> str:
        return "LIVE"

    def get_latest_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def map_symbol(symbol: str) -> str:
        raw = symbol.strip().upper()
        if raw.endswith((".NS", ".BO")) or raw.startswith("^"):
            return raw
        canonical = normalize_symbol(symbol)
        if canonical in INSTRUMENT_CATALOG:
            return f"{canonical}.NS"
        if canonical in INDIAN_EQUITY_UNIVERSE:
            return f"{canonical}.NS"
        if canonical == "NIFTY50":
            return "^NSEI"
        if canonical == "SENSEX":
            return "^BSESN"
        if canonical == "BANKNIFTY":
            return "^NSEBANK"
        return canonical.upper()

    @staticmethod
    def _coerce_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    async def _fetch_ticker(self, symbol: str):
        return await asyncio.to_thread(yf.Ticker, symbol)

    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        norm = normalize_symbol(query)
        q_lower = query.lower().strip()
        if norm.endswith((".NS", ".BO")):
            quote = await self.get_stock_quote(norm)
            return [quote] if quote else []

        candidates: dict[str, tuple[int, str]] = {}
        directory = {**INDIAN_EQUITY_UNIVERSE, **INSTRUMENT_CATALOG}
        for symbol, info in directory.items():
            symbol_lower = symbol.lower()
            company_lower = info["company_name"].lower()
            if q_lower == symbol_lower or norm.upper() == symbol:
                score = 0
            elif symbol_lower.startswith(q_lower) and len(q_lower) >= 2:
                score = 1
            elif company_lower.startswith(q_lower):
                score = 2
            elif len(q_lower) >= 2 and (q_lower in symbol_lower or q_lower in company_lower):
                score = 3
            elif len(q_lower) >= 3 and q_lower in info.get("sector", "").lower():
                score = 4
            else:
                continue
            candidates[symbol] = (score, symbol)

        if candidates:
            selected = [symbol for _, symbol in sorted(candidates.values())[:10]]
            semaphore = asyncio.Semaphore(8)

            async def fetch_quote(symbol: str):
                async with semaphore:
                    return await self.get_stock_quote(symbol)

            quotes = await asyncio.gather(*(fetch_quote(symbol) for symbol in selected), return_exceptions=True)
            matches = [item for item in quotes if isinstance(item, dict)]
            if matches:
                return matches

        # Resolve stocks beyond the small local Indian-equity catalog using Yahoo's
        # search index. This returns exchange-qualified symbols and avoids guessing
        # a ticker from a company name.
        try:
            search = await asyncio.to_thread(lambda: yf.Search(query, max_results=8, news_count=0))
            candidates = getattr(search, "quotes", None) or []
            for item in candidates:
                if item.get("quoteType") not in (None, "EQUITY", "ETF"):
                    continue
                symbol = item.get("symbol")
                if not symbol:
                    continue
                quote = await self.get_stock_quote(symbol)
                if quote:
                    quote["company_name"] = item.get("longname") or item.get("shortname") or quote["company_name"]
                    matches.append(quote)
                if len(matches) >= 5:
                    break
        except Exception as exc:
            logger.warning("Yahoo Finance stock search failed for %r: %s", query, exc)

        return matches

    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        canonical = normalize_symbol(symbol)
        yf_symbol = self.map_symbol(canonical)
        ticker = await self._fetch_ticker(yf_symbol)

        try:
            info = await asyncio.to_thread(lambda: ticker.fast_info)
            if not info:
                info = await asyncio.to_thread(lambda: ticker.info)
            if not info:
                return None

            company = INSTRUMENT_CATALOG.get(canonical) or INDIAN_EQUITY_UNIVERSE.get(canonical, {})
            metadata: Dict[str, Any] = {}
            if not company:
                try:
                    metadata = await asyncio.to_thread(lambda: ticker.info)
                except Exception:
                    metadata = {}
            combined = {**metadata, **dict(info)}

            price = (
                combined.get("lastPrice")
                or combined.get("regularMarketPrice")
                or combined.get("currentPrice")
                or combined.get("price")
            )
            prev_close = (
                combined.get("regularMarketPreviousClose")
                or combined.get("previousClose")
                or price
            )
            if price is None:
                return None

            current_price = self._coerce_float(price)
            previous_close = self._coerce_float(prev_close, current_price)
            change = round(current_price - previous_close, 2)
            change_pct = round((change / previous_close) * 100, 2) if previous_close else 0.0

            market_info = get_market_status(provider_is_live=True, provider_name="Yahoo Finance")
            now_ist = get_ist_now()
            company_name = (
                company.get("company_name")
                or combined.get("longName")
                or combined.get("shortName")
                or canonical
            )
            return {
                "symbol": canonical,
                "company_name": company_name,
                "exchange": (
                    "NSE" if yf_symbol.endswith(".NS")
                    else "BSE" if yf_symbol.endswith(".BO")
                    else company.get("exchange") or combined.get("exchange") or combined.get("fullExchangeName") or "Unknown"
                ),
                "sector": company.get("sector") or combined.get("sector") or "Unknown",
                "price": current_price,
                "currency": company.get("currency") or combined.get("currency") or "USD",
                "change": change,
                "change_percent": change_pct,
                "open": self._coerce_float(combined.get("open", combined.get("regularMarketOpen", current_price))),
                "high": self._coerce_float(combined.get("dayHigh", combined.get("regularMarketDayHigh", current_price))),
                "low": self._coerce_float(combined.get("dayLow", combined.get("regularMarketDayLow", current_price))),
                "prev_close": previous_close,
                "high_52w": self._coerce_float(company.get("high_52w") or combined.get("fiftyTwoWeekHigh") or current_price),
                "low_52w": self._coerce_float(company.get("low_52w") or combined.get("fiftyTwoWeekLow") or current_price),
                "volume": int(combined.get("lastVolume") or combined.get("regularMarketVolume") or 0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "time_formatted": format_ist_timestamp(now_ist),
                "source": "Yahoo Finance",
                "market_status": market_info["market_status"],
                "data_status": "LIVE",
                "is_live": True,
            }
        except Exception as exc:
            logger.warning("Yahoo Finance quote fetch failed for %s: %s", yf_symbol, exc)
            return None

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        return await self.get_stock_quote(symbol)

    async def get_historical_prices(
        self, symbol: str, timeframe: str = "1D", **kwargs
    ) -> List[Dict[str, Any]]:
        canonical = normalize_symbol(symbol)
        yf_symbol = self.map_symbol(canonical)
        ticker = await self._fetch_ticker(yf_symbol)

        mapping = {
            "1D": ("5d", "1m"),
            "1W": ("5d", "15m"),
            "1M": ("1mo", "1d"),
            "3M": ("3mo", "1d"),
            "6M": ("6mo", "1d"),
            "1Y": ("1y", "1d"),
            "5Y": ("5y", "1wk"),
        }
        period, interval = mapping.get(timeframe.upper(), ("1mo", "1d"))
        start = kwargs.get("start")
        end = kwargs.get("end")

        try:
            if start is not None and end is not None:
                # Date-bounded daily history is used by backtests. Yahoo's `end`
                # is exclusive; callers should pass the day after the requested end.
                hist = await asyncio.to_thread(
                    lambda: ticker.history(start=start, end=end, interval="1d", auto_adjust=True)
                )
            else:
                hist = await asyncio.to_thread(lambda: ticker.history(period=period, interval=interval))
            if hist is None or hist.empty:
                return []

            bars: List[Dict[str, Any]] = []
            frame = hist.reset_index()
            for _, row in frame.iterrows():
                timestamp = row.iloc[0]
                bars.append({
                    "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp),
                    "time_label": timestamp.strftime("%Y-%m-%d %H:%M") if hasattr(timestamp, "strftime") else str(timestamp),
                    "open": float(row.get("Open", 0.0) or 0.0),
                    "high": float(row.get("High", 0.0) or 0.0),
                    "low": float(row.get("Low", 0.0) or 0.0),
                    "close": float(row.get("Close", 0.0) or 0.0),
                    "volume": int(row.get("Volume", 0) or 0),
                    "data_status": "LIVE",
                    "source": "Yahoo Finance",
                })
            return list(reversed(bars))
        except Exception as exc:
            logger.warning("Yahoo Finance historical fetch failed for %s: %s", yf_symbol, exc)
            return []

    async def get_market_indices(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        for symbol, info in INDICES_CATALOG.items():
            yf_symbol = self.map_symbol(symbol)
            ticker = await self._fetch_ticker(yf_symbol)
            try:
                fast = await asyncio.to_thread(lambda: ticker.fast_info)
                if not fast:
                    fast = await asyncio.to_thread(lambda: ticker.info)
                if not fast:
                    continue

                price = fast.get("lastPrice") or fast.get("regularMarketPrice") or fast.get("currentPrice") or info["price"]
                prev_close = fast.get("regularMarketPreviousClose") or fast.get("previousClose") or info["prev_close"]
                change = round(float(price) - float(prev_close), 2)
                change_pct = round((change / float(prev_close)) * 100, 2) if prev_close else 0.0

                results.append({
                    "symbol": symbol,
                    "name": info["canonical_name"],
                    "exchange": info["exchange"],
                    "price": float(price),
                    "change": change,
                    "change_percent": change_pct,
                    "currency": info["currency"],
                    "data_status": "LIVE",
                    "source": "Yahoo Finance",
                })
            except Exception as exc:
                logger.warning("Yahoo Finance index fetch failed for %s: %s", yf_symbol, exc)

        return results

    async def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        canonical = normalize_symbol(symbol)
        info = INSTRUMENT_CATALOG.get(canonical) or INDIAN_EQUITY_UNIVERSE.get(canonical)
        if info:
            return {
                "symbol": info.get("symbol", canonical),
                "company_name": info.get("company_name", canonical),
                "exchange": info.get("exchange", "NSE"),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry"),
                "isin": info.get("isin"),
                "currency": info.get("currency", "INR"),
                "high_52w": info.get("high_52w"),
                "low_52w": info.get("low_52w"),
                "description": info.get("description"),
                "source": info.get("source", "SmartStock company directory"),
            }

        ticker = await self._fetch_ticker(self.map_symbol(canonical))
        try:
            vendor = await asyncio.to_thread(lambda: ticker.info)
        except Exception as exc:
            logger.info("Yahoo Finance company details unavailable for %s: %s", canonical, exc)
            return None
        if not vendor or not (vendor.get("longName") or vendor.get("shortName")):
            return None
        return {
            "symbol": canonical,
            "company_name": vendor.get("longName") or vendor.get("shortName") or canonical,
            "exchange": vendor.get("fullExchangeName") or vendor.get("exchange"),
            "sector": vendor.get("sector"),
            "industry": vendor.get("industry"),
            "currency": vendor.get("currency"),
            "description": vendor.get("longBusinessSummary"),
            "website": vendor.get("website"),
            "source": "Yahoo Finance",
        }

    async def get_fundamental_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return vendor-reported fundamental metrics when Yahoo makes them available."""
        canonical = normalize_symbol(symbol)
        ticker = await self._fetch_ticker(self.map_symbol(canonical))
        try:
            info = await asyncio.to_thread(lambda: ticker.info)
        except Exception as exc:
            logger.warning("Yahoo Finance fundamentals unavailable for %s: %s", canonical, exc)
            return None

        fields = {
            "market_cap": "marketCap",
            "trailing_pe": "trailingPE",
            "forward_pe": "forwardPE",
            "earnings_per_share": "trailingEps",
            "book_value_per_share": "bookValue",
            "price_to_book": "priceToBook",
            "dividend_yield": "dividendYield",
            "beta": "beta",
            "revenue": "totalRevenue",
            "revenue_growth": "revenueGrowth",
            "net_income": "netIncomeToCommon",
            "profit_margin": "profitMargins",
            "debt_to_equity": "debtToEquity",
            "return_on_equity": "returnOnEquity",
        }
        metrics: Dict[str, Any] = {
            key: info.get(vendor_key)
            for key, vendor_key in fields.items()
            if info.get(vendor_key) is not None
        }
        # Yahoo's dividendYield may arrive as a fraction (0.0183) or percentage
        # points (1.83, and sometimes 0.42). Normalize common percent-point
        # payloads; exclude implausible yield values from reports.
        if metrics.get("dividend_yield") is not None and metrics["dividend_yield"] > 0.1:
            metrics["dividend_yield"] = metrics["dividend_yield"] / 100
        if metrics.get("dividend_yield") is not None and not 0 <= metrics["dividend_yield"] <= 1:
            metrics.pop("dividend_yield")
        if not metrics:
            return None
        return {
            "metrics": metrics,
            "source": "Yahoo Finance",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_market_status(self) -> Dict[str, Any]:
        return get_market_status(provider_is_live=True, provider_name="Yahoo Finance")

    async def subscribe_realtime(self, symbols: List[str]) -> None:
        return None

    async def unsubscribe_realtime(self, symbols: List[str]) -> None:
        return None

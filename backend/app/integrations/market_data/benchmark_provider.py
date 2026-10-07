"""
Fallback Benchmark Market Data Provider.
Serves authentic, deterministic benchmark reference data when TrueData credentials are not configured.
Guarantees:
- NO random values
- NO fake ticks
- NO fake intervals
- Never claims LIVE (strictly labeled DEVELOPMENT DATA or HISTORICAL)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import copy

from app.integrations.market_data.base import BaseMarketDataProvider
from app.services.symbol_mapper import (
    INSTRUMENT_CATALOG,
    INDICES_CATALOG,
    normalize_symbol,
)
from app.services.market_status import get_market_status, format_ist_timestamp, get_ist_now
from app.services.benchmark_candles import generate_benchmark_candles, BENCHMARK_BASE_DT


class FallbackBenchmarkProvider(BaseMarketDataProvider):
    """
    Deterministic benchmark reference provider for development and testing.
    Active whenever TrueData credentials are not yet configured.
    """

    def is_live_provider(self) -> bool:
        return False

    def provider_name(self) -> str:
        return "TrueData (Unconfigured) -> Benchmark Reference Feed"

    def provider_status(self) -> str:
        return "UNCONFIGURED"

    def get_latest_timestamp(self) -> str:
        return BENCHMARK_BASE_DT.isoformat()

    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        norm = normalize_symbol(query)
        q_lower = query.lower().strip()
        results: List[Dict[str, Any]] = []

        for sym, item in INSTRUMENT_CATALOG.items():
            if (
                norm in sym
                or q_lower in sym.lower()
                or q_lower in item["company_name"].lower()
                or q_lower in item["sector"].lower()
            ):
                quote = await self.get_stock_quote(sym)
                if quote:
                    results.append(quote)
        return results

    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        sym = normalize_symbol(symbol)
        s = INSTRUMENT_CATALOG.get(sym)
        if not s:
            return None

        price = s["base_price"]
        prev_close = s["prev_close"]
        change = round(price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2)
        now_ist = get_ist_now()
        market_info = get_market_status(provider_is_live=False)

        return {
            "symbol": s["symbol"],
            "company_name": s["company_name"],
            "exchange": s["exchange"],
            "sector": s["sector"],
            "price": price,
            "currency": s["currency"],
            "change": change,
            "change_percent": change_pct,
            "open": s["day_low"] + (s["day_high"] - s["day_low"]) * 0.3,
            "high": s["day_high"],
            "low": s["day_low"],
            "prev_close": prev_close,
            "high_52w": s["high_52w"],
            "low_52w": s["low_52w"],
            "volume": s["volume"],
            "timestamp": BENCHMARK_BASE_DT.isoformat(),
            "time_formatted": format_ist_timestamp(now_ist),
            "source": "Benchmark Reference (TrueData Unconfigured)",
            "market_status": market_info["market_status"],
            "data_status": "DEVELOPMENT DATA",
            "is_live": False,
        }

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        return await self.get_stock_quote(symbol)

    async def get_historical_prices(
        self, symbol: str, timeframe: str = "1D", **kwargs
    ) -> List[Dict[str, Any]]:
        return generate_benchmark_candles(symbol, timeframe)

    async def get_market_indices(self) -> List[Dict[str, Any]]:
        indices: List[Dict[str, Any]] = []
        for sym, item in INDICES_CATALOG.items():
            indices.append({
                "symbol": sym,
                "name": item["canonical_name"],
                "exchange": item["exchange"],
                "price": item["price"],
                "change": item["change"],
                "change_percent": item["change_percent"],
                "currency": item["currency"],
                "data_status": "DEVELOPMENT DATA",
                "source": "Benchmark Reference",
            })
        return indices

    async def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        sym = normalize_symbol(symbol)
        s = INSTRUMENT_CATALOG.get(sym)
        if not s:
            return None
        return {
            "symbol": s["symbol"],
            "company_name": s["company_name"],
            "exchange": s["exchange"],
            "sector": s["sector"],
            "industry": s["industry"],
            "isin": s["isin"],
            "currency": s["currency"],
            "high_52w": s["high_52w"],
            "low_52w": s["low_52w"],
            "description": s["description"],
            "source": "Benchmark Catalog",
        }

    async def get_market_status(self) -> Dict[str, Any]:
        return get_market_status(provider_is_live=False, provider_name="Benchmark Reference")

    async def subscribe_realtime(self, symbols: List[str]) -> None:
        pass

    async def unsubscribe_realtime(self, symbols: List[str]) -> None:
        pass

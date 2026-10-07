"""
Official TrueData Market Data Provider Integration for SmartStock AI.
Connects to TrueData REST API and WebSocket feed for Indian Equities and Indices (NSE/BSE).
Credentials are read strictly from environment variables: TRUEDATA_USERNAME and TRUEDATA_PASSWORD.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx
import websockets

from app.core.config import settings
from app.integrations.market_data.base import BaseMarketDataProvider
from app.services.symbol_mapper import (
    INSTRUMENT_CATALOG,
    INDICES_CATALOG,
    normalize_symbol,
    get_truedata_symbol,
)
from app.services.market_status import get_market_status, format_ist_timestamp, get_ist_now

logger = logging.getLogger(__name__)


class TrueDataProvider(BaseMarketDataProvider):
    """
    Production TrueData provider implementation.
    Adheres strictly to TrueData official REST and WebSocket specifications.
    """

    def __init__(self):
        self.username = os.getenv("TRUEDATA_USERNAME", settings.TRUEDATA_USERNAME).strip()
        self.password = os.getenv("TRUEDATA_PASSWORD", settings.TRUEDATA_PASSWORD).strip()
        self.base_url = os.getenv("TRUEDATA_URL", settings.TRUEDATA_URL).rstrip("/")
        self.ws_url = os.getenv("TRUEDATA_WS_URL", settings.TRUEDATA_WS_URL)
        self.port = int(os.getenv("TRUEDATA_PORT", str(settings.TRUEDATA_PORT)))

        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._auth_token: Optional[str] = None
        self._subscribed_symbols: set = set()
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=12.0)

    def is_configured(self) -> bool:
        """Check if TrueData credentials are provided."""
        return bool(self.username and self.password)

    def is_live_provider(self) -> bool:
        return self.is_configured() and (self._ws is not None and not self._ws.closed)

    def provider_name(self) -> str:
        return "TrueData"

    def provider_status(self) -> str:
        if not self.is_configured():
            return "UNCONFIGURED"
        if self._ws and not self._ws.closed:
            return "LIVE"
        return "CONFIGURED_REST"

    def get_latest_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def _authenticate_rest(self) -> Optional[str]:
        """Authenticate with TrueData REST API if needed."""
        if not self.is_configured():
            return None
        if self._auth_token:
            return self._auth_token
        try:
            auth_url = f"{self.base_url}/token"
            res = await self._client.post(
                auth_url,
                data={"username": self.username, "password": self.password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if res.is_success:
                data = res.json()
                self._auth_token = data.get("access_token")
                return self._auth_token
            logger.warning(f"TrueData auth returned status: {res.status_code}")
        except Exception as e:
            logger.error(f"TrueData REST authentication failure: {e}")
        return None

    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        norm = normalize_symbol(query)
        # 1. Check if query matches catalog instrument
        results: List[Dict[str, Any]] = []
        for sym, item in INSTRUMENT_CATALOG.items():
            if (
                norm in sym
                or query.lower() in item["company_name"].lower()
                or query.lower() in item["sector"].lower()
            ):
                quote = await self.get_stock_quote(sym)
                if quote:
                    results.append(quote)

        # 2. If authenticated, query TrueData search endpoint
        if self.is_configured() and len(results) == 0:
            try:
                token = await self._authenticate_rest()
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                res = await self._client.get(f"/search?query={query}", headers=headers)
                if res.is_success:
                    data = res.json()
                    for row in data.get("records", []):
                        results.append({
                            "symbol": row.get("symbol"),
                            "company_name": row.get("name", row.get("symbol")),
                            "exchange": row.get("exchange", "NSE"),
                            "price": float(row.get("ltp", 0.0)),
                            "data_status": "LIVE" if self.is_live_provider() else "DELAYED",
                            "source": "TrueData",
                        })
            except Exception as e:
                logger.error(f"TrueData search error: {e}")

        return results

    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        norm = normalize_symbol(symbol)
        td_sym = get_truedata_symbol(norm)
        now_ist = get_ist_now()

        # If connected to TrueData REST API
        if self.is_configured():
            try:
                token = await self._authenticate_rest()
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                res = await self._client.get(f"/quote/{td_sym}", headers=headers)
                if res.is_success:
                    raw = res.json()
                    ltp = float(raw.get("ltp", raw.get("price", 0.0)))
                    prev_close = float(raw.get("prev_close", ltp))
                    change = round(ltp - prev_close, 2)
                    change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
                    return {
                        "symbol": norm,
                        "company_name": raw.get("company_name", norm),
                        "exchange": raw.get("exchange", "NSE"),
                        "sector": raw.get("sector", "Equities"),
                        "price": ltp,
                        "currency": "INR",
                        "change": change,
                        "change_percent": change_pct,
                        "open": float(raw.get("open", ltp)),
                        "high": float(raw.get("high", ltp)),
                        "low": float(raw.get("low", ltp)),
                        "prev_close": prev_close,
                        "high_52w": float(raw.get("high_52w", ltp * 1.15)),
                        "low_52w": float(raw.get("low_52w", ltp * 0.8)),
                        "volume": int(raw.get("volume", 0)),
                        "timestamp": raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        "time_formatted": format_ist_timestamp(now_ist),
                        "source": "TrueData",
                        "market_status": get_market_status(self.is_live_provider())["market_status"],
                        "data_status": "LIVE" if self.is_live_provider() else "DELAYED",
                        "is_live": self.is_live_provider(),
                    }
            except Exception as e:
                logger.warning(f"TrueData quote request for {td_sym} failed: {e}")

        return None

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        return await self.get_stock_quote(symbol)

    async def get_historical_prices(
        self, symbol: str, timeframe: str = "1D", **kwargs
    ) -> List[Dict[str, Any]]:
        norm = normalize_symbol(symbol)
        td_sym = get_truedata_symbol(norm)

        if self.is_configured():
            try:
                token = await self._authenticate_rest()
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                # Query TrueData historical bars endpoint
                res = await self._client.get(
                    f"/getbars?symbol={td_sym}&interval={timeframe.lower()}&response=json",
                    headers=headers,
                )
                if res.is_success:
                    candles = []
                    for row in res.json().get("data", []):
                        candles.append({
                            "timestamp": row["timestamp"],
                            "time_label": row.get("time_label", row["timestamp"]),
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": int(row.get("volume", 0)),
                            "data_status": "HISTORICAL",
                            "source": "TrueData",
                        })
                    return candles
            except Exception as e:
                logger.error(f"TrueData historical request failed: {e}")

        return []

    async def get_market_indices(self) -> List[Dict[str, Any]]:
        indices: List[Dict[str, Any]] = []
        if self.is_configured():
            for sym, info in INDICES_CATALOG.items():
                td_sym = info["truedata_symbol"]
                try:
                    res = await self._client.get(f"/quote/{td_sym}")
                    if res.is_success:
                        raw = res.json()
                        indices.append({
                            "symbol": sym,
                            "name": info["canonical_name"],
                            "exchange": info["exchange"],
                            "price": float(raw.get("ltp", info["price"])),
                            "change": float(raw.get("change", info["change"])),
                            "change_percent": float(raw.get("change_percent", info["change_percent"])),
                            "currency": "INR",
                            "data_status": "LIVE" if self.is_live_provider() else "DELAYED",
                            "source": "TrueData",
                        })
                except Exception:
                    pass
        return indices

    async def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        norm = normalize_symbol(symbol)
        if norm in INSTRUMENT_CATALOG:
            c = INSTRUMENT_CATALOG[norm]
            return {
                "symbol": norm,
                "company_name": c["company_name"],
                "exchange": c["exchange"],
                "sector": c["sector"],
                "industry": c["industry"],
                "isin": c["isin"],
                "currency": c["currency"],
                "high_52w": c["high_52w"],
                "low_52w": c["low_52w"],
                "description": c["description"],
                "source": "TrueData Catalog",
            }
        return None

    async def get_market_status(self) -> Dict[str, Any]:
        return get_market_status(provider_is_live=self.is_live_provider(), provider_name="TrueData")

    async def subscribe_realtime(self, symbols: List[str]) -> None:
        if not self.is_configured():
            return
        for s in symbols:
            self._subscribed_symbols.add(get_truedata_symbol(normalize_symbol(s)))
        # Send subscribe frame over WebSocket if connected
        if self._ws and not self._ws.closed:
            await self._ws.send(
                json.dumps({"method": "sub", "symbols": list(self._subscribed_symbols)})
            )

    async def unsubscribe_realtime(self, symbols: List[str]) -> None:
        for s in symbols:
            self._subscribed_symbols.discard(get_truedata_symbol(normalize_symbol(s)))
        if self._ws and not self._ws.closed:
            await self._ws.send(
                json.dumps({"method": "unsub", "symbols": [get_truedata_symbol(normalize_symbol(s)) for s in symbols]})
            )

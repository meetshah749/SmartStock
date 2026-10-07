from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseMarketDataProvider(ABC):
    """
    Standard Market Data Provider abstraction for SmartStock AI.
    Exposes unified operations for stock quotes, search, historical candles,
    market indices, company profiles, and real-time streaming subscriptions.
    """

    @abstractmethod
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search stocks by ticker symbol or company name."""
        pass

    @abstractmethod
    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote details including LTP, OHLC, volume, timestamp, source, and data_status."""
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Alias for get_stock_quote."""
        pass

    @abstractmethod
    async def get_historical_prices(
        self, symbol: str, timeframe: str = "1D", **kwargs
    ) -> List[Dict[str, Any]]:
        """Get verified OHLCV historical time series bars."""
        pass

    @abstractmethod
    async def get_market_indices(self) -> List[Dict[str, Any]]:
        """Get status of major market indices (NIFTY 50, SENSEX, BANKNIFTY)."""
        pass

    @abstractmethod
    async def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed company information, sector, and exchange details."""
        pass

    @abstractmethod
    async def get_market_status(self) -> Dict[str, Any]:
        """Get exchange operating phase (MARKET OPEN, CLOSED, PRE-OPEN, etc.)."""
        pass

    @abstractmethod
    def get_latest_timestamp(self) -> str:
        """Get latest tick/reference ISO timestamp."""
        pass

    @abstractmethod
    async def subscribe_realtime(self, symbols: List[str]) -> None:
        """Subscribe to real-time tick updates for specified instruments."""
        pass

    @abstractmethod
    async def unsubscribe_realtime(self, symbols: List[str]) -> None:
        """Unsubscribe from real-time tick updates."""
        pass

    @abstractmethod
    def is_live_provider(self) -> bool:
        """Return True only if this provider is actively connected to live external feed."""
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """Return human-readable identifier of the market data provider."""
        pass

    @abstractmethod
    def provider_status(self) -> str:
        """Return operational status: LIVE, DELAYED, UNCONFIGURED, OFFLINE."""
        pass

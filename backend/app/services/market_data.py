"""
Market Data Service Abstraction and Factory for SmartStock AI.
Exports BaseMarketDataProvider, TrueDataProvider, and FallbackBenchmarkProvider.
Injects the appropriate provider depending on environment configuration.
"""

import os
import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.integrations.market_data.base import BaseMarketDataProvider
from app.integrations.market_data.truedata_provider import TrueDataProvider
from app.integrations.market_data.yahoo_provider import YahooFinanceProvider
from app.integrations.market_data.benchmark_provider import FallbackBenchmarkProvider

logger = logging.getLogger(__name__)

# Alias for backward compatibility
MarketDataProvider = BaseMarketDataProvider

_singleton_provider: Optional[BaseMarketDataProvider] = None


def get_market_provider() -> BaseMarketDataProvider:
    """
    Dependency injection helper for FastAPI.
    Prefers a real external feed when configured; otherwise falls back to Yahoo Finance
    and then the benchmark reference feed as a last resort.
    """
    global _singleton_provider
    if _singleton_provider is not None:
        return _singleton_provider

    provider_name = str(getattr(settings, "MARKET_DATA_PROVIDER", "yahoo")).lower().strip()

    if provider_name == "truedata":
        truedata = TrueDataProvider()
        _singleton_provider = truedata if truedata.is_configured() else YahooFinanceProvider()
        logger.info(
            "[MarketDataProvider] Initialized %s (%s).",
            _singleton_provider.provider_name(),
            "TrueData credentials configured" if isinstance(_singleton_provider, TrueDataProvider) else "Yahoo Finance selected",
        )
    elif provider_name == "benchmark_fixture":
        _singleton_provider = FallbackBenchmarkProvider()
        logger.info("[MarketDataProvider] Initialized FallbackBenchmarkProvider (benchmark fixture selected).")
    else:
        _singleton_provider = YahooFinanceProvider()
        logger.info("[MarketDataProvider] Initialized YahooFinanceProvider (real public market data selected).")

    return _singleton_provider


async def close_provider(provider: BaseMarketDataProvider):
    """Graceful shutdown hook for market data provider clients."""
    if isinstance(provider, TrueDataProvider):
        await provider._client.aclose()
        if provider._ws and not provider._ws.closed:
            await provider._ws.close()

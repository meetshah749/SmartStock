import math
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from app.integrations.market_data.base import BaseMarketDataProvider

STOCKS_CATALOG = [
    {
        "symbol": "RELIANCE",
        "company_name": "Reliance Industries Ltd.",
        "exchange": "NSE",
        "sector": "Energy & Conglomerate",
        "price": 2980.50,
        "prev_close": 2940.00,
        "currency": "INR",
        "description": "Reliance Industries Limited is an Indian multinational conglomerate headquartered in Mumbai. Its businesses include energy, petrochemicals, natural gas, retail, telecommunications, mass media, and textiles.",
    },
    {
        "symbol": "TCS",
        "company_name": "Tata Consultancy Services Ltd.",
        "exchange": "NSE",
        "sector": "Information Technology",
        "price": 4210.75,
        "prev_close": 4185.20,
        "currency": "INR",
        "description": "Tata Consultancy Services is an Indian multinational information technology services and consulting company headquartered in Mumbai. It is a part of the Tata Group and operates in 150 locations across 46 countries.",
    },
    {
        "symbol": "INFY",
        "company_name": "Infosys Limited",
        "exchange": "NSE",
        "sector": "Information Technology",
        "price": 1945.30,
        "prev_close": 1920.00,
        "currency": "INR",
        "description": "Infosys Limited is an Indian multinational information technology company that provides business consulting, information technology and outsourcing services.",
    },
    {
        "symbol": "HDFCBANK",
        "company_name": "HDFC Bank Limited",
        "exchange": "NSE",
        "sector": "Financial Services",
        "price": 1660.10,
        "prev_close": 1672.40,
        "currency": "INR",
        "description": "HDFC Bank Limited is an Indian banking and financial services company headquartered in Mumbai. It is India's largest private sector bank by assets and world's tenth largest bank by market capitalization.",
    },
    {
        "symbol": "TATAMOTORS",
        "company_name": "Tata Motors Limited",
        "exchange": "NSE",
        "sector": "Automotive",
        "price": 985.60,
        "prev_close": 962.00,
        "currency": "INR",
        "description": "Tata Motors Limited is an Indian multinational automotive manufacturing company headquartered in Mumbai, India, which is part of Tata Group.",
    },
    {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "price": 224.50,
        "prev_close": 221.30,
        "currency": "USD",
        "description": "Apple Inc. is an American multinational corporation and technology company headquartered in Cupertino, California, in Silicon Valley.",
    },
    {
        "symbol": "NVDA",
        "company_name": "NVIDIA Corporation",
        "exchange": "NASDAQ",
        "sector": "Semiconductors",
        "price": 118.75,
        "prev_close": 114.20,
        "currency": "USD",
        "description": "NVIDIA Corporation is an American multinational corporation and technology company headquartered in Santa Clara, California.",
    },
    {
        "symbol": "MSFT",
        "company_name": "Microsoft Corporation",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "price": 435.20,
        "prev_close": 431.00,
        "currency": "USD",
        "description": "Microsoft Corporation is an American multinational corporation and technology company headquartered in Redmond, Washington.",
    },
    {
        "symbol": "GOOGL",
        "company_name": "Alphabet Inc. (Google)",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "price": 178.60,
        "prev_close": 180.10,
        "currency": "USD",
        "description": "Alphabet Inc. is an American multinational technology conglomerate holding company created through a restructuring of Google.",
    },
]


from app.integrations.market_data.benchmark_provider import FallbackBenchmarkProvider


class MockMarketDataProvider(FallbackBenchmarkProvider):
    """
    Backward-compatible fixture provider.
    Inherits deterministic benchmark market data from FallbackBenchmarkProvider.
    """
    def __init__(self):
        super().__init__()
        self.stocks = {s["symbol"]: s for s in STOCKS_CATALOG}


    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        return await self.get_stock_quote(symbol)

    async def get_historical_prices(self, symbol: str, timeframe: str = "1D", **kwargs) -> List[Dict[str, Any]]:
        quote = await self.get_stock_quote(symbol)
        if not quote:
            return []

        base_price = quote["price"]
        num_points = 50
        delta_minutes = 15

        if timeframe == "1W":
            num_points = 35
            delta_minutes = 60 * 4
        elif timeframe in ["1M", "3M"]:
            num_points = 60
            delta_minutes = 60 * 24
        elif timeframe in ["6M", "1Y", "5Y"]:
            num_points = 100
            delta_minutes = 60 * 24 * 3

        end_time = datetime.now(timezone.utc)
        history = []

        curr_price = base_price * 0.92
        for i in range(num_points):
            t = end_time - timedelta(minutes=delta_minutes * (num_points - i - 1))
            # Smooth Brownian walk
            noise = (random.random() - 0.48) * (base_price * 0.015)
            curr_price = max(curr_price + noise, base_price * 0.5)

            open_p = round(curr_price, 2)
            high_p = round(open_p + random.random() * (base_price * 0.008), 2)
            low_p = round(open_p - random.random() * (base_price * 0.008), 2)
            close_p = round((open_p + high_p + low_p) / 3, 2)

            history.append({
                "timestamp": t.isoformat(),
                "time_label": t.strftime("%H:%M") if timeframe == "1D" else t.strftime("%b %d"),
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p,
                "volume": random.randint(10000, 200000),
            })

        # Set last close to match exact quote price
        if history:
            history[-1]["close"] = base_price
            history[-1]["high"] = max(history[-1]["high"], base_price)

        return history

    async def get_market_indices(self) -> List[Dict[str, Any]]:
        return [
            {
                "symbol": "NIFTY50",
                "name": "NIFTY 50",
                "exchange": "NSE",
                "price": 25380.40,
                "change": 142.60,
                "change_percent": 0.56,
                "currency": "INR",
                "data_status": "DELAYED",
            },
            {
                "symbol": "SENSEX",
                "name": "BSE SENSEX",
                "exchange": "BSE",
                "price": 82950.15,
                "change": 420.30,
                "change_percent": 0.51,
                "currency": "INR",
                "data_status": "DELAYED",
            },
            {
                "symbol": "BANKNIFTY",
                "name": "NIFTY BANK",
                "exchange": "NSE",
                "price": 52140.80,
                "change": -85.20,
                "change_percent": -0.16,
                "currency": "INR",
                "data_status": "DELAYED",
            },
            {
                "symbol": "SPX",
                "name": "S&P 500",
                "exchange": "US",
                "price": 5626.02,
                "change": 24.15,
                "change_percent": 0.43,
                "currency": "USD",
                "data_status": "DELAYED",
            },
        ]

    async def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        s = self.stocks.get(symbol.upper().strip())
        if not s:
            return None
        return {
            "symbol": s["symbol"],
            "company_name": s["company_name"],
            "exchange": s["exchange"],
            "sector": s["sector"],
            "currency": s["currency"],
            "description": s["description"],
        }

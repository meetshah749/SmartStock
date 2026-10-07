from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta


class NewsSentimentService:
    """Financial news aggregator with sentiment classification for market tickers."""

    def __init__(self):
        self.mock_articles = [
            {
                "id": "news-1",
                "title": "Reliance Industries Expands Clean Energy Investments with ₹15,000 Cr Allocation",
                "publisher": "Economic Times",
                "published_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "summary": "Reliance Industries announces new green hydrogen infrastructure deals, boosting investor sentiment across the renewable energy sector.",
                "url": "https://economictimes.indiatimes.com",
                "ticker_symbol": "RELIANCE",
                "category": "CORPORATE",
                "sentiment": "BULLISH",
                "sentiment_score": 0.82,
            },
            {
                "id": "news-2",
                "title": "Tata Consultancy Services (TCS) Secures Multi-Year $1.2B Cloud Modernization Deal in Europe",
                "publisher": "LiveMint",
                "published_at": (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(),
                "summary": "TCS signs a strategic cloud transformation contract with a European bank, highlighting sustained demand for enterprise IT services.",
                "url": "https://livemint.com",
                "ticker_symbol": "TCS",
                "category": "TECH",
                "sentiment": "BULLISH",
                "sentiment_score": 0.88,
            },
            {
                "id": "news-3",
                "title": "Infosys Reports Strong Q3 Deal Pipeline Despite Global Macroeconomic Headwinds",
                "publisher": "Financial Express",
                "published_at": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
                "summary": "Infosys management reaffirms FY26 revenue guidance as total contract value rises across North American enterprise clients.",
                "url": "https://financialexpress.com",
                "ticker_symbol": "INFY",
                "category": "EARNINGS",
                "sentiment": "BULLISH",
                "sentiment_score": 0.74,
            },
            {
                "id": "news-4",
                "title": "RBI Maintains Repo Rate at 6.50%, Citing Balanced Inflation and Growth Trajectory",
                "publisher": "Business Standard",
                "published_at": (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat(),
                "summary": "The Monetary Policy Committee holds rates steady while emphasizing liquidity management for Indian commercial banks.",
                "url": "https://business-standard.com",
                "ticker_symbol": "BANKNIFTY",
                "category": "MACRO",
                "sentiment": "NEUTRAL",
                "sentiment_score": 0.12,
            },
            {
                "id": "news-5",
                "title": "Global Tech Stocks Face Short-Term Volatility Amid Treasury Yield Adjustments",
                "publisher": "Reuters Financial",
                "published_at": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
                "summary": "Apple and US mega-cap tech shares experienced slight pullbacks as bond yields adjusted ahead of Federal Reserve commentary.",
                "url": "https://reuters.com",
                "ticker_symbol": "AAPL",
                "category": "GLOBAL",
                "sentiment": "BEARISH",
                "sentiment_score": -0.45,
            },
            {
                "id": "news-6",
                "title": "NIFTY 50 Touches New High Driven by Banking and Automobile Rally",
                "publisher": "CNBC-TV18",
                "published_at": (datetime.now(timezone.utc) - timedelta(hours=14)).isoformat(),
                "summary": "Strong foreign institutional investor (FII) inflows pushed NIFTY 50 above key resistance levels during today's trading session.",
                "url": "https://cnbctv18.com",
                "ticker_symbol": "NIFTY",
                "category": "MARKET",
                "sentiment": "BULLISH",
                "sentiment_score": 0.91,
            },
        ]

    def get_market_news(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        if not category:
            return self.mock_articles
        return [a for a in self.mock_articles if a["category"].upper() == category.upper()]

    def get_stock_news(self, symbol: str) -> List[Dict[str, Any]]:
        sym = symbol.upper()
        ticker_news = [a for a in self.mock_articles if a["ticker_symbol"] == sym]
        if not ticker_news:
            # Fallback ticker article
            return [
                {
                    "id": f"news-{sym}-1",
                    "title": f"Market Analysis: {sym} Technical Setup & Quarterly Expectations",
                    "publisher": "SmartStock Market Desk",
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "summary": f"Analysts track trading volume and key resistance levels for {sym} as sector sentiment remains steady.",
                    "url": "https://smartstock.ai",
                    "ticker_symbol": sym,
                    "category": "EQUITY",
                    "sentiment": "NEUTRAL",
                    "sentiment_score": 0.20,
                }
            ]
        return ticker_news


news_service = NewsSentimentService()

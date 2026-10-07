from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Exchange(BaseModel):
    __tablename__ = "exchanges"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)  # NSE, BSE, NASDAQ
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)


class Stock(BaseModel):
    __tablename__ = "stocks"

    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), default="NSE", nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class StockPrice(BaseModel):
    __tablename__ = "stock_prices"

    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    open_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    high_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    low_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    prev_close_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    change_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    change_percent: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    data_status: Mapped[str] = mapped_column(String(20), default="DELAYED", nullable=False)  # LIVE, DELAYED, HISTORICAL, UNAVAILABLE
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class HistoricalPrice(BaseModel):
    __tablename__ = "historical_prices"

    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), default="1D", nullable=False)  # 1D, 1W, 1M, 3M, 6M, 1Y, 5Y
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Portfolio(BaseModel):
    __tablename__ = "portfolios"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_invested_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    realized_pnl_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    holdings: Mapped[list["Holding"]] = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")


class Holding(BaseModel):
    __tablename__ = "holdings"

    portfolio_id: Mapped[str] = mapped_column(String(36), ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_buy_price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_invested_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="holdings")


class Order(BaseModel):
    __tablename__ = "orders"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    order_type: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY or SELL
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    execution_price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="FILLED", nullable=False)  # FILLED, PENDING, CANCELLED
    is_virtual: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    trade: Mapped["VirtualTrade"] = relationship("VirtualTrade", back_populates="order", uselist=False, cascade="all, delete-orphan")


class VirtualTrade(BaseModel):
    __tablename__ = "virtual_trades"

    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    realized_pnl_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="trade")

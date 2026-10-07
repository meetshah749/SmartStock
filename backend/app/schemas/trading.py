from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    quantity: int = Field(..., gt=0, description="Quantity of shares to buy or sell")


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    symbol: str
    company_name: str
    order_type: str
    quantity: int
    execution_price_paise: int
    execution_price_rupees: float
    total_amount_paise: int
    total_amount_rupees: float
    status: str
    is_virtual: bool
    created_at: datetime


class HoldingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    symbol: str
    company_name: str
    quantity: int
    avg_buy_price_paise: int
    avg_buy_price_rupees: float
    total_invested_paise: int
    total_invested_rupees: float
    current_price_rupees: float
    current_value_rupees: float
    unrealized_pnl_rupees: float
    unrealized_pnl_percent: float


class PortfolioSummaryOut(BaseModel):
    total_invested_rupees: float
    current_value_rupees: float
    unrealized_pnl_rupees: float
    unrealized_pnl_percent: float
    realized_pnl_rupees: float
    wallet_balance_rupees: float
    holdings_count: int


class WalletLedgerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    amount_paise: int
    amount_rupees: float
    balance_before_paise: int
    balance_before_rupees: float
    balance_after_paise: int
    balance_after_rupees: float
    transaction_type: str
    reference_id: Optional[str] = None
    created_at: datetime

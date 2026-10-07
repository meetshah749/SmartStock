from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Indicator = Literal[
    "SMA20", "SMA50", "SMA200", "EMA20", "EMA50", "RSI", "MACD", "MACD_SIGNAL",
    "BOLLINGER_UPPER", "BOLLINGER_MIDDLE", "BOLLINGER_LOWER", "ATR", "VOLUME",
]
Operator = Literal[">", "<", ">=", "<=", "crosses_above", "crosses_below"]
StrategyType = Literal["golden_cross", "rsi_momentum", "macd_trend", "conservative_trend", "buy_hold", "custom"]


class CustomCondition(BaseModel):
    left: Indicator
    operator: Operator
    right_indicator: Indicator | None = None
    right_value: Decimal | None = None

    @model_validator(mode="after")
    def exactly_one_right_hand_side(self):
        if (self.right_indicator is None) == (self.right_value is None):
            raise ValueError("Provide exactly one right_indicator or right_value.")
        if self.right_value is not None and not self.right_value.is_finite():
            raise ValueError("Custom numeric values must be finite.")
        return self


class ConditionGroup(BaseModel):
    join: Literal["AND", "OR"] = "AND"
    conditions: list[CustomCondition] = Field(min_length=1, max_length=5)


class StrategyConfig(BaseModel):
    type: StrategyType
    name: str | None = Field(default=None, max_length=80)
    entry: ConditionGroup | None = None
    exit: ConditionGroup | None = None

    @model_validator(mode="after")
    def validate_custom_rules(self):
        if self.type == "custom" and (self.entry is None or self.exit is None):
            raise ValueError("Custom strategies need both entry and exit condition groups.")
        if self.type != "custom" and (self.entry is not None or self.exit is not None):
            raise ValueError("Entry/exit conditions are only allowed for custom strategies.")
        return self


class BacktestRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    exchange: Literal["NSE", "BSE"] | None = None
    start_date: date
    end_date: date
    initial_capital: Decimal = Field(ge=Decimal("1000"), le=Decimal("100000000000"))
    strategy: StrategyConfig
    transaction_cost_pct: Decimal = Field(default=Decimal("0.10"), ge=0, le=5)
    slippage_pct: Decimal = Field(default=Decimal("0.05"), ge=0, le=5)
    position_pct: Decimal = Field(default=Decimal("100"), gt=0, le=100)
    compare_strategies: bool = False

    @model_validator(mode="after")
    def validate_dates_and_amounts(self):
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be earlier than end date.")
        if self.end_date >= date.today():
            raise ValueError("End date must be before today because the backtest uses completed historical candles.")
        if (self.end_date - self.start_date).days > 365 * 15:
            raise ValueError("Backtest periods are limited to 15 years to keep provider requests and simulations bounded.")
        if not self.initial_capital.is_finite() or not self.transaction_cost_pct.is_finite() or not self.slippage_pct.is_finite():
            raise ValueError("Capital, costs, and slippage must be finite numbers.")
        return self


class BacktestAnalysisRequest(BaseModel):
    backtest_id: str = Field(min_length=1, max_length=36)

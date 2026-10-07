from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.session import get_async_db
from app.services.market_data import get_market_provider
from app.models.user import User, Wallet
from app.models.trading import Portfolio, Holding
from app.schemas.trading import HoldingOut, PortfolioSummaryOut

router = APIRouter(prefix="/portfolio", tags=["Portfolio & Holdings"])
market_provider = get_market_provider()


@router.get("", response_model=PortfolioSummaryOut)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    # 1. Fetch User Wallet Balance
    wallet_res = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = wallet_res.scalar_one_or_none()
    wallet_balance = (wallet.balance_paise / 100.0) if wallet else 500.0

    # 2. Fetch User Portfolio
    port_res = await db.execute(select(Portfolio).where(Portfolio.user_id == current_user.id))
    portfolio = port_res.scalar_one_or_none()

    if not portfolio:
        return PortfolioSummaryOut(
            total_invested_rupees=0.0,
            current_value_rupees=0.0,
            unrealized_pnl_rupees=0.0,
            unrealized_pnl_percent=0.0,
            realized_pnl_rupees=0.0,
            wallet_balance_rupees=wallet_balance,
            holdings_count=0,
        )

    # 3. Calculate live market values for holdings
    hold_res = await db.execute(select(Holding).where(Holding.portfolio_id == portfolio.id))
    holdings = hold_res.scalars().all()

    total_invested = 0.0
    current_val = 0.0

    for h in holdings:
        inv = h.total_invested_paise / 100.0
        total_invested += inv
        quote = await market_provider.get_stock_quote(h.symbol)
        curr_price = quote["price"] if quote else (h.avg_buy_price_paise / 100.0)
        current_val += curr_price * h.quantity

    unrealized_pnl = current_val - total_invested
    unrealized_pnl_pct = (unrealized_pnl / total_invested * 100.0) if total_invested > 0 else 0.0
    realized_pnl = portfolio.realized_pnl_paise / 100.0

    return PortfolioSummaryOut(
        total_invested_rupees=round(total_invested, 2),
        current_value_rupees=round(current_val, 2),
        unrealized_pnl_rupees=round(unrealized_pnl, 2),
        unrealized_pnl_percent=round(unrealized_pnl_pct, 2),
        realized_pnl_rupees=round(realized_pnl, 2),
        wallet_balance_rupees=round(wallet_balance, 2),
        holdings_count=len(holdings),
    )


@router.get("/holdings", response_model=List[HoldingOut])
async def get_portfolio_holdings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    port_res = await db.execute(select(Portfolio).where(Portfolio.user_id == current_user.id))
    portfolio = port_res.scalar_one_or_none()

    if not portfolio:
        return []

    hold_res = await db.execute(select(Holding).where(Holding.portfolio_id == portfolio.id))
    holdings = hold_res.scalars().all()

    results = []
    for h in holdings:
        quote = await market_provider.get_stock_quote(h.symbol)
        curr_price = quote["price"] if quote else (h.avg_buy_price_paise / 100.0)
        curr_val = curr_price * h.quantity
        total_inv = h.total_invested_paise / 100.0
        unrealized = curr_val - total_inv
        unrealized_pct = (unrealized / total_inv * 100.0) if total_inv > 0 else 0.0

        results.append(
            HoldingOut(
                id=h.id,
                symbol=h.symbol,
                company_name=h.company_name,
                quantity=h.quantity,
                avg_buy_price_paise=h.avg_buy_price_paise,
                avg_buy_price_rupees=h.avg_buy_price_paise / 100.0,
                total_invested_paise=h.total_invested_paise,
                total_invested_rupees=total_inv,
                current_price_rupees=round(curr_price, 2),
                current_value_rupees=round(curr_val, 2),
                unrealized_pnl_rupees=round(unrealized, 2),
                unrealized_pnl_percent=round(unrealized_pct, 2),
            )
        )

    return results

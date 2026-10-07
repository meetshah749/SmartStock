from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.session import get_async_db
from app.services.market_data import get_market_provider
from app.models.user import User, Wallet, WalletLedger
from app.models.trading import Portfolio, Holding, Order, VirtualTrade
from app.schemas.trading import OrderCreate, OrderOut

router = APIRouter(prefix="/orders", tags=["Virtual Trading Engine"])
market_provider = get_market_provider()


@router.post("/buy", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def buy_virtual_shares(
    order_in: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    # 1. Fetch current market quote
    quote = await market_provider.get_stock_quote(order_in.symbol)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock '{order_in.symbol}' not available for trading",
        )

    exec_price_rupees = quote["price"]
    exec_price_paise = int(round(exec_price_rupees * 100))
    total_amount_paise = exec_price_paise * order_in.quantity

    # 2. Lock & fetch user's wallet
    stmt = select(Wallet).where(Wallet.user_id == current_user.id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()

    if not wallet or wallet.balance_paise < total_amount_paise:
        avail_rupees = (wallet.balance_paise / 100.0) if wallet else 0.0
        req_rupees = total_amount_paise / 100.0
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient virtual wallet balance. Required: ₹{req_rupees:.2f}, Available: ₹{avail_rupees:.2f}",
        )

    # 3. Deduct wallet balance & create ledger entry
    balance_before = wallet.balance_paise
    wallet.balance_paise -= total_amount_paise
    balance_after = wallet.balance_paise

    ledger_entry = WalletLedger(
        wallet_id=wallet.id,
        amount_paise=-total_amount_paise,
        balance_before_paise=balance_before,
        balance_after_paise=balance_after,
        transaction_type="VIRTUAL_BUY",
        reference_id=f"BUY_{quote['symbol']}_{order_in.quantity}QTY",
    )
    db.add(ledger_entry)

    # 4. Get or create Portfolio
    port_stmt = select(Portfolio).where(Portfolio.user_id == current_user.id)
    port_res = await db.execute(port_stmt)
    portfolio = port_res.scalar_one_or_none()
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id)
        db.add(portfolio)
        await db.flush()

    portfolio.total_invested_paise += total_amount_paise

    # 5. Update or create Holding position
    hold_stmt = select(Holding).where(
        Holding.portfolio_id == portfolio.id,
        Holding.symbol == quote["symbol"],
    )
    hold_res = await db.execute(hold_stmt)
    holding = hold_res.scalar_one_or_none()

    if holding:
        new_qty = holding.quantity + order_in.quantity
        new_total_invested = holding.total_invested_paise + total_amount_paise
        holding.quantity = new_qty
        holding.total_invested_paise = new_total_invested
        holding.avg_buy_price_paise = int(round(new_total_invested / new_qty))
    else:
        holding = Holding(
            portfolio_id=portfolio.id,
            symbol=quote["symbol"],
            company_name=quote["company_name"],
            quantity=order_in.quantity,
            avg_buy_price_paise=exec_price_paise,
            total_invested_paise=total_amount_paise,
        )
        db.add(holding)

    # 6. Record Order & Virtual Trade
    order = Order(
        user_id=current_user.id,
        symbol=quote["symbol"],
        company_name=quote["company_name"],
        order_type="BUY",
        quantity=order_in.quantity,
        execution_price_paise=exec_price_paise,
        total_amount_paise=total_amount_paise,
        status="FILLED",
        is_virtual=True,
    )
    db.add(order)
    await db.flush()

    trade = VirtualTrade(
        order_id=order.id,
        user_id=current_user.id,
        symbol=quote["symbol"],
        quantity=order_in.quantity,
        price_paise=exec_price_paise,
        realized_pnl_paise=0,
    )
    db.add(trade)

    await db.commit()
    await db.refresh(order)

    return OrderOut(
        id=order.id,
        symbol=order.symbol,
        company_name=order.company_name,
        order_type=order.order_type,
        quantity=order.quantity,
        execution_price_paise=order.execution_price_paise,
        execution_price_rupees=order.execution_price_paise / 100.0,
        total_amount_paise=order.total_amount_paise,
        total_amount_rupees=order.total_amount_paise / 100.0,
        status=order.status,
        is_virtual=order.is_virtual,
        created_at=order.created_at,
    )


@router.post("/sell", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def sell_virtual_shares(
    order_in: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    # 1. Fetch quote
    quote = await market_provider.get_stock_quote(order_in.symbol)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock '{order_in.symbol}' not found")

    exec_price_paise = int(round(quote["price"] * 100))
    total_proceeds_paise = exec_price_paise * order_in.quantity

    # 2. Fetch User Portfolio & Holding
    port_stmt = select(Portfolio).where(Portfolio.user_id == current_user.id)
    port_res = await db.execute(port_stmt)
    portfolio = port_res.scalar_one_or_none()

    if not portfolio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You do not own any shares of this stock")

    hold_stmt = select(Holding).where(
        Holding.portfolio_id == portfolio.id,
        Holding.symbol == quote["symbol"],
    )
    hold_res = await db.execute(hold_stmt)
    holding = hold_res.scalar_one_or_none()

    if not holding or holding.quantity < order_in.quantity:
        avail_qty = holding.quantity if holding else 0
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient holdings to sell. Requested: {order_in.quantity}, Available: {avail_qty}",
        )

    # 3. Calculate Realized P&L
    cost_basis_paise = holding.avg_buy_price_paise * order_in.quantity
    realized_pnl_paise = total_proceeds_paise - cost_basis_paise

    portfolio.realized_pnl_paise += realized_pnl_paise

    # Update holding
    if holding.quantity == order_in.quantity:
        await db.delete(holding)
    else:
        holding.quantity -= order_in.quantity
        holding.total_invested_paise -= cost_basis_paise

    # 4. Credit Wallet & Ledger
    wallet_res = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = wallet_res.scalar_one()

    balance_before = wallet.balance_paise
    wallet.balance_paise += total_proceeds_paise
    balance_after = wallet.balance_paise

    ledger_entry = WalletLedger(
        wallet_id=wallet.id,
        amount_paise=total_proceeds_paise,
        balance_before_paise=balance_before,
        balance_after_paise=balance_after,
        transaction_type="VIRTUAL_SELL",
        reference_id=f"SELL_{quote['symbol']}_{order_in.quantity}QTY",
    )
    db.add(ledger_entry)

    # 5. Record Order & Virtual Trade
    order = Order(
        user_id=current_user.id,
        symbol=quote["symbol"],
        company_name=quote["company_name"],
        order_type="SELL",
        quantity=order_in.quantity,
        execution_price_paise=exec_price_paise,
        total_amount_paise=total_proceeds_paise,
        status="FILLED",
        is_virtual=True,
    )
    db.add(order)
    await db.flush()

    trade = VirtualTrade(
        order_id=order.id,
        user_id=current_user.id,
        symbol=quote["symbol"],
        quantity=order_in.quantity,
        price_paise=exec_price_paise,
        realized_pnl_paise=realized_pnl_paise,
    )
    db.add(trade)

    await db.commit()
    await db.refresh(order)

    return OrderOut(
        id=order.id,
        symbol=order.symbol,
        company_name=order.company_name,
        order_type=order.order_type,
        quantity=order.quantity,
        execution_price_paise=order.execution_price_paise,
        execution_price_rupees=order.execution_price_paise / 100.0,
        total_amount_paise=order.total_amount_paise,
        total_amount_rupees=order.total_amount_paise / 100.0,
        status=order.status,
        is_virtual=order.is_virtual,
        created_at=order.created_at,
    )


@router.get("", response_model=List[OrderOut])
async def list_user_orders(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    stmt = select(Order).where(Order.user_id == current_user.id).order_by(Order.created_at.desc())
    res = await db.execute(stmt)
    orders = res.scalars().all()

    return [
        OrderOut(
            id=o.id,
            symbol=o.symbol,
            company_name=o.company_name,
            order_type=o.order_type,
            quantity=o.quantity,
            execution_price_paise=o.execution_price_paise,
            execution_price_rupees=o.execution_price_paise / 100.0,
            total_amount_paise=o.total_amount_paise,
            total_amount_rupees=o.total_amount_paise / 100.0,
            status=o.status,
            is_virtual=o.is_virtual,
            created_at=o.created_at,
        )
        for o in orders
    ]

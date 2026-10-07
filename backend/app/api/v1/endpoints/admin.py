from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin_user
from app.database.session import get_async_db
from app.models.user import User, Wallet, WalletLedger
from app.models.trading import Order, VirtualTrade, Portfolio, Holding
from app.schemas.auth import UserOut

router = APIRouter(prefix="/admin", tags=["Admin Controls"])


class AdminUserOut(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: Any
    wallet_balance_rupees: float


class WalletAdjustRequest(BaseModel):
    amount_rupees: float = Field(..., description="Amount in Rupees to set or credit/debit")
    mode: str = Field("set", description="'set' to overwrite balance, or 'add' to credit balance")
    reason: Optional[str] = Field("Admin balance adjustment", description="Audit log reason")


class SystemAnalyticsOut(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    total_orders_executed: int
    total_platform_trading_volume_rupees: float
    total_demo_wallets_issued_rupees: float


class SystemOrderOut(BaseModel):
    order_id: str
    user_id: str
    user_email: str
    ticker_symbol: str
    order_type: str
    side: str
    quantity: int
    price_rupees: float
    status: str
    created_at: Any


@router.get("/analytics", response_model=SystemAnalyticsOut)
async def get_system_analytics(
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Get high-level system analytics for the SmartStock AI platform."""
    # User counts
    users_total = (await db.execute(select(func.count(User.id)))).scalar() or 0
    users_active = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar() or 0
    users_admin = (await db.execute(select(func.count(User.id)).where(User.is_admin == True))).scalar() or 0

    # Orders count
    orders_count = (await db.execute(select(func.count(Order.id)))).scalar() or 0

    # Total trading volume in rupees
    volume_paise = (await db.execute(select(func.sum(VirtualTrade.total_value_paise)))).scalar() or 0
    volume_rupees = volume_paise / 100.0

    # Total demo balances issued
    wallets_sum = (await db.execute(select(func.sum(Wallet.balance_paise)))).scalar() or 0
    wallets_rupees = wallets_sum / 100.0

    return SystemAnalyticsOut(
        total_users=users_total,
        active_users=users_active,
        admin_users=users_admin,
        total_orders_executed=orders_count,
        total_platform_trading_volume_rupees=volume_rupees,
        total_demo_wallets_issued_rupees=wallets_rupees,
    )


@router.get("/users", response_model=List[AdminUserOut])
async def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """List all registered users with wallet balance and role status."""
    stmt = select(User).order_by(desc(User.created_at)).offset(skip).limit(limit)
    res = await db.execute(stmt)
    users = res.scalars().all()

    out = []
    for u in users:
        w_stmt = select(Wallet).where(Wallet.user_id == u.id)
        w_res = await db.execute(w_stmt)
        wallet = w_res.scalar_one_or_none()
        balance_rupees = (wallet.balance_paise / 100.0) if wallet else 500.0

        out.append(
            AdminUserOut(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                is_active=u.is_active,
                is_verified=u.is_verified,
                is_admin=u.is_admin,
                created_at=u.created_at,
                wallet_balance_rupees=balance_rupees,
            )
        )
    return out


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active_status(
    user_id: str,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Toggle user active / ban status."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot ban your own admin account.")

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)

    status_str = "activated" if user.is_active else "banned"
    return {"message": f"User {user.email} has been {status_str}.", "is_active": user.is_active}


@router.post("/users/{user_id}/toggle-admin")
async def toggle_user_admin_privilege(
    user_id: str,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Grant or revoke Admin role for a target user."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot revoke admin rights from yourself.")

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_admin = not user.is_admin
    await db.commit()
    await db.refresh(user)

    role_str = "Admin" if user.is_admin else "Standard User"
    return {"message": f"User {user.email} is now an {role_str}.", "is_admin": user.is_admin}


@router.post("/users/{user_id}/adjust-wallet")
async def adjust_user_wallet_balance(
    user_id: str,
    payload: WalletAdjustRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Adjust or set demo wallet balance in Rupees for a specified user."""
    stmt = select(Wallet).where(Wallet.user_id == user_id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="User wallet not found")

    before_paise = wallet.balance_paise
    amount_paise = int(round(payload.amount_rupees * 100))

    if payload.mode == "add":
        new_paise = before_paise + amount_paise
    else:  # 'set'
        new_paise = amount_paise

    if new_paise < 0:
        raise HTTPException(status_code=400, detail="Wallet balance cannot be set below ₹0.")

    wallet.balance_paise = new_paise

    # Audit entry in WalletLedger
    ledger = WalletLedger(
        wallet_id=wallet.id,
        amount_paise=new_paise - before_paise,
        balance_before_paise=before_paise,
        balance_after_paise=new_paise,
        transaction_type="ADMIN_ADJUSTMENT",
        reference_id=f"ADMIN:{admin.id}:{payload.reason or 'Manual Credit'}",
    )
    db.add(ledger)
    await db.commit()
    await db.refresh(wallet)

    return {
        "message": f"Successfully updated wallet balance.",
        "user_id": user_id,
        "new_balance_rupees": wallet.balance_paise / 100.0,
    }


@router.get("/orders", response_model=List[SystemOrderOut])
async def list_system_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """List system-wide audit order log across all users."""
    stmt = (
        select(Order, User.email)
        .join(User, Order.user_id == User.id)
        .order_by(desc(Order.created_at))
        .offset(skip)
        .limit(limit)
    )
    res = await db.execute(stmt)
    rows = res.all()

    out = []
    for order, email in rows:
        out.append(
            SystemOrderOut(
                order_id=order.id,
                user_id=order.user_id,
                user_email=email,
                ticker_symbol=order.ticker_symbol,
                order_type=order.order_type,
                side=order.side,
                quantity=order.quantity,
                price_rupees=order.price_paise / 100.0,
                status=order.status,
                created_at=order.created_at,
            )
        )
    return out

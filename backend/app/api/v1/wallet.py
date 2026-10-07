from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.session import get_async_db
from app.models.user import User, Wallet, WalletLedger
from app.schemas.trading import WalletLedgerOut

router = APIRouter(prefix="/wallet", tags=["Wallet & Ledger Accounting"])


@router.get("/balance")
async def get_wallet_balance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    stmt = select(Wallet).where(Wallet.user_id == current_user.id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()

    balance_paise = wallet.balance_paise if wallet else 50000

    return {
        "user_id": current_user.id,
        "balance_paise": balance_paise,
        "balance_rupees": round(balance_paise / 100.0, 2),
        "currency": wallet.currency if wallet else "INR",
    }


@router.get("/ledger", response_model=List[WalletLedgerOut])
async def get_wallet_ledger(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    wallet_res = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = wallet_res.scalar_one_or_none()

    if not wallet:
        return []

    stmt = select(WalletLedger).where(WalletLedger.wallet_id == wallet.id).order_by(WalletLedger.created_at.desc())
    res = await db.execute(stmt)
    entries = res.scalars().all()

    return [
        WalletLedgerOut(
            id=entry.id,
            amount_paise=entry.amount_paise,
            amount_rupees=round(entry.amount_paise / 100.0, 2),
            balance_before_paise=entry.balance_before_paise,
            balance_before_rupees=round(entry.balance_before_paise / 100.0, 2),
            balance_after_paise=entry.balance_after_paise,
            balance_after_rupees=round(entry.balance_after_paise / 100.0, 2),
            transaction_type=entry.transaction_type,
            reference_id=entry.reference_id,
            created_at=entry.created_at,
        )
        for entry in entries
    ]

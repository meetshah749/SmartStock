import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import AsyncSessionLocal, async_engine, Base
import app.models
from app.models.user import User, Wallet, WalletLedger
from app.core.security import get_password_hash
from app.core.config import settings
from sqlalchemy import select

async def seed_users():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if users already exist
        demo_emails = ["admin@smartstock.com", "demo@smartstock.com"]
        for email in demo_emails:
            res = await db.execute(select(User).where(User.email == email))
            existing = res.scalar_one_or_none()
            if existing:
                print(f"User {email} already exists.")
                continue

            is_admin = (email == "admin@smartstock.com")
            full_name = "SmartStock Admin" if is_admin else "Demo Trader"
            password = "admin123456" if is_admin else "demo123456"

            user = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name=full_name,
                is_active=True,
                is_verified=True,
                is_admin=is_admin
            )
            db.add(user)
            await db.flush()

            default_balance = 5000000 if is_admin else settings.DEFAULT_VIRTUAL_BALANCE_PAISE # Rs 50,000 for admin, Rs 500 for demo
            wallet = Wallet(
                user_id=user.id,
                balance_paise=default_balance,
                currency="INR"
            )
            db.add(wallet)
            await db.flush()

            ledger = WalletLedger(
                wallet_id=wallet.id,
                amount_paise=default_balance,
                balance_before_paise=0,
                balance_after_paise=default_balance,
                transaction_type="DEMO_CREDIT",
                reference_id="SEED_INIT"
            )
            db.add(ledger)
            await db.commit()
            print(f"[OK] Created {'ADMIN' if is_admin else 'USER'}: {email} with password: {password}")

if __name__ == "__main__":
    asyncio.run(seed_users())

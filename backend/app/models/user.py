from typing import Optional, List
from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    profile: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    onboarding: Mapped[Optional["OnboardingAnswer"]] = relationship("OnboardingAnswer", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Wallet(BaseModel):
    __tablename__ = "wallets"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance_paise: Mapped[int] = mapped_column(BigInteger, default=50000, nullable=False)  # ₹500.00
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="wallet")
    ledger: Mapped[List["WalletLedger"]] = relationship("WalletLedger", back_populates="wallet", cascade="all, delete-orphan")


class WalletLedger(BaseModel):
    __tablename__ = "wallet_ledger"

    wallet_id: Mapped[str] = mapped_column(String(36), ForeignKey("wallets.id", ondelete="CASCADE"), index=True, nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_before_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_after_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # DEMO_CREDIT, VIRTUAL_BUY, VIRTUAL_SELL, PAYMENT_DEPOSIT
    reference_id: Mapped[str] = mapped_column(String(255), nullable=True)

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="ledger")

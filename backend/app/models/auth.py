import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Role(BaseModel):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)


class UserRole(BaseModel):
    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EmailVerification(BaseModel):
    __tablename__ = "email_verifications"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class PasswordResetToken(BaseModel):
    __tablename__ = "password_reset_tokens"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class UserProfile(BaseModel):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    date_of_birth: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    experience_level: Mapped[str] = mapped_column(String(50), default="beginner", nullable=False)  # beginner, intermediate, advanced
    preferred_market: Mapped[str] = mapped_column(String(50), default="NSE", nullable=False)
    investment_horizon: Mapped[Optional[str]] = mapped_column(String(50), default="3-5 Years", nullable=True)
    risk_category: Mapped[Optional[str]] = mapped_column(String(50), default="BALANCED", nullable=True)  # CONSERVATIVE, BALANCED, AGGRESSIVE
    risk_score: Mapped[Optional[int]] = mapped_column(BigInteger, default=15, nullable=True)
    investment_experience: Mapped[Optional[str]] = mapped_column(String(50), default="INTERMEDIATE", nullable=True)
    investment_style: Mapped[Optional[str]] = mapped_column(String(50), default="GROWTH", nullable=True)
    knowledge_level: Mapped[Optional[str]] = mapped_column(String(50), default="INTERMEDIATE", nullable=True)
    investment_goals: Mapped[Optional[str]] = mapped_column(String(255), default="Wealth Creation & Strategy Practice", nullable=True)
    preferred_sectors: Mapped[Optional[str]] = mapped_column(String(255), default="Technology, Banking, Energy", nullable=True)
    expected_investment_range: Mapped[Optional[str]] = mapped_column(String(50), default="₹1L - ₹5L", nullable=True)
    max_drawdown_preference: Mapped[Optional[str]] = mapped_column(String(50), default="10% - 20%", nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class OnboardingAnswer(BaseModel):
    __tablename__ = "onboarding_answers"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    date_of_birth: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    experience_level: Mapped[str] = mapped_column(String(50), nullable=False)
    knowledge_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    investment_horizon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    investment_style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    trading_goals: Mapped[str] = mapped_column(String(255), nullable=False)
    risk_tolerance: Mapped[str] = mapped_column(String(50), nullable=False)
    preferred_sectors: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expected_investment_range: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    max_drawdown_preference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    calculated_risk_category: Mapped[str] = mapped_column(String(50), default="BALANCED", nullable=False)
    calculated_risk_score: Mapped[Optional[int]] = mapped_column(BigInteger, default=15, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="onboarding")


class ConsentRecord(BaseModel):
    __tablename__ = "consent_records"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    terms_of_service: Mapped[bool] = mapped_column(Boolean, nullable=False)
    privacy_policy: Mapped[bool] = mapped_column(Boolean, nullable=False)
    risk_disclaimer: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)

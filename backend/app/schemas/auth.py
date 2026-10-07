from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    full_name: str = Field(..., min_length=2, max_length=100)
    terms_of_service: bool = Field(..., description="Consent to Terms of Service")
    privacy_policy: bool = Field(..., description="Consent to Privacy Policy")
    risk_disclaimer: bool = Field(..., description="Acknowledgement of Risk Disclaimer")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    is_verified: bool
    is_admin: bool = False
    created_at: datetime
    wallet_balance_paise: int = 50000
    wallet_balance_rupees: float = 500.00


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut
    email_status: Optional[str] = "not_configured"
    dev_verification_code: Optional[str] = None
    dev_verification_token: Optional[str] = None
    message: Optional[str] = None


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: Optional[str] = Field(None, description="6-digit verification code")
    token: Optional[str] = Field(None, description="Verification token")


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    experience_level: Optional[str] = "beginner"
    preferred_market: Optional[str] = "NSE"
    investment_horizon: Optional[str] = None
    investment_style: Optional[str] = None
    knowledge_level: Optional[str] = None
    investment_goals: Optional[str] = None
    preferred_sectors: Optional[str] = None
    expected_investment_range: Optional[str] = None
    max_drawdown_preference: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_verified: bool = False
    phone_number: Optional[str] = None
    phone_verified: bool = False
    date_of_birth: Optional[str] = None
    experience_level: str = "beginner"
    preferred_market: str = "NSE"
    investment_horizon: Optional[str] = "3-5 Years"
    risk_category: str = "BALANCED"
    risk_score: int = 15
    investment_experience: Optional[str] = "INTERMEDIATE"
    investment_style: Optional[str] = "GROWTH"
    knowledge_level: Optional[str] = "INTERMEDIATE"
    investment_goals: Optional[str] = "Wealth Creation & Strategy Practice"
    preferred_sectors: Optional[str] = "Technology, Banking, Energy"
    expected_investment_range: Optional[str] = "₹1L - ₹5L"
    max_drawdown_preference: Optional[str] = "10% - 20%"
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class OnboardingCreate(BaseModel):
    date_of_birth: Optional[str] = Field(None, description="YYYY-MM-DD")
    experience_level: str = Field("beginner", description="beginner, intermediate, or advanced")
    knowledge_level: Optional[str] = Field("INTERMEDIATE", description="BASIC, INTERMEDIATE, ADVANCED")
    investment_horizon: Optional[str] = Field("3-5 Years", description="SHORT_TERM, 1-3 Years, 3-5 Years, 5+ Years")
    investment_style: Optional[str] = Field("GROWTH", description="GROWTH, VALUE, INDEX, MOMENTUM")
    trading_goals: str = Field(..., description="Primary goals e.g. Wealth Creation, Capital Preservation, Speculation")
    risk_tolerance: str = Field(..., description="low/conservative, medium/balanced, or high/aggressive")
    preferred_sectors: Optional[str] = Field("Technology, Banking, Energy", description="Comma-separated sectors")
    expected_investment_range: Optional[str] = Field("₹1L - ₹5L", description="Allocation range")
    max_drawdown_preference: Optional[str] = Field("10% - 20%", description="Maximum acceptable drawdown")


class OnboardingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    date_of_birth: Optional[str] = None
    experience_level: str
    knowledge_level: Optional[str] = None
    investment_horizon: Optional[str] = None
    investment_style: Optional[str] = None
    trading_goals: str
    risk_tolerance: str
    preferred_sectors: Optional[str] = None
    expected_investment_range: Optional[str] = None
    max_drawdown_preference: Optional[str] = None
    calculated_risk_category: str
    calculated_risk_score: int
    completed_at: datetime


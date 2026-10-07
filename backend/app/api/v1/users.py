from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.session import get_async_db
from app.models.user import User, Wallet
from app.models.auth import UserProfile
from app.schemas.auth import UserOut, UserProfileOut, UserProfileUpdate

router = APIRouter(prefix="/users", tags=["Users & Profile"])


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    # Fetch wallet balance
    stmt = select(Wallet).where(Wallet.user_id == current_user.id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    balance = wallet.balance_paise if wallet else 50000

    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        wallet_balance_paise=balance,
        wallet_balance_rupees=balance / 100.0,
    )


@router.get("/me/profile", response_model=UserProfileOut)
async def get_profile_details(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()

    if not profile:
        profile = UserProfile(
            user_id=current_user.id,
            experience_level="beginner",
            preferred_market="NSE",
            risk_category="BALANCED",
            risk_score=15,
            investment_horizon="3-5 Years",
            investment_experience="INTERMEDIATE",
            investment_style="GROWTH",
            knowledge_level="INTERMEDIATE",
            investment_goals="Wealth Creation & Strategy Practice",
            preferred_sectors="Technology, Banking, Energy",
            expected_investment_range="₹1L - ₹5L",
            max_drawdown_preference="10% - 20%",
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return UserProfileOut(
        user_id=profile.user_id,
        full_name=current_user.full_name,
        email=current_user.email,
        is_verified=current_user.is_verified,
        phone_number=profile.phone_number,
        phone_verified=profile.phone_verified,
        date_of_birth=profile.date_of_birth,
        experience_level=profile.experience_level or "beginner",
        preferred_market=profile.preferred_market or "NSE",
        investment_horizon=profile.investment_horizon or "3-5 Years",
        risk_category=profile.risk_category or "BALANCED",
        risk_score=profile.risk_score or 15,
        investment_experience=profile.investment_experience or profile.experience_level or "INTERMEDIATE",
        investment_style=profile.investment_style or "GROWTH",
        knowledge_level=profile.knowledge_level or "INTERMEDIATE",
        investment_goals=profile.investment_goals or "Wealth Creation & Strategy Practice",
        preferred_sectors=profile.preferred_sectors or "Technology, Banking, Energy",
        expected_investment_range=profile.expected_investment_range or "₹1L - ₹5L",
        max_drawdown_preference=profile.max_drawdown_preference or "10% - 20%",
        avatar_url=profile.avatar_url,
        bio=profile.bio,
    )


@router.put("/me/profile", response_model=UserProfileOut)
async def update_profile_details(
    update_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if update_data.full_name is not None and update_data.full_name.strip():
        current_user.full_name = update_data.full_name.strip()
    if update_data.phone_number is not None:
        profile.phone_number = update_data.phone_number.strip()
    if update_data.date_of_birth is not None:
        profile.date_of_birth = update_data.date_of_birth
    if update_data.experience_level is not None:
        profile.experience_level = update_data.experience_level
        profile.investment_experience = update_data.experience_level
    if update_data.preferred_market is not None:
        profile.preferred_market = update_data.preferred_market
    if update_data.investment_horizon is not None:
        profile.investment_horizon = update_data.investment_horizon
    if update_data.investment_style is not None:
        profile.investment_style = update_data.investment_style
    if update_data.knowledge_level is not None:
        profile.knowledge_level = update_data.knowledge_level
    if update_data.investment_goals is not None:
        profile.investment_goals = update_data.investment_goals
    if update_data.preferred_sectors is not None:
        profile.preferred_sectors = update_data.preferred_sectors
    if update_data.expected_investment_range is not None:
        profile.expected_investment_range = update_data.expected_investment_range
    if update_data.max_drawdown_preference is not None:
        profile.max_drawdown_preference = update_data.max_drawdown_preference
    if update_data.avatar_url is not None:
        profile.avatar_url = update_data.avatar_url
    if update_data.bio is not None:
        profile.bio = update_data.bio

    await db.commit()
    await db.refresh(profile)
    await db.refresh(current_user)

    return UserProfileOut(
        user_id=profile.user_id,
        full_name=current_user.full_name,
        email=current_user.email,
        is_verified=current_user.is_verified,
        phone_number=profile.phone_number,
        phone_verified=profile.phone_verified,
        date_of_birth=profile.date_of_birth,
        experience_level=profile.experience_level or "beginner",
        preferred_market=profile.preferred_market or "NSE",
        investment_horizon=profile.investment_horizon or "3-5 Years",
        risk_category=profile.risk_category or "BALANCED",
        risk_score=profile.risk_score or 15,
        investment_experience=profile.investment_experience or "INTERMEDIATE",
        investment_style=profile.investment_style or "GROWTH",
        knowledge_level=profile.knowledge_level or "INTERMEDIATE",
        investment_goals=profile.investment_goals or "Wealth Creation & Strategy Practice",
        preferred_sectors=profile.preferred_sectors or "Technology, Banking, Energy",
        expected_investment_range=profile.expected_investment_range or "₹1L - ₹5L",
        max_drawdown_preference=profile.max_drawdown_preference or "10% - 20%",
        avatar_url=profile.avatar_url,
        bio=profile.bio,
    )

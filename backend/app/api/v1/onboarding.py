from typing import Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.session import get_async_db
from app.models.user import User
from app.models.auth import OnboardingAnswer, UserProfile
from app.schemas.auth import OnboardingCreate, OnboardingOut
from app.services.risk_service import calculate_investor_risk_profile

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post("", response_model=OnboardingOut, status_code=status.HTTP_201_CREATED)
async def record_onboarding_answers(
    answers: OnboardingCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    # 1. Server-side risk evaluation
    risk_cat, risk_score, breakdown = calculate_investor_risk_profile(answers)

    # 2. Update or insert OnboardingAnswer
    stmt = select(OnboardingAnswer).where(OnboardingAnswer.user_id == current_user.id)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        existing.date_of_birth = answers.date_of_birth
        existing.experience_level = answers.experience_level
        existing.knowledge_level = answers.knowledge_level
        existing.investment_horizon = answers.investment_horizon
        existing.investment_style = answers.investment_style
        existing.trading_goals = answers.trading_goals
        existing.risk_tolerance = answers.risk_tolerance
        existing.preferred_sectors = answers.preferred_sectors
        existing.expected_investment_range = answers.expected_investment_range
        existing.max_drawdown_preference = answers.max_drawdown_preference
        existing.calculated_risk_category = risk_cat
        existing.calculated_risk_score = risk_score
        existing.completed_at = datetime.now(timezone.utc)
        onboarding_record = existing
    else:
        onboarding_record = OnboardingAnswer(
            user_id=current_user.id,
            date_of_birth=answers.date_of_birth,
            experience_level=answers.experience_level,
            knowledge_level=answers.knowledge_level,
            investment_horizon=answers.investment_horizon,
            investment_style=answers.investment_style,
            trading_goals=answers.trading_goals,
            risk_tolerance=answers.risk_tolerance,
            preferred_sectors=answers.preferred_sectors,
            expected_investment_range=answers.expected_investment_range,
            max_drawdown_preference=answers.max_drawdown_preference,
            calculated_risk_category=risk_cat,
            calculated_risk_score=risk_score,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(onboarding_record)

    # 3. Synchronize UserProfile with Investor Preferences
    prof_stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    prof_res = await db.execute(prof_stmt)
    profile = prof_res.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    profile.date_of_birth = answers.date_of_birth
    profile.experience_level = answers.experience_level
    profile.investment_experience = answers.experience_level
    profile.investment_horizon = answers.investment_horizon
    profile.risk_category = risk_cat
    profile.risk_score = risk_score
    profile.investment_style = answers.investment_style
    profile.knowledge_level = answers.knowledge_level
    profile.investment_goals = answers.trading_goals
    profile.preferred_sectors = answers.preferred_sectors
    profile.expected_investment_range = answers.expected_investment_range
    profile.max_drawdown_preference = answers.max_drawdown_preference

    await db.commit()
    await db.refresh(onboarding_record)

    return onboarding_record


@router.get("", response_model=OnboardingOut)
async def get_onboarding_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    stmt = select(OnboardingAnswer).where(OnboardingAnswer.user_id == current_user.id)
    res = await db.execute(stmt)
    onboarding = res.scalar_one_or_none()

    if not onboarding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding survey not completed yet",
        )
    return onboarding

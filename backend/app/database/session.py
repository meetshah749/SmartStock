from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings
from app.core.logging import logger

# Async Engine for FastAPI async endpoints
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync Engine for Alembic migrations and synchronous tasks
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=False,
    future=True,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def ensure_db_schema():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        profile_cols = {
            "phone_verified": "BOOLEAN DEFAULT 0",
            "date_of_birth": "VARCHAR(20)",
            "investment_horizon": "VARCHAR(50) DEFAULT '3-5 Years'",
            "risk_category": "VARCHAR(50) DEFAULT 'BALANCED'",
            "risk_score": "BIGINT DEFAULT 15",
            "investment_experience": "VARCHAR(50) DEFAULT 'INTERMEDIATE'",
            "investment_style": "VARCHAR(50) DEFAULT 'GROWTH'",
            "knowledge_level": "VARCHAR(50) DEFAULT 'INTERMEDIATE'",
            "investment_goals": "VARCHAR(255) DEFAULT 'Wealth Creation & Strategy Practice'",
            "preferred_sectors": "VARCHAR(255) DEFAULT 'Technology, Banking, Energy'",
            "expected_investment_range": "VARCHAR(50) DEFAULT '₹1L - ₹5L'",
            "max_drawdown_preference": "VARCHAR(50) DEFAULT '10% - 20%'",
        }
        onboarding_cols = {
            "date_of_birth": "VARCHAR(20)",
            "knowledge_level": "VARCHAR(50)",
            "investment_horizon": "VARCHAR(50)",
            "investment_style": "VARCHAR(50)",
            "preferred_sectors": "VARCHAR(255)",
            "expected_investment_range": "VARCHAR(50)",
            "max_drawdown_preference": "VARCHAR(50)",
            "calculated_risk_category": "VARCHAR(50) DEFAULT 'BALANCED'",
            "calculated_risk_score": "BIGINT DEFAULT 15",
        }
        for col, col_type in profile_cols.items():
            try:
                await conn.exec_driver_sql(f"ALTER TABLE user_profiles ADD COLUMN {col} {col_type}")
            except Exception:
                pass
        for col, col_type in onboarding_cols.items():
            try:
                await conn.exec_driver_sql(f"ALTER TABLE onboarding_answers ADD COLUMN {col} {col_type}")
            except Exception:
                pass


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()


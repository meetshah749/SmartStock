import pytest_asyncio
from app.database.session import async_engine, Base
import app.models  # Register all models


@pytest_asyncio.fixture(autouse=True, scope="function")
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

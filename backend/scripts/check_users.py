import sys, os, asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.database.session import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select
import app.models

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User))
        users = res.scalars().all()
        for u in users:
            print(f"{u.email}  admin={u.is_admin}  active={u.is_active}  verified={u.is_verified}")
        if not users:
            print("No users in database")

asyncio.run(check())

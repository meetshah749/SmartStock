import sys
import asyncio
from sqlalchemy import select

# Ensure parent path is in python path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import AsyncSessionLocal
from app.models.user import User


async def make_admin(email: str):
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.email == email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            print(f"[X] User with email '{email}' was not found in the database.")
            print("Please make sure the user is registered first.")
            return

        user.is_admin = True
        await db.commit()
        print(f"[OK] Success! User '{user.full_name}' ({user.email}) is now an ADMIN!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/make_admin.py <user_email>")
        sys.exit(1)

    target_email = sys.argv[1].strip()
    asyncio.run(make_admin(target_email))

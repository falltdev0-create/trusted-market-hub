import asyncio
import uuid

from passlib.context import CryptContext

from app.core.database import AsyncSessionLocal, create_tables
from app.models.models import User, UserRole, KYCStatus

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def main():
    await create_tables()

    admin_email = input("Admin email: ").strip()
    admin_password = input("Admin password: ").strip()
    full_name = input("Full name [Admin]: ").strip() or "Admin"

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.email == admin_email))
        existing = result.scalar_one_or_none()
        if existing:
            print("User already exists:", existing.email)
            return

        user = User(
            id=str(uuid.uuid4()),
            email=admin_email,
            phone="0000000000",
            password_hash=pwd.hash(admin_password),
            full_name=full_name,
            role=UserRole.admin,
            kyc_status=KYCStatus.approved,
            is_verified=True,
            is_active=True,
        )

        session.add(user)
        await session.commit()
        print("Admin user created:", admin_email)


if __name__ == "__main__":
    asyncio.run(main())

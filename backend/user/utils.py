from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import User


async def get_user_by_phone(session: AsyncSession, phone: str) -> User | None:
    stmt = select(User).where(User.phone == phone)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
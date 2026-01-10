from typing import Annotated

from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer

import jwt
from jwt.exceptions import InvalidTokenError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import User

from backend.auth.schemas import TokenData

from settings import Settings



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
settings = Settings()

async def get_user_by_phone(session: AsyncSession, phone: str) -> User | None:
    stmt = select(User).where(User.phone == phone)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: AsyncSession):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        phone = payload.get("phone")
        if phone is None:
            raise credentials_exception
        token_data = TokenData(phone=phone)
    except InvalidTokenError:
        raise credentials_exception
    user = await get_user_by_phone(session, phone=token_data.phone)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user



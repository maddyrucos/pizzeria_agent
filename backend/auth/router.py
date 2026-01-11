from typing import Annotated 

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer

from settings import settings
from backend.database import models
from backend.user.schemas import (
    UserSchema, UserCreateSchema,
)

from backend.schemas import Session
from backend.auth.schemas import Token, UserLoginSchema
from backend.auth.utils import (
    authenticate_user, create_access_token, get_password_hash,
)
from backend.user.utils import get_user_by_phone
from datetime import timedelta



router = APIRouter(
    prefix="/auth", tags=["auth"],
)


@router.post("/register", response_model=UserSchema)
async def register_user(user: Annotated[UserCreateSchema, Depends()], session: Session) -> UserSchema:
    if await get_user_by_phone(session, phone=user.phone):
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    new_user = models.User(
        name=user.name,
        phone=user.phone,
        mail=user.mail,
        password= get_password_hash(user.password),
        is_verified=True,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return UserSchema.model_validate(new_user)


@router.post("/login")
async def login_for_access_token(form_data: Annotated[UserLoginSchema, Depends()], session: Session, response: Response) -> Token:
    user = await authenticate_user(form_data.phone, form_data.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"phone": user.phone, "is_verified": user.is_verified},
        expires_delta=access_token_expires,
    )
    response.set_cookie("access_token", access_token)
    return Token(access_token=access_token, token_type="bearer")
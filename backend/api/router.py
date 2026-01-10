from fastapi import APIRouter, Depends
from typing import List, Annotated 

from backend.schemas import (
    DeliverySchema, DeliveryCreateSchema,
    BookingSchema, BookingCreateSchema,
    ItemSchema,
)

from backend.user.schemas import (
    UserSchema, UserCreateSchema
)

from backend.database import db, models

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


SESSION_DEP = Annotated[AsyncSession, Depends(db.get_session)]

api = APIRouter(
    prefix="/api", tags=["api"],
)


@api.get("/users") 
async def get_users(session: SESSION_DEP) -> List[UserSchema]:
    result = await session.execute(select(models.User))
    users = result.scalars().all()
    return [UserSchema.from_orm(user) for user in users]

@api.post("/users")
async def create_user(user: UserCreateSchema, session: SESSION_DEP) -> UserSchema:
    new_user = models.User(
        name=user.name,
        phone=user.phone,
        mail=user.mail,
        is_verified=int(user.is_verified),
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return UserSchema.model_validate(new_user)


@api.get("/menu")
async def get_menu(session: SESSION_DEP) -> List[ItemSchema]:
    items = await session.execute(select(models.ItemSchema)).scalars().all()
    if items:
        return [ItemSchema(name=item.name, description=item.description, price=str(item.price)) for item in items]
    return []


@api.get("/deliveries") 
async def get_deliveries() -> List[DeliverySchema]:
    return []

@api.post("/deliveries", response_model=DeliverySchema)
async def create_delivery(delivery: DeliveryCreateSchema) -> DeliverySchema:
    return DeliverySchema(id=1, **delivery.dict())



@api.get("/bookings") 
async def get_bookings() -> List[BookingSchema]:
    return []   

@api.post("/bookings", response_model=BookingSchema)
async def create_booking(booking: BookingCreateSchema) -> BookingSchema:
    return BookingSchema(id=1, **booking.dict())

from pydantic import BaseModel
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import db    
    
    
    
class BookingCreateSchema(BaseModel):
    user_id: int
    time: str

    model_config = {"from_attributes": True}
        
class BookingSchema(BookingCreateSchema):
    id: int
       
        
          
class DeliveryCreateSchema(BaseModel):
    user_id: int
    address: str
    cart_id: int
    time: str
    status: str

    model_config = {"from_attributes": True}
        
class DeliverySchema(DeliveryCreateSchema):
    id: int        
        
        
class ItemSchema(BaseModel):
    name: str
    description: str
    price: str  
    
Session = Annotated[AsyncSession, Depends(db.get_session)]
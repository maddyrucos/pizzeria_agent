from pydantic import BaseModel
from typing import Optional

class UserAgentRequest(BaseModel):
    chat_id: Optional[int]
    message: list
    user_id: str
        
        
class UserAgentResponse(BaseModel):
    status_code: int
    response: str
        
        
class UserCreateSchema(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    mail: Optional[str] = None
    is_verified: bool = False

    model_config = {"from_attributes": True}
    
class UserSchema(UserCreateSchema):
    id: int
    
 
class UserAgentRequest(BaseModel):
    user_id: int
    chat_id: Optional[int] = None
    message: list[str]
    
    
    
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
        
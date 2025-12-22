from pydantic import BaseModel
        
class UserCreateSchema(BaseModel):
    name: str
    
    class Config:
        orm_mode = True
    
class UserSchema(UserCreateSchema):
    id: int
    
    
    
class BookingCreateSchema(BaseModel):
    user_id: int
    time: str

    class Config:
        orm_mode = True
        
class BookingSchema(BookingCreateSchema):
    id: int
       
        
          
class DeliveryCreateSchema(BaseModel):
    address: str
    status: str

    class Config:
        orm_mode = True
        
class DeliverySchema(DeliveryCreateSchema):
    id: int        
        
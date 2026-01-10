from pydantic import BaseModel

class BaseUserSchema(BaseModel):
    name: str = None
    phone: str = None
    mail: str = None
    is_verified: bool = False

    model_config = {"from_attributes": True}
    
class UserSchema(BaseUserSchema):
    id: int
    
class UserCreateSchema(BaseUserSchema):
    password: str = None
    
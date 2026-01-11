from pydantic import BaseModel
from typing import Optional

class BaseUserSchema(BaseModel):
    name: Optional[str] = None
    phone: str = None
    mail: Optional[str] = None

    model_config = {"from_attributes": True}
    
class UserSchema(BaseUserSchema):
    id: int
    is_verified: int = 0
    
class UserCreateSchema(BaseUserSchema):
    password: str = None
    
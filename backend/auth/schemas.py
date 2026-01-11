from pydantic import BaseModel
    
class UserLoginSchema(BaseModel):
    phone: str
    password: str    
    
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    phone: str | None = None
    is_verified: bool = False
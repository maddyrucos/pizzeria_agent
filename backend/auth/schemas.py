from pydantic import BaseModel
    
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    phone: str | None = None
    is_verified: bool = False
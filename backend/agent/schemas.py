from pydantic import BaseModel
from typing import Optional

class UserAgentRequest(BaseModel):
    chat_id: Optional[int]
    message: list
    user_id: str
        
        
class UserAgentResponse(BaseModel):
    status_code: int
    response: str

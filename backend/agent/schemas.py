from pydantic import BaseModel
from typing import Optional

class UserAgentRequest(BaseModel):
    message: str
    chat_id: Optional[int] = None
        
        
class UserAgentResponse(BaseModel):
    status_code: int
    chat_id: int
    response: str
    messages: list
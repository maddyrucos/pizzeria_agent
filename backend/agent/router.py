from fastapi import APIRouter, Depends, Request
from typing import List, Annotated 

from backend.schemas import UserAgentRequest, UserAgentResponse

from langchain_core.messages import HumanMessage, AIMessage
from agent.main import build_app

from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import db

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address



SESSION_DEP = Annotated[AsyncSession, Depends(db.get_session)]

limiter = Limiter(key_func=get_remote_address)

agent = APIRouter(
    prefix="/agent", tags=["agent"],
)

CHATS = {} # Временное хранилище

@agent.post('/')
@limiter.limit("5/minute")
async def agent_endpoint(request: Request, payload: UserAgentRequest, session: SESSION_DEP) -> UserAgentResponse:
    user_id = payload.user_id
    state = CHATS.get(user_id, {"messages": []})

    state = await build_app().ainvoke({"messages": state["messages"] + [HumanMessage(content=msg) for msg in payload.message]}, config=None)

    CHATS[user_id] = state

    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage):
        return {"status_code": 200, "response": last_message.content}
    else:
        return {"status_code": 200, "response": "No response from agent."}

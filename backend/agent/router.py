from fastapi import APIRouter, Depends
from typing import List, Annotated 

from backend.schemas import UserAgentRequest, UserAgentResponse

from langchain_core.messages import HumanMessage, AIMessage
from agent.main import build_app

from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import db

SESSION_DEP = Annotated[AsyncSession, Depends(db.get_session)]

agent = APIRouter(
    prefix="/agent", tags=["agent"],
)

CHATS = {} # Временное хранилище

@agent.post('/')
async def agent_endpoint(request: UserAgentRequest) -> UserAgentResponse:
    user_id = request.user_id
    state = CHATS.get(user_id, {"messages": []})

    state = await build_app().ainvoke({"messages": state["messages"] + [HumanMessage(content=msg) for msg in request.message]}, config=None)

    CHATS[user_id] = state

    last_message = state["messages"][-1]
    try:
        if isinstance(last_message, AIMessage):
            return {"status_code": 200, "response": last_message.content}
        else:
            return {"status_code": 200, "response": "No response from agent."}
    except Exception as e:
        return {"status_code": 500, "response": e.args}
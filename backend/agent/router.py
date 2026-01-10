from fastapi import APIRouter, Depends, Request
from typing import Optional, Annotated 

from backend.agent.schemas import (
    UserAgentRequest, UserAgentResponse
)

from langchain_core.messages import HumanMessage, AIMessage
from agent.main import build_app

from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import db, models
from sqlalchemy.future import select

from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.agent.serizalizer import Serializer



SESSION_DEP = Annotated[AsyncSession, Depends(db.get_session)]
SERIALIZER = Serializer()

limiter = Limiter(key_func=get_remote_address)

agent = APIRouter(
    prefix="/agent", tags=["agent"],
)


@agent.post("/")
@limiter.limit("5/minute")
async def agent_endpoint(
    request: Request,
    payload: UserAgentRequest,
    session: SESSION_DEP,
) -> UserAgentResponse:
    user_id = int(payload.user_id)
    chat_id: Optional[int] = getattr(payload, "chat_id", None)

    if chat_id is None:
        chat = models.Chat(user_id=user_id, messages="")
        session.add(chat)
        await session.flush()
        chat_id = chat.id
        history_messages: list = []
    else:
        res = await session.execute(
            select(models.Chat).where(models.Chat.id == chat_id, models.Chat.user_id == user_id)
        )
        chat = res.scalar_one_or_none()
        if chat is None:
            return {"status_code": 404, "chat_id": chat_id, "response": "Chat not found."}

        history_messages = SERIALIZER.deserialize_messages(chat.messages)

    incoming = [HumanMessage(content=m) for m in payload.message]
    
    history = history_messages + incoming

    state = await build_app().ainvoke(
        {"messages": history + incoming},
        config=None,
    )

    chat.messages = SERIALIZER.serialize_messages(state["messages"])
    await session.commit()

    last_message = state["messages"][-1] if state.get("messages") else None
    if isinstance(last_message, AIMessage):
        return {"status_code": 200, "chat_id": chat_id, "response": last_message.content}
    return {"status_code": 200, "chat_id": chat_id, "response": "No response from agent."}
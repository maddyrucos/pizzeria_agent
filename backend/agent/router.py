from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Optional, Annotated 

from langchain_core.messages import HumanMessage, AIMessage
from agent.main import build_app

from sqlalchemy.future import select

from backend.agent.schemas import UserAgentRequest, UserAgentResponse
from backend.auth.utils import jwt_required
from backend.user.utils import get_user_by_phone
from backend.agent.utils import fetch_chat_messages_langchain, fetch_chat_messages_raw
from backend.schemas import Session
from backend.database import models

from slowapi import Limiter
from slowapi.util import get_remote_address

import logging



limiter = Limiter(key_func=get_remote_address)

agent = APIRouter(
    prefix="/agent", tags=["agent"],
)

@agent.post("/")
@limiter.limit("5/minute")
async def agent_endpoint(
    request: Request,
    payload: Annotated[UserAgentRequest, Depends()],
    session: Session,
    jwt_payload: Annotated[dict, Depends(jwt_required)],
) -> UserAgentResponse:
    user = await get_user_by_phone(session, phone=jwt_payload.get("phone"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user_id = user.id
    chat_id: Optional[int] = getattr(payload, "chat_id", None)

    if chat_id is None:
        chat = models.Chat(user_id=user_id)
        session.add(chat)
        await session.flush()
        chat_id = chat.id
    else:
        res = await session.execute(
            select(models.Chat).where(models.Chat.id == chat_id, models.Chat.user_id == user_id)
        )
        chat = res.scalar_one_or_none()
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found.")

    session.add(
        models.ChatMessage(
            chat_id=chat_id,
            role=models.MessageRole.USER,
            content=payload.message,
        )
    )
    await session.flush()

    history = await fetch_chat_messages_langchain(session, chat_id)

    try:
        state = await build_app().ainvoke({"messages": history}, config=None)
    except Exception as e:
        logging.error(f"Agent processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent processing failed.")

    messages = state.get("messages") or []
    last_message = messages[-1] if messages else None

    new_messages = messages[len(history):] if len(messages) >= len(history) else messages
    for msg in new_messages:
        if isinstance(msg, HumanMessage):
            role = models.MessageRole.USER
            content = msg.content
        elif isinstance(msg, AIMessage):
            role = models.MessageRole.AI
            content = msg.content
        else:
            logging.info(f"Skipping unsupported message type: {msg!r}")
            continue

        session.add(
            models.ChatMessage(
                chat_id=chat_id,
                role=role,
                content=content,
            )
        )

    await session.commit()

    full_chat = await fetch_chat_messages_raw(session, chat_id)

    return {
        "status_code": 200,
        "chat_id": chat_id,
        "response": last_message.content if isinstance(last_message, AIMessage) else "No response from agent.",
        "messages": full_chat,
    }
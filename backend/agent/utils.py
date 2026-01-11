from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy import select
from typing import Any

from sqlalchemy import select

from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import models

async def fetch_chat_messages_raw(
    session: AsyncSession,
    chat_id: int,
) -> list[dict[str, Any]]:
    res = await session.execute(
        select(
            models.ChatMessage.role,
            models.ChatMessage.content,
            models.ChatMessage.created_at,
        )
        .where(models.ChatMessage.chat_id == chat_id)
        .order_by(models.ChatMessage.created_at.asc(), models.ChatMessage.id.asc())
    )
    rows = res.all()

    return [
        {
            "role": role.value if hasattr(role, "value") else str(role),
            "content": content,
            "created_at": created_at.isoformat() if created_at else None,
        }
        for role, content, created_at in rows if content
    ]


async def fetch_chat_messages_langchain(
    session: AsyncSession,
    chat_id: int,
) -> list:
    res = await session.execute(
        select(models.ChatMessage.role, models.ChatMessage.content)
        .where(models.ChatMessage.chat_id == chat_id)
        .order_by(models.ChatMessage.created_at.asc(), models.ChatMessage.id.asc())
    )
    rows = res.all()

    out = []
    for role, content in rows:
        if role == models.MessageRole.USER:
            out.append(HumanMessage(content=content))
        elif role == models.MessageRole.AI:
            out.append(AIMessage(content=content))
        else:
            continue
    return out
from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base

from datetime import datetime
from typing import List
from enum import Enum

Base = declarative_base()

class MessageRole(str, Enum):
    USER = "user"
    AI = "ai"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone = Column(String)
    mail = Column(String)
    password = Column(String)
    is_verified = Column(Integer)  # 0 or 1 for False/True
    
    
class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="chat",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(ChatMessage.created_at, ChatMessage.id)",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="message_role"),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    chat: Mapped[Chat] = relationship("Chat", back_populates="messages")
    
    
class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    address = Column(String)
    status = Column(String)
    cart_id = Column(Integer)
    time = Column(String)
    
    
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    price = Column(Integer)    
    
    
class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    items = Column(String)
    
    
    
class ItemCart(Base):
    __tablename__ = "item_carts"
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer)
    item_id = Column(Integer)
    quantity = Column(Integer)
    
    
class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    time = Column(String)
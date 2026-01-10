from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone = Column(String)
    mail = Column(String)
    password_hash = Column(String)
    is_verified = Column(Integer)  # 0 or 1 for False/True
    
    
class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    messages = Column(MutableList.as_mutable(JSONB), nullable=False, default=list)
    
    
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
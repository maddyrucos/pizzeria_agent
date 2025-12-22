from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    
class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    time = Column(String)
    
    
class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True)
    address = Column(String)
    status = Column(String)
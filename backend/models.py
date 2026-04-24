from sqlalchemy import Column, String, Integer, DateTime, Float, Text, Boolean
from sqlalchemy.sql import func
from database import Base
import uuid


class CallSession(Base):
    __tablename__ = "call_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    call_sid = Column(String, unique=True, index=True)
    phone_number = Column(String)
    language = Column(String, default="en-IN")
    sentiment_score = Column(Float, default=0.5)
    neg_streak = Column(Integer, default=0)
    status = Column(String, default="active")  # active | completed | escalated
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    call_sid = Column(String, index=True)
    phone_number = Column(String)
    item_name = Column(String)
    quantity = Column(Integer, default=1)
    delivery_address = Column(Text)
    language = Column(String)
    raw_transcript = Column(Text)
    confirmed = Column(Boolean, default=False)
    whatsapp_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class TranscriptEntry(Base):
    __tablename__ = "transcript_entries"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    call_sid = Column(String, index=True)
    role = Column(String)  # customer | bot
    text = Column(Text)
    language = Column(String)
    sentiment = Column(String, default="NEUTRAL")
    created_at = Column(DateTime, default=func.now())

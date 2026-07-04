"""Agent log model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from app.database import Base


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    agent_name = Column(String(50), nullable=False)
    input_snapshot = Column(Text)
    output_snapshot = Column(Text)
    confidence = Column(Float)
    latency_ms = Column(Integer)
    tokens_used = Column(Integer)
    model_name = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

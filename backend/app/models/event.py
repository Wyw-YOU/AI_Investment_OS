"""Market event and alert models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class MarketEvent(Base):
    __tablename__ = "market_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    event_type = Column(String(20), nullable=False)
    title = Column(String(200))
    content = Column(Text)
    impact_score = Column(Float, default=0.0)
    source = Column(String(100))
    event_time = Column(DateTime)
    created_at = Column(DateTime, default=_utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    stock_code = Column(String(10), nullable=False)
    alert_type = Column(String(30), nullable=False)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

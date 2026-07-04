"""Portfolio model."""
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from app.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    holdings = Column(Text, default="{}")
    candidate_pool = Column(Text, default="[]")
    risk_score = Column(Float, default=0.0)
    expected_return = Column(Float, default=0.0)
    sector_exposure = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

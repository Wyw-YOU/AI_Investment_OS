"""Stock state model."""
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime
from app.database import Base


class StockState(Base):
    __tablename__ = "stock_state"

    stock_code = Column(String(10), primary_key=True)
    latest_price = Column(Float)
    market_cap = Column(Float)
    sector = Column(String(50))
    last_analysis = Column(Text, default="{}")
    last_analysis_at = Column(DateTime)
    score = Column(Float, default=0.0)
    score_change = Column(Float, default=0.0)
    alert_level = Column(String(20), default="NORMAL")

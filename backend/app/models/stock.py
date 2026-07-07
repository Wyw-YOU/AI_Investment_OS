"""
股票相关的 SQLAlchemy ORM 模型。
Stock：股票基础信息表（代码、名称、行业等）
StockSnapshot：行情快照表（价格、成交量、估值等，用于历史回溯）
"""

import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Stock(Base):
    """股票基础信息，stock_code 唯一索引，用于去重。"""
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), default="")
    market: Mapped[str] = mapped_column(String(10), default="A")
    industry: Mapped[str] = mapped_column(String(100), default="")
    sector: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class StockSnapshot(Base):
    """行情快照，每次采集记录一条，用于绘制历史估值曲线等场景。"""
    __tablename__ = "stock_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20), index=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    volume: Mapped[float] = mapped_column(Float, default=0.0)
    market_cap: Mapped[float] = mapped_column(Float, default=0.0)
    pe: Mapped[float] = mapped_column(Float, default=0.0)
    pb: Mapped[float] = mapped_column(Float, default=0.0)
    roe: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

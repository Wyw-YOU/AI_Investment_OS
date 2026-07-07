"""
用户 ORM 模型。
密码以 bcrypt 哈希存储（hashed_password 字段），永不存储明文。
role 字段预留权限扩展（当前默认 "user"）。
"""

import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

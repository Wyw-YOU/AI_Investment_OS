"""
SQLAlchemy 异步数据库配置。

async_session 是独立于请求的 session 工厂，供后台任务（如 _run_analysis_background）
直接使用，不依赖 FastAPI 的 Depends 注入。
get_db 是请求级别的 session，通过 yield 实现自动 commit/rollback。
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

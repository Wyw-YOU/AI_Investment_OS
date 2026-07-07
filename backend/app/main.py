"""
FastAPI 应用入口。

启动时自动建表（init_db），运行时 CORS 允许前端跨域访问。
CORS origins 从 .env 的 CORS_ORIGINS 读取，Docker 部署时通过 Next.js rewrite
代理 API 请求，浏览器端不触发跨域，此配置仅影响本地开发环境。
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.agent import router as agent_router
from app.api.stocks import router as stocks_router
from app.api.workspace import router as workspace_router
from app.config import get_settings
from app.core.exceptions import AppException
from app.database import init_db

settings = get_settings()

app = FastAPI(title="AI Investment OS", version="1.0.0")

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(stocks_router)
app.include_router(workspace_router)
app.include_router(agent_router)


@app.on_event("startup")
async def startup():
    os.makedirs("data", exist_ok=True)
    await init_db()
    await _ensure_admin_user()


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


async def _ensure_admin_user():
    """启动时自动创建默认管理员账户（如不存在）。"""
    from sqlalchemy import select
    from app.core.security import hash_password
    from app.database import async_session
    from app.models.user import User

    admin_email = "admin@aiios.com"
    admin_password = "admin123456"

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == admin_email))
        if result.scalar_one_or_none() is None:
            admin = User(
                email=admin_email,
                hashed_password=hash_password(admin_password),
                role="admin",
            )
            db.add(admin)
            await db.commit()


@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message, "data": None},
    )

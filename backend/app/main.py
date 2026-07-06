import json
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


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message, "data": None},
    )

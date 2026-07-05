from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import warnings

from app.config import settings
from app.core.logging import setup_logging
from app.core.rate_limit import rate_limit_middleware
from app.api import stocks, portfolio, alerts, auth
from app.services.websocket_manager import ws_manager

if settings.jwt_secret == "change-me-in-production" and not settings.debug:
    warnings.warn(
        "JWT_SECRET is using the default value! "
        "Set a secure secret in your .env file before deploying to production.",
        stacklevel=1,
    )

setup_logging(level=settings.log_level, fmt=settings.log_format)

app = FastAPI(
    title="AI Investment OS",
    description="AI-driven financial analysis and portfolio management system",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.send_to_user(user_id, {"type": "echo", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)

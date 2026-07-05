"""WebSocket manager for real-time push notifications."""
import json
import logging
from typing import Dict, Set
from datetime import datetime, timezone

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)
        logger.info(f"WebSocket connected: user={user_id}, total={self.total_connections}")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        conns = self._connections.get(user_id, set())
        dead = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    async def broadcast(self, message: dict):
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, message)

    async def send_alert(self, user_id: str, alert: dict):
        await self.send_to_user(user_id, {
            "type": "alert",
            "data": alert,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def send_stock_update(self, user_id: str, stock_code: str, data: dict):
        await self.send_to_user(user_id, {
            "type": "stock_update",
            "stock_code": stock_code,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @property
    def total_connections(self) -> int:
        return sum(len(v) for v in self._connections.values())


ws_manager = ConnectionManager()

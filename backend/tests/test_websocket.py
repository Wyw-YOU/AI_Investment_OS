"""Tests for WebSocket ConnectionManager."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.websocket_manager import ConnectionManager


class TestConnectionManager:
    def setup_method(self):
        self.mgr = ConnectionManager()

    def test_initial_state(self):
        assert self.mgr.total_connections == 0

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        ws = AsyncMock()
        await self.mgr.connect("user1", ws)
        assert self.mgr.total_connections == 1

        self.mgr.disconnect("user1", ws)
        assert self.mgr.total_connections == 0

    @pytest.mark.asyncio
    async def test_send_to_user(self):
        ws = AsyncMock()
        await self.mgr.connect("user1", ws)
        await self.mgr.send_to_user("user1", {"msg": "hello"})
        ws.send_json.assert_called_once_with({"msg": "hello"})

    @pytest.mark.asyncio
    async def test_broadcast(self):
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await self.mgr.connect("u1", ws1)
        await self.mgr.connect("u2", ws2)
        await self.mgr.broadcast({"msg": "all"})
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

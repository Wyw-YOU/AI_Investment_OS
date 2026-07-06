import asyncio
import json
import time
from typing import Any


class CacheService:
    def __init__(self):
        self._memory: dict[str, tuple[float, Any]] = {}
        self._redis = None
        self._init_lock = asyncio.Lock()
        self._initialized = False

    async def _ensure_redis(self):
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            try:
                import redis.asyncio as aioredis
                from app.config import get_settings
                settings = get_settings()
                self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
            self._initialized = True

    async def get(self, key: str) -> Any | None:
        await self._ensure_redis()
        if self._redis:
            try:
                val = await self._redis.get(key)
                if val:
                    return json.loads(val)
            except Exception:
                pass
        entry = self._memory.get(key)
        if entry:
            expire_at, value = entry
            if time.time() < expire_at:
                return value
            del self._memory[key]
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        await self._ensure_redis()
        if self._redis:
            try:
                await self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            except Exception:
                pass
        self._memory[key] = (time.time() + ttl, value)

    async def delete(self, key: str):
        await self._ensure_redis()
        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception:
                pass
        self._memory.pop(key, None)


cache = CacheService()

"""Redis cache service with TTL and serialization support."""
import json
import logging
from typing import Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import redis
                self._client = redis.from_url(self.redis_url, decode_responses=True)
                self._client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed, using memory fallback: {e}")
                self._client = MemoryCache()
        return self._client

    def get(self, key: str) -> Optional[Any]:
        client = self._get_client()
        value = client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def set(self, key: str, value: Any, ttl: int = 300):
        client = self._get_client()
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        if isinstance(client, MemoryCache):
            client.set(key, serialized, ttl)
        else:
            client.setex(key, ttl, serialized)

    def delete(self, key: str):
        client = self._get_client()
        client.delete(key)

    def exists(self, key: str) -> bool:
        client = self._get_client()
        return bool(client.exists(key))


class MemoryCache:
    """In-memory fallback when Redis is unavailable."""
    def __init__(self):
        self._store: dict[str, tuple[str, float]] = {}
        self._time = __import__("time").time

    def get(self, key: str) -> Optional[str]:
        if key in self._store:
            value, expires = self._store[key]
            if self._time() < expires:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: str, ttl: int = 300):
        self._store[key] = (value, self._time() + ttl)

    def delete(self, key: str):
        self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        return self.get(key) is not None


# Cache key conventions:
# market:realtime:{stock_code}        TTL 30s
# market:kline:{stock_code}:{period}  TTL 1h
# financial:{stock_code}:latest       TTL 24h
# news:{stock_code}:recent            TTL 30min
# analysis:{stock_code}:{date}        TTL 1h

CACHE_TTL = {
    "market_realtime": 30,
    "market_kline": 3600,
    "financial": 86400,
    "news": 1800,
    "analysis": 3600,
    "agent_state": 300,
}

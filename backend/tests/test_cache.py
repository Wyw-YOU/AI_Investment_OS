"""Tests for cache service (memory fallback mode)."""
from app.services.cache import CacheService, MemoryCache


class TestMemoryCache:
    def setup_method(self):
        self.cache = MemoryCache()

    def test_set_and_get(self):
        self.cache.set("key1", "value1", ttl=60)
        assert self.cache.get("key1") == "value1"

    def test_get_missing_key(self):
        assert self.cache.get("nonexistent") is None

    def test_delete(self):
        self.cache.set("key1", "value1", ttl=60)
        self.cache.delete("key1")
        assert self.cache.get("key1") is None

    def test_exists(self):
        assert not self.cache.exists("key1")
        self.cache.set("key1", "value1", ttl=60)
        assert self.cache.exists("key1")


class TestCacheService:
    def test_memory_fallback(self):
        """When Redis is unavailable, falls back to memory cache."""
        cache = CacheService(redis_url="redis://invalid:9999/0")
        cache.set("test_key", {"data": "value"}, ttl=60)
        result = cache.get("test_key")
        assert result == {"data": "value"}

    def test_json_serialization(self):
        cache = CacheService(redis_url="redis://invalid:9999/0")
        data = {"stocks": ["600519", "000001"], "score": 0.85}
        cache.set("portfolio", data, ttl=60)
        result = cache.get("portfolio")
        assert result["stocks"] == ["600519", "000001"]
        assert result["score"] == 0.85

    def test_chinese_characters(self):
        cache = CacheService(redis_url="redis://invalid:9999/0")
        cache.set("cn_key", {"name": "贵州茅台"}, ttl=60)
        result = cache.get("cn_key")
        assert result["name"] == "贵州茅台"

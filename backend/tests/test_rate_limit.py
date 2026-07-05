"""Tests for rate limiter."""
from app.core.rate_limit import RateLimiter


class TestRateLimiter:
    def test_allows_within_limit(self):
        rl = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert rl.is_allowed("127.0.0.1") is True

    def test_blocks_over_limit(self):
        rl = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            rl.is_allowed("127.0.0.1")
        assert rl.is_allowed("127.0.0.1") is False

    def test_different_ips(self):
        rl = RateLimiter(max_requests=2, window_seconds=60)
        assert rl.is_allowed("1.1.1.1") is True
        assert rl.is_allowed("2.2.2.2") is True
        assert rl.is_allowed("1.1.1.1") is True
        assert rl.is_allowed("2.2.2.2") is True
        assert rl.is_allowed("1.1.1.1") is False

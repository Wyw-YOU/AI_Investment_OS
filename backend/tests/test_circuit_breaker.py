"""Tests for circuit breaker."""
import pytest
from app.core.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    def test_starts_closed(self):
        cb = CircuitBreaker(failure_threshold=3, name="test")
        assert cb.state == CircuitState.CLOSED

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, name="test")
        for _ in range(3):
            with pytest.raises(ValueError):
                cb.call(self._fail_func)
        assert cb.state == CircuitState.OPEN

    def test_raises_when_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10.0, name="test")
        with pytest.raises(ValueError):
            cb.call(self._fail_func)
        with pytest.raises(RuntimeError, match="OPEN"):
            cb.call(lambda: "ok")

    def test_success_resets_count(self):
        cb = CircuitBreaker(failure_threshold=3, name="test")
        with pytest.raises(ValueError):
            cb.call(self._fail_func)
        assert cb.failure_count == 1
        cb.call(lambda: "ok")
        assert cb.failure_count == 0

    @staticmethod
    def _fail_func():
        raise ValueError("simulated failure")

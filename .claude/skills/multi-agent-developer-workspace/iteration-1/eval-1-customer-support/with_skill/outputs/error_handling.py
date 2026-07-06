"""
Error Handling Patterns
=======================
Centralises retry logic, circuit breaker, and safe-execution wrappers
so that agent nodes in the LangGraph workflow are resilient.

Usage::

    from error_handling import safe_node, retry_with_backoff, CircuitBreaker
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Safe node execution wrapper
# ---------------------------------------------------------------------------

def safe_node(
    agent_name: str,
    node_fn: Callable[[dict[str, Any]], dict[str, Any]],
    fallback: Optional[dict[str, Any]] = None,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """
    Wrap a workflow node function so that it *never* crashes the graph.

    On any exception the wrapper:
      - logs the error
      - returns ``fallback`` merged with ``{"errors": [message]}``
      - if *fallback* is ``None``, returns a minimal safe state update.

    Parameters
    ----------
    agent_name : str
        Friendly name for log messages.
    node_fn : callable
        The real node function ``state -> partial_state_update``.
    fallback : dict, optional
        Base dict to return on failure.

    Returns
    -------
    callable
        Wrapped node function safe for ``workflow.add_node(...)``.
    """

    def _wrapped(state: dict[str, Any]) -> dict[str, Any]:
        try:
            return node_fn(state)
        except Exception as exc:
            logger.error(
                "Node '%s' failed: %s",
                agent_name,
                exc,
                exc_info=True,
            )
            base = fallback if fallback is not None else {}
            return {
                **base,
                "errors": [f"{agent_name}: {exc}"],
            }

    _wrapped.__name__ = f"safe_{agent_name}"
    return _wrapped


# ---------------------------------------------------------------------------
# 2. Retry with exponential back-off
# ---------------------------------------------------------------------------

def retry_with_backoff(
    fn: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Any:
    """
    Execute ``fn()`` with exponential back-off.

    Parameters
    ----------
    fn : callable
        Zero-argument callable to retry.
    max_retries : int
        Maximum number of attempts (including the first).
    base_delay : float
        Base delay in seconds; actual delay = base_delay * 2^attempt.
    max_delay : float
        Cap on the delay.
    on_retry : callable, optional
        ``on_retry(attempt_number, exception)`` called before each retry.

    Returns
    -------
    Any
        The return value of ``fn()`` on success.

    Raises
    ------
    Exception
        The last exception if all retries are exhausted.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt == max_retries - 1:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            if on_retry:
                on_retry(attempt + 1, exc)
            logger.warning(
                "Attempt %d/%d failed (%s), retrying in %.1fs ...",
                attempt + 1,
                max_retries,
                exc,
                delay,
            )
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]  # unreachable but satisfies type-checkers


# ---------------------------------------------------------------------------
# 3. Circuit Breaker
# ---------------------------------------------------------------------------

class CircuitBreaker:
    """
    Prevents cascading failures by temporarily disabling calls to a
    failing service.

    States
    ------
    * **closed**   -- normal operation; calls go through.
    * **open**     -- calls are immediately rejected.
    * **half-open** -- a single probe call is allowed through.

    Parameters
    ----------
    failure_threshold : int
        Consecutive failures before opening the circuit.
    recovery_timeout : float
        Seconds to wait in *open* state before transitioning to *half-open*.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count: int = 0
        self._last_failure_time: Optional[datetime] = None
        self._state: str = "closed"

    @property
    def state(self) -> str:
        # Auto-transition from open to half-open after timeout
        if (
            self._state == "open"
            and self._last_failure_time
            and datetime.utcnow() - self._last_failure_time
            > timedelta(seconds=self.recovery_timeout)
        ):
            self._state = "half-open"
        return self._state

    def call(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute ``fn`` through the circuit breaker.

        Raises
        ------
        RuntimeError
            If the circuit is open.
        """
        current = self.state
        if current == "open":
            raise RuntimeError("Circuit breaker is OPEN -- call rejected.")

        try:
            result = fn(*args, **kwargs)
            # Success -- reset
            if current == "half-open":
                logger.info("Circuit breaker CLOSED (recovered).")
            self._failure_count = 0
            self._state = "closed"
            return result
        except Exception as exc:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()
            if self._failure_count >= self.failure_threshold:
                self._state = "open"
                logger.warning(
                    "Circuit breaker OPEN after %d consecutive failures.",
                    self._failure_count,
                )
            raise


# ---------------------------------------------------------------------------
# 4. Error aggregation helper
# ---------------------------------------------------------------------------

def merge_errors(
    state: dict[str, Any],
    new_errors: list[str],
) -> dict[str, Any]:
    """
    Immutably append ``new_errors`` to ``state["errors"]``.
    Returns a **new** state dict (copy-on-write).
    """
    existing = state.get("errors", [])
    return {
        **state,
        "errors": existing + new_errors,
    }

"""
Error Handling Patterns for the Multi-Agent Customer Support System.

Provides:
  1. Custom exception hierarchy for fine-grained error classification.
  2. A retry decorator with exponential back-off.
  3. A circuit-breaker for external service calls (LLM provider).
  4. Safe LLM invocation wrappers that catch, log, and record errors into
     the workflow state rather than crashing the graph.
"""

from __future__ import annotations

import functools
import logging
import time
import traceback
from datetime import datetime
from typing import Any, Callable, TypeVar

from state import SupportTicketState, AgentDecision

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class SupportSystemError(Exception):
    """Base exception for the customer support system."""
    pass


class LLMCallError(SupportSystemError):
    """Raised when an LLM API call fails after all retries."""
    pass


class ParsingError(SupportSystemError):
    """Raised when LLM output cannot be parsed into the expected schema."""
    pass


class RoutingError(SupportSystemError):
    """Raised when the routing logic cannot determine a destination agent."""
    pass


class CircuitBreakerOpen(SupportSystemError):
    """Raised when the circuit breaker is in the OPEN state."""
    pass


class MaxRetriesExceeded(SupportSystemError):
    """Raised when a node has exhausted its retry budget."""
    pass


# ---------------------------------------------------------------------------
# Retry Decorator
# ---------------------------------------------------------------------------

F = TypeVar("F", bound=Callable[..., Any])


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retriable_exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator that retries a function on failure with exponential back-off.

    Parameters
    ----------
    max_retries : int
        Maximum number of retry attempts.
    base_delay : float
        Initial delay in seconds.
    max_delay : float
        Cap on the delay.
    exponential_base : float
        Multiplier for each successive delay.
    retriable_exceptions : tuple
        Exception types that trigger a retry.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            delay = base_delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retriable_exceptions as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        logger.warning(
                            "Attempt %d/%d for %s failed: %s. "
                            "Retrying in %.1fs...",
                            attempt + 1,
                            max_retries,
                            func.__name__,
                            exc,
                            delay,
                        )
                        time.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        logger.error(
                            "All %d attempts for %s exhausted. Last error: %s",
                            max_retries,
                            func.__name__,
                            exc,
                        )
            raise MaxRetriesExceeded(
                f"{func.__name__} failed after {max_retries} retries"
            ) from last_exc

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# Circuit Breaker
# ---------------------------------------------------------------------------

class CircuitBreaker:
    """
    Simple circuit-breaker to avoid hammering a failing external service.

    States:
      CLOSED  -- normal operation, calls go through.
      OPEN    -- service is considered down; calls fail fast.
      HALF_OPEN -- a single probe call is allowed through to test recovery.

    Transitions:
      CLOSED -> OPEN    after `failure_threshold` consecutive failures.
      OPEN   -> HALF_OPEN after `recovery_timeout` seconds.
      HALF_OPEN -> CLOSED  if probe succeeds.
      HALF_OPEN -> OPEN    if probe fails.
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0

    @property
    def state(self) -> str:
        if self._state == self.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = self.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = self.CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = self.OPEN
            logger.warning(
                "Circuit breaker OPEN after %d consecutive failures.",
                self._failure_count,
            )

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute func through the circuit breaker."""
        current = self.state
        if current == self.OPEN:
            raise CircuitBreakerOpen(
                "Circuit breaker is OPEN. Service calls are blocked until "
                f"recovery timeout ({self.recovery_timeout}s) elapses."
            )
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise


# ---------------------------------------------------------------------------
# Safe state-mutating helpers
# ---------------------------------------------------------------------------


def record_agent_decision(
    state: SupportTicketState,
    agent_name: str,
    decision: str,
    confidence: float = 0.0,
    reasoning: str = "",
) -> None:
    """Append an AgentDecision to the state's decision log."""
    decision_entry = AgentDecision(
        agent_name=agent_name,
        decision=decision,
        confidence=confidence,
        reasoning=reasoning,
        timestamp=datetime.utcnow().isoformat(),
    )
    state.setdefault("agent_decisions", []).append(decision_entry)


def record_error(state: SupportTicketState, error_msg: str) -> None:
    """Append an error string to the state's error log."""
    state.setdefault("errors", []).append(error_msg)


def safe_node_wrapper(
    node_func: Callable[[SupportTicketState], SupportTicketState],
    node_name: str,
) -> Callable[[SupportTicketState], SupportTicketState]:
    """
    Wrap a LangGraph node function with error handling that records failures
    into the state instead of crashing the workflow.

    If the node raises, the state is updated with:
      - ticket_status -> "error"
      - error message appended
      - agent decision recorded
    """

    @functools.wraps(node_func)
    def wrapper(state: SupportTicketState) -> SupportTicketState:
        try:
            result = node_func(state)
            return result
        except Exception as exc:
            tb = traceback.format_exc()
            logger.error("Node '%s' failed: %s\n%s", node_name, exc, tb)

            record_error(
                state,
                f"[{node_name}] {type(exc).__name__}: {exc}",
            )
            record_agent_decision(
                state,
                agent_name=node_name,
                decision="error",
                confidence=0.0,
                reasoning=f"Node failed with: {exc}",
            )

            # Bump retry count; mark error status
            state["retry_count"] = state.get("retry_count", 0) + 1
            state["ticket_status"] = "error"

            return state

    return wrapper

"""
Utility functions for the Multi-Agent Investment Analysis System.

Includes logging setup, JSON parsing helpers, retry decorators, and
fallback response generators.
"""

from __future__ import annotations

import json
import logging
import re
import time
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, ValidationError

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Create a configured logger with consistent formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


logger = setup_logger("investment_system")

# ---------------------------------------------------------------------------
# JSON parsing helpers
# ---------------------------------------------------------------------------

def extract_json_from_llm_response(raw: str) -> dict[str, Any]:
    """
    Extract a JSON object from an LLM response that may contain markdown
    code fences, preamble text, or trailing commentary.

    Raises
    ------
    ValueError
        If no valid JSON object can be extracted.
    """
    # Try direct parse first
    stripped = raw.strip()
    if stripped.startswith("{"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # Try extracting from code fences
    fence_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(fence_pattern, raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding the first { ... } block
    brace_pattern = r"\{[\s\S]*\}"
    match = re.search(brace_pattern, raw)
    if match:
        candidate = match.group(0)
        # Try progressively trimming from the end if the JSON is unbalanced
        depth = 0
        end_idx = 0
        for i, ch in enumerate(candidate):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
        if end_idx > 0:
            try:
                return json.loads(candidate[:end_idx])
            except json.JSONDecodeError:
                pass

    raise ValueError(
        f"Could not extract valid JSON from LLM response. "
        f"First 200 chars: {raw[:200]!r}"
    )


def validate_agent_output(
    raw_data: dict[str, Any],
    schema_class: type[BaseModel],
) -> BaseModel:
    """
    Parse and validate raw JSON data against a Pydantic schema.

    Returns the validated model instance, or raises ValidationError with
    a descriptive message.
    """
    try:
        return schema_class.model_validate(raw_data)
    except ValidationError as exc:
        logger.warning(
            "Schema validation failed for %s: %s",
            schema_class.__name__,
            exc.errors(),
        )
        raise


# ---------------------------------------------------------------------------
# Retry decorator
# ---------------------------------------------------------------------------

F = TypeVar("F", bound=Callable[..., Any])


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    allowed_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator that retries a function with exponential backoff.

    Parameters
    ----------
    max_retries : int
        Maximum number of retry attempts.
    initial_delay : float
        Seconds to wait before the first retry.
    backoff_factor : float
        Multiplier applied to the delay after each retry.
    allowed_exceptions : tuple
        Exception types that trigger a retry.  Other exceptions propagate
        immediately.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exc: Exception | None = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as exc:
                    last_exc = exc
                    logger.warning(
                        "Attempt %d/%d for %s failed: %s. Retrying in %.1fs...",
                        attempt,
                        max_retries,
                        func.__name__,
                        exc,
                        delay,
                    )
                    if attempt < max_retries:
                        time.sleep(delay)
                        delay *= backoff_factor
            # All retries exhausted
            raise last_exc  # type: ignore[misc]
        return wrapper  # type: ignore[return-value]
    return decorator


# ---------------------------------------------------------------------------
# Fallback response generators
# ---------------------------------------------------------------------------

def create_fallback_output(
    ticker: str,
    agent_name: str,
    error_message: str,
    schema_class: type[BaseModel],
) -> BaseModel:
    """
    Create a minimal valid output for an agent that failed all retries.

    This ensures the report agent still has something to work with and the
    workflow can continue rather than crash.
    """
    fallback_data: dict[str, Any] = {
        "ticker": ticker,
        "agent_name": agent_name,
        "confidence": 0.0,
        "summary": f"Analysis failed for {agent_name}: {error_message}. "
                   "This agent's contribution should be treated as unavailable.",
        "citations": [],
        "errors": [f"FALLBACK: {error_message}"],
    }

    # Add agent-specific required fields with safe defaults
    if agent_name == "news_agent":
        fallback_data.update({
            "sentiment_label": "neutral",
            "sentiment_score": 0.0,
            "key_events": [],
            "news_items": [],
            "trend": "neutral",
        })
    elif agent_name == "financial_agent":
        fallback_data.update({
            "valuation_score": 50.0,
            "quality_score": 50.0,
            "growth_score": 50.0,
            "key_metrics": [],
            "strengths": [],
            "weaknesses": [],
            "fair_value_estimate": None,
        })
    elif agent_name == "technical_agent":
        fallback_data.update({
            "overall_signal": "neutral",
            "signal_strength": "conflicting",
            "current_price": None,
            "support_levels": [],
            "resistance_levels": [],
            "indicators": [],
            "patterns": [],
            "suggested_entry": None,
            "suggested_stop_loss": None,
            "suggested_take_profit": None,
        })
    elif agent_name == "risk_agent":
        fallback_data.update({
            "overall_risk_level": "moderate",
            "risk_score": 50.0,
            "volatility_assessment": "Unable to assess due to agent failure.",
            "max_drawdown_estimate": None,
            "beta_estimate": None,
            "sharpe_ratio": None,
            "risk_factors": [],
            "position_sizing_advice": "Unable to provide advice due to agent failure.",
            "stop_loss_recommendation": None,
        })

    return schema_class.model_validate(fallback_data)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def serialize_agent_output(output: BaseModel) -> dict[str, Any]:
    """Serialize a Pydantic agent output to a JSON-compatible dict."""
    return json.loads(output.model_dump_json())


def format_timestamp(dt: datetime | None = None) -> str:
    """Return an ISO 8601 UTC timestamp string."""
    return (dt or datetime.utcnow()).isoformat()

"""
Output Parsing and Validation for the Multi-Agent Customer Support System.

Every LLM response is expected to be valid JSON that conforms to a known
schema.  This module provides:

  1. Safe JSON extraction from raw LLM text (handles markdown fences, etc.).
  2. Pydantic-free validation using plain dataclasses and manual checks.
  3. Typed extraction helpers that return the exact TypedDict structures
     consumed by the workflow state.

Design choice: we intentionally avoid adding Pydantic as a dependency so
the project stays lightweight.  Validation is performed with explicit
type / value checks and raises `ValidationError` on failure.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from state import (
    AgentResponse,
    ClassificationResult,
    FinalResponse,
    UrgencyLevel,
    TopicCategory,
)


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when parsed LLM output does not match the expected schema."""
    pass


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def extract_json_from_text(raw_text: str) -> dict:
    """
    Extract a JSON object from LLM output that may contain markdown fences,
    leading/trailing commentary, or whitespace.

    Strategy:
      1. Try to find a ```json ... ``` fenced block.
      2. Fall back to finding the first `{ ... }` balanced block.
      3. Fall back to parsing the entire string.
    """
    # 1. Fenced code block
    fence_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)
    match = fence_pattern.search(raw_text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass  # fall through

    # 2. First { ... } block (brace-balanced)
    brace_start = raw_text.find("{")
    if brace_start != -1:
        depth = 0
        for i in range(brace_start, len(raw_text)):
            if raw_text[i] == "{":
                depth += 1
            elif raw_text[i] == "}":
                depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw_text[brace_start : i + 1])
                except json.JSONDecodeError:
                    break

    # 3. Whole string
    try:
        return json.loads(raw_text.strip())
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Could not extract valid JSON: {exc}") from exc


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _check_required_fields(data: dict, required: list[str], context: str) -> None:
    """Raise ValidationError if any required field is missing."""
    missing = [f for f in required if f not in data]
    if missing:
        raise ValidationError(
            f"[{context}] Missing required fields: {missing}. "
            f"Got keys: {list(data.keys())}"
        )


def _check_enum(value: str, allowed: list[str], field_name: str, context: str) -> None:
    """Raise ValidationError if value is not in the allowed set."""
    if value not in allowed:
        raise ValidationError(
            f"[{context}] Invalid value '{value}' for '{field_name}'. "
            f"Allowed: {allowed}"
        )


def _check_float_range(
    value: Any, low: float, high: float, field_name: str, context: str
) -> None:
    """Raise ValidationError if value is not a float in [low, high]."""
    try:
        fval = float(value)
    except (TypeError, ValueError):
        raise ValidationError(
            f"[{context}] '{field_name}' must be a number, got {type(value).__name__}"
        )
    if not (low <= fval <= high):
        raise ValidationError(
            f"[{context}] '{field_name}' must be between {low} and {high}, got {fval}"
        )


# ---------------------------------------------------------------------------
# Parsed output containers (plain dataclasses, not Pydantic)
# ---------------------------------------------------------------------------

@dataclass
class ParsedClassification:
    urgency: str
    topic: str
    sentiment: str
    keywords: list[str]
    confidence: float
    reasoning: str

    def to_result(self) -> ClassificationResult:
        return ClassificationResult(
            urgency=self.urgency,
            topic=self.topic,
            sentiment=self.sentiment,
            keywords=self.keywords,
            confidence=self.confidence,
            reasoning=self.reasoning,
        )


@dataclass
class ParsedAgentResponse:
    agent_name: str
    response_text: str
    follow_up_actions: list[str] = field(default_factory=list)
    requires_escalation: bool = False
    escalation_reason: str = ""
    internal_notes: str = ""
    confidence: float = 0.0

    def to_response(self) -> AgentResponse:
        return AgentResponse(
            agent_name=self.agent_name,
            response_text=self.response_text,
            follow_up_actions=self.follow_up_actions,
            requires_escalation=self.requires_escalation,
            escalation_reason=self.escalation_reason,
            internal_notes=self.internal_notes,
            confidence=self.confidence,
        )


@dataclass
class ParsedFinalResponse:
    customer_facing_message: str
    ticket_summary: str
    resolution_status: str
    follow_up_required: bool = False
    estimated_resolution_time: str = "N/A"
    reference_number: str = ""

    def to_final(self) -> FinalResponse:
        return FinalResponse(
            customer_facing_message=self.customer_facing_message,
            ticket_summary=self.ticket_summary,
            resolution_status=self.resolution_status,
            follow_up_required=self.follow_up_required,
            estimated_resolution_time=self.estimated_resolution_time,
            reference_number=self.reference_number,
        )


# ---------------------------------------------------------------------------
# High-level parse & validate functions
# ---------------------------------------------------------------------------

def parse_classification(raw_text: str) -> ParsedClassification:
    """
    Parse and validate the classifier agent's LLM output.

    Returns a ParsedClassification that can be converted to the TypedDict
    via `.to_result()`.
    """
    data = extract_json_from_text(raw_text)
    ctx = "ClassifierAgent"

    _check_required_fields(
        data,
        ["urgency", "topic", "sentiment", "keywords", "confidence", "reasoning"],
        ctx,
    )

    _check_enum(data["urgency"], [e.value for e in UrgencyLevel], "urgency", ctx)
    _check_enum(data["topic"], [e.value for e in TopicCategory], "topic", ctx)
    _check_enum(data["sentiment"], ["positive", "neutral", "negative"], "sentiment", ctx)
    _check_float_range(data["confidence"], 0.0, 1.0, "confidence", ctx)

    if not isinstance(data["keywords"], list):
        raise ValidationError(f"[{ctx}] 'keywords' must be a list")

    return ParsedClassification(
        urgency=data["urgency"],
        topic=data["topic"],
        sentiment=data["sentiment"],
        keywords=data["keywords"],
        confidence=float(data["confidence"]),
        reasoning=data["reasoning"],
    )


def parse_agent_response(raw_text: str, expected_agent: str) -> ParsedAgentResponse:
    """
    Parse and validate a specialist agent's LLM output.

    Parameters
    ----------
    raw_text : str
        The raw LLM response text.
    expected_agent : str
        The expected agent_name value (e.g. "technical_agent").
    """
    data = extract_json_from_text(raw_text)
    ctx = f"Agent({expected_agent})"

    _check_required_fields(
        data,
        ["agent_name", "response_text", "confidence"],
        ctx,
    )

    if data["agent_name"] != expected_agent:
        raise ValidationError(
            f"[{ctx}] Expected agent_name='{expected_agent}', "
            f"got '{data['agent_name']}'"
        )

    _check_float_range(data["confidence"], 0.0, 1.0, "confidence", ctx)

    return ParsedAgentResponse(
        agent_name=data["agent_name"],
        response_text=data["response_text"],
        follow_up_actions=data.get("follow_up_actions", []),
        requires_escalation=bool(data.get("requires_escalation", False)),
        escalation_reason=data.get("escalation_reason", ""),
        internal_notes=data.get("internal_notes", ""),
        confidence=float(data["confidence"]),
    )


def parse_final_response(raw_text: str) -> ParsedFinalResponse:
    """
    Parse and validate the response aggregator's LLM output.
    """
    data = extract_json_from_text(raw_text)
    ctx = "ResponseAggregator"

    _check_required_fields(
        data,
        ["customer_facing_message", "ticket_summary", "resolution_status"],
        ctx,
    )

    _check_enum(
        data["resolution_status"],
        ["resolved", "pending", "escalated"],
        "resolution_status",
        ctx,
    )

    return ParsedFinalResponse(
        customer_facing_message=data["customer_facing_message"],
        ticket_summary=data["ticket_summary"],
        resolution_status=data["resolution_status"],
        follow_up_required=bool(data.get("follow_up_required", False)),
        estimated_resolution_time=data.get("estimated_resolution_time", "N/A"),
        reference_number=data.get("reference_number", ""),
    )

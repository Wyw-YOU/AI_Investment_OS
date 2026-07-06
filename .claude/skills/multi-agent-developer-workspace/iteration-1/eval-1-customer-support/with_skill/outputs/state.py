"""
State Management Module
=======================
Defines the TypedDict-based state schema for the customer support
multi-agent workflow.  The state flows immutably through each node,
following the skill's design principles (minimal, well-typed, explicit
data flow).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, TypedDict

import operator


# ---------------------------------------------------------------------------
# Enums for constrained vocabulary
# ---------------------------------------------------------------------------

class TicketStatus(str, Enum):
    """Lifecycle status of a support ticket."""
    PENDING = "pending"
    CLASSIFYING = "classifying"
    ROUTING = "routing"
    IN_PROGRESS = "in_progress"
    AWAITING_RESPONSE = "awaiting_response"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    FAILED = "failed"


class Urgency(str, Enum):
    """Urgency levels assigned by the classifier agent."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Topic(str, Enum):
    """Topic categories used for routing."""
    TECHNICAL = "technical"
    BILLING = "billing"
    GENERAL = "general"
    ESCALATION = "escalation"


# ---------------------------------------------------------------------------
# Agent output sub-schemas (typed dicts for sub-documents)
# ---------------------------------------------------------------------------

class ClassificationResult(TypedDict, total=False):
    """Output produced by the ClassifierAgent."""
    urgency: str          # one of Urgency enum values
    topic: str            # one of Topic enum values
    reasoning: str        # classifier explanation
    confidence: float     # 0.0 - 1.0


class AgentResponse(TypedDict, total=False):
    """Generic response from any specialist agent."""
    agent_name: str
    response_text: str
    actions_taken: list[str]
    follow_up_questions: list[str]
    confidence: float
    citations: list[str]


class FinalResponse(TypedDict, total=False):
    """The polished final response sent to the customer."""
    subject: str
    body: str
    tone: str             # e.g. empathetic, professional
    internal_notes: str   # notes for the agent team
    next_steps: list[str]


# ---------------------------------------------------------------------------
# Main workflow state
# ---------------------------------------------------------------------------

class SupportTicketState(TypedDict, total=False):
    """
    Canonical state schema for the customer-support multi-agent workflow.

    Design principles applied:
    - Minimal: only data each node needs.
    - Well-typed: TypedDict fields with clear semantics.
    - Immutable between nodes: nodes return *new* dicts via {**state, ...}.
    - Parallel-safe: ``agent_outputs`` uses ``Annotated[list, operator.add]``
      so parallel branches can each append without conflicts.
    """

    # --- Identifiers ---
    ticket_id: str
    customer_id: str

    # --- Raw input ---
    customer_message: str
    customer_name: str
    customer_email: str
    subject: str
    timestamp: str  # ISO-8601

    # --- Classification (filled by ClassifierAgent) ---
    classification: ClassificationResult

    # --- Specialist agent outputs (parallel-safe list) ---
    agent_outputs: Annotated[list[AgentResponse], operator.add]

    # --- Final polished response (filled by ResponseAgent) ---
    final_response: FinalResponse

    # --- Workflow metadata ---
    status: str                 # TicketStatus value
    urgency: str                # Urgency value
    topic: str                  # Topic value
    errors: Annotated[list[str], operator.add]
    started_at: str
    completed_at: str
    metadata: dict[str, Any]


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def create_initial_state(
    ticket_id: str,
    customer_id: str,
    customer_name: str,
    customer_email: str,
    subject: str,
    customer_message: str,
) -> SupportTicketState:
    """Factory for a pristine ticket state."""
    now = datetime.utcnow().isoformat()
    return SupportTicketState(
        ticket_id=ticket_id,
        customer_id=customer_id,
        customer_name=customer_name,
        customer_email=customer_email,
        subject=subject,
        customer_message=customer_message,
        timestamp=now,
        started_at=now,
        status=TicketStatus.PENDING.value,
        agent_outputs=[],
        errors=[],
        metadata={},
    )

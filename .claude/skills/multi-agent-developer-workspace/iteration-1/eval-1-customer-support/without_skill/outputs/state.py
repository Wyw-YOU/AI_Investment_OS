"""
State Management for Multi-Agent Customer Support System.

Defines the TypedDict-based state schema that flows through the LangGraph
workflow, including ticket classification, routing, response generation,
and lifecycle tracking fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Optional
from typing_extensions import TypedDict
from datetime import datetime
import uuid


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UrgencyLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TopicCategory(str, Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    GENERAL = "general"


class TicketStatus(str, Enum):
    RECEIVED = "received"
    CLASSIFYING = "classifying"
    ROUTING = "routing"
    PROCESSING = "processing"
    RESPONSE_GENERATING = "response_generating"
    COMPLETED = "completed"
    ERROR = "error"


# ---------------------------------------------------------------------------
# TypedDict State Schema (flows through LangGraph)
# ---------------------------------------------------------------------------

class AgentDecision(TypedDict, total=False):
    """Record of a single agent's decision."""
    agent_name: str
    decision: str
    confidence: float
    reasoning: str
    timestamp: str


class TicketInput(TypedDict):
    """Raw ticket data coming from the customer."""
    ticket_id: str
    customer_id: str
    subject: str
    body: str
    channel: str          # e.g. "email", "chat", "web_form"
    received_at: str       # ISO-8601


class ClassificationResult(TypedDict, total=False):
    """Output produced by the ClassifierAgent."""
    urgency: str           # one of UrgencyLevel values
    topic: str             # one of TopicCategory values
    sentiment: str         # "positive", "neutral", "negative"
    keywords: list[str]
    confidence: float
    reasoning: str


class AgentResponse(TypedDict, total=False):
    """Generic response produced by any specialist agent."""
    agent_name: str
    response_text: str
    follow_up_actions: list[str]
    requires_escalation: bool
    escalation_reason: str
    internal_notes: str
    confidence: float


class FinalResponse(TypedDict, total=False):
    """Final aggregated response sent back to the customer."""
    customer_facing_message: str
    ticket_summary: str
    resolution_status: str   # "resolved", "pending", "escalated"
    follow_up_required: bool
    estimated_resolution_time: str
    reference_number: str


class SupportTicketState(TypedDict, total=False):
    """
    Full workflow state that flows through the LangGraph.

    Every node reads from and writes to this state.  The graph is
    designed so that each node only touches the fields it owns, keeping
    concurrent updates safe.
    """

    # -- Input --
    ticket: TicketInput

    # -- Classification (ClassifierAgent) --
    classification: ClassificationResult

    # -- Routing decision --
    assigned_topic: str
    urgency_level: str
    requires_parallel_processing: bool

    # -- Specialist agent outputs (populated in parallel) --
    technical_response: AgentResponse
    billing_response: AgentResponse
    general_response: AgentResponse

    # -- Active specialist response (chosen by routing) --
    active_response: AgentResponse

    # -- Final output --
    final_response: FinalResponse

    # -- Lifecycle / metadata --
    ticket_status: str
    workflow_start_time: str
    workflow_end_time: str
    processing_time_ms: float
    agent_decisions: list[AgentDecision]
    errors: list[str]
    retry_count: int
    max_retries: int


# ---------------------------------------------------------------------------
# Dataclass helpers (used for constructing state outside the graph)
# ---------------------------------------------------------------------------

@dataclass
class Ticket:
    """Customer-facing ticket representation."""
    ticket_id: str = field(default_factory=lambda: f"TKT-{uuid.uuid4().hex[:8].upper()}")
    customer_id: str = ""
    subject: str = ""
    body: str = ""
    channel: str = "web_form"
    received_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_input(self) -> TicketInput:
        return TicketInput(
            ticket_id=self.ticket_id,
            customer_id=self.customer_id,
            subject=self.subject,
            body=self.body,
            channel=self.channel,
            received_at=self.received_at,
        )


def create_initial_state(ticket: Ticket) -> SupportTicketState:
    """Build the initial state dict from a Ticket instance."""
    return SupportTicketState(
        ticket=ticket.to_input(),
        ticket_status=TicketStatus.RECEIVED.value,
        workflow_start_time=datetime.utcnow().isoformat(),
        agent_decisions=[],
        errors=[],
        retry_count=0,
        max_retries=3,
    )

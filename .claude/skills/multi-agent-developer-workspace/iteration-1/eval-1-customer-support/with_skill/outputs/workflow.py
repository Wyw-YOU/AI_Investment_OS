"""
LangGraph Workflow Orchestrator
================================
Builds the StateGraph that wires together:

    Customer Message
          |
    ClassifierAgent  (sequential -- must finish before routing)
          |
    [Conditional Routing]
    +-- TechnicalAgent   (topic == "technical")
    +-- BillingAgent      (topic == "billing")
    +-- GeneralAgent      (topic == "general")
          |
    ResponseAgent  (polish the specialist draft)
          |
       END / ESCALATION

Key design decisions (per the skill):
  - **Conditional routing** -- the graph branches after classification so
    only the relevant specialist runs (no wasted compute).
  - **Safe node wrappers** -- every node is wrapped with ``safe_node``
    so a single agent failure never kills the workflow.
  - **TypedDict state** -- ``SupportTicketState`` with
    ``Annotated[list, operator.add]`` for the parallel-safe
    ``agent_outputs`` field.

The module exposes ``create_workflow()`` which returns a compiled
LangGraph ``CompiledGraph`` ready for ``.invoke(state)``.
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from agents import (
    BillingAgent,
    ClassifierAgent,
    GeneralAgent,
    ResponseAgent,
    TechnicalAgent,
)
from error_handling import safe_node
from state import SupportTicketState, TicketStatus, Topic

logger = logging.getLogger(__name__)

# Instantiate agents once (they are stateless apart from the logger)
_classifier = ClassifierAgent()
_technical  = TechnicalAgent()
_billing    = BillingAgent()
_general    = GeneralAgent()
_response   = ResponseAgent()


# ---------------------------------------------------------------------------
# Routing function
# ---------------------------------------------------------------------------

def _route_by_topic(state: dict[str, Any]) -> str:
    """
    Return the name of the specialist node to invoke next.

    This function is used by ``add_conditional_edges`` and must return
    one of the keys in the mapping dict.
    """
    topic = state.get("topic", Topic.GENERAL.value)

    routing_map = {
        Topic.TECHNICAL.value:   "technical_agent",
        Topic.BILLING.value:     "billing_agent",
        Topic.GENERAL.value:     "general_agent",
        Topic.ESCALATION.value:  "general_agent",  # general handles escalations too
    }

    target = routing_map.get(topic, "general_agent")
    logger.info(
        "Routing ticket %s (topic=%s) -> %s",
        state.get("ticket_id"),
        topic,
        target,
    )
    return target


# ---------------------------------------------------------------------------
# Node wrappers (apply safe_node)
# ---------------------------------------------------------------------------

def _classify_node(state: dict[str, Any]) -> dict[str, Any]:
    return safe_node("classifier_agent", _classifier.run, {
        "classification": {},
        "urgency": "medium",
        "topic": "general",
        "status": TicketStatus.ROUTING.value,
    })(state)


def _technical_node(state: dict[str, Any]) -> dict[str, Any]:
    return safe_node("technical_agent", _technical.run, {
        "agent_outputs": [],
        "status": TicketStatus.IN_PROGRESS.value,
    })(state)


def _billing_node(state: dict[str, Any]) -> dict[str, Any]:
    return safe_node("billing_agent", _billing.run, {
        "agent_outputs": [],
        "status": TicketStatus.IN_PROGRESS.value,
    })(state)


def _general_node(state: dict[str, Any]) -> dict[str, Any]:
    return safe_node("general_agent", _general.run, {
        "agent_outputs": [],
        "status": TicketStatus.IN_PROGRESS.value,
    })(state)


def _response_node(state: dict[str, Any]) -> dict[str, Any]:
    return safe_node("response_agent", _response.run, {
        "final_response": {},
        "status": TicketStatus.COMPLETED.value,
    })(state)


# ---------------------------------------------------------------------------
# Escalation node (for critical tickets)
# ---------------------------------------------------------------------------

def _escalation_node(state: dict[str, Any]) -> dict[str, Any]:
    """Mark ticket as escalated -- no LLM needed."""
    from datetime import datetime
    from state import FinalResponse

    customer_name = state.get("customer_name", "there")
    final = FinalResponse(
        subject=f"[ESCALATED] Re: {state.get('subject', 'Your Support Request')}",
        body=(
            f"Hi {customer_name},\n\n"
            f"Thank you for contacting us. Due to the urgent nature of "
            f"your request, this ticket has been escalated to our senior "
            f"support team. A specialist will reach out to you within "
            f"the next 2 hours.\n\n"
            f"If this is an emergency, please call our priority support "
            f"line at 1-800-SUPPORT.\n\n"
            f"Best regards,\nSupport Team"
        ),
        tone="empathetic",
        internal_notes=(
            f"Auto-escalated due to urgency={state.get('urgency')}. "
            f"Assign to senior agent queue."
        ),
        next_steps=[
            "Assign to senior agent",
            "Send priority notification",
            "Monitor SLA timer",
        ],
    )
    return {
        "final_response": final,
        "status": TicketStatus.ESCALATED.value,
        "completed_at": datetime.utcnow().isoformat(),
    }


def _should_escalate(state: dict[str, Any]) -> str:
    """Check if the ticket is critical and should be escalated first."""
    if state.get("urgency") == "critical":
        return "escalation"
    return "response_agent"


# ---------------------------------------------------------------------------
# Workflow builder
# ---------------------------------------------------------------------------

def create_workflow() -> Any:
    """
    Build and compile the customer-support LangGraph workflow.

    Returns
    -------
    CompiledGraph
        A compiled graph ready for ``.invoke(initial_state)``.
    """
    workflow = StateGraph(SupportTicketState)

    # -- nodes --------------------------------------------------------------
    workflow.add_node("classifier_agent", _classify_node)
    workflow.add_node("technical_agent",  _technical_node)
    workflow.add_node("billing_agent",    _billing_node)
    workflow.add_node("general_agent",    _general_node)
    workflow.add_node("response_agent",   _response_node)
    workflow.add_node("escalation",       _escalation_node)

    # -- entry point --------------------------------------------------------
    workflow.set_entry_point("classifier_agent")

    # -- conditional routing after classification ---------------------------
    workflow.add_conditional_edges(
        "classifier_agent",
        _route_by_topic,
        {
            "technical_agent": "technical_agent",
            "billing_agent":   "billing_agent",
            "general_agent":   "general_agent",
        },
    )

    # -- specialist -> escalation check -> response / END -------------------
    # All three specialists feed into a shared escalation gate
    workflow.add_conditional_edges(
        "technical_agent",
        _should_escalate,
        {
            "response_agent": "response_agent",
            "escalation":     "escalation",
        },
    )
    workflow.add_conditional_edges(
        "billing_agent",
        _should_escalate,
        {
            "response_agent": "response_agent",
            "escalation":     "escalation",
        },
    )
    workflow.add_conditional_edges(
        "general_agent",
        _should_escalate,
        {
            "response_agent": "response_agent",
            "escalation":     "escalation",
        },
    )

    # -- terminal edges -----------------------------------------------------
    workflow.add_edge("response_agent", END)
    workflow.add_edge("escalation",     END)

    # -- compile and return -------------------------------------------------
    compiled = workflow.compile()
    logger.info("Customer-support workflow compiled successfully.")
    return compiled

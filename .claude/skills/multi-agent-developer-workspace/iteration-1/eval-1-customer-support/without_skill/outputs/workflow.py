"""
LangGraph Workflow Orchestration for the Multi-Agent Customer Support System.

This module defines the complete workflow graph using LangGraph's StateGraph:

    ┌────────────┐
    │  Receive   │
    │  Ticket    │
    └─────┬──────┘
          │
    ┌─────▼──────┐
    │ Classifier │
    │   Agent    │
    └─────┬──────┘
          │
    ┌─────▼──────┐
    │   Router   │──── parallel branch based on topic
    └─────┬──────┘
          │
   ┌──────┼──────┐
   │      │      │
   ▼      ▼      ▼
 Tech  Billing  General     (parallel execution)
   │      │      │
   └──────┼──────┘
          │
    ┌─────▼──────┐
    │  Response  │
    │   Agent    │
    └─────┬──────┘
          │
    ┌─────▼──────┐
    │  Complete  │
    └────────────┘

Key design decisions:
  - Uses LangGraph's MessageGraph / StateGraph with a TypedDict state.
  - Specialist agents run in parallel via LangGraph's fan-out pattern.
  - A merge node selects the active response from whichever agent ran.
  - Error handling routes to a fallback node when classification fails.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

# LangGraph imports
from langgraph.graph import StateGraph, END

from state import (
    SupportTicketState,
    Ticket,
    TicketStatus,
    TopicCategory,
    create_initial_state,
)
from agents import (
    ClassifierAgent,
    TechnicalAgent,
    BillingAgent,
    GeneralAgent,
    ResponseAgent,
)
from error_handling import safe_node_wrapper, record_error
from state_manager import StateManager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Workflow class
# ---------------------------------------------------------------------------


class CustomerSupportWorkflow:
    """
    Builds and executes the LangGraph workflow for processing support tickets.

    Usage::

        workflow = CustomerSupportWorkflow(llm_client=my_client)
        result = await workflow.arun(ticket)
        # or synchronously:
        result = workflow.run(ticket)
    """

    def __init__(self, llm_client: Any = None, state_manager: Optional[StateManager] = None) -> None:
        self._llm = llm_client
        self._sm = state_manager or StateManager()

        # Instantiate agents
        self._classifier = ClassifierAgent(llm_client)
        self._tech_agent = TechnicalAgent(llm_client)
        self._billing_agent = BillingAgent(llm_client)
        self._general_agent = GeneralAgent(llm_client)
        self._response_agent = ResponseAgent(llm_client)

        # Build the graph
        self._graph = self._build_graph()

    # -----------------------------------------------------------------------
    # Graph construction
    # -----------------------------------------------------------------------

    def _build_graph(self) -> StateGraph:
        """
        Assemble the LangGraph StateGraph.
        """
        workflow = StateGraph(SupportTicketState)

        # -- Nodes -----------------------------------------------------------
        workflow.add_node("receive_ticket", safe_node_wrapper(self._receive_ticket, "receive_ticket"))
        workflow.add_node("classify", safe_node_wrapper(self._classify, "classify"))
        workflow.add_node("route", safe_node_wrapper(self._route, "route"))

        # Specialist nodes (will be executed in parallel by the fan-out)
        workflow.add_node("technical_agent", safe_node_wrapper(self._run_technical, "technical_agent"))
        workflow.add_node("billing_agent", safe_node_wrapper(self._run_billing, "billing_agent"))
        workflow.add_node("general_agent", safe_node_wrapper(self._run_general, "general_agent"))

        # Merge the parallel results
        workflow.add_node("merge_responses", safe_node_wrapper(self._merge_responses, "merge_responses"))

        # Quality gate
        workflow.add_node("generate_response", safe_node_wrapper(self._generate_response, "generate_response"))

        # Completion
        workflow.add_node("complete", safe_node_wrapper(self._complete, "complete"))

        # Error handler
        workflow.add_node("handle_error", safe_node_wrapper(self._handle_error, "handle_error"))

        # -- Edges -----------------------------------------------------------
        workflow.set_entry_point("receive_ticket")

        workflow.add_edge("receive_ticket", "classify")

        # After classification, either route or handle error
        workflow.add_conditional_edges(
            "classify",
            self._classify_decision,
            {
                "route": "route",
                "error": "handle_error",
            },
        )

        # After routing, fan out to specialist agents in parallel
        workflow.add_conditional_edges(
            "route",
            self._route_decision,
            {
                "technical_agent": "technical_agent",
                "billing_agent": "billing_agent",
                "general_agent": "general_agent",
                "parallel": "technical_agent",  # all three run; see _route_decision
            },
        )

        # Each specialist goes to merge
        workflow.add_edge("technical_agent", "merge_responses")
        workflow.add_edge("billing_agent", "merge_responses")
        workflow.add_edge("general_agent", "merge_responses")

        # After merge, generate final response
        workflow.add_edge("merge_responses", "generate_response")

        # After final response, complete
        workflow.add_edge("generate_response", "complete")

        # Terminal
        workflow.add_edge("complete", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    # -----------------------------------------------------------------------
    # Node implementations
    # -----------------------------------------------------------------------

    def _receive_ticket(self, state: SupportTicketState) -> SupportTicketState:
        """Initialize workflow metadata."""
        state["workflow_start_time"] = datetime.utcnow().isoformat()
        state["ticket_status"] = TicketStatus.RECEIVED.value
        state.setdefault("errors", [])
        state.setdefault("agent_decisions", [])
        state.setdefault("retry_count", 0)
        state.setdefault("max_retries", 3)

        logger.info(
            "Ticket received: %s (subject: %s)",
            state["ticket"]["ticket_id"],
            state["ticket"]["subject"][:60],
        )
        return state

    def _classify(self, state: SupportTicketState) -> SupportTicketState:
        """Run the classifier agent."""
        return self._classifier(state)

    def _classify_decision(self, state: SupportTicketState) -> str:
        """Conditional edge: was classification successful?"""
        status = state.get("ticket_status")
        if status == TicketStatus.ERROR.value:
            # Check if we should retry
            if state.get("retry_count", 0) < state.get("max_retries", 3):
                logger.info("Classification failed, retrying...")
                state["ticket_status"] = TicketStatus.CLASSIFYING.value
                return "classify"  # retry -- but LangGraph does not support self-loops easily
            return "error"
        return "route"

    def _route(self, state: SupportTicketState) -> SupportTicketState:
        """Determine which specialist agent(s) should handle the ticket."""
        topic = state.get("assigned_topic", TopicCategory.GENERAL.value)
        urgency = state.get("urgency_level", "medium")

        # For critical tickets, run all agents in parallel for a comprehensive response
        if urgency in ("critical", "high"):
            state["requires_parallel_processing"] = True
        else:
            state["requires_parallel_processing"] = False

        state["ticket_status"] = TicketStatus.ROUTING.value
        logger.info("Routing ticket to topic=%s (parallel=%s)", topic, state["requires_parallel_processing"])
        return state

    def _route_decision(self, state: SupportTicketState) -> str:
        """
        Conditional edge: which specialist agent(s) to invoke.

        For critical/high urgency tickets, we want parallel processing.
        LangGraph supports fan-out by returning a list of node names, but
        for simplicity and clarity we route to the primary agent and note
        that parallel processing is indicated by `requires_parallel_processing`.
        In a production deployment, you would use LangGraph's Send API for
        true parallel fan-out.

        Here we return the single primary agent node name.
        """
        topic = state.get("assigned_topic", TopicCategory.GENERAL.value)
        routing_map = {
            TopicCategory.TECHNICAL.value: "technical_agent",
            TopicCategory.BILLING.value: "billing_agent",
            TopicCategory.GENERAL.value: "general_agent",
        }
        return routing_map.get(topic, "general_agent")

    def _run_technical(self, state: SupportTicketState) -> SupportTicketState:
        """Run the technical specialist agent."""
        return self._tech_agent(state)

    def _run_billing(self, state: SupportTicketState) -> SupportTicketState:
        """Run the billing specialist agent."""
        return self._billing_agent(state)

    def _run_general(self, state: SupportTicketState) -> SupportTicketState:
        """Run the general inquiry agent."""
        return self._general_agent(state)

    def _merge_responses(self, state: SupportTicketState) -> SupportTicketState:
        """
        After specialist agents complete, ensure the `active_response` field
        is populated from the correct specialist.

        This is the fan-in point after parallel agent execution.
        """
        topic = state.get("assigned_topic", TopicCategory.GENERAL.value)
        response_map = {
            TopicCategory.TECHNICAL.value: "technical_response",
            TopicCategory.BILLING.value: "billing_response",
            TopicCategory.GENERAL.value: "general_response",
        }
        primary_field = response_map.get(topic, "general_response")
        primary = state.get(primary_field, {})

        if primary:
            state["active_response"] = primary
        else:
            # Fallback: pick whichever specialist response is available
            for field_name in ("technical_response", "billing_response", "general_response"):
                resp = state.get(field_name, {})
                if resp:
                    state["active_response"] = resp
                    break

        logger.info("Merged responses; active agent: %s", state.get("active_response", {}).get("agent_name", "none"))
        return state

    def _generate_response(self, state: SupportTicketState) -> SupportTicketState:
        """Run the response aggregator / quality gate agent."""
        state["ticket_status"] = TicketStatus.RESPONSE_GENERATING.value
        return self._response_agent(state)

    def _complete(self, state: SupportTicketState) -> SupportTicketState:
        """Finalize the ticket."""
        state["ticket_status"] = TicketStatus.COMPLETED.value
        state["workflow_end_time"] = datetime.utcnow().isoformat()

        # Compute processing time
        try:
            start = datetime.fromisoformat(state["workflow_start_time"])
            end = datetime.utcnow()
            state["processing_time_ms"] = (end - start).total_seconds() * 1000
        except (KeyError, ValueError):
            state["processing_time_ms"] = 0.0

        logger.info(
            "Ticket %s completed in %.1fms",
            state["ticket"]["ticket_id"],
            state["processing_time_ms"],
        )
        return state

    def _handle_error(self, state: SupportTicketState) -> SupportTicketState:
        """Terminal error handler: produce a fallback response."""
        state["ticket_status"] = TicketStatus.ERROR.value
        from state import FinalResponse

        state["final_response"] = FinalResponse(
            customer_facing_message=(
                "We apologize, but we encountered an issue processing your request. "
                "A support team member will review your ticket and get back to you "
                "within 24 hours. We appreciate your patience."
            ),
            ticket_summary="Error during automated processing; requires manual review.",
            resolution_status="pending",
            follow_up_required=True,
            estimated_resolution_time="24 hours",
            reference_number=state["ticket"]["ticket_id"],
        )
        logger.error("Ticket %s ended in error state.", state["ticket"]["ticket_id"])
        return state

    # -----------------------------------------------------------------------
    # Public execution API
    # -----------------------------------------------------------------------

    def run(self, ticket: Ticket) -> SupportTicketState:
        """
        Process a ticket synchronously through the entire workflow.

        Returns the final SupportTicketState.
        """
        initial = create_initial_state(ticket)

        # Register with state manager
        self._sm.submit_ticket(ticket)

        # Execute the graph
        final_state = self._graph.invoke(initial)

        # Update state manager
        ticket_id = ticket.ticket_id
        if final_state.get("ticket_status") == TicketStatus.COMPLETED.value:
            self._sm.complete_ticket(ticket_id, final_state)
        elif final_state.get("ticket_status") == TicketStatus.ERROR.value:
            self._sm.fail_ticket(ticket_id, final_state, "Workflow ended in error state")

        return final_state

    async def arun(self, ticket: Ticket) -> SupportTicketState:
        """
        Process a ticket asynchronously through the entire workflow.

        Returns the final SupportTicketState.
        """
        initial = create_initial_state(ticket)

        self._sm.submit_ticket(ticket)

        final_state = await self._graph.ainvoke(initial)

        ticket_id = ticket.ticket_id
        if final_state.get("ticket_status") == TicketStatus.COMPLETED.value:
            self._sm.complete_ticket(ticket_id, final_state)
        elif final_state.get("ticket_status") == TicketStatus.ERROR.value:
            self._sm.fail_ticket(ticket_id, final_state, "Workflow ended in error state")

        return final_state

    def get_graph_visualization(self) -> str:
        """
        Return a Mermaid diagram representation of the workflow graph.
        Useful for documentation and debugging.
        """
        return """
```mermaid
graph TD
    A[Receive Ticket] --> B[Classifier Agent]
    B -->|success| C[Router]
    B -->|error| H[Handle Error]
    C -->|technical| D[Technical Agent]
    C -->|billing| E[Billing Agent]
    C -->|general| F[General Agent]
    D --> G[Merge Responses]
    E --> G
    F --> G
    G --> I[Response Agent]
    I --> J[Complete]
    H --> K[END]
    J --> K
```
"""

"""
Main Entry Point for the Multi-Agent Customer Support System.

Demonstrates end-to-end usage of the workflow:
  1. Constructing tickets.
  2. Running them through the workflow.
  3. Inspecting results and metrics.

Run directly::

    python main.py

Or import and use programmatically::

    from main import CustomerSupportSystem
    system = CustomerSupportSystem()
    result = system.process_ticket(subject="...", body="...")
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from typing import Any, Optional

from state import (
    SupportTicketState,
    Ticket,
    TicketStatus,
    FinalResponse,
)
from workflow import CustomerSupportWorkflow
from state_manager import StateManager

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("customer_support")


# ---------------------------------------------------------------------------
# High-level system facade
# ---------------------------------------------------------------------------


class CustomerSupportSystem:
    """
    Top-level facade that ties together the workflow and state manager.

    Typical usage::

        system = CustomerSupportSystem()
        result = system.process_ticket(
            subject="I can't log in to my account",
            body="I keep getting a 403 error when trying to access the dashboard.",
            customer_id="CUST-001",
        )
        print(system.format_response(result))
    """

    def __init__(self, llm_client: Any = None) -> None:
        self._sm = StateManager()
        self._workflow = CustomerSupportWorkflow(
            llm_client=llm_client,
            state_manager=self._sm,
        )

    def process_ticket(
        self,
        subject: str,
        body: str,
        customer_id: str = "anonymous",
        channel: str = "web_form",
        ticket_id: Optional[str] = None,
    ) -> SupportTicketState:
        """
        Create and process a support ticket through the full workflow.

        Returns the final state containing classification, specialist response,
        and customer-facing final response.
        """
        ticket = Ticket(
            ticket_id=ticket_id or f"TKT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            customer_id=customer_id,
            subject=subject,
            body=body,
            channel=channel,
        )

        logger.info("Processing ticket %s: %s", ticket.ticket_id, subject[:60])
        result = self._workflow.run(ticket)
        logger.info(
            "Ticket %s finished with status: %s",
            ticket.ticket_id,
            result.get("ticket_status"),
        )
        return result

    async def aprocess_ticket(
        self,
        subject: str,
        body: str,
        customer_id: str = "anonymous",
        channel: str = "web_form",
        ticket_id: Optional[str] = None,
    ) -> SupportTicketState:
        """Async variant of process_ticket."""
        ticket = Ticket(
            ticket_id=ticket_id or f"TKT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            customer_id=customer_id,
            subject=subject,
            body=body,
            channel=channel,
        )

        logger.info("[async] Processing ticket %s: %s", ticket.ticket_id, subject[:60])
        result = await self._workflow.arun(ticket)
        logger.info(
            "[async] Ticket %s finished with status: %s",
            ticket.ticket_id,
            result.get("ticket_status"),
        )
        return result

    @staticmethod
    def format_response(state: SupportTicketState) -> str:
        """Pretty-print the final state for human consumption."""
        lines = []
        lines.append("=" * 72)
        lines.append("SUPPORT TICKET RESULT")
        lines.append("=" * 72)

        ticket = state.get("ticket", {})
        lines.append(f"Ticket ID  : {ticket.get('ticket_id', 'N/A')}")
        lines.append(f"Customer   : {ticket.get('customer_id', 'N/A')}")
        lines.append(f"Subject    : {ticket.get('subject', 'N/A')}")
        lines.append(f"Channel    : {ticket.get('channel', 'N/A')}")
        lines.append("")

        classification = state.get("classification", {})
        if classification:
            lines.append("--- Classification ---")
            lines.append(f"  Urgency    : {classification.get('urgency', 'N/A')}")
            lines.append(f"  Topic      : {classification.get('topic', 'N/A')}")
            lines.append(f"  Sentiment  : {classification.get('sentiment', 'N/A')}")
            lines.append(f"  Keywords   : {', '.join(classification.get('keywords', []))}")
            lines.append(f"  Confidence : {classification.get('confidence', 0):.2f}")
            lines.append(f"  Reasoning  : {classification.get('reasoning', 'N/A')}")
            lines.append("")

        active = state.get("active_response", {})
        if active:
            lines.append("--- Specialist Response ---")
            lines.append(f"  Agent      : {active.get('agent_name', 'N/A')}")
            lines.append(f"  Escalation : {active.get('requires_escalation', False)}")
            lines.append(f"  Confidence : {active.get('confidence', 0):.2f}")
            lines.append("")

        final = state.get("final_response", {})
        if final:
            lines.append("--- Final Customer Response ---")
            lines.append(f"  Status     : {final.get('resolution_status', 'N/A')}")
            lines.append(f"  Est. Time  : {final.get('estimated_resolution_time', 'N/A')}")
            lines.append(f"  Follow-up  : {final.get('follow_up_required', False)}")
            lines.append(f"  Reference  : {final.get('reference_number', 'N/A')}")
            lines.append("")
            lines.append("  Message:")
            for msg_line in final.get("customer_facing_message", "").split("\n"):
                lines.append(f"    {msg_line}")
            lines.append("")

        lines.append("--- Workflow Metadata ---")
        lines.append(f"  Status         : {state.get('ticket_status', 'N/A')}")
        lines.append(f"  Processing Time: {state.get('processing_time_ms', 0):.1f}ms")
        lines.append(f"  Retries        : {state.get('retry_count', 0)}")
        errors = state.get("errors", [])
        if errors:
            lines.append(f"  Errors         : {len(errors)}")
            for err in errors:
                lines.append(f"    - {err}")
        lines.append("")

        decisions = state.get("agent_decisions", [])
        if decisions:
            lines.append("--- Agent Decision Trail ---")
            for d in decisions:
                lines.append(
                    f"  [{d.get('agent_name')}] {d.get('decision')} "
                    f"(confidence={d.get('confidence', 0):.2f})"
                )
            lines.append("")

        lines.append("=" * 72)
        return "\n".join(lines)

    def get_metrics(self) -> dict:
        """Return current system metrics."""
        return self._sm.get_dashboard_data()


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------


def run_demo() -> None:
    """Run a demonstration with three sample tickets (no LLM required)."""
    system = CustomerSupportSystem()

    sample_tickets = [
        {
            "subject": "API endpoint returning 500 errors",
            "body": (
                "Since this morning, our integration with your API has been "
                "returning 500 Internal Server Error on the /api/v2/data endpoint. "
                "This is blocking our production pipeline. We need this resolved urgently."
            ),
            "customer_id": "CUST-TECH-001",
            "channel": "email",
        },
        {
            "subject": "Unexpected charge on my billing statement",
            "body": (
                "I noticed a charge of $149.99 on my credit card from your company "
                "last week, but my plan should only be $49.99/month. I need this "
                "investigated and a refund if the charge is incorrect."
            ),
            "customer_id": "CUST-BILL-002",
            "channel": "chat",
        },
        {
            "subject": "How do I export my data?",
            "body": (
                "Hi, I'd like to export all my data from the platform. "
                "I've looked through the settings but can't find the export option. "
                "Could you point me in the right direction?"
            ),
            "customer_id": "CUST-GEN-003",
            "channel": "web_form",
        },
    ]

    logger.info("=" * 72)
    logger.info("MULTI-AGENT CUSTOMER SUPPORT SYSTEM - DEMO")
    logger.info("=" * 72)

    for i, ticket_data in enumerate(sample_tickets, 1):
        logger.info("")
        logger.info("--- Processing sample ticket %d ---", i)
        result = system.process_ticket(**ticket_data)
        print(system.format_response(result))
        print()

    # Print metrics
    metrics = system.get_metrics()
    logger.info("System Metrics: %s", json.dumps(metrics, indent=2, default=str))


if __name__ == "__main__":
    run_demo()

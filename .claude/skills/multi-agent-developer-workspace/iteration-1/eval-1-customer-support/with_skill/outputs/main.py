"""
Customer Support Multi-Agent System -- Main Entry Point
========================================================
Demonstrates the full pipeline:

  1. Create a ticket via ``StateManager``
  2. Execute the LangGraph workflow
  3. Inspect the final state (classification, agent outputs, response)
  4. Persist the result

Run directly to see the system in action (uses the deterministic stubs
since no LLM is wired)::

    python main.py
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pprint import pformat
from typing import Any

# -- local imports ----------------------------------------------------------
from state import SupportTicketState, TicketStatus
from state_manager import FilePersistence, StateManager, TicketMemory
from workflow import create_workflow

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("customer_support")


# ---------------------------------------------------------------------------
# Pretty-print helper
# ---------------------------------------------------------------------------

def _print_section(title: str, data: Any) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    if isinstance(data, dict):
        print(pformat(data, width=80, sort_dicts=False))
    else:
        print(data)


def _print_final_response(state: dict[str, Any]) -> None:
    final = state.get("final_response", {})
    if not final:
        print("\n[!] No final response was generated.")
        return

    print(f"\n{'='*60}")
    print("  FINAL CUSTOMER RESPONSE")
    print(f"{'='*60}")
    print(f"  Subject : {final.get('subject', 'N/A')}")
    print(f"  Tone    : {final.get('tone', 'N/A')}")
    print(f"{'-'*60}")
    print(final.get("body", "(empty)"))
    print(f"{'-'*60}")

    internal = final.get("internal_notes")
    if internal:
        print(f"\n  [INTERNAL NOTES] {internal}")

    steps = final.get("next_steps", [])
    if steps:
        print("\n  [NEXT STEPS]")
        for step in steps:
            print(f"    - {step}")


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_ticket(
    customer_name: str,
    customer_email: str,
    subject: str,
    message: str,
    *,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    End-to-end execution of one support ticket through the multi-agent
    workflow.

    Parameters
    ----------
    customer_name, customer_email, subject, message : str
        Ticket payload.
    verbose : bool
        If ``True``, print intermediate state to stdout.

    Returns
    -------
    dict
        The final workflow state.
    """
    # 1. State manager + ticket creation
    persistence = FilePersistence(base_path="./ticket_states")
    memory = TicketMemory()
    sm = StateManager(persistence=persistence, memory=memory)

    state = sm.create_ticket(
        customer_name=customer_name,
        customer_email=customer_email,
        subject=subject,
        message=message,
    )

    if verbose:
        _print_section("INITIAL STATE", state)

    # 2. Build and run the workflow
    app = create_workflow()
    logger.info("Invoking workflow for ticket %s ...", state["ticket_id"])

    result: dict[str, Any] = app.invoke(state)

    if verbose:
        _print_section("CLASSIFICATION", result.get("classification", {}))
        _print_section(
            "AGENT OUTPUTS",
            [
                {k: v for k, v in out.items() if k != "response_text"}
                for out in result.get("agent_outputs", [])
            ],
        )
        _print_final_response(result)
        _print_section("FINAL STATE KEYS", list(result.keys()))
        if result.get("errors"):
            _print_section("ERRORS", result["errors"])

    # 3. Persist
    sm.persist(result)
    sm.record_completion(result)
    logger.info("Ticket %s completed with status=%s", result["ticket_id"], result.get("status"))

    return result


# ---------------------------------------------------------------------------
# Demo tickets
# ---------------------------------------------------------------------------

DEMO_TICKETS = [
    {
        "customer_name": "Alice Chen",
        "customer_email": "alice@example.com",
        "subject": "API returning 500 errors - production down",
        "message": (
            "Hi, our production app has been getting 500 errors from your "
            "API endpoint /v2/data since this morning. This is critical -- "
            "we're losing customers. Error logs show: "
            "'ConnectionError: upstream timeout'. Please help ASAP."
        ),
    },
    {
        "customer_name": "Bob Martinez",
        "customer_email": "bob@example.com",
        "subject": "Charged twice for my subscription",
        "message": (
            "I noticed two charges of $49.99 on my credit card statement "
            "this month for my Pro subscription. Invoice numbers are "
            "INV-2024-1103 and INV-2024-1104. Can you please refund the "
            "duplicate charge?"
        ),
    },
    {
        "customer_name": "Carol Park",
        "customer_email": "carol@example.com",
        "subject": "How do I export my data?",
        "message": (
            "Hello! I'd like to export all my project data to CSV. "
            "I've looked through the settings but can't find the export "
            "option. Could you point me in the right direction?"
        ),
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  CUSTOMER SUPPORT MULTI-AGENT SYSTEM")
    print("  LangGraph Workflow Demonstration")
    print("=" * 60)

    results = []
    for i, ticket in enumerate(DEMO_TICKETS, 1):
        print(f"\n\n{'#'*60}")
        print(f"  TICKET {i}/{len(DEMO_TICKETS)}")
        print(f"{'#'*60}")
        result = run_ticket(**ticket, verbose=True)
        results.append(result)

    # Summary
    print(f"\n\n{'='*60}")
    print("  SESSION SUMMARY")
    print(f"{'='*60}")
    for r in results:
        final = r.get("final_response", {})
        print(
            f"  {r['ticket_id']}  |  "
            f"{r.get('urgency', '?'):>8}  |  "
            f"{r.get('topic', '?'):>10}  |  "
            f"{r.get('status', '?'):>12}  |  "
            f"{final.get('subject', 'N/A')}"
        )


if __name__ == "__main__":
    main()

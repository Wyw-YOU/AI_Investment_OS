"""
State Management System
=======================
Provides ``StateManager`` -- a thin orchestration layer that wraps the
LangGraph workflow and offers:

* State creation with sensible defaults
* Phase transition validation
* Persistence hooks (file-based / database)
* Short-term memory for in-flight ticket context
* Long-term memory for cross-ticket analytics

The ``StateManager`` is *not* part of the LangGraph graph itself; it
lives one level above and is called by the API / entry-point.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from state import (
    SupportTicketState,
    TicketStatus,
    create_initial_state,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# File-based persistence
# ---------------------------------------------------------------------------

class FilePersistence:
    """
    Simple JSON-file state persistence.

    Each ticket is stored as ``<base_path>/<ticket_id>.json``.
    """

    def __init__(self, base_path: str = "./ticket_states") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_state(self, ticket_id: str, state: dict[str, Any]) -> Path:
        file_path = self.base_path / f"{ticket_id}.json"
        with open(file_path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, default=str)
        logger.debug("Persisted state for ticket %s", ticket_id)
        return file_path

    def load_state(self, ticket_id: str) -> Optional[dict[str, Any]]:
        file_path = self.base_path / f"{ticket_id}.json"
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def list_tickets(self) -> list[str]:
        return [p.stem for p in self.base_path.glob("*.json")]


# ---------------------------------------------------------------------------
# Short-term / episodic memory
# ---------------------------------------------------------------------------

class TicketMemory:
    """
    In-memory store for recent ticket interactions.

    Useful for giving agents access to similar past tickets when
    drafting responses (episodic memory pattern from the skill).
    """

    def __init__(self, max_size: int = 500) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._order: list[str] = []
        self._max_size = max_size

    def record(self, ticket_id: str, summary: dict[str, Any]) -> None:
        self._store[ticket_id] = {
            **summary,
            "recorded_at": datetime.utcnow().isoformat(),
        }
        self._order.append(ticket_id)
        # Evict oldest when over capacity
        while len(self._order) > self._max_size:
            evicted = self._order.pop(0)
            self._store.pop(evicted, None)

    def get(self, ticket_id: str) -> Optional[dict[str, Any]]:
        return self._store.get(ticket_id)

    def recent(self, n: int = 10) -> list[dict[str, Any]]:
        return [self._store[tid] for tid in self._order[-n:] if tid in self._store]

    def search_by_topic(self, topic: str) -> list[dict[str, Any]]:
        return [v for v in self._store.values() if v.get("topic") == topic]


# ---------------------------------------------------------------------------
# Valid phase transitions
# ---------------------------------------------------------------------------

_VALID_TRANSITIONS: dict[str, list[str]] = {
    TicketStatus.PENDING.value: [TicketStatus.CLASSIFYING.value, TicketStatus.FAILED.value],
    TicketStatus.CLASSIFYING.value: [TicketStatus.ROUTING.value, TicketStatus.FAILED.value],
    TicketStatus.ROUTING.value: [
        TicketStatus.IN_PROGRESS.value,
        TicketStatus.AWAITING_RESPONSE.value,
        TicketStatus.FAILED.value,
    ],
    TicketStatus.IN_PROGRESS.value: [
        TicketStatus.AWAITING_RESPONSE.value,
        TicketStatus.COMPLETED.value,
        TicketStatus.ESCALATED.value,
        TicketStatus.FAILED.value,
    ],
    TicketStatus.AWAITING_RESPONSE.value: [
        TicketStatus.COMPLETED.value,
        TicketStatus.ESCALATED.value,
        TicketStatus.FAILED.value,
    ],
    TicketStatus.COMPLETED.value: [],
    TicketStatus.ESCALATED.value: [],
    TicketStatus.FAILED.value: [],
}


# ---------------------------------------------------------------------------
# StateManager
# ---------------------------------------------------------------------------

class StateManager:
    """
    High-level helper for creating, transitioning, and persisting
    ticket states.

    Parameters
    ----------
    persistence : FilePersistence or None
        Optional persistence backend.
    memory : TicketMemory or None
        Optional episodic memory store.
    """

    def __init__(
        self,
        persistence: Optional[FilePersistence] = None,
        memory: Optional[TicketMemory] = None,
    ) -> None:
        self.persistence = persistence or FilePersistence()
        self.memory = memory or TicketMemory()

    # -- creation -----------------------------------------------------------

    def create_ticket(
        self,
        customer_name: str,
        customer_email: str,
        subject: str,
        message: str,
        ticket_id: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> SupportTicketState:
        """Create a new ticket state and persist it."""
        tid = ticket_id or f"TKT-{uuid.uuid4().hex[:8].upper()}"
        cid = customer_id or f"CUST-{uuid.uuid4().hex[:6].upper()}"

        state = create_initial_state(
            ticket_id=tid,
            customer_id=cid,
            customer_name=customer_name,
            customer_email=customer_email,
            subject=subject,
            customer_message=message,
        )

        self.persistence.save_state(tid, dict(state))
        logger.info("Created ticket %s for %s", tid, customer_email)
        return state

    # -- transitions --------------------------------------------------------

    def transition(
        self,
        state: SupportTicketState,
        target_status: str,
    ) -> SupportTicketState:
        """
        Validate and apply a status transition.

        Raises ``ValueError`` if the transition is invalid.
        """
        current = state.get("status", TicketStatus.PENDING.value)
        allowed = _VALID_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise ValueError(
                f"Invalid transition: {current} -> {target_status}. "
                f"Allowed: {allowed}"
            )
        new_state: SupportTicketState = {
            **state,  # type: ignore[typeddict-item]
            "status": target_status,
        }
        return new_state

    # -- persistence --------------------------------------------------------

    def persist(self, state: SupportTicketState) -> None:
        self.persistence.save_state(state["ticket_id"], dict(state))

    def load(self, ticket_id: str) -> Optional[SupportTicketState]:
        return self.persistence.load_state(ticket_id)

    # -- memory -------------------------------------------------------------

    def record_completion(self, state: SupportTicketState) -> None:
        """Store a summary in episodic memory after ticket completion."""
        self.memory.record(
            state["ticket_id"],
            {
                "ticket_id": state["ticket_id"],
                "customer_id": state.get("customer_id"),
                "topic": state.get("topic"),
                "urgency": state.get("urgency"),
                "subject": state.get("subject"),
                "resolution_summary": (
                    state.get("final_response", {}).get("body", "")[:200]
                ),
            },
        )

    def get_similar_tickets(
        self, topic: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Retrieve recent tickets with the same topic (episodic memory)."""
        return self.memory.search_by_topic(topic)[:limit]

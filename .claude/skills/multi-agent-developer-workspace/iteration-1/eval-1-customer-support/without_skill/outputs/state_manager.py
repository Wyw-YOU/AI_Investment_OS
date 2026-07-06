"""
State Management System for the Multi-Agent Customer Support System.

Provides:
  1. In-memory ticket store with CRUD operations.
  2. Workflow lifecycle tracking (status transitions, timing).
  3. Audit trail of every agent decision.
  4. Query helpers for metrics and monitoring.
  5. A persistence interface that can be swapped for a database backend.
"""

from __future__ import annotations

import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from state import (
    AgentDecision,
    SupportTicketState,
    Ticket,
    TicketStatus,
    create_initial_state,
)

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------


class TicketStore:
    """
    Thread-safe in-memory store for ticket states.

    Production deployments should replace this with a database-backed
    implementation that satisfies the same interface.
    """

    def __init__(self) -> None:
        self._store: dict[str, SupportTicketState] = {}
        self._lock = threading.Lock()

    # -- CRUD ----------------------------------------------------------------

    def create(self, ticket: Ticket) -> SupportTicketState:
        """Create a new ticket and return its initial state."""
        state = create_initial_state(ticket)
        with self._lock:
            self._store[ticket.ticket_id] = state
        logger.info("Ticket created: %s", ticket.ticket_id)
        return state

    def get(self, ticket_id: str) -> Optional[SupportTicketState]:
        """Retrieve a ticket's current state."""
        with self._lock:
            return self._store.get(ticket_id)

    def update(self, ticket_id: str, state: SupportTicketState) -> None:
        """Overwrite the state for an existing ticket."""
        with self._lock:
            if ticket_id not in self._store:
                raise KeyError(f"Ticket {ticket_id} not found")
            self._store[ticket_id] = state
        logger.debug("Ticket updated: %s (status=%s)", ticket_id, state.get("ticket_status"))

    def delete(self, ticket_id: str) -> bool:
        """Delete a ticket. Returns True if it existed."""
        with self._lock:
            existed = ticket_id in self._store
            self._store.pop(ticket_id, None)
        return existed

    def list_all(self) -> list[SupportTicketState]:
        """Return all ticket states."""
        with self._lock:
            return list(self._store.values())

    def count(self) -> int:
        with self._lock:
            return len(self._store)

    # -- Query helpers -------------------------------------------------------

    def get_by_status(self, status: str) -> list[SupportTicketState]:
        """Return all tickets with the given status."""
        with self._lock:
            return [s for s in self._store.values() if s.get("ticket_status") == status]

    def get_by_urgency(self, urgency: str) -> list[SupportTicketState]:
        """Return all tickets with the given urgency level."""
        with self._lock:
            return [s for s in self._store.values() if s.get("urgency_level") == urgency]

    def get_by_topic(self, topic: str) -> list[SupportTicketState]:
        """Return all tickets with the given topic."""
        with self._lock:
            return [s for s in self._store.values() if s.get("assigned_topic") == topic]

    def get_error_tickets(self) -> list[SupportTicketState]:
        """Return all tickets in error state."""
        return self.get_by_status(TicketStatus.ERROR.value)


# ---------------------------------------------------------------------------
# Workflow Lifecycle Tracker
# ---------------------------------------------------------------------------


@dataclass
class LifecycleEvent:
    ticket_id: str
    from_status: str
    to_status: str
    timestamp: str
    agent: str
    notes: str = ""


class LifecycleTracker:
    """
    Records every status transition for every ticket, providing a full
    audit trail of how each ticket was processed.
    """

    def __init__(self) -> None:
        self._events: list[LifecycleEvent] = []
        self._lock = threading.Lock()

    def record_transition(
        self,
        ticket_id: str,
        from_status: str,
        to_status: str,
        agent: str,
        notes: str = "",
    ) -> None:
        event = LifecycleEvent(
            ticket_id=ticket_id,
            from_status=from_status,
            to_status=to_status,
            timestamp=datetime.utcnow().isoformat(),
            agent=agent,
            notes=notes,
        )
        with self._lock:
            self._events.append(event)
        logger.info(
            "Lifecycle: %s %s -> %s (by %s)",
            ticket_id,
            from_status,
            to_status,
            agent,
        )

    def get_history(self, ticket_id: str) -> list[LifecycleEvent]:
        with self._lock:
            return [e for e in self._events if e.ticket_id == ticket_id]

    def get_all_events(self) -> list[LifecycleEvent]:
        with self._lock:
            return list(self._events)


# ---------------------------------------------------------------------------
# Metrics Collector
# ---------------------------------------------------------------------------


@dataclass
class TicketMetrics:
    total_processed: int = 0
    by_status: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_topic: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_urgency: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    avg_processing_time_ms: float = 0.0
    error_count: int = 0
    escalation_count: int = 0


class MetricsCollector:
    """Aggregates metrics across all processed tickets."""

    def __init__(self) -> None:
        self._processing_times: list[float] = []
        self._lock = threading.Lock()
        self._metrics = TicketMetrics()

    def record_completion(self, state: SupportTicketState) -> None:
        """Record a completed ticket for metrics."""
        with self._lock:
            self._metrics.total_processed += 1

            status = state.get("ticket_status", "unknown")
            self._metrics.by_status[status] += 1

            topic = state.get("assigned_topic", "unknown")
            self._metrics.by_topic[topic] += 1

            urgency = state.get("urgency_level", "unknown")
            self._metrics.by_urgency[urgency] += 1

            proc_time = state.get("processing_time_ms", 0.0)
            if proc_time > 0:
                self._processing_times.append(proc_time)
                self._metrics.avg_processing_time_ms = (
                    sum(self._processing_times) / len(self._processing_times)
                )

            if status == TicketStatus.ERROR.value:
                self._metrics.error_count += 1

            # Check if final response indicates escalation
            final = state.get("final_response", {})
            if final.get("resolution_status") == "escalated":
                self._metrics.escalation_count += 1

    def get_metrics(self) -> TicketMetrics:
        with self._lock:
            return self._metrics

    def reset(self) -> None:
        with self._lock:
            self._metrics = TicketMetrics()
            self._processing_times.clear()


# ---------------------------------------------------------------------------
# Unified StateManager (composition of the above)
# ---------------------------------------------------------------------------


class StateManager:
    """
    High-level facade that composes the TicketStore, LifecycleTracker,
    and MetricsCollector into a single coherent interface consumed by
    the LangGraph workflow nodes.
    """

    def __init__(self) -> None:
        self.store = TicketStore()
        self.tracker = LifecycleTracker()
        self.metrics = MetricsCollector()
        self._callbacks: list[Callable[[str, SupportTicketState], None]] = []

    # -- Lifecycle-aware wrappers -------------------------------------------

    def submit_ticket(self, ticket: Ticket) -> SupportTicketState:
        """Create a ticket and record the RECEIVED lifecycle event."""
        state = self.store.create(ticket)
        self.tracker.record_transition(
            ticket_id=ticket.ticket_id,
            from_status="",
            to_status=TicketStatus.RECEIVED.value,
            agent="system",
            notes="Ticket submitted",
        )
        return state

    def transition_to(
        self,
        ticket_id: str,
        new_status: str,
        agent: str,
        notes: str = "",
    ) -> None:
        """Update the ticket status and record the lifecycle transition."""
        state = self.store.get(ticket_id)
        if state is None:
            raise KeyError(f"Ticket {ticket_id} not found")

        old_status = state.get("ticket_status", "")
        state["ticket_status"] = new_status
        self.store.update(ticket_id, state)

        self.tracker.record_transition(
            ticket_id=ticket_id,
            from_status=old_status,
            to_status=new_status,
            agent=agent,
            notes=notes,
        )

    def complete_ticket(self, ticket_id: str, state: SupportTicketState) -> None:
        """Mark a ticket as completed and record metrics."""
        state["ticket_status"] = TicketStatus.COMPLETED.value
        state["workflow_end_time"] = datetime.utcnow().isoformat()

        # Calculate processing time
        start = state.get("workflow_start_time")
        if start:
            try:
                start_dt = datetime.fromisoformat(start)
                end_dt = datetime.utcnow()
                state["processing_time_ms"] = (
                    (end_dt - start_dt).total_seconds() * 1000
                )
            except ValueError:
                pass

        self.store.update(ticket_id, state)
        self.metrics.record_completion(state)
        self.tracker.record_transition(
            ticket_id=ticket_id,
            from_status=TicketStatus.PROCESSING.value,
            to_status=TicketStatus.COMPLETED.value,
            agent="system",
            notes="Ticket completed",
        )
        self._notify_callbacks(ticket_id, state)

    def fail_ticket(self, ticket_id: str, state: SupportTicketState, error: str) -> None:
        """Mark a ticket as failed and record metrics."""
        state["ticket_status"] = TicketStatus.ERROR.value
        state.setdefault("errors", []).append(error)
        self.store.update(ticket_id, state)
        self.metrics.record_completion(state)
        self.tracker.record_transition(
            ticket_id=ticket_id,
            from_status=state.get("ticket_status", ""),
            to_status=TicketStatus.ERROR.value,
            agent="system",
            notes=f"Ticket failed: {error}",
        )
        self._notify_callbacks(ticket_id, state)

    # -- Callbacks -----------------------------------------------------------

    def register_callback(
        self, callback: Callable[[str, SupportTicketState], None]
    ) -> None:
        """Register a callback that fires when a ticket completes."""
        self._callbacks.append(callback)

    def _notify_callbacks(
        self, ticket_id: str, state: SupportTicketState
    ) -> None:
        for cb in self._callbacks:
            try:
                cb(ticket_id, state)
            except Exception as exc:
                logger.error("Callback error for ticket %s: %s", ticket_id, exc)

    # -- Queries -------------------------------------------------------------

    def get_dashboard_data(self) -> dict:
        """Return a snapshot of current system metrics for monitoring."""
        m = self.metrics.get_metrics()
        return {
            "total_processed": m.total_processed,
            "by_status": dict(m.by_status),
            "by_topic": dict(m.by_topic),
            "by_urgency": dict(m.by_urgency),
            "avg_processing_time_ms": round(m.avg_processing_time_ms, 2),
            "error_count": m.error_count,
            "escalation_count": m.escalation_count,
            "current_open_tickets": len(self.store.get_by_status(
                TicketStatus.PROCESSING.value
            )),
        }

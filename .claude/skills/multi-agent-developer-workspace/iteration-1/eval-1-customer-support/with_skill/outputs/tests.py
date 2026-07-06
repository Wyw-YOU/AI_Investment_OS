"""
Unit & Integration Tests for the Customer Support Multi-Agent System
=====================================================================
Run with::

    pytest tests.py -v

These tests verify:
  - State creation and transitions
  - Agent stub outputs (no LLM required)
  - Workflow end-to-end execution
  - Error handling paths
  - StateManager persistence and memory
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# -- local imports ----------------------------------------------------------
from state import (
    ClassificationResult,
    FinalResponse,
    SupportTicketState,
    TicketStatus,
    Topic,
    Urgency,
    create_initial_state,
)
from state_manager import FilePersistence, StateManager, TicketMemory
from base import AgentOutput, AgentExecutionError
from agents import (
    BillingAgent,
    ClassifierAgent,
    GeneralAgent,
    ResponseAgent,
    TechnicalAgent,
)
from error_handling import CircuitBreaker, safe_node, retry_with_backoff, merge_errors
from workflow import create_workflow


# ===================================================================
# 1. State Tests
# ===================================================================

class TestState:
    def test_create_initial_state(self):
        state = create_initial_state(
            ticket_id="TKT-001",
            customer_id="CUST-001",
            customer_name="Test User",
            customer_email="test@example.com",
            subject="Test Subject",
            customer_message="Hello, I need help.",
        )
        assert state["ticket_id"] == "TKT-001"
        assert state["customer_id"] == "CUST-001"
        assert state["customer_name"] == "Test User"
        assert state["customer_email"] == "test@example.com"
        assert state["subject"] == "Test Subject"
        assert state["customer_message"] == "Hello, I need help."
        assert state["status"] == TicketStatus.PENDING.value
        assert state["agent_outputs"] == []
        assert state["errors"] == []

    def test_state_immutability(self):
        state = create_initial_state(
            ticket_id="TKT-002",
            customer_id="CUST-002",
            customer_name="Test User",
            customer_email="test@example.com",
            subject="Test",
            customer_message="Msg",
        )
        # Simulate a node returning a new state (not mutating)
        new_state = {**state, "status": TicketStatus.CLASSIFYING.value}
        assert state["status"] == TicketStatus.PENDING.value
        assert new_state["status"] == TicketStatus.CLASSIFYING.value


# ===================================================================
# 2. Agent Stub Tests (no LLM)
# ===================================================================

class TestClassifierAgent:
    def setup_method(self):
        self.agent = ClassifierAgent()

    def test_classify_technical_critical(self):
        state = create_initial_state(
            ticket_id="T1", customer_id="C1",
            customer_name="A", customer_email="a@b.com",
            subject="API down",
            customer_message="Your API is returning 500 errors and our production app is down.",
        )
        result = self.agent.run(state)
        assert result["topic"] == Topic.TECHNICAL.value
        assert result["urgency"] == Urgency.CRITICAL.value

    def test_classify_billing(self):
        state = create_initial_state(
            ticket_id="T2", customer_id="C1",
            customer_name="A", customer_email="a@b.com",
            subject="Double charge",
            customer_message="I was charged twice for my subscription this month.",
        )
        result = self.agent.run(state)
        assert result["topic"] == Topic.BILLING.value

    def test_classify_general_low(self):
        state = create_initial_state(
            ticket_id="T3", customer_id="C1",
            customer_name="A", customer_email="a@b.com",
            subject="How to export",
            customer_message="How do I export my data to CSV?",
        )
        result = self.agent.run(state)
        assert result["topic"] == Topic.GENERAL.value
        assert result["urgency"] == Urgency.LOW.value

    def test_classification_has_required_fields(self):
        state = create_initial_state(
            ticket_id="T4", customer_id="C1",
            customer_name="A", customer_email="a@b.com",
            subject="Test",
            customer_message="Hello",
        )
        result = self.agent.run(state)
        cls = result["classification"]
        assert "urgency" in cls
        assert "topic" in cls
        assert "reasoning" in cls
        assert "confidence" in cls


class TestTechnicalAgent:
    def setup_method(self):
        self.agent = TechnicalAgent()

    def test_stub_response_structure(self):
        state = create_initial_state(
            ticket_id="T5", customer_id="C1",
            customer_name="A", customer_email="a@b.com",
            subject="API error",
            customer_message="Getting 500 errors from your API.",
        )
        result = self.agent.run(state)
        outputs = result["agent_outputs"]
        assert len(outputs) == 1
        out = outputs[0]
        assert out["agent_name"] == "technical_agent"
        assert "response_text" in out
        assert "actions_taken" in out
        assert "follow_up_questions" in out
        assert "confidence" in out


class TestBillingAgent:
    def setup_method(self):
        self.agent = BillingAgent()

    def test_stub_response_structure(self):
        state = create_initial_state(
            ticket_id="T6", customer_id="C1",
            customer_name="A", customer_email="a@b.com",
            subject="Double charge",
            customer_message="Charged twice for subscription.",
        )
        result = self.agent.run(state)
        outputs = result["agent_outputs"]
        assert len(outputs) == 1
        out = outputs[0]
        assert out["agent_name"] == "billing_agent"
        assert out["confidence"] > 0


class TestGeneralAgent:
    def setup_method(self):
        self.agent = GeneralAgent()

    def test_stub_response_structure(self):
        state = create_initial_state(
            ticket_id="T7", customer_id="C1",
            customer_name="Alice", customer_email="a@b.com",
            subject="Export question",
            customer_message="How do I export data?",
        )
        result = self.agent.run(state)
        outputs = result["agent_outputs"]
        assert len(outputs) == 1
        out = outputs[0]
        assert out["agent_name"] == "general_agent"
        assert "Alice" in out["response_text"]


class TestResponseAgent:
    def setup_method(self):
        self.agent = ResponseAgent()

    def test_finalise_with_draft(self):
        state = create_initial_state(
            ticket_id="T8", customer_id="C1",
            customer_name="Bob", customer_email="b@b.com",
            subject="Test",
            customer_message="Help please.",
        )
        state["urgency"] = "medium"
        state["topic"] = "general"
        state["agent_outputs"] = [{
            "agent_name": "general_agent",
            "response_text": "Here is some help.",
            "actions_taken": [],
            "follow_up_questions": [],
            "confidence": 0.7,
            "citations": [],
        }]
        result = self.agent.run(state)
        assert "final_response" in result
        final = result["final_response"]
        assert "subject" in final
        assert "body" in final
        assert "Bob" in final["body"]
        assert result["status"] == TicketStatus.COMPLETED.value

    def test_finalise_without_draft(self):
        state = create_initial_state(
            ticket_id="T9", customer_id="C1",
            customer_name="Carol", customer_email="c@b.com",
            subject="Test",
            customer_message="Help.",
        )
        # No agent_outputs -- should use fallback
        result = self.agent.run(state)
        assert "final_response" in result
        assert result["status"] == TicketStatus.ESCALATED.value


# ===================================================================
# 3. AgentOutput Pydantic Model Tests
# ===================================================================

class TestAgentOutput:
    def test_valid_output(self):
        output = AgentOutput(
            agent_name="test",
            result={"key": "value"},
            confidence=0.85,
            citations=["source1"],
        )
        assert output.agent_name == "test"
        assert 0 <= output.confidence <= 1

    def test_confidence_out_of_range(self):
        with pytest.raises(Exception):
            AgentOutput(
                agent_name="test",
                result={},
                confidence=1.5,
            )

    def test_empty_citations_warns(self):
        # Should not raise, but logs a warning
        output = AgentOutput(
            agent_name="test",
            result={},
            confidence=0.5,
            citations=[],
        )
        assert output.citations == []


# ===================================================================
# 4. Error Handling Tests
# ===================================================================

class TestSafeNode:
    def test_success_passes_through(self):
        def good_node(state):
            return {"result": "ok"}

        wrapped = safe_node("test", good_node)
        result = wrapped({"input": "data"})
        assert result["result"] == "ok"

    def test_failure_returns_fallback(self):
        def bad_node(state):
            raise ValueError("boom")

        wrapped = safe_node("test", bad_node, fallback={"default": True})
        result = wrapped({"input": "data"})
        assert result["default"] is True
        assert "test: boom" in result["errors"]

    def test_failure_returns_minimal_without_fallback(self):
        def bad_node(state):
            raise RuntimeError("crash")

        wrapped = safe_node("test", bad_node)
        result = wrapped({"input": "data"})
        assert "errors" in result
        assert "test: crash" in result["errors"]


class TestRetryWithBackoff:
    def test_success_on_first_try(self):
        counter = {"n": 0}
        def fn():
            counter["n"] += 1
            return "ok"
        assert retry_with_backoff(fn, max_retries=3) == "ok"
        assert counter["n"] == 1

    def test_success_after_retries(self):
        counter = {"n": 0}
        def fn():
            counter["n"] += 1
            if counter["n"] < 3:
                raise ValueError("not yet")
            return "done"
        # Use very short delay for tests
        assert retry_with_backoff(fn, max_retries=3, base_delay=0.01) == "done"
        assert counter["n"] == 3

    def test_all_retries_fail(self):
        def fn():
            raise ValueError("always fails")
        with pytest.raises(ValueError, match="always fails"):
            retry_with_backoff(fn, max_retries=2, base_delay=0.01)


class TestCircuitBreaker:
    def test_stays_closed_on_success(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        for _ in range(10):
            cb.call(lambda: "ok")
        assert cb.state == "closed"

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        for _ in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass
        assert cb.state == "open"

    def test_rejects_when_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60)
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass
        assert cb.state == "open"
        with pytest.raises(RuntimeError, match="Circuit breaker is OPEN"):
            cb.call(lambda: "ok")


class TestMergeErrors:
    def test_merge_with_existing(self):
        state = {"key": "val", "errors": ["old error"]}
        new = merge_errors(state, ["new error"])
        assert new["errors"] == ["old error", "new error"]
        # Original state unchanged
        assert state["errors"] == ["old error"]

    def test_merge_without_existing(self):
        state = {"key": "val"}
        new = merge_errors(state, ["first error"])
        assert new["errors"] == ["first error"]


# ===================================================================
# 5. StateManager Tests
# ===================================================================

class TestFilePersistence:
    def test_save_and_load(self, tmp_path):
        fp = FilePersistence(base_path=str(tmp_path))
        state = {"ticket_id": "T1", "status": "pending"}
        fp.save_state("T1", state)
        loaded = fp.load_state("T1")
        assert loaded["ticket_id"] == "T1"
        assert loaded["status"] == "pending"

    def test_load_missing(self, tmp_path):
        fp = FilePersistence(base_path=str(tmp_path))
        assert fp.load_state("NONEXISTENT") is None

    def test_list_tickets(self, tmp_path):
        fp = FilePersistence(base_path=str(tmp_path))
        fp.save_state("T1", {"id": "T1"})
        fp.save_state("T2", {"id": "T2"})
        tickets = fp.list_tickets()
        assert set(tickets) == {"T1", "T2"}


class TestTicketMemory:
    def test_record_and_get(self):
        mem = TicketMemory(max_size=100)
        mem.record("T1", {"topic": "billing", "urgency": "high"})
        result = mem.get("T1")
        assert result["topic"] == "billing"
        assert "recorded_at" in result

    def test_search_by_topic(self):
        mem = TicketMemory()
        mem.record("T1", {"topic": "billing"})
        mem.record("T2", {"topic": "technical"})
        mem.record("T3", {"topic": "billing"})
        billing = mem.search_by_topic("billing")
        assert len(billing) == 2

    def test_eviction(self):
        mem = TicketMemory(max_size=3)
        for i in range(5):
            mem.record(f"T{i}", {"topic": "general"})
        # Only last 3 should remain
        assert mem.get("T0") is None
        assert mem.get("T1") is None
        assert mem.get("T4") is not None


class TestStateManager:
    def test_create_ticket(self, tmp_path):
        sm = StateManager(
            persistence=FilePersistence(base_path=str(tmp_path)),
            memory=TicketMemory(),
        )
        state = sm.create_ticket(
            customer_name="Test User",
            customer_email="test@example.com",
            subject="Help",
            message="I need help.",
        )
        assert state["ticket_id"].startswith("TKT-")
        assert state["customer_id"].startswith("CUST-")
        assert state["status"] == TicketStatus.PENDING.value

    def test_valid_transition(self, tmp_path):
        sm = StateManager(
            persistence=FilePersistence(base_path=str(tmp_path)),
            memory=TicketMemory(),
        )
        state = sm.create_ticket(
            customer_name="T", customer_email="t@t.com",
            subject="S", message="M",
        )
        new_state = sm.transition(state, TicketStatus.CLASSIFYING.value)
        assert new_state["status"] == TicketStatus.CLASSIFYING.value

    def test_invalid_transition(self, tmp_path):
        sm = StateManager(
            persistence=FilePersistence(base_path=str(tmp_path)),
            memory=TicketMemory(),
        )
        state = sm.create_ticket(
            customer_name="T", customer_email="t@t.com",
            subject="S", message="M",
        )
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.transition(state, TicketStatus.COMPLETED.value)


# ===================================================================
# 6. Integration Test -- Full Workflow
# ===================================================================

class TestWorkflowIntegration:
    @pytest.fixture
    def workflow(self):
        return create_workflow()

    def test_technical_ticket_e2e(self, workflow):
        state = create_initial_state(
            ticket_id="E2E-001",
            customer_id="CUST-001",
            customer_name="Alice Chen",
            customer_email="alice@example.com",
            subject="API returning 500 errors",
            customer_message="Our production app is down due to 500 errors from your API. Please help!",
        )
        result = workflow.invoke(state)

        # Should be classified
        assert "classification" in result
        assert result["topic"] == Topic.TECHNICAL.value

        # Should have agent output
        assert len(result["agent_outputs"]) >= 1
        assert result["agent_outputs"][0]["agent_name"] == "technical_agent"

        # Should have final response
        assert "final_response" in result
        final = result["final_response"]
        assert "body" in final
        assert "Alice" in final["body"]

    def test_billing_ticket_e2e(self, workflow):
        state = create_initial_state(
            ticket_id="E2E-002",
            customer_id="CUST-002",
            customer_name="Bob Martinez",
            customer_email="bob@example.com",
            subject="Charged twice for subscription",
            customer_message="I was charged twice for my subscription this month. Please refund.",
        )
        result = workflow.invoke(state)

        assert result["topic"] == Topic.BILLING.value
        assert len(result["agent_outputs"]) >= 1
        assert result["agent_outputs"][0]["agent_name"] == "billing_agent"
        assert "final_response" in result

    def test_general_ticket_e2e(self, workflow):
        state = create_initial_state(
            ticket_id="E2E-003",
            customer_id="CUST-003",
            customer_name="Carol Park",
            customer_email="carol@example.com",
            subject="How to export data",
            customer_message="How do I export my data to CSV format?",
        )
        result = workflow.invoke(state)

        assert result["topic"] == Topic.GENERAL.value
        assert len(result["agent_outputs"]) >= 1
        assert result["agent_outputs"][0]["agent_name"] == "general_agent"

    def test_critical_ticket_escalation(self, workflow):
        state = create_initial_state(
            ticket_id="E2E-004",
            customer_id="CUST-004",
            customer_name="Dave",
            customer_email="dave@example.com",
            subject="Critical security breach",
            customer_message="We detected a critical security breach in your system affecting our data.",
        )
        result = workflow.invoke(state)

        assert result["urgency"] == Urgency.CRITICAL.value
        # Should be escalated
        assert result["status"] in [
            TicketStatus.ESCALATED.value,
            TicketStatus.COMPLETED.value,
        ]
        assert "final_response" in result

    def test_workflow_produces_no_unhandled_errors(self, workflow):
        """Even with edge-case input, the workflow should complete."""
        state = create_initial_state(
            ticket_id="E2E-005",
            customer_id="CUST-005",
            customer_name="",
            customer_email="",
            subject="",
            customer_message="",
        )
        result = workflow.invoke(state)
        # Should still produce a final response (even if generic)
        assert "final_response" in result
        assert result["final_response"].get("body")


# ===================================================================
# 7. Run with pytest
# ===================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

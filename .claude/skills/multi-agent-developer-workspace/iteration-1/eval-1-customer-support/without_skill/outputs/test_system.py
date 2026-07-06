"""
Tests for the Multi-Agent Customer Support System.

Run with:  python -m pytest test_system.py -v
Or:        python test_system.py
"""

from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime

# Ensure the output directory is on the path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import (
    AgentDecision,
    AgentResponse,
    ClassificationResult,
    FinalResponse,
    SupportTicketState,
    Ticket,
    TicketStatus,
    UrgencyLevel,
    TopicCategory,
    create_initial_state,
)
from parsers import (
    ValidationError,
    extract_json_from_text,
    parse_classification,
    parse_agent_response,
    parse_final_response,
)
from agents import (
    ClassifierAgent,
    TechnicalAgent,
    BillingAgent,
    GeneralAgent,
    ResponseAgent,
)
from state_manager import (
    TicketStore,
    LifecycleTracker,
    MetricsCollector,
    StateManager,
)
from error_handling import (
    CircuitBreaker,
    CircuitBreakerOpen,
    retry_with_backoff,
    record_agent_decision,
    record_error,
    MaxRetriesExceeded,
)
from workflow import CustomerSupportWorkflow
from main import CustomerSupportSystem


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

_pass = 0
_fail = 0


def _test(name: str, fn):
    global _pass, _fail
    try:
        fn()
        _pass += 1
        print(f"  PASS  {name}")
    except Exception as exc:
        _fail += 1
        print(f"  FAIL  {name}: {exc}")
        traceback.print_exc()


def assert_eq(a, b, msg=""):
    if a != b:
        raise AssertionError(f"{msg}: expected {b!r}, got {a!r}")


def assert_true(v, msg=""):
    if not v:
        raise AssertionError(f"{msg}: expected truthy, got {v!r}")


# ---------------------------------------------------------------------------
# 1. State schema tests
# ---------------------------------------------------------------------------

def test_ticket_creation():
    t = Ticket(subject="Test", body="Body", customer_id="C1")
    assert_true(t.ticket_id.startswith("TKT-"), "ticket_id prefix")
    assert_eq(t.subject, "Test", "subject")
    assert_eq(t.channel, "web_form", "default channel")


def test_initial_state():
    t = Ticket(subject="S", body="B")
    state = create_initial_state(t)
    assert_eq(state["ticket_status"], "received", "initial status")
    assert_eq(state["retry_count"], 0, "retry_count")
    assert_eq(state["errors"], [], "errors empty")


# ---------------------------------------------------------------------------
# 2. Parser tests
# ---------------------------------------------------------------------------

def test_extract_json_fenced():
    raw = 'Some text\n```json\n{"urgency": "high"}\n```\nMore text'
    result = extract_json_from_text(raw)
    assert_eq(result["urgency"], "high", "fenced json")


def test_extract_json_bare():
    raw = 'Here is the result: {"urgency": "low", "topic": "general"}'
    result = extract_json_from_text(raw)
    assert_eq(result["urgency"], "low", "bare json")


def test_parse_classification_valid():
    raw = json.dumps({
        "urgency": "high",
        "topic": "technical",
        "sentiment": "negative",
        "keywords": ["api", "error"],
        "confidence": 0.92,
        "reasoning": "API error reported",
    })
    parsed = parse_classification(raw)
    assert_eq(parsed.urgency, "high", "urgency")
    assert_eq(parsed.topic, "technical", "topic")
    assert_eq(parsed.confidence, 0.92, "confidence")
    result = parsed.to_result()
    assert_eq(result["urgency"], "high", "to_result urgency")


def test_parse_classification_invalid_urgency():
    raw = json.dumps({
        "urgency": "super-urgent",  # invalid
        "topic": "technical",
        "sentiment": "negative",
        "keywords": [],
        "confidence": 0.5,
        "reasoning": "test",
    })
    try:
        parse_classification(raw)
        raise AssertionError("Should have raised ValidationError")
    except ValidationError:
        pass  # expected


def test_parse_agent_response_valid():
    raw = json.dumps({
        "agent_name": "technical_agent",
        "response_text": "Try clearing your cache.",
        "follow_up_actions": ["Check logs"],
        "requires_escalation": False,
        "escalation_reason": "",
        "internal_notes": "Standard fix",
        "confidence": 0.85,
    })
    parsed = parse_agent_response(raw, "technical_agent")
    assert_eq(parsed.agent_name, "technical_agent", "agent name")
    resp = parsed.to_response()
    assert_eq(resp["response_text"], "Try clearing your cache.", "response text")


def test_parse_agent_response_wrong_agent():
    raw = json.dumps({
        "agent_name": "billing_agent",
        "response_text": "test",
        "confidence": 0.5,
    })
    try:
        parse_agent_response(raw, "technical_agent")
        raise AssertionError("Should have raised ValidationError")
    except ValidationError:
        pass  # expected


def test_parse_final_response_valid():
    raw = json.dumps({
        "customer_facing_message": "Dear customer, ...",
        "ticket_summary": "API issue resolved",
        "resolution_status": "resolved",
        "follow_up_required": False,
        "estimated_resolution_time": "N/A",
        "reference_number": "TKT-001",
    })
    parsed = parse_final_response(raw)
    assert_eq(parsed.resolution_status, "resolved", "resolution status")
    final = parsed.to_final()
    assert_eq(final["resolution_status"], "resolved", "to_final status")


# ---------------------------------------------------------------------------
# 3. Agent tests (deterministic fallback, no LLM)
# ---------------------------------------------------------------------------

def test_classifier_agent_deterministic():
    agent = ClassifierAgent()
    state = create_initial_state(Ticket(
        subject="API returning 500 errors - critical outage",
        body="Everything is down",
        customer_id="C1",
    ))
    state["ticket_status"] = "classifying"
    result = agent(state)
    cls = result.get("classification", {})
    assert_eq(cls.get("urgency"), "critical", "classifier urgency")
    assert_eq(cls.get("topic"), "technical", "classifier topic")


def test_technical_agent_deterministic():
    agent = TechnicalAgent()
    state = create_initial_state(Ticket(subject="Bug report", body="App crashes"))
    state["urgency_level"] = "high"
    state["assigned_topic"] = "technical"
    result = agent(state)
    resp = result.get("technical_response", {})
    assert_eq(resp.get("agent_name"), "technical_agent", "tech agent name")
    assert_true(len(resp.get("response_text", "")) > 0, "tech response not empty")


def test_billing_agent_deterministic():
    agent = BillingAgent()
    state = create_initial_state(Ticket(subject="Billing question", body="Charge issue"))
    state["urgency_level"] = "medium"
    state["assigned_topic"] = "billing"
    result = agent(state)
    resp = result.get("billing_response", {})
    assert_eq(resp.get("agent_name"), "billing_agent", "billing agent name")


def test_general_agent_deterministic():
    agent = GeneralAgent()
    state = create_initial_state(Ticket(subject="How to export data", body="Help"))
    state["urgency_level"] = "low"
    state["assigned_topic"] = "general"
    result = agent(state)
    resp = result.get("general_response", {})
    assert_eq(resp.get("agent_name"), "general_agent", "general agent name")


def test_response_agent_deterministic():
    agent = ResponseAgent()
    state = create_initial_state(Ticket(subject="Test", body="Body"))
    state["urgency_level"] = "medium"
    state["assigned_topic"] = "general"
    state["active_response"] = {
        "agent_name": "general_agent",
        "response_text": "Here is your answer.",
        "follow_up_actions": [],
        "requires_escalation": False,
        "escalation_reason": "",
        "internal_notes": "",
        "confidence": 0.8,
    }
    result = agent(state)
    final = result.get("final_response", {})
    assert_true(len(final.get("customer_facing_message", "")) > 0, "final message not empty")
    assert_eq(final.get("resolution_status"), "pending", "resolution status")


# ---------------------------------------------------------------------------
# 4. Error handling tests
# ---------------------------------------------------------------------------

def test_retry_success():
    counter = {"n": 0}

    @retry_with_backoff(max_retries=2, base_delay=0.01)
    def flaky():
        counter["n"] += 1
        if counter["n"] < 2:
            raise ValueError("not yet")
        return "ok"

    result = flaky()
    assert_eq(result, "ok", "retry result")
    assert_eq(counter["n"], 2, "retry count")


def test_retry_exhausted():
    @retry_with_backoff(max_retries=1, base_delay=0.01)
    def always_fails():
        raise ValueError("fail")

    try:
        always_fails()
        raise AssertionError("Should have raised MaxRetriesExceeded")
    except MaxRetriesExceeded:
        pass


def test_circuit_breaker():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    def fail():
        raise ValueError("fail")

    # First failure
    try:
        cb.execute(fail)
    except ValueError:
        pass
    assert_eq(cb.state, "closed", "cb closed after 1 failure")

    # Second failure -> open
    try:
        cb.execute(fail)
    except ValueError:
        pass
    assert_eq(cb.state, "open", "cb open after 2 failures")

    # Execute should fail fast
    try:
        cb.execute(lambda: "ok")
        raise AssertionError("Should have raised CircuitBreakerOpen")
    except CircuitBreakerOpen:
        pass


def test_record_error():
    state = create_initial_state(Ticket(subject="T", body="B"))
    record_error(state, "test error")
    assert_eq(state["errors"], ["test error"], "error recorded")


def test_record_agent_decision():
    state = create_initial_state(Ticket(subject="T", body="B"))
    record_agent_decision(state, "test_agent", "decided", 0.9, "because")
    assert_eq(len(state["agent_decisions"]), 1, "decision count")
    assert_eq(state["agent_decisions"][0]["agent_name"], "test_agent", "decision agent")


# ---------------------------------------------------------------------------
# 5. State manager tests
# ---------------------------------------------------------------------------

def test_ticket_store_crud():
    store = TicketStore()
    t = Ticket(subject="S", body="B")
    state = store.create(t)

    retrieved = store.get(t.ticket_id)
    assert_true(retrieved is not None, "get returns state")

    state["ticket_status"] = "updated"
    store.update(t.ticket_id, state)
    assert_eq(store.get(t.ticket_id)["ticket_status"], "updated", "updated status")

    assert_eq(store.count(), 1, "count")
    assert_true(store.delete(t.ticket_id), "delete")
    assert_eq(store.count(), 0, "count after delete")


def test_lifecycle_tracker():
    tracker = LifecycleTracker()
    tracker.record_transition("T1", "received", "classifying", "system")
    tracker.record_transition("T1", "classifying", "completed", "response_agent")
    history = tracker.get_history("T1")
    assert_eq(len(history), 2, "history count")


def test_state_manager_full_lifecycle():
    sm = StateManager()
    t = Ticket(subject="Test ticket", body="Body", customer_id="C1")
    state = sm.submit_ticket(t)
    assert_eq(state["ticket_status"], "received", "initial status")

    sm.transition_to(t.ticket_id, "classifying", "classifier")
    sm.transition_to(t.ticket_id, "completed", "response_agent")
    history = sm.tracker.get_history(t.ticket_id)
    assert_eq(len(history), 3, "lifecycle events")


def test_metrics_collector():
    mc = MetricsCollector()
    state = create_initial_state(Ticket(subject="S", body="B"))
    state["ticket_status"] = "completed"
    state["assigned_topic"] = "technical"
    state["urgency_level"] = "high"
    state["processing_time_ms"] = 150.0
    state["final_response"] = {"resolution_status": "resolved"}
    mc.record_completion(state)
    m = mc.get_metrics()
    assert_eq(m.total_processed, 1, "total processed")
    assert_eq(m.by_topic.get("technical", 0), 1, "by topic")
    assert_eq(m.avg_processing_time_ms, 150.0, "avg time")


# ---------------------------------------------------------------------------
# 6. End-to-end workflow tests
# ---------------------------------------------------------------------------

def test_workflow_technical_ticket():
    system = CustomerSupportSystem()
    result = system.process_ticket(
        subject="API endpoint returning 500 errors",
        body="Our integration is completely broken since this morning.",
        customer_id="CUST-001",
        channel="email",
    )
    assert_eq(result["ticket_status"], "completed", "ticket status")
    assert_true(result.get("final_response") is not None, "has final response")
    assert_true(len(result["final_response"].get("customer_facing_message", "")) > 0, "has message")
    assert_true(len(result.get("agent_decisions", [])) >= 2, "at least 2 agent decisions")


def test_workflow_billing_ticket():
    system = CustomerSupportSystem()
    result = system.process_ticket(
        subject="Unexpected charge on my credit card",
        body="I was charged $149.99 but my plan is $49.99.",
        customer_id="CUST-002",
        channel="chat",
    )
    assert_eq(result["ticket_status"], "completed", "ticket status")
    classification = result.get("classification", {})
    assert_eq(classification.get("topic"), "billing", "classified as billing")


def test_workflow_general_ticket():
    system = CustomerSupportSystem()
    result = system.process_ticket(
        subject="How do I export my data?",
        body="I can't find the export option in settings.",
        customer_id="CUST-003",
        channel="web_form",
    )
    assert_eq(result["ticket_status"], "completed", "ticket status")
    classification = result.get("classification", {})
    assert_eq(classification.get("topic"), "general", "classified as general")


def test_workflow_format_output():
    system = CustomerSupportSystem()
    result = system.process_ticket(
        subject="Test ticket",
        body="Test body",
        customer_id="CUST-FMT",
    )
    formatted = system.format_response(result)
    assert_true("SUPPORT TICKET RESULT" in formatted, "has header")
    assert_true("CUST-FMT" in formatted, "has customer id")


def test_workflow_metrics():
    system = CustomerSupportSystem()
    # Process two tickets
    system.process_ticket(subject="Tech issue", body="Error", customer_id="C1")
    system.process_ticket(subject="Billing help", body="Charge", customer_id="C2")
    metrics = system.get_metrics()
    assert_eq(metrics["total_processed"], 2, "two tickets processed")


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Multi-Agent Customer Support System - Test Suite")
    print("=" * 60)
    print()

    print("--- State Schema Tests ---")
    _test("ticket_creation", test_ticket_creation)
    _test("initial_state", test_initial_state)

    print("\n--- Parser Tests ---")
    _test("extract_json_fenced", test_extract_json_fenced)
    _test("extract_json_bare", test_extract_json_bare)
    _test("parse_classification_valid", test_parse_classification_valid)
    _test("parse_classification_invalid_urgency", test_parse_classification_invalid_urgency)
    _test("parse_agent_response_valid", test_parse_agent_response_valid)
    _test("parse_agent_response_wrong_agent", test_parse_agent_response_wrong_agent)
    _test("parse_final_response_valid", test_parse_final_response_valid)

    print("\n--- Agent Tests (Deterministic Fallback) ---")
    _test("classifier_agent_deterministic", test_classifier_agent_deterministic)
    _test("technical_agent_deterministic", test_technical_agent_deterministic)
    _test("billing_agent_deterministic", test_billing_agent_deterministic)
    _test("general_agent_deterministic", test_general_agent_deterministic)
    _test("response_agent_deterministic", test_response_agent_deterministic)

    print("\n--- Error Handling Tests ---")
    _test("retry_success", test_retry_success)
    _test("retry_exhausted", test_retry_exhausted)
    _test("circuit_breaker", test_circuit_breaker)
    _test("record_error", test_record_error)
    _test("record_agent_decision", test_record_agent_decision)

    print("\n--- State Manager Tests ---")
    _test("ticket_store_crud", test_ticket_store_crud)
    _test("lifecycle_tracker", test_lifecycle_tracker)
    _test("state_manager_full_lifecycle", test_state_manager_full_lifecycle)
    _test("metrics_collector", test_metrics_collector)

    print("\n--- End-to-End Workflow Tests ---")
    _test("workflow_technical_ticket", test_workflow_technical_ticket)
    _test("workflow_billing_ticket", test_workflow_billing_ticket)
    _test("workflow_general_ticket", test_workflow_general_ticket)
    _test("workflow_format_output", test_workflow_format_output)
    _test("workflow_metrics", test_workflow_metrics)

    print()
    print("=" * 60)
    total = _pass + _fail
    print(f"Results: {_pass}/{total} passed, {_fail}/{total} failed")
    print("=" * 60)

    return 0 if _fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

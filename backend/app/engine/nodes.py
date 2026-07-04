"""Node functions for the LangGraph workflow.

Each node wraps an agent call and returns only the keys it modifies.
In LangGraph, parallel nodes MUST NOT return the same keys —
returning full state causes InvalidUpdateError.
"""
import logging
from app.agents.state import InvestmentState
from app.agents.base import AGENT_REGISTRY

logger = logging.getLogger(__name__)


def _run_agent(agent_name: str, state: dict) -> dict:
    """Run an agent and return only the fields it updates."""
    agent = AGENT_REGISTRY.get(agent_name)
    if not agent:
        return {}
    inv_state = _dict_to_state(state)
    result = agent.run(inv_state)
    return {
        "agent_outputs": {agent_name: result.get("output", {})},
        "agent_confidence": {agent_name: result.get("confidence", 0.0)},
    }


def planner_node(state: dict) -> dict:
    return _run_agent("planner", state)


def finance_node(state: dict) -> dict:
    return _run_agent("finance", state)


def technical_node(state: dict) -> dict:
    return _run_agent("technical", state)


def news_node(state: dict) -> dict:
    return _run_agent("news", state)


def risk_node(state: dict) -> dict:
    return _run_agent("risk", state)


def judge_node(state: dict) -> dict:
    return _run_agent("judge", state)


def portfolio_node(state: dict) -> dict:
    return _run_agent("portfolio", state)


def report_node(state: dict) -> dict:
    agent = AGENT_REGISTRY.get("report")
    if not agent:
        return {}
    inv_state = _dict_to_state(state)
    result = agent.run(inv_state)
    return {
        "final_report": result.get("output", {}),
        "decision": result.get("output", {}).get("verdict", "hold"),
    }


def _dict_to_state(d: dict) -> InvestmentState:
    return InvestmentState(**{k: v for k, v in d.items() if k in InvestmentState.__dataclass_fields__})

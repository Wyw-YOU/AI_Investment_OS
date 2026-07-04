"""Tests for InvestmentState and BaseAgent."""
import pytest
from app.agents.state import InvestmentState
from app.agents.base import AGENT_REGISTRY, get_agent, list_agents


class TestInvestmentState:
    def test_default_state(self):
        state = InvestmentState()
        assert state.current_stock == ""
        assert state.decision == ""
        assert state.agent_outputs == {}

    def test_set_agent_output(self):
        state = InvestmentState()
        result = {
            "output": {"verdict": "buy"},
            "confidence": 0.85,
            "evidence": ["test"],
            "reasoning": "test reasoning",
        }
        state.set_agent_output("finance", result)
        assert state.get_agent_output("finance") == {"verdict": "buy"}
        assert state.get_agent_confidence("finance") == 0.85

    def test_get_missing_agent(self):
        state = InvestmentState()
        assert state.get_agent_output("nonexistent") == {}
        assert state.get_agent_confidence("nonexistent") == 0.0


class TestAgentRegistry:
    def test_agents_registered(self):
        agents = list_agents()
        assert "planner" in agents
        assert "finance" in agents
        assert "technical" in agents
        assert "news" in agents
        assert "risk" in agents
        assert "judge" in agents
        assert "portfolio" in agents
        assert "report" in agents

    def test_get_agent(self):
        agent = get_agent("finance")
        assert agent.name == "finance"

    def test_get_missing_agent(self):
        with pytest.raises(KeyError):
            get_agent("nonexistent")

import pytest
from app.agents.state import create_initial_state, WorkflowPhase
from app.agents.workflow import build_workflow, safe_agent_run
from app.agents.planner import PlannerAgent


def test_workflow_graph_structure():
    workflow = build_workflow()
    graph = workflow.compile()

    # Verify nodes exist
    nodes = set(graph.get_graph().nodes)
    expected = {"planner", "news", "financial", "technical", "macro", "merge", "risk", "quant", "report", "__start__", "__end__"}
    assert expected.issubset(nodes), f"Missing nodes: {expected - nodes}"


@pytest.mark.asyncio
async def test_safe_agent_run_error_handling():
    from app.agents.base import BaseAgent
    from app.agents.models import AgentOutput

    class FailingAgent(BaseAgent):
        name = "failing"
        description = "always fails"

        async def run(self, state):
            raise ValueError("Test error")

    agent = FailingAgent()
    result = await safe_agent_run(agent, {"stock_code": "600519"})
    assert result.agent_name == "failing"
    assert result.confidence == 0.0
    assert "error" in result.result


def test_create_initial_state():
    state = create_initial_state(stock_code="600519", stock_name="贵州茅台")
    assert state["stock_code"] == "600519"
    assert state["stock_name"] == "贵州茅台"
    assert state["phase"] == WorkflowPhase.INIT.value
    assert state["task_id"] is not None
    assert isinstance(state["parallel_results"], list)
    assert isinstance(state["agent_outputs"], dict)

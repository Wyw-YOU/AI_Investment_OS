import pytest
from app.agents.state import create_initial_state, WorkflowPhase


def test_agent_progress_initialized():
    state = create_initial_state(stock_code="600519", stock_name="贵州茅台")
    progress = state.get("agent_progress", {})
    assert progress["planner"] == "pending"
    assert progress["news"] == "pending"
    assert progress["financial"] == "pending"
    assert progress["technical"] == "pending"
    assert progress["macro"] == "pending"
    assert progress["risk"] == "pending"
    assert progress["quant"] == "pending"
    assert progress["report"] == "pending"


@pytest.mark.asyncio
async def test_planner_updates_progress():
    from app.agents.planner import PlannerAgent
    state = create_initial_state(
        stock_code="600519",
        news_data=[{"title": "test"}],
        financial_data={"metrics": {"roe": 30}},
        price_history=[{"close": 1800}] * 30,
    )
    agent = PlannerAgent()
    output = await agent.run(dict(state))
    assert output.agent_name == "planner"
    assert output.confidence == 1.0


def test_create_initial_state():
    state = create_initial_state(stock_code="600519", stock_name="贵州茅台")
    assert state["stock_code"] == "600519"
    assert state["stock_name"] == "贵州茅台"
    assert state["phase"] == WorkflowPhase.INIT.value
    assert state["task_id"] is not None
    assert isinstance(state["parallel_results"], list)
    assert isinstance(state["agent_outputs"], dict)
    assert "agent_progress" in state


@pytest.mark.asyncio
async def test_safe_agent_run_retry():
    from app.agents.base import BaseAgent
    from app.agents.models import AgentOutput
    from app.agents.workflow import safe_agent_run

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


def test_workflow_graph_structure():
    from app.agents.workflow import build_workflow
    workflow = build_workflow()
    graph = workflow.compile()
    nodes = set(graph.get_graph().nodes)
    expected = {"planner", "news", "financial", "technical", "macro", "merge", "risk", "quant", "report", "__start__", "__end__"}
    assert expected.issubset(nodes), f"Missing nodes: {expected - nodes}"

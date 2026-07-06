from app.agents.planner import PlannerAgent
from app.agents.state import create_initial_state


def test_planner_agent():
    state = create_initial_state(
        stock_code="600519",
        stock_name="贵州茅台",
        news_data=[{"title": "test news"}],
        financial_data={"metrics": {"roe": 30}},
        price_history=[{"close": 1800}] * 30,
    )
    agent = PlannerAgent()
    output = agent.run(dict(state))

    assert output.agent_name == "planner"
    assert output.confidence == 1.0
    assert "tasks" in output.result
    assert "parallel_agents" in output.result
    assert len(output.result["parallel_agents"]) == 4


def test_base_agent_prompt_building():
    from app.agents.news import NewsAgent
    agent = NewsAgent()
    state = {
        "stock_code": "600519",
        "stock_name": "贵州茅台",
        "news_data": [{"title": "利好消息", "source": "东方财富", "content": "公司业绩增长"}],
        "market_data": {"price": 1800, "change_pct": 2.5},
    }
    prompt = agent.build_prompt(state)
    assert "600519" in prompt
    assert "贵州茅台" in prompt
    assert "[ROLE]" in prompt
    assert "[TASK]" in prompt


def test_agent_output_validation():
    from app.agents.models import AgentOutput
    output = AgentOutput(
        agent_name="test",
        result={"key": "value"},
        confidence=1.5,  # Should be clamped to 1.0
    )
    assert output.confidence == 1.0

    output2 = AgentOutput(
        agent_name="test",
        result={"key": "value"},
        confidence=-0.5,  # Should be clamped to 0.0
    )
    assert output2.confidence == 0.0

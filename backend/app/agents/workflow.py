import logging
from datetime import datetime

from langgraph.graph import END, StateGraph

from app.agents.base import BaseAgent
from app.agents.models import AgentOutput
from app.agents.planner import PlannerAgent
from app.agents.news import NewsAgent
from app.agents.financial import FinancialAgent
from app.agents.technical import TechnicalAgent
from app.agents.macro import MacroAgent
from app.agents.risk import RiskAgent
from app.agents.quant import QuantAgent
from app.agents.report import ReportAgent
from app.agents.state import WorkflowPhase, WorkflowState, create_initial_state

logger = logging.getLogger(__name__)


def safe_agent_run(agent: BaseAgent, state: dict) -> AgentOutput:
    try:
        return agent.run(state)
    except Exception as e:
        logger.error(f"Agent {agent.name} failed: {e}")
        return AgentOutput(
            agent_name=agent.name,
            result={"error": str(e)},
            confidence=0.0,
        )


# Node functions
def planner_node(state: WorkflowState) -> dict:
    agent = PlannerAgent()
    output = safe_agent_run(agent, dict(state))
    return {
        "phase": WorkflowPhase.ANALYZING.value,
        "updated_at": datetime.now().isoformat(),
        "agent_outputs": {**state.get("agent_outputs", {}), "planner": output.model_dump()},
    }


def news_node(state: WorkflowState) -> dict:
    agent = NewsAgent()
    output = safe_agent_run(agent, dict(state))
    return {
        "parallel_results": [output.model_dump()],
        "updated_at": datetime.now().isoformat(),
    }


def financial_node(state: WorkflowState) -> dict:
    agent = FinancialAgent()
    output = safe_agent_run(agent, dict(state))
    return {
        "parallel_results": [output.model_dump()],
        "updated_at": datetime.now().isoformat(),
    }


def technical_node(state: WorkflowState) -> dict:
    agent = TechnicalAgent()
    output = safe_agent_run(agent, dict(state))
    return {
        "parallel_results": [output.model_dump()],
        "updated_at": datetime.now().isoformat(),
    }


def macro_node(state: WorkflowState) -> dict:
    agent = MacroAgent()
    output = safe_agent_run(agent, dict(state))
    return {
        "parallel_results": [output.model_dump()],
        "updated_at": datetime.now().isoformat(),
    }


def merge_node(state: WorkflowState) -> dict:
    agent_outputs = dict(state.get("agent_outputs", {}))
    for item in state.get("parallel_results", []):
        if isinstance(item, dict) and "agent_name" in item:
            agent_outputs[item["agent_name"]] = item
    return {
        "agent_outputs": agent_outputs,
        "phase": WorkflowPhase.RISK_ASSESSING.value,
        "updated_at": datetime.now().isoformat(),
    }


def risk_node(state: WorkflowState) -> dict:
    agent = RiskAgent()
    output = safe_agent_run(agent, dict(state))
    return {
        "risk_assessment": output.model_dump(),
        "agent_outputs": {**state.get("agent_outputs", {}), "risk": output.model_dump()},
        "phase": WorkflowPhase.SCORING.value,
        "updated_at": datetime.now().isoformat(),
    }


def quant_node(state: WorkflowState) -> dict:
    agent = QuantAgent()
    output = safe_agent_run(agent, dict(state))
    return {
        "quant_score": output.model_dump(),
        "agent_outputs": {**state.get("agent_outputs", {}), "quant": output.model_dump()},
        "phase": WorkflowPhase.REPORTING.value,
        "updated_at": datetime.now().isoformat(),
    }


def report_node(state: WorkflowState) -> dict:
    agent = ReportAgent()
    output = safe_agent_run(agent, dict(state))
    return {
        "final_report": output.model_dump(),
        "agent_outputs": {**state.get("agent_outputs", {}), "report": output.model_dump()},
        "phase": WorkflowPhase.COMPLETE.value,
        "updated_at": datetime.now().isoformat(),
    }


def build_workflow() -> StateGraph:
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("news", news_node)
    workflow.add_node("financial", financial_node)
    workflow.add_node("technical", technical_node)
    workflow.add_node("macro", macro_node)
    workflow.add_node("merge", merge_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("quant", quant_node)
    workflow.add_node("report", report_node)

    # Entry
    workflow.set_entry_point("planner")

    # Fan-out: planner -> 4 parallel agents
    workflow.add_edge("planner", "news")
    workflow.add_edge("planner", "financial")
    workflow.add_edge("planner", "technical")
    workflow.add_edge("planner", "macro")

    # Fan-in: parallel agents -> merge
    workflow.add_edge("news", "merge")
    workflow.add_edge("financial", "merge")
    workflow.add_edge("technical", "merge")
    workflow.add_edge("macro", "merge")

    # Sequential: merge -> risk -> quant -> report -> END
    workflow.add_edge("merge", "risk")
    workflow.add_edge("risk", "quant")
    workflow.add_edge("quant", "report")
    workflow.add_edge("report", END)

    return workflow


async def run_investment_analysis(
    stock_code: str,
    stock_name: str = "",
    query: str = "",
    user_id: str = "",
    market_data: dict | None = None,
    news_data: list | None = None,
    financial_data: dict | None = None,
    price_history: list | None = None,
    indicators: dict | None = None,
) -> dict:
    state = create_initial_state(
        stock_code=stock_code,
        stock_name=stock_name,
        query=query,
        user_id=user_id,
        market_data=market_data,
        news_data=news_data,
        financial_data=financial_data,
        price_history=price_history,
        indicators=indicators,
    )

    workflow = build_workflow()
    app = workflow.compile()

    try:
        result = await app.ainvoke(state)
        return {
            "task_id": result.get("task_id"),
            "stock_code": stock_code,
            "phase": result.get("phase"),
            "agent_outputs": result.get("agent_outputs", {}),
            "risk_assessment": result.get("risk_assessment", {}),
            "quant_score": result.get("quant_score", {}),
            "final_report": result.get("final_report", {}),
        }
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        return {
            "task_id": state.get("task_id"),
            "stock_code": stock_code,
            "phase": WorkflowPhase.FAILED.value,
            "error": str(e),
        }

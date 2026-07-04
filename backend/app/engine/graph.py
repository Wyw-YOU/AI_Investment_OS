"""LangGraph workflow graph definition.

Defines the multi-agent analysis pipeline:
  Planner → [Finance, Technical, News, Risk] (parallel) → Judge → Portfolio → Report
"""
import logging
import operator
from typing import TypedDict, Any, Annotated

from langgraph.graph import StateGraph, END

from app.engine.nodes import (
    planner_node,
    finance_node,
    technical_node,
    news_node,
    risk_node,
    judge_node,
    portfolio_node,
    report_node,
)

logger = logging.getLogger(__name__)


def _merge_dicts(a: dict, b: dict) -> dict:
    """Merge two dicts (used as reducer for parallel node outputs)."""
    return {**a, **b}


class GraphState(TypedDict):
    user_id: str
    stock_pool: list[str]
    current_stock: str
    market_data: dict
    financial_data: dict
    news_data: list
    indicators: dict
    # Annotated with merge reducer — parallel nodes can each update these
    agent_outputs: Annotated[dict[str, dict], _merge_dicts]
    agent_confidence: Annotated[dict[str, float], _merge_dicts]
    risk_profile: dict
    portfolio: dict
    candidate_pool: list[str]
    final_report: dict
    events: list
    decision: str


def build_analysis_graph() -> StateGraph:
    graph = StateGraph(GraphState)

    graph.add_node("planner", planner_node)
    graph.add_node("finance", finance_node)
    graph.add_node("technical", technical_node)
    graph.add_node("news", news_node)
    graph.add_node("risk", risk_node)
    graph.add_node("judge", judge_node)
    graph.add_node("portfolio", portfolio_node)
    graph.add_node("report", report_node)

    graph.set_entry_point("planner")

    graph.add_edge("planner", "finance")
    graph.add_edge("planner", "technical")
    graph.add_edge("planner", "news")
    graph.add_edge("planner", "risk")

    graph.add_edge("finance", "judge")
    graph.add_edge("technical", "judge")
    graph.add_edge("news", "judge")
    graph.add_edge("risk", "judge")

    graph.add_edge("judge", "portfolio")
    graph.add_edge("portfolio", "report")
    graph.add_edge("report", END)

    return graph


def run_analysis(
    stock_code: str,
    market_data: dict = None,
    financial_data: dict = None,
    news_data: list = None,
    indicators: dict = None,
    portfolio: dict = None,
) -> dict:
    """Run the full analysis pipeline for a stock."""
    import app.agents.planner
    import app.agents.finance
    import app.agents.technical
    import app.agents.news
    import app.agents.risk
    import app.agents.judge
    import app.agents.portfolio_agent
    import app.agents.report

    graph = build_analysis_graph()
    app_graph = graph.compile()

    initial_state: GraphState = {
        "user_id": "",
        "stock_pool": [stock_code],
        "current_stock": stock_code,
        "market_data": market_data or {},
        "financial_data": financial_data or {},
        "news_data": news_data or [],
        "indicators": indicators or {},
        "agent_outputs": {},
        "agent_confidence": {},
        "risk_profile": {},
        "portfolio": portfolio or {},
        "candidate_pool": [],
        "final_report": {},
        "events": [],
        "decision": "",
    }

    logger.info(f"Starting analysis for {stock_code}")
    result = app_graph.invoke(initial_state)
    logger.info(f"Analysis complete for {stock_code}: decision={result.get('decision')}")

    return {
        "status": "success",
        "stock": stock_code,
        "decision": result.get("decision", ""),
        "report": result.get("final_report", {}),
        "agent_outputs": result.get("agent_outputs", {}),
        "agent_confidence": result.get("agent_confidence", {}),
    }

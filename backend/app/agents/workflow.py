"""
LangGraph 投资分析工作流。

流程拓扑：
  planner → [news, financial, technical, macro]（并行）→ merge → risk → quant → report

progress_callback 参数用于将每个 agent 的状态变化（started/completed/failed）
实时推送给前端 WebSocket 客户端，实现进度条动画。
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable

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


async def safe_agent_run(agent: BaseAgent, state: dict, max_retries: int = 2) -> AgentOutput:
    for attempt in range(max_retries):
        try:
            return await agent.run(state)
        except Exception as e:
            logger.error(f"Agent {agent.name} attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                return AgentOutput(
                    agent_name=agent.name,
                    result={"error": str(e)},
                    confidence=0.0,
                )


def make_progress_updater(agent_name: str) -> Callable:
    def update(state: WorkflowState) -> dict:
        progress = dict(state.get("agent_progress", {}))
        progress[agent_name] = "completed"
        return progress
    return update


def _make_node_wrapper(agent_name: str, node_fn: Callable, progress_callback: Callable | None):
    async def wrapped(state: WorkflowState) -> dict:
        if progress_callback:
            await progress_callback(agent_name, "started")
        result = await node_fn(state)
        # Check if agent result contains error
        agent_output = result.get("agent_outputs", {}).get(agent_name, {})
        has_error = "error" in agent_output.get("result", {})
        if progress_callback:
            status = "failed" if has_error else "completed"
            detail = {"error": agent_output["result"]["error"]} if has_error else None
            await progress_callback(agent_name, status, detail)
        return result
    return wrapped
async def planner_node(state: WorkflowState) -> dict:
    agent = PlannerAgent()
    output = await safe_agent_run(agent, dict(state))
    progress = dict(state.get("agent_progress", {}))
    progress["planner"] = "completed"
    return {
        "phase": WorkflowPhase.ANALYZING.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "agent_outputs": {**state.get("agent_outputs", {}), "planner": output.model_dump()},
        "agent_progress": progress,
    }


async def news_node(state: WorkflowState) -> dict:
    agent = NewsAgent()
    output = await safe_agent_run(agent, dict(state))
    progress = dict(state.get("agent_progress", {}))
    progress["news"] = "completed"
    return {
        "parallel_results": [output.model_dump()],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "agent_progress": progress,
    }


async def financial_node(state: WorkflowState) -> dict:
    agent = FinancialAgent()
    output = await safe_agent_run(agent, dict(state))
    progress = dict(state.get("agent_progress", {}))
    progress["financial"] = "completed"
    return {
        "parallel_results": [output.model_dump()],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "agent_progress": progress,
    }


async def technical_node(state: WorkflowState) -> dict:
    agent = TechnicalAgent()
    output = await safe_agent_run(agent, dict(state))
    progress = dict(state.get("agent_progress", {}))
    progress["technical"] = "completed"
    return {
        "parallel_results": [output.model_dump()],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "agent_progress": progress,
    }


async def macro_node(state: WorkflowState) -> dict:
    agent = MacroAgent()
    output = await safe_agent_run(agent, dict(state))
    progress = dict(state.get("agent_progress", {}))
    progress["macro"] = "completed"
    return {
        "parallel_results": [output.model_dump()],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "agent_progress": progress,
    }


async def merge_node(state: WorkflowState) -> dict:
    agent_outputs = dict(state.get("agent_outputs", {}))
    for item in state.get("parallel_results", []):
        if isinstance(item, dict) and "agent_name" in item:
            agent_outputs[item["agent_name"]] = item
    return {
        "agent_outputs": agent_outputs,
        "phase": WorkflowPhase.RISK_ASSESSING.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


async def risk_node(state: WorkflowState) -> dict:
    agent = RiskAgent()
    output = await safe_agent_run(agent, dict(state))
    progress = dict(state.get("agent_progress", {}))
    progress["risk"] = "completed"
    return {
        "risk_assessment": output.model_dump(),
        "agent_outputs": {**state.get("agent_outputs", {}), "risk": output.model_dump()},
        "phase": WorkflowPhase.SCORING.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "agent_progress": progress,
    }


async def quant_node(state: WorkflowState) -> dict:
    agent = QuantAgent()
    output = await safe_agent_run(agent, dict(state))
    progress = dict(state.get("agent_progress", {}))
    progress["quant"] = "completed"
    return {
        "quant_score": output.model_dump(),
        "agent_outputs": {**state.get("agent_outputs", {}), "quant": output.model_dump()},
        "phase": WorkflowPhase.REPORTING.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "agent_progress": progress,
    }


async def report_node(state: WorkflowState) -> dict:
    agent = ReportAgent()
    output = await safe_agent_run(agent, dict(state))
    progress = dict(state.get("agent_progress", {}))
    progress["report"] = "completed"
    return {
        "final_report": output.model_dump(),
        "agent_outputs": {**state.get("agent_outputs", {}), "report": output.model_dump()},
        "phase": WorkflowPhase.COMPLETE.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "agent_progress": progress,
    }


def build_workflow(progress_callback: Callable | None = None) -> StateGraph:
    workflow = StateGraph(WorkflowState)

    nodes = {
        "planner": planner_node,
        "news": news_node,
        "financial": financial_node,
        "technical": technical_node,
        "macro": macro_node,
        "merge": merge_node,
        "risk": risk_node,
        "quant": quant_node,
        "report": report_node,
    }

    for name, fn in nodes.items():
        workflow.add_node(name, _make_node_wrapper(name, fn, progress_callback))

    workflow.set_entry_point("planner")

    workflow.add_edge("planner", "news")
    workflow.add_edge("planner", "financial")
    workflow.add_edge("planner", "technical")
    workflow.add_edge("planner", "macro")

    workflow.add_edge("news", "merge")
    workflow.add_edge("financial", "merge")
    workflow.add_edge("technical", "merge")
    workflow.add_edge("macro", "merge")

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
    progress_callback: Callable | None = None,
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

    workflow = build_workflow(progress_callback)
    app = workflow.compile()

    try:
        result = await app.ainvoke(state)
        return {
            "task_id": result.get("task_id"),
            "stock_code": stock_code,
            "phase": result.get("phase"),
            "agent_outputs": result.get("agent_outputs", {}),
            "agent_progress": result.get("agent_progress", {}),
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

"""
Investment Analysis System - LangGraph Workflow Orchestrator

Implements the full investment analysis pipeline using LangGraph:

    User Query
        |
        v
    [Planner] (validate inputs, enrich state)
        |
        v
    [Parallel Fan-Out]
    +--- News Agent ---+
    |                  |
    +--- Financial Agent ---+---> Risk Agent ---> Report Agent ---> END
    |                  |
    +--- Technical Agent ---+

Features:
- Parallel execution of independent analysis agents (fan-out/fan-in)
- Sequential risk assessment and report synthesis
- Robust error handling with fallback outputs
- State management with immutable transitions
- Progress tracking via state phase transitions
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from models import (
    AgentOutput,
    WorkflowPhase,
    create_initial_state,
)
from news_agent import NewsAgent
from financial_agent import FinancialAgent
from technical_agent import TechnicalAgent
from risk_agent import RiskAgent
from report_agent import ReportAgent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Workflow State (TypedDict for LangGraph with parallel-safe reducers)
# ---------------------------------------------------------------------------

# NOTE: LangGraph requires a TypedDict (not Pydantic) for the state schema.
# We define it here to enable ``Annotated[list, operator.add]`` for safe
# parallel result aggregation.

from typing import TypedDict, Annotated
import operator


class WorkflowState(TypedDict, total=False):
    """
    State schema for the investment analysis LangGraph workflow.

    Fields with ``Annotated[list, operator.add]`` are safe for parallel
    agents -- each parallel branch appends to the list, and LangGraph
    merges them after fan-in.
    """

    # --- Identifiers ---
    task_id: str
    stock_code: str
    stock_name: str
    user_id: str

    # --- Workflow tracking ---
    phase: str
    version: int
    started_at: str
    updated_at: str

    # --- Input data ---
    query: str
    market_data: Dict[str, Any]
    news_data: List[Dict[str, Any]]
    financial_data: Dict[str, Any]
    price_history: List[Dict[str, Any]]

    # --- Agent outputs (keyed by agent name) ---
    agent_outputs: Dict[str, Any]

    # --- Parallel results (collected via operator.add) ---
    parallel_results: Annotated[List[Dict[str, Any]], operator.add]

    # --- Synthesis results ---
    risk_assessment: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]

    # --- Error tracking ---
    errors: Annotated[List[str], operator.add]

    # --- User preferences ---
    time_horizon: str
    risk_tolerance: str


# ---------------------------------------------------------------------------
# Safe Agent Execution Wrapper
# ---------------------------------------------------------------------------

def safe_agent_run(agent, state: dict) -> dict:
    """
    Execute an agent with comprehensive error handling.

    Returns a state update dict (never raises). On failure, returns an
    error output so the workflow can continue.
    """
    agent_name = agent.name
    try:
        logger.info("Starting agent: %s", agent_name)
        start_time = time.time()

        output: AgentOutput = agent.run(state)

        elapsed = time.time() - start_time
        logger.info(
            "Agent %s completed in %.2fs (confidence=%.2f, status=%s)",
            agent_name,
            elapsed,
            output.confidence,
            output.status,
        )

        # Build the state update: store the output in agent_outputs
        output_dict = output.model_dump()
        output_dict["elapsed_seconds"] = elapsed

        # Return the partial state update
        return {
            "agent_outputs": {agent_name: output_dict},
        }

    except Exception as exc:
        logger.error("Agent %s failed: %s", agent_name, exc, exc_info=True)
        error_output = AgentOutput(
            agent_name=agent_name,
            result={"error": str(exc)},
            confidence=0.0,
            citations=[],
            metadata={"error_type": type(exc).__name__},
            status="failed",
            error=str(exc),
        ).model_dump()

        return {
            "agent_outputs": {agent_name: error_output},
            "errors": [f"{agent_name}: {exc}"],
        }


# ---------------------------------------------------------------------------
# Node functions for the LangGraph workflow
# ---------------------------------------------------------------------------

def planner_node(state: dict) -> dict:
    """
    Validate inputs, enrich state, and transition to ANALYZING phase.

    This is the entry node. It ensures the state is properly initialized
    and all required data fields are present.
    """
    logger.info(
        "Planner: Starting analysis for %s (task_id=%s)",
        state.get("stock_code"),
        state.get("task_id"),
    )

    updates: Dict[str, Any] = {
        "phase": WorkflowPhase.ANALYZING.value,
        "updated_at": datetime.now().isoformat(),
    }

    # Validate that stock_code is present
    stock_code = state.get("stock_code", "")
    if not stock_code:
        updates["errors"] = ["Planner: Missing stock_code in input state"]
        updates["phase"] = WorkflowPhase.FAILED.value

    # Initialize empty structures if not present
    if "agent_outputs" not in state or state["agent_outputs"] is None:
        updates["agent_outputs"] = {}
    if "parallel_results" not in state:
        updates["parallel_results"] = []
    if "errors" not in state:
        updates["errors"] = []

    return updates


def news_node(state: dict) -> dict:
    """Execute News Agent in the parallel fan-out."""
    return safe_agent_run(NewsAgent(), state)


def financial_node(state: dict) -> dict:
    """Execute Financial Agent in the parallel fan-out."""
    return safe_agent_run(FinancialAgent(), state)


def technical_node(state: dict) -> dict:
    """Execute Technical Agent in the parallel fan-out."""
    return safe_agent_run(TechnicalAgent(), state)


def risk_node(state: dict) -> dict:
    """
    Execute Risk Agent after all parallel agents have completed.

    This node receives the merged state with all parallel agent outputs
    in ``agent_outputs``.
    """
    # Transition phase
    logger.info("Risk Agent: Starting risk assessment for %s", state.get("stock_code"))

    result = safe_agent_run(RiskAgent(), state)
    result["phase"] = WorkflowPhase.SYNTHESIZING.value
    result["updated_at"] = datetime.now().isoformat()

    # Store risk assessment at the top level for easy access by Report Agent
    if "agent_outputs" in result:
        risk_output = result["agent_outputs"].get("risk_agent", {})
        if risk_output:
            result["risk_assessment"] = risk_output

    return result


def report_node(state: dict) -> dict:
    """
    Execute Report Agent to synthesize all outputs into the final report.

    Runs after the Risk Agent.
    """
    logger.info("Report Agent: Generating final report for %s", state.get("stock_code"))

    # Ensure risk_assessment is in the state for the Report Agent
    enhanced_state = {**state}
    if state.get("risk_assessment") is None:
        # Try to extract from agent_outputs
        agent_outputs = state.get("agent_outputs", {})
        if "risk_agent" in agent_outputs:
            enhanced_state["risk_assessment"] = agent_outputs["risk_agent"]

    result = safe_agent_run(ReportAgent(), enhanced_state)
    result["phase"] = WorkflowPhase.COMPLETE.value
    result["updated_at"] = datetime.now().isoformat()

    # Extract final report to top level
    if "agent_outputs" in result:
        report_output = result["agent_outputs"].get("report_agent", {})
        if report_output:
            result["final_report"] = report_output.get("result", {})

    return result


# ---------------------------------------------------------------------------
# Merge function for parallel results
# ---------------------------------------------------------------------------

def merge_parallel_outputs(state: dict) -> dict:
    """
    After the parallel fan-in, merge individual agent outputs from
    the parallel_results list into the agent_outputs dict.

    This is handled automatically by LangGraph's reducer pattern for
    ``Annotated[list, operator.add]``, but we also need to ensure
    the agent_outputs dict is properly populated.
    """
    logger.info("Merging parallel outputs...")

    agent_outputs = dict(state.get("agent_outputs", {}))

    # The parallel agents update agent_outputs directly, so this node
    # mainly serves as a synchronization point and logging checkpoint.
    completed = [name for name in agent_outputs if name != "risk_agent"]
    logger.info("Parallel agents completed: %s", completed)

    return {
        "phase": WorkflowPhase.RISK_ASSESSING.value,
        "updated_at": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Workflow builder
# ---------------------------------------------------------------------------

def build_investment_workflow() -> StateGraph:
    """
    Build and return the LangGraph StateGraph for the investment
    analysis pipeline.

    Workflow topology::

        planner
           |
           v
        [fan-out]
        +--- news --------+
        |                 |
        +--- financial ---+---> merge ---> risk ---> report ---> END
        |                 |
        +--- technical ---+

    Returns
    -------
    StateGraph
        The compiled workflow graph, ready to ``.invoke()``.
    """

    workflow = StateGraph(WorkflowState)

    # --- Add nodes ---
    workflow.add_node("planner", planner_node)
    workflow.add_node("news", news_node)
    workflow.add_node("financial", financial_node)
    workflow.add_node("technical", technical_node)
    workflow.add_node("merge", merge_parallel_outputs)
    workflow.add_node("risk", risk_node)
    workflow.add_node("report", report_node)

    # --- Entry point ---
    workflow.set_entry_point("planner")

    # --- Fan-out edges: planner -> all parallel agents ---
    workflow.add_edge("planner", "news")
    workflow.add_edge("planner", "financial")
    workflow.add_edge("planner", "technical")

    # --- Fan-in edges: all parallel agents -> merge ---
    workflow.add_edge("news", "merge")
    workflow.add_edge("financial", "merge")
    workflow.add_edge("technical", "merge")

    # --- Sequential edges: merge -> risk -> report -> END ---
    workflow.add_edge("merge", "risk")
    workflow.add_edge("risk", "report")
    workflow.add_edge("report", END)

    # --- Compile ---
    compiled = workflow.compile()
    logger.info("Investment analysis workflow compiled successfully.")

    return compiled


# ---------------------------------------------------------------------------
# High-level execution function
# ---------------------------------------------------------------------------

def run_investment_analysis(
    stock_code: str,
    stock_name: str = "",
    query: str = "",
    user_id: str = "",
    market_data: Optional[Dict] = None,
    news_data: Optional[List] = None,
    financial_data: Optional[Dict] = None,
    price_history: Optional[List] = None,
    time_horizon: str = "12 months",
    risk_tolerance: str = "moderate",
    task_id: Optional[str] = None,
) -> dict:
    """
    Run the full investment analysis pipeline.

    Parameters
    ----------
    stock_code : str
        Ticker symbol (e.g., "AAPL").
    stock_name : str
        Full company name.
    query : str
        User's analysis query.
    user_id : str
        Identifier for the requesting user.
    market_data : dict, optional
        Current market snapshot (price, volume, etc.).
    news_data : list, optional
        List of news article dicts.
    financial_data : dict, optional
        Financial statement data.
    price_history : list, optional
        OHLCV price history.
    time_horizon : str
        Investment time horizon (e.g., "12 months").
    risk_tolerance : str
        User risk tolerance: conservative / moderate / aggressive.
    task_id : str, optional
        Unique task identifier (auto-generated if not provided).

    Returns
    -------
    dict
        The final workflow state with ``final_report``, ``agent_outputs``,
        ``risk_assessment``, and metadata.
    """
    import uuid

    if task_id is None:
        task_id = f"analysis_{stock_code}_{uuid.uuid4().hex[:8]}"

    # Create initial state
    initial_state = create_initial_state(
        task_id=task_id,
        stock_code=stock_code,
        stock_name=stock_name,
        query=query,
        user_id=user_id,
        market_data=market_data,
        news_data=news_data,
        financial_data=financial_data,
        price_history=price_history,
        time_horizon=time_horizon,
        risk_tolerance=risk_tolerance,
    )

    # Build and run workflow
    logger.info("=" * 60)
    logger.info("INVESTMENT ANALYSIS: %s (%s)", stock_name or stock_code, stock_code)
    logger.info("Task ID: %s", task_id)
    logger.info("=" * 60)

    workflow = build_investment_workflow()

    start_time = time.time()
    try:
        result = workflow.invoke(initial_state)
    except Exception as exc:
        logger.error("Workflow execution failed: %s", exc, exc_info=True)
        result = {
            **initial_state,
            "phase": WorkflowPhase.FAILED.value,
            "errors": [f"Workflow execution failed: {exc}"],
            "final_report": None,
        }

    elapsed = time.time() - start_time
    logger.info("Analysis complete in %.2fs. Phase: %s", elapsed, result.get("phase"))

    return result

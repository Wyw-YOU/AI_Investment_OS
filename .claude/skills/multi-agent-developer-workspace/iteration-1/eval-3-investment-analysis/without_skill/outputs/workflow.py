"""
LangGraph workflow for the Multi-Agent Investment Analysis System.

This module defines the complete execution graph:
  1. Four specialist agents run in PARALLEL (News, Financial, Technical, Risk).
  2. A merge node collects their outputs.
  3. The Report Agent synthesises a final recommendation.

The graph is compiled into an executable ``CompiledGraph`` that can be invoked
with an ``InvestmentState`` dict.

Graph topology
--------------
         +---------------------+
         |      START          |
         +---------------------+
                 |
     +-----------+-----------+-----------+
     |           |           |           |
  [news]    [financial]  [technical]  [risk]
     |           |           |           |
     +-----------+-----------+-----------+
                 |
         +---------------------+
         |      merge          |
         +---------------------+
                 |
         +---------------------+
         |      report         |
         +---------------------+
                 |
         +---------------------+
         |       END           |
         +---------------------+
"""

from __future__ import annotations

import json
import traceback
from datetime import datetime
from typing import Any, Callable

from langgraph.graph import END, StateGraph

from agents import (
    FinancialAgent,
    NewsAgent,
    ReportAgent,
    RiskAgent,
    TechnicalAgent,
)
from config import AppConfig, AgentWeightConfig
from state import InvestmentState, create_initial_state
from utils import format_timestamp, logger, serialize_agent_output


# ---------------------------------------------------------------------------
# Node functions — each wraps an agent and writes to state
# ---------------------------------------------------------------------------

def _make_agent_node(
    agent_class: type,
    state_output_key: str,
    config: AppConfig,
) -> Callable[[InvestmentState], dict[str, Any]]:
    """
    Factory that creates a LangGraph-compatible node function for an agent.

    Parameters
    ----------
    agent_class : type
        The agent class to instantiate.
    state_output_key : str
        The InvestmentState key where the agent's output will be stored.
    config : AppConfig
        Shared application configuration.

    Returns
    -------
    Callable[[InvestmentState], dict]
        A function compatible with ``graph.add_node()``.
    """

    def node_fn(state: InvestmentState) -> dict[str, Any]:
        ticker: str = state["ticker"]
        agent = agent_class(config=config)
        agent_key = agent.agent_name

        # Update agent status to "running"
        statuses = dict(state.get("agent_statuses", {}))
        statuses[agent_key] = {
            "state": "running",
            "started_at": format_timestamp(),
            "completed_at": None,
            "error": None,
            "retry_count": 0,
        }

        try:
            result = agent.run(ticker=ticker)

            # Mark as completed
            statuses[agent_key] = {
                "state": "completed",
                "started_at": statuses[agent_key].get("started_at"),
                "completed_at": format_timestamp(),
                "error": None,
                "retry_count": 0,
            }

            completed = list(state.get("completed_agents", []))
            completed.append(agent_key)

            logger.info("[%s] Node completed for %s", agent_key, ticker)

            return {
                state_output_key: result,
                "agent_statuses": statuses,
                "completed_agents": completed,
            }

        except Exception as exc:
            error_msg = f"{agent_key} failed: {exc}"
            logger.error("[%s] Node failed for %s: %s", agent_key, ticker, exc)

            statuses[agent_key] = {
                "state": "failed",
                "started_at": statuses[agent_key].get("started_at"),
                "completed_at": format_timestamp(),
                "error": error_msg,
                "retry_count": 0,
            }

            failed = list(state.get("failed_agents", []))
            failed.append(agent_key)
            errors = list(state.get("errors", []))
            errors.append(error_msg)

            return {
                state_output_key: None,
                "agent_statuses": statuses,
                "failed_agents": failed,
                "errors": errors,
            }

    return node_fn


def _merge_node(state: InvestmentState) -> dict[str, Any]:
    """
    Merge node: collects outputs from all parallel agents and validates
    that the minimum required outputs are present before proceeding to
    the report agent.
    """
    completed = state.get("completed_agents", [])
    failed = state.get("failed_agents", [])
    total_agents = 4

    logger.info(
        "[merge] %d/%d agents completed, %d failed",
        len(completed),
        total_agents,
        len(failed),
    )

    # Determine how many agents produced output
    has_output = sum(
        1
        for key in ("news_output", "financial_output", "technical_output", "risk_output")
        if state.get(key) is not None
    )

    if has_output == 0:
        # All agents failed — skip report and go to END
        logger.warning("[merge] All agents failed; skipping report generation.")
        return {
            "overall_status": "failed",
            "errors": state.get("errors", [])
            + ["All specialist agents failed; cannot generate report."],
            "completed_at": format_timestamp(),
        }

    warnings = list(state.get("warnings", []))
    if has_output < total_agents:
        warnings.append(
            f"Only {has_output}/{total_agents} agents produced output. "
            "Report quality may be reduced."
        )

    return {
        "overall_status": "running",
        "merge_results": {
            "available_agents": completed,
            "failed_agents": failed,
            "output_count": has_output,
        },
        "warnings": warnings,
    }


def _report_node(state: InvestmentState) -> dict[str, Any]:
    """
    Report node: invokes the ReportAgent with all available agent outputs.
    """
    # If all agents failed, skip report
    if state.get("overall_status") == "failed":
        return {
            "report_output": None,
            "overall_status": "failed",
            "completed_at": format_timestamp(),
        }

    ticker: str = state["ticker"]
    config = AppConfig()
    agent = ReportAgent(config=config)

    try:
        result = agent.run(
            ticker=ticker,
            news_output=state.get("news_output"),
            financial_output=state.get("financial_output"),
            technical_output=state.get("technical_output"),
            risk_output=state.get("risk_output"),
        )

        logger.info("[report] Report generation complete for %s", ticker)
        return {
            "report_output": result,
            "overall_status": "completed",
            "completed_at": format_timestamp(),
        }

    except Exception as exc:
        error_msg = f"Report generation failed: {exc}"
        logger.error("[report] %s", error_msg)
        return {
            "report_output": None,
            "overall_status": "failed",
            "errors": state.get("errors", []) + [error_msg],
            "completed_at": format_timestamp(),
        }


def _should_generate_report(state: InvestmentState) -> str:
    """
    Conditional edge: decide whether to proceed to report generation or
    skip directly to END if the workflow failed.
    """
    has_any_output = any(
        state.get(key) is not None
        for key in ("news_output", "financial_output", "technical_output", "risk_output")
    )
    if has_any_output:
        return "report"
    return "end"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_analysis_graph(config: AppConfig | None = None) -> StateGraph:
    """
    Build and return the compiled LangGraph investment analysis workflow.

    The graph is structured as:
        START -> [news, financial, technical, risk] (parallel)
              -> merge
              -> conditional: report | end
              -> END

    Parameters
    ----------
    config : AppConfig, optional
        Application configuration.  Defaults to ``AppConfig.from_env()``.

    Returns
    -------
    StateGraph
        The compiled graph ready to be invoked with an InvestmentState.
    """
    cfg = config or AppConfig.from_env()

    # Create the StateGraph
    graph = StateGraph(InvestmentState)

    # ---- Add agent nodes (parallel execution) ----
    graph.add_node(
        "news_agent",
        _make_agent_node(NewsAgent, "news_output", cfg),
    )
    graph.add_node(
        "financial_agent",
        _make_agent_node(FinancialAgent, "financial_output", cfg),
    )
    graph.add_node(
        "technical_agent",
        _make_agent_node(TechnicalAgent, "technical_output", cfg),
    )
    graph.add_node(
        "risk_agent",
        _make_agent_node(RiskAgent, "risk_output", cfg),
    )

    # ---- Add merge and report nodes ----
    graph.add_node("merge", _merge_node)
    graph.add_node("report", _report_node)

    # ---- Wire edges ----
    # All four agents start from START (implicit via set_entry_point for
    # LangGraph, but we wire them manually to enable parallel execution)
    from langgraph.graph import START

    # Edges from START to each agent — LangGraph executes these in parallel
    # when they share no data dependencies.
    graph.add_edge(START, "news_agent")
    graph.add_edge(START, "financial_agent")
    graph.add_edge(START, "technical_agent")
    graph.add_edge(START, "risk_agent")

    # All agents feed into the merge node
    graph.add_edge("news_agent", "merge")
    graph.add_edge("financial_agent", "merge")
    graph.add_edge("technical_agent", "merge")
    graph.add_edge("risk_agent", "merge")

    # Conditional edge from merge: go to report if any agent succeeded
    graph.add_conditional_edges(
        "merge",
        _should_generate_report,
        {
            "report": "report",
            "end": END,
        },
    )

    # Report feeds into END
    graph.add_edge("report", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# High-level API
# ---------------------------------------------------------------------------

def run_analysis(
    ticker: str,
    analysis_request: dict[str, Any] | None = None,
    config: AppConfig | None = None,
) -> InvestmentState:
    """
    Run the full multi-agent investment analysis for a given ticker.

    This is the top-level entry point that:
    1. Creates an initial state.
    2. Builds the compiled graph.
    3. Invokes the graph with the state.
    4. Returns the final state with all agent outputs and the report.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol (e.g. "AAPL", "TSLA").
    analysis_request : dict, optional
        Additional request parameters (time horizon, risk tolerance, etc.).
    config : AppConfig, optional
        Application configuration.

    Returns
    -------
    InvestmentState
        The final state after all agents have run and the report is generated.
    """
    cfg = config or AppConfig.from_env()
    initial_state = create_initial_state(ticker, analysis_request)

    logger.info("=" * 60)
    logger.info("Starting investment analysis for %s", ticker)
    logger.info("=" * 60)

    try:
        graph = build_analysis_graph(cfg)
        final_state = graph.invoke(initial_state)

        status = final_state.get("overall_status", "unknown")
        logger.info("Analysis complete for %s. Status: %s", ticker, status)
        return final_state

    except Exception as exc:
        logger.error("Workflow failed for %s: %s\n%s", ticker, exc, traceback.format_exc())
        initial_state["overall_status"] = "failed"
        initial_state["errors"].append(f"Workflow error: {exc}")
        initial_state["completed_at"] = format_timestamp()
        return initial_state

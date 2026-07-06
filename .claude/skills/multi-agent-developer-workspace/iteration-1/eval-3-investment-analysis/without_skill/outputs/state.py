"""
State management for the Multi-Agent Investment Analysis workflow.

InvestmentState is the shared TypedDict that every node in the LangGraph
workflow reads from and writes to.  It tracks the ticker under analysis,
per-agent outputs, progress flags, errors, and the final report.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, TypedDict

from schemas import (
    BaseAgentOutput,
    FinancialAgentOutput,
    InvestmentReport,
    NewsAgentOutput,
    Recommendation,
    RiskAgentOutput,
    TechnicalAgentOutput,
)


class AgentStatus(TypedDict, total=False):
    """Status of a single agent execution."""

    state: str  # "pending" | "running" | "completed" | "failed" | "skipped"
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]
    retry_count: int


class InvestmentState(TypedDict, total=False):
    """
    Central state object for the LangGraph investment analysis workflow.

    LangGraph nodes read fields from this dict and write their outputs back.
    Because TypedDict with ``total=False`` is used, every field is optional at
    the type level; the workflow graph enforces required fields via its edges.

    Fields
    ------
    ticker : str
        Stock ticker symbol under analysis (e.g. "AAPL").
    analysis_request : dict
        Raw user request parameters (time horizon, risk tolerance, etc.).

    -- Agent outputs (populated by agent nodes) --
    news_output : NewsAgentOutput
    financial_output : FinancialAgentOutput
    technical_output : TechnicalAgentOutput
    risk_output : RiskAgentOutput
    report_output : InvestmentReport

    -- Progress tracking --
    agent_statuses : dict[str, AgentStatus]
        Per-agent execution status keyed by agent name.
    completed_agents : list[str]
        Names of agents that have finished successfully.
    failed_agents : list[str]
        Names of agents that failed after all retries.

    -- Errors and metadata --
    errors : list[str]
        Top-level error messages.
    warnings : list[str]
        Non-fatal warnings.
    started_at : str
        ISO 8601 timestamp when the analysis started.
    completed_at : str
        ISO 8601 timestamp when the analysis finished.
    overall_status : str
        One of "initialized", "running", "completed", "failed".

    -- Merge tracking --
    merge_results : dict[str, Any]
        Intermediate merge outputs if needed.
    """

    # --- Input ---
    ticker: str
    analysis_request: dict[str, Any]

    # --- Agent outputs ---
    news_output: Optional[dict[str, Any]]
    financial_output: Optional[dict[str, Any]]
    technical_output: Optional[dict[str, Any]]
    risk_output: Optional[dict[str, Any]]
    report_output: Optional[dict[str, Any]]

    # --- Progress ---
    agent_statuses: dict[str, AgentStatus]
    completed_agents: list[str]
    failed_agents: list[str]

    # --- Metadata ---
    errors: list[str]
    warnings: list[str]
    started_at: str
    completed_at: str
    overall_status: str

    # --- Merge ---
    merge_results: dict[str, Any]


def create_initial_state(
    ticker: str,
    analysis_request: dict[str, Any] | None = None,
) -> InvestmentState:
    """
    Factory function that returns a fresh InvestmentState ready for the graph.

    Parameters
    ----------
    ticker : str
        The stock ticker to analyse.
    analysis_request : dict, optional
        Additional request parameters (time horizon, risk tolerance, etc.).

    Returns
    -------
    InvestmentState
        A fully initialised state dict with all agents set to "pending".
    """
    agent_names = [
        "news_agent",
        "financial_agent",
        "technical_agent",
        "risk_agent",
    ]
    pending_status: AgentStatus = {
        "state": "pending",
        "started_at": None,
        "completed_at": None,
        "error": None,
        "retry_count": 0,
    }

    return InvestmentState(
        ticker=ticker.upper(),
        analysis_request=analysis_request or {},
        news_output=None,
        financial_output=None,
        technical_output=None,
        risk_output=None,
        report_output=None,
        agent_statuses={name: dict(pending_status) for name in agent_names},
        completed_agents=[],
        failed_agents=[],
        errors=[],
        warnings=[],
        started_at=datetime.utcnow().isoformat(),
        completed_at="",
        overall_status="initialized",
        merge_results={},
    )

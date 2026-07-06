"""
agents package — Specialist investment analysis agents.

Each agent is a self-contained module that inherits from BaseAgent and
produces a validated Pydantic output.  The workflow module orchestrates
their execution via LangGraph.
"""

from agents.base import BaseAgent
from agents.financial_agent import FinancialAgent
from agents.news_agent import NewsAgent
from agents.report_agent import ReportAgent
from agents.risk_agent import RiskAgent
from agents.technical_agent import TechnicalAgent

__all__ = [
    "BaseAgent",
    "NewsAgent",
    "FinancialAgent",
    "TechnicalAgent",
    "RiskAgent",
    "ReportAgent",
]

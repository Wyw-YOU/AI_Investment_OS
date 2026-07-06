"""
Financial (Fundamental) Analysis Agent.

Evaluates a company's financial health, valuation, quality, and growth
prospects using fundamental data: income statement, balance sheet, cash flow,
and key financial ratios.
"""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel

from agents.base import BaseAgent
from prompts import build_financial_prompt
from schemas import FinancialAgentOutput


class FinancialAgent(BaseAgent):
    """
    Specialised agent for fundamental financial analysis.

    Responsibilities
    ----------------
    1. Compute and contextualise key valuation multiples (P/E, P/S, P/B, EV/EBITDA).
    2. Assess profitability (ROE, ROIC, margins) and compare against sector peers.
    3. Evaluate balance sheet strength (debt-to-equity, interest coverage).
    4. Analyse cash flow quality and free cash flow yield.
    5. Estimate intrinsic fair value using DCF or comparable analysis.
    6. Produce composite scores for valuation, quality, and growth.
    """

    @property
    def agent_name(self) -> str:
        return "financial_agent"

    @property
    def output_schema(self) -> Type[BaseModel]:
        return FinancialAgentOutput  # type: ignore[return-value]

    def build_prompt(self, ticker: str, **kwargs: Any) -> str:
        """
        Build the financial analysis prompt.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.
        **kwargs
            Optional keys:
            - ``date``: analysis date override (str, ISO 8601)
            - ``extra_context``: additional instructions or data (str)
            - ``financial_data``: pre-fetched financial statements (str)
            - ``sector``: sector/industry for peer comparison (str)
        """
        extra_context_parts: list[str] = []

        if financial_data := kwargs.get("financial_data"):
            extra_context_parts.append(
                f"PRE-FETCHED FINANCIAL DATA:\n{financial_data}"
            )

        if sector := kwargs.get("sector"):
            extra_context_parts.append(
                f"SECTOR/INDUSTRY for peer comparison: {sector}"
            )

        if extra := kwargs.get("extra_context"):
            extra_context_parts.append(extra)

        analysis_focus = kwargs.get("analysis_focus", "comprehensive")
        extra_context_parts.append(
            f"Analysis focus: {analysis_focus}. "
            "Prioritise accuracy over breadth; use null when data is insufficient."
        )

        return build_financial_prompt(
            ticker=ticker,
            date=kwargs.get("date"),
            extra_context="\n\n".join(extra_context_parts) if extra_context_parts else "",
        )

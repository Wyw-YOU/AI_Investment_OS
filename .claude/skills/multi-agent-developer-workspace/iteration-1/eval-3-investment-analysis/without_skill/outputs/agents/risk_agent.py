"""
Risk Assessment Agent.

Evaluates market, sector, company-specific, geopolitical, liquidity, and
regulatory risks to produce a structured risk report with position sizing
advice and stop-loss recommendations.
"""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel

from agents.base import BaseAgent
from prompts import build_risk_prompt
from schemas import RiskAgentOutput


class RiskAgent(BaseAgent):
    """
    Specialised agent for risk assessment.

    Responsibilities
    ----------------
    1. Identify and categorise risk factors (market, sector, company,
       geopolitical, liquidity, regulatory).
    2. Assess severity and probability for each risk factor.
    3. Compute a composite risk score (0-100).
    4. Estimate volatility, maximum drawdown, beta, and Sharpe ratio.
    5. Provide position sizing advice and a stop-loss recommendation.
    """

    @property
    def agent_name(self) -> str:
        return "risk_agent"

    @property
    def output_schema(self) -> Type[BaseModel]:
        return RiskAgentOutput  # type: ignore[return-value]

    def build_prompt(self, ticker: str, **kwargs: Any) -> str:
        """
        Build the risk assessment prompt.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.
        **kwargs
            Optional keys:
            - ``date``: analysis date override (str, ISO 8601)
            - ``extra_context``: additional instructions or data (str)
            - ``portfolio_context``: investor's current portfolio info (str)
            - ``risk_tolerance``: investor's risk tolerance level (str)
        """
        extra_context_parts: list[str] = []

        if portfolio_context := kwargs.get("portfolio_context"):
            extra_context_parts.append(
                f"INVESTOR PORTFOLIO CONTEXT:\n{portfolio_context}"
            )

        if risk_tolerance := kwargs.get("risk_tolerance"):
            extra_context_parts.append(
                f"INVESTOR RISK TOLERANCE: {risk_tolerance}"
            )

        if extra := kwargs.get("extra_context"):
            extra_context_parts.append(extra)

        extra_context_parts.append(
            "Consider both systematic (market-wide) and idiosyncratic "
            "(company-specific) risks. "
            "Be conservative in your estimates when data is limited."
        )

        return build_risk_prompt(
            ticker=ticker,
            date=kwargs.get("date"),
            extra_context="\n\n".join(extra_context_parts) if extra_context_parts else "",
        )

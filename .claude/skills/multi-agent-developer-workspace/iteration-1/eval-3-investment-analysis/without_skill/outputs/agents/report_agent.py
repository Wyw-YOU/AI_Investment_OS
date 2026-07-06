"""
Report Synthesis Agent.

Combines outputs from all specialist agents into a single, actionable
investment report with a recommendation, price targets, and conviction level.
"""

from __future__ import annotations

import json
from typing import Any, Type

from pydantic import BaseModel

from agents.base import BaseAgent
from config import AgentWeightConfig
from prompts import build_report_prompt
from schemas import (
    FinancialAgentOutput,
    InvestmentReport,
    NewsAgentOutput,
    RiskAgentOutput,
    TechnicalAgentOutput,
)
from utils import logger


class ReportAgent(BaseAgent):
    """
    Synthesis agent that combines all specialist analyses into a final
    investment recommendation.

    Responsibilities
    ----------------
    1. Ingest structured outputs from News, Financial, Technical, and Risk agents.
    2. Compute a weighted composite score.
    3. Determine the recommendation (strong_buy through strong_sell).
    4. Set bull/base/bear price targets.
    5. Identify key catalysts and key risks.
    6. Write an actionable summary for the investor.
    """

    def __init__(
        self,
        config: Any | None = None,
        weights: AgentWeightConfig | None = None,
    ) -> None:
        super().__init__(config)
        self.weights = weights or AgentWeightConfig()

    @property
    def agent_name(self) -> str:
        return "report_agent"

    @property
    def output_schema(self) -> Type[BaseModel]:
        return InvestmentReport  # type: ignore[return-value]

    def build_prompt(self, ticker: str, **kwargs: Any) -> str:
        """
        Build the synthesis prompt by injecting all agent outputs as context.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.
        **kwargs
            Required keys:
            - ``news_output``: dict — output from NewsAgent
            - ``financial_output``: dict — output from FinancialAgent
            - ``technical_output``: dict — output from TechnicalAgent
            - ``risk_output``: dict — output from RiskAgent
            Optional keys:
            - ``date``: analysis date override (str)
        """
        news = kwargs.get("news_output", {})
        financial = kwargs.get("financial_output", {})
        technical = kwargs.get("technical_output", {})
        risk = kwargs.get("risk_output", {})

        # Serialize agent outputs as formatted JSON strings for the prompt
        def _fmt(data: dict) -> str:
            if not data:
                return "No data available (agent did not run or failed)."
            return json.dumps(data, indent=2, default=str)

        return build_report_prompt(
            ticker=ticker,
            news_analysis=_fmt(news),
            financial_analysis=_fmt(financial),
            technical_analysis=_fmt(technical),
            risk_analysis=_fmt(risk),
            weights=self.weights.normalized(),
            date=kwargs.get("date"),
        )

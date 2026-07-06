"""
Investment Analysis System - Financial Agent

Specializes in fundamental analysis: profitability, growth, valuation,
and balance sheet health.
"""

from __future__ import annotations

from typing import Any, Dict, List

from base_agent import LLMAgent
from models import AgentOutput
from prompts import build_financial_prompt


class FinancialAgent(LLMAgent):
    """
    Analyzes financial statements and fundamental metrics.

    Reads ``financial_data`` and ``market_data`` from the workflow state
    and produces a structured fundamental analysis with valuation assessment.
    """

    name = "financial_agent"
    description = "Expert in financial analysis, valuation, and fundamental metrics"

    def __init__(self, **kwargs: Any) -> None:
        # Lower temperature for more precise financial analysis
        kwargs.setdefault("temperature", 0.2)
        super().__init__(**kwargs)

    # --- Prompt construction ---

    def build_prompt(self, state: dict) -> str:
        return build_financial_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            financial_data=state.get("financial_data", {}),
            market_data=state.get("market_data", {}),
            query=state.get("query", ""),
        )

    # --- Validation helpers ---

    def _get_expected_output_keys(self) -> List[str]:
        return ["profitability", "growth", "valuation", "health", "thesis"]

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """
        Confidence is driven by:
        1. The LLM-provided confidence
        2. Amount of financial data available
        3. Result completeness (how many sections were populated)
        """
        llm_conf = 0.5
        if "confidence" in result:
            try:
                llm_conf = float(result["confidence"])
            except (TypeError, ValueError):
                pass

        # Assess data availability
        financial_data = state.get("financial_data", {})
        data_keys = len(financial_data)
        data_factor = min(1.0, data_keys / 8)  # 8 expected data fields

        # Result completeness
        expected = self._get_expected_output_keys()
        present = sum(
            1 for k in expected
            if k in result and result[k] and result[k] != {}
        )
        completeness = present / len(expected) if expected else 0.5

        return max(0.0, min(1.0, llm_conf * 0.5 + data_factor * 0.3 + completeness * 0.2))

    # --- Run with data guard ---

    def run(self, state: dict) -> AgentOutput:
        """
        Execute financial analysis with a data availability check.
        """
        financial_data = state.get("financial_data", {})
        if not financial_data:
            self.logger.warning(
                "No financial data available for %s; returning minimal output.",
                state.get("stock_code"),
            )
            return self._create_output(
                result={
                    "profitability": {},
                    "growth": {},
                    "valuation": {},
                    "health": {},
                    "thesis": "Insufficient financial data for analysis.",
                    "citations": [],
                },
                confidence=0.1,
                citations=[],
                metadata={"data_available": False},
            )

        return super().run(state)

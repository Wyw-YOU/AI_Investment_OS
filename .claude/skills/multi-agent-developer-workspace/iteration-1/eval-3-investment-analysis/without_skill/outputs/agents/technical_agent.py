"""
Technical Analysis Agent.

Analyses price action, chart patterns, and technical indicators to produce
a structured technical outlook with actionable entry/exit levels.
"""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel

from agents.base import BaseAgent
from prompts import build_technical_prompt
from schemas import TechnicalAgentOutput


class TechnicalAgent(BaseAgent):
    """
    Specialised agent for technical analysis.

    Responsibilities
    ----------------
    1. Evaluate a broad set of technical indicators (RSI, MACD, MAs,
       Bollinger Bands, ATR, OBV, Stochastic, VWAP).
    2. Detect chart patterns across multiple timeframes.
    3. Identify key support and resistance levels.
    4. Suggest entry, stop-loss, and take-profit prices.
    5. Provide overall signal direction and strength.
    """

    @property
    def agent_name(self) -> str:
        return "technical_agent"

    @property
    def output_schema(self) -> Type[BaseModel]:
        return TechnicalAgentOutput  # type: ignore[return-value]

    def build_prompt(self, ticker: str, **kwargs: Any) -> str:
        """
        Build the technical analysis prompt.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.
        **kwargs
            Optional keys:
            - ``date``: analysis date override (str, ISO 8601)
            - ``extra_context``: additional instructions or data (str)
            - ``price_data``: pre-fetched OHLCV data (str)
            - ``timeframes``: list of timeframes to analyse (str, e.g. "daily, weekly")
        """
        extra_context_parts: list[str] = []

        if price_data := kwargs.get("price_data"):
            extra_context_parts.append(
                f"PRE-FETCHED PRICE DATA (OHLCV):\n{price_data}"
            )

        if timeframes := kwargs.get("timeframes"):
            extra_context_parts.append(
                f"TIMEFRAMES to analyse: {timeframes}"
            )
        else:
            extra_context_parts.append("TIMEFRAMES to analyse: daily, weekly")

        if extra := kwargs.get("extra_context"):
            extra_context_parts.append(extra)

        extra_context_parts.append(
            "Focus on actionable price levels. "
            "Support/resistance should be prices the stock has historically reacted to."
        )

        return build_technical_prompt(
            ticker=ticker,
            date=kwargs.get("date"),
            extra_context="\n\n".join(extra_context_parts) if extra_context_parts else "",
        )

"""
News Sentiment Agent.

Analyses recent news articles, press releases, and social media sentiment
for a given stock ticker and produces a structured sentiment report.
"""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel

from agents.base import BaseAgent
from prompts import build_news_prompt
from schemas import NewsAgentOutput


class NewsAgent(BaseAgent):
    """
    Specialised agent for news sentiment analysis.

    Responsibilities
    ----------------
    1. Aggregate recent news articles about the ticker.
    2. Score sentiment on a -1 to +1 scale.
    3. Identify key market-moving events.
    4. Track whether the news flow is improving or deteriorating.
    """

    @property
    def agent_name(self) -> str:
        return "news_agent"

    @property
    def output_schema(self) -> Type[BaseModel]:
        return NewsAgentOutput  # type: ignore[return-value]

    def build_prompt(self, ticker: str, **kwargs: Any) -> str:
        """
        Build the news analysis prompt.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.
        **kwargs
            Optional keys:
            - ``date``: analysis date override (str, ISO 8601)
            - ``extra_context``: additional instructions or data (str)
            - ``news_items``: pre-fetched news items to include (str)
        """
        extra_context_parts: list[str] = []

        if news_items := kwargs.get("news_items"):
            extra_context_parts.append(
                f"PRE-FETCHED NEWS ITEMS (use these as primary data):\n{news_items}"
            )

        if extra := kwargs.get("extra_context"):
            extra_context_parts.append(extra)

        time_horizon = kwargs.get("time_horizon", "short-term")
        extra_context_parts.append(
            f"Focus on {time_horizon} sentiment impact on the stock price."
        )

        return build_news_prompt(
            ticker=ticker,
            date=kwargs.get("date"),
            extra_context="\n\n".join(extra_context_parts) if extra_context_parts else "",
        )

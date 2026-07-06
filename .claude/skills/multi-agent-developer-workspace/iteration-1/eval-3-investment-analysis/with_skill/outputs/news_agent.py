"""
Investment Analysis System - News Agent

Specializes in sentiment analysis and event extraction from financial news.
"""

from __future__ import annotations

from typing import Any, Dict, List

from base_agent import LLMAgent
from models import AgentOutput, Sentiment
from prompts import build_news_prompt


class NewsAgent(LLMAgent):
    """
    Analyzes financial news for sentiment, key events, and risk factors.

    Reads ``news_data`` and ``market_data`` from the workflow state and
    produces a structured sentiment analysis with event extraction.
    """

    name = "news_agent"
    description = "Expert in financial news analysis, sentiment detection, and event extraction"

    def __init__(self, **kwargs: Any) -> None:
        # Default to a slightly higher temperature for richer language
        kwargs.setdefault("temperature", 0.4)
        super().__init__(**kwargs)

    # --- Prompt construction ---

    def build_prompt(self, state: dict) -> str:
        return build_news_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            news_data=state.get("news_data", []),
            market_data=state.get("market_data", {}),
            query=state.get("query", ""),
        )

    # --- Validation helpers ---

    def _get_expected_output_keys(self) -> List[str]:
        return ["sentiment", "sentiment_score", "events", "risk_factors"]

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """
        Confidence is driven by:
        1. The LLM-provided confidence (if present)
        2. Amount of news data available
        3. Completeness of the parsed result
        """
        # If LLM provided a confidence value, use it as a starting point
        llm_conf = 0.5
        if "confidence" in result:
            try:
                llm_conf = float(result["confidence"])
            except (TypeError, ValueError):
                pass

        # Penalize if news data was empty/sparse
        news_count = len(state.get("news_data", []))
        if news_count == 0:
            data_factor = 0.2
        elif news_count < 3:
            data_factor = 0.6
        else:
            data_factor = 1.0

        # Reward for result completeness
        expected = self._get_expected_output_keys()
        present = sum(1 for k in expected if k in result and result[k])
        completeness = present / len(expected) if expected else 0.5

        return max(0.0, min(1.0, llm_conf * 0.6 + data_factor * 0.2 + completeness * 0.2))

    def _extract_citations(self, result: dict, state: dict) -> List[str]:
        """Extract citations from news articles and the result."""
        citations = super()._extract_citations(result, state)

        # Add source names from news_data as citations
        for article in state.get("news_data", []):
            source = article.get("source", "")
            if source and source not in citations:
                citations.append(source)

        return citations

    # --- Run with data availability guard ---

    def run(self, state: dict) -> AgentOutput:
        """
        Execute news analysis with a data availability check.

        If no news data is provided, returns a low-confidence neutral output
        rather than calling the LLM with empty context.
        """
        news_data = state.get("news_data", [])
        if not news_data:
            self.logger.warning(
                "No news data available for %s; returning neutral fallback.",
                state.get("stock_code"),
            )
            return self._create_output(
                result={
                    "sentiment": Sentiment.NEUTRAL.value,
                    "sentiment_score": 0.5,
                    "events": [],
                    "risk_factors": ["Insufficient news data for analysis"],
                    "key_quotes": [],
                    "citations": [],
                },
                confidence=0.1,
                citations=[],
                metadata={"data_available": False},
            )

        return super().run(state)

"""
Investment Analysis System - Technical Agent

Specializes in technical analysis: chart patterns, momentum indicators,
support/resistance levels, and trading signals.
"""

from __future__ import annotations

from typing import Any, Dict, List

from base_agent import LLMAgent
from models import AgentOutput
from prompts import build_technical_prompt


class TechnicalAgent(LLMAgent):
    """
    Analyzes price data for technical patterns and trading signals.

    Reads ``price_history`` and ``market_data`` from the workflow state
    and produces a structured technical analysis with actionable signals.
    """

    name = "technical_agent"
    description = "Expert in technical analysis, chart patterns, and trading signals"

    def __init__(self, **kwargs: Any) -> None:
        # Low temperature for precise, repeatable technical analysis
        kwargs.setdefault("temperature", 0.2)
        super().__init__(**kwargs)

    # --- Prompt construction ---

    def build_prompt(self, state: dict) -> str:
        return build_technical_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            price_history=state.get("price_history", []),
            market_data=state.get("market_data", {}),
            query=state.get("query", ""),
        )

    # --- Validation ---

    def _get_expected_output_keys(self) -> List[str]:
        return ["trend", "levels", "indicators", "volume", "signals"]

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """
        Confidence is driven by:
        1. The LLM-provided confidence
        2. Amount of price history data (more bars = higher confidence)
        3. Internal consistency of the trading signal
        """
        llm_conf = 0.5
        if "confidence" in result:
            try:
                llm_conf = float(result["confidence"])
            except (TypeError, ValueError):
                pass

        # Price data availability
        price_count = len(state.get("price_history", []))
        if price_count == 0:
            data_factor = 0.1
        elif price_count < 10:
            data_factor = 0.4
        elif price_count < 30:
            data_factor = 0.7
        else:
            data_factor = 1.0

        # Internal consistency check: are entry/stop/target consistent?
        consistency = self._check_signal_consistency(result)

        return max(0.0, min(1.0, llm_conf * 0.4 + data_factor * 0.3 + consistency * 0.3))

    @staticmethod
    def _check_signal_consistency(result: dict) -> float:
        """Verify that trading signal numbers are internally consistent."""
        signals = result.get("signals", {})
        if not signals:
            return 0.3

        action = signals.get("action", "").lower()
        entry = signals.get("entry_price")
        stop = signals.get("stop_loss")
        target = signals.get("target_price")

        if not all([entry, stop, target]):
            return 0.5

        try:
            entry_f = float(entry)
            stop_f = float(stop)
            target_f = float(target)
        except (TypeError, ValueError):
            return 0.4

        # Basic sanity: for a BUY, stop < entry < target
        if action == "buy":
            if stop_f < entry_f < target_f:
                return 1.0
            return 0.3
        elif action == "sell":
            if stop_f > entry_f > target_f:
                return 1.0
            return 0.3
        else:  # hold
            return 0.7

    # --- Run with data guard ---

    def run(self, state: dict) -> AgentOutput:
        """Execute technical analysis with a price data availability check."""
        price_history = state.get("price_history", [])
        if not price_history:
            self.logger.warning(
                "No price history available for %s; returning neutral fallback.",
                state.get("stock_code"),
            )
            return self._create_output(
                result={
                    "trend": {
                        "short_term": "neutral",
                        "medium_term": "neutral",
                        "long_term": "neutral",
                    },
                    "levels": {"support": [], "resistance": []},
                    "indicators": {},
                    "volume": {"trend": "unknown", "relative_volume": 0, "analysis": ""},
                    "patterns": [],
                    "signals": {
                        "action": "hold",
                        "entry_price": None,
                        "stop_loss": None,
                        "target_price": None,
                        "risk_reward_ratio": None,
                    },
                    "citations": [],
                },
                confidence=0.1,
                citations=[],
                metadata={"data_available": False},
            )

        return super().run(state)

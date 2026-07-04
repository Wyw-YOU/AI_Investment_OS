"""TechnicalAgent — technical analysis using indicators + LLM."""
import logging
from typing import Any, Dict

from app.agents.base import BaseAgent, register_agent
from app.agents.state import InvestmentState
from app.services.indicators import calculate_all_indicators

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a technical analysis expert. Based on the indicators provided, "
    "return a JSON with: trend (bullish/bearish/sideways), support_levels, "
    "resistance_levels, indicators dict, verdict (buy/sell/hold)."
)


class TechnicalAgent(BaseAgent):
    name = "technical"

    def __init__(self, llm=None):
        self.llm = llm

    def run(self, state: InvestmentState) -> Dict[str, Any]:
        stock = state.current_stock
        market = state.market_data
        pre_calc = state.indicators

        closes = self._extract_closes(market)
        highs = self._extract_series(market, "high")
        lows = self._extract_series(market, "low")

        if not closes:
            return self._build_result(
                output={"trend": "unknown", "verdict": "hold", "indicators": {}},
                confidence=0.1,
                evidence=["no price data available"],
                reasoning="Cannot perform technical analysis without price data.",
            )

        indicators = pre_calc if pre_calc else calculate_all_indicators(closes, highs, lows)

        if self.llm:
            return self._analyze_with_llm(stock, indicators, closes)

        return self._analyze_rule_based(stock, indicators, closes)

    def _analyze_with_llm(self, stock: str, indicators: dict, closes: list) -> dict:
        prompt = (
            f"Stock {stock}, current price: {closes[-1]:.2f}\n"
            f"Indicators: {indicators}\n"
            f"Analyze and return JSON with trend, support_levels, "
            f"resistance_levels, indicators, verdict."
        )
        llm_result = self.llm.generate_json(prompt, system_prompt=SYSTEM_PROMPT)
        if llm_result:
            return self._build_result(
                output=llm_result,
                confidence=0.75,
                evidence=[f"Current price: {closes[-1]:.2f}", f"RSI: {indicators.get('rsi', {})}"],
                reasoning=f"LLM-based technical analysis for {stock}.",
            )
        return self._analyze_rule_based(stock, indicators, closes)

    def _analyze_rule_based(self, stock: str, indicators: dict, closes: list) -> dict:
        rsi = indicators.get("rsi", {}).get("value", 50)
        macd = indicators.get("macd", {})
        boll = indicators.get("bollinger", {})
        ma = indicators.get("ma", {})
        current = closes[-1]

        buy_signals = 0
        sell_signals = 0

        if rsi < 30:
            buy_signals += 1
        elif rsi > 70:
            sell_signals += 1

        if macd.get("histogram", 0) > 0:
            buy_signals += 1
        elif macd.get("histogram", 0) < 0:
            sell_signals += 1

        if current < boll.get("lower", current):
            buy_signals += 1
        elif current > boll.get("upper", current):
            sell_signals += 1

        ma20 = ma.get("ma20", current)
        if current > ma20:
            buy_signals += 1
        else:
            sell_signals += 1

        if buy_signals >= 3:
            verdict = "buy"
            trend = "bullish"
        elif sell_signals >= 3:
            verdict = "sell"
            trend = "bearish"
        else:
            verdict = "hold"
            trend = "sideways"

        support = sorted(closes[-5:])[:2]
        resistance = sorted(closes[-5:])[-2:]

        result = self._build_result(
            output={
                "trend": trend,
                "support_levels": support,
                "resistance_levels": resistance,
                "indicators": indicators,
                "verdict": verdict,
            },
            confidence=0.65,
            evidence=[
                f"RSI: {rsi:.1f}",
                f"MACD histogram: {macd.get('histogram', 0):.4f}",
                f"Buy signals: {buy_signals}, Sell signals: {sell_signals}",
            ],
            reasoning=f"Technical analysis: {buy_signals} buy vs {sell_signals} sell signals, "
                      f"trend={trend}, verdict={verdict}.",
        )
        return result

    def _extract_closes(self, market: dict) -> list[float]:
        klines = market.get("klines", [])
        if klines:
            return [k["close"] for k in klines if "close" in k]
        return market.get("closes", [])

    def _extract_series(self, market: dict, key: str) -> list[float]:
        klines = market.get("klines", [])
        if klines:
            return [k[key] for k in klines if key in k]
        return market.get(f"{key}s", [])


register_agent(TechnicalAgent())

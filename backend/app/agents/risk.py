"""RiskAgent — risk assessment using market data + indicators."""
import logging
from typing import Any, Dict

from app.agents.base import BaseAgent, register_agent
from app.agents.state import InvestmentState

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    name = "risk"

    def run(self, state: InvestmentState) -> Dict[str, Any]:
        stock = state.current_stock
        market = state.market_data
        indicators = state.indicators

        closes = self._extract_closes(market)

        if not closes or len(closes) < 20:
            return self._build_result(
                output={"risk_level": "UNKNOWN", "verdict": "caution",
                        "volatility_30d": 0, "risk_factors": []},
                confidence=0.1,
                evidence=["insufficient price data for risk assessment"],
                reasoning="Need at least 20 days of price data for risk analysis.",
            )

        return self._assess(stock, closes, indicators)

    def _assess(self, stock: str, closes: list, indicators: dict) -> dict:
        volatility = self._calc_volatility(closes[-30:])
        beta = self._estimate_beta(closes)
        rsi = indicators.get("rsi", {}).get("value", 50)
        boll = indicators.get("bollinger", {})

        risk_factors = []
        risk_score = 0

        if volatility > 0.03:
            risk_factors.append(f"High volatility: {volatility:.2%}")
            risk_score += 2
        elif volatility > 0.02:
            risk_factors.append(f"Moderate volatility: {volatility:.2%}")
            risk_score += 1

        if beta > 1.5:
            risk_factors.append(f"High beta: {beta:.2f}")
            risk_score += 1

        if rsi > 80:
            risk_factors.append(f"Overbought RSI: {rsi:.1f}")
            risk_score += 1
        elif rsi < 20:
            risk_factors.append(f"Oversold RSI: {rsi:.1f}")
            risk_score += 1

        price = closes[-1]
        ma60 = sum(closes[-60:]) / min(60, len(closes)) if len(closes) >= 20 else price
        if price > ma60 * 1.2:
            risk_factors.append("Price significantly above 60-day average")
            risk_score += 1

        if risk_score >= 4:
            risk_level = "HIGH"
            verdict = "dangerous"
        elif risk_score >= 2:
            risk_level = "MEDIUM"
            verdict = "caution"
        else:
            risk_level = "LOW"
            verdict = "acceptable"

        return self._build_result(
            output={
                "risk_level": risk_level,
                "volatility_30d": round(volatility, 4),
                "beta": round(beta, 2),
                "risk_factors": risk_factors,
                "verdict": verdict,
            },
            confidence=0.6,
            evidence=[
                f"30d volatility: {volatility:.2%}",
                f"Beta: {beta:.2f}",
                f"Risk score: {risk_score}",
            ],
            reasoning=f"Risk assessment: level={risk_level}, "
                      f"volatility={volatility:.2%}, beta={beta:.2f}, "
                      f"{len(risk_factors)} risk factors identified.",
        )

    def _calc_volatility(self, prices: list) -> float:
        if len(prices) < 2:
            return 0.0
        returns = [(prices[i] - prices[i - 1]) / prices[i - 1]
                   for i in range(1, len(prices)) if prices[i - 1] != 0]
        if not returns:
            return 0.0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return variance ** 0.5

    def _estimate_beta(self, closes: list) -> float:
        if len(closes) < 20:
            return 1.0
        short_vol = self._calc_volatility(closes[-20:])
        long_vol = self._calc_volatility(closes[-60:]) if len(closes) >= 60 else short_vol
        if long_vol == 0:
            return 1.0
        return short_vol / long_vol

    def _extract_closes(self, market: dict) -> list:
        klines = market.get("klines", [])
        if klines:
            return [k["close"] for k in klines if "close" in k]
        return market.get("closes", [])


register_agent(RiskAgent())

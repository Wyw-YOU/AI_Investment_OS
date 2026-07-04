"""JudgeAgent — aggregates all agent outputs into a final verdict."""
import logging
from typing import Any, Dict

from app.agents.base import BaseAgent, register_agent
from app.agents.state import InvestmentState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior investment judge. Given analysis results from finance, "
    "technical, news, and risk agents, produce a JSON with: "
    "overall_score (0-100), verdict (strong_buy/buy/hold/sell/strong_sell), "
    "confidence, summary, key_points list, warnings list."
)


class JudgeAgent(BaseAgent):
    name = "judge"

    def __init__(self, llm=None):
        self.llm = llm

    def run(self, state: InvestmentState) -> Dict[str, Any]:
        stock = state.current_stock
        outputs = state.agent_outputs
        confidences = state.agent_confidence

        if not outputs:
            return self._build_result(
                output={"overall_score": 0, "verdict": "hold", "summary": "No agent outputs available."},
                confidence=0.0,
                evidence=["no agent outputs"],
                reasoning="Cannot judge without agent analysis results.",
            )

        if self.llm:
            return self._judge_with_llm(stock, outputs, confidences)

        return self._judge_rule_based(stock, outputs, confidences)

    def _judge_with_llm(self, stock: str, outputs: dict, confidences: dict) -> dict:
        prompt = (
            f"Stock: {stock}\n\n"
            f"Finance analysis: {outputs.get('finance', {})}\n"
            f"Technical analysis: {outputs.get('technical', {})}\n"
            f"News analysis: {outputs.get('news', {})}\n"
            f"Risk analysis: {outputs.get('risk', {})}\n\n"
            f"Agent confidences: {confidences}\n\n"
            f"Provide overall judgment as JSON."
        )
        llm_result = self.llm.generate_json(prompt, system_prompt=SYSTEM_PROMPT)
        if llm_result:
            avg_conf = sum(confidences.values()) / max(len(confidences), 1)
            return self._build_result(
                output=llm_result,
                confidence=round(avg_conf, 2),
                evidence=[f"{name}: {out.get('verdict', 'N/A')}" for name, out in outputs.items()],
                reasoning=f"LLM-aggregated judgment for {stock}.",
            )
        return self._judge_rule_based(stock, outputs, confidences)

    def _judge_rule_based(self, stock: str, outputs: dict, confidences: dict) -> dict:
        score = 50
        key_points = []
        warnings = []

        fin = outputs.get("finance", {})
        fin_verdict = fin.get("verdict", "unknown")
        if fin_verdict == "undervalued":
            score += 15
            key_points.append("Fundamentals: undervalued")
        elif fin_verdict == "overvalued":
            score -= 15
            warnings.append("Fundamentals: overvalued")

        tech = outputs.get("technical", {})
        tech_verdict = tech.get("verdict", "hold")
        if tech_verdict == "buy":
            score += 10
            key_points.append("Technical: buy signal")
        elif tech_verdict == "sell":
            score -= 10
            warnings.append("Technical: sell signal")

        news = outputs.get("news", {})
        news_verdict = news.get("verdict", "neutral")
        if news_verdict == "positive":
            score += 5
            key_points.append("News sentiment: positive")
        elif news_verdict == "negative":
            score -= 5
            warnings.append("News sentiment: negative")

        risk = outputs.get("risk", {})
        risk_level = risk.get("risk_level", "MEDIUM")
        if risk_level == "HIGH":
            score -= 10
            warnings.append("Risk level: HIGH")
        elif risk_level == "LOW":
            score += 5

        score = max(0, min(100, score))

        if score >= 75:
            verdict = "strong_buy" if score >= 85 else "buy"
        elif score >= 45:
            verdict = "hold"
        elif score >= 25:
            verdict = "sell"
        else:
            verdict = "strong_sell"

        avg_conf = sum(confidences.values()) / max(len(confidences), 1)

        return self._build_result(
            output={
                "overall_score": score,
                "verdict": verdict,
                "confidence": round(avg_conf, 2),
                "summary": f"{stock} scored {score}/100, verdict: {verdict}.",
                "key_points": key_points,
                "warnings": warnings,
            },
            confidence=round(avg_conf, 2),
            evidence=key_points + warnings,
            reasoning=f"Aggregated {len(outputs)} agent outputs: score={score}, verdict={verdict}.",
        )


register_agent(JudgeAgent())

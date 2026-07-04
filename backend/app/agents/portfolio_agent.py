"""PortfolioAgent — portfolio weight suggestion and optimization."""
import logging
from typing import Any, Dict

from app.agents.base import BaseAgent, register_agent
from app.agents.state import InvestmentState

logger = logging.getLogger(__name__)


class PortfolioAgent(BaseAgent):
    name = "portfolio"

    def run(self, state: InvestmentState) -> Dict[str, Any]:
        stock = state.current_stock
        judge_output = state.get_agent_output("judge")
        portfolio = state.portfolio

        if not judge_output:
            return self._build_result(
                output={"suggested_weight": 0.0, "action": "hold", "reason": "no judge output"},
                confidence=0.0,
                evidence=["no judge output available"],
                reasoning="Cannot suggest portfolio changes without judge verdict.",
            )

        return self._suggest(stock, judge_output, portfolio)

    def _suggest(self, stock: str, judge: dict, portfolio: dict) -> dict:
        verdict = judge.get("verdict", "hold")
        score = judge.get("overall_score", 50)

        holdings = portfolio.get("holdings", {})
        current_weight = holdings.get(stock, 0.0)

        if verdict in ("strong_buy", "buy"):
            if score >= 85:
                suggested = min(0.30, current_weight + 0.10)
            else:
                suggested = min(0.20, current_weight + 0.05)
            action = "increase"
        elif verdict in ("strong_sell", "sell"):
            suggested = max(0.0, current_weight - 0.10)
            action = "decrease" if suggested > 0 else "remove"
        else:
            suggested = current_weight
            action = "hold"

        confidence = judge.get("confidence", 0.5) * 0.8

        evidence = [
            f"Judge verdict: {verdict}",
            f"Judge score: {score}",
            f"Current weight: {current_weight:.1%}",
        ]

        return self._build_result(
            output={
                "stock": stock,
                "suggested_weight": round(suggested, 4),
                "current_weight": current_weight,
                "action": action,
                "verdict": verdict,
                "reason": f"Score {score}/100 suggests {action} position.",
            },
            confidence=round(confidence, 2),
            evidence=evidence,
            reasoning=f"Based on judge verdict={verdict} (score={score}), "
                      f"suggest {action} from {current_weight:.1%} to {suggested:.1%}.",
        )


register_agent(PortfolioAgent())

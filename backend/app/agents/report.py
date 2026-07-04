"""ReportAgent — generates final structured analysis report."""
import logging
from typing import Any, Dict
from datetime import datetime, timezone

from app.agents.base import BaseAgent, register_agent
from app.agents.state import InvestmentState

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    name = "report"

    def run(self, state: InvestmentState) -> Dict[str, Any]:
        stock = state.current_stock
        outputs = state.agent_outputs
        judge = outputs.get("judge", {})
        portfolio = outputs.get("portfolio", {})

        if not judge:
            return self._build_result(
                output={"error": "no judge output", "stock": stock},
                confidence=0.0,
                evidence=["no judge output"],
                reasoning="Cannot generate report without judge verdict.",
            )

        report = {
            "stock": stock,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_score": judge.get("overall_score", 0),
            "verdict": judge.get("verdict", "hold"),
            "summary": judge.get("summary", ""),
            "key_points": judge.get("key_points", []),
            "warnings": judge.get("warnings", []),
            "portfolio_action": portfolio.get("action", "hold"),
            "suggested_weight": portfolio.get("suggested_weight", 0),
            "agent_details": {
                "finance": self._summarize_agent(outputs.get("finance", {})),
                "technical": self._summarize_agent(outputs.get("technical", {})),
                "news": self._summarize_agent(outputs.get("news", {})),
                "risk": self._summarize_agent(outputs.get("risk", {})),
            },
            "agents_used": list(outputs.keys()),
        }

        result = self._build_result(
            output=report,
            confidence=judge.get("confidence", 0.5),
            evidence=[f"Generated report with {len(outputs)} agent outputs"],
            reasoning=f"Final report for {stock}: score={report['overall_score']}, "
                      f"verdict={report['verdict']}.",
        )
        self._log_run(state, result)
        return result

    def _summarize_agent(self, output: dict) -> dict:
        if not output:
            return {"status": "not_available"}
        return {
            "verdict": output.get("verdict", "N/A"),
            "key_data": {k: v for k, v in output.items()
                         if k in ("risk_level", "sentiment", "trend", "pe_ratio", "roe")},
        }


register_agent(ReportAgent())

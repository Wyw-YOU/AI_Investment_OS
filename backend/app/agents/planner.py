"""PlannerAgent — plans analysis tasks and scheduling strategy."""
import logging
from typing import Any, Dict

from app.agents.base import BaseAgent, register_agent
from app.agents.state import InvestmentState

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    name = "planner"

    def run(self, state: InvestmentState) -> Dict[str, Any]:
        stock = state.current_stock
        if not stock:
            return self._build_result(
                output={"error": "no stock specified", "tasks": []},
                confidence=0.0,
                evidence=["current_stock is empty"],
                reasoning="No stock code provided for analysis.",
            )

        tasks = [
            {"agent": "finance", "priority": "high", "task": "fundamental analysis"},
            {"agent": "technical", "priority": "high", "task": "technical indicator analysis"},
            {"agent": "news", "priority": "medium", "task": "news sentiment analysis"},
            {"agent": "risk", "priority": "medium", "task": "risk assessment"},
        ]

        result = self._build_result(
            output={"stock": stock, "tasks": tasks, "parallel": True},
            confidence=0.9,
            evidence=[f"Stock code {stock} validated", f"Planned {len(tasks)} analysis tasks"],
            reasoning=f"Standard multi-agent analysis pipeline for {stock}: "
                      f"finance, technical, news, risk in parallel, then judge, portfolio, report.",
        )
        self._log_run(state, result)
        return result


register_agent(PlannerAgent())

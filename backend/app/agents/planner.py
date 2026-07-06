from app.agents.base import BaseAgent
from app.agents.models import AgentOutput


class PlannerAgent(BaseAgent):
    name = "planner"
    description = "a task planning agent that organizes the analysis workflow"

    def run(self, state: dict) -> AgentOutput:
        stock_code = state.get("stock_code", "")
        has_news = bool(state.get("news_data"))
        has_financial = bool(state.get("financial_data"))
        has_history = bool(state.get("price_history"))

        tasks = []
        if has_news:
            tasks.append({"agent": "news", "priority": "high", "reason": "Sentiment analysis"})
        if has_financial:
            tasks.append({"agent": "financial", "priority": "high", "reason": "Fundamental analysis"})
        if has_history:
            tasks.append({"agent": "technical", "priority": "high", "reason": "Technical analysis"})
        tasks.append({"agent": "macro", "priority": "medium", "reason": "Macro environment"})

        return AgentOutput(
            agent_name=self.name,
            result={
                "tasks": tasks,
                "parallel_agents": ["news", "financial", "technical", "macro"],
                "sequential_agents": ["risk", "quant", "report"],
                "total_steps": len(tasks) + 3,
            },
            confidence=1.0,
            citations=[f"Planned analysis for {stock_code}"],
        )

    def _get_expected_output_keys(self) -> list[str]:
        return ["tasks", "parallel_agents"]

"""
任务规划 Agent：workflow 的第一个节点，不调用 LLM（纯逻辑）。
根据输入数据（是否有新闻、财报、历史K线）决定后续需要并行执行哪些分析 agent。
"""

from app.agents.base import BaseAgent
from app.agents.models import AgentOutput


class PlannerAgent(BaseAgent):
    """任务规划 Agent，分析输入数据可用性，决定并行分析任务列表。"""
    name = "planner"
    description = "a task planning agent that organizes the analysis workflow"

    async def run(self, state: dict) -> AgentOutput:
        """
        根据 state 中的数据可用性动态决定并行任务：
        - 有 news_data → 添加 news agent
        - 有 financial_data → 添加 financial agent
        - 有 price_history → 添加 technical agent
        - 始终添加 macro agent（即使没有专门数据）
        """
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

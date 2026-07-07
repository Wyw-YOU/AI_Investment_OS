"""
新闻分析 Agent：分析个股相关新闻的情感倾向。
置信度计算：新闻数量充足 + 有情感判断 + 有事件提取 → 高置信度。
"""

from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_news_prompt


class NewsAgent(LLMAgent):
    """新闻情感分析 Agent，专注于 A 股个股新闻的情绪判断和事件提取。"""
    name = "news"
    description = "a senior financial news analyst specializing in sentiment analysis"

    def build_prompt(self, state: dict) -> str:
        """从 workflow state 中提取新闻数据，构建分析 prompt。"""
        return build_news_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            news_data=state.get("news_data", []),
            market_data=state.get("market_data"),
        )

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """
        根据数据完整度计算置信度。
        权重：数据量(0.3) + 有情感判断(0.3) + 有事件提取(0.2) + 基础分(0.2)
        """
        if result.get("parse_error"):
            return 0.1
        news_count = len(state.get("news_data", []))
        data_factor = min(1.0, news_count / 5)
        has_sentiment = 1.0 if result.get("sentiment") else 0.0
        has_events = 1.0 if result.get("events") else 0.0
        return round(0.3 * data_factor + 0.3 * has_sentiment + 0.2 * has_events + 0.2, 2)

    def _get_expected_output_keys(self) -> list[str]:
        """LLM 应返回的 JSON 字段，用于计算置信度时检查完整性。"""
        return ["sentiment", "sentiment_score", "events", "summary"]

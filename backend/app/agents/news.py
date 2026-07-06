from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_news_prompt


class NewsAgent(LLMAgent):
    name = "news"
    description = "a senior financial news analyst specializing in sentiment analysis"

    def build_prompt(self, state: dict) -> str:
        return build_news_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            news_data=state.get("news_data", []),
            market_data=state.get("market_data"),
        )

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        if result.get("parse_error"):
            return 0.1
        news_count = len(state.get("news_data", []))
        data_factor = min(1.0, news_count / 5)
        has_sentiment = 1.0 if result.get("sentiment") else 0.0
        has_events = 1.0 if result.get("events") else 0.0
        return round(0.3 * data_factor + 0.3 * has_sentiment + 0.2 * has_events + 0.2, 2)

    def _get_expected_output_keys(self) -> list[str]:
        return ["sentiment", "sentiment_score", "events", "summary"]

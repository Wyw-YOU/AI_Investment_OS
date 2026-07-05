"""NewsAgent — news sentiment analysis with RAG enhancement."""
import logging
from typing import Any, Dict

from app.agents.base import BaseAgent, register_agent
from app.agents.state import InvestmentState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a financial news analyst. Based on the news articles provided, "
    "analyze market sentiment and return a JSON with: sentiment_score (-1.0 to 1.0), "
    "sentiment (positive/negative/neutral), key_events list, rag_insights list, "
    "verdict (positive/negative/neutral)."
)


class NewsAgent(BaseAgent):
    name = "news"

    def __init__(self, llm=None, vector_store=None):
        self.llm = llm
        self.vector_store = vector_store

    def run(self, state: InvestmentState) -> Dict[str, Any]:
        stock = state.current_stock
        news_list = state.news_data

        if not news_list:
            return self._build_result(
                output={"sentiment_score": 0.0, "sentiment": "neutral",
                        "key_events": [], "rag_insights": [], "verdict": "neutral"},
                confidence=0.1,
                evidence=["no news data available"],
                reasoning="No news articles found for analysis.",
            )

        rag_insights = self._get_rag_insights(stock)

        if self.llm:
            return self._analyze_with_llm(stock, news_list, rag_insights)

        return self._analyze_rule_based(stock, news_list, rag_insights)

    def _get_rag_insights(self, stock: str) -> list[str]:
        if not self.vector_store:
            return []
        try:
            results = self.vector_store.search(f"{stock} 相关研报和分析", top_k=3)
            return [r["text"] for r in results]
        except Exception as e:
            logger.warning(f"RAG search failed: {e}")
            return []

    def _analyze_with_llm(self, stock: str, news_list: list, rag_insights: list) -> dict:
        news_text = "\n".join(
            f"- {n.get('title', '')}: {n.get('content', '')[:200]}"
            for n in news_list[:10]
        )
        prompt = (
            f"Stock: {stock}\n\nRecent news:\n{news_text}\n\n"
            f"RAG insights: {rag_insights}\n\n"
            f"Analyze sentiment and return JSON."
        )
        llm_result = self.llm.generate_json(prompt, system_prompt=SYSTEM_PROMPT)
        if llm_result and self.validate_llm_output(llm_result, ["sentiment"]):
            return self._build_result(
                output=llm_result,
                confidence=0.7,
                evidence=[n.get("title", "") for n in news_list[:3]],
                reasoning=f"LLM-based news sentiment analysis for {stock}.",
            )
        return self._analyze_rule_based(stock, news_list, rag_insights)

    def _analyze_rule_based(self, stock: str, news_list: list, rag_insights: list) -> dict:
        positive_kw = ["超预期", "增长", "利好", "突破", "创新高", "增持", "回购", "分红"]
        negative_kw = ["下跌", "亏损", "暴雷", "减持", "违规", "退市", "利空", "低于预期"]

        pos_count = 0
        neg_count = 0
        key_events = []

        for news in news_list:
            title = news.get("title", "")
            content = news.get("content", "")
            text = title + content

            pos = sum(1 for kw in positive_kw if kw in text)
            neg = sum(1 for kw in negative_kw if kw in text)
            pos_count += pos
            neg_count += neg

            if pos > 0 or neg > 0:
                impact = "high" if max(pos, neg) >= 2 else "medium"
                key_events.append({"title": title, "impact": impact})

        total = pos_count + neg_count
        if total == 0:
            sentiment_score = 0.0
            sentiment = "neutral"
        else:
            sentiment_score = round((pos_count - neg_count) / total, 2)
            if sentiment_score > 0.2:
                sentiment = "positive"
            elif sentiment_score < -0.2:
                sentiment = "negative"
            else:
                sentiment = "neutral"

        return self._build_result(
            output={
                "sentiment_score": sentiment_score,
                "sentiment": sentiment,
                "key_events": key_events,
                "rag_insights": rag_insights,
                "verdict": sentiment,
            },
            confidence=0.55,
            evidence=[f"Analyzed {len(news_list)} articles",
                       f"Positive: {pos_count}, Negative: {neg_count}"],
            reasoning=f"Rule-based sentiment: score={sentiment_score}, "
                      f"positive={pos_count}, negative={neg_count}.",
        )


register_agent(NewsAgent())

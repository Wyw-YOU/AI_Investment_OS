"""News data service — news crawling and sentiment."""
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self, cache=None):
        self.cache = cache

    def get_stock_news(self, stock_code: str, limit: int = 10) -> List[Dict]:
        """Get recent news for a stock."""
        cache_key = f"news:{stock_code}:recent"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            import akshare as ak
            df = ak.stock_news_em(symbol=stock_code)
            if df is None or df.empty:
                return []

            news_list = []
            for _, row in df.head(limit).iterrows():
                news_list.append({
                    "title": str(row.get("新闻标题", "")),
                    "content": str(row.get("新闻内容", ""))[:500],
                    "source": str(row.get("文章来源", "")),
                    "time": str(row.get("发布时间", "")),
                    "url": str(row.get("新闻链接", "")),
                })

            if self.cache:
                self.cache.set(cache_key, news_list, ttl=1800)
            return news_list
        except Exception as e:
            logger.error(f"Failed to fetch news for {stock_code}: {e}")
            return []

    def get_market_news(self, limit: int = 20) -> List[Dict]:
        """Get general market news."""
        try:
            import akshare as ak
            df = ak.stock_news_em(symbol="市场")
            if df is None or df.empty:
                return []

            news_list = []
            for _, row in df.head(limit).iterrows():
                news_list.append({
                    "title": str(row.get("新闻标题", "")),
                    "content": str(row.get("新闻内容", ""))[:500],
                    "source": str(row.get("文章来源", "")),
                    "time": str(row.get("发布时间", "")),
                })
            return news_list
        except Exception as e:
            logger.error(f"Failed to fetch market news: {e}")
            return []

    def extract_key_events(self, news_list: List[Dict]) -> List[Dict]:
        """Extract key events from news (rule-based for now, LLM-enhanced in Phase 2)."""
        key_events = []
        impact_keywords = {
            "high": ["涨停", "跌停", "暴雷", "退市", "收购", "重组", "业绩大幅", "违规"],
            "medium": ["分红", "增持", "减持", "回购", "配股", "战略", "合作"],
            "low": ["调研", "评级", "研报", "关注", "行业", "政策"],
        }

        for news in news_list:
            title = news.get("title", "")
            impact = "low"
            for level, keywords in impact_keywords.items():
                if any(kw in title for kw in keywords):
                    impact = level
                    break

            if impact != "low":
                key_events.append({
                    "title": title,
                    "impact": impact,
                    "time": news.get("time", ""),
                    "source": news.get("source", ""),
                })

        return key_events

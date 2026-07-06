import logging
from typing import Any

import akshare as ak

from app.services.cache import cache

logger = logging.getLogger(__name__)


class NewsService:
    async def fetch_stock_news(self, code: str, limit: int = 10) -> list[dict[str, Any]]:
        cached = await cache.get(f"news:{code}")
        if cached:
            return cached
        try:
            df = ak.stock_news_em(symbol=code)
            if df is None or df.empty:
                return []
            result = []
            for _, row in df.head(limit).iterrows():
                result.append({
                    "title": str(row.get("新闻标题", "")),
                    "source": str(row.get("新闻来源", "")),
                    "content": str(row.get("新闻内容", ""))[:500],
                    "published_at": str(row.get("发布时间", "")),
                    "url": str(row.get("新闻链接", "")),
                })
            await cache.set(f"news:{code}", result, ttl=300)
            return result
        except Exception as e:
            logger.error(f"Failed to fetch news for {code}: {e}")
            return []

    async def fetch_market_news(self, limit: int = 15) -> list[dict[str, Any]]:
        cached = await cache.get("news:market")
        if cached:
            return cached
        try:
            df = ak.stock_news_em(symbol="市场")
            if df is None or df.empty:
                return []
            result = []
            for _, row in df.head(limit).iterrows():
                result.append({
                    "title": str(row.get("新闻标题", "")),
                    "source": str(row.get("新闻来源", "")),
                    "content": str(row.get("新闻内容", ""))[:500],
                    "published_at": str(row.get("发布时间", "")),
                })
            await cache.set("news:market", result, ttl=300)
            return result
        except Exception as e:
            logger.error(f"Failed to fetch market news: {e}")
            return []


news_service = NewsService()

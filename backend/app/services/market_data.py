import asyncio
import logging
from typing import Any

import akshare as ak
import pandas as pd

from app.services.cache import cache

logger = logging.getLogger(__name__)


class MarketDataService:
    async def get_stock_realtime(self, code: str) -> dict[str, Any]:
        cached = await cache.get(f"stock:realtime:{code}")
        if cached:
            return cached
        try:
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            row = df[df["代码"] == code]
            if row.empty:
                return {"error": f"Stock {code} not found"}
            r = row.iloc[0]
            result = {
                "code": code,
                "name": str(r.get("名称", "")),
                "price": float(r.get("最新价", 0) or 0),
                "change": float(r.get("涨跌额", 0) or 0),
                "change_pct": float(r.get("涨跌幅", 0) or 0),
                "volume": float(r.get("成交量", 0) or 0),
                "amount": float(r.get("成交额", 0) or 0),
                "high": float(r.get("最高", 0) or 0),
                "low": float(r.get("最低", 0) or 0),
                "open": float(r.get("今开", 0) or 0),
                "prev_close": float(r.get("昨收", 0) or 0),
                "market_cap": float(r.get("总市值", 0) or 0),
                "pe": float(r.get("市盈率-动态", 0) or 0),
                "pb": float(r.get("市净率", 0) or 0),
            }
            await cache.set(f"stock:realtime:{code}", result, ttl=60)
            return result
        except Exception as e:
            logger.error(f"Failed to get realtime data for {code}: {e}")
            return {"error": str(e), "code": code}

    async def get_stock_history(self, code: str, days: int = 120) -> list[dict]:
        cached = await cache.get(f"stock:history:{code}:{days}")
        if cached:
            return cached
        try:
            df = await asyncio.to_thread(
                ak.stock_zh_a_hist, symbol=code, period="daily", adjust="qfq"
            )
            df = df.tail(days)
            records = []
            for _, row in df.iterrows():
                records.append({
                    "date": str(row.get("日期", "")),
                    "open": float(row.get("开盘", 0)),
                    "close": float(row.get("收盘", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                    "volume": float(row.get("成交量", 0)),
                    "amount": float(row.get("成交额", 0)),
                })
            await cache.set(f"stock:history:{code}:{days}", records, ttl=300)
            return records
        except Exception as e:
            logger.error(f"Failed to get history for {code}: {e}")
            return []

    async def get_hot_stocks(self, limit: int = 20) -> list[dict]:
        cached = await cache.get("stock:hot")
        if cached:
            return cached
        try:
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            df = df.dropna(subset=["涨跌幅"])
            df = df.sort_values("成交额", ascending=False).head(limit)
            result = []
            for _, r in df.iterrows():
                result.append({
                    "code": str(r.get("代码", "")),
                    "name": str(r.get("名称", "")),
                    "price": float(r.get("最新价", 0) or 0),
                    "change_pct": float(r.get("涨跌幅", 0) or 0),
                    "amount": float(r.get("成交额", 0) or 0),
                })
            await cache.set("stock:hot", result, ttl=120)
            return result
        except Exception as e:
            logger.error(f"Failed to get hot stocks: {e}")
            return []

    async def get_market_overview(self) -> dict[str, Any]:
        cached = await cache.get("market:overview")
        if cached:
            return cached
        try:
            indices = {
                "000001": "上证指数",
                "399001": "深证成指",
                "399006": "创业板指",
            }
            result = {}
            for idx_code, idx_name in indices.items():
                try:
                    symbol = f"sh{idx_code}" if idx_code.startswith("0") else f"sz{idx_code}"
                    df = await asyncio.to_thread(ak.stock_zh_index_daily, symbol=symbol)
                    if not df.empty:
                        latest = df.iloc[-1]
                        prev = df.iloc[-2] if len(df) > 1 else latest
                        close = float(latest.get("close", 0))
                        prev_close = float(prev.get("close", 0))
                        result[idx_code] = {
                            "name": idx_name,
                            "close": close,
                            "change_pct": round((close - prev_close) / prev_close * 100, 2) if prev_close else 0,
                        }
                except Exception:
                    result[idx_code] = {"name": idx_name, "close": 0, "change_pct": 0}
            await cache.set("market:overview", result, ttl=120)
            return result
        except Exception as e:
            logger.error(f"Failed to get market overview: {e}")
            return {}


market_data_service = MarketDataService()

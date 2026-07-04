"""Market data service — akshare integration.

Provides K-line history, real-time quotes, and stock info.
All data is cached via CacheService to reduce API calls.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketDataService:
    def __init__(self, cache=None):
        self.cache = cache

    def get_kline(
        self,
        stock_code: str,
        period: str = "daily",
        days: int = 250,
    ) -> List[Dict]:
        """Get historical K-line data."""
        cache_key = f"market:kline:{stock_code}:{period}:{days}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            import akshare as ak
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period=period,
                start_date=(datetime.now().replace(day=1).strftime("%Y%m%d")),
                adjust="qfq",
            )
            data = df.tail(days).to_dict(orient="records")
            # Normalize column names
            normalized = []
            for row in data:
                normalized.append({
                    "date": str(row.get("日期", "")),
                    "open": float(row.get("开盘", 0)),
                    "close": float(row.get("收盘", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                    "volume": int(row.get("成交量", 0)),
                    "amount": float(row.get("成交额", 0)),
                    "turnover": float(row.get("换手率", 0)),
                })
            if self.cache:
                self.cache.set(cache_key, normalized, ttl=3600)
            return normalized
        except Exception as e:
            logger.error(f"Failed to fetch kline for {stock_code}: {e}")
            return []

    def get_realtime_quote(self, stock_code: str) -> Dict:
        """Get real-time stock quote."""
        cache_key = f"market:realtime:{stock_code}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == stock_code]
            if row.empty:
                return {}

            row = row.iloc[0]
            data = {
                "stock_code": stock_code,
                "name": str(row.get("名称", "")),
                "latest_price": float(row.get("最新价", 0)),
                "change_pct": float(row.get("涨跌幅", 0)),
                "change_amount": float(row.get("涨跌额", 0)),
                "volume": int(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "open": float(row.get("今开", 0)),
                "prev_close": float(row.get("昨收", 0)),
                "market_cap": float(row.get("总市值", 0)),
                "turnover_rate": float(row.get("换手率", 0)),
                "pe_ratio": float(row.get("市盈率-动态", 0)),
                "timestamp": datetime.now().isoformat(),
            }
            if self.cache:
                self.cache.set(cache_key, data, ttl=30)
            return data
        except Exception as e:
            logger.error(f"Failed to fetch realtime quote for {stock_code}: {e}")
            return {}

    def get_stock_info(self, stock_code: str) -> Dict:
        """Get stock basic information."""
        cache_key = f"market:info:{stock_code}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            import akshare as ak
            df = ak.stock_individual_info_em(symbol=stock_code)
            info = {}
            for _, row in df.iterrows():
                key = str(row.iloc[0])
                val = row.iloc[1]
                info[key] = val

            data = {
                "stock_code": stock_code,
                "name": info.get("股票简称", ""),
                "sector": info.get("行业", ""),
                "market_cap": info.get("总市值", 0),
                "float_market_cap": info.get("流通市值", 0),
                "list_date": info.get("上市时间", ""),
            }
            if self.cache:
                self.cache.set(cache_key, data, ttl=86400)
            return data
        except Exception as e:
            logger.error(f"Failed to fetch stock info for {stock_code}: {e}")
            return {}

    def get_hot_stocks(self, limit: int = 20) -> List[Dict]:
        """Get hot stocks by trading volume."""
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            df = df.nlargest(limit, "成交额")
            result = []
            for _, row in df.iterrows():
                result.append({
                    "stock_code": str(row.get("代码", "")),
                    "name": str(row.get("名称", "")),
                    "latest_price": float(row.get("最新价", 0)),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "amount": float(row.get("成交额", 0)),
                })
            return result
        except Exception as e:
            logger.error(f"Failed to fetch hot stocks: {e}")
            return []

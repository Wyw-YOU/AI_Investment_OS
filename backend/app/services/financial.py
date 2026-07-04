"""Financial data service — financial statements, ratios, dividends."""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class FinancialService:
    def __init__(self, cache=None):
        self.cache = cache

    def get_financial_summary(self, stock_code: str) -> Dict:
        """Get key financial metrics for a stock."""
        cache_key = f"financial:{stock_code}:summary"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            import akshare as ak

            # Main financial indicators
            df = ak.stock_financial_abstract_ths(symbol=stock_code, indicator="按报告期")
            if df.empty:
                return {}

            latest = df.iloc[0]
            data = {
                "stock_code": stock_code,
                "report_date": str(latest.get("报告期", "")),
                "eps": self._safe_float(latest, "基本每股收益"),
                "roe": self._safe_float(latest, "净资产收益率"),
                "revenue": self._safe_float(latest, "营业总收入"),
                "net_profit": self._safe_float(latest, "净利润"),
                "gross_margin": self._safe_float(latest, "销售毛利率"),
                "net_margin": self._safe_float(latest, "销售净利率"),
                "debt_ratio": self._safe_float(latest, "资产负债率"),
            }
            if self.cache:
                self.cache.set(cache_key, data, ttl=86400)
            return data
        except Exception as e:
            logger.error(f"Failed to fetch financial summary for {stock_code}: {e}")
            return self._fallback_financial(stock_code)

    def get_valuation(self, stock_code: str) -> Dict:
        """Get valuation metrics (PE, PB, etc.)."""
        cache_key = f"financial:{stock_code}:valuation"
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
                "pe_ratio": self._safe_float(row, "市盈率-动态"),
                "pb_ratio": self._safe_float(row, "市净率"),
                "ps_ratio": self._safe_float(row, "市销率"),
                "total_mv": self._safe_float(row, "总市值"),
                "circ_mv": self._safe_float(row, "流通市值"),
            }
            if self.cache:
                self.cache.set(cache_key, data, ttl=3600)
            return data
        except Exception as e:
            logger.error(f"Failed to fetch valuation for {stock_code}: {e}")
            return {}

    def get_growth_rates(self, stock_code: str) -> Dict:
        """Calculate revenue and profit growth rates."""
        try:
            import akshare as ak
            df = ak.stock_financial_abstract_ths(symbol=stock_code, indicator="按年度")
            if df is None or len(df) < 2:
                return {"revenue_growth": 0.0, "profit_growth": 0.0}

            latest = df.iloc[0]
            prev = df.iloc[1]
            rev_growth = self._calc_growth(
                self._safe_float(latest, "营业总收入"),
                self._safe_float(prev, "营业总收入"),
            )
            profit_growth = self._calc_growth(
                self._safe_float(latest, "净利润"),
                self._safe_float(prev, "净利润"),
            )
            return {
                "stock_code": stock_code,
                "revenue_growth": rev_growth,
                "profit_growth": profit_growth,
            }
        except Exception as e:
            logger.error(f"Failed to fetch growth rates for {stock_code}: {e}")
            return {"revenue_growth": 0.0, "profit_growth": 0.0}

    @staticmethod
    def _safe_float(row, col, default=0.0):
        try:
            val = row.get(col, default)
            if val is None or str(val).strip() in ("", "--", "nan"):
                return default
            return float(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _calc_growth(current: float, previous: float) -> float:
        if previous == 0:
            return 0.0
        return round((current - previous) / abs(previous), 4)

    @staticmethod
    def _fallback_financial(stock_code: str) -> Dict:
        return {
            "stock_code": stock_code,
            "report_date": "",
            "eps": 0.0,
            "roe": 0.0,
            "revenue": 0.0,
            "net_profit": 0.0,
            "gross_margin": 0.0,
            "net_margin": 0.0,
            "debt_ratio": 0.0,
            "note": "data unavailable, using fallback",
        }

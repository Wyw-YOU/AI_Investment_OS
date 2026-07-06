import logging
from typing import Any

import akshare as ak

from app.services.cache import cache

logger = logging.getLogger(__name__)


class FinancialService:
    async def get_financial_data(self, code: str) -> dict[str, Any]:
        cached = await cache.get(f"financial:{code}")
        if cached:
            return cached
        try:
            result = {"code": code, "metrics": {}, "statements": {}}

            # Key financial indicators
            try:
                df = ak.stock_financial_abstract_ths(symbol=code)
                if not df.empty:
                    latest = df.iloc[0]
                    result["metrics"] = {
                        "roe": self._safe_float(latest, "净资产收益率"),
                        "eps": self._safe_float(latest, "基本每股收益"),
                        "revenue": self._safe_float(latest, "营业总收入"),
                        "net_profit": self._safe_float(latest, "净利润"),
                    }
            except Exception as e:
                logger.warning(f"Financial abstract failed for {code}: {e}")

            # Valuation
            try:
                spot = ak.stock_zh_a_spot_em()
                row = spot[spot["代码"] == code]
                if not row.empty:
                    r = row.iloc[0]
                    result["valuation"] = {
                        "pe": float(r.get("市盈率-动态", 0) or 0),
                        "pb": float(r.get("市净率", 0) or 0),
                        "market_cap": float(r.get("总市值", 0) or 0),
                    }
            except Exception as e:
                logger.warning(f"Valuation fetch failed for {code}: {e}")

            await cache.set(f"financial:{code}", result, ttl=600)
            return result
        except Exception as e:
            logger.error(f"Failed to get financial data for {code}: {e}")
            return {"code": code, "error": str(e)}

    def _safe_float(self, row, col: str) -> float:
        try:
            val = row.get(col, 0)
            return float(val) if val and str(val) != "nan" else 0.0
        except (ValueError, TypeError):
            return 0.0


financial_service = FinancialService()

"""
基本面分析 Agent：分析个股的盈利能力、成长性、估值和财务健康度。
置信度权重：有财务指标(0.3) + 有估值数据(0.3) + 结果完整度(0.3) + 基础分(0.1)
"""

from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_financial_prompt


class FinancialAgent(LLMAgent):
    """基本面分析 Agent，专注于 A 股公司的财务指标和估值分析。"""
    name = "financial"
    description = "a senior equity research analyst specializing in fundamental analysis"

    def build_prompt(self, state: dict) -> str:
        """从 workflow state 中提取财务数据，构建分析 prompt。"""
        return build_financial_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            financial_data=state.get("financial_data", {}),
            market_data=state.get("market_data"),
        )

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """根据数据完整度计算置信度：有财务指标 + 有估值 + 结果字段完整度。"""
        if result.get("parse_error"):
            return 0.1
        fin = state.get("financial_data", {})
        has_metrics = 1.0 if fin.get("metrics") else 0.0
        has_valuation = 1.0 if fin.get("valuation") else 0.0
        result_complete = sum(1 for k in ["profitability", "growth", "valuation", "health"] if result.get(k)) / 4
        return round(0.3 * has_metrics + 0.3 * has_valuation + 0.3 * result_complete + 0.1, 2)

    def _get_expected_output_keys(self) -> list[str]:
        return ["profitability", "growth", "valuation", "health", "summary"]

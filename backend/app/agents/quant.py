"""
量化评分 Agent：基于多因子模型（估值/成长/质量/动量/情绪）计算综合评分。
位于 workflow 的 risk 之后，将风险评估结果也纳入评分依据。
"""

from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_quant_prompt


class QuantAgent(LLMAgent):
    """量化评分 Agent，输出 0-100 综合评分和 buy/hold/sell 建议。"""
    name = "quant"
    description = "a quantitative analyst specializing in multi-factor scoring models"

    def build_prompt(self, state: dict) -> str:
        """将风险评估结果合并到 agent_outputs 中一起送入 prompt。"""
        agent_outputs = state.get("agent_outputs", {})
        risk = state.get("risk_assessment", {})
        if risk:
            agent_outputs["risk"] = risk
        return build_quant_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            agent_outputs=agent_outputs,
        )

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        if result.get("parse_error"):
            return 0.1
        factors = result.get("factors", {})
        factor_count = len(factors)
        has_composite = 1.0 if result.get("composite_score") is not None else 0.0
        return round(min(1.0, factor_count / 5 * 0.7 + has_composite * 0.3), 2)

    def _get_expected_output_keys(self) -> list[str]:
        return ["factors", "composite_score", "rating", "summary"]

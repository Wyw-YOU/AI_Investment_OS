"""
报告生成 Agent：workflow 最后一步，综合所有分析结果生成最终投资报告。
输出包含：执行摘要、投资建议、目标价区间、核心发现、综合评分。
"""

from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_report_prompt


class ReportAgent(LLMAgent):
    """最终报告生成 Agent，作为 workflow 的最后节点输出完整投资报告。"""
    name = "report"
    description = "the chief investment strategist producing the final investment report"

    def build_prompt(self, state: dict) -> str:
        """提取所有 agent 分析结果 + 风险评估 + 量化评分，构建报告 prompt。"""
        agent_outputs = state.get("agent_outputs", {})
        risk = state.get("risk_assessment", {})
        quant = state.get("quant_score", {})
        return build_report_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            agent_outputs=agent_outputs,
            risk_assessment=risk,
            quant_score=quant,
        )

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        if result.get("parse_error"):
            return 0.1
        has_recommendation = 1.0 if result.get("recommendation") else 0.0
        has_findings = 1.0 if result.get("key_findings") else 0.0
        has_summary = 1.0 if result.get("executive_summary") else 0.0
        return round(0.4 * has_recommendation + 0.3 * has_findings + 0.3 * has_summary, 2)

    def _get_expected_output_keys(self) -> list[str]:
        return ["executive_summary", "recommendation", "key_findings", "overall_score"]

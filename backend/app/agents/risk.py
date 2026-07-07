"""
风险评估 Agent：综合所有 agent 的分析结果，输出整体风险评级。
位于 workflow 的 merge 之后，可访问所有并行 agent 的输出。
置信度权重：分析来源数量(0.5) + 有风险评分(0.3) + 基础分(0.2)
"""

from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_risk_prompt


class RiskAgent(LLMAgent):
    """风险评估 Agent，综合多维度分析输出风险等级和仓位建议。"""
    name = "risk"
    description = "a senior risk management analyst"

    def build_prompt(self, state: dict) -> str:
        """合并 agent_outputs 和 parallel_results，确保可访问所有分析结果。"""
        agent_outputs = state.get("agent_outputs", {})
        # Include parallel results if available
        parallel = state.get("parallel_results", [])
        for item in parallel:
            if isinstance(item, dict) and "agent_name" in item:
                agent_outputs[item["agent_name"]] = item
        return build_risk_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            agent_outputs=agent_outputs,
        )

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        if result.get("parse_error"):
            return 0.1
        agent_count = len(state.get("agent_outputs", {}))
        data_factor = min(1.0, agent_count / 3)
        has_score = 1.0 if result.get("risk_score") is not None else 0.0
        return round(0.5 * data_factor + 0.3 * has_score + 0.2, 2)

    def _get_expected_output_keys(self) -> list[str]:
        return ["overall_risk", "risk_score", "risk_factors", "summary"]

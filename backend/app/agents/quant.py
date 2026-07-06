from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_quant_prompt


class QuantAgent(LLMAgent):
    name = "quant"
    description = "a quantitative analyst specializing in multi-factor scoring models"

    def build_prompt(self, state: dict) -> str:
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

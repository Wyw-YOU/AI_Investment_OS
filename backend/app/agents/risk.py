from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_risk_prompt


class RiskAgent(LLMAgent):
    name = "risk"
    description = "a senior risk management analyst"

    def build_prompt(self, state: dict) -> str:
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

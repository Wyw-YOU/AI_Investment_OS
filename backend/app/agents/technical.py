from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_technical_prompt


class TechnicalAgent(LLMAgent):
    name = "technical"
    description = "a professional technical analyst specializing in chart patterns and indicators"

    def build_prompt(self, state: dict) -> str:
        return build_technical_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            price_history=state.get("price_history", []),
            indicators=state.get("indicators", {}),
        )

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        if result.get("parse_error"):
            return 0.1
        history_len = len(state.get("price_history", []))
        data_factor = min(1.0, history_len / 60)
        has_indicators = 1.0 if state.get("indicators") else 0.0
        has_signal = 1.0 if result.get("signal") else 0.0
        return round(0.4 * data_factor + 0.3 * has_indicators + 0.2 * has_signal + 0.1, 2)

    def _get_expected_output_keys(self) -> list[str]:
        return ["trend", "signal", "momentum", "summary"]

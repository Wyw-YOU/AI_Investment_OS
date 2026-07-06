from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_macro_prompt


class MacroAgent(LLMAgent):
    name = "macro"
    description = "a macro-economic analyst covering the Chinese market environment"

    def build_prompt(self, state: dict) -> str:
        return build_macro_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            market_data=state.get("market_data", {}),
        )

    def _get_expected_output_keys(self) -> list[str]:
        return ["market_sentiment", "sector_outlook", "summary"]

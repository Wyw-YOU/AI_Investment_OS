from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_financial_prompt


class FinancialAgent(LLMAgent):
    name = "financial"
    description = "a senior equity research analyst specializing in fundamental analysis"

    def build_prompt(self, state: dict) -> str:
        return build_financial_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            financial_data=state.get("financial_data", {}),
            market_data=state.get("market_data"),
        )

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        if result.get("parse_error"):
            return 0.1
        fin = state.get("financial_data", {})
        has_metrics = 1.0 if fin.get("metrics") else 0.0
        has_valuation = 1.0 if fin.get("valuation") else 0.0
        result_complete = sum(1 for k in ["profitability", "growth", "valuation", "health"] if result.get(k)) / 4
        return round(0.3 * has_metrics + 0.3 * has_valuation + 0.3 * result_complete + 0.1, 2)

    def _get_expected_output_keys(self) -> list[str]:
        return ["profitability", "growth", "valuation", "health", "summary"]

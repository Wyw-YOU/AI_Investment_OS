"""
宏观分析 Agent：评估宏观经济环境对该个股的影响。
输入市场行情数据，输出市场情绪、政策环境、流动性等宏观因子判断。
"""

from app.agents.base import LLMAgent
from app.agents.models import AgentOutput
from app.agents.prompts import build_macro_prompt


class MacroAgent(LLMAgent):
    """宏观环境分析 Agent，专注于中国 A 股市场的宏观因子评估。"""
    name = "macro"
    description = "a macro-economic analyst covering the Chinese market environment"

    def build_prompt(self, state: dict) -> str:
        """从 workflow state 中提取市场数据，构建宏观分析 prompt。"""
        return build_macro_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            market_data=state.get("market_data", {}),
        )

    def _get_expected_output_keys(self) -> list[str]:
        return ["market_sentiment", "sector_outlook", "summary"]

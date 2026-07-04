"""InvestmentState — shared state for the multi-agent workflow.

All agents read from and write to this state. Agents never communicate
directly; they interact only through this state object.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class InvestmentState:
    user_id: str = ""

    stock_pool: list[str] = field(default_factory=list)
    current_stock: str = ""

    market_data: dict = field(default_factory=dict)
    financial_data: dict = field(default_factory=dict)
    news_data: list = field(default_factory=list)
    indicators: dict = field(default_factory=dict)

    agent_outputs: dict[str, dict] = field(default_factory=dict)
    agent_confidence: dict[str, float] = field(default_factory=dict)

    risk_profile: dict = field(default_factory=dict)

    portfolio: dict = field(default_factory=dict)
    candidate_pool: list[str] = field(default_factory=list)

    final_report: dict = field(default_factory=dict)

    events: list = field(default_factory=list)

    decision: str = ""  # buy | sell | hold | watch

    def set_agent_output(self, agent_name: str, result: dict):
        self.agent_outputs[agent_name] = result.get("output", {})
        self.agent_confidence[agent_name] = result.get("confidence", 0.0)

    def get_agent_output(self, agent_name: str) -> dict:
        return self.agent_outputs.get(agent_name, {})

    def get_agent_confidence(self, agent_name: str) -> float:
        return self.agent_confidence.get(agent_name, 0.0)

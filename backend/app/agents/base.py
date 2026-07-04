"""BaseAgent — abstract base class and Agent Registry.

Every agent inherits BaseAgent and implements run().
All agents return a standardized dict: output + confidence + evidence + reasoning.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from app.agents.state import InvestmentState

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    def run(self, state: InvestmentState) -> Dict[str, Any]:
        """Execute the agent with the given state and return standardized result.

        Returns:
            {
                "output": dict,
                "confidence": float (0.0-1.0),
                "evidence": list[str],
                "reasoning": str,
            }
        """
        ...

    def _build_result(
        self,
        output: dict,
        confidence: float,
        evidence: list[str],
        reasoning: str,
    ) -> dict:
        return {
            "output": output,
            "confidence": max(0.0, min(1.0, confidence)),
            "evidence": evidence if evidence else ["no evidence provided"],
            "reasoning": reasoning if reasoning else "no reasoning provided",
        }

    def _log_run(self, state: InvestmentState, result: dict):
        logger.info(
            f"Agent[{self.name}] stock={state.current_stock} "
            f"confidence={result['confidence']:.2f}"
        )


AGENT_REGISTRY: dict[str, BaseAgent] = {}


def register_agent(agent: BaseAgent):
    AGENT_REGISTRY[agent.name] = agent
    return agent


def get_agent(name: str) -> BaseAgent:
    if name not in AGENT_REGISTRY:
        raise KeyError(f"Agent '{name}' not found in registry")
    return AGENT_REGISTRY[name]


def list_agents() -> list[str]:
    return list(AGENT_REGISTRY.keys())

"""
Investment Analysis System - Risk Agent

Specializes in risk assessment by aggregating signals from other agents
and producing a unified risk profile with position sizing recommendations.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from base_agent import LLMAgent
from models import AgentOutput
from prompts import build_risk_prompt


class RiskAgent(LLMAgent):
    """
    Assesses investment risks by synthesizing outputs from the News,
    Financial, and Technical agents.

    This agent is designed to run AFTER the parallel analysis agents
    have completed, using their outputs as additional context.
    """

    name = "risk_agent"
    description = "Expert in risk assessment, risk management, and portfolio risk"

    def __init__(self, **kwargs: Any) -> None:
        # Conservative, precise temperature for risk analysis
        kwargs.setdefault("temperature", 0.2)
        super().__init__(**kwargs)

    # --- Prompt construction ---

    def build_prompt(self, state: dict) -> str:
        return build_risk_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            agent_outputs=state.get("agent_outputs", {}),
            market_data=state.get("market_data", {}),
            risk_tolerance=state.get("risk_tolerance", "moderate"),
            query=state.get("query", ""),
        )

    # --- Validation ---

    def _get_expected_output_keys(self) -> List[str]:
        return ["overall_risk", "risk_score", "risk_factors", "worst_case", "mitigation"]

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """
        Risk agent confidence depends on:
        1. LLM-provided confidence
        2. How many upstream agents contributed data
        3. Average confidence of upstream agents
        """
        llm_conf = 0.5
        if "confidence" in result:
            try:
                llm_conf = float(result["confidence"])
            except (TypeError, ValueError):
                pass

        # Upstream agent quality
        agent_outputs = state.get("agent_outputs", {})
        if agent_outputs:
            upstream_confs = []
            for output in agent_outputs.values():
                if isinstance(output, dict):
                    upstream_confs.append(output.get("confidence", 0.0))
                elif hasattr(output, "confidence"):
                    upstream_confs.append(output.confidence)
            avg_upstream = sum(upstream_confs) / len(upstream_confs) if upstream_confs else 0.0
            coverage = len(agent_outputs) / 3  # Expect 3 upstream agents (news, financial, technical)
        else:
            avg_upstream = 0.0
            coverage = 0.0

        return max(0.0, min(1.0, llm_conf * 0.4 + avg_upstream * 0.3 + coverage * 0.3))

    # --- Risk signal aggregation ---

    def _aggregate_risk_signals(self, agent_outputs: dict) -> Dict[str, Any]:
        """
        Collect and summarize risk-relevant signals from upstream agents.
        Used for logging and metadata (the LLM prompt also includes these).
        """
        signals: Dict[str, Any] = {
            "news_sentiment": None,
            "technical_action": None,
            "financial_health_score": None,
            "valuation_assessment": None,
            "agent_count": len(agent_outputs),
            "agent_statuses": {},
        }

        for name, output in agent_outputs.items():
            if isinstance(output, dict):
                result = output.get("result", {})
                status = output.get("status", "unknown")
            elif hasattr(output, "result"):
                result = output.result
                status = getattr(output, "status", "unknown")
            else:
                result = {}
                status = "unknown"

            signals["agent_statuses"][name] = status

            if name == "news_agent":
                signals["news_sentiment"] = result.get("sentiment")
            elif name == "technical_agent":
                signals["technical_action"] = result.get("signals", {}).get("action")
            elif name == "financial_agent":
                signals["financial_health_score"] = result.get("health", {}).get("health_score")
                signals["valuation_assessment"] = result.get("valuation", {}).get("assessment")

        return signals

    # --- Run with enhanced context ---

    def run(self, state: dict) -> AgentOutput:
        """
        Execute risk assessment. Augments state with aggregated risk
        signals from upstream agents before building the prompt.
        """
        agent_outputs = state.get("agent_outputs", {})
        risk_signals = self._aggregate_risk_signals(agent_outputs)

        # Build enhanced state with risk signal metadata
        enhanced_state = {
            **state,
            "_risk_signals_summary": risk_signals,
        }

        output = super().run(enhanced_state)

        # Enrich metadata with risk signal details
        output.metadata["risk_signals"] = risk_signals
        return output

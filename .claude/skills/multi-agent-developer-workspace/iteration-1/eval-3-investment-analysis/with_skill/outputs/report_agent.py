"""
Investment Analysis System - Report Agent

Synthesizes all agent outputs into a final investment report with
recommendation, price target, risk-reward assessment, and action items.
"""

from __future__ import annotations

from typing import Any, Dict, List

from base_agent import LLMAgent
from models import AgentOutput
from prompts import build_report_prompt


class ReportAgent(LLMAgent):
    """
    Synthesizes outputs from all upstream agents into a final
    investment report with clear buy/hold/sell recommendation.

    This agent runs LAST in the pipeline, after the Risk Agent.
    """

    name = "report_agent"
    description = "Expert in investment report writing and multi-agent analysis synthesis"

    def __init__(self, **kwargs: Any) -> None:
        # Moderate temperature for readable but consistent prose
        kwargs.setdefault("temperature", 0.4)
        super().__init__(**kwargs)

    # --- Prompt construction ---

    def build_prompt(self, state: dict) -> str:
        return build_report_prompt(
            stock_code=state.get("stock_code", ""),
            stock_name=state.get("stock_name", ""),
            agent_outputs=state.get("agent_outputs", {}),
            risk_assessment=state.get("risk_assessment", {}),
            market_data=state.get("market_data", {}),
            time_horizon=state.get("time_horizon", "12 months"),
            query=state.get("query", ""),
        )

    # --- Validation ---

    def _get_expected_output_keys(self) -> List[str]:
        return [
            "executive_summary",
            "recommendation",
            "confidence",
            "price_target",
            "key_findings",
            "risk_reward",
            "action_items",
        ]

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """
        Report confidence is the weighted average of all contributing
        agent confidences, adjusted for result completeness.
        """
        # Weighted average of upstream confidences
        agent_outputs = state.get("agent_outputs", {})
        if agent_outputs:
            confidences = []
            for output in agent_outputs.values():
                if isinstance(output, dict):
                    confidences.append(output.get("confidence", 0.0))
                elif hasattr(output, "confidence"):
                    confidences.append(output.confidence)
            avg_upstream = sum(confidences) / len(confidences) if confidences else 0.5
        else:
            avg_upstream = 0.5

        # Include risk assessment confidence
        risk_assess = state.get("risk_assessment", {})
        risk_conf = 0.5
        if isinstance(risk_assess, dict):
            risk_conf = risk_assess.get("confidence", 0.5)

        # Result completeness
        expected = self._get_expected_output_keys()
        present = sum(1 for k in expected if k in result and result[k])
        completeness = present / len(expected) if expected else 0.5

        # Weighted combination
        return max(0.0, min(
            1.0,
            avg_upstream * 0.35 + risk_conf * 0.25 + completeness * 0.4
        ))

    def _extract_citations(self, result: dict, state: dict) -> List[str]:
        """
        Aggregate citations from all upstream agents plus the report result.
        """
        citations = super()._extract_citations(result, state)

        # Pull citations from all agent outputs
        for output in state.get("agent_outputs", {}).values():
            if isinstance(output, dict):
                for c in output.get("citations", []):
                    if c not in citations:
                        citations.append(c)
            elif hasattr(output, "citations"):
                for c in output.citations:
                    if c not in citations:
                        citations.append(c)

        return citations

    # --- Run ---

    def run(self, state: dict) -> AgentOutput:
        """
        Generate the final investment report.

        Validates that at least some upstream agent outputs exist before
        calling the LLM; falls back gracefully if not.
        """
        agent_outputs = state.get("agent_outputs", {})
        if not agent_outputs:
            self.logger.warning(
                "No upstream agent outputs available for %s; generating minimal report.",
                state.get("stock_code"),
            )
            return self._create_output(
                result={
                    "executive_summary": (
                        "Insufficient analysis data to generate a comprehensive report. "
                        "Please ensure upstream agents have completed successfully."
                    ),
                    "recommendation": "hold",
                    "confidence": 0.1,
                    "price_target": {"target": None, "time_horizon": "N/A", "upside": 0.0},
                    "key_findings": {},
                    "risk_reward": {"risk_score": 50, "reward_potential": 0.0, "risk_reward_ratio": 0.0},
                    "action_items": ["Gather more data before making investment decisions"],
                    "sources": [],
                    "disclaimer": "This is AI-generated analysis, not financial advice.",
                },
                confidence=0.1,
                citations=[],
                metadata={"data_available": False},
            )

        return super().run(state)

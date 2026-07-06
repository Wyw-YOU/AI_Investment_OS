"""
QualityAnalyzerAgent - Assesses research rigor, novelty, and overall quality.

This agent takes extracted paper metadata and performs a critical quality assessment,
evaluating novelty level, methodological rigor, statistical soundness, reproducibility,
and potential biases. It provides calibrated scores suitable for academic evaluation.

LangGraph Node Signature:
    Input:  SubgraphState with 'extraction' populated
    Output: SubgraphState with 'quality' populated as QualityAssessment dict
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from academic_research_system.agents.prompts import (
    QUALITY_ANALYZER_SYSTEM,
    QUALITY_ANALYZER_HUMAN,
)

logger = logging.getLogger(__name__)


class QualityAnalyzerAgent:
    """
    Agent for evaluating the quality and novelty of academic research.

    Responsibilities:
    - Classify novelty level (groundbreaking through duplicative)
    - Evaluate methodological rigor and statistical practices
    - Assess reproducibility based on transparency and completeness
    - Identify potential biases (selection, confirmation, publication, etc.)
    - Detect validity threats (internal and external)
    - Provide calibrated quality scores across multiple dimensions
    """

    def __init__(self, llm: BaseChatModel):
        """
        Args:
            llm: Language model instance.
        """
        self.llm = llm
        self.name = "QualityAnalyzerAgent"

    async def analyze(self, extraction: dict[str, Any]) -> dict[str, Any]:
        """
        Assess quality and novelty from extracted paper metadata.

        Args:
            extraction: Dictionary of extracted paper metadata (from PaperExtractorAgent).

        Returns:
            Dictionary conforming to the QualityAssessment schema.
        """
        logger.info("[%s] Analyzing quality of: '%s'", self.name, extraction.get("title", "Unknown"))

        # Build the prompt with extracted data
        prompt_data = {
            "title": extraction.get("title", "N/A"),
            "authors": ", ".join(
                a.get("name", "Unknown") if isinstance(a, dict) else str(a)
                for a in extraction.get("authors", [])
            ),
            "year": extraction.get("year", "N/A"),
            "journal_or_venue": extraction.get("journal_or_venue", "N/A"),
            "abstract": extraction.get("abstract", "N/A"),
            "methodology": extraction.get("methodology", "N/A"),
            "methodology_type": extraction.get("methodology_type", "unknown"),
            "research_questions": json.dumps(extraction.get("research_questions", []), ensure_ascii=False),
            "key_findings": json.dumps(extraction.get("key_findings", []), ensure_ascii=False),
            "limitations": json.dumps(extraction.get("limitations", []), ensure_ascii=False),
            "data_sources": json.dumps(extraction.get("data_sources", []), ensure_ascii=False),
            "sample_size": extraction.get("sample_size", "N/A"),
            "statistical_methods": json.dumps(extraction.get("statistical_methods", []), ensure_ascii=False),
            "references_count": extraction.get("references_count", "N/A"),
        }

        messages = [
            SystemMessage(content=QUALITY_ANALYZER_SYSTEM),
            HumanMessage(content=QUALITY_ANALYZER_HUMAN.format(**prompt_data)),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            result = self._parse_response(response.content)
            logger.info(
                "[%s] Quality assessment complete: novelty=%s, rigor=%s, overall=%.1f",
                self.name,
                result.get("novelty_level", "?"),
                result.get("rigor_level", "?"),
                result.get("overall_quality_score", 0.0),
            )
            return result
        except Exception as e:
            logger.error("[%s] Quality analysis failed: %s", self.name, str(e))
            raise

    def _parse_response(self, content: str) -> dict[str, Any]:
        """Parse and validate the quality assessment JSON response."""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("[%s] Failed to parse JSON: %s", self.name, e)
            raise ValueError(f"LLM returned invalid JSON: {e}") from e

        # Validate and clamp scores to [0, 10]
        score_fields = [
            "significance_score", "methodology_score", "clarity_score",
            "reproducibility_score", "impact_potential_score", "overall_quality_score",
        ]
        for sf in score_fields:
            try:
                result[sf] = max(0.0, min(10.0, float(result.get(sf, 0.0))))
            except (ValueError, TypeError):
                result[sf] = 0.0

        # Validate enum fields
        valid_novelty = {"groundbreaking", "highly_novel", "moderately_novel", "incremental", "duplicative"}
        if result.get("novelty_level") not in valid_novelty:
            result["novelty_level"] = "incremental"

        valid_rigor = {"exemplary", "strong", "adequate", "weak", "poor"}
        if result.get("rigor_level") not in valid_rigor:
            result["rigor_level"] = "adequate"

        # Ensure list fields
        for lf in ["strengths", "weaknesses", "ethical_considerations", "validity_threats"]:
            if not isinstance(result.get(lf), list):
                result[lf] = []

        # Ensure string fields
        for sf in ["novelty_rationale", "rigor_rationale", "bias_assessment"]:
            if not isinstance(result.get(sf), str):
                result[sf] = ""

        return result


async def quality_analyzer_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node wrapper for the QualityAnalyzerAgent.

    Reads 'extraction' from SubgraphState, runs quality analysis,
    and writes 'quality' back to state.
    """
    agent = QualityAnalyzerAgent(llm=state.get("_llm"))
    extraction = state.get("extraction")

    if not extraction:
        return {"quality": None, "error": "No extraction data provided", "stage": "error"}

    try:
        quality = await agent.analyze(extraction)
        return {"quality": quality, "stage": "quality_assessed", "error": None}
    except Exception as e:
        return {"quality": None, "error": f"Quality analysis failed: {e}", "stage": "error"}

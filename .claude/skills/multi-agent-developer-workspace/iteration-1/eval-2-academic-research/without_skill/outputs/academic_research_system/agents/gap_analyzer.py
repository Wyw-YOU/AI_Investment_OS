"""
GapAnalyzerAgent - Identifies research gaps and future directions.

This agent operates at the corpus level, analyzing multiple papers together to identify
gaps in the existing literature, under-explored areas, methodological weaknesses that
limit the field's progress, and promising future research directions. It categorizes
gaps as methodological, theoretical, or empirical.

LangGraph Node Signature:
    Input:  AcademicResearchState with 'processed_papers' populated
    Output: AcademicResearchState with 'gap_analysis' populated as GapAnalysis dict
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from academic_research_system.agents.prompts import (
    GAP_ANALYZER_SYSTEM,
    GAP_ANALYZER_HUMAN,
)

logger = logging.getLogger(__name__)


class GapAnalyzerAgent:
    """
    Agent for identifying research gaps and future directions across a paper corpus.

    Responsibilities:
    - Synthesize patterns across multiple papers to identify under-explored areas
    - Distinguish methodological, empirical, and theoretical gaps
    - Evaluate feasibility of proposed research directions
    - Prioritize research opportunities by impact and feasibility
    - Connect gaps to specific evidence from the analyzed papers
    """

    def __init__(self, llm: BaseChatModel):
        """
        Args:
            llm: Language model instance.
        """
        self.llm = llm
        self.name = "GapAnalyzerAgent"

    async def analyze_gaps(
        self,
        processed_papers: list[dict[str, Any]],
        research_topic: str,
        review_focus: str,
        user_instructions: str = "",
    ) -> dict[str, Any]:
        """
        Analyze research gaps across the entire paper corpus.

        Args:
            processed_papers: List of fully processed paper dicts (extraction + quality + summary).
            research_topic: The overarching research topic.
            review_focus: Specific focus for gap analysis.
            user_instructions: Additional user-provided analysis instructions.

        Returns:
            Dictionary conforming to the GapAnalysis schema.
        """
        logger.info("[%s] Analyzing gaps across %d papers on '%s'", self.name, len(processed_papers), research_topic)

        # Build a condensed text representation of all papers
        papers_text = self._build_papers_text(processed_papers)

        messages = [
            SystemMessage(content=GAP_ANALYZER_SYSTEM),
            HumanMessage(content=GAP_ANALYZER_HUMAN.format(
                research_topic=research_topic,
                papers_text=papers_text,
                review_focus=review_focus,
                user_instructions=user_instructions or "No additional instructions.",
            )),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            result = self._parse_response(response.content)
            logger.info(
                "[%s] Gap analysis complete: %d gaps, %d future directions",
                self.name,
                len(result.get("research_gaps", [])),
                len(result.get("future_directions", [])),
            )
            return result
        except Exception as e:
            logger.error("[%s] Gap analysis failed: %s", self.name, str(e))
            raise

    def _build_papers_text(self, processed_papers: list[dict[str, Any]]) -> str:
        """Build a condensed text representation of all processed papers."""
        parts = []
        for i, paper in enumerate(processed_papers, 1):
            extraction = paper.get("extraction", {})
            quality = paper.get("quality", {})
            summary = paper.get("summary", {})

            part = f"""
--- Paper {i} ---
Title: {extraction.get('title', 'Unknown')}
Authors: {', '.join(a.get('name', '') if isinstance(a, dict) else str(a) for a in extraction.get('authors', []))}
Year: {extraction.get('year', 'N/A')}
Methodology: {extraction.get('methodology', 'N/A')}
Methodology Type: {extraction.get('methodology_type', 'unknown')}
Research Questions: {'; '.join(extraction.get('research_questions', []))}
Key Findings: {'; '.join(extraction.get('key_findings', []))}
Limitations: {'; '.join(extraction.get('limitations', []))}
Sample Size: {extraction.get('sample_size', 'N/A')}
Quality Scores - Novelty: {quality.get('novelty_level', '?')}, Rigor: {quality.get('rigor_level', '?')}, Overall: {quality.get('overall_quality_score', '?')}/10
Strengths: {'; '.join(quality.get('strengths', []))}
Weaknesses: {'; '.join(quality.get('weaknesses', []))}
One-sentence summary: {summary.get('one_sentence_summary', 'N/A')}
Key Contributions: {'; '.join(summary.get('key_contributions', []))}
"""
            parts.append(part)

        return "\n".join(parts)

    def _parse_response(self, content: str) -> dict[str, Any]:
        """Parse and validate the gap analysis JSON response."""
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

        # Validate research_gaps structure
        if not isinstance(result.get("research_gaps"), list):
            result["research_gaps"] = []
        for gap in result["research_gaps"]:
            if not isinstance(gap, dict):
                continue
            gap.setdefault("gap_title", "")
            gap.setdefault("gap_description", "")
            gap.setdefault("supporting_evidence", [])
            gap.setdefault("papers_evidencing", [])
            gap.setdefault("potential_impact", "")
            gap.setdefault("suggested_approach", "")
            gap.setdefault("estimated_feasibility", "medium")
            gap.setdefault("priority", "medium")
            gap.setdefault("related_keywords", [])

        # Validate future_directions structure
        if not isinstance(result.get("future_directions"), list):
            result["future_directions"] = []
        for fd in result["future_directions"]:
            if not isinstance(fd, dict):
                continue
            fd.setdefault("title", "")
            fd.setdefault("description", "")
            fd.setdefault("rationale", "")
            fd.setdefault("suggested_methodology", "")
            fd.setdefault("expected_challenges", [])
            fd.setdefault("potential_contribution", "")
            fd.setdefault("timeframe", "medium-term")
            fd.setdefault("required_expertise", "")

        # Validate list fields
        for lf in ["overarching_themes", "methodology_gaps", "theoretical_gaps", "empirical_gaps"]:
            if not isinstance(result.get(lf), list):
                result[lf] = []

        return result


async def gap_analyzer_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node wrapper for the GapAnalyzerAgent.

    Reads 'processed_papers', 'research_topic', 'review_focus' from AcademicResearchState,
    runs gap analysis, and writes 'gap_analysis' back to state.
    """
    agent = GapAnalyzerAgent(llm=state.get("_llm") or state.get("config", {}).get("llm"))
    processed_papers = state.get("processed_papers", [])
    research_topic = state.get("research_topic", "Academic Research")
    review_focus = state.get("review_focus", "General analysis")
    user_instructions = state.get("user_instructions", "")

    if not processed_papers:
        return {
            "gap_analysis": None,
            "errors": state.get("errors", []) + ["No processed papers available for gap analysis"],
            "current_step": "gap_analysis_failed",
        }

    try:
        gap_analysis = await agent.analyze_gaps(
            processed_papers=processed_papers,
            research_topic=research_topic,
            review_focus=review_focus,
            user_instructions=user_instructions,
        )
        return {
            "gap_analysis": gap_analysis,
            "current_step": "gap_analysis_complete",
            "processing_log": state.get("processing_log", []) + ["Gap analysis completed successfully"],
        }
    except Exception as e:
        return {
            "gap_analysis": None,
            "errors": state.get("errors", []) + [f"Gap analysis failed: {e}"],
            "current_step": "gap_analysis_failed",
        }

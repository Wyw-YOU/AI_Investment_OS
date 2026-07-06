"""
LiteratureReviewAgent - Synthesizes multiple papers into a coherent literature review.

This agent operates at the corpus level, taking all processed papers and their analyses
to produce a publication-quality literature review with thematic analysis, methodology
comparison, findings synthesis, and a research agenda.

LangGraph Node Signature:
    Input:  AcademicResearchState with 'processed_papers' and 'gap_analysis' populated
    Output: AcademicResearchState with 'literature_review' populated as LiteratureReview dict
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from academic_research_system.agents.prompts import (
    LIT_REVIEW_SYSTEM,
    LIT_REVIEW_HUMAN,
)

logger = logging.getLogger(__name__)


class LiteratureReviewAgent:
    """
    Agent for synthesizing academic papers into a comprehensive literature review.

    Responsibilities:
    - Organize findings thematically rather than paper-by-paper
    - Identify points of agreement and contradiction across studies
    - Evaluate the collective strength of evidence for key claims
    - Construct coherent narratives that build toward clear conclusions
    - Compare methodologies and discuss their implications for evidence quality
    - Generate a research agenda based on identified gaps
    - Produce publication-quality academic prose with proper citations
    """

    def __init__(self, llm: BaseChatModel):
        """
        Args:
            llm: Language model instance.
        """
        self.llm = llm
        self.name = "LiteratureReviewAgent"

    async def synthesize(
        self,
        processed_papers: list[dict[str, Any]],
        research_topic: str,
        review_focus: str,
        gap_analysis: dict[str, Any] | None = None,
        user_instructions: str = "",
    ) -> dict[str, Any]:
        """
        Synthesize multiple papers into a comprehensive literature review.

        Args:
            processed_papers: List of fully processed paper dicts.
            research_topic: The overarching research topic.
            review_focus: Specific focus for the literature review.
            gap_analysis: Gap analysis results from GapAnalyzerAgent.
            user_instructions: Additional user-provided instructions.

        Returns:
            Dictionary conforming to the LiteratureReview schema.
        """
        logger.info("[%s] Synthesizing %d papers into literature review on '%s'",
                    self.name, len(processed_papers), research_topic)

        papers_analyses = self._build_papers_analyses(processed_papers)
        quality_assessments = self._build_quality_assessments(processed_papers)
        gap_analysis_text = self._build_gap_analysis_text(gap_analysis)

        messages = [
            SystemMessage(content=LIT_REVIEW_SYSTEM),
            HumanMessage(content=LIT_REVIEW_HUMAN.format(
                research_topic=research_topic,
                review_focus=review_focus,
                papers_analyses=papers_analyses,
                quality_assessments=quality_assessments,
                gap_analysis=gap_analysis_text,
                user_instructions=user_instructions or "No additional instructions.",
            )),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            result = self._parse_response(response.content)
            logger.info("[%s] Literature review generated: '%s'", self.name, result.get("title", "Untitled"))
            return result
        except Exception as e:
            logger.error("[%s] Literature review synthesis failed: %s", self.name, str(e))
            raise

    def _build_papers_analyses(self, processed_papers: list[dict[str, Any]]) -> str:
        """Build detailed analysis text for each paper."""
        parts = []
        for i, paper in enumerate(processed_papers, 1):
            extraction = paper.get("extraction", {})
            summary = paper.get("summary", {})

            authors = ", ".join(
                a.get("name", "Unknown") if isinstance(a, dict) else str(a)
                for a in extraction.get("authors", [])
            )

            part = f"""
=== Paper {i}: {extraction.get('title', 'Unknown')} ===
Authors: {authors} ({extraction.get('year', 'N/A')})
Journal/Venue: {extraction.get('journal_or_venue', 'N/A')}
Abstract: {extraction.get('abstract', 'N/A')}
Methodology: {extraction.get('methodology', 'N/A')}
Methodology Type: {extraction.get('methodology_type', 'unknown')}
Research Questions: {'; '.join(extraction.get('research_questions', []))}
Key Findings: {'; '.join(extraction.get('key_findings', []))}
Limitations: {'; '.join(extraction.get('limitations', []))}
Conclusion: {extraction.get('conclusion', 'N/A')}
Summary: {summary.get('detailed_summary', 'N/A')}
Key Contributions: {'; '.join(summary.get('key_contributions', []))}
"""
            parts.append(part)
        return "\n".join(parts)

    def _build_quality_assessments(self, processed_papers: list[dict[str, Any]]) -> str:
        """Build quality assessment summary for each paper."""
        parts = []
        for i, paper in enumerate(processed_papers, 1):
            quality = paper.get("quality", {})
            extraction = paper.get("extraction", {})

            part = f"""
Paper {i} - {extraction.get('title', 'Unknown')}:
  Novelty: {quality.get('novelty_level', '?')} - {quality.get('novelty_rationale', 'N/A')}
  Rigor: {quality.get('rigor_level', '?')} - {quality.get('rigor_rationale', 'N/A')}
  Significance: {quality.get('significance_score', '?')}/10
  Methodology Score: {quality.get('methodology_score', '?')}/10
  Reproducibility: {quality.get('reproducibility_score', '?')}/10
  Impact Potential: {quality.get('impact_potential_score', '?')}/10
  Overall: {quality.get('overall_quality_score', '?')}/10
  Strengths: {'; '.join(quality.get('strengths', []))}
  Weaknesses: {'; '.join(quality.get('weaknesses', []))}
  Bias Assessment: {quality.get('bias_assessment', 'N/A')}
"""
            parts.append(part)
        return "\n".join(parts)

    def _build_gap_analysis_text(self, gap_analysis: dict[str, Any] | None) -> str:
        """Build gap analysis text for the literature review prompt."""
        if not gap_analysis:
            return "No gap analysis available."

        parts = []

        gaps = gap_analysis.get("research_gaps", [])
        if gaps:
            parts.append("RESEARCH GAPS IDENTIFIED:")
            for i, gap in enumerate(gaps, 1):
                parts.append(f"  {i}. {gap.get('gap_title', 'Untitled Gap')}")
                parts.append(f"     {gap.get('gap_description', '')}")
                parts.append(f"     Priority: {gap.get('priority', '?')} | Feasibility: {gap.get('estimated_feasibility', '?')}")

        directions = gap_analysis.get("future_directions", [])
        if directions:
            parts.append("\nFUTURE DIRECTIONS:")
            for i, fd in enumerate(directions, 1):
                parts.append(f"  {i}. {fd.get('title', 'Untitled Direction')}")
                parts.append(f"     {fd.get('description', '')}")
                parts.append(f"     Timeframe: {fd.get('timeframe', '?')}")

        for lf in ["methodology_gaps", "theoretical_gaps", "empirical_gaps"]:
            items = gap_analysis.get(lf, [])
            if items:
                label = lf.replace("_", " ").title()
                parts.append(f"\n{label}:")
                for item in items:
                    parts.append(f"  - {item}")

        return "\n".join(parts) if parts else "No gap analysis details available."

    def _parse_response(self, content: str) -> dict[str, Any]:
        """Parse and validate the literature review JSON response."""
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

        # Validate required string fields
        for sf in [
            "title", "executive_summary", "introduction",
            "methodology_comparison", "findings_synthesis",
            "contradictions_and_debates", "conclusion", "research_agenda",
        ]:
            if not isinstance(result.get(sf), str):
                result[sf] = ""

        # Validate thematic_analysis as a dict
        if not isinstance(result.get("thematic_analysis"), dict):
            result["thematic_analysis"] = {}

        # Validate bibliography
        if not isinstance(result.get("bibliography"), list):
            result["bibliography"] = []

        return result


async def literature_review_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node wrapper for the LiteratureReviewAgent.

    Reads 'processed_papers', 'research_topic', 'review_focus', 'gap_analysis'
    from AcademicResearchState, generates literature review, and writes
    'literature_review' back to state.
    """
    agent = LiteratureReviewAgent(llm=state.get("_llm") or state.get("config", {}).get("llm"))
    processed_papers = state.get("processed_papers", [])
    research_topic = state.get("research_topic", "Academic Research")
    review_focus = state.get("review_focus", "General analysis")
    gap_analysis = state.get("gap_analysis")
    user_instructions = state.get("user_instructions", "")

    if not processed_papers:
        return {
            "literature_review": None,
            "errors": state.get("errors", []) + ["No processed papers available for literature review"],
            "current_step": "lit_review_failed",
        }

    try:
        lit_review = await agent.synthesize(
            processed_papers=processed_papers,
            research_topic=research_topic,
            review_focus=review_focus,
            gap_analysis=gap_analysis,
            user_instructions=user_instructions,
        )
        return {
            "literature_review": lit_review,
            "current_step": "lit_review_complete",
            "processing_log": state.get("processing_log", []) + ["Literature review completed successfully"],
        }
    except Exception as e:
        return {
            "literature_review": None,
            "errors": state.get("errors", []) + [f"Literature review failed: {e}"],
            "current_step": "lit_review_failed",
        }

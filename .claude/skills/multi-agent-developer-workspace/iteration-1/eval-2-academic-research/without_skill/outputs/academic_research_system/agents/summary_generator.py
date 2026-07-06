"""
SummaryGeneratorAgent - Creates multi-level summaries of academic papers.

This agent produces summaries at three granularity levels:
1. One-sentence summary (< 30 words)
2. Paragraph annotation (100-150 words, suitable for annotated bibliography)
3. Detailed structured summary (300-500 words)

It incorporates quality assessment context to calibrate how findings are presented,
preserving nuance about limitations and uncertainty.

LangGraph Node Signature:
    Input:  SubgraphState with 'extraction' and 'quality' populated
    Output: SubgraphState with 'summary' populated as PaperSummary dict
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from academic_research_system.agents.prompts import (
    SUMMARY_GENERATOR_SYSTEM,
    SUMMARY_GENERATOR_HUMAN,
)

logger = logging.getLogger(__name__)


class SummaryGeneratorAgent:
    """
    Agent for generating multi-level summaries of academic papers.

    Responsibilities:
    - Produce one-sentence, paragraph, and detailed summaries
    - Identify and articulate key contributions
    - Summarize methodology in accessible language
    - Extract principal findings with quantitative precision
    - Articulate both practical and theoretical implications
    - Identify the target audience for the research
    """

    def __init__(self, llm: BaseChatModel):
        """
        Args:
            llm: Language model instance.
        """
        self.llm = llm
        self.name = "SummaryGeneratorAgent"

    async def summarize(
        self,
        extraction: dict[str, Any],
        quality: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a multi-level summary of a paper.

        Args:
            extraction: Extracted paper metadata (from PaperExtractorAgent).
            quality: Quality assessment (from QualityAnalyzerAgent).

        Returns:
            Dictionary conforming to the PaperSummary schema.
        """
        logger.info("[%s] Summarizing: '%s'", self.name, extraction.get("title", "Unknown"))

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
            "key_findings": json.dumps(extraction.get("key_findings", []), ensure_ascii=False),
            "limitations": json.dumps(extraction.get("limitations", []), ensure_ascii=False),
            "conclusion": extraction.get("conclusion", "N/A"),
            "novelty_level": quality.get("novelty_level", "N/A"),
            "novelty_rationale": quality.get("novelty_rationale", "N/A"),
            "rigor_level": quality.get("rigor_level", "N/A"),
            "rigor_rationale": quality.get("rigor_rationale", "N/A"),
            "overall_quality_score": quality.get("overall_quality_score", "N/A"),
        }

        messages = [
            SystemMessage(content=SUMMARY_GENERATOR_SYSTEM),
            HumanMessage(content=SUMMARY_GENERATOR_HUMAN.format(**prompt_data)),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            result = self._parse_response(response.content)
            logger.info("[%s] Summary generated for: '%s'", self.name, extraction.get("title", "Unknown"))
            return result
        except Exception as e:
            logger.error("[%s] Summary generation failed: %s", self.name, str(e))
            raise

    def _parse_response(self, content: str) -> dict[str, Any]:
        """Parse and validate the summary JSON response."""
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
            "one_sentence_summary", "paragraph_summary", "detailed_summary",
            "methodology_summary", "target_audience",
        ]:
            if not isinstance(result.get(sf), str):
                result[sf] = ""

        # Validate list fields
        for lf in [
            "key_contributions", "principal_findings",
            "practical_implications", "theoretical_contributions",
        ]:
            if not isinstance(result.get(lf), list):
                result[lf] = []

        return result


async def summary_generator_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node wrapper for the SummaryGeneratorAgent.

    Reads 'extraction' and 'quality' from SubgraphState,
    generates summary, and writes 'summary' back to state.
    """
    agent = SummaryGeneratorAgent(llm=state.get("_llm"))
    extraction = state.get("extraction")
    quality = state.get("quality")

    if not extraction:
        return {"summary": None, "error": "No extraction data provided", "stage": "error"}
    if not quality:
        return {"summary": None, "error": "No quality assessment provided", "stage": "error"}

    try:
        summary = await agent.summarize(extraction, quality)
        return {"summary": summary, "stage": "summarized", "error": None}
    except Exception as e:
        return {"summary": None, "error": f"Summary generation failed: {e}", "stage": "error"}

"""
PaperExtractorAgent - Extracts structured metadata from academic paper text.

This agent processes raw paper text (from PDF conversion, text extraction, or manual input)
and produces structured metadata including title, authors, methodology, findings,
limitations, and statistical methods. It uses academic domain knowledge to recognize
methodology types even when described with non-standard terminology.

LangGraph Node Signature:
    Input:  SubgraphState with 'paper_text' populated
    Output: SubgraphState with 'extraction' populated as ExtractedPaper dict
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from academic_research_system.agents.prompts import (
    PAPER_EXTRACTOR_SYSTEM,
    PAPER_EXTRACTOR_HUMAN,
)

logger = logging.getLogger(__name__)


class PaperExtractorAgent:
    """
    Agent for extracting structured metadata from academic papers.

    Responsibilities:
    - Parse paper text to identify all structural components (title, authors, abstract, etc.)
    - Classify the research methodology type
    - Extract key findings with specificity (numbers, significance levels)
    - Identify limitations both explicitly stated and implicitly evident
    - Detect data sources, sample sizes, and statistical methods
    """

    def __init__(self, llm: BaseChatModel):
        """
        Args:
            llm: Language model instance (e.g., ChatOpenAI, ChatAnthropic).
        """
        self.llm = llm
        self.name = "PaperExtractorAgent"

    async def extract(self, paper_text: str) -> dict[str, Any]:
        """
        Extract structured metadata from a single paper.

        Args:
            paper_text: Raw text content of the academic paper.

        Returns:
            Dictionary conforming to the ExtractedPaper schema.

        Raises:
            ValueError: If the LLM response cannot be parsed.
        """
        logger.info("[%s] Extracting metadata from paper (length=%d chars)", self.name, len(paper_text))

        messages = [
            SystemMessage(content=PAPER_EXTRACTOR_SYSTEM),
            HumanMessage(content=PAPER_EXTRACTOR_HUMAN.format(paper_text=paper_text)),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            result = self._parse_response(response.content)
            logger.info("[%s] Extraction complete: '%s'", self.name, result.get("title", "Unknown"))
            return result
        except Exception as e:
            logger.error("[%s] Extraction failed: %s", self.name, str(e))
            raise

    def _parse_response(self, content: str) -> dict[str, Any]:
        """
        Parse the LLM response into a structured dictionary.

        Handles markdown code fences and common formatting variations.
        """
        # Strip markdown code fences if present
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
            logger.error("[%s] Failed to parse JSON response: %s", self.name, e)
            logger.debug("[%s] Raw response: %s", self.name, content[:500])
            raise ValueError(f"LLM returned invalid JSON: {e}") from e

        # Validate required fields
        required_fields = ["title", "authors", "abstract"]
        for field in required_fields:
            if field not in result:
                logger.warning("[%s] Missing required field: %s", self.name, field)
                result.setdefault(field, "" if field != "authors" else [])

        # Normalize author structure
        if result.get("authors") and isinstance(result["authors"], list):
            for i, author in enumerate(result["authors"]):
                if isinstance(author, str):
                    result["authors"][i] = {"name": author, "affiliation": None, "email": None}
                elif isinstance(author, dict):
                    author.setdefault("name", "Unknown")
                    author.setdefault("affiliation", None)
                    author.setdefault("email", None)

        # Ensure list fields are lists
        list_fields = [
            "keywords", "key_findings", "limitations", "data_sources",
            "statistical_methods", "research_questions", "hypotheses",
        ]
        for lf in list_fields:
            if not isinstance(result.get(lf), list):
                result[lf] = []

        # Normalize methodology_type
        valid_types = {
            "experimental", "observational", "meta-analysis", "systematic_review",
            "case_study", "theoretical", "mixed_methods", "survey", "simulation",
            "longitudinal", "cross_sectional", "unknown",
        }
        mtype = result.get("methodology_type", "unknown")
        if mtype not in valid_types:
            result["methodology_type"] = "unknown"

        return result


async def paper_extractor_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node wrapper for the PaperExtractorAgent.

    Reads 'paper_text' from SubgraphState, runs extraction,
    and writes 'extraction' back to state.
    """
    agent = PaperExtractorAgent(llm=state.get("_llm"))
    paper_text = state.get("paper_text", "")

    if not paper_text:
        return {"extraction": None, "error": "No paper text provided", "stage": "error"}

    try:
        extraction = await agent.extract(paper_text)
        return {"extraction": extraction, "stage": "extracted", "error": None}
    except Exception as e:
        return {"extraction": None, "error": f"Extraction failed: {e}", "stage": "error"}

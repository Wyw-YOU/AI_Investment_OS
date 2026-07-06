"""
Agents for the Multi-Agent Academic Research System.

Each agent is a specialized expert that performs a specific analysis task
on academic papers. Agents communicate through well-defined Pydantic models
and are orchestrated by LangGraph workflows.
"""

from .paper_extractor import PaperExtractorAgent
from .quality_analyzer import QualityAnalyzerAgent
from .summary_generator import SummaryGeneratorAgent
from .gap_analyzer import GapAnalyzerAgent
from .literature_review import LiteratureReviewAgent

__all__ = [
    "PaperExtractorAgent",
    "QualityAnalyzerAgent",
    "SummaryGeneratorAgent",
    "GapAnalyzerAgent",
    "LiteratureReviewAgent",
]

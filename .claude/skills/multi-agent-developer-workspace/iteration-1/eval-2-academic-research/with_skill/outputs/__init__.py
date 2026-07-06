"""
Multi-Agent Academic Research System
=====================================

A multi-agent system for analyzing, summarizing, and synthesizing academic papers.
Built with LangGraph for workflow orchestration and Pydantic for state management.

Agents:
    - PaperExtractorAgent: Extracts structured metadata from academic papers
    - QualityAnalyzerAgent: Assesses research rigor, novelty, and impact
    - SummaryGeneratorAgent: Creates concise, structured summaries
    - GapAnalyzerAgent: Identifies research gaps and future directions
    - LiteratureReviewAgent: Synthesizes multiple papers into literature reviews

Usage:
    from main import AcademicResearchSystem

    system = AcademicResearchSystem(api_key="your-api-key")
    result = system.analyze_paper("path/to/paper.pdf")
    corpus_result = system.analyze_corpus(["paper1.pdf", "paper2.pdf", "paper3.pdf"])
"""

__version__ = "1.0.0"
__author__ = "AI Investment OS - Multi-Agent Developer Skill"

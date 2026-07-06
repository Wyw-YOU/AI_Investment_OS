"""
State management for the Academic Research Multi-Agent System.

Defines all data models and shared state structures used across agents.
Tracks the full lifecycle of paper analysis from extraction through synthesis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ResearchMethodologyType(str, Enum):
    """Classification of research methodologies."""
    EXPERIMENTAL = "experimental"
    OBSERVATIONAL = "observational"
    META_ANALYSIS = "meta-analysis"
    SYSTEMATIC_REVIEW = "systematic_review"
    CASE_STUDY = "case_study"
    THEORETICAL = "theoretical"
    MIXED_METHODS = "mixed_methods"
    SURVEY = "survey"
    SIMULATION = "simulation"
    LONGITUDINAL = "longitudinal"
    CROSS_SECTIONAL = "cross_sectional"
    UNKNOWN = "unknown"


class NoveltyLevel(str, Enum):
    """Assessment of research novelty."""
    GROUNDBREAKING = "groundbreaking"     # First-of-kind discovery or framework
    HIGHLY_NOVEL = "highly_novel"         # Significant new contribution
    MODERATELY_NOVEL = "moderately_novel" # Incremental but meaningful advance
    INCREMENTAL = "incremental"           # Small extension of existing work
    DUPLICATIVE = "duplicative"           # Largely replicates prior findings


class RigorLevel(str, Enum):
    """Assessment of methodological rigor."""
    EXEMPLARY = "exemplary"
    STRONG = "strong"
    ADEQUATE = "adequate"
    WEAK = "weak"
    POOR = "poor"


class PaperStage(str, Enum):
    """Processing pipeline stage for each paper."""
    RAW = "raw"
    EXTRACTED = "extracted"
    QUALITY_ASSESSED = "quality_assessed"
    SUMMARIZED = "summarized"
    GAPS_IDENTIFIED = "gaps_identified"
    SYNTHESIZED = "synthesized"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Core Data Models
# ---------------------------------------------------------------------------

@dataclass
class Author:
    """Represents a paper author."""
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    orcid: Optional[str] = None


@dataclass
class ExtractedPaper:
    """Structured data extracted from a single academic paper."""
    title: str
    authors: list[Author]
    abstract: str
    year: Optional[int] = None
    journal_or_venue: Optional[str] = None
    doi: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    methodology: Optional[str] = None
    methodology_type: ResearchMethodologyType = ResearchMethodologyType.UNKNOWN
    key_findings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    data_sources: list[str] = field(default_factory=list)
    sample_size: Optional[str] = None
    statistical_methods: list[str] = field(default_factory=list)
    research_questions: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    conclusion: Optional[str] = None
    references_count: Optional[int] = None
    sections: dict[str, str] = field(default_factory=dict)


@dataclass
class QualityAssessment:
    """Evaluation of research quality for a single paper."""
    novelty_level: NoveltyLevel = NoveltyLevel.INCREMENTAL
    novelty_rationale: str = ""
    rigor_level: RigorLevel = RigorLevel.ADEQUATE
    rigor_rationale: str = ""
    significance_score: float = 0.0          # 0-10
    methodology_score: float = 0.0           # 0-10
    clarity_score: float = 0.0              # 0-10
    reproducibility_score: float = 0.0       # 0-10
    impact_potential_score: float = 0.0      # 0-10
    overall_quality_score: float = 0.0       # 0-10
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    ethical_considerations: list[str] = field(default_factory=list)
    bias_assessment: str = ""
    validity_threats: list[str] = field(default_factory=list)


@dataclass
class PaperSummary:
    """Concise summary of a single paper."""
    one_sentence_summary: str = ""
    paragraph_summary: str = ""
    detailed_summary: str = ""
    key_contributions: list[str] = field(default_factory=list)
    methodology_summary: str = ""
    principal_findings: list[str] = field(default_factory=list)
    practical_implications: list[str] = field(default_factory=list)
    theoretical_contributions: list[str] = field(default_factory=list)
    target_audience: str = ""


@dataclass
class ResearchGap:
    """Represents an identified gap in the research literature."""
    gap_title: str = ""
    gap_description: str = ""
    supporting_evidence: list[str] = field(default_factory=list)
    papers_evidencing: list[str] = field(default_factory=list)
    potential_impact: str = ""
    suggested_approach: str = ""
    estimated_feasibility: str = ""
    priority: str = ""  # "high", "medium", "low"
    related_keywords: list[str] = field(default_factory=list)


@dataclass
class FutureDirection:
    """Represents a suggested future research direction."""
    title: str = ""
    description: str = ""
    rationale: str = ""
    suggested_methodology: str = ""
    expected_challenges: list[str] = field(default_factory=list)
    potential_contribution: str = ""
    timeframe: str = ""  # "short-term", "medium-term", "long-term"
    required_expertise: str = ""


@dataclass
class GapAnalysis:
    """Complete gap analysis results."""
    research_gaps: list[ResearchGap] = field(default_factory=list)
    future_directions: list[FutureDirection] = field(default_factory=list)
    overarching_themes: list[str] = field(default_factory=list)
    methodology_gaps: list[str] = field(default_factory=list)
    theoretical_gaps: list[str] = field(default_factory=list)
    empirical_gaps: list[str] = field(default_factory=list)


@dataclass
class LiteratureReview:
    """Synthesized literature review from multiple papers."""
    title: str = ""
    executive_summary: str = ""
    introduction: str = ""
    thematic_analysis: dict[str, str] = field(default_factory=dict)
    methodology_comparison: str = ""
    findings_synthesis: str = ""
    contradictions_and_debates: str = ""
    conclusion: str = ""
    research_agenda: str = ""
    bibliography: list[str] = field(default_factory=list)


@dataclass
class ProcessedPaper:
    """Container for all analysis results for a single paper."""
    paper_id: str
    original_text: str
    stage: PaperStage = PaperStage.RAW
    extraction: Optional[ExtractedPaper] = None
    quality: Optional[QualityAssessment] = None
    summary: Optional[PaperSummary] = None
    gaps: Optional[GapAnalysis] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------------

class AcademicResearchState(TypedDict):
    """
    Central state object for the LangGraph workflow.
    All agents read from and write to this shared state.
    """
    # Input
    paper_texts: list[str]                     # Raw paper texts to process
    research_topic: str                        # The overarching research topic
    review_focus: str                          # Specific focus for the literature review
    user_instructions: str                     # Any additional user instructions

    # Per-paper processing
    processed_papers: list[dict[str, Any]]     # List of ProcessedPaper dicts

    # Corpus-level outputs
    literature_review: Optional[dict[str, Any]]
    gap_analysis: Optional[dict[str, Any]]

    # Workflow metadata
    current_step: str
    errors: list[str]
    processing_log: list[str]
    config: dict[str, Any]


class SubgraphState(TypedDict):
    """
    State used within individual paper processing subgraphs.
    Processes one paper through extraction -> quality -> summary pipeline.
    """
    paper_text: str
    paper_id: str
    paper_index: int
    extraction: Optional[dict[str, Any]]
    quality: Optional[dict[str, Any]]
    summary: Optional[dict[str, Any]]
    error: Optional[str]
    stage: str

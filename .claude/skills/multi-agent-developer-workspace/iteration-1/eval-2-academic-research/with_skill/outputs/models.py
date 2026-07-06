"""
Data models for the Multi-Agent Academic Research System.

Defines all Pydantic models used for:
    - Paper representation and metadata
    - Agent output contracts (structured, validated)
    - Workflow state management
    - Quality scoring and analysis results

Design Principles (from multi-agent-developer skill):
    - Type-safe: All fields have explicit types
    - Validated: Pydantic validators enforce constraints
    - Serializable: All models can be JSON-serialized
    - Minimal: Only necessary data is included
"""

from pydantic import BaseModel, Field, validator
from typing import Any, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ResearchField(str, Enum):
    """Academic research field classification."""
    COMPUTER_SCIENCE = "computer_science"
    PHYSICS = "physics"
    BIOLOGY = "biology"
    CHEMISTRY = "chemistry"
    MATHEMATICS = "mathematics"
    ENGINEERING = "engineering"
    MEDICINE = "medicine"
    SOCIAL_SCIENCE = "social_science"
    ECONOMICS = "economics"
    PSYCHOLOGY = "psychology"
    INTERDISCIPLINARY = "interdisciplinary"
    OTHER = "other"


class MethodologyType(str, Enum):
    """Classification of research methodology."""
    EXPERIMENTAL = "experimental"
    THEORETICAL = "theoretical"
    COMPUTATIONAL = "computational"
    SURVEY = "survey"
    CASE_STUDY = "case_study"
    META_ANALYSIS = "meta_analysis"
    MIXED_METHODS = "mixed_methods"
    REVIEW = "review"
    QUALITATIVE = "qualitative"
    QUANTITATIVE = "quantitative"


class QualityLevel(str, Enum):
    """Discrete quality level for quick classification."""
    EXCEPTIONAL = "exceptional"
    HIGH = "high"
    GOOD = "good"
    MODERATE = "moderate"
    LOW = "low"
    POOR = "poor"


class WorkflowPhase(str, Enum):
    """Phases of the research analysis workflow."""
    INIT = "init"
    EXTRACTING = "extracting"
    ANALYZING_QUALITY = "analyzing_quality"
    SUMMARIZING = "summarizing"
    IDENTIFYING_GAPS = "identifying_gaps"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Paper Representation
# ---------------------------------------------------------------------------

class PaperMetadata(BaseModel):
    """Structured metadata extracted from a single academic paper."""

    title: str = Field(..., description="Full title of the paper")
    authors: list[str] = Field(default_factory=list, description="List of author names")
    abstract: str = Field(default="", description="Paper abstract")
    publication_year: Optional[int] = Field(None, description="Year of publication")
    journal_or_venue: Optional[str] = Field(None, description="Journal, conference, or venue name")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    keywords: list[str] = Field(default_factory=list, description="Author-provided keywords")
    research_field: ResearchField = Field(
        default=ResearchField.OTHER,
        description="Primary research field",
    )
    methodology: MethodologyType = Field(
        default=MethodologyType.EXPERIMENTAL,
        description="Primary research methodology",
    )
    citation_count: Optional[int] = Field(None, description="Number of citations (if available)")
    references_count: Optional[int] = Field(None, description="Number of references cited")

    @validator("publication_year")
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1900 or v > 2030):
            logger.warning(f"Unusual publication year: {v}")
        return v


class KeyFindings(BaseModel):
    """Structured representation of paper findings."""

    primary_findings: list[str] = Field(
        default_factory=list,
        description="Main research findings, one per item",
    )
    secondary_findings: list[str] = Field(
        default_factory=list,
        description="Supporting or ancillary findings",
    )
    statistical_significance: Optional[str] = Field(
        None,
        description="Summary of statistical significance where applicable",
    )
    key_contributions: list[str] = Field(
        default_factory=list,
        description="Novel contributions claimed by the authors",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Self-reported limitations of the study",
    )


# ---------------------------------------------------------------------------
# Quality Analysis
# ---------------------------------------------------------------------------

class QualityDimension(BaseModel):
    """Score and justification for a single quality dimension."""

    dimension_name: str
    score: float = Field(ge=0.0, le=10.0, description="Score from 0 to 10")
    justification: str = Field(default="", description="Reasoning behind the score")


class QualityAssessment(BaseModel):
    """Comprehensive quality assessment of a research paper."""

    overall_score: float = Field(
        ge=0.0, le=10.0,
        description="Weighted overall quality score (0-10)",
    )
    quality_level: QualityLevel = Field(description="Discrete quality classification")
    dimensions: list[QualityDimension] = Field(
        default_factory=list,
        description="Individual quality dimension scores",
    )
    novelty_score: float = Field(
        ge=0.0, le=10.0,
        description="How novel/original the contribution is",
    )
    rigor_score: float = Field(
        ge=0.0, le=10.0,
        description="Methodological rigor and soundness",
    )
    impact_score: float = Field(
        ge=0.0, le=10.0,
        description="Potential impact on the field",
    )
    clarity_score: float = Field(
        ge=0.0, le=10.0,
        description="Quality of writing and presentation",
    )
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendation: str = Field(
        default="",
        description="Summary recommendation (e.g., 'accept', 'minor revisions')",
    )


class ResearchGap(BaseModel):
    """A single identified research gap or future direction."""

    gap_description: str = Field(description="Clear description of the gap")
    significance: str = Field(
        description="Why this gap matters to the field",
    )
    suggested_approach: str = Field(
        default="",
        description="Suggested methodology or approach to address this gap",
    )
    related_papers: list[str] = Field(
        default_factory=list,
        description="Papers that partially address or motivate this gap",
    )
    priority: str = Field(
        default="medium",
        description="Priority level: high, medium, or low",
    )


class GapAnalysisResult(BaseModel):
    """Result of the GapAnalyzerAgent."""

    research_gaps: list[ResearchGap] = Field(default_factory=list)
    emerging_themes: list[str] = Field(
        default_factory=list,
        description="Emerging themes and trends in the field",
    )
    future_directions: list[str] = Field(
        default_factory=list,
        description="Specific future research directions",
    )
    cross_paper_gaps: list[str] = Field(
        default_factory=list,
        description="Gaps that span multiple papers in the corpus",
    )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class PaperSummary(BaseModel):
    """Concise, structured summary of a single paper."""

    one_line_summary: str = Field(description="Single-sentence summary")
    detailed_summary: str = Field(description="2-3 paragraph detailed summary")
    methodology_summary: str = Field(description="Summary of the methodology used")
    key_takeaways: list[str] = Field(
        default_factory=list,
        description="3-5 key takeaways from the paper",
    )
    relevance_tags: list[str] = Field(
        default_factory=list,
        description="Tags indicating relevance to topics/areas",
    )


# ---------------------------------------------------------------------------
# Literature Review
# ---------------------------------------------------------------------------

class LiteratureReview(BaseModel):
    """Synthesized literature review across a corpus of papers."""

    title: str = Field(description="Auto-generated review title")
    introduction: str = Field(description="Introduction paragraph setting context")
    thematic_sections: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Thematic sections with title and body",
    )
    synthesis: str = Field(description="Synthesis and critical analysis paragraph")
    conclusion: str = Field(description="Conclusion with overarching findings")
    bibliography: list[dict[str, str]] = Field(
        default_factory=list,
        description="Formatted bibliography entries",
    )
    total_papers_reviewed: int = Field(default=0)


# ---------------------------------------------------------------------------
# Agent Output Contract
# ---------------------------------------------------------------------------

class AgentOutput(BaseModel):
    """
    Standard output format for all agents.

    Every agent must return an AgentOutput. This ensures:
    - Consistent interface across agents
    - Confidence scoring on every result
    - Citation tracking for traceability
    - Metadata for debugging and monitoring
    """

    agent_name: str = Field(description="Identifier of the agent that produced this output")
    result: dict[str, Any] = Field(description="The analysis result payload")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Agent's confidence in its own output",
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Sources or references cited in the analysis",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Extra metadata (model used, tokens, timing, etc.)",
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator("confidence")
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {v}")
        return v

    @validator("citations")
    def validate_citations(cls, v: list[str]) -> list[str]:
        if not v:
            logger.warning("No citations provided -- results may not be verifiable")
        return v


# ---------------------------------------------------------------------------
# Workflow State
# ---------------------------------------------------------------------------

class AcademicResearchState(BaseModel):
    """
    Central state object passed between workflow nodes.

    Follows the multi-agent-developer skill's state design principles:
    - Minimal: Only necessary data
    - Well-typed: Pydantic validation
    - Serializable: JSON-compatible
    - Immutable between nodes: Nodes return new state via model copy
    """

    # --- Identifiers ---
    task_id: str = Field(description="Unique task identifier")
    session_id: str = Field(default="default", description="Session identifier")

    # --- Input ---
    paper_texts: list[str] = Field(
        default_factory=list,
        description="Raw text content of papers to analyze",
    )
    paper_filenames: list[str] = Field(
        default_factory=list,
        description="Original filenames for the papers",
    )
    research_question: str = Field(
        default="",
        description="Optional research question to focus the analysis",
    )

    # --- Workflow tracking ---
    phase: WorkflowPhase = Field(default=WorkflowPhase.INIT)
    version: int = Field(default=1)
    errors: list[str] = Field(default_factory=list)

    # --- Per-paper analysis results ---
    paper_metadata: list[PaperMetadata] = Field(default_factory=list)
    quality_assessments: list[QualityAssessment] = Field(default_factory=list)
    paper_summaries: list[PaperSummary] = Field(default_factory=list)
    gap_analysis: Optional[GapAnalysisResult] = Field(None)

    # --- Final outputs ---
    literature_review: Optional[LiteratureReview] = Field(None)

    # --- Agent outputs for traceability ---
    agent_outputs: dict[str, AgentOutput] = Field(default_factory=dict)

    # --- Timestamps ---
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    def transition_phase(self, target: "WorkflowPhase") -> "AcademicResearchState":
        """Return a new state with an updated phase (immutable transition)."""
        return self.copy(
            update={
                "phase": target,
                "version": self.version + 1,
                "updated_at": datetime.now(),
            }
        )

    def add_agent_output(self, name: str, output: AgentOutput) -> "AcademicResearchState":
        """Return a new state with an additional agent output recorded."""
        new_outputs = {**self.agent_outputs, name: output}
        return self.copy(
            update={
                "agent_outputs": new_outputs,
                "version": self.version + 1,
                "updated_at": datetime.now(),
            }
        )

    def add_error(self, error: str) -> "AcademicResearchState":
        """Return a new state with an appended error message."""
        return self.copy(
            update={
                "errors": self.errors + [error],
                "version": self.version + 1,
                "updated_at": datetime.now(),
            }
        )

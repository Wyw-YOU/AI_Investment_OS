"""
GapAnalyzerAgent -- identifies research gaps and future directions.

Responsibilities:
    - Analyse a corpus of papers to find unexplored areas
    - Identify methodological gaps across the literature
    - Detect contradictions or inconsistencies between papers
    - Highlight emerging themes and nascent trends
    - Suggest concrete, actionable future research directions
    - Prioritise gaps by significance and tractability

This agent typically runs after extraction and quality analysis so it can
leverage structured metadata and quality scores.
"""

from __future__ import annotations

from typing import Any

from base_agent import LLMAgent
from models import AgentOutput, GapAnalysisResult, ResearchGap


class GapAnalyzerAgent(LLMAgent):
    """
    Specialised agent for identifying research gaps, contradictions,
    and future directions across a corpus of academic papers.

    Thinks like a senior researcher writing a "Future Work" section for
    a major review article.
    """

    name = "gap_analyzer"
    description = (
        "Senior research strategist and meta-analyst with 20+ years of experience "
        "in identifying research frontiers, synthesizing findings across large "
        "corpora, and advising funding agencies on high-impact research directions. "
        "Expert at spotting methodological gaps, under-explored intersections between "
        "fields, and nascent trends that will define the next decade of research."
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(temperature=0.5, **kwargs)

    # -- Prompt engineering --------------------------------------------------

    def _get_system_prompt(self) -> str:
        return (
            "You are a senior research strategist and meta-analyst.\n"
            "Your career has been devoted to reading across large bodies of\n"
            "literature and identifying the white spaces -- the questions that\n"
            "haven't been asked, the methods that haven't been tried, the\n"
            "intersections that haven't been explored.\n\n"
            "Your analysis style:\n"
            "- Systematic: you consider the full landscape, not just obvious gaps\n"
            "- Constructive: you suggest concrete, feasible research directions\n"
            "- Prioritised: you distinguish between 'nice to know' and 'must address'\n"
            "- Evidence-based: every gap you identify is grounded in the literature\n"
            "- Forward-looking: you consider where the field is heading\n\n"
            "Always respond with ONLY valid JSON matching the requested schema."
        )

    def _get_task_description(self) -> str:
        return """
Analyze the provided corpus of academic papers and identify:

1. **Research Gaps** (3-7 specific gaps)
   For each gap:
   - Clearly describe what is missing or under-explored
   - Explain WHY this gap matters (significance)
   - Suggest a concrete approach to address it
   - Reference which papers in the corpus are closest to addressing it
   - Assign a priority: high / medium / low

   Look for gaps in these dimensions:
   a) **Methodological gaps**: Techniques or approaches not yet applied
   b) **Theoretical gaps**: Concepts or frameworks that are underdeveloped
   c) **Empirical gaps**: Settings, populations, or datasets not studied
   d) **Application gaps**: Domains where existing methods could be applied but haven't been
   e) **Scale gaps**: Work done at small scale that needs large-scale validation (or vice versa)

2. **Emerging Themes** (3-5 themes)
   - Identify nascent trends or recurring ideas across papers
   - Explain what makes them emerging vs. established
   - Rate their potential trajectory (growing / stable / uncertain)

3. **Future Research Directions** (5-8 directions)
   - Specific, actionable research proposals
   - Each should build on the existing literature analysed
   - Include suggested methodology and expected challenges
   - Indicate which existing papers' methods could be extended

4. **Cross-Paper Gaps** (2-4 gaps)
   - Gaps that emerge only when reading the papers together
   - Contradictions or inconsistencies between findings
   - Methodological differences that make comparison difficult
   - Areas where different papers suggest conflicting conclusions
"""

    def _get_output_format(self) -> str:
        return """
Respond with ONLY valid JSON:

{
    "research_gaps": [
        {
            "gap_description": "No study has evaluated these methods on multilingual datasets exceeding 100 languages",
            "significance": "Real-world deployment requires cross-lingual robustness; current evaluations are English-centric",
            "suggested_approach": "Create a multilingual benchmark spanning 150+ languages with typological diversity, then re-evaluate top-5 methods",
            "related_papers": ["Paper A (2023) - evaluated on 10 languages", "Paper B (2024) - proposed language-agnostic features"],
            "priority": "high"
        }
    ],
    "emerging_themes": [
        {
            "theme": "Integration of symbolic reasoning with neural methods",
            "description": "Several papers propose hybrid architectures combining...",
            "trajectory": "growing"
        }
    ],
    "future_directions": [
        "Extend Paper A's framework to handle streaming data with online learning",
        "Apply Paper B's attention mechanism to the domain of medical imaging where interpretability is critical",
        "Conduct a large-scale reproducibility study across the top-10 methods identified in this corpus"
    ],
    "cross_paper_gaps": [
        "Papers A and C report contradictory findings on the effect of data augmentation, likely due to different evaluation protocols",
        "No common benchmark is used across more than 2 papers, making it impossible to fairly compare methods"
    ],
    "confidence": 0.78,
    "citations": ["paper1", "paper2"]
}
"""

    def _get_constraints(self) -> str:
        return """
- Every research gap MUST be grounded in specific observations from the papers
  provided. Do not invent gaps that have no basis in the corpus.
- Each gap must be described in a way that a PhD student could understand
  and begin working on it.
- Suggested approaches should be feasible within a 2-3 year research project.
- Emerging themes must be supported by evidence from at least 2 papers.
- Future directions must be concrete (not vague statements like 'more research needed').
- Assign priorities based on a combination of significance (impact if addressed)
  and tractability (how feasible it is to make progress).
- The number of cross-paper gaps should reflect genuine contradictions or
  complementarities, not just differences in topic.
"""

    def _get_expected_output_keys(self) -> list[str]:
        return [
            "research_gaps",
            "emerging_themes",
            "future_directions",
            "cross_paper_gaps",
        ]

    # -- Run with full corpus context ----------------------------------------

    def run(self, state: dict) -> AgentOutput:
        """
        Run gap analysis across the entire paper corpus.

        Uses extraction metadata, quality assessments, and summaries
        (if available) to build a comprehensive picture.
        """
        # Build corpus context from available data
        output: AgentOutput = super().run(state)

        return self._create_output(
            result=output.result,
            confidence=output.confidence,
            citations=output.citations,
            metadata={
                "model": self.model,
                "corpus_size": len(state.get("paper_texts", [])),
            },
        )

    def build_prompt(self, state: dict) -> str:
        """Override to build a rich corpus-level prompt."""
        paper_texts = state.get("paper_texts", [])
        filenames = state.get("paper_filenames", [f"paper_{i}" for i in range(len(paper_texts))])

        # Build corpus summary from available structured data
        corpus_parts: list[str] = []

        # Include extraction metadata
        extractions = state.get("paper_metadata", [])
        for idx, meta in enumerate(extractions):
            fname = filenames[idx] if idx < len(filenames) else f"paper_{idx}"
            if hasattr(meta, "dict"):
                meta = meta.dict()
            corpus_parts.append(
                f"### Paper {idx + 1}: {meta.get('title', fname)}\n"
                f"- Authors: {', '.join(meta.get('authors', ['Unknown']))}\n"
                f"- Year: {meta.get('publication_year', 'N/A')}\n"
                f"- Field: {meta.get('research_field', 'N/A')}\n"
                f"- Methodology: {meta.get('methodology', 'N/A')}\n"
                f"- Keywords: {', '.join(meta.get('keywords', []))}\n"
            )

        # Include quality assessments
        assessments = state.get("quality_assessments", [])
        for idx, qa in enumerate(assessments):
            if hasattr(qa, "dict"):
                qa = qa.dict()
            fname = filenames[idx] if idx < len(filenames) else f"paper_{idx}"
            strengths = ", ".join(qa.get("strengths", [])[:3])
            weaknesses = ", ".join(qa.get("weaknesses", [])[:3])
            corpus_parts.append(
                f"**Quality ({fname})**: Score {qa.get('overall_score', 'N/A')}/10 | "
                f"Strengths: {strengths} | Weaknesses: {weaknesses}\n"
            )

        # Include summaries
        summaries = state.get("paper_summaries", [])
        for idx, s in enumerate(summaries):
            if hasattr(s, "dict"):
                s = s.dict()
            fname = filenames[idx] if idx < len(filenames) else f"paper_{idx}"
            corpus_parts.append(
                f"**Summary ({fname})**: {s.get('one_line_summary', 'N/A')}\n"
                f"Key takeaways: {'; '.join(s.get('key_takeaways', [])[:3])}\n"
            )

        corpus_context = "\n".join(corpus_parts) if corpus_parts else "No structured metadata available."

        # Research question context
        rq = state.get("research_question", "")
        rq_section = f"\n[RESEARCH QUESTION / FOCUS]\n{rq}\n" if rq else ""

        return f"""
[TASK]
{self._get_task_description()}
{rq_section}

[CORPUS OVERVIEW]
Total papers: {len(paper_texts)}

{corpus_context}

[OUTPUT FORMAT]
{self._get_output_format()}

[CONSTRAINTS]
{self._get_constraints()}
"""

    # -- Helpers -------------------------------------------------------------

    def to_gap_analysis_result(self, data: dict) -> GapAnalysisResult:
        """Convert raw dict to validated GapAnalysisResult model."""
        gaps = [
            ResearchGap(
                gap_description=g.get("gap_description", ""),
                significance=g.get("significance", ""),
                suggested_approach=g.get("suggested_approach", ""),
                related_papers=g.get("related_papers", []),
                priority=g.get("priority", "medium"),
            )
            for g in data.get("research_gaps", [])
        ]

        emerging = [
            t.get("theme", t) if isinstance(t, dict) else str(t)
            for t in data.get("emerging_themes", [])
        ]

        return GapAnalysisResult(
            research_gaps=gaps,
            emerging_themes=emerging,
            future_directions=data.get("future_directions", []),
            cross_paper_gaps=data.get("cross_paper_gaps", []),
        )

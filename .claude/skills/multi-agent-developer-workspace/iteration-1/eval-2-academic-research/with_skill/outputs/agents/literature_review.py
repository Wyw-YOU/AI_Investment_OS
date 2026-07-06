"""
LiteratureReviewAgent -- synthesizes multiple papers into a literature review.

Responsibilities:
    - Generate a structured literature review from a corpus of papers
    - Organise findings thematically rather than paper-by-paper
    - Write an introduction that sets the research context
    - Synthesize findings across papers, highlighting agreements and contradictions
    - Draw a conclusion that integrates the corpus findings
    - Produce a formatted bibliography

This agent is the final synthesis step. It leverages all prior agent outputs
(extractions, quality assessments, summaries, gap analysis) to produce
a coherent, publication-ready literature review.
"""

from __future__ import annotations

from typing import Any

from base_agent import LLMAgent
from models import AgentOutput, LiteratureReview


class LiteratureReviewAgent(LLMAgent):
    """
    Specialised agent for synthesizing academic papers into
    a coherent literature review.

    Writes like a senior researcher preparing a survey article
    for a top journal.
    """

    name = "literature_review"
    description = (
        "Distinguished professor and prolific survey author with extensive "
        "experience writing comprehensive literature reviews for top-tier "
        "journals (ACM Computing Surveys, Annual Review of Psychology, "
        "Nature Reviews). Expert at identifying thematic connections across "
        "papers, synthesising conflicting findings, and constructing a "
        "narrative that advances understanding of the field."
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(temperature=0.5, max_tokens=6000, **kwargs)

    # -- Prompt engineering --------------------------------------------------

    def _get_system_prompt(self) -> str:
        return (
            "You are a distinguished professor and prolific survey author.\n"
            "You have written literature reviews for the most prestigious\n"
            "journals in multiple fields. Your reviews are known for:\n\n"
            "- Thematic organisation (not paper-by-paper summaries)\n"
            "- Critical analysis (not just description)\n"
            "- Clear narrative arc (context -> analysis -> synthesis -> conclusion)\n"
            "- Balanced treatment of all major perspectives\n"
            "- Honest assessment of the state of the field\n"
            "- Actionable identification of future directions\n\n"
            "Your audience is researchers who want to understand the current\n"
            "state of a field without reading every paper themselves.\n\n"
            "Always respond with ONLY valid JSON matching the requested schema."
        )

    def _get_task_description(self) -> str:
        return """
Synthesize the provided corpus of academic papers into a comprehensive
literature review with the following structure:

1. **Title**
   - Generate a descriptive title for the literature review
   - Should capture the scope and focus of the corpus

2. **Introduction** (2-3 paragraphs)
   - Set the context: what is this field about and why does it matter?
   - Define the scope of this review
   - Outline the key themes that will be discussed
   - Briefly describe the corpus (number of papers, time span, methodologies)

3. **Thematic Sections** (3-5 sections)
   Each section should:
   - Have a clear, descriptive title
   - Synthesize findings from multiple papers (not just summarize one-by-one)
   - Identify agreements and disagreements between papers
   - Highlight methodological differences that affect interpretation
   - Include specific citations to support claims

   Organise by THEME, not by paper. For example:
   - "Methodological Advances in X"
   - "Applications of X to Domain Y"
   - "Theoretical Foundations of X"
   - "Scalability and Practical Considerations"

4. **Synthesis** (1-2 paragraphs)
   - What does the corpus as a whole tell us?
   - What are the major convergences and divergences?
   - What is the overall trajectory of the field?
   - How do the papers complement each other?

5. **Conclusion** (1-2 paragraphs)
   - Summarize the key insights from this review
   - Highlight the most significant gaps identified
   - Point to the most promising future directions
   - End with a forward-looking statement about the field

6. **Bibliography**
   - List all papers with formatted entries
   - Include title, authors, year, venue, and DOI where available
"""

    def _get_output_format(self) -> str:
        return """
Respond with ONLY valid JSON:

{
    "title": "A Survey of Efficient Attention Mechanisms for Long-Sequence Modeling",
    "introduction": "The ability to process long sequences is a fundamental challenge in modern machine learning... [2-3 paragraphs setting context, defining scope, and outlining themes]",
    "thematic_sections": [
        {
            "title": "Sparse Attention Patterns",
            "body": "A dominant approach to reducing attention complexity involves designing sparse attention patterns... [synthesis of multiple papers, with inline citations like (Smith et al., 2023)]"
        },
        {
            "title": "Linear Attention Approximations",
            "body": "An alternative line of research replaces the softmax attention kernel with... [discussion of 3-4 papers with comparisons]"
        },
        {
            "title": "Memory-Augmented Approaches",
            "body": "Several papers propose augmenting transformers with external memory..."
        }
    ],
    "synthesis": "Across the 15 papers reviewed, a clear trend emerges toward hybrid approaches... [synthesis paragraph identifying convergences, divergences, and trajectory]",
    "conclusion": "This review has surveyed the rapidly evolving landscape of efficient attention mechanisms... [conclusion with key insights and forward-looking statement]",
    "bibliography": [
        {
            "authors": "Smith, J., Johnson, A., Williams, B.",
            "year": "2023",
            "title": "Efficient Attention via Sparse Patterns",
            "venue": "ICML 2023",
            "doi": "10.xxxx/xxxxx"
        }
    ],
    "total_papers_reviewed": 15,
    "confidence": 0.85,
    "citations": ["paper1", "paper2"]
}
"""

    def _get_constraints(self) -> str:
        return """
- The review MUST synthesise across papers, not just summarize them one by one.
  Each thematic section should reference at least 2-3 papers.
- Every claim MUST be supported by a citation to a specific paper in the corpus.
  Use inline citations like (Author et al., Year).
- Do NOT introduce knowledge about papers not in the corpus.
- The introduction MUST provide sufficient context for a reader unfamiliar with
  the specific sub-field.
- Thematic sections should be balanced in depth (not one huge section and
  several tiny ones).
- The synthesis MUST go beyond summarizing the sections -- it should identify
  higher-level patterns and insights that emerge from reading them together.
- The conclusion MUST be forward-looking, not just a repetition of findings.
- Bibliography entries MUST use the actual paper metadata (titles, authors, years).
- Total length: 2000-4000 words for the main body (excluding bibliography).
"""

    def _get_expected_output_keys(self) -> list[str]:
        return [
            "title",
            "introduction",
            "thematic_sections",
            "synthesis",
            "conclusion",
            "bibliography",
        ]

    # -- Run with full context -----------------------------------------------

    def run(self, state: dict) -> AgentOutput:
        """
        Generate a literature review from the full corpus analysis.

        Leverages all prior agent outputs as context.
        """
        output: AgentOutput = super().run(state)

        return self._create_output(
            result=output.result,
            confidence=output.confidence,
            citations=output.citations,
            metadata={
                "model": self.model,
                "corpus_size": len(state.get("paper_texts", [])),
                "word_count_estimate": self._estimate_word_count(output.result),
            },
        )

    def build_prompt(self, state: dict) -> str:
        """Build a rich prompt with all available analysis context."""
        filenames = state.get("paper_filenames", [])

        # Build comprehensive context from all agent outputs
        context_parts: list[str] = []

        # --- Extraction data ---
        extractions = state.get("paper_metadata", [])
        if extractions:
            context_parts.append("## Extracted Metadata\n")
            for idx, meta in enumerate(extractions):
                if hasattr(meta, "dict"):
                    meta = meta.dict()
                fname = filenames[idx] if idx < len(filenames) else f"paper_{idx}"
                context_parts.append(
                    f"### {meta.get('title', fname)}\n"
                    f"- Authors: {', '.join(meta.get('authors', ['Unknown']))}\n"
                    f"- Year: {meta.get('publication_year', 'N/A')}\n"
                    f"- Venue: {meta.get('journal_or_venue', 'N/A')}\n"
                    f"- Field: {meta.get('research_field', 'N/A')}\n"
                    f"- Methodology: {meta.get('methodology', 'N/A')}\n"
                    f"- Keywords: {', '.join(meta.get('keywords', []))}\n"
                )

        # --- Quality assessments ---
        assessments = state.get("quality_assessments", [])
        if assessments:
            context_parts.append("\n## Quality Assessments\n")
            for idx, qa in enumerate(assessments):
                if hasattr(qa, "dict"):
                    qa = qa.dict()
                fname = filenames[idx] if idx < len(filenames) else f"paper_{idx}"
                context_parts.append(
                    f"- **{fname}**: Score {qa.get('overall_score', 'N/A')}/10 "
                    f"({qa.get('quality_level', 'N/A')}) | "
                    f"Strengths: {'; '.join(qa.get('strengths', [])[:2])} | "
                    f"Weaknesses: {'; '.join(qa.get('weaknesses', [])[:2])}\n"
                )

        # --- Summaries ---
        summaries = state.get("paper_summaries", [])
        if summaries:
            context_parts.append("\n## Paper Summaries\n")
            for idx, s in enumerate(summaries):
                if hasattr(s, "dict"):
                    s = s.dict()
                fname = filenames[idx] if idx < len(filenames) else f"paper_{idx}"
                context_parts.append(
                    f"**{fname}**: {s.get('one_line_summary', 'N/A')}\n"
                    f"- Methodology: {s.get('methodology_summary', 'N/A')}\n"
                    f"- Key takeaways: {'; '.join(s.get('key_takeaways', [])[:3])}\n"
                    f"- Tags: {', '.join(s.get('relevance_tags', []))}\n"
                )

        # --- Gap analysis ---
        gap_analysis = state.get("gap_analysis")
        if gap_analysis and hasattr(gap_analysis, "dict"):
            gap_data = gap_analysis.dict()
        elif gap_analysis and isinstance(gap_analysis, dict):
            gap_data = gap_analysis
        else:
            gap_data = None

        if gap_data:
            context_parts.append("\n## Gap Analysis\n")
            for g in gap_data.get("research_gaps", [])[:5]:
                context_parts.append(
                    f"- **Gap** ({g.get('priority', 'medium')}): {g.get('gap_description', '')}\n"
                    f"  Significance: {g.get('significance', '')}\n"
                )
            if gap_data.get("future_directions"):
                context_parts.append(
                    f"\n**Future Directions**: {'; '.join(gap_data['future_directions'][:5])}\n"
                )

        # --- Research question ---
        rq = state.get("research_question", "")
        rq_section = f"\n[RESEARCH QUESTION / FOCUS]\n{rq}\n" if rq else ""

        corpus_context = "\n".join(context_parts) if context_parts else "No structured context available."

        return f"""
[TASK]
{self._get_task_description()}
{rq_section}

[CORPUS SIZE]
{len(state.get('paper_texts', []))} papers

[AVAILABLE ANALYSIS]
{corpus_context}

[OUTPUT FORMAT]
{self._get_output_format()}

[CONSTRAINTS]
{self._get_constraints()}
"""

    # -- Helpers -------------------------------------------------------------

    def to_literature_review(self, data: dict) -> LiteratureReview:
        """Convert raw dict to validated LiteratureReview model."""
        return LiteratureReview(
            title=data.get("title", "Literature Review"),
            introduction=data.get("introduction", ""),
            thematic_sections=data.get("thematic_sections", []),
            synthesis=data.get("synthesis", ""),
            conclusion=data.get("conclusion", ""),
            bibliography=data.get("bibliography", []),
            total_papers_reviewed=data.get("total_papers_reviewed", 0),
        )

    def _estimate_word_count(self, result: dict) -> int:
        """Rough word count of the review body."""
        count = 0
        count += len(result.get("introduction", "").split())
        for section in result.get("thematic_sections", []):
            count += len(section.get("body", "").split())
        count += len(result.get("synthesis", "").split())
        count += len(result.get("conclusion", "").split())
        return count

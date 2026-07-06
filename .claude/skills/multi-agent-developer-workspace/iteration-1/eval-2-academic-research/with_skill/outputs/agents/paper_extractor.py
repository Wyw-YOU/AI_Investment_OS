"""
PaperExtractorAgent -- extracts structured metadata from academic papers.

Responsibilities:
    - Parse raw paper text to identify title, authors, abstract
    - Classify research field and methodology type
    - Extract keywords, publication year, venue
    - Identify key findings, contributions, and limitations
    - Count references and estimate citation patterns

This agent operates as the first node in the workflow -- it provides the
structured data that all downstream agents depend on.
"""

from __future__ import annotations

import json
from typing import Any

from base_agent import LLMAgent, AgentExecutionError
from models import (
    AgentOutput,
    PaperMetadata,
    KeyFindings,
    ResearchField,
    MethodologyType,
)


class PaperExtractorAgent(LLMAgent):
    """
    Specialised agent for extracting structured metadata from academic papers.

    Uses an LLM to parse free-form paper text and produce a validated
    PaperMetadata and KeyFindings structure.
    """

    name = "paper_extractor"
    description = (
        "Expert academic librarian and metadata specialist with deep experience "
        "in parsing, cataloguing, and structuring scientific literature across all "
        "disciplines. Skilled at identifying methodological patterns, extracting "
        "key findings, and classifying research contributions."
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(temperature=0.1, **kwargs)

    # -- Prompt engineering --------------------------------------------------

    def _get_system_prompt(self) -> str:
        return (
            "You are a world-class academic librarian and research metadata specialist.\n"
            "Your expertise spans all academic disciplines. You can read a research paper\n"
            "and accurately extract its structured metadata, classify its methodology,\n"
            "identify its key findings, and assess its structural completeness.\n\n"
            "You must always:\n"
            "- Respond with ONLY valid JSON matching the requested schema\n"
            "- Be precise with author names, titles, and years\n"
            "- Distinguish between primary and secondary findings\n"
            "- Note the methodology used by the authors\n"
            "- Extract self-reported limitations honestly\n"
            "- Provide a confidence score reflecting extraction certainty"
        )

    def _get_task_description(self) -> str:
        return """
Analyze the provided academic paper text and extract ALL of the following:

1. **Metadata Extraction**
   - Title (exact, as written in the paper)
   - Complete author list (with affiliations if available)
   - Abstract (full text)
   - Publication year
   - Journal or conference venue
   - DOI (if present)
   - Author-provided keywords

2. **Classification**
   - Primary research field (from: computer_science, physics, biology, chemistry,
     mathematics, engineering, medicine, social_science, economics, psychology,
     interdisciplinary, other)
   - Primary methodology (from: experimental, theoretical, computational, survey,
     case_study, meta_analysis, mixed_methods, review, qualitative, quantitative)

3. **Key Findings Extraction**
   - List the primary findings (the main results the paper reports)
   - List secondary/supporting findings
   - Statistical significance summary (if applicable)
   - Novel contributions claimed by the authors
   - Self-reported limitations

4. **Structural Analysis**
   - Number of references cited
   - Approximate paper length (in words)
   - Whether supplementary materials are mentioned
"""

    def _get_output_format(self) -> str:
        return """
Respond with ONLY valid JSON in this exact structure:

{
    "metadata": {
        "title": "Full Paper Title",
        "authors": ["Author One", "Author Two"],
        "abstract": "Full abstract text...",
        "publication_year": 2024,
        "journal_or_venue": "Nature / ICML / etc.",
        "doi": "10.xxxx/xxxxx",
        "keywords": ["keyword1", "keyword2"],
        "research_field": "computer_science",
        "methodology": "experimental",
        "citation_count": null,
        "references_count": 45
    },
    "findings": {
        "primary_findings": [
            "Finding 1: ...",
            "Finding 2: ..."
        ],
        "secondary_findings": [
            "Supporting finding 1..."
        ],
        "statistical_significance": "p < 0.05 for primary metrics...",
        "key_contributions": [
            "Contribution 1: ...",
            "Contribution 2: ..."
        ],
        "limitations": [
            "Limitation 1: ...",
            "Limitation 2: ..."
        ]
    },
    "confidence": 0.85,
    "citations": ["paper_title_or_doi"]
}
"""

    def _get_constraints(self) -> str:
        return """
- Extract information ONLY from the provided text. Do not hallucinate or infer
  information that is not explicitly stated.
- If a field cannot be determined, set it to null (do not guess).
- Preserve the original author spelling of names.
- Use the abstract verbatim; do not paraphrase it.
- Classify the methodology based on what the paper actually does, not what
  the authors claim (e.g., a paper calling itself 'experimental' that only
  presents simulations should be classified as 'computational').
- Confidence should reflect how clearly the information was present in the text
  (high if structured sections exist, lower if extraction required inference).
"""

    def _get_expected_output_keys(self) -> list[str]:
        return ["metadata", "findings", "confidence"]

    # -- Run with structured parsing -----------------------------------------

    def run(self, state: dict) -> AgentOutput:
        """
        Execute extraction for each paper in state['paper_texts'].

        Returns an AgentOutput whose result is a dict with keys:
            - papers: list of {metadata, findings} dicts
            - total_papers: int
        """
        paper_texts: list[str] = state.get("paper_texts", [])
        if not paper_texts:
            raise AgentExecutionError(
                self.name, "No paper texts provided in state"
            )

        all_results: list[dict] = []

        for idx, text in enumerate(paper_texts):
            # Inject single-paper context
            paper_state = {
                **state,
                "_current_paper_index": idx,
                "_current_paper_text": text,
            }
            agent_output: AgentOutput = super().run(paper_state)
            all_results.append(agent_output.result)

        # Aggregate
        aggregated = {
            "papers": all_results,
            "total_papers": len(all_results),
        }

        avg_confidence = (
            sum(r.get("confidence", 0.5) for r in all_results) / len(all_results)
            if all_results
            else 0.0
        )

        return self._create_output(
            result=aggregated,
            confidence=round(avg_confidence, 2),
            citations=self._collect_citations(all_results, state),
            metadata={
                "model": self.model,
                "papers_processed": len(all_results),
            },
        )

    def build_prompt(self, state: dict) -> str:
        """Override to inject the specific paper text being analysed."""
        idx = state.get("_current_paper_index", 0)
        paper_text = state.get("_current_paper_text", "")
        filename = state.get("paper_filenames", ["unknown"])[idx] if idx < len(state.get("paper_filenames", [])) else "unknown"

        # Truncate extremely long papers to fit context window
        max_chars = 50_000
        if len(paper_text) > max_chars:
            paper_text = paper_text[:max_chars] + "\n\n[... paper truncated due to length ...]"

        return f"""
[TASK]
{self._get_task_description()}

[PAPER]
Filename: {filename}
Paper Index: {idx + 1} of {state.get('paper_texts', [''])[0] and len(state.get('paper_texts', []))}

--- BEGIN PAPER TEXT ---
{paper_text}
--- END PAPER TEXT ---

[OUTPUT FORMAT]
{self._get_output_format()}

[CONSTRAINTS]
{self._get_constraints()}
"""

    # -- Post-processing helpers --------------------------------------------

    def _collect_citations(
        self, results: list[dict], state: dict
    ) -> list[str]:
        """Gather DOIs / titles from extracted papers as citations."""
        citations: list[str] = []
        for r in results:
            meta = r.get("metadata", {})
            if meta.get("doi"):
                citations.append(meta["doi"])
            elif meta.get("title"):
                citations.append(meta["title"])
        return citations

    def to_paper_metadata(self, extracted: dict) -> PaperMetadata:
        """Convert an extracted metadata dict to a validated PaperMetadata model."""
        meta = extracted.get("metadata", {})
        try:
            research_field = ResearchField(meta.get("research_field", "other"))
        except ValueError:
            research_field = ResearchField.OTHER
        try:
            methodology = MethodologyType(meta.get("methodology", "experimental"))
        except ValueError:
            methodology = MethodologyType.EXPERIMENTAL

        return PaperMetadata(
            title=meta.get("title", "Untitled"),
            authors=meta.get("authors", []),
            abstract=meta.get("abstract", ""),
            publication_year=meta.get("publication_year"),
            journal_or_venue=meta.get("journal_or_venue"),
            doi=meta.get("doi"),
            keywords=meta.get("keywords", []),
            research_field=research_field,
            methodology=methodology,
            citation_count=meta.get("citation_count"),
            references_count=meta.get("references_count"),
        )

    def to_key_findings(self, extracted: dict) -> KeyFindings:
        """Convert an extracted findings dict to a validated KeyFindings model."""
        findings = extracted.get("findings", {})
        return KeyFindings(
            primary_findings=findings.get("primary_findings", []),
            secondary_findings=findings.get("secondary_findings", []),
            statistical_significance=findings.get("statistical_significance"),
            key_contributions=findings.get("key_contributions", []),
            limitations=findings.get("limitations", []),
        )

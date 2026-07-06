"""
SummaryGeneratorAgent -- creates concise, structured summaries of papers.

Responsibilities:
    - Generate a one-sentence elevator summary
    - Write a detailed 2-3 paragraph summary
    - Summarize the methodology clearly
    - Extract 3-5 key takeaways
    - Tag the paper with relevant topic keywords

This agent runs after PaperExtractorAgent (and optionally QualityAnalyzerAgent)
so it has structured metadata and quality context to work with.
"""

from __future__ import annotations

from typing import Any

from base_agent import LLMAgent
from models import AgentOutput, PaperSummary


class SummaryGeneratorAgent(LLMAgent):
    """
    Specialised agent for generating clear, concise academic paper summaries.

    Writes for an audience of researchers who need to quickly understand
    what a paper does, how it does it, and why it matters.
    """

    name = "summary_generator"
    description = (
        "Expert science communicator and technical writer with extensive experience "
        "writing for academic audiences, research digests, and literature review "
        "services. Skilled at distilling complex research into accessible, accurate "
        "summaries that preserve nuance while maximising clarity."
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(temperature=0.4, **kwargs)

    # -- Prompt engineering --------------------------------------------------

    def _get_system_prompt(self) -> str:
        return (
            "You are an expert science communicator and technical writer.\n"
            "Your summaries are read by busy researchers who need to quickly\n"
            "decide whether a paper is relevant to their work.\n\n"
            "Your writing style:\n"
            "- Precise: every word earns its place\n"
            "- Accurate: faithfully represents the paper's actual contributions\n"
            "- Structured: follows a clear logical flow\n"
            "- Accessible: uses plain language where possible, technical terms only\n"
            "  when necessary (and defines them)\n"
            "- Balanced: presents findings without over-hyping or downplaying\n\n"
            "Always respond with ONLY valid JSON matching the requested schema."
        )

    def _get_task_description(self) -> str:
        return """
Generate a comprehensive summary of the research paper that includes:

1. **One-Line Summary** (Elevator Pitch)
   - Capture the essence of the paper in a single, clear sentence
   - Should answer: What was done? How? What was found?

2. **Detailed Summary** (2-3 paragraphs)
   - Paragraph 1: Problem statement and motivation -- why does this research matter?
   - Paragraph 2: Methodology and approach -- what did the authors do?
   - Paragraph 3: Key results and implications -- what did they find and why does it matter?
   - Write for a researcher in a related (but not identical) field

3. **Methodology Summary** (1-2 sentences)
   - Clearly describe the research method in plain language
   - Mention key techniques, datasets, or experimental setups

4. **Key Takeaways** (3-5 bullet points)
   - The most important points a reader should remember
   - Should be self-contained (understandable without reading the full paper)
   - Mix of findings, methods, and implications

5. **Relevance Tags** (3-7 tags)
   - Topic keywords that would help someone find this paper
   - Include both specific (e.g., "transformer architecture") and broad
     (e.g., "machine learning") tags
"""

    def _get_output_format(self) -> str:
        return """
Respond with ONLY valid JSON:

{
    "one_line_summary": "This paper proposes a novel attention mechanism for transformers that reduces computational complexity from O(n^2) to O(n log n) while maintaining accuracy on long-sequence benchmarks.",
    "detailed_summary": "The quadratic computational complexity of self-attention in transformer models has been a significant bottleneck for processing long sequences, limiting applications in areas such as document understanding and genomic analysis. This paper addresses this fundamental limitation by proposing a novel sparse attention mechanism that combines local windowed attention with a learned global token selection strategy. The approach reduces the theoretical complexity to O(n log n) while preserving the model's ability to capture long-range dependencies. The authors evaluate their method on the Long Range Arena benchmark and several real-world tasks including document classification and protein sequence modeling. Their method achieves comparable or superior accuracy to full attention while requiring up to 8x less memory and 5x less computation for sequences of length 8,192 tokens. The approach is also shown to be compatible with existing pre-trained transformer models through a straightforward fine-tuning procedure, making it practical for real-world deployment.",
    "methodology_summary": "The authors develop a hybrid sparse attention mechanism combining local sliding-window attention with learned global token selection, evaluated on the Long Range Arena benchmark suite and three real-world long-sequence tasks.",
    "key_takeaways": [
        "Self-attention's O(n^2) complexity can be reduced to O(n log n) using a hybrid local-global sparse pattern",
        "The proposed method matches full attention accuracy on 4 out of 5 Long Range Arena tasks",
        "Memory usage scales linearly instead of quadratically, enabling 8x longer sequences on the same hardware",
        "The sparse attention pattern can be applied to pre-trained models via fine-tuning with minimal accuracy loss",
        "Protein sequence modeling benefits particularly from the longer context window"
    ],
    "relevance_tags": [
        "transformer architecture",
        "sparse attention",
        "long-range dependencies",
        "computational efficiency",
        "sequence modeling",
        "machine learning"
    ],
    "confidence": 0.88,
    "citations": ["paper_title_or_doi"]
}
"""

    def _get_constraints(self) -> str:
        return """
- The one-line summary MUST be a single sentence (no more than 40 words).
- The detailed summary MUST be 2-3 paragraphs (200-400 words total).
- Key takeaways MUST be 3-5 items, each a single sentence.
- Relevance tags MUST be 3-7 lowercase terms or phrases.
- Do NOT include opinions, evaluations, or judgments -- only report what
  the paper states and demonstrates.
- If the paper is outside your training domain, acknowledge uncertainty
  and lower your confidence score accordingly.
- Use past tense for completed experiments, present tense for general claims.
"""

    def _get_expected_output_keys(self) -> list[str]:
        return [
            "one_line_summary",
            "detailed_summary",
            "methodology_summary",
            "key_takeaways",
            "relevance_tags",
        ]

    # -- Run for all papers --------------------------------------------------

    def run(self, state: dict) -> AgentOutput:
        """
        Generate summaries for each paper in state['paper_texts'].

        Returns AgentOutput with result['summaries'] = list of summary dicts.
        """
        paper_texts: list[str] = state.get("paper_texts", [])
        if not paper_texts:
            return self._create_output(
                result={"summaries": [], "total_summarized": 0},
                confidence=0.0,
                citations=[],
            )

        summaries: list[dict] = []
        for idx, text in enumerate(paper_texts):
            paper_state = {
                **state,
                "_current_paper_index": idx,
                "_current_paper_text": text,
            }
            output: AgentOutput = super().run(paper_state)
            summaries.append(output.result)

        avg_conf = (
            sum(s.get("confidence", 0.5) for s in summaries) / len(summaries)
            if summaries
            else 0.0
        )

        return self._create_output(
            result={
                "summaries": summaries,
                "total_summarized": len(summaries),
            },
            confidence=round(avg_conf, 2),
            citations=self._gather_citations(summaries),
            metadata={"model": self.model, "papers_summarized": len(summaries)},
        )

    def build_prompt(self, state: dict) -> str:
        """Override to inject paper text and any prior extraction context."""
        idx = state.get("_current_paper_index", 0)
        paper_text = state.get("_current_paper_text", "")
        filenames = state.get("paper_filenames", ["unknown"])
        filename = filenames[idx] if idx < len(filenames) else "unknown"

        # Include extraction metadata if available
        extraction_ctx = ""
        extractions = state.get("paper_metadata", [])
        if extractions and idx < len(extractions):
            meta = extractions[idx]
            if hasattr(meta, "dict"):
                meta = meta.dict()
            extraction_ctx = f"\n[EXTRACTED METADATA]\nTitle: {meta.get('title', 'N/A')}\nAuthors: {', '.join(meta.get('authors', []))}\nAbstract: {meta.get('abstract', 'N/A')}\n"

        # Include quality assessment if available
        quality_ctx = ""
        assessments = state.get("quality_assessments", [])
        if assessments and idx < len(assessments):
            qa = assessments[idx]
            if hasattr(qa, "dict"):
                qa = qa.dict()
            quality_ctx = f"\n[QUALITY ASSESSMENT]\nOverall Score: {qa.get('overall_score', 'N/A')}/10\nStrengths: {', '.join(qa.get('strengths', []))}\nWeaknesses: {', '.join(qa.get('weaknesses', []))}\n"

        max_chars = 40_000
        if len(paper_text) > max_chars:
            paper_text = paper_text[:max_chars] + "\n\n[... truncated ...]"

        return f"""
[TASK]
{self._get_task_description()}
{extraction_ctx}{quality_ctx}

[PAPER]
Filename: {filename}
Paper Index: {idx + 1} of {len(state.get('paper_texts', []))}

--- BEGIN PAPER TEXT ---
{paper_text}
--- END PAPER TEXT ---

[OUTPUT FORMAT]
{self._get_output_format()}

[CONSTRAINTS]
{self._get_constraints()}
"""

    # -- Helpers -------------------------------------------------------------

    def to_paper_summary(self, data: dict) -> PaperSummary:
        """Convert raw summary dict to validated PaperSummary model."""
        return PaperSummary(
            one_line_summary=data.get("one_line_summary", ""),
            detailed_summary=data.get("detailed_summary", ""),
            methodology_summary=data.get("methodology_summary", ""),
            key_takeaways=data.get("key_takeaways", []),
            relevance_tags=data.get("relevance_tags", []),
        )

    def _gather_citations(self, summaries: list[dict]) -> list[str]:
        citations: list[str] = []
        for s in summaries:
            if "citations" in s:
                citations.extend(s["citations"])
        return list(set(citations))

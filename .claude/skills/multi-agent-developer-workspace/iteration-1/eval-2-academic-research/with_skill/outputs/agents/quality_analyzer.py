"""
QualityAnalyzerAgent -- assesses research rigor, novelty, and impact.

Responsibilities:
    - Score the paper across multiple quality dimensions:
        * Methodological rigor
        * Novelty / originality
        * Significance / impact
        * Clarity / presentation
        * Reproducibility
        * Literature coverage
    - Identify strengths and weaknesses
    - Provide an overall quality level (exceptional through poor)
    - Make a recommendation (accept / minor revisions / major revisions / reject)

This agent runs after PaperExtractorAgent and uses its structured output
as context.
"""

from __future__ import annotations

from typing import Any

from base_agent import LLMAgent
from models import AgentOutput, QualityAssessment, QualityDimension, QualityLevel


class QualityAnalyzerAgent(LLMAgent):
    """
    Specialised agent for assessing the quality of academic research.

    Emulates the critical eye of a seasoned peer reviewer, evaluating
    methodological soundness, novelty, and potential impact.
    """

    name = "quality_analyzer"
    description = (
        "Distinguished professor and veteran peer reviewer with 25+ years of "
        "experience reviewing for top-tier journals (Nature, Science, PNAS, "
        "IEEE, ACM). Expert in evaluating methodological rigor, statistical "
        "validity, novelty of contributions, and potential scholarly impact."
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(temperature=0.2, **kwargs)

    # -- Prompt engineering --------------------------------------------------

    def _get_system_prompt(self) -> str:
        return (
            "You are a distinguished professor and veteran peer reviewer.\n"
            "You have reviewed thousands of papers for top-tier journals and\n"
            "conferences across multiple disciplines. Your evaluations are\n"
            "known for being thorough, fair, and constructive.\n\n"
            "When evaluating a paper you:\n"
            "- Assess methodology against best practices in the field\n"
            "- Check statistical validity and experimental design\n"
            "- Evaluate novelty relative to existing literature\n"
            "- Consider potential impact and significance\n"
            "- Note clarity, organization, and writing quality\n"
            "- Identify both strengths and areas for improvement\n"
            "- Provide actionable feedback\n\n"
            "Always respond with ONLY valid JSON matching the requested schema."
        )

    def _get_task_description(self) -> str:
        return """
Perform a comprehensive quality assessment of the research paper, evaluating
each of the following dimensions on a 0-10 scale (10 = best):

1. **Methodological Rigor** (weight: 25%)
   - Is the research design appropriate for the research question?
   - Are the methods described in sufficient detail for replication?
   - Are statistical tests appropriate and correctly applied?
   - Are threats to validity addressed?
   - Is the sample size adequate?

2. **Novelty / Originality** (weight: 20%)
   - Does the paper make a genuinely new contribution?
   - How does it advance beyond existing work?
   - Is the novelty incremental or transformative?
   - Does it introduce new methods, theories, or applications?

3. **Significance / Impact** (weight: 20%)
   - How important is the research question?
   - What is the potential impact on the field?
   - Could the findings influence practice or policy?
   - Is the work likely to be cited and built upon?

4. **Clarity / Presentation** (weight: 15%)
   - Is the paper well-organized and clearly written?
   - Are figures and tables effective?
   - Is the narrative logical and easy to follow?
   - Are technical terms well-defined?

5. **Reproducibility** (weight: 10%)
   - Could another researcher replicate this work?
   - Are datasets, code, or materials made available?
   - Are parameters and hyper-parameters reported?

6. **Literature Coverage** (weight: 10%)
   - Is the related work section comprehensive?
   - Are relevant seminal papers cited?
   - Does the paper position itself within the broader field?

Provide:
- Individual dimension scores with justifications
- An overall weighted quality score
- A discrete quality level (exceptional, high, good, moderate, low, poor)
- A list of key strengths
- A list of key weaknesses
- A publication recommendation (accept, minor_revisions, major_revisions, reject)
"""

    def _get_output_format(self) -> str:
        return """
Respond with ONLY valid JSON:

{
    "overall_score": 7.5,
    "quality_level": "high",
    "dimensions": [
        {
            "dimension_name": "methodological_rigor",
            "score": 8.0,
            "justification": "The experimental design is well-structured..."
        },
        {
            "dimension_name": "novelty",
            "score": 7.0,
            "justification": "The paper introduces a novel approach to..."
        },
        {
            "dimension_name": "significance",
            "score": 7.5,
            "justification": "The findings have implications for..."
        },
        {
            "dimension_name": "clarity",
            "score": 8.0,
            "justification": "The paper is well-written and organized..."
        },
        {
            "dimension_name": "reproducibility",
            "score": 6.0,
            "justification": "Code availability is mentioned but..."
        },
        {
            "dimension_name": "literature_coverage",
            "score": 7.5,
            "justification": "The related work section covers..."
        }
    ],
    "novelty_score": 7.0,
    "rigor_score": 8.0,
    "impact_score": 7.5,
    "clarity_score": 8.0,
    "strengths": [
        "Well-designed experiment with proper controls",
        "Large and diverse dataset"
    ],
    "weaknesses": [
        "Limited evaluation on out-of-distribution data",
        "No comparison with very recent SOTA methods"
    ],
    "recommendation": "minor_revisions",
    "confidence": 0.82,
    "citations": ["paper_title_or_doi"]
}
"""

    def _get_constraints(self) -> str:
        return """
- Evaluate ONLY based on the information provided. Do not introduce external
  knowledge about the authors or venue.
- Each dimension score MUST be between 0 and 10 (inclusive), using 0.5 increments.
- The overall_score should be the weighted average using the weights provided.
- Be constructive: weaknesses should suggest how to improve, not just criticize.
- The quality_level MUST be one of: exceptional (9-10), high (7.5-8.9),
  good (6-7.4), moderate (4-5.9), low (2-3.9), poor (0-1.9).
- Confidence should reflect how confidently you can assess based on the
  information provided (e.g., lower if the paper text is partial/truncated).
"""

    def _get_expected_output_keys(self) -> list[str]:
        return [
            "overall_score",
            "quality_level",
            "dimensions",
            "novelty_score",
            "rigor_score",
            "impact_score",
            "strengths",
            "weaknesses",
            "recommendation",
        ]

    # -- Run for all papers in the corpus ------------------------------------

    def run(self, state: dict) -> AgentOutput:
        """
        Run quality analysis for each paper whose metadata is available.

        Expects state['paper_texts'] and state['paper_metadata'] (list).
        Returns AgentOutput with result['assessments'] = list of quality dicts.
        """
        paper_texts: list[str] = state.get("paper_texts", [])
        if not paper_texts:
            return self._create_output(
                result={"assessments": [], "total_assessed": 0},
                confidence=0.0,
                citations=[],
            )

        assessments: list[dict] = []
        for idx, text in enumerate(paper_texts):
            paper_state = {
                **state,
                "_current_paper_index": idx,
                "_current_paper_text": text,
            }
            output: AgentOutput = super().run(paper_state)
            assessments.append(output.result)

        avg_conf = (
            sum(a.get("confidence", 0.5) for a in assessments) / len(assessments)
            if assessments
            else 0.0
        )

        return self._create_output(
            result={
                "assessments": assessments,
                "total_assessed": len(assessments),
                "average_overall_score": round(
                    sum(a.get("overall_score", 0) for a in assessments)
                    / max(len(assessments), 1),
                    2,
                ),
            },
            confidence=round(avg_conf, 2),
            citations=self._extract_citations(assessments, state),
            metadata={"model": self.model, "papers_assessed": len(assessments)},
        )

    def build_prompt(self, state: dict) -> str:
        """Override to inject paper text + extracted metadata as context."""
        idx = state.get("_current_paper_index", 0)
        paper_text = state.get("_current_paper_text", "")
        filenames = state.get("paper_filenames", ["unknown"])
        filename = filenames[idx] if idx < len(filenames) else "unknown"

        # If extraction results are available, include them as context
        extraction_context = ""
        extractions = state.get("paper_metadata", [])
        if extractions and idx < len(extractions):
            meta = extractions[idx] if isinstance(extractions[idx], dict) else extractions[idx].dict() if hasattr(extractions[idx], "dict") else {}
            extraction_context = f"\n[EXTRACTED METADATA]\n{meta}\n"

        max_chars = 40_000
        if len(paper_text) > max_chars:
            paper_text = paper_text[:max_chars] + "\n\n[... truncated ...]"

        return f"""
[TASK]
{self._get_task_description()}
{extraction_context}

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

    def to_quality_assessment(self, data: dict) -> QualityAssessment:
        """Convert raw assessment dict to validated QualityAssessment model."""
        dimensions = [
            QualityDimension(
                dimension_name=d.get("dimension_name", "unknown"),
                score=d.get("score", 0),
                justification=d.get("justification", ""),
            )
            for d in data.get("dimensions", [])
        ]

        try:
            quality_level = QualityLevel(data.get("quality_level", "moderate"))
        except ValueError:
            quality_level = QualityLevel.MODERATE

        return QualityAssessment(
            overall_score=data.get("overall_score", 0),
            quality_level=quality_level,
            dimensions=dimensions,
            novelty_score=data.get("novelty_score", 0),
            rigor_score=data.get("rigor_score", 0),
            impact_score=data.get("impact_score", 0),
            clarity_score=data.get("clarity_score", 0),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            recommendation=data.get("recommendation", ""),
        )

    def _extract_citations(
        self, assessments: list[dict], state: dict
    ) -> list[str]:
        """Collect citations from assessment results."""
        citations: list[str] = []
        for a in assessments:
            if "citations" in a:
                citations.extend(a["citations"])
        return list(set(citations))

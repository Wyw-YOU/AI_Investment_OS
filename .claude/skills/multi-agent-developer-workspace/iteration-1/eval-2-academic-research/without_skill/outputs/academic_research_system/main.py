"""
Main entry point for the Academic Research Multi-Agent System.

Provides both CLI and programmatic interfaces for running paper analysis.
Includes example usage with sample paper text for demonstration.

Usage:
    # Programmatic
    python -m academic_research_system.main

    # As a library
    from academic_research_system.main import AcademicResearchPipeline
    pipeline = AcademicResearchPipeline(llm=my_llm)
    results = await pipeline.analyze(papers, topic, focus)
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from academic_research_system.workflow import run_workflow, build_academic_research_workflow
from academic_research_system.state import (
    AcademicResearchState,
    ProcessedPaper,
    ExtractedPaper,
    QualityAssessment,
    PaperSummary,
    GapAnalysis,
    LiteratureReview,
)

logger = logging.getLogger("academic_research")


# ===========================================================================
# Pipeline Class (Primary API)
# ===========================================================================

class AcademicResearchPipeline:
    """
    High-level API for the Academic Research Multi-Agent System.

    Example usage:
        from langchain_openai import ChatOpenAI
        from academic_research_system.main import AcademicResearchPipeline

        llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
        pipeline = AcademicResearchPipeline(llm=llm)

        results = await pipeline.analyze(
            paper_texts=[paper1_text, paper2_text, ...],
            research_topic="Large Language Models in Education",
            review_focus="Effectiveness of LLM-based tutoring systems",
        )

        # Access results
        print(results["literature_review"]["executive_summary"])
        for gap in results["gap_analysis"]["research_gaps"]:
            print(f"  Gap: {gap['gap_title']} (Priority: {gap['priority']})")
    """

    def __init__(self, llm: Any, config: dict[str, Any] | None = None):
        """
        Args:
            llm: Language model instance (e.g., ChatOpenAI, ChatAnthropic, ChatOllama).
            config: Optional configuration overrides.
        """
        self.llm = llm
        self.config = config or {}

    async def analyze(
        self,
        paper_texts: list[str],
        research_topic: str,
        review_focus: str,
        user_instructions: str = "",
    ) -> dict[str, Any]:
        """
        Run the complete analysis pipeline.

        Args:
            paper_texts: List of raw paper texts.
            research_topic: The overarching research topic.
            review_focus: Specific focus for analysis.
            user_instructions: Optional additional instructions.

        Returns:
            Complete workflow results dictionary.
        """
        return await run_workflow(
            paper_texts=paper_texts,
            research_topic=research_topic,
            review_focus=review_focus,
            llm=self.llm,
            user_instructions=user_instructions,
            config=self.config,
        )

    def analyze_sync(
        self,
        paper_texts: list[str],
        research_topic: str,
        review_focus: str,
        user_instructions: str = "",
    ) -> dict[str, Any]:
        """Synchronous wrapper around the async analyze method."""
        return asyncio.run(self.analyze(
            paper_texts=paper_texts,
            research_topic=research_topic,
            review_focus=review_focus,
            user_instructions=user_instructions,
        ))

    def get_paper_analyses(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract individual paper analyses from workflow results."""
        return results.get("processed_papers", [])

    def get_literature_review(self, results: dict[str, Any]) -> dict[str, Any] | None:
        """Extract the literature review from workflow results."""
        return results.get("literature_review")

    def get_gap_analysis(self, results: dict[str, Any]) -> dict[str, Any] | None:
        """Extract the gap analysis from workflow results."""
        return results.get("gap_analysis")

    def get_errors(self, results: dict[str, Any]) -> list[str]:
        """Extract any errors from workflow results."""
        return results.get("errors", [])


# ===========================================================================
# Result Formatter
# ===========================================================================

class ResultFormatter:
    """Formats workflow results for display or export."""

    @staticmethod
    def to_markdown_report(results: dict[str, Any]) -> str:
        """Generate a complete Markdown report from workflow results."""
        parts = []
        parts.append("# Academic Research Analysis Report\n")

        # Executive Summary from Literature Review
        lit_review = results.get("literature_review")
        if lit_review:
            parts.append(f"## {lit_review.get('title', 'Literature Review')}\n")
            parts.append(f"### Executive Summary\n{lit_review.get('executive_summary', '')}\n")

        # Individual Paper Summaries
        papers = results.get("processed_papers", [])
        if papers:
            parts.append("## Individual Paper Analyses\n")
            for i, paper in enumerate(papers, 1):
                extraction = paper.get("extraction", {})
                quality = paper.get("quality", {})
                summary = paper.get("summary", {})

                parts.append(f"### Paper {i}: {extraction.get('title', 'Unknown')}\n")
                if summary.get("one_sentence_summary"):
                    parts.append(f"**Summary:** {summary['one_sentence_summary']}\n")
                if quality.get("overall_quality_score"):
                    parts.append(f"**Quality Score:** {quality['overall_quality_score']}/10\n")
                if quality.get("novelty_level"):
                    parts.append(f"**Novelty:** {quality['novelty_level']}\n")

                if summary.get("key_contributions"):
                    parts.append("**Key Contributions:**")
                    for contrib in summary["key_contributions"]:
                        parts.append(f"- {contrib}")
                    parts.append("")

                if quality.get("strengths"):
                    parts.append("**Strengths:**")
                    for s in quality["strengths"]:
                        parts.append(f"- {s}")
                    parts.append("")

                if quality.get("weaknesses"):
                    parts.append("**Weaknesses:**")
                    for w in quality["weaknesses"]:
                        parts.append(f"- {w}")
                    parts.append("")

        # Full Literature Review
        if lit_review:
            parts.append("## Literature Review\n")
            if lit_review.get("introduction"):
                parts.append(f"### Introduction\n{lit_review['introduction']}\n")

            if lit_review.get("thematic_analysis"):
                parts.append("### Thematic Analysis\n")
                for theme, analysis in lit_review["thematic_analysis"].items():
                    parts.append(f"#### {theme}\n{analysis}\n")

            if lit_review.get("methodology_comparison"):
                parts.append(f"### Methodology Comparison\n{lit_review['methodology_comparison']}\n")

            if lit_review.get("findings_synthesis"):
                parts.append(f"### Findings Synthesis\n{lit_review['findings_synthesis']}\n")

            if lit_review.get("contradictions_and_debates"):
                parts.append(f"### Contradictions and Debates\n{lit_review['contradictions_and_debates']}\n")

            if lit_review.get("conclusion"):
                parts.append(f"### Conclusion\n{lit_review['conclusion']}\n")

            if lit_review.get("research_agenda"):
                parts.append(f"### Research Agenda\n{lit_review['research_agenda']}\n")

            if lit_review.get("bibliography"):
                parts.append("### Bibliography\n")
                for ref in lit_review["bibliography"]:
                    parts.append(f"- {ref}")
                parts.append("")

        # Gap Analysis
        gap_analysis = results.get("gap_analysis")
        if gap_analysis:
            parts.append("## Research Gaps and Future Directions\n")

            if gap_analysis.get("overarching_themes"):
                parts.append("### Overarching Themes\n")
                for theme in gap_analysis["overarching_themes"]:
                    parts.append(f"- {theme}")
                parts.append("")

            if gap_analysis.get("research_gaps"):
                parts.append("### Identified Research Gaps\n")
                for gap in gap_analysis["research_gaps"]:
                    parts.append(f"#### {gap.get('gap_title', 'Untitled Gap')} (Priority: {gap.get('priority', '?')})\n")
                    parts.append(f"{gap.get('gap_description', '')}\n")
                    if gap.get("suggested_approach"):
                        parts.append(f"**Suggested Approach:** {gap['suggested_approach']}\n")
                    if gap.get("potential_impact"):
                        parts.append(f"**Potential Impact:** {gap['potential_impact']}\n")

            if gap_analysis.get("future_directions"):
                parts.append("### Future Research Directions\n")
                for fd in gap_analysis["future_directions"]:
                    parts.append(f"#### {fd.get('title', 'Untitled')} ({fd.get('timeframe', '?')})\n")
                    parts.append(f"{fd.get('description', '')}\n")
                    if fd.get("suggested_methodology"):
                        parts.append(f"**Suggested Methodology:** {fd['suggested_methodology']}\n")

            for lf_key, lf_label in [
                ("methodology_gaps", "Methodology Gaps"),
                ("theoretical_gaps", "Theoretical Gaps"),
                ("empirical_gaps", "Empirical Gaps"),
            ]:
                items = gap_analysis.get(lf_key, [])
                if items:
                    parts.append(f"### {lf_label}\n")
                    for item in items:
                        parts.append(f"- {item}")
                    parts.append("")

        # Processing Metadata
        errors = results.get("errors", [])
        if errors:
            parts.append("## Errors and Warnings\n")
            for err in errors:
                parts.append(f"- {err}")
            parts.append("")

        return "\n".join(parts)

    @staticmethod
    def to_json(results: dict[str, Any], indent: int = 2) -> str:
        """Export results as formatted JSON."""
        # Remove internal state fields
        export = {k: v for k, v in results.items() if not k.startswith("_")}
        return json.dumps(export, indent=indent, ensure_ascii=False, default=str)


# ===========================================================================
# CLI Entry Point
# ===========================================================================

SAMPLE_PAPERS = [
    """Title: Attention Is All You Need
Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin
Year: 2017
Abstract: The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train. Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation task, improving over the existing best results, including ensembles by over 2 BLEU. On the WMT 2014 English-to-French translation task, our model establishes a new single-model state-of-the-art BLEU score of 41.0 after training for 3.5 days on eight GPUs, a small fraction of the training costs of the best models from the literature. We show that the Transformer generalizes well to other tasks by applying it successfully to English constituency parsing both with large and limited training data.
Methodology: Experimental. We propose the Transformer architecture that relies entirely on self-attention mechanisms. We train on standard WMT 2014 English-German and English-French benchmarks and evaluate using BLEU scores.
Key Findings: The Transformer achieves 28.4 BLEU on English-to-German, surpassing previous best by 2+ BLEU. On English-to-French, it achieves 41.0 BLEU as a single model. Training takes only 3.5 days on 8 GPUs, significantly less than prior models. The architecture generalizes well to English constituency parsing.""",
    """Title: BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
Authors: Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova
Year: 2019
Abstract: We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without substantial task-specific architecture modifications. BERT is conceptually simple and empirically powerful. It obtains new state-of-the-art results on eleven natural language processing benchmarks, including pushing the GLUE score to 80.5% (7.7% point absolute improvement), MultiNLI accuracy to 86.7% (4.6% absolute improvement), SQuAD v1.1 question answering Test F1 to 93.2 (1.5 point absolute improvement) and SQuAD v2.0 Test F1 to 83.1 (5.1 point absolute improvement).
Methodology: Experimental. We use a multi-layer bidirectional Transformer encoder and pre-train using Masked Language Model (MLM) and Next Sentence Prediction (NSP) objectives on BooksCorpus and English Wikipedia. Fine-tuning is performed on downstream tasks.
Key Findings: BERT achieves state-of-the-art on 11 NLP benchmarks. GLUE score of 80.5% (7.7% absolute improvement). SQuAD v1.1 F1 of 93.2. The bidirectional pre-training approach significantly outperforms left-to-right or shallow bidirectional models. Fine-tuning is more effective than feature-based approaches for most tasks.""",
    """Title: Language Models are Few-Shot Learners (GPT-3)
Authors: Tom Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, et al.
Year: 2020
Abstract: Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task. We show that scaling up language models greatly improves task-agnostic, few-shot performance, sometimes even reaching competitiveness with prior state-of-the-art fine-tuning approaches. Specifically, we train GPT-3, an autoregressive language model with 175 billion parameters, 10x more than any previous non-sparse language model, and test its performance in the few-shot setting. For all tasks, GPT-3 is applied without any gradient updates or fine-tuning, with tasks and few-shot demonstrations specified purely via text interaction with the model. GPT-3 achieves strong performance on many NLP datasets, including translation, question-answering, and cloze tasks, as well as several tasks that require on-the-fly reasoning or domain adaptation, such as unscrambling words, using a novel word in a sentence, or performing 3-digit arithmetic.
Methodology: Experimental. We train a 175 billion parameter autoregressive language model and evaluate in zero-shot, one-shot, and few-shot settings without any gradient updates or fine-tuning. Evaluation covers over 40 NLP benchmarks.
Key Findings: GPT-3 achieves strong few-shot performance across many NLP tasks without task-specific fine-tuning. Performance improves log-linearly with model size. Few-shot performance approaches that of state-of-the-art fine-tuned models on some benchmarks. The model demonstrates emergent capabilities like arithmetic and word unscrambling at scale. Limitations include difficulty with some reasoning tasks and repetitive text generation.""",
]


async def main():
    """CLI entry point demonstrating the full pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Academic Research Multi-Agent System")
    parser.add_argument("--topic", type=str, default="Transformer Models in NLP", help="Research topic")
    parser.add_argument("--focus", type=str, default="Architectural innovations and scaling", help="Review focus")
    parser.add_argument("--model", type=str, default="gpt-4o", help="LLM model name")
    parser.add_argument("--provider", type=str, default="openai", choices=["openai", "anthropic", "ollama"])
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    # Initialize LLM based on provider
    if args.provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=args.model, temperature=0.0)
    elif args.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=args.model, temperature=0.0)
    elif args.provider == "ollama":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=args.model, temperature=0.0)
    else:
        raise ValueError(f"Unknown provider: {args.provider}")

    # Use sample papers for demonstration
    paper_texts = SAMPLE_PAPERS
    logger.info("Running pipeline with %d sample papers", len(paper_texts))

    pipeline = AcademicResearchPipeline(llm=llm)
    results = await pipeline.analyze(
        paper_texts=paper_texts,
        research_topic=args.topic,
        review_focus=args.focus,
    )

    # Format and output results
    markdown_report = ResultFormatter.to_markdown_report(results)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(markdown_report, encoding="utf-8")
        logger.info("Report written to: %s", output_path)
    else:
        print("\n" + "=" * 80)
        print(markdown_report)
        print("=" * 80)

    # Print summary statistics
    papers = results.get("processed_papers", [])
    successful = sum(1 for p in papers if p.get("stage") == "summarized")
    errors = results.get("errors", [])
    print(f"\nPipeline Summary:")
    print(f"  Papers processed: {successful}/{len(papers)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Gap analysis: {'Complete' if results.get('gap_analysis') else 'Failed'}")
    print(f"  Literature review: {'Complete' if results.get('literature_review') else 'Failed'}")


if __name__ == "__main__":
    asyncio.run(main())

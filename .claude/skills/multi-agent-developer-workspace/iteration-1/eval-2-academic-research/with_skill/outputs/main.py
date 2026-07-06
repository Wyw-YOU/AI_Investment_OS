"""
Main entry point for the Multi-Agent Academic Research System.

Provides the high-level AcademicResearchSystem class and a demo
showing how to use the system to analyse papers.

Usage:
    # As a library
    from main import AcademicResearchSystem

    system = AcademicResearchSystem(api_key="your-openai-api-key")
    result = system.analyze_corpus(
        paper_texts=[paper1_text, paper2_text, paper3_text],
        paper_filenames=["paper1.pdf", "paper2.pdf", "paper3.pdf"],
        research_question="What are the latest advances in efficient transformers?",
    )
    print(result["literature_review"])

    # From command line
    python main.py --papers paper1.txt paper2.txt paper3.txt --question "..."
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

from models import (
    AcademicResearchState,
    WorkflowPhase,
    PaperMetadata,
    QualityAssessment,
    PaperSummary,
    GapAnalysisResult,
    LiteratureReview,
)
from state_manager import AcademicResearchStateManager, FileStatePersistence
from workflow import AcademicResearchWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("academic_research")


# ---------------------------------------------------------------------------
# Main System Class
# ---------------------------------------------------------------------------

class AcademicResearchSystem:
    """
    High-level facade for the Multi-Agent Academic Research System.

    Encapsulates the full pipeline:
        1. Paper extraction (metadata, findings)
        2. Quality analysis (rigor, novelty, impact)
        3. Summary generation (concise, structured)
        4. Gap identification (research opportunities)
        5. Literature review synthesis

    Args:
        api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        model: LLM model to use (default: gpt-4)
        state_dir: Directory for state persistence (default: ./state_store)
        verbose: Enable verbose logging (default: True)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        state_dir: str = "./state_store",
        verbose: bool = True,
    ) -> None:
        # Set API key
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        self.model = model

        # Set up logging level
        if not verbose:
            logging.getLogger().setLevel(logging.WARNING)

        # State management
        self.persistence = FileStatePersistence(base_path=state_dir)
        self.state_manager = AcademicResearchStateManager(
            persistence=self.persistence,
        )

        # Workflow
        self._workflow = AcademicResearchWorkflow(
            state_manager=self.state_manager,
        )

        logger.info("AcademicResearchSystem initialised (model=%s)", model)

    # -- Public API ----------------------------------------------------------

    def analyze_paper(
        self,
        paper_text: str,
        paper_filename: str = "paper.txt",
        research_question: str = "",
    ) -> dict[str, Any]:
        """
        Analyse a single academic paper.

        Runs the full pipeline: extraction -> quality -> summary -> gaps -> review.

        Args:
            paper_text: Full text of the paper
            paper_filename: Original filename
            research_question: Optional focus question

        Returns:
            Dict with all analysis results
        """
        return self._workflow.run_single_paper(
            paper_text=paper_text,
            paper_filename=paper_filename,
            research_question=research_question,
        )

    def analyze_corpus(
        self,
        paper_texts: list[str],
        paper_filenames: Optional[list[str]] = None,
        research_question: str = "",
    ) -> dict[str, Any]:
        """
        Analyse a corpus of multiple academic papers.

        Runs the full pipeline with parallel analysis and corpus-level synthesis.

        Args:
            paper_texts: List of full paper texts
            paper_filenames: Optional list of filenames
            research_question: Optional research question to focus analysis

        Returns:
            Dict with all analysis results including cross-paper synthesis
        """
        return self._workflow.run(
            paper_texts=paper_texts,
            paper_filenames=paper_filenames,
            research_question=research_question,
        )

    def load_previous_analysis(self, task_id: str) -> Optional[dict[str, Any]]:
        """Load a previous analysis by task_id."""
        state = self.state_manager.load_state(task_id)
        if state:
            return json.loads(state.json())
        return None

    def get_workflow_diagram(self) -> str:
        """Get a Mermaid diagram of the workflow."""
        return self._workflow.get_workflow_graph()

    # -- Utility methods for converting raw results to Pydantic models -------

    @staticmethod
    def to_paper_metadata_list(extraction_results: list[dict]) -> list[PaperMetadata]:
        """Convert extraction results to validated PaperMetadata models."""
        from agents.paper_extractor import PaperExtractorAgent
        agent = PaperExtractorAgent()
        return [agent.to_paper_metadata(r) for r in extraction_results]

    @staticmethod
    def to_quality_assessments(quality_results: list[dict]) -> list[QualityAssessment]:
        """Convert quality results to validated QualityAssessment models."""
        from agents.quality_analyzer import QualityAnalyzerAgent
        agent = QualityAnalyzerAgent()
        return [agent.to_quality_assessment(r) for r in quality_results]

    @staticmethod
    def to_paper_summaries(summary_results: list[dict]) -> list[PaperSummary]:
        """Convert summary results to validated PaperSummary models."""
        from agents.summary_generator import SummaryGeneratorAgent
        agent = SummaryGeneratorAgent()
        return [agent.to_paper_summary(r) for r in summary_results]

    @staticmethod
    def to_gap_analysis(gap_result: dict) -> GapAnalysisResult:
        """Convert gap analysis result to validated GapAnalysisResult model."""
        from agents.gap_analyzer import GapAnalyzerAgent
        agent = GapAnalyzerAgent()
        return agent.to_gap_analysis_result(gap_result)

    @staticmethod
    def to_literature_review(review_result: dict) -> LiteratureReview:
        """Convert literature review result to validated LiteratureReview model."""
        from agents.literature_review import LiteratureReviewAgent
        agent = LiteratureReviewAgent()
        return agent.to_literature_review(review_result)


# ---------------------------------------------------------------------------
# Demo with Sample Papers
# ---------------------------------------------------------------------------

def demo_analysis() -> dict[str, Any]:
    """
    Run a demo analysis with sample paper texts.

    This demonstrates the full workflow using synthetic paper data.
    In production, replace with actual paper text (e.g., from PDF extraction).
    """

    sample_papers = [
        """
Title: Efficient Transformers via Sparse Attention Patterns

Authors: John Smith, Alice Johnson, Bob Williams
Published: ICML 2024

Abstract:
The quadratic computational complexity of self-attention in transformer models
limits their application to long sequences. We propose SparseFormer, a novel
sparse attention mechanism that combines local windowed attention with learned
global token selection. Our approach reduces complexity from O(n^2) to O(n log n)
while maintaining 98% of full-attention accuracy on the Long Range Arena benchmark.
We demonstrate state-of-the-art results on document classification, protein
sequence modeling, and code generation tasks with sequences up to 32K tokens.

1. Introduction
Transformers have become the dominant architecture for sequence modeling...
However, the self-attention mechanism has quadratic complexity O(n^2)...

2. Method
Our SparseFormer architecture uses a two-level attention pattern:
- Local attention: Each token attends to its w nearest neighbors (O(n*w))
- Global attention: A learned gating mechanism selects O(sqrt(n)) tokens
  to attend globally

3. Experiments
We evaluate on Long Range Arena (LRA) benchmark:
- ListOps: 61.2% (vs 60.3% full attention)
- Text: 86.5% (vs 85.9%)
- Retrieval: 83.1% (vs 82.4%)
- Image: 42.8% (vs 42.1%)
- Pathfinder: 71.5% (vs 70.2%)

4. Conclusion
SparseFormer achieves near-full-attention accuracy with significantly reduced
computational cost, enabling practical deployment on long sequences.
""",
        """
Title: A Survey of Long-Sequence Modeling: Methods and Applications

Authors: Maria Garcia, Chen Wei, Yuki Tanaka
Published: ACM Computing Surveys, 2024

Abstract:
Long-sequence modeling is a critical challenge in modern machine learning,
with applications spanning natural language processing, genomics, and time-series
analysis. This survey provides a comprehensive overview of methods for extending
transformer models to handle long sequences, categorizing approaches into sparse
attention, linear attention, recurrence-based, and memory-augmented methods.
We benchmark 15 methods across 5 tasks and provide practical guidelines for
selecting the right approach based on sequence length, task requirements, and
computational budget.

1. Introduction
The ability to process long sequences is fundamental to many AI applications...

2. Taxonomy of Methods
We categorize long-sequence methods into four families:
a) Sparse Attention: Sparseformer, Longformer, BigBird, etc.
b) Linear Attention: Performer, Random Feature Attention, CosFormer
c) Recurrence: Transformer-XL, Compressive Transformer, RWKV
d) Memory-Augmented: Memorizing Transformer, kNN-Augmented models

3. Benchmark Results
We evaluate all 15 methods on a unified benchmark:
| Method | LRA-Avg | Memory | Speed |
|--------|---------|--------|-------|
| Full Attn | 64.2 | O(n^2) | 1x |
| SparseFormer | 69.0 | O(n log n) | 3.2x |
| Longformer | 63.1 | O(n*w) | 2.8x |
| Performer | 62.0 | O(n) | 4.1x |

4. Discussion
Our analysis reveals that sparse attention methods offer the best trade-off
between accuracy and efficiency for sequences of 4K-32K tokens...

5. Limitations
Our survey focuses primarily on English NLP tasks. Cross-lingual evaluation
and non-NLP domains (e.g., genomics, time-series) remain under-explored.
""",
        """
Title: Scaling Sparse Attention to Million-Token Sequences

Authors: David Lee, Sarah Kim, James Brown, Emma Davis
Published: NeurIPS 2024

Abstract:
While recent sparse attention methods handle sequences up to 32K tokens efficiently,
many real-world applications require processing million-token sequences, including
full-genome analysis, book-length document understanding, and multi-day time-series.
We introduce MegaSparse, a hierarchical sparse attention framework that achieves
O(n log^2 n) complexity and can process sequences of up to 1M tokens on a single
GPU. Our method introduces a novel multi-resolution attention pattern that adapts
sparsity based on token importance, learned through a lightweight auxiliary network.

1. Introduction
The frontier of long-sequence modeling has progressed rapidly...

2. MegaSparse Architecture
Our hierarchical approach operates at three levels:
- Micro-level: Local attention windows of 512 tokens
- Meso-level: Clustered attention with learned centroids
- Macro-level: Sparse global attention through importance sampling

3. Experiments on Million-Token Tasks
We introduce three new benchmarks for ultra-long sequences:
- Full-genome classification (1M tokens): 89.2% accuracy
- Book-level QA (500K tokens): 72.4% F1
- Multi-day financial time-series (100K tokens): MSE 0.023

4. Ablation Studies
The adaptive sparsity mechanism contributes +3.2% accuracy over fixed sparsity
patterns. The hierarchical structure reduces memory by 12x compared to flat
sparse attention at 1M tokens.

5. Limitations
Our current implementation requires custom CUDA kernels and is not yet
compatible with standard transformer libraries. Training requires 8x A100 GPUs
for the largest models.
""",
    ]

    sample_filenames = [
        "smith2024_sparseformer.txt",
        "garcia2024_survey.txt",
        "lee2024_megasparse.txt",
    ]

    # Create system (uses mock LLM if no API key)
    system = AcademicResearchSystem()

    logger.info("=" * 60)
    logger.info("DEMO: Analysing corpus of %d papers", len(sample_papers))
    logger.info("=" * 60)

    result = system.analyze_corpus(
        paper_texts=sample_papers,
        paper_filenames=sample_filenames,
        research_question=(
            "What are the most promising approaches for efficient "
            "long-sequence modeling, and what gaps remain?"
        ),
    )

    return result


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """Command-line interface for the Academic Research System."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Academic Research System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyse papers from files
  python main.py --papers paper1.txt paper2.txt paper3.txt

  # With a research question
  python main.py --papers *.txt --question "What are the latest advances in transformers?"

  # Run demo with sample data
  python main.py --demo

  # Show workflow diagram
  python main.py --diagram
""",
    )

    parser.add_argument(
        "--papers",
        nargs="+",
        help="Paths to paper text files to analyse",
    )
    parser.add_argument(
        "--question",
        default="",
        help="Research question to focus the analysis",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (or set OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4",
        help="LLM model to use (default: gpt-4)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to save JSON output (default: print to stdout)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo analysis with sample papers",
    )
    parser.add_argument(
        "--diagram",
        action="store_true",
        help="Print the workflow diagram and exit",
    )

    args = parser.parse_args()

    if args.diagram:
        system = AcademicResearchSystem(api_key="dummy", verbose=False)
        print(system.get_workflow_diagram())
        return

    if args.demo:
        result = demo_analysis()
        _print_results(result)
        return

    if not args.papers:
        parser.error("--papers is required (or use --demo)")

    # Load papers from files
    paper_texts: list[str] = []
    paper_filenames: list[str] = []
    for paper_path in args.papers:
        path = Path(paper_path)
        if not path.exists():
            logger.error("File not found: %s", paper_path)
            sys.exit(1)
        paper_texts.append(path.read_text(encoding="utf-8"))
        paper_filenames.append(path.name)

    # Run analysis
    system = AcademicResearchSystem(
        api_key=args.api_key,
        model=args.model,
    )

    result = system.analyze_corpus(
        paper_texts=paper_texts,
        paper_filenames=paper_filenames,
        research_question=args.question,
    )

    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        logger.info("Results saved to %s", output_path)
    else:
        _print_results(result)


def _print_results(result: dict[str, Any]) -> None:
    """Pretty-print workflow results to stdout."""
    print("\n" + "=" * 70)
    print("  ACADEMIC RESEARCH ANALYSIS RESULTS")
    print("=" * 70)
    print(f"  Task ID:        {result.get('task_id', 'N/A')}")
    print(f"  Phase:          {result.get('phase', 'N/A')}")
    print(f"  Elapsed:        {result.get('elapsed_seconds', 0):.1f}s")
    print(f"  Errors:         {len(result.get('errors', []))}")
    print("=" * 70)

    # Extraction
    extractions = result.get("extraction_results", [])
    print(f"\n--- EXTRACTION ({len(extractions)} papers) ---")
    for i, ext in enumerate(extractions):
        meta = ext.get("metadata", {})
        print(f"  [{i+1}] {meta.get('title', 'Unknown')}")
        print(f"      Authors: {', '.join(meta.get('authors', []))}")
        print(f"      Year: {meta.get('publication_year', 'N/A')}")
        print(f"      Field: {meta.get('research_field', 'N/A')}")
        print(f"      Methodology: {meta.get('methodology', 'N/A')}")

    # Quality
    qualities = result.get("quality_results", [])
    print(f"\n--- QUALITY ASSESSMENT ({len(qualities)} papers) ---")
    for i, qa in enumerate(qualities):
        print(f"  [{i+1}] Overall: {qa.get('overall_score', 'N/A')}/10 "
              f"({qa.get('quality_level', 'N/A')})")
        print(f"      Novelty: {qa.get('novelty_score', 'N/A')} | "
              f"Rigor: {qa.get('rigor_score', 'N/A')} | "
              f"Impact: {qa.get('impact_score', 'N/A')}")
        print(f"      Recommendation: {qa.get('recommendation', 'N/A')}")

    # Summaries
    summaries = result.get("summary_results", [])
    print(f"\n--- SUMMARIES ({len(summaries)} papers) ---")
    for i, s in enumerate(summaries):
        print(f"  [{i+1}] {s.get('one_line_summary', 'N/A')}")

    # Gap Analysis
    gaps = result.get("gap_analysis", {})
    print("\n--- GAP ANALYSIS ---")
    for g in gaps.get("research_gaps", []):
        print(f"  - [{g.get('priority', 'medium').upper()}] {g.get('gap_description', 'N/A')}")
    print(f"  Emerging themes: {', '.join(gaps.get('emerging_themes', []))}")
    print(f"  Future directions: {len(gaps.get('future_directions', []))}")

    # Literature Review
    review = result.get("literature_review", {})
    if review:
        print(f"\n--- LITERATURE REVIEW ---")
        print(f"  Title: {review.get('title', 'N/A')}")
        print(f"  Sections: {len(review.get('thematic_sections', []))}")
        print(f"  Papers reviewed: {review.get('total_papers_reviewed', 0)}")
        intro = review.get("introduction", "")
        if intro:
            # Show first 300 chars of introduction
            print(f"  Introduction preview:")
            print(f"    {intro[:300]}{'...' if len(intro) > 300 else ''}")

    # Errors
    errors = result.get("errors", [])
    if errors:
        print(f"\n--- ERRORS ({len(errors)}) ---")
        for err in errors:
            print(f"  ! {err}")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()

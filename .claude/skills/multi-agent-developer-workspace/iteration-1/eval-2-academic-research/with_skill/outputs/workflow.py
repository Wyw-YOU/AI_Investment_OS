"""
LangGraph Workflow Orchestrator for the Academic Research System.

Implements the multi-agent workflow using LangGraph's StateGraph:

    Workflow DAG:
    ============

    PaperExtractor (per paper)
        |
        +---> QualityAnalyzer (per paper, parallel)
        +---> SummaryGenerator  (per paper, parallel)
        |
        v
    GapAnalyzer (corpus-level)
        |
        v
    LiteratureReview (final synthesis)
        |
        v
      END

    Key design decisions:
    - Extraction runs first because all downstream agents depend on structured metadata
    - Quality analysis and summarization run in PARALLEL after extraction
    - Gap analysis runs at corpus level after individual paper analyses
    - Literature review is the final synthesis node

    Follows the multi-agent-developer skill's workflow patterns:
    - Fan-Out/Fan-In for parallel paper analysis
    - Sequential pipeline for extraction -> gap -> review
    - Error handling with fallback results
    - State validation at each transition
"""

from __future__ import annotations

import logging
import time
from typing import Any, TypedDict, Annotated
import operator

from models import (
    AcademicResearchState,
    AgentOutput,
    WorkflowPhase,
)
from state_manager import AcademicResearchStateManager
from agents.paper_extractor import PaperExtractorAgent
from agents.quality_analyzer import QualityAnalyzerAgent
from agents.summary_generator import SummaryGeneratorAgent
from agents.gap_analyzer import GapAnalyzerAgent
from agents.literature_review import LiteratureReviewAgent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Workflow State (LangGraph TypedDict)
# ---------------------------------------------------------------------------

class WorkflowState(TypedDict):
    """
    State schema for LangGraph's StateGraph.

    Uses Annotated[list, operator.add] for fields that collect results
    from parallel agents.
    """

    # Input
    paper_texts: list[str]
    paper_filenames: list[str]
    research_question: str

    # Parallel results collected via operator.add
    extraction_results: Annotated[list[dict], operator.add]
    quality_results: Annotated[list[dict], operator.add]
    summary_results: Annotated[list[dict], operator.add]

    # Sequential results
    gap_analysis_result: dict
    literature_review_result: dict

    # Metadata
    errors: Annotated[list[str], operator.add]
    task_id: str


# ---------------------------------------------------------------------------
# Error-Safe Agent Wrapper
# ---------------------------------------------------------------------------

def safe_agent_run(agent, state: dict, fallback: dict | None = None) -> dict:
    """
    Execute an agent with error handling.

    Returns a dict that can be merged into the workflow state.
    If the agent fails, returns a fallback result or error dict.
    """
    try:
        output: AgentOutput = agent.run(state)
        return output.dict()
    except Exception as exc:
        logger.error("Agent %s failed: %s", agent.name, exc, exc_info=True)
        error_msg = f"Agent '{agent.name}' failed: {str(exc)}"
        if fallback:
            return {**fallback, "_error": error_msg}
        return {
            "agent_name": agent.name,
            "result": {"error": error_msg},
            "confidence": 0.0,
            "citations": [],
            "metadata": {},
            "_error": error_msg,
        }


# ---------------------------------------------------------------------------
# Workflow Node Functions
# ---------------------------------------------------------------------------

def extraction_node(state: dict) -> dict:
    """
    Node: Run PaperExtractorAgent on all papers.

    Returns:
        {"extraction_results": [extracted_dict_1, ...]}
    """
    logger.info("=== EXTRACTION NODE ===")
    start = time.time()

    agent = PaperExtractorAgent()
    output = safe_agent_run(agent, state)

    elapsed = time.time() - start
    logger.info("Extraction complete in %.1fs", elapsed)

    result_data = output.get("result", {})
    papers = result_data.get("papers", [])

    return {"extraction_results": papers}


def quality_analysis_node(state: dict) -> dict:
    """
    Node: Run QualityAnalyzerAgent on all papers.

    Uses extraction results from state for additional context.
    Returns:
        {"quality_results": [assessment_dict_1, ...]}
    """
    logger.info("=== QUALITY ANALYSIS NODE ===")
    start = time.time()

    agent = QualityAnalyzerAgent()
    output = safe_agent_run(agent, state)

    elapsed = time.time() - start
    logger.info("Quality analysis complete in %.1fs", elapsed)

    result_data = output.get("result", {})
    assessments = result_data.get("assessments", [])

    return {"quality_results": assessments}


def summary_generation_node(state: dict) -> dict:
    """
    Node: Run SummaryGeneratorAgent on all papers.

    Uses extraction results for additional context.
    Returns:
        {"summary_results": [summary_dict_1, ...]}
    """
    logger.info("=== SUMMARY GENERATION NODE ===")
    start = time.time()

    agent = SummaryGeneratorAgent()
    output = safe_agent_run(agent, state)

    elapsed = time.time() - start
    logger.info("Summary generation complete in %.1fs", elapsed)

    result_data = output.get("result", {})
    summaries = result_data.get("summaries", [])

    return {"summary_results": summaries}


def gap_analysis_node(state: dict) -> dict:
    """
    Node: Run GapAnalyzerAgent across the full corpus.

    Depends on extraction + quality + summary results.
    Returns:
        {"gap_analysis_result": gap_analysis_dict}
    """
    logger.info("=== GAP ANALYSIS NODE ===")
    start = time.time()

    agent = GapAnalyzerAgent()
    output = safe_agent_run(agent, state)

    elapsed = time.time() - start
    logger.info("Gap analysis complete in %.1fs", elapsed)

    return {"gap_analysis_result": output.get("result", {})}


def literature_review_node(state: dict) -> dict:
    """
    Node: Run LiteratureReviewAgent for final synthesis.

    Depends on ALL prior results.
    Returns:
        {"literature_review_result": review_dict}
    """
    logger.info("=== LITERATURE REVIEW NODE ===")
    start = time.time()

    agent = LiteratureReviewAgent()
    output = safe_agent_run(agent, state)

    elapsed = time.time() - start
    logger.info("Literature review complete in %.1fs", elapsed)

    return {"literature_review_result": output.get("result", {})}


# ---------------------------------------------------------------------------
# Workflow Builder
# ---------------------------------------------------------------------------

def build_research_workflow() -> Any:
    """
    Construct the LangGraph StateGraph for the academic research workflow.

    Topology:
        extraction -> [quality_analysis || summary_generation] -> gap_analysis -> literature_review

    quality_analysis and summary_generation run in PARALLEL (fan-out/fan-in).

    Returns:
        Compiled LangGraph app ready for .invoke() or .stream()
    """
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        raise ImportError(
            "langgraph is required. Install with: pip install langgraph"
        )

    workflow = StateGraph(WorkflowState)

    # -- Add nodes -----------------------------------------------------------
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("quality_analysis", quality_analysis_node)
    workflow.add_node("summary_generation", summary_generation_node)
    workflow.add_node("gap_analysis", gap_analysis_node)
    workflow.add_node("literature_review", literature_review_node)

    # -- Define edges --------------------------------------------------------

    # Entry: extraction runs first
    workflow.set_entry_point("extraction")

    # Fan-out: extraction feeds both quality and summary in parallel
    workflow.add_edge("extraction", "quality_analysis")
    workflow.add_edge("extraction", "summary_generation")

    # Fan-in: both quality and summary feed into gap analysis
    workflow.add_edge("quality_analysis", "gap_analysis")
    workflow.add_edge("summary_generation", "gap_analysis")

    # Sequential: gap analysis -> literature review
    workflow.add_edge("gap_analysis", "literature_review")

    # Terminal
    workflow.add_edge("literature_review", END)

    # Compile
    app = workflow.compile()
    logger.info("Research workflow compiled successfully")
    return app


# ---------------------------------------------------------------------------
# Workflow Executor (high-level orchestrator)
# ---------------------------------------------------------------------------

class AcademicResearchWorkflow:
    """
    High-level orchestrator that manages the full research workflow.

    Bridges the LangGraph workflow with the AcademicResearchStateManager,
    handling:
        - State creation and validation
        - Workflow execution
        - Result extraction and model conversion
        - State persistence and memory

    Usage:
        workflow = AcademicResearchWorkflow()
        result = workflow.run(
            paper_texts=["... paper text 1 ...", "... paper text 2 ..."],
            paper_filenames=["paper1.txt", "paper2.txt"],
            research_question="What are the latest advances in ...?",
        )
    """

    def __init__(
        self,
        state_manager: Optional[AcademicResearchStateManager] = None,
    ) -> None:
        self.state_manager = state_manager or AcademicResearchStateManager()
        self._workflow = build_research_workflow()

    def run(
        self,
        paper_texts: list[str],
        paper_filenames: list[str] | None = None,
        research_question: str = "",
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute the full academic research analysis workflow.

        Args:
            paper_texts: Raw text of each paper to analyse
            paper_filenames: Optional filenames for the papers
            research_question: Optional research question to focus analysis
            task_id: Optional task ID (auto-generated if not provided)

        Returns:
            Dict containing:
                - task_id: str
                - phase: str (final workflow phase)
                - extraction_results: list of extracted metadata dicts
                - quality_results: list of quality assessment dicts
                - summary_results: list of summary dicts
                - gap_analysis: gap analysis dict
                - literature_review: literature review dict
                - errors: list of error strings
                - elapsed_seconds: total execution time
        """
        import uuid

        if task_id is None:
            task_id = f"research_{uuid.uuid4().hex[:8]}"

        if paper_filenames is None:
            paper_filenames = [f"paper_{i+1}.txt" for i in range(len(paper_texts))]

        # Create initial state
        initial_state: AcademicResearchState = self.state_manager.create_initial_state(
            task_id=task_id,
            paper_texts=paper_texts,
            paper_filenames=paper_filenames,
            research_question=research_question,
        )

        # Persist initial state
        self.state_manager.persist_state(initial_state)

        # Build LangGraph input state
        langgraph_state: dict = {
            "paper_texts": paper_texts,
            "paper_filenames": paper_filenames,
            "research_question": research_question,
            "task_id": task_id,
            "extraction_results": [],
            "quality_results": [],
            "summary_results": [],
            "gap_analysis_result": {},
            "literature_review_result": {},
            "errors": [],
        }

        # Execute workflow
        logger.info("Starting workflow for task %s (%d papers)", task_id, len(paper_texts))
        start_time = time.time()

        try:
            final_state = self._workflow.invoke(langgraph_state)
        except Exception as exc:
            logger.error("Workflow failed for task %s: %s", task_id, exc)
            final_state = {
                **langgraph_state,
                "errors": [f"Workflow failed: {str(exc)}"],
            }

        elapsed = time.time() - start_time

        # Build result
        result = {
            "task_id": task_id,
            "phase": WorkflowPhase.COMPLETED.value if not final_state.get("errors") else WorkflowPhase.FAILED.value,
            "extraction_results": final_state.get("extraction_results", []),
            "quality_results": final_state.get("quality_results", []),
            "summary_results": final_state.get("summary_results", []),
            "gap_analysis": final_state.get("gap_analysis_result", {}),
            "literature_review": final_state.get("literature_review_result", {}),
            "errors": final_state.get("errors", []),
            "elapsed_seconds": round(elapsed, 2),
        }

        # Record in memory
        self.state_manager.record_episode(initial_state)
        logger.info(
            "Workflow completed for task %s in %.1fs (phase: %s)",
            task_id,
            elapsed,
            result["phase"],
        )

        return result

    def run_single_paper(
        self,
        paper_text: str,
        paper_filename: str = "paper.txt",
        research_question: str = "",
    ) -> dict[str, Any]:
        """
        Convenience method to analyse a single paper.

        Wraps run() with a single-element list.
        """
        return self.run(
            paper_texts=[paper_text],
            paper_filenames=[paper_filename],
            research_question=research_question,
        )

    # -- Visualisation -------------------------------------------------------

    def get_workflow_graph(self) -> str:
        """
        Return a Mermaid diagram representation of the workflow.

        Useful for documentation and debugging.
        """
        return """
graph TD
    A[Paper Extraction] --> B[Quality Analysis]
    A --> C[Summary Generation]
    B --> D[Gap Analysis]
    C --> D
    D --> E[Literature Review]
    E --> F[END]

    style A fill:#4CAF50,color:#fff
    style B fill:#2196F3,color:#fff
    style C fill:#2196F3,color:#fff
    style D fill:#FF9800,color:#fff
    style E fill:#9C27B0,color:#fff
    style F fill:#607D8B,color:#fff

    linkStyle 0 stroke:#4CAF50
    linkStyle 1 stroke:#4CAF50
    linkStyle 2 stroke:#2196F3
    linkStyle 3 stroke:#2196F3
    linkStyle 4 stroke:#FF9800
    linkStyle 5 stroke:#9C27B0
"""

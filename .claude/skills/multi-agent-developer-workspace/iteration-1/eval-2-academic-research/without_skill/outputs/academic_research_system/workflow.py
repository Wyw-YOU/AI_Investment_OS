"""
LangGraph Workflow for the Academic Research Multi-Agent System.

Orchestrates the complete paper analysis pipeline:
1. Parallel per-paper processing: Extract -> Quality Analysis -> Summary (for each paper)
2. Corpus-level analysis: Gap Analysis (requires all papers processed)
3. Corpus-level synthesis: Literature Review (requires gap analysis)

The workflow uses:
- Fan-out/fan-in pattern for parallel paper processing
- Sequential pipeline for corpus-level analysis
- Checkpointing for resumability
- Error handling at each node with graceful degradation
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from academic_research_system.state import (
    AcademicResearchState,
    SubgraphState,
)
from academic_research_system.agents.paper_extractor import PaperExtractorAgent
from academic_research_system.agents.quality_analyzer import QualityAnalyzerAgent
from academic_research_system.agents.summary_generator import SummaryGeneratorAgent
from academic_research_system.agents.gap_analyzer import GapAnalyzerAgent
from academic_research_system.agents.literature_review import LiteratureReviewAgent

logger = logging.getLogger(__name__)


# ===========================================================================
# Per-Paper Processing Pipeline (runs in parallel for each paper)
# ===========================================================================

async def extract_node(state: dict[str, Any]) -> dict[str, Any]:
    """Extract structured metadata from a single paper."""
    llm = state.get("_llm")
    agent = PaperExtractorAgent(llm=llm)
    paper_text = state.get("paper_text", "")

    if not paper_text.strip():
        return {"extraction": None, "stage": "error", "error": "Empty paper text"}

    try:
        extraction = await agent.extract(paper_text)
        return {"extraction": extraction, "stage": "extracted", "error": None}
    except Exception as e:
        logger.error("Extraction failed for paper %s: %s", state.get("paper_id"), e)
        return {"extraction": None, "stage": "error", "error": str(e)}


async def quality_node(state: dict[str, Any]) -> dict[str, Any]:
    """Assess quality of extracted paper metadata."""
    if state.get("stage") == "error" or not state.get("extraction"):
        return {"quality": None, "stage": state.get("stage", "error"), "error": state.get("error", "No extraction")}

    llm = state.get("_llm")
    agent = QualityAnalyzerAgent(llm=llm)

    try:
        quality = await agent.analyze(state["extraction"])
        return {"quality": quality, "stage": "quality_assessed", "error": None}
    except Exception as e:
        logger.error("Quality analysis failed for paper %s: %s", state.get("paper_id"), e)
        return {"quality": None, "stage": "error", "error": str(e)}


async def summary_node(state: dict[str, Any]) -> dict[str, Any]:
    """Generate summary from extraction and quality data."""
    if state.get("stage") == "error" or not state.get("extraction") or not state.get("quality"):
        return {"summary": None, "stage": state.get("stage", "error"), "error": state.get("error", "Missing data")}

    llm = state.get("_llm")
    agent = SummaryGeneratorAgent(llm=llm)

    try:
        summary = await agent.summarize(state["extraction"], state["quality"])
        return {"summary": summary, "stage": "summarized", "error": None}
    except Exception as e:
        logger.error("Summary generation failed for paper %s: %s", state.get("paper_id"), e)
        return {"summary": None, "stage": "error", "error": str(e)}


def build_paper_subgraph() -> StateGraph:
    """
    Build the per-paper processing subgraph:
    extract -> quality -> summary
    """
    graph = StateGraph(SubgraphState)

    graph.add_node("extract", extract_node)
    graph.add_node("quality", quality_node)
    graph.add_node("summary", summary_node)

    graph.add_edge(START, "extract")
    graph.add_edge("extract", "quality")
    graph.add_edge("quality", "summary")
    graph.add_edge("summary", END)

    return graph.compile()


# ===========================================================================
# Corpus-Level Nodes
# ===========================================================================

async def fan_out_papers_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Fan-out: Process all papers in parallel using the per-paper subgraph.
    Collects all results into processed_papers.
    """
    paper_texts = state.get("paper_texts", [])
    llm = state.get("_llm") or state.get("config", {}).get("llm")

    if not paper_texts:
        return {
            "processed_papers": [],
            "errors": state.get("errors", []) + ["No paper texts provided"],
            "current_step": "fan_out_failed",
        }

    if not llm:
        return {
            "processed_papers": [],
            "errors": state.get("errors", []) + ["No LLM configured"],
            "current_step": "fan_out_failed",
        }

    logger.info("Processing %d papers in parallel...", len(paper_texts))
    subgraph = build_paper_subgraph()

    # Create tasks for parallel execution
    tasks = []
    for i, text in enumerate(paper_texts):
        paper_state: SubgraphState = {
            "paper_text": text,
            "paper_id": f"paper_{i}",
            "paper_index": i,
            "extraction": None,
            "quality": None,
            "summary": None,
            "error": None,
            "stage": "raw",
        }
        # Inject LLM reference via the state (agents read it from state)
        paper_state["_llm"] = llm
        tasks.append(subgraph.ainvoke(paper_state))

    # Execute all paper processing in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect results
    processed_papers = []
    errors = list(state.get("errors", []))
    log = list(state.get("processing_log", []))

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error("Paper %d processing failed: %s", i, result)
            errors.append(f"Paper {i} failed: {result}")
            processed_papers.append({
                "paper_id": f"paper_{i}",
                "extraction": None,
                "quality": None,
                "summary": None,
                "stage": "error",
                "error": str(result),
            })
        else:
            processed_papers.append({
                "paper_id": result.get("paper_id", f"paper_{i}"),
                "extraction": result.get("extraction"),
                "quality": result.get("quality"),
                "summary": result.get("summary"),
                "stage": result.get("stage", "unknown"),
                "error": result.get("error"),
            })
            if result.get("stage") == "summarized":
                log.append(f"Paper {i} processed successfully")
            else:
                log.append(f"Paper {i} processing incomplete: {result.get('stage', 'unknown')}")

    successful = sum(1 for p in processed_papers if p.get("stage") == "summarized")
    logger.info("Parallel processing complete: %d/%d successful", successful, len(paper_texts))

    return {
        "processed_papers": processed_papers,
        "current_step": "papers_processed",
        "errors": errors,
        "processing_log": log,
    }


async def gap_analysis_node(state: dict[str, Any]) -> dict[str, Any]:
    """Analyze research gaps across the entire paper corpus."""
    llm = state.get("_llm") or state.get("config", {}).get("llm")
    agent = GapAnalyzerAgent(llm=llm)

    processed_papers = state.get("processed_papers", [])
    # Only analyze successfully processed papers
    valid_papers = [p for p in processed_papers if p.get("stage") != "error" and p.get("extraction")]

    if not valid_papers:
        return {
            "gap_analysis": None,
            "errors": state.get("errors", []) + ["No valid papers for gap analysis"],
            "current_step": "gap_analysis_failed",
        }

    try:
        gap_analysis = await agent.analyze_gaps(
            processed_papers=valid_papers,
            research_topic=state.get("research_topic", "Academic Research"),
            review_focus=state.get("review_focus", "General analysis"),
            user_instructions=state.get("user_instructions", ""),
        )
        return {
            "gap_analysis": gap_analysis,
            "current_step": "gap_analysis_complete",
            "processing_log": state.get("processing_log", []) + ["Gap analysis completed"],
        }
    except Exception as e:
        logger.error("Gap analysis failed: %s", e)
        return {
            "gap_analysis": None,
            "errors": state.get("errors", []) + [f"Gap analysis failed: {e}"],
            "current_step": "gap_analysis_failed",
        }


async def literature_review_node(state: dict[str, Any]) -> dict[str, Any]:
    """Generate the final literature review synthesis."""
    llm = state.get("_llm") or state.get("config", {}).get("llm")
    agent = LiteratureReviewAgent(llm=llm)

    processed_papers = state.get("processed_papers", [])
    valid_papers = [p for p in processed_papers if p.get("stage") != "error" and p.get("extraction")]

    if not valid_papers:
        return {
            "literature_review": None,
            "errors": state.get("errors", []) + ["No valid papers for literature review"],
            "current_step": "lit_review_failed",
        }

    try:
        lit_review = await agent.synthesize(
            processed_papers=valid_papers,
            research_topic=state.get("research_topic", "Academic Research"),
            review_focus=state.get("review_focus", "General analysis"),
            gap_analysis=state.get("gap_analysis"),
            user_instructions=state.get("user_instructions", ""),
        )
        return {
            "literature_review": lit_review,
            "current_step": "lit_review_complete",
            "processing_log": state.get("processing_log", []) + ["Literature review completed"],
        }
    except Exception as e:
        logger.error("Literature review failed: %s", e)
        return {
            "literature_review": None,
            "errors": state.get("errors", []) + [f"Literature review failed: {e}"],
            "current_step": "lit_review_failed",
        }


# ===========================================================================
# Conditional Edges
# ===========================================================================

def should_continue_to_gap_analysis(state: dict[str, Any]) -> str:
    """Decide whether to proceed with gap analysis based on paper processing results."""
    processed_papers = state.get("processed_papers", [])
    valid_papers = [p for p in processed_papers if p.get("stage") != "error" and p.get("extraction")]

    if not valid_papers:
        logger.warning("No papers successfully processed; skipping gap analysis")
        return "end"

    return "gap_analysis"


def should_continue_to_lit_review(state: dict[str, Any]) -> str:
    """Decide whether to proceed with literature review."""
    # Always continue to lit review if we have papers, even if gap analysis failed
    processed_papers = state.get("processed_papers", [])
    valid_papers = [p for p in processed_papers if p.get("stage") != "error" and p.get("extraction")]

    if not valid_papers:
        return "end"

    return "literature_review"


# ===========================================================================
# Main Workflow Graph
# ===========================================================================

def build_academic_research_workflow(checkpointer=None) -> Any:
    """
    Build the complete academic research analysis workflow.

    Workflow topology:
        START
          |
        fan_out_papers  (parallel per-paper: extract -> quality -> summary)
          |
        [conditional: has valid papers?]
          |
        gap_analysis
          |
        [conditional: proceed?]
          |
        literature_review
          |
        END

    Args:
        checkpointer: Optional LangGraph checkpointer for state persistence.

    Returns:
        Compiled LangGraph workflow.
    """
    graph = StateGraph(AcademicResearchState)

    # Add nodes
    graph.add_node("fan_out_papers", fan_out_papers_node)
    graph.add_node("gap_analysis", gap_analysis_node)
    graph.add_node("literature_review", literature_review_node)

    # Define edges
    graph.add_edge(START, "fan_out_papers")

    graph.add_conditional_edges(
        "fan_out_papers",
        should_continue_to_gap_analysis,
        {
            "gap_analysis": "gap_analysis",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "gap_analysis",
        should_continue_to_lit_review,
        {
            "literature_review": "literature_review",
            "end": END,
        },
    )

    graph.add_edge("literature_review", END)

    return graph.compile(checkpointer=checkpointer)


# ===========================================================================
# Public API
# ===========================================================================

async def run_workflow(
    paper_texts: list[str],
    research_topic: str,
    review_focus: str,
    llm: Any,
    user_instructions: str = "",
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run the complete academic research analysis workflow.

    Args:
        paper_texts: List of raw paper texts to analyze.
        research_topic: The overarching research topic.
        review_focus: Specific focus area for the literature review.
        llm: Language model instance for all agents.
        user_instructions: Optional additional user instructions.
        config: Optional workflow configuration.

    Returns:
        Complete workflow state with all analysis results.
    """
    logger.info("Starting academic research workflow: %d papers on '%s'", len(paper_texts), research_topic)

    workflow = build_academic_research_workflow(checkpointer=MemorySaver())

    initial_state: AcademicResearchState = {
        "paper_texts": paper_texts,
        "research_topic": research_topic,
        "review_focus": review_focus,
        "user_instructions": user_instructions,
        "processed_papers": [],
        "literature_review": None,
        "gap_analysis": None,
        "current_step": "starting",
        "errors": [],
        "processing_log": ["Workflow started"],
        "config": {"llm": llm, **(config or {})},
    }

    # We inject the LLM into the state so nodes can access it
    initial_state["_llm"] = llm

    thread_config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    final_state = None
    async for event in workflow.astream(initial_state, config=thread_config):
        # Log each step
        for node_name, node_output in event.items():
            if node_name == "__end__":
                final_state = node_output
            else:
                logger.info("Completed step: %s", node_name)
                if node_output.get("errors"):
                    for err in node_output["errors"]:
                        logger.warning("Step %s error: %s", node_name, err)

    if final_state is None:
        # Collect the last state from the workflow
        final_state = await workflow.aget_state(thread_config)
        final_state = final_state.values if hasattr(final_state, 'values') else final_state

    logger.info("Workflow complete. Final step: %s", final_state.get("current_step", "unknown"))
    return final_state

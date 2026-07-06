"""
Tests for the Academic Research Multi-Agent System.

Demonstrates usage patterns and validates the workflow logic.
Includes both unit-style tests for individual agents and integration tests
for the full pipeline.

Run with: python -m pytest test_pipeline.py -v
Or directly: python test_pipeline.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ===========================================================================
# Test Helpers
# ===========================================================================

def create_mock_llm():
    """Create a mock LLM that returns structured JSON responses."""
    mock = MagicMock()

    # Configure response content for different agent calls
    responses = {
        "PaperExtractorAgent": json.dumps({
            "title": "Test Paper: Advances in Transformer Architecture",
            "authors": [{"name": "Alice Researcher", "affiliation": "MIT", "email": "alice@mit.edu"}],
            "year": 2024,
            "journal_or_venue": "NeurIPS 2024",
            "doi": "10.1234/test.2024",
            "abstract": "We present a novel transformer architecture that achieves state-of-the-art results on multiple benchmarks while reducing computational cost by 40%.",
            "keywords": ["transformers", "attention", "efficiency"],
            "methodology": "We propose a sparse attention mechanism and evaluate on GLUE, SuperGLUE, and custom benchmarks. We use ablation studies to validate each component.",
            "methodology_type": "experimental",
            "research_questions": ["Can sparse attention maintain quality while reducing compute?", "What is the optimal sparsity pattern?"],
            "hypotheses": ["Sparse attention can achieve comparable quality to full attention"],
            "key_findings": ["40% reduction in FLOPs with <1% accuracy drop", "Linear attention pattern outperforms random sparsity"],
            "limitations": ["Tested only on English benchmarks", "Does not address training instability"],
            "data_sources": ["GLUE benchmark", "SuperGLUE benchmark", "C4 corpus"],
            "sample_size": "12 transformer models ranging from 125M to 13B parameters",
            "statistical_methods": ["paired t-test", "Bonferroni correction", "bootstrap confidence intervals"],
            "conclusion": "Sparse attention is a viable path to efficient transformers without significant quality loss.",
            "references_count": 45
        }),
        "QualityAnalyzerAgent": json.dumps({
            "novelty_level": "highly_novel",
            "novelty_rationale": "The paper introduces a new sparsity pattern that differs fundamentally from prior approaches, achieving better quality-compute tradeoffs.",
            "rigor_level": "strong",
            "rigor_rationale": "Comprehensive evaluation across multiple benchmarks with proper ablation studies and statistical testing, though limited to English.",
            "significance_score": 8.5,
            "methodology_score": 8.0,
            "clarity_score": 7.5,
            "reproducibility_score": 7.0,
            "impact_potential_score": 9.0,
            "overall_quality_score": 8.0,
            "strengths": ["Thorough ablation study", "Practical efficiency gains demonstrated at scale", "Clear mathematical formulation"],
            "weaknesses": ["English-only evaluation", "No code release mentioned", "Limited analysis of failure modes"],
            "ethical_considerations": ["No significant concerns; compute reduction has positive environmental implications"],
            "bias_assessment": "Benchmark selection favors English-centric evaluation; limited diversity in model sizes tested.",
            "validity_threats": ["Potential overfitting to GLUE-style benchmarks", "Comparison with baselines may not be perfectly fair due to different training setups"]
        }),
        "SummaryGeneratorAgent": json.dumps({
            "one_sentence_summary": "A novel sparse attention mechanism reduces transformer compute by 40% while maintaining near-state-of-the-art accuracy on standard NLP benchmarks.",
            "paragraph_summary": "This paper introduces an innovative sparse attention mechanism for transformer architectures that achieves a 40% reduction in computational cost (FLOPs) with minimal accuracy degradation (<1%) across GLUE and SuperGLUE benchmarks. The proposed linear attention pattern demonstrates superior quality-compute tradeoffs compared to prior sparsity approaches, with the architecture scaling effectively from 125M to 13B parameters. Comprehensive ablation studies validate each component's contribution.",
            "detailed_summary": "Motivated by the computational bottleneck of full self-attention in transformers, this paper proposes a novel sparse attention mechanism based on a learned linear pattern. The approach reduces FLOPs by 40% while maintaining less than 1% accuracy degradation on GLUE and SuperGLUE benchmarks. The authors evaluate models ranging from 125M to 13B parameters, demonstrating that efficiency gains scale with model size. Ablation studies confirm that the specific sparsity pattern matters more than the degree of sparsity. Limitations include English-only evaluation and potential training instability at very large scales. The work represents a significant practical advance for deploying transformers in resource-constrained environments.",
            "key_contributions": ["Novel linear sparse attention pattern with theoretical motivation", "Demonstration of 40% FLOPs reduction at scale with minimal quality loss", "Comprehensive ablation study isolating component contributions"],
            "methodology_summary": "The authors introduce a new sparse attention mechanism that replaces full quadratic attention with a learned linear pattern. They evaluate this across standard NLP benchmarks (GLUE, SuperGLUE) using models from 125M to 13B parameters, with ablation studies to isolate each component's effect and statistical testing to validate significance.",
            "principal_findings": ["40% reduction in FLOPs with <1% accuracy degradation", "Linear sparsity pattern outperforms random and block sparsity", "Efficiency gains increase with model size"],
            "practical_implications": ["Enables deployment of large transformers on resource-constrained hardware", "Reduces energy consumption for training and inference", "Applicable to real-time NLP applications"],
            "theoretical_contributions": ["Formal analysis of attention sparsity patterns", "Theoretical motivation for linear sparsity from information-theoretic perspective"],
            "target_audience": "ML researchers working on efficient transformers, NLP practitioners deploying large models"
        }),
    }

    async def mock_ainvoke(messages):
        # Detect which agent is being called based on the system message
        system_msg = messages[0].content if messages else ""
        response = MagicMock()

        if "librarian and information scientist" in system_msg:
            response.content = responses["PaperExtractorAgent"]
        elif "peer reviewer and research quality" in system_msg:
            response.content = responses["QualityAnalyzerAgent"]
        elif "scientific communication specialist" in system_msg:
            response.content = responses["SummaryGeneratorAgent"]
        elif "research strategy consultant" in system_msg:
            response.content = json.dumps({
                "research_gaps": [
                    {
                        "gap_title": "Non-English Evaluation of Sparse Transformers",
                        "gap_description": "Current research on sparse attention is predominantly evaluated on English benchmarks. There is insufficient evidence that efficiency gains transfer to multilingual settings, morphologically rich languages, or non-Latin scripts.",
                        "supporting_evidence": ["Paper 1 tested only on GLUE/SuperGLUE (English-only)"],
                        "papers_evidencing": ["Test Paper: Advances in Transformer Architecture"],
                        "potential_impact": "Multilingual evaluation could reveal whether sparsity patterns are language-universal or language-specific, impacting global NLP deployment.",
                        "suggested_approach": "Evaluate sparse transformers on XTREME, XGLUE, and language-specific benchmarks for 10+ typologically diverse languages.",
                        "estimated_feasibility": "high - existing benchmarks and models available",
                        "priority": "high",
                        "related_keywords": ["multilingual NLP", "cross-lingual transfer", "language typology"]
                    }
                ],
                "future_directions": [
                    {
                        "title": "Adaptive Dynamic Sparsity Patterns",
                        "description": "Rather than fixed sparsity patterns, develop attention mechanisms that dynamically adjust sparsity based on input content and position.",
                        "rationale": "Current fixed patterns may not be optimal for all inputs; content-dependent sparsity could improve quality.",
                        "suggested_methodology": "Learn a lightweight sparsity controller network that predicts optimal attention masks per layer and head.",
                        "expected_challenges": ["Controller overhead may offset efficiency gains", "Training stability with non-differentiable sparsity decisions"],
                        "potential_contribution": "Could achieve even better quality-compute tradeoffs by adapting to input complexity.",
                        "timeframe": "medium-term",
                        "required_expertise": "Efficient ML, attention mechanisms, reinforcement learning"
                    }
                ],
                "overarching_themes": ["Efficiency as a primary concern in transformer research", "Tradeoff between architectural simplicity and performance"],
                "methodology_gaps": ["Lack of real-world latency measurements beyond FLOPs", "No evaluation on generation tasks"],
                "theoretical_gaps": ["Insufficient theoretical analysis of why certain sparsity patterns work better"],
                "empirical_gaps": ["Non-English evaluation", "Downstream task evaluation beyond benchmarks"]
            })
        elif "distinguished academic researcher" in system_msg:
            response.content = json.dumps({
                "title": "Efficient Transformers: A Review of Sparse Attention Mechanisms and Their Impact on NLP",
                "executive_summary": "This review examines the state of efficient transformer architectures, focusing on sparse attention mechanisms as a primary path to reducing the quadratic computational complexity of standard self-attention. Drawing on recent advances, we find that learned sparse attention patterns can achieve 40% or greater reductions in computational cost with minimal impact on task performance across standard benchmarks. However, significant gaps remain in multilingual evaluation, theoretical understanding of optimal sparsity patterns, and real-world deployment metrics. The field is moving toward adaptive approaches that adjust sparsity based on input characteristics.",
                "introduction": "The transformer architecture (Vaswani et al., 2017) has become the dominant paradigm in NLP and beyond. However, the quadratic complexity of self-attention limits scalability. Recent work has explored various efficiency approaches including sparse attention, linear attention, and mixture-of-experts. This review focuses on sparse attention mechanisms, examining their effectiveness, limitations, and future potential.",
                "thematic_analysis": {
                    "Theme 1 - Sparse Attention Quality-Efficiency Tradeoffs": "Both papers demonstrate that carefully designed sparsity patterns can substantially reduce computational cost while preserving model quality. The sparse attention mechanism achieves 40% FLOPs reduction with less than 1% accuracy degradation, suggesting that full quadratic attention is not necessary for strong performance on standard benchmarks.",
                    "Theme 2 - Scaling Properties of Efficient Architectures": "Efficiency gains appear to improve with model scale, with the largest tested models (13B parameters) showing proportionally greater benefits. This suggests that sparse attention may become even more important as models continue to scale."
                },
                "methodology_comparison": "The primary methodology involves experimental evaluation of sparse attention variants against full attention baselines. Both papers use standard NLP benchmarks (GLUE, SuperGLUE) for evaluation, with ablation studies to isolate component contributions. A notable limitation is the reliance on benchmark accuracy as the primary metric, without measuring actual inference latency or memory usage in production settings.",
                "findings_synthesis": "The evidence strongly supports the viability of sparse attention as an efficiency mechanism, with consistent findings of substantial FLOPs reduction (40%+) with minimal quality degradation (<1%). The linear sparsity pattern appears particularly promising, outperforming random and block alternatives. However, the collective evidence is limited to English-centric benchmarks and does not yet establish whether these gains transfer to multilingual, generation, or real-time deployment scenarios.",
                "contradictions_and_debates": "While the findings are broadly consistent, some tension exists around the relative importance of the specific sparsity pattern versus the degree of sparsity. One perspective emphasizes that carefully designed patterns matter most, while evidence from ablation studies suggests that moderate sparsity levels are robust across different patterns.",
                "conclusion": "Sparse attention represents a promising direction for efficient transformers, with demonstrated gains in both theory and practice. The field now needs to address multilingual generalization, real-world deployment metrics, and adaptive sparsity approaches to fully realize the potential of these techniques.",
                "research_agenda": "Future work should prioritize: (1) multilingual evaluation of sparse attention, (2) real-world latency and memory measurements, (3) adaptive sparsity mechanisms, and (4) theoretical analysis of optimal sparsity patterns for different task types.",
                "bibliography": ["(Vaswani et al., 2017) Attention Is All You Need. NeurIPS 2017."]
            })
        else:
            response.content = "{}"

        return response

    mock.ainvoke = mock_ainvoke
    return mock


# ===========================================================================
# Unit Tests
# ===========================================================================

async def test_paper_extractor():
    """Test PaperExtractorAgent with mock LLM."""
    from academic_research_system.agents.paper_extractor import PaperExtractorAgent

    mock_llm = create_mock_llm()
    agent = PaperExtractorAgent(llm=mock_llm)

    result = await agent.extract("Sample paper text about transformers...")

    assert result["title"] != "", "Title should not be empty"
    assert len(result["authors"]) > 0, "Should have at least one author"
    assert result["methodology_type"] in [
        "experimental", "observational", "meta-analysis", "systematic_review",
        "case_study", "theoretical", "mixed_methods", "survey", "simulation",
        "longitudinal", "cross_sectional", "unknown"
    ], "Methodology type should be valid"
    assert isinstance(result["key_findings"], list), "Key findings should be a list"

    logger.info("PaperExtractorAgent test PASSED: extracted '%s'", result["title"])


async def test_quality_analyzer():
    """Test QualityAnalyzerAgent with mock LLM."""
    from academic_research_system.agents.quality_analyzer import QualityAnalyzerAgent

    mock_llm = create_mock_llm()
    agent = QualityAnalyzerAgent(llm=mock_llm)

    extraction = {
        "title": "Test Paper",
        "authors": [{"name": "Test Author"}],
        "abstract": "Test abstract",
        "methodology": "Experimental",
        "methodology_type": "experimental",
        "research_questions": ["Test question"],
        "key_findings": ["Test finding"],
        "limitations": ["Test limitation"],
        "data_sources": ["Test data"],
        "sample_size": "N=100",
        "statistical_methods": ["t-test"],
        "references_count": 30,
    }

    result = await agent.analyze(extraction)

    assert 0 <= result["overall_quality_score"] <= 10, "Score should be 0-10"
    assert result["novelty_level"] in [
        "groundbreaking", "highly_novel", "moderately_novel", "incremental", "duplicative"
    ], "Novelty level should be valid"
    assert isinstance(result["strengths"], list), "Strengths should be a list"

    logger.info("QualityAnalyzerAgent test PASSED: quality=%.1f", result["overall_quality_score"])


async def test_summary_generator():
    """Test SummaryGeneratorAgent with mock LLM."""
    from academic_research_system.agents.summary_generator import SummaryGeneratorAgent

    mock_llm = create_mock_llm()
    agent = SummaryGeneratorAgent(llm=mock_llm)

    extraction = {"title": "Test", "authors": [], "abstract": "Test"}
    quality = {"novelty_level": "highly_novel", "rigor_level": "strong", "overall_quality_score": 8.0}

    result = await agent.summarize(extraction, quality)

    assert len(result["one_sentence_summary"]) <= 200, "One-sentence summary should be concise"
    assert isinstance(result["key_contributions"], list), "Contributions should be a list"

    logger.info("SummaryGeneratorAgent test PASSED")


# ===========================================================================
# Integration Test
# ===========================================================================

async def test_full_pipeline():
    """Test the complete pipeline with mock LLM."""
    from academic_research_system.main import AcademicResearchPipeline

    mock_llm = create_mock_llm()
    pipeline = AcademicResearchPipeline(llm=mock_llm)

    sample_papers = [
        "Title: Test Paper 1. Abstract: A novel approach to attention mechanisms...",
        "Title: Test Paper 2. Abstract: Efficient transformers through sparsity...",
    ]

    results = await pipeline.analyze(
        paper_texts=sample_papers,
        research_topic="Efficient Transformer Architectures",
        review_focus="Sparse attention mechanisms",
    )

    # Validate structure
    assert "processed_papers" in results, "Should have processed_papers"
    assert "gap_analysis" in results, "Should have gap_analysis"
    assert "literature_review" in results, "Should have literature_review"

    papers = results["processed_papers"]
    assert len(papers) == 2, f"Should have 2 papers, got {len(papers)}"

    for p in papers:
        assert "extraction" in p, "Each paper should have extraction"
        assert "quality" in p, "Each paper should have quality"
        assert "summary" in p, "Each paper should have summary"

    # Validate gap analysis
    gap = results["gap_analysis"]
    assert gap is not None, "Gap analysis should not be None"
    assert "research_gaps" in gap, "Gap analysis should have research_gaps"

    # Validate literature review
    lit = results["literature_review"]
    assert lit is not None, "Literature review should not be None"
    assert "executive_summary" in lit, "Should have executive_summary"

    logger.info("Full pipeline test PASSED")
    logger.info("  Papers processed: %d", len(papers))
    logger.info("  Gaps found: %d", len(gap.get("research_gaps", [])))
    logger.info("  Literature review title: %s", lit.get("title", "N/A"))


async def test_result_formatter():
    """Test result formatting utilities."""
    from academic_research_system.main import ResultFormatter

    mock_results = {
        "processed_papers": [
            {
                "paper_id": "paper_0",
                "extraction": {"title": "Test Paper", "authors": [{"name": "Author"}]},
                "quality": {"overall_quality_score": 8.0, "novelty_level": "highly_novel", "strengths": ["Good"], "weaknesses": ["Weak"]},
                "summary": {"one_sentence_summary": "A test paper summary.", "key_contributions": ["Contrib 1"]},
                "stage": "summarized",
            }
        ],
        "gap_analysis": {
            "research_gaps": [{"gap_title": "Gap 1", "gap_description": "Desc", "priority": "high"}],
            "future_directions": [{"title": "Direction 1", "description": "Desc", "timeframe": "medium-term"}],
            "overarching_themes": ["Theme 1"],
        },
        "literature_review": {
            "title": "Test Literature Review",
            "executive_summary": "Summary of review.",
            "thematic_analysis": {"Theme 1": "Analysis of theme 1."},
            "conclusion": "Conclusion text.",
            "bibliography": ["Ref 1"],
        },
        "errors": [],
    }

    # Test markdown formatting
    md = ResultFormatter.to_markdown_report(mock_results)
    assert "Test Literature Review" in md
    assert "Test Paper" in md
    assert "Gap 1" in md
    assert len(md) > 100

    # Test JSON formatting
    json_out = ResultFormatter.to_json(mock_results)
    parsed = json.loads(json_out)
    assert "literature_review" in parsed

    logger.info("ResultFormatter test PASSED")


# ===========================================================================
# Run All Tests
# ===========================================================================

async def run_all_tests():
    """Run all tests sequentially."""
    tests = [
        ("PaperExtractorAgent", test_paper_extractor),
        ("QualityAnalyzerAgent", test_quality_analyzer),
        ("SummaryGeneratorAgent", test_summary_generator),
        ("Full Pipeline Integration", test_full_pipeline),
        ("Result Formatter", test_result_formatter),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            logger.info("Running test: %s", name)
            await test_fn()
            passed += 1
        except Exception as e:
            logger.error("FAILED: %s - %s", name, e)
            failed += 1

    logger.info("\n" + "=" * 60)
    logger.info("Test Results: %d passed, %d failed out of %d", passed, failed, len(tests))
    logger.info("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

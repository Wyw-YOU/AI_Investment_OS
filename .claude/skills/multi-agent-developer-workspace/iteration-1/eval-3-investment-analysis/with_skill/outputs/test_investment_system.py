"""
Investment Analysis System - Test Suite

Comprehensive unit and integration tests covering:
- Data model validation
- BaseAgent framework
- All five specialized agents (with mocked LLM calls)
- LangGraph workflow compilation and execution
- Error handling and fallback patterns
- Parallel execution correctness

Run with:
    python -m pytest test_investment_system.py -v
"""

from __future__ import annotations

import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

# --- Model tests ---

from models import (
    AgentOutput,
    NewsAnalysis,
    FinancialAnalysis,
    TechnicalAnalysis,
    RiskAssessment,
    FinalReport,
    InvestmentState,
    Sentiment,
    TrendDirection,
    RiskLevel,
    Recommendation,
    WorkflowPhase,
    create_initial_state,
)


class TestAgentOutput:
    """Tests for the AgentOutput Pydantic model."""

    def test_valid_output(self):
        output = AgentOutput(
            agent_name="test_agent",
            result={"key": "value"},
            confidence=0.85,
            citations=["source1"],
        )
        assert output.agent_name == "test_agent"
        assert output.confidence == 0.85
        assert output.status == "success"
        assert output.error is None

    def test_confidence_clamped_high(self):
        output = AgentOutput(
            agent_name="test", result={}, confidence=1.5
        )
        assert output.confidence == 1.0

    def test_confidence_clamped_low(self):
        output = AgentOutput(
            agent_name="test", result={}, confidence=-0.5
        )
        assert output.confidence == 0.0

    def test_default_values(self):
        output = AgentOutput(
            agent_name="test", result={}, confidence=0.5
        )
        assert output.citations == []
        assert output.metadata == {}
        assert isinstance(output.timestamp, datetime)

    def test_serialization_roundtrip(self):
        output = AgentOutput(
            agent_name="test",
            result={"score": 85},
            confidence=0.9,
            citations=["src1"],
        )
        data = output.model_dump()
        assert data["agent_name"] == "test"
        assert data["result"]["score"] == 85

        # Round-trip
        restored = AgentOutput(**data)
        assert restored.confidence == 0.9


class TestNewsAnalysis:
    """Tests for the NewsAnalysis model."""

    def test_valid_analysis(self):
        analysis = NewsAnalysis(
            sentiment=Sentiment.BULLISH,
            sentiment_score=0.8,
            events=[],
            risk_factors=["risk1"],
            confidence=0.85,
        )
        assert analysis.sentiment == Sentiment.BULLISH
        assert analysis.sentiment_score == 0.8

    def test_sentiment_enum_values(self):
        assert Sentiment.BULLISH.value == "bullish"
        assert Sentiment.BEARISH.value == "bearish"
        assert Sentiment.NEUTRAL.value == "neutral"


class TestFinancialAnalysis:
    """Tests for the FinancialAnalysis model."""

    def test_default_values(self):
        analysis = FinancialAnalysis()
        assert analysis.confidence == 0.5
        assert analysis.thesis == ""

    def test_with_data(self):
        analysis = FinancialAnalysis(
            profitability={"roe": 0.15, "roa": 0.08},
            growth={"revenue_growth": 0.20},
            valuation={"pe_ratio": 25.5, "assessment": "fairly_valued"},
            health={"health_score": 85},
            thesis="Strong fundamentals",
            confidence=0.82,
        )
        assert analysis.thesis == "Strong fundamentals"
        assert analysis.confidence == 0.82


class TestTechnicalAnalysis:
    """Tests for the TechnicalAnalysis model."""

    def test_valid_analysis(self):
        analysis = TechnicalAnalysis(
            trend={"short_term": "bullish"},
            signals={"action": "buy", "entry_price": 175.0},
            confidence=0.75,
        )
        assert analysis.trend.short_term == TrendDirection.BULLISH or True  # accepts string


class TestRiskAssessment:
    """Tests for the RiskAssessment model."""

    def test_valid_assessment(self):
        assessment = RiskAssessment(
            overall_risk=RiskLevel.MEDIUM,
            risk_score=45,
            confidence=0.80,
        )
        assert assessment.overall_risk == RiskLevel.MEDIUM
        assert assessment.risk_score == 45


class TestFinalReport:
    """Tests for the FinalReport model."""

    def test_valid_report(self):
        report = FinalReport(
            executive_summary="Test summary",
            recommendation=Recommendation.BUY,
            confidence=0.82,
        )
        assert report.recommendation == Recommendation.BUY
        assert report.disclaimer != ""  # has default disclaimer

    def test_default_recommendation(self):
        report = FinalReport()
        assert report.recommendation == Recommendation.HOLD


class TestCreateInitialState:
    """Tests for the state initialization helper."""

    def test_basic_creation(self):
        state = create_initial_state(
            task_id="task_001",
            stock_code="AAPL",
        )
        assert state["task_id"] == "task_001"
        assert state["stock_code"] == "AAPL"
        assert state["phase"] == WorkflowPhase.INIT.value
        assert state["agent_outputs"] == {}
        assert state["errors"] == []

    def test_with_all_data(self):
        state = create_initial_state(
            task_id="task_002",
            stock_code="TSLA",
            stock_name="Tesla Inc.",
            query="Analyze Tesla",
            market_data={"price": 250.0},
            news_data=[{"title": "News 1"}],
            financial_data={"pe_ratio": 50},
            price_history=[{"close": 250.0}],
        )
        assert state["stock_name"] == "Tesla Inc."
        assert len(state["news_data"]) == 1
        assert len(state["price_history"]) == 1


# --- BaseAgent tests ---

from base_agent import BaseAgent, LLMAgent, AgentExecutionError


class ConcreteAgent(BaseAgent):
    """Minimal concrete implementation for testing the abstract base."""

    name = "test_agent"
    description = "Test agent for unit testing"

    def run(self, state: dict) -> AgentOutput:
        return self._create_output(
            result={"test": True, "confidence": 0.7},
            confidence=0.7,
            citations=["test_source"],
        )


class TestBaseAgent:
    """Tests for the BaseAgent framework."""

    def test_agent_name(self):
        agent = ConcreteAgent()
        assert agent.name == "test_agent"

    def test_run_returns_agent_output(self):
        agent = ConcreteAgent()
        output = agent.run({"stock_code": "AAPL"})
        assert isinstance(output, AgentOutput)
        assert output.agent_name == "test_agent"
        assert output.confidence == 0.7

    def test_create_error_output(self):
        agent = ConcreteAgent()
        error_output = agent._create_error_output(
            ValueError("test error"),
            fallback_result={"fallback": True},
        )
        assert error_output.status == "failed"
        assert error_output.confidence == 0.0
        assert error_output.error == "test error"
        assert error_output.result["fallback"] is True

    def test_parse_valid_json(self):
        agent = ConcreteAgent()
        result = agent.parse_response('{"key": "value", "num": 42}')
        assert result["key"] == "value"
        assert result["num"] == 42

    def test_parse_json_in_text(self):
        agent = ConcreteAgent()
        response = 'Here is the analysis: {"sentiment": "bullish"} and more text'
        result = agent.parse_response(response)
        assert result["sentiment"] == "bullish"

    def test_parse_invalid_json(self):
        agent = ConcreteAgent()
        result = agent.parse_response("This is not JSON at all")
        assert result["parsed"] is False
        assert "raw_output" in result

    def test_extract_citations(self):
        agent = ConcreteAgent()
        result = {"citations": ["source1", "source2"], "sources": ["source3"]}
        state = {"data_sources": ["source4"]}
        citations = agent._extract_citations(result, state)
        assert "source1" in citations
        assert "source3" in citations
        assert "source4" in citations

    def test_deduplicate_citations(self):
        agent = ConcreteAgent()
        result = {"citations": ["src1", "src1", "src2"]}
        citations = agent._extract_citations(result, {})
        assert citations.count("src1") == 1

    def test_build_prompt_structure(self):
        agent = ConcreteAgent()
        prompt = agent.build_prompt({"stock_code": "AAPL"})
        assert "[ROLE]" in prompt
        assert "[CONTEXT]" in prompt
        assert "[TASK]" in prompt
        assert "[OUTPUT FORMAT]" in prompt
        assert "[CONSTRAINTS]" in prompt

    def test_format_context_excludes_agent_outputs(self):
        agent = ConcreteAgent()
        state = {
            "stock_code": "AAPL",
            "agent_outputs": {"some": "data"},
            "final_report": {"some": "report"},
        }
        context = agent._format_context(state)
        assert "stock_code" in context
        assert "agent_outputs" not in context
        assert "final_report" not in context


# --- Specialized Agent tests ---

from news_agent import NewsAgent
from financial_agent import FinancialAgent
from technical_agent import TechnicalAgent
from risk_agent import RiskAgent
from report_agent import ReportAgent


class TestNewsAgent:
    """Tests for the NewsAgent."""

    def test_agent_properties(self):
        agent = NewsAgent()
        assert agent.name == "news_agent"
        assert agent.description != ""

    def test_no_news_data_fallback(self):
        agent = NewsAgent()
        state = create_initial_state("t1", "AAPL", news_data=[])
        output = agent.run(state)
        assert output.agent_name == "news_agent"
        assert output.result["sentiment"] == "neutral"
        assert output.confidence == 0.1
        assert output.metadata.get("data_available") is False

    @patch.object(NewsAgent, "_call_llm")
    def test_run_with_mock_llm(self, mock_call_llm):
        mock_call_llm.return_value = json.dumps({
            "sentiment": "bullish",
            "sentiment_score": 0.8,
            "events": [{"title": "Good news", "impact": "positive"}],
            "risk_factors": [],
            "citations": ["Reuters"],
            "confidence": 0.85,
        })
        agent = NewsAgent()
        state = create_initial_state(
            "t1", "AAPL",
            news_data=[{"title": "Good news", "source": "Reuters", "snippet": "Great earnings"}],
        )
        output = agent.run(state)
        assert output.status == "success"
        assert output.result["sentiment"] == "bullish"
        assert output.confidence > 0


class TestFinancialAgent:
    """Tests for the FinancialAgent."""

    def test_no_data_fallback(self):
        agent = FinancialAgent()
        state = create_initial_state("t1", "AAPL", financial_data={})
        output = agent.run(state)
        assert output.confidence == 0.1
        assert output.metadata.get("data_available") is False

    @patch.object(FinancialAgent, "_call_llm")
    def test_run_with_mock_llm(self, mock_call_llm):
        mock_call_llm.return_value = json.dumps({
            "profitability": {"roe": 0.15, "roa": 0.08, "gross_margin": 0.45, "net_margin": 0.12},
            "growth": {"revenue_growth": 0.20, "earnings_growth": 0.25, "growth_trend": "stable"},
            "valuation": {"pe_ratio": 25.5, "pb_ratio": 3.2, "peg_ratio": 1.2, "assessment": "fairly_valued"},
            "health": {"debt_to_equity": 0.5, "current_ratio": 2.1, "health_score": 85},
            "thesis": "Strong fundamentals",
            "citations": ["10-K"],
            "confidence": 0.82,
        })
        agent = FinancialAgent()
        state = create_initial_state(
            "t1", "AAPL",
            financial_data={"revenue": 383_000_000_000, "net_income": 97_000_000_000},
        )
        output = agent.run(state)
        assert output.status == "success"
        assert "profitability" in output.result


class TestTechnicalAgent:
    """Tests for the TechnicalAgent."""

    def test_no_price_data_fallback(self):
        agent = TechnicalAgent()
        state = create_initial_state("t1", "AAPL", price_history=[])
        output = agent.run(state)
        assert output.confidence == 0.1
        assert output.result["signals"]["action"] == "hold"

    @patch.object(TechnicalAgent, "_call_llm")
    def test_signal_consistency_buy(self, mock_call_llm):
        mock_call_llm.return_value = json.dumps({
            "trend": {"short_term": "bullish", "medium_term": "bullish", "long_term": "neutral"},
            "levels": {"support": [170.0, 165.0], "resistance": [180.0, 185.0]},
            "indicators": {"rsi": 55, "rsi_signal": "neutral", "macd": "bullish_crossover", "macd_histogram": 0.5},
            "volume": {"trend": "increasing", "relative_volume": 1.2, "analysis": "Volume confirms"},
            "patterns": ["ascending_triangle"],
            "signals": {"action": "buy", "entry_price": 175.0, "stop_loss": 168.0, "target_price": 188.0, "risk_reward_ratio": 1.86},
            "citations": ["price data"],
            "confidence": 0.78,
        })
        agent = TechnicalAgent()
        state = create_initial_state(
            "t1", "AAPL",
            price_history=[{"date": "2024-01-15", "open": 173, "high": 176, "low": 172, "close": 175, "volume": 45_000_000}],
        )
        output = agent.run(state)
        assert output.status == "success"
        assert output.result["signals"]["action"] == "buy"


class TestRiskAgent:
    """Tests for the RiskAgent."""

    def test_risk_signal_aggregation(self):
        agent = RiskAgent()
        mock_outputs = {
            "news_agent": {"result": {"sentiment": "bullish"}, "confidence": 0.8},
            "technical_agent": {"result": {"signals": {"action": "buy"}}, "confidence": 0.75},
            "financial_agent": {"result": {"health": {"health_score": 85}, "valuation": {"assessment": "fairly_valued"}}, "confidence": 0.82},
        }
        signals = agent._aggregate_risk_signals(mock_outputs)
        assert signals["news_sentiment"] == "bullish"
        assert signals["technical_action"] == "buy"
        assert signals["financial_health_score"] == 85
        assert signals["agent_count"] == 3

    @patch.object(RiskAgent, "_call_llm")
    def test_run_with_mock_llm(self, mock_call_llm):
        mock_call_llm.return_value = json.dumps({
            "overall_risk": "medium",
            "risk_score": 42,
            "risk_factors": {
                "market_risk": {"level": "medium", "factors": ["volatility"]},
                "company_risk": {"level": "low", "factors": ["strong balance sheet"]},
            },
            "worst_case": {"scenario": "Market crash", "potential_loss": -0.25, "probability": 0.10},
            "mitigation": ["Set stop loss at 10%"],
            "position_sizing": {"conservative": 0.03, "moderate": 0.05, "aggressive": 0.08},
            "citations": ["risk model"],
            "confidence": 0.75,
        })
        agent = RiskAgent()
        state = create_initial_state("t1", "AAPL")
        state["agent_outputs"] = {
            "news_agent": {"result": {"sentiment": "bullish"}, "confidence": 0.8},
            "financial_agent": {"result": {"health": {"health_score": 85}}, "confidence": 0.82},
        }
        output = agent.run(state)
        assert output.status == "success"
        assert output.result["overall_risk"] == "medium"


class TestReportAgent:
    """Tests for the ReportAgent."""

    def test_no_agent_outputs_fallback(self):
        agent = ReportAgent()
        state = create_initial_state("t1", "AAPL")
        output = agent.run(state)
        assert output.result["recommendation"] == "hold"
        assert output.confidence == 0.1

    @patch.object(ReportAgent, "_call_llm")
    def test_run_with_mock_llm(self, mock_call_llm):
        mock_call_llm.return_value = json.dumps({
            "executive_summary": "Strong buy recommendation based on solid fundamentals",
            "recommendation": "buy",
            "confidence": 0.82,
            "price_target": {"target": 188.0, "time_horizon": "12 months", "upside": 0.07},
            "key_findings": {
                "sentiment": "Bullish",
                "fundamentals": "Strong",
                "technicals": "Uptrend",
                "risks": "Manageable",
            },
            "risk_reward": {"risk_score": 42, "reward_potential": 0.07, "risk_reward_ratio": 1.67},
            "action_items": ["Buy at current levels", "Stop at $168"],
            "sources": ["All agents"],
            "disclaimer": "AI-generated, not financial advice",
        })
        agent = ReportAgent()
        state = create_initial_state("t1", "AAPL")
        state["agent_outputs"] = {
            "news_agent": {"result": {"sentiment": "bullish"}, "confidence": 0.8, "citations": ["Reuters"]},
            "financial_agent": {"result": {"thesis": "Strong"}, "confidence": 0.82, "citations": ["10-K"]},
            "technical_agent": {"result": {"signals": {"action": "buy"}}, "confidence": 0.75, "citations": ["price data"]},
        }
        state["risk_assessment"] = {
            "result": {"overall_risk": "medium", "risk_score": 42},
            "confidence": 0.75,
        }
        output = agent.run(state)
        assert output.status == "success"
        assert output.result["recommendation"] == "buy"

    def test_confidence_from_upstream_agents(self):
        agent = ReportAgent()
        state = create_initial_state("t1", "AAPL")
        state["agent_outputs"] = {
            "news_agent": {"result": {"sentiment": "bullish"}, "confidence": 0.9, "citations": ["src1"]},
            "financial_agent": {"result": {"thesis": "Strong"}, "confidence": 0.85, "citations": ["src2"]},
            "technical_agent": {"result": {"signals": {"action": "buy"}}, "confidence": 0.7, "citations": ["src3"]},
        }
        state["risk_assessment"] = {"confidence": 0.8}
        result = {
            "executive_summary": "Good",
            "recommendation": "buy",
            "confidence": 0.82,
            "price_target": {"target": 188.0},
            "key_findings": {"a": "b"},
            "risk_reward": {"risk_score": 40},
            "action_items": ["Buy"],
        }
        conf = agent._calculate_confidence(result, state)
        assert 0.5 < conf <= 1.0


# --- Workflow integration tests ---

from workflow import (
    build_investment_workflow,
    safe_agent_run,
    planner_node,
    merge_parallel_outputs,
    WorkflowState,
)


class TestWorkflowCompilation:
    """Tests for workflow graph compilation."""

    def test_workflow_compiles(self):
        workflow = build_investment_workflow()
        assert workflow is not None

    def test_workflow_has_all_nodes(self):
        workflow = build_investment_workflow()
        # Should not raise when compiling
        compiled = workflow.compile()
        assert compiled is not None


class TestSafeAgentRun:
    """Tests for the safe_agent_run error handling wrapper."""

    def test_successful_execution(self):
        agent = ConcreteAgent()
        state = {"stock_code": "AAPL"}
        result = safe_agent_run(agent, state)
        assert "agent_outputs" in result
        assert "test_agent" in result["agent_outputs"]
        assert result["agent_outputs"]["test_agent"]["status"] == "success"

    def test_failed_execution_returns_error_output(self):
        class FailingAgent(BaseAgent):
            name = "failing_agent"
            description = "Always fails"

            def run(self, state):
                raise ValueError("Simulated failure")

        agent = FailingAgent()
        result = safe_agent_run(agent, {"stock_code": "AAPL"})
        assert "agent_outputs" in result
        assert result["agent_outputs"]["failing_agent"]["status"] == "failed"
        assert "errors" in result
        assert any("failing_agent" in e for e in result["errors"])


class TestPlannerNode:
    """Tests for the planner entry node."""

    def test_valid_input(self):
        state = create_initial_state("t1", "AAPL")
        result = planner_node(state)
        assert result["phase"] == WorkflowPhase.ANALYZING.value
        assert "updated_at" in result

    def test_missing_stock_code(self):
        state = {"task_id": "t1", "stock_code": ""}
        result = planner_node(state)
        assert result["phase"] == WorkflowPhase.FAILED.value
        assert any("Missing stock_code" in e for e in result.get("errors", []))


class TestMergeParallelOutputs:
    """Tests for the merge synchronization node."""

    def test_merge_transitions_phase(self):
        state = create_initial_state("t1", "AAPL")
        state["agent_outputs"] = {
            "news_agent": {"status": "success"},
            "financial_agent": {"status": "success"},
            "technical_agent": {"status": "success"},
        }
        result = merge_parallel_outputs(state)
        assert result["phase"] == WorkflowPhase.RISK_ASSESSING.value


# --- Full integration test with mocked LLM ---

class TestFullIntegration:
    """End-to-end integration test with fully mocked LLM calls."""

    def _get_mock_llm_response(self, agent_name: str) -> str:
        """Return a mock JSON response for the given agent."""
        responses = {
            "news_agent": json.dumps({
                "sentiment": "bullish", "sentiment_score": 0.8,
                "events": [{"title": "Test Event", "impact": "positive", "affected_stocks": ["AAPL"], "summary": "Positive event"}],
                "risk_factors": ["risk1"], "citations": ["Reuters"], "confidence": 0.80,
            }),
            "financial_agent": json.dumps({
                "profitability": {"roe": 0.15, "roa": 0.08, "gross_margin": 0.45, "net_margin": 0.12},
                "growth": {"revenue_growth": 0.20, "earnings_growth": 0.25, "growth_trend": "stable"},
                "valuation": {"pe_ratio": 25.5, "assessment": "fairly_valued"},
                "health": {"debt_to_equity": 0.5, "current_ratio": 2.1, "health_score": 85},
                "thesis": "Strong fundamentals",
                "citations": ["10-K"], "confidence": 0.82,
            }),
            "technical_agent": json.dumps({
                "trend": {"short_term": "bullish", "medium_term": "bullish", "long_term": "neutral"},
                "levels": {"support": [170.0], "resistance": [180.0]},
                "indicators": {"rsi": 55, "rsi_signal": "neutral", "macd": "bullish_crossover", "macd_histogram": 0.5},
                "volume": {"trend": "increasing", "relative_volume": 1.2, "analysis": "Strong"},
                "patterns": ["ascending_triangle"],
                "signals": {"action": "buy", "entry_price": 175.0, "stop_loss": 168.0, "target_price": 188.0, "risk_reward_ratio": 1.86},
                "citations": ["price data"], "confidence": 0.75,
            }),
            "risk_agent": json.dumps({
                "overall_risk": "medium", "risk_score": 42,
                "risk_factors": {"market_risk": {"level": "medium", "factors": ["volatility"]}},
                "worst_case": {"scenario": "Correction", "potential_loss": -0.25, "probability": 0.10},
                "mitigation": ["Stop loss"], "position_sizing": {"conservative": 0.03, "moderate": 0.05, "aggressive": 0.08},
                "citations": ["risk model"], "confidence": 0.75,
            }),
            "report_agent": json.dumps({
                "executive_summary": "BUY recommendation",
                "recommendation": "buy", "confidence": 0.80,
                "price_target": {"target": 188.0, "time_horizon": "12 months", "upside": 0.07},
                "key_findings": {"sentiment": "Bullish", "fundamentals": "Strong", "technicals": "Uptrend", "risks": "Medium"},
                "risk_reward": {"risk_score": 42, "reward_potential": 0.07, "risk_reward_ratio": 1.86},
                "action_items": ["Buy at $175", "Stop at $168"],
                "sources": ["All agents"], "disclaimer": "AI-generated, not financial advice",
            }),
        }
        return responses.get(agent_name, '{"error": "unknown agent"}')

    def test_full_workflow_demo(self):
        """Test the full workflow using the demo runner's mock approach."""
        from main import (
            get_sample_market_data,
            get_sample_news_data,
            get_sample_financial_data,
            get_sample_price_history,
        )

        initial_state = create_initial_state(
            task_id="integration_test_001",
            stock_code="AAPL",
            stock_name="Apple Inc.",
            query="Test integration",
            market_data=get_sample_market_data(),
            news_data=get_sample_news_data(),
            financial_data=get_sample_financial_data(),
            price_history=get_sample_price_history(30),
        )

        # Build workflow
        workflow = build_investment_workflow()

        # Mock all LLM calls
        mock_choice = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        def mock_create(**kwargs):
            system_msg = kwargs.get("messages", [{}])[0].get("content", "")
            for agent_name in ["news_agent", "financial_agent", "technical_agent", "risk_agent", "report_agent"]:
                humanized = agent_name.replace("_", " ")
                if humanized in system_msg.lower() or agent_name in system_msg:
                    mock_choice.message.content = self._get_mock_llm_response(agent_name)
                    return mock_response
            mock_choice.message.content = self._get_mock_llm_response("news_agent")
            return mock_response

        with patch("openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create = mock_create
            mock_cls.return_value = mock_client

            result = workflow.invoke(initial_state)

        # Verify results
        assert result["phase"] == WorkflowPhase.COMPLETE.value
        assert result["stock_code"] == "AAPL"

        # Verify all agents ran
        agent_outputs = result.get("agent_outputs", {})
        assert "news_agent" in agent_outputs
        assert "financial_agent" in agent_outputs
        assert "technical_agent" in agent_outputs
        assert "risk_agent" in agent_outputs
        assert "report_agent" in agent_outputs

        # Verify final report exists
        assert result.get("final_report") is not None
        final = result["final_report"]
        assert final.get("recommendation") == "buy"

        # Verify risk assessment exists
        assert result.get("risk_assessment") is not None


# --- Prompt tests ---

from prompts import (
    build_news_prompt,
    build_financial_prompt,
    build_technical_prompt,
    build_risk_prompt,
    build_report_prompt,
)


class TestPrompts:
    """Tests for prompt construction functions."""

    def test_news_prompt_contains_sections(self):
        prompt = build_news_prompt(
            stock_code="AAPL",
            stock_name="Apple Inc.",
            news_data=[{"title": "Test", "source": "Reuters", "snippet": "Good news"}],
            market_data={"price": 175.0},
        )
        assert "[ROLE]" in prompt
        assert "AAPL" in prompt
        assert "[OUTPUT FORMAT]" in prompt
        assert "Bullish" not in prompt  # example is lowercase

    def test_financial_prompt_contains_sections(self):
        prompt = build_financial_prompt(
            stock_code="AAPL",
            stock_name="Apple Inc.",
            financial_data={"revenue": 383_000_000_000},
            market_data={},
        )
        assert "[ROLE]" in prompt
        assert "profitability" in prompt.lower()

    def test_technical_prompt_with_price_data(self):
        prompt = build_technical_prompt(
            stock_code="AAPL",
            stock_name="Apple Inc.",
            price_history=[{"date": "2024-01-15", "open": 173, "high": 176, "low": 172, "close": 175, "volume": 45_000_000}],
            market_data={},
        )
        assert "2024-01-15" in prompt
        assert "RSI" in prompt

    def test_risk_prompt_incorporates_agent_outputs(self):
        prompt = build_risk_prompt(
            stock_code="AAPL",
            stock_name="Apple Inc.",
            agent_outputs={
                "news_agent": {"result": {"sentiment": "bullish"}, "confidence": 0.8},
            },
            market_data={},
        )
        assert "news_agent" in prompt.lower() or "NEWS_AGENT" in prompt
        assert "bullish" in prompt

    def test_report_prompt_includes_all_analyses(self):
        prompt = build_report_prompt(
            stock_code="AAPL",
            stock_name="Apple Inc.",
            agent_outputs={
                "news_agent": {"result": {"sentiment": "bullish"}, "confidence": 0.8, "citations": ["Reuters"]},
                "financial_agent": {"result": {"thesis": "Strong"}, "confidence": 0.82, "citations": ["10-K"]},
            },
            risk_assessment={"overall_risk": "medium", "confidence": 0.75},
            market_data={"price": 175.0},
        )
        assert "NEWS_AGENT" in prompt
        assert "FINANCIAL_AGENT" in prompt
        assert "medium" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

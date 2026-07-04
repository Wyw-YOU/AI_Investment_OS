"""Tests for agent output schema compliance."""
import pytest
from app.agents.state import InvestmentState
from app.agents.finance import FinanceAgent
from app.agents.technical import TechnicalAgent
from app.agents.risk import RiskAgent
from app.agents.judge import JudgeAgent


def validate_output(result: dict) -> list[str]:
    errors = []
    for field in ("output", "confidence", "evidence", "reasoning"):
        if field not in result:
            errors.append(f"missing field: {field}")
    conf = result.get("confidence", -1)
    if not (0.0 <= conf <= 1.0):
        errors.append(f"confidence out of range: {conf}")
    evidence = result.get("evidence", [])
    if not isinstance(evidence, list) or len(evidence) == 0:
        errors.append("evidence must be non-empty list")
    reasoning = result.get("reasoning", "")
    if not isinstance(reasoning, str) or len(reasoning) < 10:
        errors.append("reasoning too short")
    return errors


class TestFinanceAgentSchema:
    def test_with_data(self):
        state = InvestmentState(
            current_stock="600519",
            financial_data={"pe_ratio": 35, "roe": 0.32, "debt_ratio": 0.45},
        )
        result = FinanceAgent().run(state)
        assert validate_output(result) == []
        assert result["output"]["verdict"] in ("undervalued", "fairly_valued", "overvalued")

    def test_empty_data(self):
        state = InvestmentState(current_stock="600519", financial_data={})
        result = FinanceAgent().run(state)
        assert validate_output(result) == []
        assert result["confidence"] < 0.5


class TestTechnicalAgentSchema:
    def test_with_klines(self):
        closes = [100 + i * 0.5 for i in range(50)]
        state = InvestmentState(
            current_stock="600519",
            market_data={"closes": closes},
        )
        result = TechnicalAgent().run(state)
        assert validate_output(result) == []
        assert result["output"]["trend"] in ("bullish", "bearish", "sideways")

    def test_no_data(self):
        state = InvestmentState(current_stock="600519")
        result = TechnicalAgent().run(state)
        assert validate_output(result) == []
        assert result["confidence"] < 0.5


class TestRiskAgentSchema:
    def test_with_prices(self):
        import random
        random.seed(42)
        closes = [100 + random.uniform(-2, 2) for _ in range(60)]
        state = InvestmentState(
            current_stock="600519",
            market_data={"closes": closes},
        )
        result = RiskAgent().run(state)
        assert validate_output(result) == []
        assert result["output"]["risk_level"] in ("LOW", "MEDIUM", "HIGH")


class TestJudgeAgentSchema:
    def test_with_outputs(self):
        state = InvestmentState(current_stock="600519")
        state.set_agent_output("finance", {
            "output": {"verdict": "undervalued"},
            "confidence": 0.8, "evidence": ["e"], "reasoning": "r" * 20,
        })
        state.set_agent_output("technical", {
            "output": {"verdict": "buy"},
            "confidence": 0.7, "evidence": ["e"], "reasoning": "r" * 20,
        })
        state.set_agent_output("news", {
            "output": {"verdict": "positive"},
            "confidence": 0.6, "evidence": ["e"], "reasoning": "r" * 20,
        })
        state.set_agent_output("risk", {
            "output": {"risk_level": "LOW"},
            "confidence": 0.7, "evidence": ["e"], "reasoning": "r" * 20,
        })
        result = JudgeAgent().run(state)
        assert validate_output(result) == []
        assert result["output"]["overall_score"] > 50

    def test_no_outputs(self):
        state = InvestmentState(current_stock="600519")
        result = JudgeAgent().run(state)
        assert validate_output(result) == []
        assert result["confidence"] == 0.0

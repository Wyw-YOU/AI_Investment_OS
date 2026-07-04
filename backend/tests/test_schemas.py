"""Agent output schema validation tests."""
from app.models.schemas import AgentOutput


def test_valid_agent_output():
    output = AgentOutput(
        output={"pe_ratio": 35.2, "verdict": "fairly_valued"},
        confidence=0.82,
        evidence=["PE 35.2 低于行业均值"],
        reasoning="综合基本面指标分析，该股票估值合理偏低位。",
    )
    assert output.confidence == 0.82
    assert len(output.evidence) == 1


def test_confidence_out_of_range():
    import pytest
    with pytest.raises(Exception):
        AgentOutput(
            output={"test": True},
            confidence=1.5,
            evidence=["test"],
            reasoning="This is a test reasoning string.",
        )


def test_empty_evidence():
    import pytest
    with pytest.raises(Exception):
        AgentOutput(
            output={"test": True},
            confidence=0.8,
            evidence=[],
            reasoning="This is a test reasoning string.",
        )

# Agent 输出 Schema — 测试校验规范

## 通用校验函数

```python
def validate_agent_output(result: dict, agent_name: str) -> list[str]:
    """校验 Agent 输出是否符合统一规范，返回错误列表"""
    errors = []

    # 必须字段
    for field in ["output", "confidence", "evidence", "reasoning"]:
        if field not in result:
            errors.append(f"[{agent_name}] 缺少必填字段: {field}")

    # confidence 范围
    conf = result.get("confidence", -1)
    if not (0.0 <= conf <= 1.0):
        errors.append(f"[{agent_name}] confidence={conf}, 应在 0.0-1.0")

    # evidence 非空
    evidence = result.get("evidence", [])
    if not isinstance(evidence, list) or len(evidence) == 0:
        errors.append(f"[{agent_name}] evidence 不能为空列表")

    # reasoning 非空
    reasoning = result.get("reasoning", "")
    if not isinstance(reasoning, str) or len(reasoning) < 10:
        errors.append(f"[{agent_name}] reasoning 长度不足 10 字符")

    return errors
```

## 各 Agent 特定字段校验

### FinanceAgent
```python
REQUIRED_OUTPUT_FIELDS = ["pe_ratio", "pb_ratio", "roe", "verdict"]
VALID_VERDICTS = ["undervalued", "fairly_valued", "overvalued"]
```

### TechnicalAgent
```python
REQUIRED_OUTPUT_FIELDS = ["trend", "indicators", "verdict"]
VALID_TRENDS = ["bullish", "bearish", "sideways"]
VALID_VERDICTS = ["buy", "sell", "hold"]
```

### NewsAgent
```python
REQUIRED_OUTPUT_FIELDS = ["sentiment_score", "sentiment", "key_events"]
VALID_SENTIMENTS = ["positive", "negative", "neutral"]
assert -1.0 <= result["output"]["sentiment_score"] <= 1.0
```

### RiskAgent
```python
REQUIRED_OUTPUT_FIELDS = ["risk_level", "volatility_30d", "verdict"]
VALID_RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
VALID_VERDICTS = ["acceptable", "caution", "dangerous"]
```

## 测试用例模板

```python
import pytest
from app.agents.finance import FinanceAgent
from app.agents.state import InvestmentState

class TestFinanceAgent:
    def setup_method(self):
        self.agent = FinanceAgent()

    def test_output_schema_completeness(self):
        state = InvestmentState(current_stock="600519", financial_data=MOCK_DATA)
        result = self.agent.run(state)
        errors = validate_agent_output(result, "FinanceAgent")
        assert errors == [], f"Schema errors: {errors}"

    def test_low_data_yields_low_confidence(self):
        state = InvestmentState(current_stock="600519", financial_data={})
        result = self.agent.run(state)
        assert result["confidence"] < 0.5

    def test_verdict_is_valid_enum(self):
        state = InvestmentState(current_stock="600519", financial_data=MOCK_DATA)
        result = self.agent.run(state)
        assert result["output"]["verdict"] in ["undervalued", "fairly_valued", "overvalued"]
```

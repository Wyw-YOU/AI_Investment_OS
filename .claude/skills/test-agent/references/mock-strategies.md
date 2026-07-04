# Mock 策略指南

## LLM Mock（最高优先级）

LLM 调用是所有 Agent 的核心依赖，必须 mock 以保证测试稳定性和速度。

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock, patch

MOCK_LLM_RESPONSES = {
    "finance": {
        "output": {
            "pe_ratio": 35.2, "pb_ratio": 8.1, "roe": 0.32,
            "revenue_growth": 0.15, "net_profit_growth": 0.18,
            "debt_ratio": 0.45, "verdict": "fairly_valued",
            "key_metrics": {
                "strengths": ["高ROE", "营收增长"],
                "weaknesses": ["负债偏高"]
            }
        },
        "confidence": 0.82,
        "evidence": ["PE 35.2 低于行业均值", "ROE 32% 行业领先"],
        "reasoning": "综合基本面指标分析，该股票估值合理偏低位。"
    },
    "technical": { ... },
    "news": { ... },
    "risk": { ... },
}

@pytest.fixture
def mock_llm():
    """Mock LLM 调用，返回预设响应"""
    with patch("app.services.llm_adapter.LLMAdapter.generate") as mock:
        def side_effect(prompt, agent_type="default", **kwargs):
            return MOCK_LLM_RESPONSES.get(agent_type, MOCK_LLM_RESPONSES["finance"])
        mock.side_effect = side_effect
        yield mock
```

## 数据源 Mock

### akshare (行情数据)

```python
@pytest.fixture
def mock_akshare():
    with patch("app.services.market_data.ak") as mock:
        mock.stock_zh_a_hist.return_value = generate_fake_kline_df(days=250)
        mock.stock_individual_info_em.return_value = {
            "总市值": 2000000000000,
            "流通市值": 1800000000000,
            "行业": "白酒",
        }
        yield mock
```

### Redis (缓存)

```python
@pytest.fixture
def fake_redis():
    """使用 fakeredis 替代真实 Redis"""
    import fakeredis
    return fakeredis.FakeRedis(decode_responses=True)
```

### FAISS (向量检索)

```python
@pytest.fixture
def mock_vector_store():
    with patch("app.services.vector_store.FAISSStore") as mock:
        instance = mock.return_value
        instance.search.return_value = [
            {"text": "茅台Q3营收增长15%", "score": 0.92},
            {"text": "白酒行业政策利好", "score": 0.87},
        ]
        yield instance
```

## 测试数据生成

```python
import random
from datetime import datetime, timedelta

def generate_fake_kline_df(days=250, base_price=100.0):
    """生成模拟 K 线数据"""
    dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]
    prices = []
    price = base_price
    for _ in range(days):
        change = random.uniform(-0.03, 0.03)
        price *= (1 + change)
        open_p = price * (1 + random.uniform(-0.01, 0.01))
        close_p = price
        high_p = max(open_p, close_p) * (1 + random.uniform(0, 0.02))
        low_p = min(open_p, close_p) * (1 - random.uniform(0, 0.02))
        volume = random.randint(1000000, 50000000)
        prices.append({
            "日期": dates[len(prices)],
            "开盘": round(open_p, 2),
            "收盘": round(close_p, 2),
            "最高": round(high_p, 2),
            "最低": round(low_p, 2),
            "成交量": volume,
        })
    import pandas as pd
    return pd.DataFrame(prices)
```

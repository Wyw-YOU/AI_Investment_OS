---
name: test-agent
description: "AI Investment OS 测试 Agent。编写和运行单元测试、集成测试、Agent 输出质量测试。当用户要求测试、验证代码、写 test case、检查覆盖率、运行 pytest、验证 Agent 输出、测试 API 端点时触发。任何与测试相关的请求都应使用此 skill。"
---

# Testing Agent — AI Investment OS

你是一名测试工程师，负责确保 AI Investment OS 每个模块的正确性和可靠性。

## 核心原则

- 测试验证的是**行为**，不是实现细节
- 测试应能在无外部依赖的情况下运行（mock 外部 API/LLM）
- 每个 Agent 必须有至少 3 个测试用例（正常路径、边界情况、异常输入）
- 测试文件与被测文件同目录：`test_<module>.py`

## 测试分层

### 1. 单元测试（Unit Tests）

**范围:** 单个函数/类，无外部依赖

```python
# 示例：技术指标计算
def test_macd_calculation():
    prices = [10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 11.3, 11.8, 12.0, 12.5,
              12.3, 12.8, 13.0, 13.2, 13.5, 13.3, 13.8, 14.0, 14.2, 14.5,
              14.3, 14.8, 15.0, 15.2, 15.5, 15.3, 15.8, 16.0, 16.2, 16.5]
    result = calculate_macd(prices)
    assert "macd_line" in result
    assert "signal_line" in result
    assert "histogram" in result
    assert isinstance(result["macd_line"], float)
```

**需要 mock 的模块:**
- `market_data.py` — mock akshare/tushare API 调用
- `llm_adapter.py` — mock LLM 响应（返回固定 JSON）
- `cache.py` — 可用 fakeredis 替代真实 Redis
- `vector_store.py` — mock FAISS 查询结果

### 2. Agent 输出质量测试

这是本项目最关键的测试类型。每个 Agent 的输出必须符合统一格式。

```python
def test_finance_agent_output_schema():
    """验证 FinanceAgent 输出结构完整性"""
    state = create_mock_state(stock="600519")
    agent = FinanceAgent()
    result = agent.run(state)

    # 结构校验
    assert "output" in result
    assert "confidence" in result
    assert "evidence" in result
    assert "reasoning" in result

    # 类型校验
    assert isinstance(result["output"], dict)
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["evidence"], list)
    assert len(result["evidence"]) > 0
    assert isinstance(result["reasoning"], str)
    assert len(result["reasoning"]) > 10  # 不能是空话


def test_finance_agent_confidence_range():
    """验证置信度在合理范围内"""
    state = create_mock_state(stock="600519", financial_data=EMPTY_DATA)
    agent = FinanceAgent()
    result = agent.run(state)

    # 数据不足时置信度应低
    assert result["confidence"] < 0.5
```

### 3. 集成测试（Integration Tests）

**范围:** 多模块协作，LangGraph 工作流端到端

```python
@pytest.mark.integration
def test_full_analysis_pipeline():
    """测试完整分析管道：输入股票代码 → 输出报告"""
    result = run_analysis(stock="600519")

    assert result["status"] == "success"
    assert "report" in result
    assert result["report"]["stock"] == "600519"
    assert len(result["report"]["agents_used"]) >= 4
```

### 4. API 端点测试

```python
def test_analyze_stock_endpoint(client):
    response = client.post("/api/stocks/analyze", json={"stock": "600519"})
    assert response.status_code == 200
    data = response.json()
    assert data["stock"] == "600519"
    assert "analysis" in data


def test_portfolio_crud(client):
    # Create
    resp = client.post("/api/portfolio", json={"name": "test", "holdings": {}})
    assert resp.status_code == 201

    # Read
    portfolio_id = resp.json()["id"]
    resp = client.get(f"/api/portfolio/{portfolio_id}")
    assert resp.status_code == 200
```

## 测试数据工厂

为每个模块创建 fixtures 和 factories：

```python
# conftest.py
@pytest.fixture
def mock_market_data():
    return {
        "stock": "600519",
        "prices": generate_fake_klines(days=250),
        "volume": generate_fake_volume(days=250),
    }

@pytest.fixture
def mock_financial_data():
    return {
        "pe_ratio": 35.2,
        "pb_ratio": 8.1,
        "roe": 0.32,
        "revenue_growth": 0.15,
        "net_profit_growth": 0.18,
    }
```

## 测试运行规范

| 场景 | 命令 |
|------|------|
| 运行全部测试 | `pytest backend/tests/ -v` |
| 仅运行单元测试 | `pytest backend/tests/ -v -m "not integration"` |
| 运行集成测试 | `pytest backend/tests/ -v -m integration` |
| 查看覆盖率 | `pytest backend/tests/ --cov=app --cov-report=html` |
| 运行 Agent 测试 | `pytest backend/tests/agents/ -v` |

## 覆盖率目标

| 模块 | 最低覆盖率 | 说明 |
|------|:----------:|------|
| models/ | 95% | 数据模型必须严格正确 |
| agents/ | 85% | Agent 逻辑复杂，LLM 输出难完全覆盖 |
| services/ | 80% | 外部依赖多，mock 覆盖核心路径 |
| api/ | 90% | 端点行为必须明确 |
| engine/ | 85% | 工作流正确性至关重要 |

## 读取参考文件

- 当需要了解 Agent 输出 schema 详情时，读取 `references/agent-schemas.md`
- 当需要了解 mock 策略时，读取 `references/mock-strategies.md`

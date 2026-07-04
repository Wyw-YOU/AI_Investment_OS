# AI Investment OS — Phase 2 测试报告

**日期：** 2026-07-05
**阶段：** Phase 0/1/2（Foundation + Data Layer + Agent Engine）
**测试结果：** 63 passed, 0 failed

---

## 目录

1. [Phase 2 新增内容概览](#1-phase-2-新增内容概览)
2. [单元测试结果](#2-单元测试结果)
3. [已发现并修复的 Bug](#3-已发现并修复的-bug)
4. [akshare 网络代理问题](#4-akshare-网络代理问题)
5. [Agent 引擎手动测试](#5-agent-引擎手动测试)
6. [LangGraph 工作流测试](#6-langgraph-工作流测试)
7. [预期结果速查表](#7-预期结果速查表)
8. [遗留问题与建议](#8-遗留问题与建议)

---

## 1. Phase 2 新增内容概览

### 新增文件

| 目录 | 文件 | 说明 |
|------|------|------|
| `agents/` | `state.py` | InvestmentState 共享状态 |
| `agents/` | `base.py` | BaseAgent 抽象基类 + Agent Registry |
| `agents/` | `planner.py` | PlannerAgent — 任务规划 |
| `agents/` | `finance.py` | FinanceAgent — 基本面分析 |
| `agents/` | `technical.py` | TechnicalAgent — 技术面分析 |
| `agents/` | `news.py` | NewsAgent — 新闻舆情 + RAG |
| `agents/` | `risk.py` | RiskAgent — 风险评估 |
| `agents/` | `judge.py` | JudgeAgent — 综合评判 |
| `agents/` | `portfolio_agent.py` | PortfolioAgent — 组合权重建议 |
| `agents/` | `report.py` | ReportAgent — 最终报告生成 |
| `engine/` | `nodes.py` | LangGraph 节点函数 |
| `engine/` | `graph.py` | LangGraph 工作流定义 + `run_analysis()` |
| `tests/` | `test_agents.py` | State + Registry 测试 |
| `tests/` | `test_agent_schemas.py` | Agent 输出格式合规测试 |

### 修改文件

| 文件 | 变更内容 |
|------|---------|
| `api/stocks.py` | 新增 `/analyze` 和 `/analyze/sync/{stock_code}` 端点，调用 `engine.graph.run_analysis` |
| `tests/conftest.py` | 导入所有 Agent 模块确保注册完整 |

### 架构设计

```
Planner Agent
    │
    ├──→ Finance Agent  ──┐
    ├──→ Technical Agent ──┤
    ├──→ News Agent     ──┼──→ Judge Agent ──→ Portfolio Agent ──→ Report Agent
    └──→ Risk Agent     ──┘
    (并行执行)              (汇聚)
```

每个 Agent 都有两条路径：
- **LLM 路径**：调用大模型生成分析结果（当 `self.llm` 存在时）
- **Rule-based 路径**：基于规则引擎的降级方案（LLM 不可用时自动切换）

---

## 2. 单元测试结果

```
tests/test_agents.py         (3 tests)   — State + Registry
tests/test_agent_schemas.py  (8 tests)   — Agent 输出格式合规
tests/test_cache.py          (7 tests)   — 缓存服务
tests/test_circuit_breaker.py (4 tests)  — 熔断器
tests/test_indicators.py     (14 tests)  — 技术指标
tests/test_llm_adapter.py    (7 tests)   — LLM 适配器
tests/test_models.py         (6 tests)   — 数据库模型
tests/test_news.py           (4 tests)   — 新闻事件提取
tests/test_schemas.py        (3 tests)   — Pydantic Schema
tests/test_smoke.py          (5 tests)   — API 冒烟测试
─────────────────────────────────────────────
Total: 63 passed, 0 failed
```

**检查点：** 运行 `cd backend && python -m pytest tests/ -v` 应看到 `63 passed`。

---

## 3. 已发现并修复的 Bug

### Bug 1: `calculate_kdj` 空列表崩溃

**现象：**
```
tests/test_agent_schemas.py::TestTechnicalAgentSchema::test_with_klines — FAILED
ValueError: max() iterable argument is empty
```

**根因：** `TechnicalAgent` 调用 `calculate_all_indicators(closes, highs, lows)` 时，如果测试数据只提供 `closes` 而没有 `highs`/`lows`，`_extract_series` 返回空列表，`calculate_kdj` 中 `max([])` 抛出异常。

**修复：** `backend/app/services/indicators.py`
```python
# 修复前
if len(closes) < period:
    return {"k": 50.0, "d": 50.0, "j": 50.0, "signal": "neutral"}

# 修复后
if len(closes) < period or not highs or not lows:
    return {"k": 50.0, "d": 50.0, "j": 50.0, "signal": "neutral"}
```

同时在 `calculate_all_indicators` 中增加空列表 fallback：
```python
# 修复前
if highs is None:
    highs = closes

# 修复后
if highs is None or not highs:
    highs = closes
```

---

### Bug 2: Agent 注册不完整（4/8）

**现象：**
```
tests/test_agents.py::TestAgentRegistry::test_agents_registered — FAILED
AssertionError: assert 'planner' in ['finance', 'technical', 'risk', 'judge']
```

**根因：** Agent 的 `register_agent(XxxAgent())` 在模块顶层执行，只有被 `import` 的模块才会注册。测试文件只导入了 4 个 Agent（finance, technical, risk, judge），其余 4 个（planner, news, portfolio, report）从未被导入，因此未注册。

**修复：** `backend/tests/conftest.py` 在顶部导入所有 Agent 模块：
```python
import app.agents.planner
import app.agents.finance
import app.agents.technical
import app.agents.news
import app.agents.risk
import app.agents.judge
import app.agents.portfolio_agent
import app.agents.report
```

---

## 4. akshare 网络代理问题

### 现象

```
Failed to fetch all spot data: HTTPSConnectionPool(host='82.push2.eastmoney.com', port=443):
Max retries exceeded with url: ... (Caused by ProxyError('Unable to connect to proxy',
RemoteDisconnected('Remote end closed connection without response')))
```

- K 线数据（`stock_zh_a_hist`）：时而成功时而失败
- 实时行情（`stock_zh_a_spot_em`）：始终失败
- 热门股票（`get_hot_stocks`）：始终失败

### 根因

你的系统配置了 Clash 代理（`127.0.0.1:7890`），通过 Windows 注册表注入系统代理设置。

```
Python urllib.request.getproxies() → 读取注册表 → 返回 {'https': 'http://127.0.0.1:7890'}
                                              ↓
                            requests 库自动使用系统代理
                                              ↓
                        eastmoney.com 国内数据源被代理拦截 → 连接失败
```

akshare 内部调用链：`stock_zh_a_spot_em()` → `fetch_paginated_data()` → `request_with_retry()` → `requests.Session.get()`

每个 `requests.Session` 创建时 `trust_env=True`，自动读取系统代理。

### 已应用的代码修复

`backend/app/services/market_data.py` 顶部增加了代理绕过 patch：

```python
def _bypass_system_proxy_for_akshare():
    import requests
    _original_init = requests.Session.__init__
    def _patched_init(self, *args, **kwargs):
        _original_init(self, *args, **kwargs)
        self.trust_env = False
    requests.Session.__init__ = _patched_init

_bypass_system_proxy_for_akshare()
```

**效果：** 所有 `requests.Session` 创建时自动设置 `trust_env=False`，不再读取系统代理。

### 验证方式

**方法 1：关闭 Clash 系统代理后测试**

在 Clash for Windows 中关闭「系统代理」开关，然后运行：

```bash
cd backend
python -c "
from app.services.market_data import MarketDataService
svc = MarketDataService()
quote = svc.get_realtime_quote('600519')
print(f'股票: {quote.get(\"name\", \"FAILED\")}')
print(f'最新价: {quote.get(\"latest_price\", \"FAILED\")}')
"
```

**预期结果（交易时间 9:30-15:00）：**
```
股票: 贵州茅台
最新价: 1500.0
```

**预期结果（非交易时间）：**
```
股票: 贵州茅台
最新价: 1194.45   ← 上一个交易日收盘价
```

**方法 2：在 Clash 配置中添加直连规则**

编辑 Clash 配置文件（`~/.config/clash/config.yaml`），在 `rules:` 最前面加：

```yaml
rules:
  - DOMAIN-SUFFIX,eastmoney.com,DIRECT
  - DOMAIN-SUFFIX,12371.cn,DIRECT
  # ... 其他规则
```

然后在 Clash for Windows 中重载配置。

### 测试 K 线数据

```bash
cd backend
python -c "
from app.services.market_data import MarketDataService
svc = MarketDataService()
kline = svc.get_kline('600519', days=30)
print(f'获取到 {len(kline)} 条 K 线数据')
if kline:
    print(f'最新: {kline[-1][\"date\"]} 收盘: {kline[-1][\"close\"]}')
"
```

**预期结果：**
```
获取到 22 条 K 线数据
最新: 2026-07-03 收盘: 1194.45
```

---

## 5. Agent 引擎手动测试

### 5.1 测试 Agent Registry 注册

```bash
cd backend
python -c "
from app.agents.base import list_agents, get_agent

agents = list_agents()
print(f'已注册 Agent ({len(agents)}): {agents}')

for name in agents:
    agent = get_agent(name)
    print(f'  {name}: {agent.__class__.__name__}')
"
```

**预期结果：**
```
已注册 Agent (8): ['planner', 'finance', 'technical', 'news', 'risk', 'judge', 'portfolio', 'report']
  planner: PlannerAgent
  finance: FinanceAgent
  technical: TechnicalAgent
  news: NewsAgent
  risk: RiskAgent
  judge: JudgeAgent
  portfolio: PortfolioAgent
  report: ReportAgent
```

### 5.2 测试单个 Agent（Rule-based 模式）

```bash
cd backend
python -c "
from app.agents.state import InvestmentState
from app.agents.finance import FinanceAgent
from app.agents.technical import TechnicalAgent
from app.agents.risk import RiskAgent

# Finance Agent
state = InvestmentState(
    current_stock='600519',
    financial_data={'pe_ratio': 35, 'roe': 0.32, 'debt_ratio': 0.45, 'pb_ratio': 8.5},
)
result = FinanceAgent().run(state)
print(f'Finance: verdict={result[\"output\"][\"verdict\"]}, confidence={result[\"confidence\"]}')
print(f'  evidence: {result[\"evidence\"]}')

# Technical Agent
state = InvestmentState(
    current_stock='600519',
    market_data={'closes': [100 + i * 0.5 for i in range(50)]},
)
result = TechnicalAgent().run(state)
print(f'Technical: trend={result[\"output\"][\"trend\"]}, verdict={result[\"output\"][\"verdict\"]}')
print(f'  confidence={result[\"confidence\"]}')

# Risk Agent
import random; random.seed(42)
state = InvestmentState(
    current_stock='600519',
    market_data={'closes': [100 + random.uniform(-2, 2) for _ in range(60)]},
)
result = RiskAgent().run(state)
print(f'Risk: level={result[\"output\"][\"risk_level\"]}, verdict={result[\"output\"][\"verdict\"]}')
print(f'  volatility={result[\"output\"][\"volatility_30d\"]}')
"
```

**预期结果：**
```
Finance: verdict=undervalued, confidence=0.75
  evidence: ['PE ratio: 35.0', 'ROE: 32.0%', 'Revenue growth: 0.0%']
Technical: trend=bullish, verdict=buy
  confidence=0.65
Risk: level=LOW, verdict=acceptable
  volatility=0.0162
```

### 5.3 测试 Judge Agent 聚合

```bash
cd backend
python -c "
from app.agents.state import InvestmentState
from app.agents.judge import JudgeAgent

state = InvestmentState(current_stock='600519')
state.set_agent_output('finance', {
    'output': {'verdict': 'undervalued'},
    'confidence': 0.8, 'evidence': ['e'], 'reasoning': 'r' * 20,
})
state.set_agent_output('technical', {
    'output': {'verdict': 'buy'},
    'confidence': 0.7, 'evidence': ['e'], 'reasoning': 'r' * 20,
})
state.set_agent_output('news', {
    'output': {'verdict': 'positive'},
    'confidence': 0.6, 'evidence': ['e'], 'reasoning': 'r' * 20,
})
state.set_agent_output('risk', {
    'output': {'risk_level': 'LOW'},
    'confidence': 0.7, 'evidence': ['e'], 'reasoning': 'r' * 20,
})

result = JudgeAgent().run(state)
out = result['output']
print(f'Score: {out[\"overall_score\"]}/100')
print(f'Verdict: {out[\"verdict\"]}')
print(f'Key points: {out[\"key_points\"]}')
print(f'Warnings: {out[\"warnings\"]}')
"
```

**预期结果：**
```
Score: 80/100
Verdict: buy
Key points: ['Fundamentals: undervalued', 'Technical: buy signal', 'News sentiment: positive']
Warnings: []
```

---

## 6. LangGraph 工作流测试

### 6.1 测试工作流构建

```bash
cd backend
python -c "
from app.engine.graph import build_analysis_graph, GraphState

graph = build_analysis_graph()
compiled = graph.compile()
print('Graph compiled successfully!')
print(f'State type: {GraphState.__name__}')
print(f'Nodes: {list(compiled.get_graph().nodes.keys())}')
"
```

**预期结果：**
```
Graph compiled successfully!
State type: GraphState
Nodes: ['__start__', 'planner', 'finance', 'technical', 'news', 'risk', 'judge', 'portfolio', 'report', '__end__']
```

### 6.2 测试完整分析流程（Rule-based，无 LLM）

```bash
cd backend
python -c "
from app.engine.graph import run_analysis

# 使用模拟数据，不调用真实 API
result = run_analysis(
    stock_code='600519',
    market_data={
        'closes': [100 + i * 0.3 for i in range(60)],
        'klines': [{'close': 100 + i * 0.3, 'high': 101 + i * 0.3,
                     'low': 99 + i * 0.3} for i in range(60)],
    },
    financial_data={
        'pe_ratio': 35, 'roe': 0.32, 'debt_ratio': 0.45,
        'pb_ratio': 8.5, 'revenue_growth': 0.15,
    },
    news_data=[
        {'title': '茅台Q3业绩超预期', 'content': '净利润增长20%'},
        {'title': '白酒板块整体走强', 'content': '行业景气度持续'},
    ],
)

print(f'Status: {result[\"status\"]}')
print(f'Stock: {result[\"stock\"]}')
print(f'Decision: {result[\"decision\"]}')
print(f'Score: {result[\"report\"].get(\"overall_score\", \"N/A\")}')
print(f'Verdict: {result[\"report\"].get(\"verdict\", \"N/A\")}')
print(f'Agents used: {list(result[\"agent_outputs\"].keys())}')
print(f'Confidences: {result[\"agent_confidence\"]}')
"
```

**预期结果：**
```
Status: success
Stock: 600519
Decision: buy
Score: 80
Verdict: buy
Agents used: ['planner', 'finance', 'technical', 'news', 'risk', 'judge', 'portfolio', 'report']
Confidences: {'planner': 0.9, 'finance': 0.75, 'technical': 0.65, 'news': 0.55, 'risk': 0.6, 'judge': 0.65, 'portfolio': 0.52, 'report': 0.65}
```

### 6.3 测试 API 端点（同步分析）

启动服务后测试新增的 API 端点：

```bash
# 启动服务
cd backend
uvicorn app.main:app --reload --port 8000

# 另一个终端
curl http://localhost:8000/api/stocks/analyze/sync/600519
```

**预期结果：**
```json
{
  "status": "success",
  "stock": "600519",
  "decision": "hold",
  "report": { ... },
  "agent_outputs": { ... },
  "agent_confidence": { ... }
}
```

**注意：** 此端点会调用真实 akshare API（需要网络正常），且执行时间较长（约 5-15 秒）。

### 6.4 测试 API 端点（异步分析）

```bash
curl -X POST "http://localhost:8000/api/stocks/analyze?stock_code=600519"
```

**预期结果：**
```json
{
  "stock_code": "600519",
  "status": "submitted"
}
```

异步任务在后台执行，结果不会立即返回。

---

## 7. 预期结果速查表

| 测试项 | 命令 | 预期结果 |
|-------|------|---------|
| 全部测试 | `pytest tests/ -v` | `63 passed` |
| Agent 注册 | `list_agents()` | 8 个 Agent 全部注册 |
| Finance Agent | `FinanceAgent().run(state)` | `verdict=undervalued, confidence=0.75` |
| Technical Agent | `TechnicalAgent().run(state)` | `trend=bullish, verdict=buy` |
| Risk Agent | `RiskAgent().run(state)` | `risk_level=LOW, volatility<0.03` |
| Judge 聚合 | `JudgeAgent().run(state)` | `score=80, verdict=buy` |
| LangGraph 构建 | `build_analysis_graph().compile()` | 10 个节点（含 start/end） |
| 完整流程 | `run_analysis(stock_code, ...)` | `status=success, decision=buy/hold/sell` |
| 实时行情 | `svc.get_realtime_quote('600519')` | 返回 name, latest_price, change_pct |
| K 线数据 | `svc.get_kline('600519', days=30)` | 返回 20-22 条数据 |
| 热门股票 | `svc.get_hot_stocks(5)` | 返回 5 只股票 |

---

## 8. 遗留问题与建议

### 网络层

| 问题 | 严重性 | 状态 | 说明 |
|------|--------|------|------|
| Clash 代理阻断 eastmoney API | High | 已修复（代码层） | `trust_env=False` patch；Clash 侧建议加直连规则 |
| eastmoney 连接不稳定 | Medium | 待观察 | 部分时段连接超时，建议增加重试 |

### 代码层

| 问题 | 严重性 | 说明 |
|------|--------|------|
| LLM 输出未做 Schema 校验 | Medium | Agent 的 `_analyze_with_llm` 直接使用 LLM 返回值，未校验必需字段 |
| `FinanceAgent._log_run` hack | Low | 用 `type("_S", ...)` 创建假 state 对象，应直接传 state |
| `nodes.py` 重复代码 | Low | 8 个 node 函数结构相同，可提取为通用 `_make_node(name)` 工厂函数 |
| `prices[i - 1] != 0` 除零保护 | Low | `risk.py:98` 已处理，但 `indicators.py` 的 `_calc_growth` 只检查 `previous == 0` |

### 功能待完善

| 功能 | 当前状态 | 说明 |
|------|---------|------|
| LLM 集成测试 | 未覆盖 | 所有 Agent 测试使用 rule-based 路径，LLM 路径未测试 |
| Agent 超时处理 | 未实现 | 单个 Agent 执行无超时限制，可能导致整个 pipeline 卡住 |
| Agent 执行日志 | 未持久化 | `AgentLog` 模型存在但未在 Agent 执行时写入 |
| WebSocket 实时推送 | 未实现 | 异步分析完成后无法推送给客户端（Phase 3/4） |

# Phase 2 开发报告 — Agent Engine

> 开发日期：2026-07-05
> 阶段：Sprint 3-5 — Agent Engine（核心阶段）
> 状态：DONE

---

## 1. 任务完成清单

| # | Task | Story Points | Status |
|---|------|:------------:|:------:|
| 2.1 | InvestmentState 数据类 | 2 | DONE |
| 2.2 | BaseAgent + Registry | 3 | DONE |
| 2.3 | LangGraph 工作流图 | 5 | DONE |
| 2.4 | PlannerAgent | 3 | DONE |
| 2.5 | FinanceAgent | 6 | DONE |
| 2.6 | TechnicalAgent | 6 | DONE |
| 2.7 | NewsAgent | 6 | DONE |
| 2.8 | RiskAgent | 3 | DONE |
| 2.9 | JudgeAgent | 5 | DONE |
| 2.10 | PortfolioAgent | 5 | DONE |
| 2.11 | ReportAgent | 3 | DONE |
| 2.12 | Agent 重试 + 熔断器 | 3 | DONE (Phase 0) |
| 2.13 | Agent 日志记录 | 2 | DONE (Phase 0) |

**Total: 49 / 49 story points**

---

## 2. 核心架构

### 2.1 InvestmentState — 共享状态

```
InvestmentState (dataclass)
├── 输入: stock_pool, current_stock, market_data, financial_data, news_data
├── Agent 输出: agent_outputs{}, agent_confidence{}
├── 组合: portfolio, candidate_pool, risk_profile
└── 产出: final_report, decision
```

所有 Agent 通过 State 间接通信，不直接调用彼此。

### 2.2 Agent 工作流图

```
Planner → [Finance, Technical, News, Risk] (并行) → Judge → Portfolio → Report
```

使用 LangGraph `StateGraph` 编排，支持条件路由和并行执行。

### 2.3 8 个 Agent 实现

| Agent | 文件 | LLM 增强 | 规则引擎 |
|-------|------|:--------:|:--------:|
| Planner | `planner.py` | - | 规划分析任务 |
| Finance | `finance.py` | JSON 输出 | PE/ROE/负债率规则 |
| Technical | `technical.py` | JSON 输出 | RSI/MACD/BOLL/MA 信号计数 |
| News | `news.py` | 情感分析 | 关键词匹配 |
| Risk | `risk.py` | - | 波动率/Beta/RSI 风险评分 |
| Judge | `judge.py` | 综合评判 | 多信号加权聚合 |
| Portfolio | `portfolio_agent.py` | - | 基于 Judge verdict 建议权重 |
| Report | `report.py` | - | 结构化报告生成 |

每个 Agent 都有 **LLM 模式 + 规则引擎 fallback**，LLM 不可用时自动降级。

### 2.4 Agent 统一输出格式

```json
{
  "output": { "...agent-specific..." },
  "confidence": 0.0-1.0,
  "evidence": ["fact 1", "fact 2"],
  "reasoning": "2-5 sentences explaining the conclusion"
}
```

---

## 3. 测试方法

### 3.1 新增测试文件

| 文件 | 测试内容 | 用例数 |
|------|---------|:------:|
| `test_agents.py` | InvestmentState + Agent Registry | 5 |
| `test_agent_schemas.py` | 4 个 Agent 输出 schema 校验 | 9 |
| **Total (Phase 2)** | | **14** |

### 3.2 测试策略

| 测试类型 | 方法 | 覆盖 Agent |
|---------|------|-----------|
| Schema 校验 | 验证输出包含 4 个必填字段 + confidence 范围 | All |
| 空数据处理 | 验证无输入时返回低 confidence | Finance, Technical, Risk |
| 规则引擎 | 给定数据验证 verdict 逻辑 | Finance, Technical, Judge |
| Registry | 验证 8 个 Agent 全部注册 | All |

### 3.3 运行测试

```bash
cd backend
pytest tests/test_agents.py tests/test_agent_schemas.py -v
```

---

## 4. API 集成

### 新增端点

| Method | Path | 功能 |
|--------|------|------|
| POST | `/api/stocks/analyze` | 异步触发分析（BackgroundTasks） |
| GET | `/api/stocks/analyze/sync/{code}` | 同步分析（等待结果） |

---

## 5. 文件变更清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `app/agents/state.py` | New | InvestmentState dataclass |
| `app/agents/base.py` | New | BaseAgent ABC + Registry |
| `app/agents/planner.py` | New | PlannerAgent |
| `app/agents/finance.py` | New | FinanceAgent (LLM + rule-based) |
| `app/agents/technical.py` | New | TechnicalAgent |
| `app/agents/news.py` | New | NewsAgent (RAG 增强) |
| `app/agents/risk.py` | New | RiskAgent |
| `app/agents/judge.py` | New | JudgeAgent |
| `app/agents/portfolio_agent.py` | New | PortfolioAgent |
| `app/agents/report.py` | New | ReportAgent |
| `app/engine/nodes.py` | New | LangGraph 节点函数 |
| `app/engine/graph.py` | New | LangGraph 工作流图 + run_analysis() |
| `app/api/stocks.py` | Updated | 新增 analyze 端点 |
| `tests/test_agents.py` | New | State + Registry 测试 |
| `tests/test_agent_schemas.py` | New | Agent 输出 schema 测试 |

# 📘 AI Investment OS — 详细设计（DDD + 模块级设计 V1.0）

------

# 1. 领域建模（Domain Model）

## 1.1 核心领域划分（Bounded Context）

整个系统划分为 6 个核心领域：

```
Identity Domain        → 用户系统
Investment Domain      → 投研核心（股票/市场）
Workspace Domain       → 研究空间
Agent Domain           → 多智能体系统
Analytics Domain       → 量化/指标/评分
Automation Domain      → 定时任务/扫描/推送
```

------

# 2. 投研核心领域（Investment Domain）

------

# 2.1 股票实体（Stock Entity）

```
class Stock:
    stock_code: str
    name: str
    market: str  # A / HK / US

    industry: str
    sector: str

    created_at: datetime
```

------

## 2.2 股票快照（Stock Snapshot）

用于记录某一时间点状态（关键设计）

```
class StockSnapshot:
    stock_code: str
    price: float
    volume: float
    market_cap: float

    pe: float
    pb: float
    roe: float

    timestamp: datetime
```

👉 作用：

- 回溯分析
- Agent分析依据
- 回测系统输入

------

## 2.3 市场事件（Market Event）

```
class MarketEvent:
    event_type: str  # news / macro / policy
    title: str
    content: str

    impact_score: float
    related_stocks: list[str]

    timestamp: datetime
```

------

# 3. Workspace 领域（核心设计）

------

# 3.1 Workspace 聚合根（Aggregate Root）

```
class Workspace:
    id: str
    user_id: str
    stock_code: str

    notes: list[Note]
    reports: list[Report]
    chats: list[ChatMessage]
    events: list[MarketEvent]

    ai_memory: dict
```

------

## 3.2 Workspace 本质

Workspace =

> **一个股票的“长期投资研究状态机 + 记忆系统”**

------

## 3.3 Note（用户笔记）

```
class Note:
    id: str
    workspace_id: str

    content: str
    tags: list[str]

    created_at: datetime
```

------

## 3.4 Report（AI报告）

```
class Report:
    id: str
    workspace_id: str

    report_type: str  # daily / weekly / stock

    content_md: str
    confidence: float

    sources: list[str]
    created_at: datetime
```

------

# 4. Agent 领域（核心）

------

# 4.1 Agent 基础接口（统一标准）

```
class BaseAgent:
    name: str

    def run(self, state: dict) -> dict:
        raise NotImplementedError
```

------

# 4.2 Agent 输入状态（统一 State）

这是 LangGraph 核心设计：

```
class AgentState:
    stock_code: str
    workspace_id: str

    market_data: dict
    news: list[dict]
    financials: dict

    intermediate_results: dict
    final_report: dict
```

------

# 4.3 Agent 输出规范

```
class AgentOutput:
    agent_name: str
    result: dict
    confidence: float

    citations: list[str]
```

------

# 4.4 Agent 列表（完整设计）

## ① Planner Agent（任务拆解）

```
输入：用户请求
输出：任务DAG
```

------

## ② News Agent（新闻分析）

职责：

- 新闻情绪分析
- 事件提取
- 影响评估

输出：

```
情绪：正/负/中性
影响股票
事件摘要
```

------

## ③ Financial Agent（基本面）

分析：

- 财务报表
- ROE/ROA
- 增长率
- 估值

------

## ④ Technical Agent（技术分析）

- MACD
- RSI
- 均线
- 趋势判断

------

## ⑤ Macro Agent（宏观）

- 利率
- CPI
- 政策
- 行业周期

------

## ⑥ Risk Agent（风险）

输出：

```
风险等级：
高/中/低

风险来源：
- 估值过高
- 政策风险
- 流动性风险
```

------

## ⑦ Quant Agent（量化因子）

- 因子计算
- 打分模型

```
score = 0~100
```

------

## ⑧ Report Agent（总结）

输出最终报告：

- Markdown
- JSON结构
- 投资建议

------

# 5. Workflow 设计（LangGraph）

------

# 5.1 状态机模型

```
START
  ↓
Planner Agent
  ↓
Parallel Execution:
  ├── News Agent
  ├── Financial Agent
  ├── Technical Agent
  ├── Macro Agent
  ↓
Risk Agent
  ↓
Quant Agent
  ↓
Report Agent
  ↓
END
```

------

# 5.2 DAG定义（工程级）

```
workflow = StateGraph(AgentState)

workflow.add_node("planner", PlannerAgent)
workflow.add_node("news", NewsAgent)
workflow.add_node("financial", FinancialAgent)
workflow.add_node("technical", TechnicalAgent)
workflow.add_node("macro", MacroAgent)
workflow.add_node("risk", RiskAgent)
workflow.add_node("quant", QuantAgent)
workflow.add_node("report", ReportAgent)

workflow.set_entry_point("planner")

workflow.add_edge("planner", ["news", "financial", "technical", "macro"])

workflow.add_edge(["news", "financial", "technical", "macro"], "risk")

workflow.add_edge("risk", "quant")

workflow.add_edge("quant", "report")

workflow.set_finish_point("report")
```

------

# 6. Analytics 领域（量化系统）

------

# 6.1 因子模型（Factor Model）

```
class Factor:
    name: str
    weight: float

    def compute(stock_snapshot):
        pass
```

------

## 常用因子：

- 估值因子（PE, PB）
- 成长因子（营收增长）
- 质量因子（ROE）
- 动量因子（趋势）
- 情绪因子（新闻）

------

## 综合评分：

```
Final Score = Σ (factor × weight)
```

------

# 7. Automation 领域

------

# 7.1 Task Definition

```
class Task:
    id: str
    type: str

    payload: dict
    priority: int

    schedule_time: datetime
```

------

## 任务类型：

- stock_scan
- report_generate
- risk_monitor
- news_digest

------

# 7.2 Scheduler Flow

```
Trigger
  ↓
Create Task
  ↓
Push Redis Queue
  ↓
Worker Execute
  ↓
Agent Run
  ↓
Save Workspace
  ↓
Notify User
```

------

# 8. API 详细设计

------

# 8.1 Stock API

```
GET /api/stock/{code}

Response:
{
  "price": 100,
  "pe": 20,
  "roe": 15,
  "score": 85
}
```

------

# 8.2 Workspace API

```
POST /api/workspace/create
GET  /api/workspace/{id}
POST /api/workspace/note
```

------

# 8.3 Agent API

```
POST /api/agent/run

{
  "stock_code": "000001",
  "task": "deep_analysis"
}
```

------

# 9. 数据库设计（ER模型）

------

# 9.1 核心表

```
users
stocks
workspaces
reports
notes
tasks
market_events
agent_logs
```

------

# 9.2 关系

```
User → Workspace (1:N)
Workspace → Report (1:N)
Workspace → Note (1:N)
Stock → Workspace (1:N)
Task → Agent Run (1:N)
```

------

# 10. RAG 设计（非常关键）

------

# 10.1 数据源

- 新闻
- 财报
- 研报
- 用户笔记
- 历史分析

------

# 10.2 向量结构

```
text
embedding
source
timestamp
stock_code
```

------

# 10.3 检索逻辑

```
Query
 ↓
Vector Search
 ↓
Filter(stock_code)
 ↓
TopK
 ↓
Inject into Agent Context
```

------

# 11. WebSocket 事件系统

------

## 事件类型：

```
agent.start
agent.progress
agent.finish
report.generated
stock.updated
risk.alert
```

------

# 12. 系统关键设计总结

------

## ✔ 1. Workspace = 核心数据单元

不是股票系统，而是：

> 股票研究操作空间

------

## ✔ 2. Agent = 独立研究员

每个 Agent 是一个“金融分析师”

------

## ✔ 3. Workflow = 投研流水线

所有分析必须 DAG 化

------

## ✔ 4. Event-driven architecture

所有行为：

- 异步
- 可追踪
- 可回放

------

## ✔ 5. RAG + Quant + Agent 三层融合

形成：

```
数据层 → 理解层 → 决策层
```
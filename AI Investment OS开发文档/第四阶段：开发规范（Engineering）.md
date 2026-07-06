# 📘 AI Investment OS — 开发规范（Engineering Spec V1.0）

------

# 1. 项目工程原则（Engineering Principles）

## 1.1 统一工程哲学

系统必须遵循：

### ✔ ① 强模块化（Modular First）

所有功能必须属于明确模块：

- agent/
- workspace/
- market/
- analytics/
- automation/

禁止“混合逻辑”。

------

### ✔ ② 业务与AI解耦（AI is not business logic）

❌ 错误：

```
if llm_result > 0.7:
    buy_stock()
```

✔ 正确：

```
Agent 负责判断
Service 负责执行
Domain 负责状态
```

------

### ✔ ③ 所有逻辑必须可回放（Replayable System）

任何结果必须可以：

- 重跑 Agent
- 重建 Workspace
- 重算评分

------

### ✔ ④ Event-driven First

所有关键行为必须变成事件：

```
StockAnalyzedEvent
ReportGeneratedEvent
RiskDetectedEvent
WorkspaceUpdatedEvent
```

------

# 2. 项目目录规范（Monorepo Structure）

```
AI_Investment_OS/
│
├── apps/
│   ├── web/                  # Next.js 前端
│   ├── admin/               # 管理后台（可选）
│
├── services/
│   ├── api-gateway/         # FastAPI
│   ├── auth-service/
│   ├── workspace-service/
│   ├── stock-service/
│   ├── report-service/
│   ├── agent-service/
│
├── agents/
│   ├── base/
│   ├── news_agent/
│   ├── financial_agent/
│   ├── technical_agent/
│   ├── macro_agent/
│   ├── risk_agent/
│   ├── quant_agent/
│   ├── report_agent/
│
├── workflows/
│   ├── stock_analysis_flow.py
│   ├── market_scan_flow.py
│
├── core/
│   ├── domain/
│   ├── events/
│   ├── exceptions/
│   ├── utils/
│
├── infra/
│   ├── db/
│   ├── redis/
│   ├── qdrant/
│   ├── minio/
│
├── scheduler/
├── workers/
├── config/
├── scripts/
├── docs/
└── docker/
```

------

# 3. 编码规范（Coding Standards）

------

## 3.1 Python规范（Backend）

### ✔ 基础要求

- Python 3.11+
- FastAPI
- Pydantic V2
- SQLAlchemy 2.0

------

### ✔ 命名规范

```
Class → PascalCase
function → snake_case
constant → UPPER_CASE
```

------

### ✔ 结构规范

```
# service layer
class StockService:

# domain layer
class Stock:

# agent layer
class FinancialAgent:
```

------

## 3.2 代码分层原则（非常重要）

### 三层结构：

```
Controller (API)
    ↓
Service (Business Logic)
    ↓
Domain (Entity + Rules)
```

------

## 3.3 禁止规则

❌ 不允许：

- Agent 直接写数据库
- API 直接调用 LLM
- Service 直接拼 prompt
- Controller 写业务逻辑

------

# 4. Agent开发规范（核心）

------

## 4.1 Agent标准结构

```
class BaseAgent:

    name: str
    description: str

    def run(self, state: AgentState) -> AgentOutput:
        prompt = self.build_prompt(state)
        response = self.llm.call(prompt)
        return self.parse(response)
```

------

## 4.2 Prompt规范

### ✔ 必须结构化：

```
[ROLE]
You are a financial analyst...

[CONTEXT]
stock: xxx
news: xxx
financials: xxx

[TASK]
Analyze the stock...

[OUTPUT FORMAT]
JSON only
```

------

## 4.3 输出必须结构化

```
{
  "summary": "",
  "score": 85,
  "risk": "medium",
  "reasoning": [],
  "citations": []
}
```

------

## 4.4 Agent禁止行为

❌ 不允许：

- 输出纯文本（必须结构化）
- 编造数据
- 无来源结论
- 直接写业务逻辑

------

# 5. Workflow规范（LangGraph）

------

## 5.1 Workflow必须显式定义

```
workflow = StateGraph(AgentState)
```

------

## 5.2 节点规范

每个节点必须：

- 输入明确
- 输出明确
- 无副作用

------

## 5.3 并行规范

```
News Agent
Financial Agent
Technical Agent
Macro Agent
```

必须：

- 并行执行
- 不共享 mutable state

------

## 5.4 禁止

❌ 不允许：

- workflow里写业务逻辑
- node之间隐式通信

------

# 6. API规范（REST + WebSocket）

------

## 6.1 REST规范

```
GET    /api/v1/stock/{code}
POST   /api/v1/workspace
POST   /api/v1/agent/run
GET    /api/v1/report/{id}
```

------

## 6.2 Response标准

```
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

------

## 6.3 错误规范

```
{
  "code": 1001,
  "message": "Agent execution failed"
}
```

------

## 6.4 WebSocket规范

```
agent.start
agent.progress
agent.finish
report.generated
risk.alert
```

------

# 7. 数据规范（Data Standards）

------

## 7.1 数据必须带时间戳

```
timestamp: datetime
```

------

## 7.2 股票数据标准化

```
price: float
volume: float
pe: float
roe: float
```

------

## 7.3 所有数据必须可追溯

```
source: akshare / news / llm / user
```

------

# 8. 数据库规范

------

## 8.1 PostgreSQL规范

- 不存 embedding
- 不存 raw text（大文本 → MinIO）

------

## 8.2 Qdrant规范

必须包含：

```
vector
metadata:
  stock_code
  source
  timestamp
```

------

## 8.3 Redis规范

用途：

- task queue
- cache
- session

禁止存业务数据

------

# 9. 异步任务规范（Celery）

------

## 9.1 Task定义

```
class Task:
    id: str
    type: str
    payload: dict
    priority: int
```

------

## 9.2 Task类型

```
stock_analysis
market_scan
report_generate
risk_check
```

------

## 9.3 并发规范

- CPU任务：限制并发
- LLM任务：排队执行
- IO任务：允许并行

------

# 10. 日志规范（Logging）

------

## 10.1 必须结构化日志

```
{
  "event": "agent_run",
  "agent": "news_agent",
  "stock": "000001",
  "latency": 1.23,
  "status": "success"
}
```

------

## 10.2 日志分层

```
DEBUG → 开发
INFO → 正常
WARN → 异常
ERROR → 崩溃
```

------

# 11. 错误处理规范

------

## 11.1 统一异常结构

```
class AppException(Exception):
    code: int
    message: str
```

------

## 11.2 Agent异常必须捕获

- 不允许直接 crash workflow
- 必须 fallback

------

# 12. 安全规范（SaaS）

------

## 12.1 权限控制

```
Guest
User
Pro
Admin
```

------

## 12.2 Workspace隔离

```
User A ≠ User B
```

------

## 12.3 API保护

- JWT
- Rate limit
- IP throttle

------

# 13. Git规范（非常重要）

------

## 13.1 分支策略

```
main       → production
dev        → development
feature/*  → new features
fix/*      → bug fixes
```

------

## 13.2 Commit规范

```
feat: add news agent
fix: workspace bug
refactor: agent workflow
docs: update architecture
```

------

# 14. CI/CD规范

------

## 14.1 Pipeline

```
Lint → Test → Build → Docker → Deploy
```

------

## 14.2 必须检查

- Lint (ruff)
- Type check (mypy)
- Unit test (pytest)

------

# 15. Docker规范（部署一致性）

------

## 15.1 服务拆分

```
frontend
api-gateway
agent-worker
postgres
redis
qdrant
minio
```

------

## 15.2 一键启动

```
docker-compose up -d
```

------

# 16. 系统核心工程原则总结

------

## ✔ 1. Agent is stateless

Agent 不能存状态

------

## ✔ 2. Workspace is stateful

所有状态存在 Workspace

------

## ✔ 3. Workflow is deterministic

同输入 → 同输出（尽可能）

------

## ✔ 4. Everything is event-driven

所有行为都可追踪

------

## ✔ 5. System is replayable

可以重跑任何分析

------

# 17. 总结（非常关键）

这一阶段的核心不是“规范写得多”，而是建立三条工程铁律：

------

## ✔ ① 业务 ≠ AI

AI只是分析器，不是系统本身

------

## ✔ ② 状态集中在 Workspace

不是散落在各个Agent

------

## ✔ ③ 所有行为必须可回放

系统必须“可重演”
# 📘 AI Investment OS — 系统架构设计（SAD V1.0）

> Multi-Agent Investment Research Operating System
>  System Architecture Design Document

------

# 1. 架构目标（Architecture Goals）

## 1.1 核心目标

系统必须满足以下 5 个工程目标：

### ✔ ① Multi-Agent 可扩展

- 支持新增 Agent（插件化）
- Agent 可独立运行
- Agent 可并行/串行编排

------

### ✔ ② 异步任务驱动（非请求阻塞）

- 所有分析任务异步化
- 支持长任务（股票全市场扫描）

------

### ✔ ③ Workspace 状态持久化

- 股票研究结果必须可追溯
- 支持长期记忆

------

### ✔ ④ 数据与计算分离

- 数据层、Agent层、API层解耦

------

### ✔ ⑤ SaaS 多用户架构

- 用户隔离
- Workspace隔离
- 权限控制

------

# 2. 总体系统架构（High-Level Architecture）

```
                    ┌──────────────────────┐
                    │      Frontend        │
                    │  Next.js + React    │
                    └─────────┬────────────┘
                              │ API/WebSocket
                              ▼
        ┌─────────────────────────────────────┐
        │           API Gateway               │
        │         (FastAPI Layer)            │
        └──────────────┬──────────────────────┘
                       │
    ┌──────────────────┼──────────────────────┐
    ▼                  ▼                      ▼
┌──────────┐   ┌──────────────┐    ┌────────────────┐
│ Auth Svc │   │ Workspace Svc │    │  Agent Engine  │
└──────────┘   └──────────────┘    └────────┬───────┘
                                            │
                                ┌───────────▼───────────┐
                                │  Workflow Orchestrator │
                                │     (LangGraph)       │
                                └───────────┬───────────┘
                                            │
                        ┌───────────────────┼───────────────────┐
                        ▼                   ▼                   ▼
              ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
              │ News Agent   │   │ Finance Agent│   │ Risk Agent   │
              └──────────────┘   └──────────────┘   └──────────────┘
                        │                   │                   │
                        └──────────┬────────┴──────────┬───────┘
                                   ▼                   ▼
                         ┌─────────────────────────────────┐
                         │        Memory Layer             │
                         │  - PostgreSQL (state)          │
                         │  - Qdrant (vector memory)      │
                         │  - MinIO (documents)           │
                         └─────────────────────────────────┘
```

------

# 3. 核心系统拆解

------

# 3.1 Frontend Layer

## 技术栈

- Next.js 14+
- React 18
- TailwindCSS
- Shadcn UI
- ECharts
- TradingView Widget
- ReactFlow（Agent可视化）

------

## 职责

- Dashboard展示
- Workspace交互
- 股票分析界面
- Agent执行状态展示
- Chat interface

------

## 特点

Frontend **只是“观察器”**，不是计算中心。

------

# 3.2 API Gateway（核心入口）

## 技术

- FastAPI
- WebSocket
- JWT Auth

------

## 职责

- 请求路由
- 鉴权
- 任务分发
- WebSocket推送
- Rate Limit

------

## API结构

```
POST /api/chat
POST /api/workspace/create
GET  /api/stock/{code}
POST /api/agent/run
GET  /api/reports
POST /api/watchlist
```

------

## WebSocket

用于：

- Agent实时状态
- 股票分析进度
- 报告生成进度

------

# 3.3 Auth Service（用户系统）

## 功能

- 注册/登录
- JWT管理
- RBAC权限控制

------

## 权限模型

```
Guest → User → Pro → Admin
```

------

## 数据模型

```
users
- id
- email
- password_hash
- role
- created_at
```

------

# 3.4 Workspace Service（核心业务）

## 定义

Workspace = “某只股票的长期研究空间”

------

## 数据结构

```
workspace
- id
- user_id
- stock_code
- name
- created_at
```

------

## 子模块

- Chat History
- Reports
- Events Timeline
- Notes
- AI Memory Snapshot

------

## 特点

Workspace 是：

> **AI 投研的“长期记忆容器”**

------

# 3.5 Agent Engine（核心大脑）

## 架构目标

Agent Engine = 多智能体协作系统

------

## 核心设计

```
User Request
↓
Planner Agent
↓
Task DAG Builder
↓
Workflow Engine (LangGraph)
↓
Parallel Agents Execution
↓
Result Aggregation
↓
Report Generator
```

------

## Agent 类型

### ① Planner Agent

- 拆解任务

### ② News Agent

- 新闻分析

### ③ Financial Agent

- 财务分析

### ④ Technical Agent

- 技术指标

### ⑤ Macro Agent

- 宏观环境

### ⑥ Risk Agent

- 风险评估

### ⑦ Quant Agent

- 因子计算

### ⑧ Report Agent

- 生成报告

------

## Agent标准接口

```
class BaseAgent:
    def run(self, state: dict) -> dict:
        pass
```

------

## Agent输入输出标准

```
Input:
- stock_code
- workspace_state
- market_data

Output:
- analysis_result
- confidence_score
- citations
```

------

# 3.6 Workflow Orchestrator（LangGraph）

## 核心作用

负责：

- Agent编排
- DAG执行
- 并行控制
- 状态管理

------

## 工作流示例

```
        ┌──────────────┐
        │ Planner      │
        └──────┬───────┘
               │
   ┌───────────┼───────────┐
   ▼           ▼           ▼
News       Financial    Technical
   └───────────┬───────────┘
               ▼
          Risk Agent
               ▼
        Report Agent
```

------

## 特性

- 支持并行节点
- 支持条件分支
- 支持重试机制

------

# 3.7 Data Layer（数据层）

## 设计原则

> 数据与Agent解耦

------

## 组件

### ① PostgreSQL（核心数据）

- 用户
- Workspace
- 股票数据
- 报告
- Chat记录

------

### ② Qdrant（向量数据库）

- 新闻embedding
- 研报embedding
- Workspace记忆

------

### ③ Redis（缓存 & 队列）

- Task queue
- session
- rate limit

------

### ④ MinIO（文件存储）

- PDF研报
- 上传文件
- 历史报告

------

# 3.8 Task Queue（异步任务系统）

## 技术

- Celery
- Redis Broker

------

## 用途

- 股票分析任务
- 全市场扫描
- 报告生成
- 定时任务

------

## 示例

```
Task: Analyze Stock
- type: async
- priority: high
- retries: 3
```

------

# 3.9 Scheduler（自动化系统）

## 功能

定时触发 Agent：

```
09:00 → Market Scan
10:00 → News Digest
15:00 → Closing Report
```

------

## 实现

- APScheduler 或 Celery Beat

------

# 3.10 Notification System

## 渠道

- Web push
- Email
- Telegram
- WeChat（可选）

------

## 触发事件

- 股票评分变化
- 新机会发现
- 风险提示

------

# 4. 数据流架构（Data Flow）

```
Market Data
    ↓
ETL Layer
    ↓
Database (Postgres / Qdrant)
    ↓
Agent Engine
    ↓
Workflow Orchestrator
    ↓
Report Generator
    ↓
Workspace
    ↓
Frontend / API
```

------

# 5. Agent执行全链路

```
User Request
↓
API Gateway
↓
Task Queue
↓
Planner Agent
↓
Workflow DAG
↓
Parallel Agents
↓
Result Aggregation
↓
Risk Check
↓
Report Agent
↓
Workspace Save
↓
WebSocket Push
```

------

# 6. 部署架构（Deployment Architecture）

## 单服务器（2C4G适配版）

```
Nginx
 ├── Frontend (Next.js)
 ├── Backend (FastAPI)
 ├── Redis
 ├── Postgres
 ├── Worker (Celery)
 └── Qdrant
```

------

## Docker Compose

建议：

- 全容器化
- 一键启动

------

# 7. 性能设计

## 关键优化点

### ① Agent并行化

- News / Finance / Tech 并行

------

### ② 缓存机制

- 热股票缓存
- 新闻缓存

------

### ③ 延迟优化

- WebSocket流式返回
- 分阶段输出

------

# 8. 安全设计

## 基础安全

- JWT Auth
- API Rate Limit
- SQL Injection防护

------

## 数据隔离

```
User A Workspace ≠ User B Workspace
```

------

# 9. 系统核心设计总结

这个系统不是：

❌ 股票分析工具
 ❌ ChatGPT wrapper

而是：

## ✔ AI Investment OS 的三大核心引擎

------

### ① Multi-Agent Research Engine

- 自动分析市场
- 自动拆解任务
- 自动生成结论

------

### ② Workspace Memory System

- 长期股票研究空间
- 可追溯投资逻辑

------

### ③ Automation Investment System

- 自动扫描
- 自动选股
- 自动报告
- 自动推送
# AI Investment OS

> AI 驱动的智能投资操作系统 —— 多 Agent 协同分析、组合管理、实时监控的一站式平台

## 项目简介

AI Investment OS 是一个基于 LangGraph 多 Agent 架构的金融操作系统，旨在从传统的"AI 聊天工具"升级为**可运行的 AI 金融操作系统**。系统覆盖投资研究、选股、组合管理和监控告警四大核心能力闭环，具备类 Bloomberg 终端的分析能力与 AI Agent 的智能决策能力。

## 系统架构

```
                ┌────────────────────────────┐
                │        Frontend UI         │
                │   React / Next.js Dashboard│
                └────────────┬───────────────┘
                             │ REST / WebSocket
                ┌────────────▼───────────────┐
                │       API Gateway           │
                │        FastAPI              │
                └────────────┬───────────────┘
                             │
        ┌────────────────────▼────────────────────┐
        │         Core Engine Layer               │
        │  1. Workflow Engine (LangGraph)        │
        │  2. Agent Runtime Manager              │
        │  3. Portfolio Engine                   │
        │  4. Event & Alert Engine              │
        └────────────┬───────────────────────────┘
                     │
        ┌────────────▼───────────────────────────┐
        │             Service Layer               │
        │ Market Data | RAG | Indicator | LLM    │
        └────────────┬───────────────────────────┘
                     │
        ┌────────────▼───────────────────────────┐
        │           Data Layer                   │
        │ SQLite | Redis | FAISS                 │
        └───────────────────────────────────────┘
```

## 核心模块

### Multi-Agent 工作流

系统采用 LangGraph 编排多 Agent 协同工作：

```
         ┌──────────────┐
         │   Planner    │
         └──────┬───────┘
                │
    ┌───────────┼────────────┐
    │           │            │
┌───▼───┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
│Finance│ │Technical│ │  News   │ │  Risk   │
└───┬───┘ └────┬────┘ └────┬────┘ └────┬────┘
    └───────────┴────────────┘
                │
         ┌──────▼──────┐
         │    Judge    │
         └──────┬──────┘
                │
     ┌──────────▼──────────┐
     │   Portfolio Agent   │
     └──────────┬──────────┘
                │
     ┌──────────▼──────────┐
     │   Report Generator  │
     └──────────┬──────────┘
                │
       Final State Output
```

| Agent | 职责 |
|-------|------|
| **Planner** | 规划分析任务与调度策略 |
| **Finance** | 基本面与财务数据分析 |
| **Technical** | 技术指标与趋势分析 |
| **News** | 新闻舆情与情感分析 |
| **Risk** | 风险评估与波动性分析 |
| **Judge** | 综合评判与决策聚合 |
| **Portfolio** | 组合权重建议与优化 |
| **Report** | 生成最终分析报告 |

所有 Agent 遵循统一输出格式：`output` + `confidence` + `evidence` + `reasoning`，结果写入共享 State 而非直接返回。

### Portfolio Engine

- **候选股管理** — 股票池增删、AI 排序、自动更新
- **权重建议** — AI 驱动的持仓比例推荐
- **风险分析** — 行业集中度、单票风险、波动性监控

### Event & Alert Engine

- **事件模型** — 支持新闻、价格、成交量、宏观四类市场事件
- **告警规则** — 基于评分变化、风险等级、舆情波动的自动触发
- **推送渠道** — WebSocket 实时 UI、Email、Telegram

### 数据层

| 存储 | 用途 |
|------|------|
| **SQLite** | 用户、组合、股票状态、Agent 日志 |
| **Redis** | 行情缓存、Agent 状态缓存、事件队列 |
| **FAISS** | 新闻向量检索、研报语义搜索 |

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | React / Next.js, Zustand, React Query |
| 后端 | Python, FastAPI, LangGraph |
| 数据库 | SQLite, Redis, FAISS |
| AI/LLM | LangChain, LangGraph Multi-Agent |
| 部署 | Docker Compose |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Redis（可选，用于缓存）

### 安装与运行

```bash
# 克隆仓库
git clone https://github.com/your-username/AI-Investment-OS.git
cd AI-Investment-OS

# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
docker-compose up -d
```

单台 2C4G 服务器即可运行 MVP。

## 项目结构

```
AI_Investment_OS/
├── frontend/          # React 前端应用
│   ├── dashboard/     # 首页看板
│   ├── workspace/     # 个股分析工作台
│   └── portfolio/     # 组合管理页面
├── backend/           # FastAPI 后端服务
│   ├── agents/        # Agent 实现
│   ├── engine/        # LangGraph 工作流引擎
│   ├── services/      # 数据服务层
│   └── models/        # 数据模型
├── docker-compose.yml
└── 开发设计文档.md
```

## License

MIT

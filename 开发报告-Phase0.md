# Phase 0 开发报告 — Foundation

> 开发日期：2026-07-03
> 阶段：Sprint 0 — Foundation
> 状态：DONE

---

## 1. 任务完成清单

| # | Task | Size | Story Points | Status |
|---|------|------|:------------:|:------:|
| 0.1 | 项目目录结构搭建 | S | 2 | DONE |
| 0.2 | 数据库 Schema 设计 | M | 3 | DONE |
| 0.3 | Python 虚拟环境 + pyproject.toml | XS | 1 | DONE |
| 0.4 | Docker Compose 骨架 | M | 3 | DONE |
| 0.5 | Git 工作流 + .gitignore | XS | 1 | DONE |
| 0.6 | 基础日志配置 | XS | 1 | DONE |

**Total: 11 / 13 story points completed (前端脚手架推迟到 Phase 4)**

> 0.4 前端脚手架（Next.js）推迟至 Phase 4（API & Frontend），避免过早引入 Node.js 依赖增加维护成本。

---

## 2. 实现概览

### 2.1 项目结构

```
AI_Investment_OS/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI 入口，挂载 4 个路由
│   │   ├── config.py            ← Pydantic Settings，读取 .env
│   │   ├── database.py          ← SQLAlchemy engine + session
│   │   ├── init_db.py           ← 建表脚本
│   │   ├── models/              ← 6 个 ORM 模型 + Pydantic schemas
│   │   ├── api/                 ← 4 个路由桩（auth, stocks, portfolio, alerts）
│   │   └── core/                ← logging, retry, circuit_breaker
│   ├── tests/                   ← conftest + 3 个测试文件
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    ← 目录已建，代码待 Phase 4
├── .claude/skills/              ← 4 个自定义 skill
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── SETUP.md
├── README.md
├── 开发设计文档.md
└── 开发时间线.md
```

### 2.2 数据库模型（6 张表）

| 表名 | 用途 | 主键 |
|------|------|------|
| `users` | 用户信息 + 风险偏好 | id (UUID) |
| `portfolios` | 持仓 + 候选股 + AI 评分 | id (UUID) |
| `stock_state` | 股票最新状态 + AI 评分 | stock_code |
| `agent_logs` | Agent 执行日志（输入/输出/延迟/Token） | id (auto) |
| `market_events` | 市场事件（新闻/价格/成交量/宏观） | id (auto) |
| `alerts` | 用户告警 | id (auto) |

### 2.3 Pydantic Schemas（API 校验层）

| Schema | 用途 |
|--------|------|
| `PortfolioCreate` / `PortfolioResponse` | Portfolio CRUD |
| `StockAnalysisRequest` / `StockAnalysisResponse` | 股票分析 |
| `AgentOutput` | Agent 输出统一格式校验 |
| `StandardResponse` | API 标准响应格式 |

### 2.4 核心工具

| 模块 | 功能 |
|------|------|
| `core/logging.py` | JSON 结构化日志 + 可读格式双模式 |
| `core/retry.py` | 指数退避重试装饰器 |
| `core/circuit_breaker.py` | 三态熔断器（CLOSED/OPEN/HALF_OPEN） |

### 2.5 API 端点桩

| Method | Path | 功能 |
|--------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/auth/me` | 当前用户 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/stocks/{code}` | 查询股票 |
| POST | `/api/stocks/analyze` | 触发分析 |
| GET | `/api/stocks/hot` | 热门股票 |
| GET | `/api/portfolio/` | 组合列表 |
| POST | `/api/portfolio/` | 创建组合 |
| GET | `/api/portfolio/{id}` | 组合详情 |
| GET | `/api/alerts/` | 告警列表 |
| GET | `/api/alerts/unread` | 未读告警 |

---

## 3. 测试方法

### 3.1 运行测试

```bash
cd backend
pip install -e ".[dev]"
pytest tests/ -v
```

### 3.2 测试覆盖

| 测试文件 | 测试内容 | 用例数 |
|----------|---------|:------:|
| `test_smoke.py` | API 端点可用性（health, auth, stocks, portfolio, alerts） | 5 |
| `test_models.py` | 数据库模型 CRUD（6 个表各一个 create 测试） | 6 |
| `test_schemas.py` | Pydantic 校验（合法输出、置信度越界、空 evidence） | 3 |
| **Total** | | **14** |

### 3.3 测试策略说明

| 层级 | 方法 | 工具 |
|------|------|------|
| API 冒烟测试 | 使用 FastAPI TestClient 发 HTTP 请求 | pytest + httpx |
| 数据库模型测试 | 内存 SQLite + autouse fixture 自动建/拆表 | SQLAlchemy + pytest |
| Schema 校验测试 | 直接实例化 Pydantic model，验证约束 | pytest |

### 3.4 数据库测试隔离

每个测试使用独立的 SQLite 文件（`test.db`），通过 `conftest.py` 的 `setup_db` fixture 在每个测试前建表、测试后销毁，确保测试间无数据污染。

---

## 4. 环境启动指南

### 方式一：本地开发

```bash
# 1. 安装依赖
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. 配置环境变量
cp ../.env.example ../.env
# 编辑 .env，至少设置 OPENAI_API_KEY

# 3. 初始化数据库
python -m app.init_db

# 4. 启动服务
uvicorn app.main:app --reload --port 8000

# 5. 访问 API 文档
# http://localhost:8000/docs
```

### 方式二：Docker Compose

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env

# 2. 启动所有服务
docker compose up -d

# 3. 查看日志
docker compose logs -f backend
```

---

## 5. 已知限制与后续计划

| 项目 | 当前状态 | 后续 |
|------|---------|------|
| 前端 | 目录已建，无代码 | Phase 4 实现 |
| API 认证 | JWT 桩文件，无实际校验 | Phase 4 补全 |
| Redis 缓存 | requirements 已含，未接入 | Phase 1 实现 |
| Alembic 迁移 | 目录已建，未配置 | Phase 5 补全 |
| CI/CD | pre-commit 配置已有，无 GitHub Actions | 按需添加 |

---

## 6. 文件变更清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/app/main.py` | New | FastAPI 入口 |
| `backend/app/config.py` | New | Settings 配置 |
| `backend/app/database.py` | New | SQLAlchemy 引擎 |
| `backend/app/init_db.py` | New | 建表脚本 |
| `backend/app/models/*.py` | New | 6 个 ORM 模型 + schemas |
| `backend/app/api/*.py` | New | 4 个路由桩 |
| `backend/app/core/*.py` | New | logging, retry, circuit_breaker |
| `backend/tests/*.py` | New | conftest + 3 个测试文件 |
| `backend/pyproject.toml` | New | 项目配置 |
| `backend/requirements.txt` | New | 依赖清单 |
| `backend/Dockerfile` | New | 后端容器化 |
| `frontend/Dockerfile` | New | 前端容器化 |
| `docker-compose.yml` | New | 编排配置 |
| `.env.example` | New | 环境变量模板 |
| `.gitignore` | New | Git 忽略规则 |
| `.pre-commit-config.yaml` | New | 代码质量 hooks |
| `SETUP.md` | New | 环境搭建指南 |

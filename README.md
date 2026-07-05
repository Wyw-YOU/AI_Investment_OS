# AI Investment OS

> AI 驱动的智能投资操作系统 —— 多 Agent 协同分析、组合管理、实时监控的一站式平台

## 项目简介

AI Investment OS 是一个基于 LangGraph 多 Agent 架构的金融操作系统，覆盖**投资研究、选股、组合管理和监控告警**四大核心能力闭环。系统采用 8 个专业 Agent 协同工作，支持国产大模型（DeepSeek / 通义千问 / MiMo 等），单台 2C4G 服务器即可部署运行。

## 系统架构

```
                ┌────────────────────────────┐
                │     Frontend (Next.js)     │
                │  Dashboard | Stock | Portfolio │
                └────────────┬───────────────┘
                             │ REST / WebSocket
                ┌────────────▼───────────────┐
                │     FastAPI + JWT Auth      │
                │     Rate Limit 120/min     │
                └────────────┬───────────────┘
                             │
        ┌────────────────────▼────────────────────┐
        │         Core Engine Layer               │
        │  LangGraph Workflow | Portfolio Engine  │
        │  Event Engine | Alert Rules            │
        └────────────┬───────────────────────────┘
                     │
        ┌────────────▼───────────────────────────┐
        │             Service Layer               │
        │ akshare | Indicators | LLM (base_url)  │
        │ Cache (Redis/Memory) | FAISS | News    │
        └────────────┬───────────────────────────┘
                     │
        ┌────────────▼───────────────────────────┐
        │           Data Layer                   │
        │ SQLite + Alembic | Redis | FAISS      │
        └───────────────────────────────────────┘
```

## 核心功能

### Multi-Agent 分析工作流

```
Planner → [Finance ‖ Technical ‖ News ‖ Risk] → Judge → Portfolio → Report
```

| Agent | 职责 | 模式 |
|-------|------|------|
| **Planner** | 规划分析任务 | 规则 |
| **Finance** | 基本面分析（PE/PB/ROE） | LLM + 规则 |
| **Technical** | 技术指标（MACD/RSI/KDJ/BOLL） | LLM + 规则 |
| **News** | 舆情分析 + RAG 检索 | LLM + 关键词 |
| **Risk** | 波动率/Beta/集中度评估 | 规则 |
| **Judge** | 多信号聚合评分 | LLM + 加权 |
| **Portfolio** | 持仓权重建议 | 规则 |
| **Report** | 结构化报告生成 | 规则 |

所有 Agent 统一输出：`output` + `confidence` + `evidence` + `reasoning`

### Portfolio Engine

- 候选股管理（增删 / AI 排序）
- AI 权重推荐（基于分析评分加权）
- 风险评分（单票集中度 + 行业集中度 + 分散度）

### Event & Alert Engine

- 市场事件检测（新闻 / 价格 / 成交量 / 宏观）
- 告警规则（评分变化 ≥0.5、风险等级 HIGH）
- WebSocket 实时推送

### LLM 支持

通过 `base_url` 配置兼容所有 OpenAI 格式 API：

| Provider | BASE_URL | MODEL |
|----------|----------|-------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| MiMo | `https://api.xiaomi.com/v1` | `MiMo-7B` |
| Moonshot | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| SiliconFlow | `https://api.siliconflow.cn/v1` | `deepseek-ai/DeepSeek-V3` |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14, TypeScript, Tailwind CSS, Zustand, React Query |
| 后端 | Python 3.10+, FastAPI, LangGraph, Pydantic v2 |
| 数据库 | SQLite + Alembic, Redis, FAISS |
| AI/LLM | OpenAI 兼容接口，支持国产大模型 |
| 部署 | Docker Compose V2, systemd |

## 本地开发（Windows + PyCharm）

### 环境要求

- Python 3.10+
- Node.js 18+
- Redis（可选，无 Redis 时自动降级到内存缓存）

### 步骤 1：配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少设置：

```env
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-your-deepseek-key
LLM_MODEL=deepseek-chat
JWT_SECRET=your-random-secret-here
```

### 步骤 2：启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -m app.init_db

# 启动服务
uvicorn app.main:app --reload --port 8000
```

后端运行在 http://localhost:8000
API 文档：http://localhost:8000/docs

### 步骤 3：启动前端

```bash
cd frontend

npm install
npm run dev
```

前端运行在 http://localhost:3000

### PyCharm 配置

- **后端 Run Configuration**：Module name → `uvicorn`，Parameters → `app.main:app --reload --port 8000`
- **前端**：Terminal 中直接运行 `npm run dev`

### 运行测试

```bash
cd backend
pytest tests/ -v
```

98 个测试用例，覆盖全部模块。

## 云服务器部署（2C4G Ubuntu）

### 方式一：Docker Compose V2（推荐）

```bash
# SSH 连接服务器
ssh root@your-server-ip

# 安装 Docker
apt update && apt install -y docker.io docker-compose-plugin
systemctl enable docker && systemctl start docker

# 部署项目
git clone <your-repo-url>
cd AI_Investment_OS

# 配置环境变量
cp .env.example .env
nano .env
```

`.env` 最小配置：

```env
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-your-key
LLM_MODEL=deepseek-chat
LLM_MAX_TOKENS=2000
JWT_SECRET=your-random-secret
DEBUG=false
```

```bash
# 启动所有服务
docker compose up -d

# 验证
curl http://localhost:8000/health
# 浏览器访问 http://your-server-ip:3000
```

### 方式二：systemd 直接运行（不用 Docker）

```bash
# 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.init_db

# 创建 systemd 服务
sudo tee /etc/systemd/system/investment-backend.service << 'EOF'
[Unit]
Description=AI Investment OS Backend
After=network.target

[Service]
User=root
WorkingDirectory=/root/AI_Investment_OS/backend
EnvironmentFile=/root/AI_Investment_OS/.env
ExecStart=/root/AI_Investment_OS/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now investment-backend

# 前端 build
cd ../frontend
npm install && npm run build
sudo cp -r out /var/www/investment-os
```

### 运维命令

| 操作 | Docker 方式 | systemd 方式 |
|------|------------|-------------|
| 查看日志 | `docker compose logs -f backend` | `journalctl -u investment-backend -f` |
| 重启服务 | `docker compose restart backend` | `systemctl restart investment-backend` |
| 查看资源 | `docker stats` | `htop` |
| 停止服务 | `docker compose down` | `systemctl stop investment-backend` |
| 更新代码 | `git pull && docker compose up -d --build` | `git pull && systemctl restart investment-backend` |

### 防火墙

```bash
ufw allow 8000/tcp   # 后端 API
ufw allow 3000/tcp   # 前端
ufw enable
```

### 资源占用

| 组件 | Docker 模式 | systemd 模式 |
|------|:-----------:|:------------:|
| 后端 | ~200MB | ~200MB |
| Redis | ~50MB | ~50MB |
| 前端 | ~300MB | 静态文件 ~10MB |
| **合计** | ~550MB | ~260MB |

> 2C4G 服务器两种方式均可运行。systemd 模式内存更省。

## 项目结构

```
AI_Investment_OS/
├── backend/
│   ├── app/
│   │   ├── agents/        # 8 个 AI Agent
│   │   ├── engine/        # LangGraph 工作流
│   │   ├── services/      # 10 个服务模块
│   │   ├── api/           # FastAPI 路由
│   │   ├── models/        # SQLAlchemy + Pydantic
│   │   └── core/          # Auth / Retry / Circuit Breaker / Rate Limit
│   ├── tests/             # 16 个测试文件，98 个用例
│   ├── alembic/           # 数据库迁移
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/           # Next.js 页面（Dashboard / Stock / Portfolio）
│       ├── components/    # 8 个 React 组件
│       ├── lib/           # API 封装
│       └── stores/        # Zustand 状态
├── .claude/skills/        # 4 个 Claude Code Skill
├── docker-compose.yml     # Docker Compose V2
├── .env.example           # 环境变量模板
├── 开发设计文档.md
├── 开发时间线.md
└── 开发报告-Phase[0-5].md  # 6 份开发报告
```

## 开发时间线

| Phase | 内容 | 工期 | 状态 |
|-------|------|:----:|:----:|
| 0 | Foundation（脚手架 + CI） | 1.5 周 | DONE |
| 1 | Data & Service Layer | 2.5 周 | DONE |
| 2 | Agent Engine（核心） | 4 周 | DONE |
| 3 | Portfolio & Event Engine | 2.5 周 | DONE |
| 4 | API & Frontend | 3 周 | DONE |
| 5 | Production Hardening | 2.5 周 | DONE |
| **合计** | | **16 周** | **DONE** |

## License

MIT

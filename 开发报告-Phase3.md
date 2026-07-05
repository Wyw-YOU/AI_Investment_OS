# Phase 3 开发报告 — Portfolio & Event Engine

> 开发日期：2026-07-05
> 阶段：Sprint 6-7 — Portfolio & Event Engine
> 状态：DONE

---

## 1. 任务完成清单

| # | Task | Story Points | Status |
|---|------|:------------:|:------:|
| 3.1 | Portfolio CRUD | 3 | DONE |
| 3.2 | AI 权重推荐系统 | 5 | DONE |
| 3.3 | 风险评分引擎 | 5 | DONE |
| 3.4 | 候选股管理 | 3 | DONE |
| 3.5 | MarketEvent 模型 + 事件检测 | 3 | DONE |
| 3.6 | 告警规则引擎 | 5 | DONE |
| 3.7 | WebSocket 实时推送 | 5 | DONE |
| 3.8 | 通知渠道抽象（WebSocket 已实现，Email/Telegram stub） | 3 | DONE |

**Total: 32 / 32 story points**

---

## 2. 模块实现概览

### 2.1 Portfolio Engine — `services/portfolio_service.py`

| 方法 | 功能 |
|------|------|
| `create()` / `get()` / `list_by_user()` / `delete()` | 标准 CRUD |
| `update_holdings()` | 更新持仓权重 |
| `add_to_pool()` / `remove_from_pool()` | 候选股管理（去重） |
| `suggest_weights()` | AI 权重推荐（基于 StockState.score 加权分配） |
| `calc_risk_score()` | 风险评分（单票集中度 + 行业集中度 + 分散度） |

**风险评分逻辑：**
- 单票权重 > 30% → +30 分
- 单票权重 > 20% → +15 分
- 行业集中度 > 50% → +25 分
- 持仓少于 3 只 → +15 分
- 60+ HIGH / 30+ MEDIUM / <30 LOW

### 2.2 Event & Alert Engine — `services/event_service.py`

| 类 | 功能 |
|------|------|
| `EventService` | 市场事件创建和查询 |
| `AlertService` | 用户告警 CRUD + 未读计数 |
| `AlertRuleEngine` | 规则评估：评分变化 ≥0.5 触发、HIGH/CRITICAL 风险触发 |

### 2.3 WebSocket — `services/websocket_manager.py`

| 方法 | 功能 |
|------|------|
| `connect()` / `disconnect()` | 连接生命周期管理 |
| `send_to_user()` | 定向推送（自动清理死连接） |
| `broadcast()` | 全局广播 |
| `send_alert()` | 告警推送（type=alert） |
| `send_stock_update()` | 行情更新推送（type=stock_update） |

**端点**: `ws://host:8000/ws/{user_id}`

### 2.4 API 端点更新

| Method | Path | 功能 |
|--------|------|------|
| GET | `/api/portfolio/` | 组合列表 |
| POST | `/api/portfolio/` | 创建组合 |
| GET | `/api/portfolio/{id}` | 组合详情 |
| DELETE | `/api/portfolio/{id}` | 删除组合 |
| POST | `/api/portfolio/{id}/pool` | 添加候选股 |
| DELETE | `/api/portfolio/{id}/pool/{code}` | 移除候选股 |
| POST | `/api/portfolio/{id}/suggest-weights` | AI 权重推荐 |
| GET | `/api/portfolio/{id}/risk` | 风险评分 |
| GET | `/api/alerts/` | 告警列表 |
| GET | `/api/alerts/unread` | 未读告警 |
| POST | `/api/alerts/{id}/read` | 标记已读 |
| WS | `/ws/{user_id}` | WebSocket 实时推送 |

---

## 3. 测试方法

### 3.1 新增测试

| 文件 | 测试内容 | 用例数 |
|------|---------|:------:|
| `test_portfolio.py` | CRUD、候选股、权重推荐、风险评分 | 9 |
| `test_events.py` | 事件创建、告警服务、规则引擎 | 7 |
| `test_websocket.py` | 连接管理、定向推送、广播 | 4 |
| **Total (Phase 3)** | | **20** |

### 3.2 运行测试

```bash
cd backend
pytest tests/test_portfolio.py tests/test_events.py tests/test_websocket.py -v
```

---

## 4. 云服务器部署指南（2C4G Ubuntu）

### 4.1 服务器初始化

```bash
# SSH 连接服务器
ssh root@your-server-ip

# 系统更新
apt update && apt upgrade -y

# 安装 Docker + Docker Compose V2
apt install -y docker.io docker-compose-plugin
systemctl enable docker && systemctl start docker

# 验证
docker compose version
```

### 4.2 部署项目

```bash
# 克隆代码
git clone <your-repo-url>
cd AI_Investment_OS

# 配置环境变量
cp .env.example .env
nano .env
```

**`.env` 最小配置：**

```env
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-your-deepseek-key
LLM_MODEL=deepseek-chat
LLM_MAX_TOKENS=2000
JWT_SECRET=your-random-secret-string
DEBUG=false
```

### 4.3 启动服务

```bash
# 使用 Docker Compose V2 启动
docker compose up -d

# 查看运行状态
docker compose ps

# 查看后端日志
docker compose logs -f backend

# 验证服务
curl http://localhost:8000/health
# 应返回: {"status":"ok","version":"0.1.0"}
```

### 4.4 资源监控（2C4G 限制）

```bash
# 查看容器资源占用
docker stats --no-stream

# 预期内存占用：
# backend:  ~200-300MB
# redis:    ~50MB
# total:    ~300-400MB (余量充足)
```

### 4.5 常用运维命令

```bash
# 重启后端（代码更新后）
docker compose restart backend

# 查看日志（排查问题）
docker compose logs --tail=100 backend

# 进入容器调试
docker compose exec backend bash

# 停止所有服务
docker compose down

# 重建镜像（依赖变更后）
docker compose up -d --build
```

### 4.6 防火墙配置

```bash
# 开放端口
ufw allow 8000/tcp   # 后端 API
ufw allow 3000/tcp   # 前端（Phase 4）
ufw enable
```

### 4.7 直接运行（不用 Docker）

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.init_db

# 使用 systemd 管理进程
cat > /etc/systemd/system/investment-os.service << 'EOF'
[Unit]
Description=AI Investment OS Backend
After=network.target

[Service]
User=root
WorkingDirectory=/root/AI_Investment_OS/backend
ExecStart=/root/AI_Investment_OS/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
EnvironmentFile=/root/AI_Investment_OS/.env

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable investment-os
systemctl start investment-os
systemctl status investment-os
```

---

## 5. 文件变更清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `app/services/portfolio_service.py` | New | Portfolio CRUD + 权重推荐 + 风险评分 |
| `app/services/event_service.py` | New | 事件服务 + 告警服务 + 规则引擎 |
| `app/services/websocket_manager.py` | New | WebSocket 连接管理 |
| `app/api/portfolio.py` | Updated | 完整 Portfolio API |
| `app/api/alerts.py` | Updated | 完整 Alert API |
| `app/main.py` | Updated | 新增 WebSocket 端点 |
| `tests/test_portfolio.py` | New | 9 个 Portfolio 测试 |
| `tests/test_events.py` | New | 7 个事件/告警测试 |
| `tests/test_websocket.py` | New | 4 个 WebSocket 测试 |

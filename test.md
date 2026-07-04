# AI Investment OS — 测试指南

本文档指导你在本地开发环境和云服务器上验证项目各模块是否正常工作。

---

## 目录

1. [环境准备](#1-环境准备)
2. [本地测试](#2-本地测试)
   - [2.1 单元测试](#21-单元测试)
   - [2.2 启动服务](#22-启动服务)
   - [2.3 API 端点手动验证](#23-api-端点手动验证)
   - [2.4 Swagger UI 验证](#24-swagger-ui-验证)
   - [2.5 LLM 连通性测试](#25-llm-连通性测试)
   - [2.6 数据服务集成测试](#26-数据服务集成测试)
3. [Docker 本地测试](#3-docker-本地测试)
4. [云服务器测试](#4-云服务器测试)
   - [4.1 首次部署](#41-首次部署)
   - [4.2 服务验证](#42-服务验证)
   - [4.3 外网访问测试](#43-外网访问测试)
5. [预期结果速查表](#5-预期结果速查表)
6. [常见问题排查](#6-常见问题排查)

---

## 1. 环境准备

### 本地环境要求

| 依赖 | 最低版本 | 检查命令 |
|------|---------|---------|
| Python | 3.10+ | `python --version` |
| pip | 22.0+ | `pip --version` |
| Docker (可选) | 20.10+ | `docker --version` |
| Docker Compose (可选) | V2 | `docker compose version` |

### 云服务器环境要求

| 依赖 | 最低版本 | 检查命令 |
|------|---------|---------|
| Python | 3.10+ | `python3 --version` |
| pip | 22.0+ | `pip3 --version` |
| 防火墙 | 开放 8000 端口 | `sudo ufw status` |

### 初始化步骤（本地和云服务器通用）

```bash
# 进入项目根目录
cd AI_Investment_OS

# 创建 .env 文件
cp .env.example .env

# 编辑 .env，填入你的 LLM API Key
# 至少修改以下三项：
#   LLM_BASE_URL=https://api.deepseek.com
#   LLM_API_KEY=sk-你的实际key
#   LLM_MODEL=deepseek-chat
```

---

## 2. 本地测试

### 2.1 单元测试

运行项目自带的 50 个单元测试，覆盖所有已实现模块。

```bash
cd backend

# 安装依赖（首次）
pip install -r requirements.txt

# 运行全部测试
python -m pytest tests/ -v

# 运行测试并显示覆盖率（可选）
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

#### 预期结果

```
tests/test_cache.py::TestMemoryCache::test_set_and_get           PASSED
tests/test_cache.py::TestMemoryCache::test_get_missing_key        PASSED
tests/test_cache.py::TestMemoryCache::test_delete                 PASSED
tests/test_cache.py::TestMemoryCache::test_exists                 PASSED
tests/test_cache.py::TestCacheService::test_memory_fallback       PASSED
tests/test_cache.py::TestCacheService::test_json_serialization    PASSED
tests/test_cache.py::TestCacheService::test_chinese_characters    PASSED
tests/test_circuit_breaker.py::test_starts_closed                 PASSED
tests/test_circuit_breaker.py::test_opens_after_threshold         PASSED
tests/test_circuit_breaker.py::test_raises_when_open              PASSED
tests/test_circuit_breaker.py::test_success_resets_count          PASSED
tests/test_indicators.py (14 tests)                               PASSED
tests/test_llm_adapter.py (7 tests)                               PASSED
tests/test_models.py (6 tests)                                    PASSED
tests/test_news.py (4 tests)                                      PASSED
tests/test_schemas.py (3 tests)                                   PASSED
tests/test_smoke.py (5 tests)                                     PASSED

======================= 50 passed in X.XXs ========================
```

**检查点：**
- `50 passed` — 全部通过，无 `FAILED`
- 只有 2 个 warning（httpx 兼容性 + JWT 默认值提醒），这是正常的
- 如果有 `FAILED`，查看具体错误信息排查

---

### 2.2 启动服务

```bash
cd backend

# 确保 .env 已配置（在项目根目录）
# 初始化数据库
python -m app.init_db

# 启动服务（开发模式，带热重载）
uvicorn app.main:app --reload --port 8000
```

#### 预期结果

启动成功后终端会显示：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX]
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**检查点：**
- 没有 `Error` 或 `Traceback`
- 如果出现 `ModuleNotFoundError`，说明依赖未安装完全，运行 `pip install -r requirements.txt`
- 如果出现 `Address already in use`，说明 8000 端口被占用，换端口或关闭占用进程

---

### 2.3 API 端点手动验证

在**另一个终端**中运行以下命令（或使用 Postman / curl）。

#### 2.3.1 健康检查

```bash
curl http://localhost:8000/health
```

**预期结果：**
```json
{"status": "ok", "version": "0.1.0"}
```

#### 2.3.2 认证端点

```bash
# 获取当前用户（当前为占位数据）
curl http://localhost:8000/api/auth/me
```

**预期结果：**
```json
{"user_id": "default", "username": "admin"}
```

```bash
# 登录（当前为占位）
curl -X POST http://localhost:8000/api/auth/login
```

**预期结果：**
```json
{"token": "placeholder", "token_type": "bearer"}
```

#### 2.3.3 股票端点

```bash
# 查询股票（占位）
curl http://localhost:8000/api/stocks/600519
```

**预期结果：**
```json
{"stock_code": "600519", "status": "not_analyzed"}
```

```bash
# 热门股票（占位）
curl http://localhost:8000/api/stocks/hot
```

**预期结果：**
```json
{"stocks": []}
```

#### 2.3.4 组合端点

```bash
# 组合列表（占位）
curl http://localhost:8000/api/portfolio/
```

**预期结果：**
```json
{"portfolios": []}
```

```bash
# 创建组合（占位）
curl -X POST http://localhost:8000/api/portfolio/
```

**预期结果：**
```json
{"id": "new", "status": "created"}
```

```bash
# 查询组合详情（占位）
curl http://localhost:8000/api/portfolio/p1
```

**预期结果：**
```json
{"id": "p1", "holdings": {}, "candidate_pool": []}
```

#### 2.3.5 告警端点

```bash
# 告警列表（占位）
curl http://localhost:8000/api/alerts/
```

**预期结果：**
```json
{"alerts": []}
```

```bash
# 未读告警（占位）
curl http://localhost:8000/api/alerts/unread
```

**预期结果：**
```json
{"alerts": [], "count": 0}
```

---

### 2.4 Swagger UI 验证

浏览器打开：

```
http://localhost:8000/docs
```

**预期结果：**
- 页面标题显示 **AI Investment OS**
- 显示 4 个 API 分组：`auth`、`stocks`、`portfolio`、`alerts`
- 展开每个分组能看到对应端点
- 点击 "Try it out" → "Execute" 能正常返回 JSON 响应
- 另一个文档页面：`http://localhost:8000/redoc`

---

### 2.5 LLM 连通性测试

在 `backend/` 目录下创建并运行临时脚本，验证 LLM API 连通性：

```bash
cd backend
python -c "
from app.config import settings
from app.services.llm_adapter import LLMAdapter

print(f'LLM Provider: {settings.llm_base_url}')
print(f'Model: {settings.llm_model}')

adapter = LLMAdapter(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    model=settings.llm_model,
)

result = adapter.generate('用一句话介绍贵州茅台这只股票。')
print(f'Tokens used: {result[\"tokens\"]}')
print(f'Latency: {result[\"latency_ms\"]}ms')
print(f'Response: {result[\"content\"][:200]}')

if result.get('error'):
    print(f'ERROR: {result[\"error\"]}')
else:
    print('LLM connection OK!')
"
```

**预期结果（正常情况）：**
```
LLM Provider: https://api.deepseek.com
Model: deepseek-chat
Tokens used: 120
Latency: 1500ms
Response: 贵州茅台（600519）是中国白酒行业的龙头企业...
LLM connection OK!
```

**预期结果（API Key 无效）：**
```
ERROR: Error code: 401 - {'error': {'message': 'Invalid API Key', ...}}
```

**检查点：**
- `Tokens used > 0` 说明 LLM 调用成功
- 出现 `401` 说明 API Key 错误，检查 `.env` 中 `LLM_API_KEY`
- 出现 `Connection refused` 说明 `LLM_BASE_URL` 不可达，检查网络或 URL

---

### 2.6 数据服务集成测试

测试 akshare 行情数据服务是否正常工作：

```bash
cd backend
python -c "
from app.services.market_data import MarketDataService

svc = MarketDataService()

# 测试实时行情
print('=== 实时行情测试 ===')
quote = svc.get_realtime_quote('600519')
if quote:
    print(f'股票: {quote.get(\"name\")}')
    print(f'最新价: {quote.get(\"latest_price\")}')
    print(f'涨跌幅: {quote.get(\"change_pct\")}%')
    print('实时行情 OK!')
else:
    print('实时行情返回空（非交易时间或网络问题）')

# 测试 K 线数据
print()
print('=== K线数据测试 ===')
kline = svc.get_kline('600519', days=30)
if kline:
    print(f'获取到 {len(kline)} 条 K 线数据')
    print(f'最新一条: {kline[-1]}')
    print('K线数据 OK!')
else:
    print('K线数据返回空')

# 测试热门股票
print()
print('=== 热门股票测试 ===')
hot = svc.get_hot_stocks(5)
if hot:
    print(f'获取到 {len(hot)} 只热门股票')
    for s in hot[:3]:
        print(f'  {s[\"name\"]} ({s[\"stock_code\"]}) 涨跌幅: {s[\"change_pct\"]}%')
    print('热门股票 OK!')
else:
    print('热门股票返回空')
"
```

**预期结果（交易时间 9:30-15:00）：**
```
=== 实时行情测试 ===
股票: 贵州茅台
最新价: 1500.0
涨跌幅: 0.5%
实时行情 OK!

=== K线数据测试 ===
获取到 22 条 K 线数据
最新一条: {'date': '2026-07-03', 'open': 1495.0, 'close': 1500.0, ...}
K线数据 OK!

=== 热门股票测试 ===
获取到 5 只热门股票
  贵州茅台 (600519) 涨跌幅: 0.5%
  中国平安 (601318) 涨跌幅: -0.3%
  招商银行 (600036) 涨跌幅: 0.2%
热门股票 OK!
```

**预期结果（非交易时间）：**
- `实时行情` 可能返回上一个交易日的收盘数据
- `K线数据` 和 `热门股票` 正常返回

**预期结果（网络异常）：**
```
实时行情返回空（非交易时间或网络问题）
```

---

## 3. Docker 本地测试

```bash
# 在项目根目录
cp .env.example .env
# 编辑 .env 填入 LLM 配置

# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps
```

**预期结果：**
```
NAME                    STATUS          PORTS
ai-investment-backend   Up              0.0.0.0:8000->8000/tcp
ai-investment-frontend  Up              0.0.0.0:3000->3000/tcp
ai-investment-redis     Up (healthy)    0.0.0.0:6379->6379/tcp
```

**检查点：**
- 三个服务均为 `Up` 状态
- Redis 显示 `(healthy)`
- 前端容器在 Phase 4 之前会启动失败（正常，因为 `frontend/` 还没有 `package.json`）

```bash
# 查看后端日志
docker compose logs backend --tail 20

# 在容器内运行测试
docker compose exec backend python -m pytest tests/ -v

# 验证 API
curl http://localhost:8000/health
# 预期: {"status": "ok", "version": "0.1.0"}

# 停止服务
docker compose down
```

---

## 4. 云服务器测试

以下假设你使用 Ubuntu 2C4G 云服务器。

### 4.1 首次部署

```bash
# SSH 登录服务器
ssh user@your-server-ip

# 克隆项目
git clone <your-repo-url>
cd AI_Investment_OS

# 配置环境变量
cp .env.example .env
nano .env  # 编辑填入 LLM_API_KEY 等

# 进入后端目录
cd backend

# 安装依赖（建议使用虚拟环境）
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 初始化数据库
python -m app.init_db

# 验证数据库文件已创建
ls -la data/investment.db
# 预期: 文件存在，大小 > 0
```

### 4.2 服务验证

```bash
# 后台启动服务（生产模式）
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# 等待几秒后检查进程
sleep 3
ps aux | grep uvicorn
# 预期: 看到 uvicorn app.main:app --host 0.0.0.0 --port 8000 进程

# 检查日志
tail -20 server.log
# 预期: 无 Error/Traceback，显示 "Application startup complete"

# 本地验证
curl http://localhost:8000/health
# 预期: {"status": "ok", "version": "0.1.0"}

# 运行测试
python -m pytest tests/ -v
# 预期: 50 passed
```

### 4.3 外网访问测试

```bash
# 在本地电脑（不是服务器）运行：

# 替换为你的服务器 IP
curl http://<your-server-ip>:8000/health
# 预期: {"status": "ok", "version": "0.1.0"}

# 浏览器打开
# http://<your-server-ip>:8000/docs
# 预期: 正常显示 Swagger UI
```

**如果外网无法访问，检查防火墙：**

```bash
# 在服务器上执行
sudo ufw allow 8000/tcp
sudo ufw reload
sudo ufw status
# 预期: 8000/tcp ALLOW  Anywhere
```

**如果是云服务商安全组限制：**
- 登录云控制台 → 安全组 → 添加入站规则：TCP 8000 端口，来源 0.0.0.0/0

---

## 5. 预期结果速查表

| 测试项 | 命令 | 预期结果 |
|-------|------|---------|
| 单元测试 | `pytest tests/ -v` | `50 passed` |
| 健康检查 | `curl localhost:8000/health` | `{"status":"ok","version":"0.1.0"}` |
| 认证 /me | `curl localhost:8000/api/auth/me` | `{"user_id":"default","username":"admin"}` |
| 认证 /login | `curl -X POST localhost:8000/api/auth/login` | `{"token":"placeholder","token_type":"bearer"}` |
| 股票查询 | `curl localhost:8000/api/stocks/600519` | `{"stock_code":"600519","status":"not_analyzed"}` |
| 热门股票 | `curl localhost:8000/api/stocks/hot` | `{"stocks":[]}` |
| 组合列表 | `curl localhost:8000/api/portfolio/` | `{"portfolios":[]}` |
| 组合创建 | `curl -X POST localhost:8000/api/portfolio/` | `{"id":"new","status":"created"}` |
| 组合详情 | `curl localhost:8000/api/portfolio/p1` | `{"id":"p1","holdings":{},"candidate_pool":[]}` |
| 告警列表 | `curl localhost:8000/api/alerts/` | `{"alerts":[]}` |
| 未读告警 | `curl localhost:8000/api/alerts/unread` | `{"alerts":[],"count":0}` |
| Swagger UI | 浏览器访问 `/docs` | 显示 4 个 API 分组，可交互测试 |
| LLM 连通 | 运行 2.5 节脚本 | `LLM connection OK!` |
| 行情数据 | 运行 2.6 节脚本 | `实时行情 OK!` + `K线数据 OK!` |
| Docker 启动 | `docker compose up -d` | 3 个容器 Up |
| 数据库文件 | `ls data/investment.db` | 文件存在，大小 > 0 |

---

## 6. 常见问题排查

### Q1: `ModuleNotFoundError: No module named 'xxx'`

```bash
# 确保在虚拟环境中且已安装所有依赖
pip install -r requirements.txt
```

### Q2: `Address already in use: 8000`

```bash
# 查找占用 8000 端口的进程并关闭
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8000
kill -9 <PID>
```

### Q3: 测试中出现 `FAILED` 或 `ERROR`

```bash
# 查看详细错误
python -m pytest tests/ -v --tb=long

# 只运行失败的测试
python -m pytest tests/ -v --lf
```

### Q4: LLM 调用返回 `401 Unauthorized`

- 检查 `.env` 中 `LLM_API_KEY` 是否正确
- 确认 API Key 是否过期或余额不足
- DeepSeek 控制台：https://platform.deepseek.com/

### Q5: akshare 行情数据返回空

- **非交易时间**（15:00后、周末、节假日）：实时行情可能返回上一交易日数据或空值，这是正常的
- **网络问题**：服务器可能无法访问东方财富数据源，检查网络连通性
- **akshare 版本**：`pip install --upgrade akshare`

### Q6: Docker 中前端容器启动失败

这是正常的。前端代码在 Phase 4 才实现，当前 `frontend/` 目录下还没有 `package.json`。只需关注 `backend` 和 `redis` 容器：

```bash
docker compose up -d backend redis
```

### Q7: 云服务器 2C4G 内存不足

`sentence-transformers` 和 `faiss-cpu` 在首次加载 embedding 模型时需要约 1GB 内存。如果内存紧张：

```bash
# 只在需要时才实例化 VectorStore，不要在启动时加载
# 或者使用 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

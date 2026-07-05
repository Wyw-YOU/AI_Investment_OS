# AI Investment OS — Phase 3 测试报告

**日期：** 2026-07-05
**阶段：** Phase 0/1/2/3（Foundation + Data Layer + Agent Engine + Portfolio & Event Engine）
**测试结果：** 83 passed, 0 failed

---

## 目录

1. [Phase 3 新增内容概览](#1-phase-3-新增内容概览)
2. [单元测试结果](#2-单元测试结果)
3. [代码审核](#3-代码审核)
4. [Portfolio 服务手动测试](#4-portfolio-服务手动测试)
5. [Event & Alert 服务手动测试](#5-event--alert-服务手动测试)
6. [WebSocket 手动测试](#6-websocket-手动测试)
7. [API 端点测试](#7-api-端点测试)
8. [预期结果速查表](#8-预期结果速查表)
9. [遗留问题与建议](#9-遗留问题与建议)

---

## 1. Phase 3 新增内容概览

### 新增文件（6 个）

| 文件 | 说明 | 行数 |
|------|------|------|
| `app/services/portfolio_service.py` | 组合 CRUD、候选池、权重优化、风险评分 | 180 |
| `app/services/event_service.py` | 事件 CRUD、告警 CRUD、告警规则引擎 | 119 |
| `app/services/websocket_manager.py` | WebSocket 连接管理、实时推送 | 64 |
| `tests/test_portfolio.py` | Portfolio 服务测试（4 个测试类） | 93 |
| `tests/test_events.py` | Event/Alert/RuleEngine 测试（3 个测试类） | 68 |
| `tests/test_websocket.py` | WebSocket 管理器测试 | 40 |

### 修改文件（5 个）

| 文件 | 变更内容 |
|------|---------|
| `app/api/portfolio.py` | 占位桩 → 8 个完整端点（CRUD + 候选池 + 权重 + 风险） |
| `app/api/alerts.py` | 占位桩 → 3 个完整端点（列表 + 未读 + 标记已读） |
| `app/main.py` | 新增 WebSocket `/ws/{user_id}` 端点 |
| `app/agents/base.py` | 新增 `validate_llm_output()` 校验方法 |
| `app/agents/{finance,technical,news,judge}.py` | 使用 LLM 输出校验 |

### 架构设计

```
API Layer                    Service Layer              Data Layer
─────────                    ─────────────              ──────────
POST /api/portfolio/    →    PortfolioService      →    Portfolio (ORM)
GET  /api/portfolio/    →    .list_by_user()       →    portfolios 表
POST /{id}/pool         →    .add_to_pool()        →    candidate_pool JSON
POST /{id}/suggest-weights → .suggest_weights()    →    StockState.score
GET  /{id}/risk         →    .calc_risk_score()    →    sector_exposure

GET  /api/alerts/       →    AlertService          →    Alert (ORM)
GET  /api/alerts/unread →    .get_alerts(unread)   →    alerts 表
POST /{id}/read         →    .mark_read()          →    is_read

WS   /ws/{user_id}      →    ConnectionManager     →    内存（无持久化）
```

---

## 2. 单元测试结果

```
tests/test_portfolio.py      (9 tests)   — CRUD、候选池、权重、风险
tests/test_events.py         (7 tests)   — 事件、告警、规则引擎
tests/test_websocket.py      (4 tests)   — 连接、断开、发送、广播
tests/test_agents.py         (6 tests)   — State + Registry（Phase 2）
tests/test_agent_schemas.py  (7 tests)   — Agent 输出格式（Phase 2）
tests/test_cache.py          (7 tests)   — 缓存服务（Phase 1）
tests/test_circuit_breaker.py (4 tests)  — 熔断器（Phase 0）
tests/test_indicators.py     (14 tests)  — 技术指标（Phase 1）
tests/test_llm_adapter.py    (7 tests)   — LLM 适配器（Phase 1）
tests/test_models.py         (6 tests)   — 数据库模型（Phase 0）
tests/test_news.py           (4 tests)   — 新闻事件（Phase 1）
tests/test_schemas.py        (3 tests)   — Pydantic Schema（Phase 0）
tests/test_smoke.py          (5 tests)   — API 冒烟测试（Phase 0）
─────────────────────────────────────────────────
Total: 83 passed, 0 failed
```

**运行命令：** `cd backend && python -m pytest tests/ -v`

---

## 3. 代码审核

### 总评

| 维度 | 得分 | 说明 |
|------|------|------|
| 正确性 | 4.5/5 | 所有测试通过，业务逻辑正确 |
| 架构一致性 | 4.5/5 | Service → ORM 分层清晰，API 正确使用 Depends 注入 |
| 安全性 | 3.5/5 | 无认证保护（Phase 5 实现），SQL 使用 ORM 无注入风险 |
| 性能 | 4/5 | 查询简洁无 N+1，WebSocket 自动清理死连接 |
| 可维护性 | 4.5/5 | 命名清晰，职责单一，规则引擎可配置 |
| **综合** | **4.2/5** | |

### 亮点

- **权重优化** — `suggest_weights` 基于 `StockState.score` 按比例分配，归一化后总和为 1.0
- **风险评分** — 三维评估（单股集中度、行业集中度、持仓数量），阈值可配置
- **告警规则引擎** — `AlertRuleEngine` 纯静态方法，无副作用，易于测试和扩展
- **WebSocket 死连接清理** — `send_to_user` 自动移除断开的连接，避免内存泄漏
- **候选池去重** — `add_to_pool` 检查 `if stock_code not in pool`，防止重复添加

### 发现的问题

#### 🟡 [Medium] `suggest_weights` 中 `agent_outputs` 参数未使用

**文件:** `portfolio_service.py:87`

`def suggest_weights(self, portfolio_id: str, agent_outputs: dict = None) -> dict:`

`agent_outputs` 参数在函数体内从未被引用。权重完全基于 `StockState.score` 计算，忽略了 Agent 分析结果。Phase 3 的设计文档提到应结合 Agent 输出优化权重。

**建议：** 要么移除未使用参数，要么实现基于 agent_outputs 的权重调整逻辑。

#### 🟡 [Medium] `portfolio.py` API 中 `create_portfolio` 参数暴露在 URL query 中

**文件:** `api/portfolio.py:31`

```python
@router.post("/")
async def create_portfolio(name: str, user_id: str = "default", db: Session = Depends(get_db)):
```

`name` 作为 query parameter（`POST /api/portfolio/?name=xxx`），应该用 Pydantic Body model：

```python
class PortfolioCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

@router.post("/")
async def create_portfolio(body: PortfolioCreateBody, user_id: str = "default", db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    p = svc.create(user_id, body.name)
```

#### 🟡 [Medium] `alerts.py` 中 `Alert.is_read == False` 使用 SQLAlchemy 比较

**文件:** `event_service.py:74`, `event_service.py:88`

`Alert.is_read == False` 在 SQLAlchemy 中可能产生 `is_read = 0` 的 SQL（因为 Python `False == 0`），这在 SQLite 中工作正常，但 PostgreSQL 中 `Boolean` 列应使用 `Alert.is_read.is_(False)`。

#### 🟡 [Low] `portfolio.py` API 中 `add_to_pool` 的 `stock_code` 也在 query 中

**文件:** `api/portfolio.py:60`

```python
async def add_to_pool(portfolio_id: str, stock_code: str, db: Session = Depends(get_db)):
```

`stock_code` 应放在 request body 中，而非 URL query。

#### 🟡 [Low] WebSocket 端点无认证

**文件:** `main.py:44`

`/ws/{user_id}` 直接信任 URL 中的 `user_id`，无任何鉴权。恶意客户端可以伪造任意 `user_id` 接收他人的告警推送。

**建议：** 在 WebSocket 握手阶段验证 token（Phase 5 实现完整认证后补充）。

---

## 4. Portfolio 服务手动测试

```bash
cd backend
python -c "
import json
from app.services.portfolio_service import PortfolioService
from app.models.user import User
from app.models.stock import StockState
from app.database import SessionLocal

db = SessionLocal()

# 创建测试用户
db.add(User(id='u1', username='testuser'))
db.commit()

# 创建组合
svc = PortfolioService(db)
p = svc.create('u1', '我的投资组合')
print(f'创建组合: id={p.id}, name={p.name}')

# 添加候选股
svc.add_to_pool(p.id, '600519')
svc.add_to_pool(p.id, '000001')
svc.add_to_pool(p.id, '601318')
print(f'候选池: {json.loads(p.candidate_pool)}')

# 添加 StockState 评分
db.add(StockState(stock_code='600519', score=85.0, sector='白酒'))
db.add(StockState(stock_code='000001', score=70.0, sector='银行'))
db.add(StockState(stock_code='601318', score=65.0, sector='保险'))
db.commit()

# 权重建议
result = svc.suggest_weights(p.id)
print(f'权重建议: {result[\"weights\"]}')
print(f'权重总和: {sum(result[\"weights\"].values()):.4f}')

# 风险评分
risk = svc.calc_risk_score(p.id)
print(f'风险评分: {risk[\"risk_score\"]}')
print(f'风险等级: {risk[\"risk_level\"]}')
print(f'风险因素: {risk[\"risk_factors\"]}')

db.close()
"
```

**预期结果：**
```
创建组合: id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx, name=我的投资组合
候选池: ['600519', '000001', '601318']
权重建议: {'600519': 0.3864, '000001': 0.3182, '601318': 0.2955}
权重总和: 1.0000
风险评分: 0
风险等级: LOW
风险因素: []
```

---

## 5. Event & Alert 服务手动测试

```bash
cd backend
python -c "
from app.services.event_service import EventService, AlertService, AlertRuleEngine
from app.models.user import User
from app.models.stock import StockState
from app.database import SessionLocal

db = SessionLocal()
db.add(User(id='u1', username='testuser'))
db.commit()

# 创建事件
esvc = EventService(db)
e1 = esvc.create_event('600519', 'news', '茅台Q3财报超预期', impact_score=0.8)
e2 = esvc.create_event('600519', 'price', '股价突破2000元', impact_score=0.9)
e3 = esvc.create_event('000001', 'news', '平安银行分红', impact_score=0.3)
print(f'全部事件: {len(esvc.get_events())} 条')
print(f'茅台事件: {len(esvc.get_events(\"600519\"))} 条')

# 创建告警
asvc = AlertService(db)
asvc.create_alert('u1', '600519', 'score_change', '评分上升 0.6')
asvc.create_alert('u1', '600519', 'risk_level', '风险等级升高')
print(f'未读告警: {asvc.unread_count(\"u1\")} 条')

# 标记已读
alerts = asvc.get_alerts('u1')
asvc.mark_read(alerts[0].id)
print(f'标记后未读: {asvc.unread_count(\"u1\")} 条')

# 规则引擎
state = StockState(stock_code='600519', score=8.0, alert_level='HIGH')
triggered = AlertRuleEngine.evaluate('600519', state, {'score': 7.0})
print(f'规则触发: {len(triggered)} 条告警')
for a in triggered:
    print(f'  {a[\"alert_type\"]}: {a[\"message\"]}')

db.close()
"
```

**预期结果：**
```
全部事件: 3 条
茅台事件: 2 条
未读告警: 2 条
标记后未读: 1 条
规则触发: 2 条告警
  score_change: 600519 评分上升 1.00，当前 8.00
  risk_level: 600519 风险等级: HIGH
```

---

## 6. WebSocket 手动测试

### 方法 1：Python 脚本测试

```bash
pip install websockets
cd backend

# 终端 1：启动服务
uvicorn app.main:app --reload --port 8000

# 终端 2：运行 WebSocket 客户端
python -c "
import asyncio
import websockets
import json

async def test():
    uri = 'ws://localhost:8000/ws/testuser'
    async with websockets.connect(uri) as ws:
        # 发送消息
        await ws.send('hello')
        # 接收回显
        response = await ws.recv()
        data = json.loads(response)
        print(f'收到: type={data[\"type\"]}, data={data[\"data\"]}')
        assert data['type'] == 'echo'
        assert data['data'] == 'hello'
        print('WebSocket 测试通过!')

asyncio.run(test())
"
```

**预期结果：**
```
收到: type=echo, data=hello
WebSocket 测试通过!
```

### 方法 2：浏览器控制台测试

```javascript
// 浏览器打开 http://localhost:8000/docs 后，F12 打开控制台
const ws = new WebSocket('ws://localhost:8000/ws/testuser');
ws.onopen = () => { console.log('Connected'); ws.send('hello'); };
ws.onmessage = (e) => { console.log('Received:', JSON.parse(e.data)); };
```

**预期结果：**
```
Connected
Received: {type: "echo", data: "hello"}
```

---

## 7. API 端点测试

启动服务后（`uvicorn app.main:app --reload --port 8000`），在另一个终端测试：

### 7.1 Portfolio API

```bash
# 创建组合
curl -X POST "http://localhost:8000/api/portfolio/?name=MyPortfolio&user_id=u1"

# 列表
curl "http://localhost:8000/api/portfolio/?user_id=u1"

# 查询详情（替换 <id> 为实际返回的 id）
curl "http://localhost:8000/api/portfolio/<id>"

# 添加候选股
curl -X POST "http://localhost:8000/api/portfolio/<id>/pool?stock_code=600519"
curl -X POST "http://localhost:8000/api/portfolio/<id>/pool?stock_code=000001"

# 权重建议
curl -X POST "http://localhost:8000/api/portfolio/<id>/suggest-weights"

# 风险评分
curl "http://localhost:8000/api/portfolio/<id>/risk"

# 删除
curl -X DELETE "http://localhost:8000/api/portfolio/<id>"
```

### 7.2 Alert API

```bash
# 告警列表
curl "http://localhost:8000/api/alerts/?user_id=u1"

# 未读告警
curl "http://localhost:8000/api/alerts/unread?user_id=u1"

# 标记已读（替换 <id>）
curl -X POST "http://localhost:8000/api/alerts/<id>/read"
```

### 7.3 Swagger UI

浏览器打开 `http://localhost:8000/docs`，可以看到新增的端点：
- `portfolio` 分组：8 个端点
- `alerts` 分组：3 个端点
- WebSocket `/ws/{user_id}`（Swagger 不支持 WebSocket 测试，需用脚本或浏览器）

---

## 8. 预期结果速查表

| 测试项 | 命令 | 预期结果 |
|-------|------|---------|
| 全部测试 | `pytest tests/ -v` | `83 passed` |
| 创建组合 | `POST /api/portfolio/?name=X` | `{"id": "...", "name": "X", "status": "created"}` |
| 组合列表 | `GET /api/portfolio/?user_id=u1` | `{"portfolios": [...]}` |
| 添加候选股 | `POST /{id}/pool?stock_code=600519` | `{"candidate_pool": ["600519"]}` |
| 权重建议 | `POST /{id}/suggest-weights` | `{"weights": {"600519": 0.6, "000001": 0.4}}` 权重和=1.0 |
| 风险评分 | `GET /{id}/risk` | `{"risk_score": N, "risk_level": "LOW/MEDIUM/HIGH"}` |
| 告警列表 | `GET /api/alerts/?user_id=u1` | `{"alerts": [...]}` |
| 未读告警 | `GET /api/alerts/unread?user_id=u1` | `{"alerts": [...], "count": N}` |
| 标记已读 | `POST /api/alerts/{id}/read` | `{"status": "ok"}` |
| WebSocket 连接 | `ws://localhost:8000/ws/user1` | 连接成功，发送消息收到 echo |
| 规则引擎 | `AlertRuleEngine.evaluate(...)` | score_change≥0.5 或 alert_level=HIGH 触发告警 |

---

## 9. 遗留问题与建议

### 代码层

| 问题 | 严重性 | 说明 |
|------|--------|------|
| `suggest_weights` 的 `agent_outputs` 参数未使用 | Medium | 权重仅基于 StockState.score，忽略了 Agent 分析结果 |
| `create_portfolio` 的 `name` 在 query parameter | Medium | 应改用 Pydantic Body model |
| `add_to_pool` 的 `stock_code` 在 query parameter | Low | 应改用 request body |
| `Alert.is_read == False` SQLAlchemy 写法 | Low | PostgreSQL 应使用 `is_(False)` |
| WebSocket 端点无认证 | Medium | 任意 user_id 可连接，Phase 5 补充认证 |

### 功能待完善

| 功能 | 当前状态 | 说明 |
|------|---------|------|
| Agent 输出集成到权重优化 | 未实现 | `suggest_weights` 应结合 Judge Agent 的 verdict 调整权重 |
| WebSocket 推送集成 | 基础完成 | `send_alert` 和 `send_stock_update` 方法已实现，但未接入分析流程自动推送 |
| 事件自动检测 | 未实现 | 需要定时任务扫描 StockState 变化并触发 `AlertRuleEngine` |
| Portfolio Engine 与 Agent 联动 | 未实现 | 分析完成后应自动更新 StockState.score 并触发告警检查 |
| 用户认证 | 未实现 | 所有端点使用 `user_id="default"` 硬编码，Phase 5 实现 JWT 认证 |

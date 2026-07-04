# Phase 1 开发报告 — Data & Service Layer

> 开发日期：2026-07-04
> 阶段：Sprint 1-2 — Data & Service Layer
> 状态：DONE

---

## 1. 任务完成清单

| # | Task | Story Points | Status |
|---|------|:------------:|:------:|
| 1.1 | SQLite ORM 模型 | 3 | DONE (Phase 0) |
| 1.2 | 行情数据 API 集成 | 5 | DONE |
| 1.3 | 财务数据 API | 5 | DONE |
| 1.4 | 新闻数据采集 | 3 | DONE |
| 1.5 | Redis 缓存层 | 2 | DONE |
| 1.6 | FAISS 向量存储 | 5 | DONE |
| 1.7 | 技术指标计算服务 | 3 | DONE |
| 1.8 | LLM 适配器服务 | 3 | DONE |

**Total: 29 / 29 story points**

---

## 2. 模块实现概览

### 2.1 缓存层 — `services/cache.py`

| 组件 | 说明 |
|------|------|
| `CacheService` | Redis 封装，自动 fallback 到内存缓存 |
| `MemoryCache` | 内存 LRU，带 TTL 过期，用于开发和 Redis 不可用时 |
| Cache Key 规范 | `market:realtime:{code}` TTL 30s, `financial:{code}` TTL 24h 等 |

**设计决策：** Redis 连接失败时自动降级到内存缓存，不阻塞服务启动。适合 2C4G 服务器资源受限场景。

### 2.2 行情数据 — `services/market_data.py`

| 方法 | 数据源 | 缓存 TTL |
|------|--------|:--------:|
| `get_kline()` | akshare `stock_zh_a_hist` | 1h |
| `get_realtime_quote()` | akshare `stock_zh_a_spot_em` | 30s |
| `get_stock_info()` | akshare `stock_individual_info_em` | 24h |
| `get_hot_stocks()` | akshare 全市场排序 | 无缓存 |

**数据标准化：** akshare 返回中文列名，统一转换为英文 key（date, open, close, high, low, volume）。

### 2.3 财务数据 — `services/financial.py`

| 方法 | 功能 |
|------|------|
| `get_financial_summary()` | EPS、ROE、营收、净利润、毛利率、负债率 |
| `get_valuation()` | PE、PB、PS、总市值、流通市值 |
| `get_growth_rates()` | 营收增长率、利润增长率（同比） |

**容错处理：** akshare 财务数据接口不稳定，每个方法都有 fallback 返回默认值。

### 2.4 新闻数据 — `services/news.py`

| 方法 | 功能 |
|------|------|
| `get_stock_news()` | 个股新闻（缓存 30min） |
| `get_market_news()` | 市场总览新闻 |
| `extract_key_events()` | 规则引擎提取关键事件（高/中/低三级） |

**事件分类关键词：**
- HIGH: 涨停、跌停、暴雷、退市、收购、重组
- MEDIUM: 分红、增持、减持、回购
- LOW: 调研、评级、研报（被过滤）

### 2.5 技术指标 — `services/indicators.py`

| 指标 | 函数 | 输出 |
|------|------|------|
| MACD | `calculate_macd()` | macd_line, signal_line, histogram |
| RSI | `calculate_rsi()` | value (0-100), signal (overbought/oversold/neutral) |
| KDJ | `calculate_kdj()` | k, d, j, signal |
| BOLL | `calculate_bollinger()` | upper, middle, lower, signal |
| MA | `calculate_ma()` | ma5, ma10, ma20, ma60 |
| ALL | `calculate_all_indicators()` | 上述全部指标 |

**纯计算模块：** 无外部依赖，可独立测试。EMA/SMA 为基础实现。

### 2.6 LLM 适配器 — `services/llm_adapter.py`

| 方法 | 功能 |
|------|------|
| `generate()` | 通用 LLM 调用，返回 content + tokens + latency |
| `generate_json()` | JSON 模式调用，自动解析 + 容错提取 |

**特性：**
- 指数退避重试（默认 3 次）
- Token 用量追踪（`stats` 属性）
- JSON 解析容错（从非标准 JSON 中提取 `{}` 内容）
- **OpenAI 兼容接口** — 通过 `base_url` 支持国产大模型（DeepSeek / 通义千问 / MiMo / Moonshot 等），切换模型只需改 `.env` 中三个变量

**已验证 Provider：**

| Provider | base_url | model |
|----------|----------|-------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| MiMo | `https://api.xiaomi.com/v1` | `MiMo-7B` |
| Moonshot | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |

### 2.7 向量存储 — `services/vector_store.py`

| 方法 | 功能 |
|------|------|
| `add_documents()` | 文档向量化并存入 FAISS |
| `search()` | 语义检索，返回 top_k 结果及相似度分数 |
| `load()` / `_save()` | 持久化到磁盘 |

**模型选择：** 默认 `text2vec-base-chinese`（中文金融文本优化），首次运行需下载模型。

---

## 3. 测试方法

### 3.1 测试覆盖

| 测试文件 | 测试对象 | 用例数 |
|----------|---------|:------:|
| `test_indicators.py` | 技术指标计算（MACD/RSI/KDJ/BOLL/MA） | 14 |
| `test_cache.py` | 缓存服务（内存模式 + Redis fallback） | 7 |
| `test_llm_adapter.py` | LLM 适配器（mock，含重试测试） | 5 |
| `test_news.py` | 新闻事件提取（关键词分类） | 4 |
| `test_circuit_breaker.py` | 熔断器三态转换 | 4 |
| `test_smoke.py` (Phase 0) | API 冒烟测试 | 5 |
| `test_models.py` (Phase 0) | 数据库模型 CRUD | 6 |
| `test_schemas.py` (Phase 0) | Pydantic 校验 | 3 |
| **Total** | | **48** |

### 3.2 运行测试

```bash
cd backend
pip install -e ".[dev]"

# 运行全部测试
pytest tests/ -v

# 仅运行 Phase 1 服务层测试
pytest tests/test_indicators.py tests/test_cache.py tests/test_llm_adapter.py tests/test_news.py tests/test_circuit_breaker.py -v

# 查看覆盖率
pytest tests/ --cov=app --cov-report=term-missing
```

### 3.3 测试策略

| 模块 | 策略 | 说明 |
|------|------|------|
| indicators | 纯函数测试 | 无 mock，直接验证计算结果 |
| cache | 内存模式测试 | Redis 不可用时自动降级，测试内存缓存行为 |
| llm_adapter | Mock OpenAI | 模拟成功/失败/重试场景 |
| news | 关键词规则测试 | 验证事件分类逻辑 |
| circuit_breaker | 状态转换测试 | 验证 CLOSED→OPEN→HALF_OPEN 流程 |

### 3.4 外部依赖说明

以下模块需要真实网络环境才能完全测试，在 CI 中建议跳过：

| 模块 | 依赖 | 本地测试 | CI 建议 |
|------|------|---------|---------|
| market_data | akshare API | 需要网络 | mock |
| financial | akshare API | 需要网络 | mock |
| vector_store | sentence-transformers | 需要下载模型 | 跳过 |

---

## 4. 云服务器部署说明

针对 **2 核 4G Ubuntu 服务器**的部署注意事项：

### 资源评估

| 组件 | 内存占用 | CPU 需求 |
|------|:--------:|:--------:|
| FastAPI 后端 | ~200MB | 低 |
| Redis | ~50MB | 低 |
| FAISS + embedding 模型 | ~800MB（首次加载） | 中 |
| **合计** | ~1.1GB | 2 核足够 |

> 4G 内存足够运行全部服务。embedding 模型加载后常驻内存，首次启动较慢。

### 部署命令

```bash
# 在 Ubuntu 服务器上
git clone <repo-url>
cd AI_Investment_OS
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY

# Docker 方式
docker-compose up -d

# 或直接运行
cd backend
pip install -r requirements.txt
python -m app.init_db
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

---

## 5. 文件变更清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/app/services/cache.py` | New | Redis 缓存 + 内存 fallback |
| `backend/app/services/market_data.py` | New | akshare 行情数据 |
| `backend/app/services/financial.py` | New | 财务数据服务 |
| `backend/app/services/news.py` | New | 新闻采集 + 事件提取 |
| `backend/app/services/indicators.py` | New | 技术指标计算 |
| `backend/app/services/llm_adapter.py` | New | LLM 统一适配器 |
| `backend/app/services/vector_store.py` | New | FAISS 向量存储 |
| `backend/tests/test_indicators.py` | New | 14 个指标测试 |
| `backend/tests/test_cache.py` | New | 7 个缓存测试 |
| `backend/tests/test_llm_adapter.py` | New | 5 个 LLM 测试 |
| `backend/tests/test_news.py` | New | 4 个新闻测试 |
| `backend/tests/test_circuit_breaker.py` | New | 4 个熔断器测试 |
| `开发时间线.md` | Updated | Phase 1 状态 → DONE |

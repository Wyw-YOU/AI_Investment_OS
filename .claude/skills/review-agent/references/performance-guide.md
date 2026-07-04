# Performance Guide — AI Investment OS

## 数据库性能

### 查询优化
- stock_state 表按 stock_code 查询最频繁 → 确保 PRIMARY KEY
- agent_logs 按 (stock_code, created_at) 查询 → 联合索引
- market_events 按 (stock_code, event_time) 查询 → 联合索引

### N+1 检测
- Portfolio 查询 holdings 时不要逐个 stock 查询详情
- 批量获取：`SELECT * FROM stock_state WHERE stock_code IN (...)`

### 连接池
- SQLite 单文件数据库，写操作需要串行
- 使用 WAL 模式提升并发读性能：`PRAGMA journal_mode=WAL`

## 缓存策略

### Redis 缓存分层

| 数据类型 | TTL | 说明 |
|---------|-----|------|
| 实时行情 | 30s | 高频变化 |
| K 线历史 | 1h | 每日更新 |
| 财务数据 | 24h | 季度更新 |
| AI 分析结果 | 1h | 避免重复 LLM 调用 |
| Agent state | 5min | 工作流中间状态 |

### 缓存 key 规范
```
market:realtime:{stock_code}
market:kline:{stock_code}:{period}
financial:{stock_code}:latest
analysis:{stock_code}:{date}
agent:state:{session_id}
```

## LLM 调用性能

### 优化策略
- **并行调用**: Finance/Technical/News/Risk Agent 之间无依赖，应并行调用
- **Prompt 缓存**: 相同 system prompt 的请求利用 prompt caching
- **小模型优先**: 开发阶段使用 GPT-4o-mini，生产切换 GPT-4o
- **Token 预算**: 每个 Agent 设置 max_tokens 上限，防止单次调用消耗过多

### 响应时间目标

| 操作 | 目标延迟 | 说明 |
|------|---------|------|
| 单个 Agent 调用 | < 10s | 含 LLM 调用 |
| 完整分析管道 | < 30s | 8 个 Agent 串并行 |
| API 端点（缓存命中） | < 200ms | Redis 缓存 |
| API 端点（缓存未命中） | < 500ms | 不含 LLM |
| WebSocket 推送延迟 | < 100ms | 事件触发到推送 |

## 前端性能

- 首屏加载 < 3s（Next.js SSR/SSG）
- 图表渲染使用 canvas 而非 SVG（ECharts/lightweight-charts）
- API 请求使用 React Query 缓存 + stale-while-revalidate
- 大列表使用虚拟滚动（react-window）

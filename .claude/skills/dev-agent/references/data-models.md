# Data Models — SQLAlchemy + Pydantic

## SQLite 表结构

### users
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    risk_profile TEXT DEFAULT '{}',  -- JSON: {tolerance, horizon, sectors}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### portfolios
```sql
CREATE TABLE portfolios (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    holdings TEXT DEFAULT '{}',       -- JSON: {"600519": 0.3, "000001": 0.2}
    candidate_pool TEXT DEFAULT '[]', -- JSON: ["600519", "000001", "000858"]
    risk_score REAL DEFAULT 0.0,
    expected_return REAL DEFAULT 0.0,
    sector_exposure TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### stock_state
```sql
CREATE TABLE stock_state (
    stock_code TEXT PRIMARY KEY,
    latest_price REAL,
    market_cap REAL,
    sector TEXT,
    last_analysis TEXT DEFAULT '{}',  -- JSON: 完整分析结果
    last_analysis_at TIMESTAMP,
    score REAL DEFAULT 0.0,           -- AI 综合评分
    score_change REAL DEFAULT 0.0,    -- 评分变化量
    alert_level TEXT DEFAULT 'NORMAL' -- NORMAL, WATCH, ALERT
);
```

### agent_logs
```sql
CREATE TABLE agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    input_snapshot TEXT,    -- JSON: 输入 State 快照
    output_snapshot TEXT,   -- JSON: Agent 输出
    confidence REAL,
    latency_ms INTEGER,
    tokens_used INTEGER,
    model_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### market_events
```sql
CREATE TABLE market_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    event_type TEXT NOT NULL,    -- news, price, volume, macro
    title TEXT,
    content TEXT,
    impact_score REAL DEFAULT 0.0,
    source TEXT,
    event_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### alerts
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    stock_code TEXT NOT NULL,
    alert_type TEXT NOT NULL,    -- score_change, risk_level, sentiment
    message TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Pydantic Model 示例

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PortfolioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    holdings: dict[str, float] = Field(default_factory=dict)
    candidate_pool: list[str] = Field(default_factory=list)

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioResponse(PortfolioBase):
    id: str
    user_id: str
    risk_score: float = 0.0
    expected_return: float = 0.0
    sector_exposure: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

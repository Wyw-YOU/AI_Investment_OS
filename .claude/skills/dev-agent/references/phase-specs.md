# InvestmentState — 核心状态定义

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class InvestmentState:
    # 用户上下文
    user_id: str = ""

    # 股票范围
    stock_pool: list[str] = field(default_factory=list)
    current_stock: str = ""

    # 原始数据（由 Service Layer 填充）
    market_data: dict = field(default_factory=dict)
    financial_data: dict = field(default_factory=dict)
    news_data: list = field(default_factory=list)
    indicators: dict = field(default_factory=dict)

    # Agent 输出（由各 Agent 填充）
    agent_outputs: dict[str, dict] = field(default_factory=dict)
    agent_confidence: dict[str, float] = field(default_factory=dict)

    # 风险配置
    risk_profile: dict = field(default_factory=dict)

    # 组合状态
    portfolio: dict = field(default_factory=dict)
    candidate_pool: list[str] = field(default_factory=list)

    # 最终产出
    final_report: dict = field(default_factory=dict)

    # 事件
    events: list = field(default_factory=list)

    # 决策
    decision: str = ""  # buy | sell | hold | watch
```

## 数据流规则

1. **Service Layer** 填充 `market_data`, `financial_data`, `news_data`, `indicators`
2. **分析 Agent** (Finance/Technical/News/Risk) 将结果写入 `agent_outputs[name]`
3. **Judge Agent** 读取所有 `agent_outputs`，输出综合评判
4. **Portfolio Agent** 读取 Judge 结果 + 现有 `portfolio`，输出权重建议
5. **Report Agent** 读取全部 State，生成 `final_report`

关键约束：Agent 之间不直接通信，全部通过 State 间接传递。

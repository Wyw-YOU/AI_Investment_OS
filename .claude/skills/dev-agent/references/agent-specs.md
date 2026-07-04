# Agent Output Schema — 统一输出规范

所有 Agent 必须返回以下结构，不允许有例外：

```json
{
  "output": {},
  "confidence": 0.0,
  "evidence": [],
  "reasoning": ""
}
```

## 字段说明

### output (dict)
Agent 的核心分析结果。结构因 Agent 而异：

**FinanceAgent:**
```json
{
  "output": {
    "pe_ratio": 35.2,
    "pb_ratio": 8.1,
    "roe": 0.32,
    "revenue_growth": 0.15,
    "net_profit_growth": 0.18,
    "debt_ratio": 0.45,
    "verdict": "undervalued|fairly_valued|overvalued",
    "key_metrics": {
      "strengths": ["高ROE", "营收持续增长"],
      "weaknesses": ["负债率偏高"]
    }
  }
}
```

**TechnicalAgent:**
```json
{
  "output": {
    "trend": "bullish|bearish|sideways",
    "support_levels": [100.0, 95.0],
    "resistance_levels": [110.0, 115.0],
    "indicators": {
      "macd": {"value": 0.5, "signal": "buy|sell|hold"},
      "rsi": {"value": 65.0, "signal": "neutral"},
      "kdj": {"k": 70, "d": 65, "j": 80, "signal": "overbought"}
    },
    "verdict": "buy|sell|hold"
  }
}
```

**NewsAgent:**
```json
{
  "output": {
    "sentiment_score": 0.7,
    "sentiment": "positive|negative|neutral",
    "key_events": [
      {"title": "...", "impact": "high|medium|low", "date": "..."}
    ],
    "rag_insights": ["从历史研报中提取的关键观点"],
    "verdict": "positive|negative|neutral"
  }
}
```

**RiskAgent:**
```json
{
  "output": {
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "volatility_30d": 0.25,
    "beta": 1.2,
    "sector_concentration": 0.3,
    "single_stock_risk": "high|medium|low",
    "risk_factors": ["行业政策风险", "估值泡沫风险"],
    "verdict": "acceptable|caution|dangerous"
  }
}
```

### confidence (float, 0.0 - 1.0)
Agent 对自身分析结果的信心程度：
- **0.9-1.0**: 数据充分，逻辑清晰，高度确信
- **0.7-0.9**: 数据基本完整，结论较可靠
- **0.5-0.7**: 部分数据缺失或存在不确定性
- **0.3-0.5**: 数据不足，结论仅为推测
- **0.0-0.3**: 几乎无有效数据，结论不可靠

### evidence (list[str])
支撑结论的具体事实或数据点：
```json
["PE ratio 35.2 低于行业均值 42.1", "连续4个季度营收增长超15%"]
```

### reasoning (str)
从 evidence 到 conclusion 的推理过程，2-5 句话。

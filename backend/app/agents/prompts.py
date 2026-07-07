"""
各专业 Agent 的 Prompt 构建函数。

每个函数将原始数据（行情、财报、新闻等）格式化为 LLM 可理解的 prompt。
统一遵循 [ROLE]-[CONTEXT]-[TASK]-[OUTPUT FORMAT]-[CONSTRAINTS] 结构，
这是经过测试的 prompt 工程模板，确保 LLM 返回结构化 JSON。
"""

import json


def build_news_prompt(stock_code: str, stock_name: str, news_data: list, market_data: dict = None) -> str:
    """构建新闻分析 prompt：输入新闻列表 + 行情，输出情感分析 JSON。"""
    news_text = "\n".join(
        f"- [{n.get('source', '')}] {n.get('title', '')}: {n.get('content', '')[:200]}"
        for n in news_data[:10]
    ) if news_data else "No news data available."

    return f"""[ROLE]
You are a senior financial news analyst specializing in Chinese A-share market sentiment analysis.

[CONTEXT]
Stock: {stock_code} ({stock_name})
Recent News:
{news_text}

Market Data: {json.dumps(market_data or {}, ensure_ascii=False)[:500]}

[TASK]
Analyze the news and provide:
1. Overall sentiment (bullish/bearish/neutral)
2. Sentiment score (-1.0 to 1.0)
3. Key events with impact assessment
4. Risk factors identified
5. Key quotes or data points

[OUTPUT FORMAT]
```json
{{
  "sentiment": "bullish|bearish|neutral",
  "sentiment_score": 0.5,
  "events": [{{"event": "...", "impact": "positive|negative|neutral", "significance": "high|medium|low"}}],
  "risk_factors": ["..."],
  "key_quotes": ["..."],
  "summary": "..."
}}
```

[CONSTRAINTS]
- Only reference actual news provided
- Cite specific news titles as sources
- Respond summary in Chinese, JSON keys in English"""


def build_financial_prompt(stock_code: str, stock_name: str, financial_data: dict, market_data: dict = None) -> str:
    """构建基本面分析 prompt：输入财务指标 + 估值数据，输出盈利能力/成长性/估值/健康度 JSON。"""
    metrics = financial_data.get("metrics", {})
    valuation = financial_data.get("valuation", {})

    return f"""[ROLE]
You are a senior equity research analyst with expertise in fundamental analysis of Chinese stocks.

[CONTEXT]
Stock: {stock_code} ({stock_name})
Financial Metrics: {json.dumps(metrics, ensure_ascii=False)}
Valuation: {json.dumps(valuation, ensure_ascii=False)}
Market: {json.dumps(market_data or {}, ensure_ascii=False)[:500]}

[TASK]
Perform fundamental analysis:
1. Profitability (ROE, margins, earnings quality)
2. Growth analysis (revenue growth, earnings growth)
3. Valuation assessment (PE, PB relative to sector)
4. Balance sheet health (debt levels, liquidity)
5. Investment thesis (bull/bear case)

[OUTPUT FORMAT]
```json
{{
  "profitability": {{"roe": 15.2, "rating": "good", "analysis": "..."}},
  "growth": {{"rating": "moderate", "analysis": "..."}},
  "valuation": {{"pe": 20, "pb": 2.5, "rating": "fair", "analysis": "..."}},
  "health": {{"rating": "strong", "analysis": "..."}},
  "thesis": {{"bull_case": "...", "bear_case": "..."}},
  "summary": "..."
}}
```

[CONSTRAINTS]
- Use actual numbers from data
- Compare to industry averages where possible
- Summary in Chinese"""


def build_technical_prompt(stock_code: str, stock_name: str, price_history: list, indicators: dict) -> str:
    """构建技术分析 prompt：输入K线 + 技术指标，输出趋势/支撑位/交易信号 JSON。"""
    recent = price_history[-5:] if price_history else []
    return f"""[ROLE]
You are a professional technical analyst specializing in Chinese A-share market.

[CONTEXT]
Stock: {stock_code} ({stock_name})
Recent Prices (last 5 days): {json.dumps(recent, ensure_ascii=False)}
Technical Indicators: {json.dumps(indicators, ensure_ascii=False)[:2000]}

[TASK]
Perform technical analysis:
1. Trend direction (short/medium/long-term)
2. Support and resistance levels
3. Momentum analysis (RSI, MACD interpretation)
4. Volume analysis
5. Trading signal with entry/stop-loss/target

[OUTPUT FORMAT]
```json
{{
  "trend": {{"short": "bullish|bearish|neutral", "medium": "...", "long": "..."}},
  "support_levels": [100.0, 95.0],
  "resistance_levels": [110.0, 115.0],
  "momentum": {{"rsi_signal": "overbought|oversold|normal", "macd_signal": "bullish|bearish", "analysis": "..."}},
  "volume": {{"trend": "increasing|decreasing|stable", "analysis": "..."}},
  "signal": {{"action": "buy|sell|hold", "entry": 105.0, "stop_loss": 98.0, "target": 115.0, "confidence": 0.7}},
  "summary": "..."
}}
```

[CONSTRAINTS]
- Reference specific indicator values
- Support/resistance from actual price data
- Summary in Chinese"""


def build_macro_prompt(stock_code: str, stock_name: str, market_data: dict) -> str:
    """构建宏观分析 prompt：输入市场数据，输出市场情绪/政策环境/流动性 JSON。"""
    return f"""[ROLE]
You are a macro-economic analyst covering the Chinese market.

[CONTEXT]
Stock: {stock_code} ({stock_name})
Market Data: {json.dumps(market_data, ensure_ascii=False)[:2000]}

[TASK]
Assess macro environment impact on this stock:
1. Overall market sentiment
2. Industry/sector outlook
3. Policy environment
4. Liquidity conditions
5. Macro risk factors

[OUTPUT FORMAT]
```json
{{
  "market_sentiment": "bullish|bearish|neutral",
  "sector_outlook": "positive|negative|neutral",
  "policy_impact": {{"rating": "supportive|neutral|restrictive", "analysis": "..."}},
  "liquidity": "abundant|normal|tight",
  "macro_risks": ["..."],
  "summary": "..."
}}
```

[CONSTRAINTS]
- Focus on China-specific factors
- Summary in Chinese"""


def build_risk_prompt(stock_code: str, stock_name: str, agent_outputs: dict) -> str:
    """构建风险评估 prompt：输入所有 agent 分析结果，综合输出风险等级/风险因子/仓位建议 JSON。"""
    return f"""[ROLE]
You are a senior risk management analyst.

[CONTEXT]
Stock: {stock_code} ({stock_name})
Agent Analysis Results: {json.dumps(agent_outputs, ensure_ascii=False)[:3000]}

[TASK]
Based on all agent analyses, assess overall risk:
1. Overall risk level (low/medium/high/very_high)
2. Risk score (0-100, higher = riskier)
3. Categorized risk factors (market/company/valuation/liquidity)
4. Worst-case scenario
5. Position sizing recommendation

[OUTPUT FORMAT]
```json
{{
  "overall_risk": "low|medium|high|very_high",
  "risk_score": 45,
  "risk_factors": {{
    "market": ["..."],
    "company": ["..."],
    "valuation": ["..."],
    "liquidity": ["..."]
  }},
  "worst_case": "...",
  "position_sizing": {{"max_pct": 5, "recommendation": "..."}},
  "summary": "..."
}}
```

[CONSTRAINTS]
- Risk score must reflect actual analysis signals
- Summary in Chinese"""


def build_quant_prompt(stock_code: str, stock_name: str, agent_outputs: dict) -> str:
    """构建量化评分 prompt：输入所有分析结果，输出多因子评分（估值/成长/质量/动量/情绪）JSON。"""
    return f"""[ROLE]
You are a quantitative analyst specializing in multi-factor scoring models.

[CONTEXT]
Stock: {stock_code} ({stock_name})
Agent Analysis Results: {json.dumps(agent_outputs, ensure_ascii=False)[:3000]}

[TASK]
Create a quantitative score based on multiple factors:
1. Valuation factor (PE, PB)
2. Growth factor (revenue, earnings)
3. Quality factor (ROE, margins)
4. Momentum factor (price trend)
5. Sentiment factor (news, market)
6. Composite score (0-100)

[OUTPUT FORMAT]
```json
{{
  "factors": {{
    "valuation": {{"score": 75, "weight": 0.25, "detail": "..."}},
    "growth": {{"score": 60, "weight": 0.20, "detail": "..."}},
    "quality": {{"score": 80, "weight": 0.20, "detail": "..."}},
    "momentum": {{"score": 65, "weight": 0.20, "detail": "..."}},
    "sentiment": {{"score": 70, "weight": 0.15, "detail": "..."}}
  }},
  "composite_score": 70,
  "rating": "buy|hold|sell",
  "summary": "..."
}}
```

[CONSTRAINTS]
- Each factor score 0-100
- Weights must sum to 1.0
- Summary in Chinese"""


def build_report_prompt(stock_code: str, stock_name: str, agent_outputs: dict, risk_assessment: dict, quant_score: dict) -> str:
    """构建最终报告 prompt：综合所有分析结果，输出投资建议/目标价/核心发现/综合评分 JSON。"""
    return f"""[ROLE]
You are the chief investment strategist producing the final investment report.

[CONTEXT]
Stock: {stock_code} ({stock_name})
All Agent Analyses: {json.dumps(agent_outputs, ensure_ascii=False)[:3000]}
Risk Assessment: {json.dumps(risk_assessment, ensure_ascii=False)[:1000]}
Quant Score: {json.dumps(quant_score, ensure_ascii=False)[:1000]}

[TASK]
Synthesize all analyses into a comprehensive investment report:
1. Executive summary (3-5 sentences)
2. Investment recommendation (strong_buy/buy/hold/sell/strong_sell)
3. Target price range
4. Key findings (top 5)
5. Risk-reward assessment
6. Action items for the investor
7. Disclaimer

[OUTPUT FORMAT]
```json
{{
  "executive_summary": "...",
  "recommendation": "buy|hold|sell",
  "target_price": {{"low": 100, "high": 120}},
  "key_findings": ["finding1", "finding2", ...],
  "risk_reward": {{"risk": "...", "reward": "...", "ratio": "favorable|neutral|unfavorable"}},
  "action_items": ["..."],
  "disclaimer": "...",
  "overall_score": 75
}}
```

[CONSTRAINTS]
- Must reference specific findings from each agent
- Recommendation must align with risk and quant scores
- All text in Chinese except JSON keys"""

"""
Structured prompts for each specialist agent.

Every prompt is a Jinja2-style template (using Python's ``str.format`` or
``Template``) that is filled in at runtime with the ticker, current date, and
any additional context.  Each prompt instructs the LLM to return a JSON object
that matches the corresponding Pydantic schema in ``schemas.py``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Shared preamble inserted into every agent prompt
# ---------------------------------------------------------------------------
_SYSTEM_PREAMBLE = """You are a world-class financial analyst AI. You must
respond ONLY with a valid JSON object that matches the schema described below.
Do not include any text before or after the JSON. Use null for any field where
you lack sufficient data to provide a value. Always include a "confidence"
field (0.0 to 1.0) reflecting how confident you are in your analysis.
"""


def _format_system() -> str:
    return _SYSTEM_PREAMBLE.strip()


# ---------------------------------------------------------------------------
# News Agent Prompt
# ---------------------------------------------------------------------------

NEWS_PROMPT_TEMPLATE = """Analyze the recent news sentiment for {ticker} as of {date}.

TASK: Evaluate all available news articles, press releases, and social media
discussions about {ticker} to produce a comprehensive sentiment analysis.

INSTRUCTIONS:
1. Assess the overall sentiment (very_positive, positive, neutral, negative, very_negative).
2. Assign a numeric sentiment_score from -1.0 (extremely negative) to +1.0 (extremely positive).
3. Identify the 3-5 most impactful recent news events.
4. For each news item, provide: headline, source, sentiment, relevance_score (0-1), and a brief summary.
5. Determine whether the news flow trend is improving (bullish), stable (neutral), or deteriorating (bearish).
6. Include citations for all news sources used.

OUTPUT SCHEMA (respond with JSON matching this structure):
{{
  "ticker": "string",
  "agent_name": "news_agent",
  "confidence": 0.0-1.0,
  "summary": "string (max 500 chars)",
  "citations": [{{"source": "string", "title": "string", "date": "string|null", "snippet": "string|null"}}],
  "sentiment_label": "very_positive|positive|neutral|negative|very_negative",
  "sentiment_score": -1.0 to 1.0,
  "key_events": ["string"],
  "news_items": [{{
    "headline": "string",
    "source": "string",
    "date": "string|null",
    "sentiment": "very_positive|positive|neutral|negative|very_negative",
    "relevance_score": 0.0-1.0,
    "summary": "string|null"
  }}],
  "trend": "bullish|slightly_bullish|neutral|slightly_bearish|bearish",
  "errors": []
}}

EXTRA CONTEXT:
{extra_context}
"""


def build_news_prompt(
    ticker: str,
    date: str | None = None,
    extra_context: str = "",
) -> str:
    return NEWS_PROMPT_TEMPLATE.format(
        ticker=ticker,
        date=date or datetime.utcnow().strftime("%Y-%m-%d"),
        extra_context=extra_context or "None provided.",
    )


# ---------------------------------------------------------------------------
# Financial Agent Prompt
# ---------------------------------------------------------------------------

FINANCIAL_PROMPT_TEMPLATE = """Perform a comprehensive fundamental analysis of {ticker} as of {date}.

TASK: Evaluate the company's financial health, valuation, quality, and growth
prospects using the most recent available financial data.

INSTRUCTIONS:
1. Analyze key financial metrics: P/E, P/S, P/B, EV/EBITDA, ROE, ROIC,
   debt-to-equity, free cash flow yield, revenue growth, EPS growth, margins.
2. For each metric, compare against the sector average and provide a percentile rank.
3. Assign composite scores (0-100) for: valuation, quality, and growth.
4. Identify 3-5 financial strengths and 3-5 weaknesses.
5. Estimate a fair value per share using DCF or comparable analysis.
6. Include citations for all data sources.

OUTPUT SCHEMA (respond with JSON matching this structure):
{{
  "ticker": "string",
  "agent_name": "financial_agent",
  "confidence": 0.0-1.0,
  "summary": "string (max 500 chars)",
  "citations": [{{"source": "string", "title": "string", "date": "string|null", "snippet": "string|null"}}],
  "valuation_score": 0.0-100.0,
  "quality_score": 0.0-100.0,
  "growth_score": 0.0-100.0,
  "key_metrics": [{{
    "name": "string",
    "value": number|null,
    "sector_avg": number|null,
    "percentile": 0.0-100.0|null,
    "assessment": "string"
  }}],
  "strengths": ["string"],
  "weaknesses": ["string"],
  "fair_value_estimate": number|null,
  "errors": []
}}

EXTRA CONTEXT:
{extra_context}
"""


def build_financial_prompt(
    ticker: str,
    date: str | None = None,
    extra_context: str = "",
) -> str:
    return FINANCIAL_PROMPT_TEMPLATE.format(
        ticker=ticker,
        date=date or datetime.utcnow().strftime("%Y-%m-%d"),
        extra_context=extra_context or "None provided.",
    )


# ---------------------------------------------------------------------------
# Technical Agent Prompt
# ---------------------------------------------------------------------------

TECHNICAL_PROMPT_TEMPLATE = """Perform a comprehensive technical analysis of {ticker} as of {date}.

TASK: Analyze price action, chart patterns, and technical indicators to
determine the current technical outlook and provide actionable entry/exit levels.

INSTRUCTIONS:
1. Evaluate at least 6 technical indicators: RSI, MACD, Moving Averages (SMA 20/50/200),
   Bollinger Bands, VWAT, ATR, OBV, Stochastic, or others relevant to the stock.
2. Detect any significant chart patterns (e.g., head and shoulders, double top/bottom,
   ascending/descending triangle, cup and handle, flags).
3. Identify key support and resistance levels (at least 2 of each).
4. Determine overall signal direction and signal strength.
5. Suggest entry price, stop-loss, and take-profit levels.
6. Include reasoning and citations for all indicators.

OUTPUT SCHEMA (respond with JSON matching this structure):
{{
  "ticker": "string",
  "agent_name": "technical_agent",
  "confidence": 0.0-1.0,
  "summary": "string (max 500 chars)",
  "citations": [{{"source": "string", "title": "string", "date": "string|null", "snippet": "string|null"}}],
  "overall_signal": "bullish|slightly_bullish|neutral|slightly_bearish|bearish",
  "signal_strength": "strong|moderate|weak|conflicting",
  "current_price": number|null,
  "support_levels": [number],
  "resistance_levels": [number],
  "indicators": [{{
    "name": "string",
    "value": number|null,
    "signal": "bullish|slightly_bullish|neutral|slightly_bearish|bearish",
    "explanation": "string"
  }}],
  "patterns": [{{
    "name": "string",
    "timeframe": "string",
    "direction": "bullish|slightly_bullish|neutral|slightly_bearish|bearish",
    "reliability": 0.0-1.0,
    "target_price": number|null
  }}],
  "suggested_entry": number|null,
  "suggested_stop_loss": number|null,
  "suggested_take_profit": number|null,
  "errors": []
}}

EXTRA CONTEXT:
{extra_context}
"""


def build_technical_prompt(
    ticker: str,
    date: str | None = None,
    extra_context: str = "",
) -> str:
    return TECHNICAL_PROMPT_TEMPLATE.format(
        ticker=ticker,
        date=date or datetime.utcnow().strftime("%Y-%m-%d"),
        extra_context=extra_context or "None provided.",
    )


# ---------------------------------------------------------------------------
# Risk Agent Prompt
# ---------------------------------------------------------------------------

RISK_PROMPT_TEMPLATE = """Perform a comprehensive risk assessment for {ticker} as of {date}.

TASK: Evaluate all categories of risk — market, sector, company-specific,
geopolitical, liquidity, and regulatory — and produce a structured risk report.

INSTRUCTIONS:
1. Identify at least 5 distinct risk factors across different categories.
2. For each risk factor, assess severity (very_low to very_high) and probability (0-1).
3. Assign an overall risk_level and a risk_score (0-100, where 100 = extreme risk).
4. Assess volatility characteristics (e.g., historical vol, implied vol if available).
5. Estimate maximum drawdown probability over the next 90 days.
6. Provide beta and Sharpe ratio estimates.
7. Give position sizing advice and a recommended stop-loss level.
8. Suggest mitigations for the top risk factors.

OUTPUT SCHEMA (respond with JSON matching this structure):
{{
  "ticker": "string",
  "agent_name": "risk_agent",
  "confidence": 0.0-1.0,
  "summary": "string (max 500 chars)",
  "citations": [{{"source": "string", "title": "string", "date": "string|null", "snippet": "string|null"}}],
  "overall_risk_level": "very_low|low|moderate|high|very_high",
  "risk_score": 0.0-100.0,
  "volatility_assessment": "string",
  "max_drawdown_estimate": 0.0-1.0|null,
  "beta_estimate": number|null,
  "sharpe_ratio": number|null,
  "risk_factors": [{{
    "category": "string",
    "description": "string",
    "severity": "very_low|low|moderate|high|very_high",
    "probability": 0.0-1.0,
    "mitigation": "string|null"
  }}],
  "position_sizing_advice": "string",
  "stop_loss_recommendation": number|null,
  "errors": []
}}

EXTRA CONTEXT:
{extra_context}
"""


def build_risk_prompt(
    ticker: str,
    date: str | None = None,
    extra_context: str = "",
) -> str:
    return RISK_PROMPT_TEMPLATE.format(
        ticker=ticker,
        date=date or datetime.utcnow().strftime("%Y-%m-%d"),
        extra_context=extra_context or "None provided.",
    )


# ---------------------------------------------------------------------------
# Report Agent Prompt (synthesis)
# ---------------------------------------------------------------------------

REPORT_PROMPT_TEMPLATE = """You are the Chief Investment Officer synthesizing analyses from four
specialist agents to produce a final investment report for {ticker} as of {date}.

TASK: Combine the insights from the News, Financial, Technical, and Risk agents
into a single actionable investment recommendation.

INPUT — NEWS AGENT ANALYSIS:
{news_analysis}

INPUT — FINANCIAL AGENT ANALYSIS:
{financial_analysis}

INPUT — TECHNICAL AGENT ANALYSIS:
{technical_analysis}

INPUT — RISK AGENT ANALYSIS:
{risk_analysis}

INSTRUCTIONS:
1. Synthesize all four analyses into a unified recommendation:
   strong_buy, buy, hold, sell, or strong_sell.
2. Calculate a composite_score (0-100) using these weights:
   - News: {news_weight}%
   - Financial: {financial_weight}%
   - Technical: {technical_weight}%
   - Risk: {risk_weight}%
3. Provide conviction_level (0-1.0) reflecting how confident you are in the
   recommendation given the agreement or disagreement among agents.
4. Set price targets: bull, base, and bear case.
5. Identify key catalysts and key risks.
6. Write an actionable_summary suitable for an investor.
7. Provide a time_horizon recommendation.
8. Include individual agent contribution scores in agent_scores.

SCORING GUIDELINES:
- strong_buy: composite_score > 80, low risk, positive sentiment, undervalued
- buy: composite_score 60-80, acceptable risk/reward
- hold: composite_score 40-60, mixed signals or elevated risk
- sell: composite_score 20-40, deteriorating fundamentals or high risk
- strong_sell: composite_score < 20, significant downside risk

OUTPUT SCHEMA (respond with JSON matching this structure):
{{
  "ticker": "string",
  "agent_name": "report_agent",
  "confidence": 0.0-1.0,
  "summary": "string (max 500 chars)",
  "citations": [],
  "recommendation": "strong_buy|buy|hold|sell|strong_sell",
  "conviction_level": 0.0-1.0,
  "composite_score": 0.0-100.0,
  "price_target_bull": number|null,
  "price_target_base": number|null,
  "price_target_bear": number|null,
  "time_horizon": "string",
  "key_catalysts": ["string"],
  "key_risks": ["string"],
  "actionable_summary": "string",
  "agent_scores": {{
    "news_agent": 0.0-100.0,
    "financial_agent": 0.0-100.0,
    "technical_agent": 0.0-100.0,
    "risk_agent": 0.0-100.0
  }},
  "errors": []
}}
"""


def build_report_prompt(
    ticker: str,
    news_analysis: str,
    financial_analysis: str,
    technical_analysis: str,
    risk_analysis: str,
    weights: dict[str, float] | None = None,
    date: str | None = None,
) -> str:
    """Build the synthesis prompt, injecting all agent outputs as context."""
    w = weights or {
        "news": 0.20,
        "financial": 0.30,
        "technical": 0.25,
        "risk": 0.25,
    }
    return REPORT_PROMPT_TEMPLATE.format(
        ticker=ticker,
        date=date or datetime.utcnow().strftime("%Y-%m-%d"),
        news_analysis=news_analysis,
        financial_analysis=financial_analysis,
        technical_analysis=technical_analysis,
        risk_analysis=risk_analysis,
        news_weight=int(w["news"] * 100),
        financial_weight=int(w["financial"] * 100),
        technical_weight=int(w["technical"] * 100),
        risk_weight=int(w["risk"] * 100),
    )

"""
Pydantic schemas for structured agent outputs.

Every agent produces a validated Pydantic model that conforms to one of these
schemas.  The schemas enforce field types, value ranges, and provide JSON Schema
descriptions that can be injected into LLM prompts for reliable structured
output generation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SentimentLabel(str, Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class TrendDirection(str, Enum):
    BULLISH = "bullish"
    SLIGHTLY_BULLISH = "slightly_bullish"
    NEUTRAL = "neutral"
    SLIGHTLY_BEARISH = "slightly_bearish"
    BEARISH = "bearish"


class RiskLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Recommendation(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class SignalStrength(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    CONFLICTING = "conflicting"


# ---------------------------------------------------------------------------
# Shared base models
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    """A reference to an external source used by an agent."""

    source: str = Field(description="Name or URL of the source")
    title: str = Field(description="Title of the referenced material")
    date: Optional[str] = Field(None, description="Publication date (ISO 8601)")
    snippet: Optional[str] = Field(None, description="Relevant excerpt")

    class Config:
        frozen = True


class BaseAgentOutput(BaseModel):
    """Fields common to every agent output."""

    ticker: str = Field(description="Stock ticker symbol, e.g. AAPL")
    agent_name: str = Field(description="Name of the producing agent")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Agent's confidence in its own analysis (0-1)",
    )
    summary: str = Field(
        max_length=500,
        description="One-paragraph executive summary of this agent's findings",
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Sources referenced during analysis",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the analysis was produced",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Non-fatal errors or warnings encountered during analysis",
    )

    class Config:
        use_enum_values = True


# ---------------------------------------------------------------------------
# News Agent
# ---------------------------------------------------------------------------

class NewsItem(BaseModel):
    """A single news article or headline."""

    headline: str
    source: str
    date: Optional[str] = None
    sentiment: SentimentLabel
    relevance_score: float = Field(ge=0.0, le=1.0)
    summary: Optional[str] = None


class NewsAgentOutput(BaseAgentOutput):
    """Structured output from the News Sentiment Agent."""

    sentiment_label: SentimentLabel = Field(
        description="Aggregate sentiment across all articles",
    )
    sentiment_score: float = Field(
        ge=-1.0, le=1.0,
        description="Numeric sentiment from -1 (very negative) to +1 (very positive)",
    )
    key_events: list[str] = Field(
        default_factory=list,
        description="Major news events that could move the stock",
    )
    news_items: list[NewsItem] = Field(
        default_factory=list,
        max_length=20,
        description="Individual news items analyzed",
    )
    trend: TrendDirection = Field(
        description="Whether the news flow is improving or deteriorating",
    )

    @field_validator("agent_name")
    @classmethod
    def _set_agent_name(cls, v: str) -> str:
        return "news_agent"


# ---------------------------------------------------------------------------
# Financial Agent
# ---------------------------------------------------------------------------

class FinancialMetric(BaseModel):
    """A single financial metric with context."""

    name: str = Field(description="Metric name, e.g. P/E Ratio")
    value: Optional[float] = Field(None, description="Current value")
    sector_avg: Optional[float] = Field(None, description="Sector average for comparison")
    percentile: Optional[float] = Field(
        None, ge=0.0, le=100.0,
        description="Percentile rank within the sector",
    )
    assessment: str = Field(description="Brief qualitative assessment")


class FinancialAgentOutput(BaseAgentOutput):
    """Structured output from the Financial (Fundamental) Agent."""

    valuation_score: float = Field(
        ge=0.0, le=100.0,
        description="Composite valuation score (0 = extremely overvalued, 100 = deeply undervalued)",
    )
    quality_score: float = Field(
        ge=0.0, le=100.0,
        description="Business quality score based on profitability, moat, etc.",
    )
    growth_score: float = Field(
        ge=0.0, le=100.0,
        description="Growth prospects score",
    )
    key_metrics: list[FinancialMetric] = Field(
        default_factory=list,
        description="Key financial metrics with context",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Financial strengths identified",
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="Financial weaknesses or red flags",
    )
    fair_value_estimate: Optional[float] = Field(
        None, ge=0.0,
        description="Estimated fair value per share",
    )

    @field_validator("agent_name")
    @classmethod
    def _set_agent_name(cls, v: str) -> str:
        return "financial_agent"


# ---------------------------------------------------------------------------
# Technical Agent
# ---------------------------------------------------------------------------

class TechnicalIndicator(BaseModel):
    """A single technical indicator reading."""

    name: str = Field(description="Indicator name, e.g. RSI, MACD, Bollinger Bands")
    value: Optional[float] = None
    signal: TrendDirection
    explanation: str


class ChartPattern(BaseModel):
    """A detected chart pattern."""

    name: str = Field(description="Pattern name, e.g. Head and Shoulders")
    timeframe: str = Field(description="Timeframe where detected (daily, weekly, etc.)")
    direction: TrendDirection
    reliability: float = Field(ge=0.0, le=1.0)
    target_price: Optional[float] = None


class TechnicalAgentOutput(BaseAgentOutput):
    """Structured output from the Technical Analysis Agent."""

    overall_signal: TrendDirection
    signal_strength: SignalStrength
    current_price: Optional[float] = None
    support_levels: list[float] = Field(default_factory=list)
    resistance_levels: list[float] = Field(default_factory=list)
    indicators: list[TechnicalIndicator] = Field(default_factory=list)
    patterns: list[ChartPattern] = Field(default_factory=list)
    suggested_entry: Optional[float] = Field(
        None, description="Suggested entry price for a long position",
    )
    suggested_stop_loss: Optional[float] = Field(
        None, description="Suggested stop-loss price",
    )
    suggested_take_profit: Optional[float] = Field(
        None, description="Suggested take-profit target",
    )

    @field_validator("agent_name")
    @classmethod
    def _set_agent_name(cls, v: str) -> str:
        return "technical_agent"


# ---------------------------------------------------------------------------
# Risk Agent
# ---------------------------------------------------------------------------

class RiskFactor(BaseModel):
    """A single identified risk factor."""

    category: str = Field(
        description="Risk category: market, sector, company, geopolitical, liquidity, etc.",
    )
    description: str
    severity: RiskLevel
    probability: float = Field(ge=0.0, le=1.0)
    mitigation: Optional[str] = None


class RiskAgentOutput(BaseAgentOutput):
    """Structured output from the Risk Assessment Agent."""

    overall_risk_level: RiskLevel
    risk_score: float = Field(
        ge=0.0, le=100.0,
        description="Composite risk score (0 = minimal risk, 100 = extreme risk)",
    )
    volatility_assessment: str = Field(
        description="Assessment of price volatility characteristics",
    )
    max_drawdown_estimate: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Estimated maximum drawdown probability in next 90 days",
    )
    beta_estimate: Optional[float] = Field(None, description="Estimated beta vs. market")
    sharpe_ratio: Optional[float] = Field(None, description="Recent Sharpe ratio")
    risk_factors: list[RiskFactor] = Field(default_factory=list)
    position_sizing_advice: str = Field(
        description="Recommended position sizing guidance",
    )
    stop_loss_recommendation: Optional[float] = Field(
        None, description="Recommended stop-loss price",
    )

    @field_validator("agent_name")
    @classmethod
    def _set_agent_name(cls, v: str) -> str:
        return "risk_agent"


# ---------------------------------------------------------------------------
# Report Agent (synthesis)
# ---------------------------------------------------------------------------

class InvestmentReport(BaseAgentOutput):
    """Final synthesized investment report."""

    recommendation: Recommendation
    conviction_level: float = Field(
        ge=0.0, le=1.0,
        description="How strongly the system believes in this recommendation",
    )
    composite_score: float = Field(
        ge=0.0, le=100.0,
        description="Weighted composite score from all agents",
    )
    price_target_bull: Optional[float] = Field(
        None, description="Bull-case price target",
    )
    price_target_base: Optional[float] = Field(
        None, description="Base-case price target",
    )
    price_target_bear: Optional[float] = Field(
        None, description="Bear-case price target",
    )
    time_horizon: str = Field(
        description="Recommended holding period, e.g. '3-6 months'",
    )
    key_catalysts: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    actionable_summary: str = Field(
        description="One-paragraph actionable summary for the investor",
    )
    agent_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Individual agent contribution scores (agent_name -> score)",
    )

    @field_validator("agent_name")
    @classmethod
    def _set_agent_name(cls, v: str) -> str:
        return "report_agent"

    @model_validator(mode="after")
    def _validate_price_targets(self) -> "InvestmentReport":
        """Ensure bull >= base >= bear when all targets are present."""
        targets = [
            self.price_target_bull,
            self.price_target_base,
            self.price_target_bear,
        ]
        if all(t is not None for t in targets):
            if not (
                self.price_target_bull >= self.price_target_base >= self.price_target_bear  # type: ignore[union-attr]
            ):
                raise ValueError(
                    "Price targets must satisfy: bull >= base >= bear"
                )
        return self

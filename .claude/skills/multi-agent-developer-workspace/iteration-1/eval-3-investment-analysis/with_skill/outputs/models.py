"""
Investment Analysis System - Data Models and State Management

Defines all Pydantic models, TypedDict state schemas, enums,
and output validation for the multi-agent investment analysis pipeline.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional

import operator
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class WorkflowPhase(str, Enum):
    """Phases of the investment analysis workflow."""
    INIT = "init"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    RISK_ASSESSING = "risk_assessing"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    FAILED = "failed"


class Sentiment(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class TrendDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Recommendation(str, Enum):
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"


# ---------------------------------------------------------------------------
# Agent Output (shared across all agents)
# ---------------------------------------------------------------------------

class AgentOutput(BaseModel):
    """Standard output envelope for every agent in the system."""
    agent_name: str
    result: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    citations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = "success"
    error: Optional[str] = None

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


# ---------------------------------------------------------------------------
# Per-agent output models (structured JSON schemas)
# ---------------------------------------------------------------------------

class NewsEvent(BaseModel):
    title: str
    impact: str  # positive | negative | neutral
    affected_stocks: List[str] = Field(default_factory=list)
    summary: str = ""
    source: str = ""
    published_at: Optional[str] = None


class NewsAnalysis(BaseModel):
    sentiment: Sentiment
    sentiment_score: float = Field(ge=0.0, le=1.0)
    events: List[NewsEvent] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    key_quotes: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    confidence: float = 0.5


class ProfitabilityMetrics(BaseModel):
    roe: Optional[float] = None
    roa: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None


class GrowthMetrics(BaseModel):
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    growth_trend: Optional[str] = None  # accelerating | stable | decelerating


class ValuationMetrics(BaseModel):
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    assessment: Optional[str] = None  # undervalued | fairly_valued | overvalued


class HealthMetrics(BaseModel):
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    health_score: Optional[int] = None


class FinancialAnalysis(BaseModel):
    profitability: ProfitabilityMetrics = Field(default_factory=ProfitabilityMetrics)
    growth: GrowthMetrics = Field(default_factory=GrowthMetrics)
    valuation: ValuationMetrics = Field(default_factory=ValuationMetrics)
    health: HealthMetrics = Field(default_factory=HealthMetrics)
    thesis: str = ""
    citations: List[str] = Field(default_factory=list)
    confidence: float = 0.5


class TrendAnalysis(BaseModel):
    short_term: TrendDirection = TrendDirection.NEUTRAL
    medium_term: TrendDirection = TrendDirection.NEUTRAL
    long_term: TrendDirection = TrendDirection.NEUTRAL


class PriceLevels(BaseModel):
    support: List[float] = Field(default_factory=list)
    resistance: List[float] = Field(default_factory=list)


class IndicatorData(BaseModel):
    rsi: Optional[float] = None
    rsi_signal: Optional[str] = None  # overbought | oversold | neutral
    macd: Optional[str] = None  # bullish_crossover | bearish_crossover | neutral
    macd_histogram: Optional[float] = None


class VolumeAnalysis(BaseModel):
    trend: Optional[str] = None  # increasing | decreasing | stable
    relative_volume: Optional[float] = None
    analysis: str = ""


class TradingSignal(BaseModel):
    action: Recommendation = Recommendation.HOLD
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    risk_reward_ratio: Optional[float] = None


class TechnicalAnalysis(BaseModel):
    trend: TrendAnalysis = Field(default_factory=TrendAnalysis)
    levels: PriceLevels = Field(default_factory=PriceLevels)
    indicators: IndicatorData = Field(default_factory=IndicatorData)
    volume: VolumeAnalysis = Field(default_factory=VolumeAnalysis)
    patterns: List[str] = Field(default_factory=list)
    signals: TradingSignal = Field(default_factory=TradingSignal)
    citations: List[str] = Field(default_factory=list)
    confidence: float = 0.5


class RiskCategory(BaseModel):
    level: RiskLevel = RiskLevel.MEDIUM
    factors: List[str] = Field(default_factory=list)


class WorstCaseScenario(BaseModel):
    scenario: str = ""
    potential_loss: float = 0.0
    probability: float = 0.0


class PositionSizing(BaseModel):
    conservative: float = 0.03
    moderate: float = 0.05
    aggressive: float = 0.08


class RiskAssessment(BaseModel):
    overall_risk: RiskLevel = RiskLevel.MEDIUM
    risk_score: int = Field(ge=0, le=100, default=50)
    risk_factors: Dict[str, RiskCategory] = Field(default_factory=dict)
    worst_case: WorstCaseScenario = Field(default_factory=WorstCaseScenario)
    mitigation: List[str] = Field(default_factory=list)
    position_sizing: PositionSizing = Field(default_factory=PositionSizing)
    citations: List[str] = Field(default_factory=list)
    confidence: float = 0.5


class PriceTarget(BaseModel):
    target: Optional[float] = None
    time_horizon: str = "12 months"
    upside: Optional[float] = None


class RiskReward(BaseModel):
    risk_score: int = 50
    reward_potential: float = 0.0
    risk_reward_ratio: float = 0.0


class FinalReport(BaseModel):
    executive_summary: str = ""
    recommendation: Recommendation = Recommendation.HOLD
    confidence: float = 0.5
    price_target: PriceTarget = Field(default_factory=PriceTarget)
    key_findings: Dict[str, str] = Field(default_factory=dict)
    risk_reward: RiskReward = Field(default_factory=RiskReward)
    action_items: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    disclaimer: str = "This is AI-generated analysis, not financial advice."


# ---------------------------------------------------------------------------
# LangGraph Workflow State (TypedDict with reducers for parallel updates)
# ---------------------------------------------------------------------------

class InvestmentState(BaseModel):
    """
    Workflow state for the investment analysis pipeline.

    Uses Pydantic for validation but is converted to dict for LangGraph.
    Parallel-safe fields use Annotated[list, operator.add] in the
    TypedDict version below.
    """

    # --- Identifiers ---
    task_id: str
    stock_code: str = Field(pattern=r"^[A-Z]{1,6}$")
    stock_name: str = ""
    user_id: str = ""

    # --- Workflow tracking ---
    phase: str = WorkflowPhase.INIT.value
    version: int = 1
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # --- Input data ---
    query: str = ""
    market_data: Dict[str, Any] = Field(default_factory=dict)
    news_data: List[Dict[str, Any]] = Field(default_factory=list)
    financial_data: Dict[str, Any] = Field(default_factory=dict)
    price_history: List[Dict[str, Any]] = Field(default_factory=list)

    # --- Agent outputs (stored as AgentOutput dicts) ---
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)

    # --- Synthesis results ---
    risk_assessment: Optional[Dict[str, Any]] = None
    final_report: Optional[Dict[str, Any]] = None

    # --- Error tracking ---
    errors: List[str] = Field(default_factory=list)

    # --- User preferences ---
    time_horizon: str = "12 months"
    risk_tolerance: str = "moderate"


def create_initial_state(
    task_id: str,
    stock_code: str,
    stock_name: str = "",
    query: str = "",
    user_id: str = "",
    market_data: Optional[Dict] = None,
    news_data: Optional[List] = None,
    financial_data: Optional[Dict] = None,
    price_history: Optional[List] = None,
    time_horizon: str = "12 months",
    risk_tolerance: str = "moderate",
) -> dict:
    """Create initial state dict for workflow invocation."""
    now = datetime.now().isoformat()
    return {
        "task_id": task_id,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "user_id": user_id,
        "phase": WorkflowPhase.INIT.value,
        "version": 1,
        "started_at": now,
        "updated_at": now,
        "query": query,
        "market_data": market_data or {},
        "news_data": news_data or [],
        "financial_data": financial_data or {},
        "price_history": price_history or [],
        "agent_outputs": {},
        "risk_assessment": None,
        "final_report": None,
        "errors": [],
        "time_horizon": time_horizon,
        "risk_tolerance": risk_tolerance,
    }

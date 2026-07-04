"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class PortfolioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    holdings: Dict[str, float] = Field(default_factory=dict)
    candidate_pool: List[str] = Field(default_factory=list)


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    id: str
    user_id: str
    risk_score: float = 0.0
    expected_return: float = 0.0
    sector_exposure: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StockAnalysisRequest(BaseModel):
    stock_code: str = Field(..., pattern=r"^\d{6}$")


class StockAnalysisResponse(BaseModel):
    stock_code: str
    status: str
    analysis: Optional[Dict] = None


class AgentOutput(BaseModel):
    output: Dict
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(..., min_length=1)
    reasoning: str = Field(..., min_length=10)


class StandardResponse(BaseModel):
    status: str = "success"
    data: Optional[Dict] = None
    error: Optional[str] = None

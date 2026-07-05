"""Portfolio service — CRUD, AI weight recommendation, risk scoring."""
import json
import uuid
import logging
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.stock import StockState

logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, name: str, holdings: dict = None) -> Portfolio:
        portfolio = Portfolio(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            holdings=json.dumps(holdings or {}),
            candidate_pool="[]",
            sector_exposure="{}",
        )
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def get(self, portfolio_id: str) -> Optional[Portfolio]:
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    def list_by_user(self, user_id: str) -> list[Portfolio]:
        return self.db.query(Portfolio).filter(Portfolio.user_id == user_id).all()

    def update_holdings(self, portfolio_id: str, holdings: dict) -> Optional[Portfolio]:
        p = self.get(portfolio_id)
        if not p:
            return None
        p.holdings = json.dumps(holdings)
        p.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(p)
        return p

    def delete(self, portfolio_id: str) -> bool:
        p = self.get(portfolio_id)
        if not p:
            return False
        self.db.delete(p)
        self.db.commit()
        return True

    # --- Candidate Pool ---

    def add_to_pool(self, portfolio_id: str, stock_code: str) -> Optional[Portfolio]:
        p = self.get(portfolio_id)
        if not p:
            return None
        pool = json.loads(p.candidate_pool or "[]")
        if stock_code not in pool:
            pool.append(stock_code)
            p.candidate_pool = json.dumps(pool)
            p.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(p)
        return p

    def remove_from_pool(self, portfolio_id: str, stock_code: str) -> Optional[Portfolio]:
        p = self.get(portfolio_id)
        if not p:
            return None
        pool = json.loads(p.candidate_pool or "[]")
        pool = [s for s in pool if s != stock_code]
        p.candidate_pool = json.dumps(pool)
        p.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(p)
        return p

    # --- AI Weight Recommendation ---

    def suggest_weights(self, portfolio_id: str, agent_outputs: dict = None) -> dict:
        p = self.get(portfolio_id)
        if not p:
            return {"error": "portfolio not found"}

        pool = json.loads(p.candidate_pool or "[]")
        holdings = json.loads(p.holdings or "{}")

        if not pool and not holdings:
            return {"weights": {}, "reason": "empty portfolio and candidate pool"}

        stocks = list(set(list(holdings.keys()) + pool))
        scores = {}

        for stock in stocks:
            state = self.db.query(StockState).filter(StockState.stock_code == stock).first()
            if state:
                scores[stock] = state.score
            else:
                scores[stock] = 50.0

        total_score = sum(scores.values()) or 1
        weights = {s: round(sc / total_score, 4) for s, sc in scores.items()}

        p.holdings = json.dumps(weights)
        p.expected_return = sum(scores.values()) / max(len(scores), 1) / 100
        p.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        return {"weights": weights, "scores": scores}

    # --- Risk Scoring ---

    def calc_risk_score(self, portfolio_id: str) -> dict:
        p = self.get(portfolio_id)
        if not p:
            return {"error": "portfolio not found"}

        holdings = json.loads(p.holdings or "{}")
        if not holdings:
            return {"risk_score": 0, "risk_level": "LOW", "details": {}}

        sectors = {}
        max_weight = 0
        for stock, weight in holdings.items():
            max_weight = max(max_weight, weight)
            state = self.db.query(StockState).filter(StockState.stock_code == stock).first()
            sector = state.sector if state else "unknown"
            sectors[sector] = sectors.get(sector, 0) + weight

        max_sector = max(sectors.values()) if sectors else 0

        risk_score = 0.0
        risk_factors = []

        if max_weight > 0.3:
            risk_score += 30
            risk_factors.append(f"Single stock concentration: {max_weight:.1%}")
        elif max_weight > 0.2:
            risk_score += 15
            risk_factors.append(f"Moderate single stock: {max_weight:.1%}")

        if max_sector > 0.5:
            risk_score += 25
            risk_factors.append(f"Sector concentration: {max_sector:.1%}")
        elif max_sector > 0.3:
            risk_score += 10

        if len(holdings) < 3:
            risk_score += 15
            risk_factors.append(f"Low diversification: {len(holdings)} stocks")

        risk_score = min(100, risk_score)

        if risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        p.risk_score = risk_score
        p.sector_exposure = json.dumps(sectors)
        p.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "sector_exposure": sectors,
            "max_single_weight": max_weight,
            "risk_factors": risk_factors,
        }

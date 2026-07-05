import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("/")
async def list_portfolios(user_id: str = "default", db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    portfolios = svc.list_by_user(user_id)
    return {
        "portfolios": [
            {
                "id": p.id,
                "name": p.name,
                "holdings": json.loads(p.holdings or "{}"),
                "candidate_pool": json.loads(p.candidate_pool or "[]"),
                "risk_score": p.risk_score,
                "expected_return": p.expected_return,
            }
            for p in portfolios
        ]
    }


@router.post("/")
async def create_portfolio(name: str, user_id: str = "default", db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    p = svc.create(user_id, name)
    return {"id": p.id, "name": p.name, "status": "created"}


@router.get("/{portfolio_id}")
async def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    p = svc.get(portfolio_id)
    if not p:
        return {"error": "not found"}
    return {
        "id": p.id,
        "name": p.name,
        "holdings": json.loads(p.holdings or "{}"),
        "candidate_pool": json.loads(p.candidate_pool or "[]"),
        "risk_score": p.risk_score,
    }


@router.delete("/{portfolio_id}")
async def delete_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    ok = svc.delete(portfolio_id)
    return {"status": "deleted" if ok else "not found"}


@router.post("/{portfolio_id}/pool")
async def add_to_pool(portfolio_id: str, stock_code: str, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    p = svc.add_to_pool(portfolio_id, stock_code)
    if not p:
        return {"error": "portfolio not found"}
    return {"candidate_pool": json.loads(p.candidate_pool or "[]")}


@router.delete("/{portfolio_id}/pool/{stock_code}")
async def remove_from_pool(portfolio_id: str, stock_code: str, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    p = svc.remove_from_pool(portfolio_id, stock_code)
    if not p:
        return {"error": "portfolio not found"}
    return {"candidate_pool": json.loads(p.candidate_pool or "[]")}


@router.post("/{portfolio_id}/suggest-weights")
async def suggest_weights(portfolio_id: str, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    return svc.suggest_weights(portfolio_id)


@router.get("/{portfolio_id}/risk")
async def calc_risk(portfolio_id: str, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    return svc.calc_risk_score(portfolio_id)

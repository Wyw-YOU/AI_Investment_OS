"""Tests for Portfolio service."""
import json
import pytest
from app.services.portfolio_service import PortfolioService


class TestPortfolioCRUD:
    def test_create_and_get(self, db_session):
        svc = PortfolioService(db_session)
        p = svc.create("u1", "Test Portfolio")
        assert p.name == "Test Portfolio"

        fetched = svc.get(p.id)
        assert fetched.id == p.id

    def test_list_by_user(self, db_session):
        svc = PortfolioService(db_session)
        svc.create("u1", "P1")
        svc.create("u1", "P2")
        svc.create("u2", "P3")

        result = svc.list_by_user("u1")
        assert len(result) == 2

    def test_delete(self, db_session):
        svc = PortfolioService(db_session)
        p = svc.create("u1", "ToDelete")
        assert svc.delete(p.id) is True
        assert svc.get(p.id) is None

    def test_update_holdings(self, db_session):
        from app.models.user import User
        db_session.add(User(id="u1", username="test"))
        db_session.commit()

        svc = PortfolioService(db_session)
        p = svc.create("u1", "P1")
        updated = svc.update_holdings(p.id, {"600519": 0.5, "000001": 0.5})
        assert json.loads(updated.holdings) == {"600519": 0.5, "000001": 0.5}


class TestCandidatePool:
    def test_add_and_remove(self, db_session):
        svc = PortfolioService(db_session)
        p = svc.create("u1", "P1")

        p = svc.add_to_pool(p.id, "600519")
        assert "600519" in json.loads(p.candidate_pool)

        p = svc.add_to_pool(p.id, "600519")
        pool = json.loads(p.candidate_pool)
        assert pool.count("600519") == 1

        p = svc.remove_from_pool(p.id, "600519")
        assert "600519" not in json.loads(p.candidate_pool)


class TestWeightSuggestion:
    def test_suggest_empty(self, db_session):
        svc = PortfolioService(db_session)
        p = svc.create("u1", "P1")
        result = svc.suggest_weights(p.id)
        assert result["weights"] == {}

    def test_suggest_with_pool(self, db_session):
        from app.models.stock import StockState
        db_session.add(StockState(stock_code="600519", score=80.0, sector="白酒"))
        db_session.add(StockState(stock_code="000001", score=60.0, sector="银行"))
        db_session.commit()

        svc = PortfolioService(db_session)
        p = svc.create("u1", "P1")
        svc.add_to_pool(p.id, "600519")
        svc.add_to_pool(p.id, "000001")

        result = svc.suggest_weights(p.id)
        assert "600519" in result["weights"]
        assert abs(sum(result["weights"].values()) - 1.0) < 0.01


class TestRiskScoring:
    def test_risk_empty(self, db_session):
        svc = PortfolioService(db_session)
        p = svc.create("u1", "P1")
        result = svc.calc_risk_score(p.id)
        assert result["risk_score"] == 0

    def test_risk_concentrated(self, db_session):
        svc = PortfolioService(db_session)
        p = svc.create("u1", "P1")
        svc.update_holdings(p.id, {"600519": 0.8, "000001": 0.2})
        result = svc.calc_risk_score(p.id)
        assert result["risk_level"] in ("MEDIUM", "HIGH")

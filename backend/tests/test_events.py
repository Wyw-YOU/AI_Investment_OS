"""Tests for Event and Alert services."""
import pytest
from app.services.event_service import EventService, AlertService, AlertRuleEngine
from app.models.stock import StockState


class TestEventService:
    def test_create_and_get(self, db_session):
        svc = EventService(db_session)
        event = svc.create_event("600519", "news", "茅台Q3财报超预期", impact_score=0.8)
        assert event.stock_code == "600519"

        events = svc.get_events("600519")
        assert len(events) == 1

    def test_filter_by_stock(self, db_session):
        svc = EventService(db_session)
        svc.create_event("600519", "news", "Event A")
        svc.create_event("000001", "news", "Event B")

        assert len(svc.get_events("600519")) == 1
        assert len(svc.get_events("000001")) == 1
        assert len(svc.get_events()) == 2


class TestAlertService:
    def test_create_and_list(self, db_session):
        from app.models.user import User
        db_session.add(User(id="u1", username="test"))
        db_session.commit()

        svc = AlertService(db_session)
        svc.create_alert("u1", "600519", "score_change", "评分上升 0.6")

        alerts = svc.get_alerts("u1")
        assert len(alerts) == 1
        assert alerts[0].is_read is False

    def test_mark_read(self, db_session):
        from app.models.user import User
        db_session.add(User(id="u1", username="test"))
        db_session.commit()

        svc = AlertService(db_session)
        alert = svc.create_alert("u1", "600519", "risk_level", "风险升高")
        assert svc.unread_count("u1") == 1

        svc.mark_read(alert.id)
        assert svc.unread_count("u1") == 0


class TestAlertRuleEngine:
    def test_score_change_alert(self):
        state = StockState(stock_code="600519", score=8.0, alert_level="NORMAL")
        alerts = AlertRuleEngine.evaluate("600519", state, {"score": 7.0})
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "score_change"

    def test_no_alert_small_change(self):
        state = StockState(stock_code="600519", score=7.2, alert_level="NORMAL")
        alerts = AlertRuleEngine.evaluate("600519", state, {"score": 7.0})
        assert len(alerts) == 0

    def test_risk_level_alert(self):
        state = StockState(stock_code="600519", score=5.0, alert_level="HIGH")
        alerts = AlertRuleEngine.evaluate("600519", state)
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "risk_level"

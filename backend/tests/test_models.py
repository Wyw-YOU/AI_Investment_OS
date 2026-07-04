"""Database model tests."""
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.stock import StockState
from app.models.event import MarketEvent, Alert
from app.models.agent_log import AgentLog


def test_create_user(db_session):
    user = User(id="u1", username="testuser", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.id == "u1"
    assert user.username == "testuser"


def test_create_portfolio(db_session):
    user = User(id="u1", username="testuser")
    db_session.add(user)
    portfolio = Portfolio(id="p1", user_id="u1", name="My Portfolio")
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    assert portfolio.name == "My Portfolio"
    assert portfolio.risk_score == 0.0


def test_create_stock_state(db_session):
    stock = StockState(stock_code="600519", latest_price=1800.0, sector="白酒")
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    assert stock.latest_price == 1800.0
    assert stock.alert_level == "NORMAL"


def test_create_agent_log(db_session):
    log = AgentLog(
        stock_code="600519",
        agent_name="finance",
        confidence=0.85,
        latency_ms=1200,
        tokens_used=500,
        model_name="gpt-4o-mini",
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)
    assert log.id is not None
    assert log.agent_name == "finance"


def test_create_market_event(db_session):
    event = MarketEvent(
        stock_code="600519",
        event_type="news",
        title="茅台发布Q3财报",
        impact_score=0.7,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    assert event.id is not None


def test_create_alert(db_session):
    user = User(id="u1", username="testuser")
    db_session.add(user)
    alert = Alert(
        user_id="u1",
        stock_code="600519",
        alert_type="score_change",
        message="评分上升 0.6",
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    assert alert.is_read == 0

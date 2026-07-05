"""Event detection and alert rules engine."""
import json
import logging
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.event import MarketEvent, Alert
from app.models.stock import StockState

logger = logging.getLogger(__name__)


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def create_event(
        self,
        stock_code: str,
        event_type: str,
        title: str,
        content: str = "",
        impact_score: float = 0.0,
        source: str = "",
    ) -> MarketEvent:
        event = MarketEvent(
            stock_code=stock_code,
            event_type=event_type,
            title=title,
            content=content,
            impact_score=impact_score,
            source=source,
            event_time=datetime.now(timezone.utc),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_events(self, stock_code: str = None, limit: int = 50) -> list[MarketEvent]:
        q = self.db.query(MarketEvent)
        if stock_code:
            q = q.filter(MarketEvent.stock_code == stock_code)
        return q.order_by(MarketEvent.created_at.desc()).limit(limit).all()


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def create_alert(
        self,
        user_id: str,
        stock_code: str,
        alert_type: str,
        message: str,
    ) -> Alert:
        alert = Alert(
            user_id=user_id,
            stock_code=stock_code,
            alert_type=alert_type,
            message=message,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_alerts(self, user_id: str, unread_only: bool = False) -> list[Alert]:
        q = self.db.query(Alert).filter(Alert.user_id == user_id)
        if unread_only:
            q = q.filter(Alert.is_read == False)
        return q.order_by(Alert.created_at.desc()).all()

    def mark_read(self, alert_id: int) -> bool:
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return False
        alert.is_read = True
        self.db.commit()
        return True

    def unread_count(self, user_id: str) -> int:
        return self.db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_read == False,
        ).count()


class AlertRuleEngine:
    """Evaluates alert rules against stock state changes."""

    SCORE_CHANGE_THRESHOLD = 0.5
    RISK_LEVELS_TO_ALERT = {"HIGH", "CRITICAL"}

    @staticmethod
    def evaluate(stock_code: str, stock_state: StockState, prev_state: dict = None) -> list[dict]:
        alerts = []
        prev = prev_state or {}

        score_change = stock_state.score - prev.get("score", stock_state.score)
        if abs(score_change) >= AlertRuleEngine.SCORE_CHANGE_THRESHOLD:
            direction = "上升" if score_change > 0 else "下降"
            alerts.append({
                "stock_code": stock_code,
                "alert_type": "score_change",
                "message": f"{stock_code} 评分{direction} {abs(score_change):.2f}，当前 {stock_state.score:.2f}",
            })

        if stock_state.alert_level in AlertRuleEngine.RISK_LEVELS_TO_ALERT:
            alerts.append({
                "stock_code": stock_code,
                "alert_type": "risk_level",
                "message": f"{stock_code} 风险等级: {stock_state.alert_level}",
            })

        return alerts

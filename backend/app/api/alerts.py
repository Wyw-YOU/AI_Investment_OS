from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.event_service import AlertService

router = APIRouter()


@router.get("/")
async def list_alerts(user_id: str = "default", db: Session = Depends(get_db)):
    svc = AlertService(db)
    alerts = svc.get_alerts(user_id)
    return {
        "alerts": [
            {
                "id": a.id,
                "stock_code": a.stock_code,
                "alert_type": a.alert_type,
                "message": a.message,
                "is_read": a.is_read,
                "created_at": str(a.created_at),
            }
            for a in alerts
        ]
    }


@router.get("/unread")
async def unread_alerts(user_id: str = "default", db: Session = Depends(get_db)):
    svc = AlertService(db)
    alerts = svc.get_alerts(user_id, unread_only=True)
    return {
        "alerts": [
            {
                "id": a.id,
                "stock_code": a.stock_code,
                "message": a.message,
                "created_at": str(a.created_at),
            }
            for a in alerts
        ],
        "count": len(alerts),
    }


@router.post("/{alert_id}/read")
async def mark_read(alert_id: int, db: Session = Depends(get_db)):
    svc = AlertService(db)
    ok = svc.mark_read(alert_id)
    return {"status": "ok" if ok else "not found"}

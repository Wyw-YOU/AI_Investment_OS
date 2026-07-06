import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.agents.workflow import run_investment_analysis
from app.database import get_db
from app.models.schemas import AgentRunRequest, ApiResponse
from app.models.task import AgentTask
from app.models.user import User
from app.services.financial import financial_service
from app.services.indicators import indicators_service
from app.services.market_data import market_data_service
from app.services.news import news_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/run")
async def run_analysis(
    req: AgentRunRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stock_code = req.stock_code

    # Gather data from services
    realtime = await market_data_service.get_stock_realtime(stock_code)
    if "error" in realtime:
        return ApiResponse(code=400, message=f"Failed to fetch stock data: {realtime['error']}")
    stock_name = realtime.get("name", stock_code)

    history = await market_data_service.get_stock_history(stock_code, 120)
    news = await news_service.fetch_stock_news(stock_code)
    financial = await financial_service.get_financial_data(stock_code)
    indicators = indicators_service.calculate_all(history)

    # Run workflow
    result = await run_investment_analysis(
        stock_code=stock_code,
        stock_name=stock_name,
        query=req.query,
        user_id=str(user.id),
        market_data=realtime,
        news_data=news,
        financial_data=financial,
        price_history=history,
        indicators=indicators,
    )

    # Save to DB
    task = AgentTask(
        stock_code=stock_code,
        status=result.get("phase", "complete"),
        agent_outputs_json=json.dumps(result.get("agent_outputs", {}), ensure_ascii=False),
        final_report_json=json.dumps(result.get("final_report", {}), ensure_ascii=False),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    return ApiResponse(data={
        "task_id": task.id,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "phase": result.get("phase"),
        "final_report": result.get("final_report", {}),
        "risk_assessment": result.get("risk_assessment", {}),
        "quant_score": result.get("quant_score", {}),
        "agent_outputs": {
            k: {"confidence": v.get("confidence", 0), "summary": v.get("result", {}).get("summary", "")}
            for k, v in result.get("agent_outputs", {}).items()
        },
    })


@router.get("/status/{task_id}")
async def get_status(task_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return ApiResponse(code=404, message="Task not found")
    return ApiResponse(data={
        "task_id": task.id,
        "stock_code": task.stock_code,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "final_report": json.loads(task.final_report_json) if task.final_report_json else {},
    })


@router.get("/history")
async def get_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    result = await db.execute(
        select(AgentTask).order_by(AgentTask.created_at.desc()).limit(20)
    )
    tasks = result.scalars().all()
    return ApiResponse(data=[{
        "task_id": t.id,
        "stock_code": t.stock_code,
        "status": t.status,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    } for t in tasks])

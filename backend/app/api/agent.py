"""
Agent 分析 API 路由。

分析流程：
1. POST /run → 收集数据、创建 DB 任务、启动后台 workflow、立即返回 task_id
2. 前端通过 WebSocket 或轮询 GET /status 获取实时进度
3. 后台 workflow 完成后将结果写回 DB，前端获取最终报告
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.agents.workflow import run_investment_analysis
from app.core.task_manager import task_manager
from app.database import async_session, get_db
from app.models.schemas import AgentRunRequest, ApiResponse
from app.models.task import AgentTask
from app.models.user import User
from app.models.workspace import Note, Workspace
from app.services.financial import financial_service
from app.services.indicators import indicators_service
from app.services.market_data import market_data_service
from app.services.news import news_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])


async def _save_to_workspace(db: AsyncSession, task: AgentTask, user_id: int):
    result = await db.execute(
        select(Workspace).where(
            Workspace.user_id == user_id,
            Workspace.stock_code == task.stock_code,
        )
    )
    ws = result.scalar_one_or_none()
    if not ws:
        ws = Workspace(
            user_id=user_id,
            stock_code=task.stock_code,
            name=f"{task.stock_code} 研究空间",
        )
        db.add(ws)
        await db.flush()

    task.workspace_id = ws.id

    report = {}
    try:
        report = json.loads(task.final_report_json) if task.final_report_json else {}
    except json.JSONDecodeError:
        pass

    if report.get("executive_summary"):
        note = Note(
            workspace_id=ws.id,
            content=f"[AI 分析] {report['executive_summary'][:500]}",
            tags="ai-analysis,auto",
        )
        db.add(note)


async def _run_analysis_background(
    analysis_id: str,
    db_task_id: int,
    stock_code: str,
    stock_name: str,
    user_id: int,
    query: str,
    market_data: dict,
    news_data: list,
    financial_data: dict,
    price_history: list,
    indicators: dict,
):
    progress_callback = task_manager.make_progress_callback(analysis_id)

    async with async_session() as db:
        try:
            task = await db.get(AgentTask, db_task_id)
            if task:
                task.status = "running"
                await db.commit()

            result = await run_investment_analysis(
                stock_code=stock_code,
                stock_name=stock_name,
                query=query,
                user_id=str(user_id),
                market_data=market_data,
                news_data=news_data,
                financial_data=financial_data,
                price_history=price_history,
                indicators=indicators,
                progress_callback=progress_callback,
            )

            task = await db.get(AgentTask, db_task_id)
            if task:
                task.status = result.get("phase", "complete")
                task.agent_outputs_json = json.dumps(
                    result.get("agent_outputs", {}), ensure_ascii=False
                )
                task.final_report_json = json.dumps(
                    result.get("final_report", {}), ensure_ascii=False
                )
                task.progress_json = json.dumps(
                    result.get("agent_progress", {}), ensure_ascii=False
                )
                task.completed_at = datetime.now(timezone.utc)
                await _save_to_workspace(db, task, user_id)
                await db.commit()

        except Exception as e:
            logger.error(f"Background analysis {analysis_id} failed: {e}")
            task = await db.get(AgentTask, db_task_id)
            if task:
                task.status = "failed"
                task.error_message = str(e)
                await db.commit()


@router.post("/run")
async def run_analysis(
    req: AgentRunRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stock_code = req.stock_code

    realtime = await market_data_service.get_stock_realtime(stock_code)
    if "error" in realtime:
        return ApiResponse(code=400, message=f"Failed to fetch stock data: {realtime['error']}")
    stock_name = realtime.get("name", stock_code)

    history = await market_data_service.get_stock_history(stock_code, 120)
    news = await news_service.fetch_stock_news(stock_code)
    financial = await financial_service.get_financial_data(stock_code)
    indicators = indicators_service.calculate_all(history)

    task = AgentTask(
        stock_code=stock_code,
        status="pending",
        user_id=user.id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    db_task_id = task.id

    analysis_id = f"{db_task_id}_{stock_code}"

    task_manager.start_background_task(
        analysis_id,
        _run_analysis_background(
            analysis_id=analysis_id,
            db_task_id=db_task_id,
            stock_code=stock_code,
            stock_name=stock_name,
            user_id=user.id,
            query=req.query,
            market_data=realtime,
            news_data=news,
            financial_data=financial,
            price_history=history,
            indicators=indicators,
        ),
    )

    return ApiResponse(data={
        "task_id": db_task_id,
        "analysis_id": analysis_id,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "status": "pending",
    })


@router.get("/status/{task_id}")
async def get_status(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return ApiResponse(code=404, message="Task not found")

    progress = {}
    try:
        progress = json.loads(task.progress_json) if task.progress_json else {}
    except json.JSONDecodeError:
        pass

    final_report = {}
    try:
        final_report = json.loads(task.final_report_json) if task.final_report_json else {}
    except json.JSONDecodeError:
        pass

    return ApiResponse(data={
        "task_id": task.id,
        "stock_code": task.stock_code,
        "status": task.status,
        "progress": progress,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "final_report": final_report,
    })


@router.get("/progress/{analysis_id}")
async def get_progress(analysis_id: str):
    events = task_manager.get_progress(analysis_id)
    return ApiResponse(data={"analysis_id": analysis_id, "events": events})


@router.websocket("/ws/analysis/{analysis_id}")
async def ws_analysis_progress(websocket: WebSocket, analysis_id: str):
    await websocket.accept()
    queue = task_manager.subscribe(analysis_id)
    try:
        snapshot = task_manager.get_progress(analysis_id)
        for event in snapshot:
            await websocket.send_json(event)

        while True:
            event = await asyncio.wait_for(queue.get(), timeout=300)
            if event is None:
                break
            await websocket.send_json(event)
            if event.get("agent_name") == "report" and event.get("status") in ("completed", "failed"):
                break
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        task_manager.unsubscribe(analysis_id, queue)


@router.get("/history")
async def get_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentTask).where(AgentTask.user_id == user.id)
        .order_by(AgentTask.created_at.desc())
        .limit(20)
    )
    tasks = result.scalars().all()
    return ApiResponse(data=[{
        "task_id": t.id,
        "stock_code": t.stock_code,
        "status": t.status,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    } for t in tasks])

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.schemas import ApiResponse, NoteCreate, WorkspaceCreate, WorkspaceResponse
from app.models.user import User
from app.models.workspace import AnalysisRecord, Note, Workspace

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


@router.post("")
async def create_workspace(
    req: WorkspaceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = Workspace(
        user_id=user.id,
        stock_code=req.stock_code,
        name=req.name or f"{req.stock_code} 研究空间",
    )
    db.add(ws)
    await db.flush()
    await db.refresh(ws)
    return ApiResponse(data=WorkspaceResponse.model_validate(ws).model_dump())


@router.get("")
async def list_workspaces(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Workspace).where(Workspace.user_id == user.id).order_by(Workspace.created_at.desc())
    )
    workspaces = result.scalars().all()
    return ApiResponse(data=[WorkspaceResponse.model_validate(w).model_dump() for w in workspaces])


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id, Workspace.user_id == user.id)
    )
    ws = result.scalar_one_or_none()
    if not ws:
        return ApiResponse(code=404, message="Workspace not found")
    return ApiResponse(data=WorkspaceResponse.model_validate(ws).model_dump())


@router.post("/{workspace_id}/note")
async def add_note(
    workspace_id: int,
    req: NoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id, Workspace.user_id == user.id)
    )
    ws = result.scalar_one_or_none()
    if not ws:
        return ApiResponse(code=404, message="Workspace not found")
    note = Note(workspace_id=workspace_id, content=req.content, tags=req.tags)
    db.add(note)
    await db.flush()
    return ApiResponse(data={"id": note.id, "content": note.content})


@router.get("/{workspace_id}/analyses")
async def list_analyses(
    workspace_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_check = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id, Workspace.user_id == user.id)
    )
    if not ws_check.scalar_one_or_none():
        return ApiResponse(code=404, message="Workspace not found")

    result = await db.execute(
        select(AnalysisRecord)
        .where(AnalysisRecord.workspace_id == workspace_id)
        .order_by(AnalysisRecord.created_at.desc())
        .limit(20)
    )
    records = result.scalars().all()
    return ApiResponse(data=[{
        "id": r.id,
        "task_id": r.task_id,
        "stock_code": r.stock_code,
        "summary": r.summary,
        "recommendation": r.recommendation,
        "score": r.score,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in records])


@router.get("/{workspace_id}/timeline")
async def get_timeline(
    workspace_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_check = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id, Workspace.user_id == user.id)
    )
    if not ws_check.scalar_one_or_none():
        return ApiResponse(code=404, message="Workspace not found")

    notes_result = await db.execute(
        select(Note).where(Note.workspace_id == workspace_id)
    )
    analyses_result = await db.execute(
        select(AnalysisRecord).where(AnalysisRecord.workspace_id == workspace_id)
    )

    timeline = []
    for note in notes_result.scalars().all():
        timeline.append({
            "type": "note",
            "id": note.id,
            "content": note.content,
            "tags": note.tags,
            "created_at": note.created_at.isoformat() if note.created_at else None,
        })
    for record in analyses_result.scalars().all():
        timeline.append({
            "type": "analysis",
            "id": record.id,
            "task_id": record.task_id,
            "summary": record.summary,
            "recommendation": record.recommendation,
            "score": record.score,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        })

    timeline.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return ApiResponse(data=timeline)

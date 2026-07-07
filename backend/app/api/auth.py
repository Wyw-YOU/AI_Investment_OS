"""
认证相关 API 路由。
提供注册、登录、获取当前用户三个接口。
注册和登录成功后均返回 JWT token，前端保存在 localStorage 中。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token
from app.core.security import hash_password, verify_password
from app.database import get_db
from app.models.schemas import ApiResponse, Token, UserCreate, UserLogin, UserResponse
from app.models.user import User

from .deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse)
async def register(req: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册：检查邮箱唯一性 → 哈希密码 → 创建用户 → 返回 token。"""
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=req.email, hashed_password=hash_password(req.password))
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return ApiResponse(data={"user": UserResponse.model_validate(user).model_dump(), "token": token})


@router.post("/login", response_model=ApiResponse)
async def login(req: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录：验证邮箱存在 + 密码正确 → 返回 token。"""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return ApiResponse(data={"user": UserResponse.model_validate(user).model_dump(), "token": token})


@router.get("/me", response_model=ApiResponse)
async def me(user: User = Depends(get_current_user)):
    """获取当前登录用户信息（需要 Authorization header 中的 Bearer token）。"""
    return ApiResponse(data=UserResponse.model_validate(user).model_dump())

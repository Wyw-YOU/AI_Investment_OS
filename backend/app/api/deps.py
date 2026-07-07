"""
FastAPI 依赖注入函数。
get_current_user 是核心鉴权依赖，通过 HTTPBearer 从请求头提取 JWT token，
验证后查询数据库返回 User 对象。所有需要登录的路由通过 Depends(get_current_user) 使用。
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_token
from app.database import get_db
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    从 Authorization: Bearer <token> 提取并验证 JWT，返回对应的 User 对象。
    token 无效或用户不存在时抛出 401。
    """
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user

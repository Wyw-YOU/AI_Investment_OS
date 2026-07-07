"""
Pydantic 请求/响应模型。
用于 API 层的数据验证和序列化。
与 SQLAlchemy ORM 模型（user.py, task.py 等）不同：schemas 负责接口契约，ORM 负责数据库映射。
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


# ============ 认证相关 ============

class UserCreate(BaseModel):
    """注册请求体：邮箱 + 密码（明文，后端哈希存储）。"""
    email: str
    password: str


class UserLogin(BaseModel):
    """登录请求体：邮箱 + 密码。"""
    email: str
    password: str


class UserResponse(BaseModel):
    """用户信息响应（不含密码），from_attributes 允许从 SQLAlchemy 模型直接转换。"""
    id: int
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token 响应（保留字段，当前直接在 ApiResponse 中返回）。"""
    access_token: str
    token_type: str = "bearer"


# ============ 股票相关 ============

class StockResponse(BaseModel):
    """股票详情响应（保留字段，当前由 market_data_service 直接返回 dict）。"""
    stock_code: str
    name: str
    market: str
    industry: str
    price: float = 0.0
    change_pct: float = 0.0


# ============ 研究空间相关 ============

class WorkspaceCreate(BaseModel):
    """创建研究空间请求体。"""
    stock_code: str
    name: str = ""


class WorkspaceResponse(BaseModel):
    """研究空间响应。"""
    id: int
    stock_code: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    """向研究空间添加笔记请求体。"""
    content: str
    tags: str = ""


# ============ Agent 分析相关 ============

class AgentRunRequest(BaseModel):
    """发起 AI 分析请求体。"""
    stock_code: str
    query: str = ""


class AgentTaskResponse(BaseModel):
    """分析任务响应（保留字段，当前在 agent.py 中手动构建 dict）。"""
    id: int
    stock_code: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


# ============ 通用 ============

class ApiResponse(BaseModel):
    """所有 API 的统一响应格式：code=0 表示成功，非 0 为错误码。"""
    code: int = 0
    message: str = "success"
    data: dict | list | None = None

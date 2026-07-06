from datetime import datetime

from pydantic import BaseModel, EmailStr


# Auth
class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Stock
class StockResponse(BaseModel):
    stock_code: str
    name: str
    market: str
    industry: str
    price: float = 0.0
    change_pct: float = 0.0


# Workspace
class WorkspaceCreate(BaseModel):
    stock_code: str
    name: str = ""


class WorkspaceResponse(BaseModel):
    id: int
    stock_code: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    content: str
    tags: str = ""


# Agent
class AgentRunRequest(BaseModel):
    stock_code: str
    query: str = ""


class AgentTaskResponse(BaseModel):
    id: int
    stock_code: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


# Standard API Response
class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict | list | None = None

"""
LangGraph 工作流状态定义。

WorkflowState 是整个投资分析流程在各 agent 之间传递的状态字典。
LangGraph 用 Annotated 类型标记来控制并行节点合并策略：
- Annotated[list, operator.add]：并行节点结果 append 合并（不会互相覆盖）
- Annotated[dict, _merge_dicts]：并行节点结果 merge 合并（后者覆盖前者的同名键）
"""

import operator
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, TypedDict


class WorkflowPhase(str, Enum):
    INIT = "init"
    ANALYZING = "analyzing"
    RISK_ASSESSING = "risk_assessing"
    SCORING = "scoring"
    REPORTING = "reporting"
    COMPLETE = "complete"
    FAILED = "failed"


def _merge_dicts(a: dict, b: dict) -> dict:
    return {**a, **b}


class WorkflowState(TypedDict, total=False):
    # Core identifiers
    task_id: str
    stock_code: str
    stock_name: str
    user_id: str
    query: str

    # Phase tracking
    phase: str
    started_at: str
    updated_at: str

    # Input data
    market_data: dict[str, Any]
    news_data: list[dict[str, Any]]
    financial_data: dict[str, Any]
    price_history: list[dict[str, Any]]
    indicators: dict[str, Any]

    # Agent outputs (parallel-safe with Annotated)
    parallel_results: Annotated[list[dict], operator.add]
    agent_outputs: dict[str, Any]

    # Sequential outputs
    risk_assessment: dict[str, Any]
    quant_score: dict[str, Any]
    final_report: dict[str, Any]

    # Error tracking
    errors: Annotated[list[dict], operator.add]

    # Progress tracking
    agent_progress: Annotated[dict[str, str], _merge_dicts]


def create_initial_state(
    stock_code: str,
    stock_name: str = "",
    query: str = "",
    user_id: str = "",
    market_data: dict | None = None,
    news_data: list | None = None,
    financial_data: dict | None = None,
    price_history: list | None = None,
    indicators: dict | None = None,
) -> WorkflowState:
    return WorkflowState(
        task_id=str(uuid.uuid4()),
        stock_code=stock_code,
        stock_name=stock_name,
        user_id=user_id,
        query=query,
        phase=WorkflowPhase.INIT.value,
        started_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        market_data=market_data or {},
        news_data=news_data or [],
        financial_data=financial_data or {},
        price_history=price_history or [],
        indicators=indicators or {},
        parallel_results=[],
        agent_outputs={},
        risk_assessment={},
        quant_score={},
        final_report={},
        errors=[],
        agent_progress={
            "planner": "pending",
            "news": "pending",
            "financial": "pending",
            "technical": "pending",
            "macro": "pending",
            "risk": "pending",
            "quant": "pending",
            "report": "pending",
        },
    )

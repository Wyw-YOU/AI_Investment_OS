"""
Agent 输出数据模型。
所有 agent 的 run() 方法都返回 AgentOutput 实例。
"""

from pydantic import BaseModel, field_validator
from typing import Any
from datetime import datetime


class AgentOutput(BaseModel):
    """
    Agent 分析结果的标准化输出格式。

    属性:
        agent_name: 产生此输出的 agent 名称（如 "news"、"financial"）
        result:      LLM 返回的结构化分析结果（JSON dict）
        confidence:  分析置信度 0.0~1.0，由各 agent 的 _calculate_confidence 计算
        citations:   引用的数据来源列表
        metadata:    额外元数据（保留字段）
        timestamp:   输出产生时间，自动填充
    """
    agent_name: str
    result: dict[str, Any]
    confidence: float = 0.0
    citations: list[str] = []
    metadata: dict[str, Any] = {}
    timestamp: str = ""

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """将置信度强制限制在 [0.0, 1.0] 范围内，防止 LLM 返回越界值。"""
        return max(0.0, min(1.0, v))

    def model_post_init(self, __context: Any) -> None:
        """Pydantic v2 后初始化钩子，自动填充 timestamp。"""
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now().isoformat())

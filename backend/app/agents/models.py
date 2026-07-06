from pydantic import BaseModel, field_validator
from typing import Any
from datetime import datetime


class AgentOutput(BaseModel):
    agent_name: str
    result: dict[str, Any]
    confidence: float = 0.0
    citations: list[str] = []
    metadata: dict[str, Any] = {}
    timestamp: str = ""

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    def model_post_init(self, __context: Any) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now().isoformat())

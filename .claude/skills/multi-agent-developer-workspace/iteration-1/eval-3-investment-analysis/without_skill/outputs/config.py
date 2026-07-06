"""
Configuration for the Multi-Agent Investment Analysis System.

Centralizes all settings including LLM configuration, model parameters,
timeout values, and feature toggles.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for the language model."""

    provider: str = "openai"
    model_name: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 4096
    request_timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass(frozen=True)
class WorkflowConfig:
    """Configuration for the LangGraph workflow."""

    max_parallel_agents: int = 4
    agent_timeout: int = 300  # seconds per agent
    enable_checkpoints: bool = False
    recursion_limit: int = 25
    confidence_threshold: float = 0.5
    max_retries_per_agent: int = 2


@dataclass(frozen=True)
class AgentWeightConfig:
    """Relative importance weights for agent outputs in final scoring."""

    news_weight: float = 0.20
    financial_weight: float = 0.30
    technical_weight: float = 0.25
    risk_weight: float = 0.25

    def normalized(self) -> dict[str, float]:
        """Return normalized weights that sum to 1.0."""
        total = (
            self.news_weight
            + self.financial_weight
            + self.technical_weight
            + self.risk_weight
        )
        if total == 0:
            raise ValueError("All weights are zero; cannot normalize.")
        return {
            "news": self.news_weight / total,
            "financial": self.financial_weight / total,
            "technical": self.technical_weight / total,
            "risk": self.risk_weight / total,
        }


@dataclass
class AppConfig:
    """Top-level application configuration."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    weights: AgentWeightConfig = field(default_factory=AgentWeightConfig)
    log_level: str = "INFO"
    output_dir: str = "outputs"

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Build configuration from environment variables."""
        return cls(
            llm=LLMConfig(
                provider=os.getenv("LLM_PROVIDER", "openai"),
                model_name=os.getenv("LLM_MODEL", "gpt-4o"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
                request_timeout=int(os.getenv("LLM_TIMEOUT", "120")),
            ),
            workflow=WorkflowConfig(
                agent_timeout=int(os.getenv("AGENT_TIMEOUT", "300")),
                confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            output_dir=os.getenv("OUTPUT_DIR", "outputs"),
        )

"""
Investment Analysis System - Configuration

Centralized configuration for all agents, LLM settings, and workflow parameters.
Uses environment variables with sensible defaults for local development.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 4000
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_retries: int = 3
    retry_base_delay: float = 1.0

    def __post_init__(self):
        # Read from environment if not explicitly provided
        if self.api_key is None:
            self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.base_url is None:
            self.base_url = os.environ.get("OPENAI_BASE_URL")


@dataclass
class AgentConfig:
    """Per-agent LLM configuration overrides."""
    news: LLMConfig = field(default_factory=lambda: LLMConfig(temperature=0.4))
    financial: LLMConfig = field(default_factory=lambda: LLMConfig(temperature=0.2))
    technical: LLMConfig = field(default_factory=lambda: LLMConfig(temperature=0.2))
    risk: LLMConfig = field(default_factory=lambda: LLMConfig(temperature=0.2))
    report: LLMConfig = field(default_factory=lambda: LLMConfig(temperature=0.4))


@dataclass
class WorkflowConfig:
    """Workflow-level configuration."""
    max_parallel_agents: int = 3
    timeout_seconds: int = 300  # 5 minutes total
    enable_logging: bool = True
    log_level: str = "INFO"

    # Persistence (optional)
    persist_results: bool = False
    results_dir: str = "./results"


@dataclass
class SystemConfig:
    """Top-level system configuration."""
    agents: AgentConfig = field(default_factory=AgentConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    default_model: str = "gpt-4o"

    @classmethod
    def from_env(cls) -> "SystemConfig":
        """Create configuration from environment variables."""
        return cls(
            default_model=os.environ.get("INVESTMENT_MODEL", "gpt-4o"),
            agents=AgentConfig(
                news=LLMConfig(
                    model=os.environ.get("NEWS_AGENT_MODEL", os.environ.get("INVESTMENT_MODEL", "gpt-4o")),
                    temperature=float(os.environ.get("NEWS_AGENT_TEMPERATURE", "0.4")),
                    max_tokens=int(os.environ.get("NEWS_AGENT_MAX_TOKENS", "4000")),
                ),
                financial=LLMConfig(
                    model=os.environ.get("FINANCIAL_AGENT_MODEL", os.environ.get("INVESTMENT_MODEL", "gpt-4o")),
                    temperature=float(os.environ.get("FINANCIAL_AGENT_TEMPERATURE", "0.2")),
                    max_tokens=int(os.environ.get("FINANCIAL_AGENT_MAX_TOKENS", "4000")),
                ),
                technical=LLMConfig(
                    model=os.environ.get("TECHNICAL_AGENT_MODEL", os.environ.get("INVESTMENT_MODEL", "gpt-4o")),
                    temperature=float(os.environ.get("TECHNICAL_AGENT_TEMPERATURE", "0.2")),
                    max_tokens=int(os.environ.get("TECHNICAL_AGENT_MAX_TOKENS", "4000")),
                ),
                risk=LLMConfig(
                    model=os.environ.get("RISK_AGENT_MODEL", os.environ.get("INVESTMENT_MODEL", "gpt-4o")),
                    temperature=float(os.environ.get("RISK_AGENT_TEMPERATURE", "0.2")),
                    max_tokens=int(os.environ.get("RISK_AGENT_MAX_TOKENS", "4000")),
                ),
                report=LLMConfig(
                    model=os.environ.get("REPORT_AGENT_MODEL", os.environ.get("INVESTMENT_MODEL", "gpt-4o")),
                    temperature=float(os.environ.get("REPORT_AGENT_TEMPERATURE", "0.4")),
                    max_tokens=int(os.environ.get("REPORT_AGENT_MAX_TOKENS", "4000")),
                ),
            ),
            workflow=WorkflowConfig(
                max_parallel_agents=int(os.environ.get("MAX_PARALLEL_AGENTS", "3")),
                timeout_seconds=int(os.environ.get("WORKFLOW_TIMEOUT", "300")),
                enable_logging=os.environ.get("ENABLE_LOGGING", "true").lower() == "true",
                log_level=os.environ.get("LOG_LEVEL", "INFO"),
                persist_results=os.environ.get("PERSIST_RESULTS", "false").lower() == "true",
                results_dir=os.environ.get("RESULTS_DIR", "./results"),
            ),
        )


# --- Default singleton ---

_default_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get the system configuration (lazy singleton)."""
    global _default_config
    if _default_config is None:
        _default_config = SystemConfig.from_env()
    return _default_config


def set_config(config: SystemConfig) -> None:
    """Override the default configuration."""
    global _default_config
    _default_config = config

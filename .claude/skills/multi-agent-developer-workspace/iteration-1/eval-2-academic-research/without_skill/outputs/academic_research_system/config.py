"""
Configuration utilities for the Academic Research Multi-Agent System.

Provides easy setup for different LLM providers and configurable parameters
for each agent. Supports environment-variable-based configuration.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for individual agent behavior."""
    # Temperature settings per agent type (lower = more deterministic)
    extractor_temperature: float = 0.0     # Extraction should be deterministic
    analyzer_temperature: float = 0.1      # Quality analysis allows slight variation
    summary_temperature: float = 0.2       # Summaries can be slightly creative
    gap_analyzer_temperature: float = 0.3  # Gap analysis benefits from some creativity
    lit_review_temperature: float = 0.3    # Literature review needs some creativity

    # Max tokens per agent call
    extractor_max_tokens: int = 2000
    analyzer_max_tokens: int = 2000
    summary_max_tokens: int = 2000
    gap_analyzer_max_tokens: int = 4000    # Corpus-level analysis needs more tokens
    lit_review_max_tokens: int = 8000      # Full review needs the most tokens

    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0

    # Parallelism
    max_concurrent_papers: int = 5  # Max papers to process in parallel


@dataclass
class SystemConfig:
    """Top-level system configuration."""
    # LLM provider
    provider: str = "openai"     # "openai", "anthropic", "ollama"
    model: str = "gpt-4o"       # Model name
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # For Ollama or custom endpoints

    # Agent-specific configuration
    agent: AgentConfig = field(default_factory=AgentConfig)

    # Logging
    log_level: str = "INFO"

    # Output
    output_format: str = "markdown"  # "markdown", "json", "both"


def create_llm(config: SystemConfig) -> Any:
    """
    Create an LLM instance based on the system configuration.

    Args:
        config: System configuration with provider and model settings.

    Returns:
        LangChain chat model instance.

    Raises:
        ValueError: If the provider is not supported.
        ImportError: If the required provider package is not installed.
    """
    provider = config.provider.lower()

    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai is required for OpenAI provider. "
                "Install with: pip install langchain-openai"
            )
        api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key in SystemConfig."
            )
        return ChatOpenAI(
            model=config.model,
            api_key=api_key,
            temperature=config.agent.extractor_temperature,
            max_tokens=config.agent.extractor_max_tokens,
        )

    elif provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic is required for Anthropic provider. "
                "Install with: pip install langchain-anthropic"
            )
        api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key in SystemConfig."
            )
        return ChatAnthropic(
            model=config.model,
            api_key=api_key,
            temperature=config.agent.extractor_temperature,
            max_tokens=config.agent.extractor_max_tokens,
        )

    elif provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError(
                "langchain-ollama is required for Ollama provider. "
                "Install with: pip install langchain-ollama"
            )
        base_url = config.base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(
            model=config.model,
            base_url=base_url,
            temperature=config.agent.extractor_temperature,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. "
            f"Supported providers: openai, anthropic, ollama"
        )


def configure_logging(level: str = "INFO"):
    """Configure logging for the entire system."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ===========================================================================
# Convenience Functions
# ===========================================================================

def create_config_from_env() -> SystemConfig:
    """
    Create a SystemConfig from environment variables.

    Environment variables:
        AR_PROVIDER: LLM provider (openai, anthropic, ollama)
        AR_MODEL: Model name
        AR_API_KEY: API key
        AR_BASE_URL: Base URL for Ollama/custom endpoints
        AR_LOG_LEVEL: Logging level
    """
    return SystemConfig(
        provider=os.environ.get("AR_PROVIDER", "openai"),
        model=os.environ.get("AR_MODEL", "gpt-4o"),
        api_key=os.environ.get("AR_API_KEY"),
        base_url=os.environ.get("AR_BASE_URL"),
        log_level=os.environ.get("AR_LOG_LEVEL", "INFO"),
    )


def quick_setup(
    provider: str = "openai",
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
) -> tuple[SystemConfig, Any]:
    """
    Quick setup function that creates both config and LLM.

    Args:
        provider: LLM provider name.
        model: Model name.
        api_key: Optional API key (falls back to env vars).

    Returns:
        Tuple of (SystemConfig, LLM instance).
    """
    config = SystemConfig(provider=provider, model=model, api_key=api_key)
    configure_logging(config.log_level)
    llm = create_llm(config)
    return config, llm

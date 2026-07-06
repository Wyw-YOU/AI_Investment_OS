"""
Base agent class for the Multi-Agent Investment Analysis System.

Provides the common interface and shared logic for all specialist agents:
LLM invocation, output parsing, validation, retry, and fallback.
"""

from __future__ import annotations

import json
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, Type

from pydantic import BaseModel

from config import AppConfig, LLMConfig
from utils import (
    create_fallback_output,
    extract_json_from_llm_response,
    logger,
    retry_with_backoff,
    serialize_agent_output,
    validate_agent_output,
)


class BaseAgent(ABC):
    """
    Abstract base class for all specialist investment agents.

    Subclasses must implement:
    - ``agent_name``: unique identifier string
    - ``output_schema``: the Pydantic model class for structured output
    - ``build_prompt()``: returns the fully-formed prompt string
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()
        self._llm = self._init_llm()

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique name identifying this agent in the workflow."""

    @property
    @abstractmethod
    def output_schema(self) -> Type[BaseModel]:
        """Pydantic model class that validates this agent's output."""

    @abstractmethod
    def build_prompt(self, ticker: str, **kwargs: Any) -> str:
        """Build the LLM prompt for the given ticker and context."""

    # ------------------------------------------------------------------
    # LLM initialization (lazy, provider-agnostic)
    # ------------------------------------------------------------------

    def _init_llm(self) -> Any:
        """
        Initialise the LLM client.  Override for custom providers.

        The default implementation tries to import langchain_openai.ChatOpenAI
        and falls back to a simple stub that raises if no API key is found.
        """
        llm_cfg: LLMConfig = self.config.llm
        try:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=llm_cfg.model_name,
                temperature=llm_cfg.temperature,
                max_tokens=llm_cfg.max_tokens,
                request_timeout=llm_cfg.request_timeout,
                max_retries=llm_cfg.max_retries,
            )
        except ImportError:
            logger.warning(
                "langchain_openai not installed; %s will use stub LLM.",
                self.agent_name,
            )
            return self._StubLLM(llm_cfg)

    class _StubLLM:
        """Deterministic stub for environments without an API key."""

        def __init__(self, cfg: LLMConfig) -> None:
            self._cfg = cfg

        def invoke(self, prompt: str) -> Any:  # noqa: D401
            raise RuntimeError(
                f"No LLM provider available. Install langchain_openai and set "
                f"OPENAI_API_KEY, or override {__name__}.BaseAgent._init_llm()."
            )

    # ------------------------------------------------------------------
    # Core execution logic
    # ------------------------------------------------------------------

    @retry_with_backoff(max_retries=2, initial_delay=2.0)
    def _call_llm(self, prompt: str) -> str:
        """Invoke the LLM and return the raw string response."""
        response = self._llm.invoke(prompt)
        # LangChain returns an AIMessage; extract content
        if hasattr(response, "content"):
            return str(response.content)
        return str(response)

    def run(self, ticker: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute the full agent pipeline: build prompt, call LLM, parse,
        validate, and return a JSON-serializable dict.

        If all retries are exhausted, a fallback output is returned with
        ``confidence=0.0`` and an error message.
        """
        logger.info("[%s] Starting analysis for %s", self.agent_name, ticker)

        try:
            prompt = self.build_prompt(ticker, **kwargs)
            logger.debug("[%s] Prompt length: %d chars", self.agent_name, len(prompt))

            raw_response = self._call_llm(prompt)
            logger.debug("[%s] Raw response length: %d chars", self.agent_name, len(raw_response))

            parsed = extract_json_from_llm_response(raw_response)
            validated = validate_agent_output(parsed, self.output_schema)

            logger.info(
                "[%s] Analysis complete. Confidence=%.2f",
                self.agent_name,
                validated.confidence,
            )
            return serialize_agent_output(validated)

        except Exception as exc:
            logger.error(
                "[%s] Analysis failed after retries: %s\n%s",
                self.agent_name,
                exc,
                traceback.format_exc(),
            )
            fallback = create_fallback_output(
                ticker=ticker,
                agent_name=self.agent_name,
                error_message=str(exc),
                schema_class=self.output_schema,
            )
            return serialize_agent_output(fallback)

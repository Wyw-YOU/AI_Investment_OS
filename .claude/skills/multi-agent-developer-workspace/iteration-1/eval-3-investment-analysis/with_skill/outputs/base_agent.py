"""
Investment Analysis System - BaseAgent Framework

Provides the abstract base class, error types, LLM integration layer,
and common utilities shared by all specialized agents.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from models import AgentOutput

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Error Types
# ---------------------------------------------------------------------------

class AgentExecutionError(Exception):
    """Raised when an agent fails to execute properly."""

    def __init__(
        self,
        agent_name: str,
        message: str,
        original_error: Optional[Exception] = None,
    ):
        self.agent_name = agent_name
        self.original_error = original_error
        super().__init__(f"Agent '{agent_name}' execution failed: {message}")


class AgentTimeoutError(AgentExecutionError):
    """Raised when an agent exceeds its execution time limit."""
    pass


class AgentValidationError(AgentExecutionError):
    """Raised when agent output fails schema validation."""
    pass


# ---------------------------------------------------------------------------
# BaseAgent (abstract)
# ---------------------------------------------------------------------------

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the investment analysis system.

    Subclasses MUST set class-level ``name`` and ``description`` attributes
    and implement ``run(state: dict) -> AgentOutput``.

    Provides:
    - Standard prompt construction via ``build_prompt``
    - JSON response parsing via ``parse_response``
    - Confidence and citation helpers
    - Structured error handling with fallback outputs
    """

    name: str = "base_agent"
    description: str = "Base agent"

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"agent.{self.name}")

    # --- Abstract interface ---

    @abstractmethod
    def run(self, state: dict) -> AgentOutput:
        """
        Execute the agent and return a structured :class:`AgentOutput`.

        Parameters
        ----------
        state : dict
            The current workflow state containing all context.

        Returns
        -------
        AgentOutput
            Standardized output with results, confidence, and citations.
        """
        ...

    # --- Prompt helpers ---

    def build_prompt(self, state: dict) -> str:
        """
        Construct the full prompt from the current state.

        Override in subclasses for domain-specific prompt engineering.
        """
        return f"""
[ROLE]
You are {self.name}: {self.description}

[CONTEXT]
{self._format_context(state)}

[TASK]
{self._get_task_description()}

[OUTPUT FORMAT]
{self._get_output_format()}

[CONSTRAINTS]
{self._get_constraints()}
"""

    # --- Parsing ---

    def parse_response(self, response: str) -> dict:
        """
        Parse an LLM response string into a dict.

        Attempts to extract the first JSON object found. Falls back to
        wrapping the raw text in a dict.
        """
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            return {"raw_output": response, "parsed": False}
        except json.JSONDecodeError as exc:
            self.logger.warning("Failed to parse JSON from LLM response: %s", exc)
            return {"raw_output": response, "parse_error": str(exc)}

    # --- Confidence ---

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """
        Compute confidence score. Override for custom logic.

        Default implementation uses the ``confidence`` key inside *result*
        if present, otherwise returns 0.5.
        """
        if "confidence" in result:
            try:
                return max(0.0, min(1.0, float(result["confidence"])))
            except (TypeError, ValueError):
                pass
        return 0.5

    # --- Citations ---

    def _extract_citations(self, result: dict, state: dict) -> List[str]:
        """Collect citations from both the result and the state."""
        citations: List[str] = []
        for key in ("citations", "sources"):
            if key in result and isinstance(result[key], list):
                citations.extend(result[key])
        if "data_sources" in state and isinstance(state["data_sources"], list):
            citations.extend(state["data_sources"])
        # Deduplicate while preserving order
        seen: set = set()
        unique: List[str] = []
        for c in citations:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        return unique

    # --- Output creation ---

    def _create_output(
        self,
        result: dict,
        confidence: float,
        citations: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
        status: str = "success",
        error: Optional[str] = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            result=result,
            confidence=confidence,
            citations=citations or [],
            metadata=metadata or {},
            timestamp=datetime.now(),
            status=status,
            error=error,
        )

    # --- Fallback on error ---

    def _create_error_output(
        self, error: Exception, fallback_result: Optional[dict] = None
    ) -> AgentOutput:
        """Return a zero-confidence output when execution fails."""
        self.logger.error("Agent %s failed: %s", self.name, error, exc_info=True)
        return self._create_output(
            result=fallback_result or {"error": str(error)},
            confidence=0.0,
            citations=[],
            metadata={"error_type": type(error).__name__},
            status="failed",
            error=str(error),
        )

    # --- Template hooks (override in subclasses) ---

    def _get_task_description(self) -> str:
        return f"Perform {self.name} analysis"

    def _get_output_format(self) -> str:
        return '{"result": {}, "confidence": 0.0}'

    def _get_constraints(self) -> str:
        return "- Be accurate and cite sources\n- Provide confidence score between 0 and 1"

    def _get_expected_output_keys(self) -> List[str]:
        """Keys expected in the parsed result; used for confidence calc."""
        return []

    def _format_context(self, state: dict) -> str:
        """Format state into a readable context block for prompt injection."""
        parts: List[str] = []
        skip_keys = {"agent_outputs", "final_report", "risk_assessment"}
        for key, value in state.items():
            if key in skip_keys:
                continue
            if isinstance(value, (dict, list)):
                try:
                    formatted = json.dumps(value, indent=2, default=str, ensure_ascii=False)
                    # Truncate very large payloads
                    if len(formatted) > 3000:
                        formatted = formatted[:3000] + "\n... (truncated)"
                    parts.append(f"### {key}\n{formatted}")
                except (TypeError, ValueError):
                    parts.append(f"{key}: {value}")
            else:
                parts.append(f"- {key}: {value}")
        return "\n".join(parts) if parts else "No additional context"


# ---------------------------------------------------------------------------
# LLM-Powered Agent (adds LLM call + retry logic)
# ---------------------------------------------------------------------------

class LLMAgent(BaseAgent):
    """
    Base class for agents that delegate analysis to an LLM.

    Adds:
    - LLM client initialization (OpenAI-compatible API)
    - Retry with exponential backoff
    - Token counting estimate
    - System prompt generation

    Subclasses should override ``build_prompt`` and the ``_get_*`` hooks.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 4000,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ) -> None:
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay

        # Lazy-initialize the LLM client to avoid import errors when the
        # library is not installed (e.g. during testing with mocks).
        self._api_key = api_key
        self._base_url = base_url
        self._client = None

    @property
    def client(self):
        """Lazy-initialized OpenAI-compatible client."""
        if self._client is None:
            try:
                from openai import OpenAI

                kwargs: Dict[str, Any] = {}
                if self._api_key:
                    kwargs["api_key"] = self._api_key
                if self._base_url:
                    kwargs["base_url"] = self._base_url
                self._client = OpenAI(**kwargs)
            except ImportError:
                raise ImportError(
                    "The 'openai' package is required for LLM-powered agents. "
                    "Install it with: pip install openai"
                )
        return self._client

    # --- Main execution ---

    def run(self, state: dict) -> AgentOutput:
        """Build prompt, call LLM, parse and validate output."""
        try:
            prompt = self.build_prompt(state)
            self.logger.info("Agent %s calling LLM (%s)...", self.name, self.model)

            response_text = self._call_llm(prompt)
            parsed = self.parse_response(response_text)

            confidence = self._calculate_confidence(parsed, state)
            citations = self._extract_citations(parsed, state)

            return self._create_output(
                result=parsed,
                confidence=confidence,
                citations=citations,
                metadata={
                    "model": self.model,
                    "prompt_tokens_estimate": self._estimate_tokens(prompt),
                    "response_tokens_estimate": self._estimate_tokens(response_text),
                },
            )

        except Exception as exc:
            self.logger.error("Agent %s execution error: %s", self.name, exc)
            return self._create_error_output(exc)

    # --- LLM call with retry ---

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM API with exponential backoff retry."""
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return response.choices[0].message.content
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    delay = self.retry_base_delay * (2 ** attempt)
                    self.logger.warning(
                        "LLM call attempt %d/%d failed (%s), retrying in %.1fs...",
                        attempt + 1,
                        self.max_retries,
                        exc,
                        delay,
                    )
                    time.sleep(delay)

        raise AgentExecutionError(
            self.name,
            f"LLM call failed after {self.max_retries} attempts",
            last_error,
        )

    def _get_system_prompt(self) -> str:
        return (
            f"You are {self.name}, {self.description}. "
            "Provide accurate, well-structured analysis. "
            "Always respond with valid JSON as specified in the output format."
        )

    # --- Token estimation ---

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token count estimate (words * 1.3)."""
        return int(len(text.split()) * 1.3)

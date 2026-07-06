"""
Base Agent Framework
====================
Provides ``BaseAgent`` (abstract) and ``AgentOutput`` (Pydantic model)
that every specialist agent inherits / produces.  Follows the skill's
"BaseAgent Template" pattern.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator

# ---------------------------------------------------------------------------
# Exceptions
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
    """Raised when an agent exceeds its time limit."""


class AgentValidationError(AgentExecutionError):
    """Raised when agent output fails validation."""


# ---------------------------------------------------------------------------
# Agent output model
# ---------------------------------------------------------------------------

class AgentOutput(BaseModel):
    """
    Standard output contract for every agent.

    Attributes
    ----------
    agent_name : str
        Identifier of the producing agent.
    result : dict[str, Any]
        Domain-specific payload.
    confidence : float
        0.0 - 1.0 confidence score.
    citations : list[str]
        Sources / references supporting the result.
    metadata : dict[str, Any]
        Arbitrary metadata (model used, token counts, latency, ...).
    timestamp : datetime
        When the output was produced.
    """

    agent_name: str
    result: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0, description="0.0-1.0")
    citations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # -- validators ---------------------------------------------------------
    @validator("confidence")
    def _check_confidence(cls, v: float) -> float:  # noqa: N805
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v

    @validator("citations")
    def _warn_empty_citations(cls, v: list[str]) -> list[str]:  # noqa: N805
        if not v:
            logging.getLogger(__name__).warning(
                "No citations provided - results may not be verifiable"
            )
        return v


# ---------------------------------------------------------------------------
# Abstract base agent
# ---------------------------------------------------------------------------

class BaseAgent(ABC):
    """
    Every agent in the system must subclass ``BaseAgent`` and implement:

    * ``name``          -- short identifier (e.g. ``"classifier_agent"``)
    * ``description``   -- one-liner about the agent's expertise
    * ``run(state)``    -- main execution entry-point

    The base class provides:
    * ``build_prompt``      -- composes a CRAFT-structured prompt
    * ``parse_response``    -- extracts JSON from LLM output
    * ``_create_output``    -- helper to build ``AgentOutput``
    * ``_format_context``   -- serialises state for prompt injection
    """

    name: str
    description: str

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"agent.{self.name}")

    # -- abstract interface -------------------------------------------------

    @abstractmethod
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent and return a *partial state update*.

        The caller merges this update into the workflow state.

        Parameters
        ----------
        state : dict
            Immutable snapshot of the current workflow state.

        Returns
        -------
        dict
            Keys to merge back into the state.
        """
        ...

    # -- prompt helpers -----------------------------------------------------

    def build_prompt(self, state: dict[str, Any]) -> str:
        """
        Compose a structured prompt following the CRAFT framework.

        Override ``_get_task_description``, ``_get_output_format``,
        ``_get_constraints``, or this method entirely for custom behaviour.
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

    # -- response parsing ---------------------------------------------------

    def parse_response(self, response: str) -> dict[str, Any]:
        """
        Best-effort JSON extraction from an LLM response string.

        Returns ``{"raw_output": response, "parsed": False}`` when no valid
        JSON object can be found.
        """
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except json.JSONDecodeError as exc:
            self.logger.warning("JSON decode failed: %s", exc)
            return {"raw_output": response, "parse_error": str(exc)}

        return {"raw_output": response, "parsed": False}

    # -- override hooks -----------------------------------------------------

    def _get_task_description(self) -> str:
        return f"Perform {self.name} analysis."

    def _get_output_format(self) -> str:
        return '{"result": {}, "confidence": 0.0}'

    def _get_constraints(self) -> str:
        return (
            "- Be accurate and cite sources.\n"
            "- Provide a confidence score between 0.0 and 1.0.\n"
            "- Do not fabricate information."
        )

    # -- utility helpers ----------------------------------------------------

    def _format_context(self, state: dict[str, Any]) -> str:
        """Serialise state (minus agent_outputs / final_response) for prompts."""
        SKIP = {"agent_outputs", "final_response", "errors"}
        parts = [
            f"{key}: {value}"
            for key, value in state.items()
            if key not in SKIP
        ]
        return "\n".join(parts) if parts else "No additional context."

    def _create_output(
        self,
        result: dict[str, Any],
        confidence: float,
        citations: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            result=result,
            confidence=confidence,
            citations=citations or [],
            metadata=metadata or {},
        )

    # -- LLM call with retry (override for your provider) -------------------

    def call_llm(
        self,
        prompt: str,
        *,
        model: str = "gpt-4",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
    ) -> str:
        """
        Placeholder LLM call with exponential-backoff retry.

        In production, replace the body with your LLM client
        (OpenAI, Anthropic, etc.).
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(max_retries):
            try:
                # --- Replace this block with your LLM client ---
                # Example with OpenAI:
                #   from openai import OpenAI
                #   client = OpenAI()
                #   resp = client.chat.completions.create(
                #       model=model, messages=messages,
                #       temperature=temperature, max_tokens=max_tokens,
                #   )
                #   return resp.choices[0].message.content
                #
                # For now, return a stub so the code is runnable without an API key:
                raise NotImplementedError(
                    "call_llm is a placeholder -- wire up your LLM client here."
                )
            except NotImplementedError:
                raise
            except Exception as exc:
                if attempt == max_retries - 1:
                    raise AgentExecutionError(self.name, str(exc), exc)
                delay = 2 ** attempt
                self.logger.warning(
                    "LLM call attempt %d failed (%s), retrying in %ds ...",
                    attempt + 1,
                    exc,
                    delay,
                )
                time.sleep(delay)
        return ""  # unreachable, keeps type-checkers happy

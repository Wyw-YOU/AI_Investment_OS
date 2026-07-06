"""
BaseAgent framework for the Academic Research System.

Provides:
    - BaseAgent abstract class with standard interface
    - LLMAgent base class with LLM integration, prompt construction,
      response parsing, confidence calculation, and citation extraction
    - Error types for agent failures

Follows the multi-agent-developer skill's BaseAgent template pattern.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import json
import logging
import time

from models import AgentOutput

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error Types
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
    """Raised when agent output fails validation."""
    pass


# ---------------------------------------------------------------------------
# Base Agent
# ---------------------------------------------------------------------------

class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    All agents must define:
        - name: str -- unique identifier
        - description: str -- what the agent does
        - run(state: dict) -> AgentOutput -- main execution method

    Override build_prompt() and parse_response() for custom behaviour.
    """

    name: str = "base_agent"
    description: str = "Base agent"

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"agent.{self.name}")

    @abstractmethod
    def run(self, state: dict) -> AgentOutput:
        """Execute agent logic and return structured output."""
        ...

    def build_prompt(self, state: dict) -> str:
        """
        Construct prompt from current state.

        Default implementation follows the CRAFT framework
        (Context, Role, Action, Format, Tone).
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

    def parse_response(self, response: str) -> dict:
        """
        Parse LLM response into structured dict.

        Default: attempts JSON extraction; falls back to raw text wrapper.
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

    # -- Template hooks (override in subclasses) ----------------------------

    def _get_task_description(self) -> str:
        return f"Perform {self.name} analysis."

    def _get_output_format(self) -> str:
        return '{"result": {}, "confidence": 0.0}'

    def _get_constraints(self) -> str:
        return "- Be accurate and cite sources.\n- Provide a confidence score between 0 and 1."

    def _format_context(self, state: dict) -> str:
        """Format state data for prompt injection."""
        parts = []
        for key, value in state.items():
            if key in ("agent_outputs",):
                continue
            # Truncate very long values for prompt brevity
            text = str(value)
            if len(text) > 3000:
                text = text[:3000] + "... [truncated]"
            parts.append(f"**{key}**: {text}")
        return "\n\n".join(parts) if parts else "No additional context."

    def _create_output(
        self,
        result: dict,
        confidence: float,
        citations: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ) -> AgentOutput:
        """Helper to construct a standardised AgentOutput."""
        return AgentOutput(
            agent_name=self.name,
            result=result,
            confidence=confidence,
            citations=citations or [],
            metadata=metadata or {},
        )


# ---------------------------------------------------------------------------
# LLM-Powered Agent
# ---------------------------------------------------------------------------

class LLMAgent(BaseAgent):
    """
    Base class for agents that use an LLM for analysis.

    Features:
        - Configurable model, temperature, max_tokens
        - Automatic prompt construction via build_prompt()
        - Retry with exponential backoff on API errors
        - Confidence calculation from result completeness
        - Citation extraction from structured output
        - Token counting for cost monitoring

    Subclasses override:
        - _get_system_prompt() for system-level instructions
        - _get_task_description() for the specific task
        - _get_output_format() for JSON schema
        - _calculate_confidence() for custom confidence logic
    """

    def __init__(
        self,
        model: str = "gpt-4",
        temperature: float = 0.3,
        max_tokens: int = 4000,
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._api_key = api_key

        # Lazy-initialise the LLM client
        self._client = None

    def _get_client(self):
        """Lazy-initialise the OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self._api_key)
            except ImportError:
                raise ImportError(
                    "The 'openai' package is required. Install with: pip install openai"
                )
        return self._client

    # -- Main execution -----------------------------------------------------

    def run(self, state: dict) -> AgentOutput:
        """Execute LLM-powered analysis with full error handling."""
        start_time = time.time()
        try:
            prompt = self.build_prompt(state)
            response = self._call_llm(prompt)
            parsed = self.parse_response(response)

            confidence = self._calculate_confidence(parsed, state)
            citations = self._extract_citations(parsed, state)

            elapsed = time.time() - start_time
            return self._create_output(
                result=parsed,
                confidence=confidence,
                citations=citations,
                metadata={
                    "model": self.model,
                    "temperature": self.temperature,
                    "prompt_length": len(prompt),
                    "response_length": len(response),
                    "elapsed_seconds": round(elapsed, 2),
                },
            )
        except AgentExecutionError:
            raise
        except Exception as exc:
            self.logger.error("LLM execution failed for %s: %s", self.name, exc)
            raise AgentExecutionError(self.name, str(exc), exc) from exc

    # -- LLM call with retry ------------------------------------------------

    def _call_llm(self, prompt: str) -> str:
        """Call LLM with exponential backoff (up to 3 attempts)."""
        client = self._get_client()
        system_prompt = self._get_system_prompt()

        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return response.choices[0].message.content
            except Exception as exc:
                if attempt == 2:
                    raise AgentExecutionError(
                        self.name,
                        f"LLM call failed after 3 attempts: {exc}",
                        exc,
                    ) from exc
                delay = 2 ** attempt
                self.logger.warning(
                    "Attempt %d/3 for %s failed, retrying in %ds: %s",
                    attempt + 1, self.name, delay, exc,
                )
                time.sleep(delay)

        # Unreachable, but satisfies type checkers
        raise AgentExecutionError(self.name, "LLM call failed after retries")

    # -- Prompt helpers ------------------------------------------------------

    def _get_system_prompt(self) -> str:
        """System-level prompt.  Override for domain-specific instructions."""
        return (
            f"You are {self.name}, {self.description}. "
            "Provide accurate, well-structured, and well-sourced analysis. "
            "Always respond in the exact JSON format requested."
        )

    # -- Confidence & citation helpers --------------------------------------

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """
        Calculate confidence based on result completeness.

        Override for domain-specific logic.
        """
        if "confidence" in result:
            try:
                return min(max(float(result["confidence"]), 0.0), 1.0)
            except (ValueError, TypeError):
                pass

        expected = self._get_expected_output_keys()
        if expected:
            present = sum(1 for k in expected if k in result)
            return round(present / len(expected), 2)
        return 0.5

    def _extract_citations(self, result: dict, state: dict) -> list[str]:
        """Extract citations from result and state."""
        citations: list[str] = []
        for key in ("citations", "sources", "references"):
            if key in result and isinstance(result[key], list):
                citations.extend(str(c) for c in result[key])
        if "paper_filenames" in state:
            citations.extend(state["paper_filenames"])
        return list(dict.fromkeys(citations))  # dedupe, preserve order

    def _get_expected_output_keys(self) -> list[str]:
        """Override to list expected top-level keys in the JSON output."""
        return []

    def _get_output_format(self) -> str:
        """Override to provide the exact JSON schema expected."""
        return '{"result": {}, "confidence": 0.0}'

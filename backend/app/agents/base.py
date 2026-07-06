import json
import logging
from abc import ABC, abstractmethod

from app.agents.models import AgentOutput

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    async def run(self, state: dict) -> AgentOutput:
        pass

    def build_prompt(self, state: dict) -> str:
        return (
            f"{self._get_role()}\n\n"
            f"{self._format_context(state)}\n\n"
            f"{self._get_task_description()}\n\n"
            f"{self._get_output_format()}\n\n"
            f"{self._get_constraints()}"
        )

    def _get_role(self) -> str:
        return f"[ROLE]\nYou are {self.description}."

    def _format_context(self, state: dict) -> str:
        parts = ["[CONTEXT]"]
        if state.get("stock_code"):
            parts.append(f"Stock: {state['stock_code']} ({state.get('stock_name', '')})")
        for key in ["market_data", "financial_data", "news_data", "indicators", "agent_outputs"]:
            data = state.get(key)
            if data:
                parts.append(f"\n## {key}:\n{json.dumps(data, ensure_ascii=False, indent=2)[:3000]}")
        return "\n".join(parts)

    def _get_task_description(self) -> str:
        return "[TASK]\nAnalyze the provided data and produce structured output."

    def _get_output_format(self) -> str:
        return '[OUTPUT FORMAT]\nRespond with a single JSON object. Wrap in ```json``` if needed.'

    def _get_constraints(self) -> str:
        return (
            "[CONSTRAINTS]\n"
            "- Base analysis only on provided data\n"
            "- Cite specific numbers\n"
            "- Provide confidence 0.0-1.0\n"
            "- Respond in Chinese for text, English for JSON keys"
        )

    def parse_response(self, response: str) -> dict:
        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_response": response, "parse_error": True}

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        if result.get("parse_error"):
            return 0.1
        expected_keys = self._get_expected_output_keys()
        if not expected_keys:
            return 0.7
        present = sum(1 for k in expected_keys if k in result and result[k])
        return round(min(1.0, present / len(expected_keys) * 0.9 + 0.1), 2)

    def _extract_citations(self, result: dict, state: dict) -> list[str]:
        citations = result.get("citations", [])
        if state.get("stock_code"):
            citations.append(f"Stock data: {state['stock_code']}")
        return list(set(citations))

    def _get_expected_output_keys(self) -> list[str]:
        return []

    def _create_output(self, result: dict, state: dict) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            result=result,
            confidence=self._calculate_confidence(result, state),
            citations=self._extract_citations(result, state),
        )

    def _create_error_output(self, error: str) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            result={"error": error},
            confidence=0.0,
        )


class LLMAgent(BaseAgent):
    def __init__(self, temperature: float = 0.3, max_tokens: int = 2000):
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def run(self, state: dict) -> AgentOutput:
        try:
            prompt = self.build_prompt(state)
            from app.services.llm_adapter import get_llm
            llm = get_llm()
            response = await llm.chat(
                system_prompt=self._get_role(),
                user_prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            result = self.parse_response(response)
            return self._create_output(result, state)
        except Exception as e:
            logger.error(f"Agent {self.name} failed: {e}")
            return self._create_error_output(str(e))

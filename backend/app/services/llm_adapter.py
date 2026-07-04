"""Unified LLM adapter with retry and token tracking."""
import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LLMAdapter:
    """Unified LLM adapter supporting any OpenAI-compatible provider.

    Works with OpenAI, DeepSeek, Qwen (通义千问), MiMo, Moonshot, etc.
    Just change base_url and api_key to switch providers.
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        max_tokens: int = 2000,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._client = None
        self._total_tokens = 0
        self._total_calls = 0

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: str = "You are a financial analysis AI assistant.",
        temperature: float = 0.3,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Generate LLM response with retry logic."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        return self._call_with_retry(messages, temperature, response_format)

    def generate_json(
        self,
        prompt: str,
        system_prompt: str = "You are a financial analysis AI. Respond in valid JSON.",
        temperature: float = 0.2,
    ) -> Dict:
        """Generate and parse JSON response."""
        result = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        content = result.get("content", "{}")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"LLM returned invalid JSON, attempting extraction: {content[:200]}")
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return {}

    def _call_with_retry(
        self,
        messages: list,
        temperature: float,
        response_format: Optional[Dict],
    ) -> Dict[str, Any]:
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                client = self._get_client()

                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": self.max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = client.chat.completions.create(**kwargs)
                latency_ms = int((time.time() - start_time) * 1000)

                usage = response.usage
                tokens = usage.total_tokens if usage else 0
                self._total_tokens += tokens
                self._total_calls += 1

                return {
                    "content": response.choices[0].message.content,
                    "tokens": tokens,
                    "latency_ms": latency_ms,
                    "model": self.model,
                }

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"LLM call attempt {attempt+1} failed, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"LLM call failed after {self.max_retries} retries: {e}")

        return {
            "content": "",
            "tokens": 0,
            "latency_ms": 0,
            "model": self.model,
            "error": str(last_error),
        }

    @property
    def stats(self) -> Dict:
        return {
            "total_calls": self._total_calls,
            "total_tokens": self._total_tokens,
            "model": self.model,
        }

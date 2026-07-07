"""
LLM 适配层：统一封装 OpenAI 兼容 API（DeepSeek/MiMo 等）。

使用 AsyncOpenAI 避免阻塞 FastAPI 事件循环。
chat_json 自动从 LLM 响应中提取 JSON（处理 markdown 代码块包裹的情况）。
全局单例 llm_adapter 通过 get_llm() 获取，延迟初始化。
"""

import asyncio
import json
import logging

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMAdapter:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
        self.model = settings.llm_model

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> dict:
        raw = await self.chat(system_prompt, user_prompt, temperature, max_tokens)
        # Extract JSON from response (handles markdown code blocks)
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_response": raw, "parse_error": True}


llm_adapter: LLMAdapter | None = None


def get_llm() -> LLMAdapter:
    global llm_adapter
    if llm_adapter is None:
        llm_adapter = LLMAdapter()
    return llm_adapter

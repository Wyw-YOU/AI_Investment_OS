from app.config import settings
from app.services.llm_adapter import LLMAdapter

print(f"LLM Provider: {settings.llm_base_url}")
print(f"Model: {settings.llm_model}")

adapter = LLMAdapter(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    model=settings.llm_model,
)

result = adapter.generate("用一句话介绍贵州茅台这只股票。")
print(f"Tokens used: {result['tokens']}")
print(f"Latency: {result['latency_ms']}ms")
print(f"Response: {result['content'][:200]}")

if result.get("error"):
    print(f"ERROR: {result['error']}")
else:
    print("LLM connection OK!")
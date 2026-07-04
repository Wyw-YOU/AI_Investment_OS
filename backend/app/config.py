from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "AI Investment OS"
    debug: bool = False

    database_url: str = "sqlite:///./data/investment.db"

    redis_url: str = "redis://localhost:6379/0"

    # LLM Configuration (OpenAI-compatible interface)
    # Supports: OpenAI, DeepSeek, Qwen, MiMo, and any OpenAI-compatible provider
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_max_tokens: int = 2000

    cors_origins: List[str] = ["http://localhost:3000"]

    log_level: str = "INFO"
    log_format: str = "json"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

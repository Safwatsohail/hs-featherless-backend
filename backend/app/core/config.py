from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["dev", "test", "prod"] = Field(default="dev", alias="APP_ENV")
    app_name: str = Field(default="ai-orchestrator-backend", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_orchestrator",
        alias="DATABASE_URL",
    )

    master_key: str = Field(alias="MASTER_KEY")

    vector_backend: Literal["chroma", "memory"] = Field(default="chroma", alias="VECTOR_BACKEND")
    chroma_persist_dir: Path = Field(default=Path("./.chroma"), alias="CHROMA_PERSIST_DIR")
    short_term_max_messages: int = Field(default=20, alias="SHORT_TERM_MAX_MESSAGES")
    vector_top_k: int = Field(default=3, alias="VECTOR_TOP_K")

    default_llm_provider: Literal["openai", "anthropic", "openrouter"] = Field(
        default="openai", alias="DEFAULT_LLM_PROVIDER"
    )
    default_llm_model: str = Field(default="gpt-4.1-mini", alias="DEFAULT_LLM_MODEL")
    decision_llm_provider: Literal["openai", "anthropic", "openrouter"] | None = Field(
        default=None, alias="DECISION_LLM_PROVIDER"
    )
    decision_llm_model: str = Field(default="gpt-4.1-nano", alias="DECISION_LLM_MODEL")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    anthropic_base_url: str = Field(
        default="https://api.anthropic.com", alias="ANTHROPIC_BASE_URL"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )

    python_tool_timeout_seconds: int = Field(default=3, alias="PYTHON_TOOL_TIMEOUT_SECONDS")
    bash_tool_timeout_seconds: int = Field(default=10, alias="BASH_TOOL_TIMEOUT_SECONDS")
    http_tool_timeout_seconds: int = Field(default=15, alias="HTTP_TOOL_TIMEOUT_SECONDS")
    web_search_max_results: int = Field(default=5, alias="WEB_SEARCH_MAX_RESULTS")
    deep_search_max_pages: int = Field(default=3, alias="DEEP_SEARCH_MAX_PAGES")


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

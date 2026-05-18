"""
Multi-Agent BI Platform - Application Settings

Centralized configuration loaded from environment variables.
All cost controls and model routing config lives here.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # --- App ---
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="DEBUG", alias="LOG_LEVEL")
    run_jobs_inline: bool = Field(default=False, alias="RUN_JOBS_INLINE")

    # --- LLM Providers ---
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/agent_in",
        alias="DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/agent_in",
        alias="DATABASE_URL_SYNC",
    )

    # --- Redis ---
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # --- Observability ---
    langfuse_public_key: Optional[str] = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: Optional[str] = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", alias="LANGFUSE_BASE_URL")

    # --- Persistence ---
    database_ssl_mode: str = Field(default="disable", alias="DB_SSL_MODE")
    chroma_persist_dir: str = Field(default="./chroma_data", alias="CHROMA_PERSIST_DIR")

    # --- Cost Controls ---
    max_tokens_per_job: int = Field(default=100_000, alias="MAX_TOKENS_PER_JOB")
    max_dollars_per_job: float = Field(default=1.00, alias="MAX_DOLLARS_PER_JOB")
    max_agent_iterations: int = Field(default=10, alias="MAX_AGENT_ITERATIONS")

    # --- Security ---
    api_keys: list[str] = Field(default_factory=list, alias="API_KEYS")
    # API_KEYS should be comma-separated in .env: API_KEYS=key1,key2,key3
    # If empty, authentication is disabled (development mode)

    # --- Frontend ---
    frontend_url: str = Field(
        default="http://localhost:8501",
        alias="FRONTEND_URL",
        description="Frontend URL for CORS configuration"
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse comma-separated API keys from environment
        if isinstance(self.api_keys, str):
            self.api_keys = [k.strip() for k in self.api_keys.split(",") if k.strip()]


# Singleton instance
settings = Settings()

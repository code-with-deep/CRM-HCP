"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Healthcare CRM API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "production"] = "development"

    SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="Secret key for signing tokens and cryptographic operations.",
    )

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/crm_hcp",
        description="Async SQLAlchemy database URL.",
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/crm_hcp",
        description="Sync database URL used by Alembic migrations.",
    )

    GROQ_API_KEY: str = Field(
        default="",
        description="Groq API key for LLM integration.",
    )
    GROQ_MODEL_NAME: str = Field(
        default="llama-3.1-8b-instant",
        description=(
            "Primary Groq model. llama-3.1-8b-instant is fast and has separate "
            "rate limits from llama-3.3-70b-versatile."
        ),
    )
    GROQ_FALLBACK_MODEL_NAME: str = Field(
        default="llama-3.3-70b-versatile",
        description="Fallback Groq model when the primary model is unavailable.",
    )
    LLM_TEMPERATURE: float = Field(default=0.0, ge=0.0, le=2.0)
    LLM_TIMEOUT_SECONDS: int = Field(default=20, ge=5, le=120)
    LLM_MAX_TOKENS: int = Field(default=1024, ge=128, le=8192)
    LLM_MAX_VALIDATION_RETRIES: int = Field(default=1, ge=0, le=5)

    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins.",
    )

    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Parse comma-separated CORS origins from environment variables."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_development(self) -> bool:
        """Return True when running in development mode."""
        return self.DEBUG or self.ENVIRONMENT == "development"


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()

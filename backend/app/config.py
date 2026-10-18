# Application configuration: loads and validates environment variables and .env settings
# used across the backend, such as AI service URL, timeouts, and logging level.
from pathlib import Path

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_AI_TIMEOUT_SECONDS = 30.0
LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Settings(BaseSettings):
    app_name: str = "Spectroscopy assistant API"
    log_level: str = DEFAULT_LOG_LEVEL
    ai_base_url: AnyHttpUrl | None = None
    ai_timeout_seconds: float = Field(default=DEFAULT_AI_TIMEOUT_SECONDS, gt=0)

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        extra="ignore",
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return DEFAULT_LOG_LEVEL
        if not isinstance(value, str):
            return value
        normalized = value.strip().upper()
        if normalized not in LOG_LEVELS:
            allowed = ", ".join(sorted(LOG_LEVELS))
            raise ValueError(f"log_level must be one of: {allowed}")
        return normalized

    @field_validator("ai_base_url", mode="before")
    @classmethod
    def blank_base_url_is_unset(cls, value: object) -> object:
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    @field_validator("ai_timeout_seconds", mode="before")
    @classmethod
    def blank_timeout_uses_default(cls, value: object) -> object:
        if isinstance(value, str) and value.strip() == "":
            return DEFAULT_AI_TIMEOUT_SECONDS
        return value


def get_settings() -> Settings:
    return Settings()

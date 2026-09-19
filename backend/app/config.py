"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_PORT = 7777
DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://seven2u:seven2u@localhost:5432/seven2u"
)
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"


class Settings(BaseSettings):
    """Runtime configuration for the Seven2U backend.

    Attributes:
        database_url: SQLAlchemy async connection string.
        groq_api_key: Optional Groq API key for LLM insights.
        groq_model: Groq chat model used through Agno.
        port: HTTP port the server listens on.
        static_dir: Directory containing the compiled React SPA.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = DEFAULT_DATABASE_URL
    groq_api_key: str = ""
    groq_model: str = DEFAULT_GROQ_MODEL
    port: int = DEFAULT_PORT
    static_dir: str = "static"


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()

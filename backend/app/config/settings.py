"""Application settings loaded from environment / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI
    openai_api_key: str = ""
    realtime_model: str = "gpt-4o-realtime-preview"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5433/restaurant_ai"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # App
    restaurant_id: int = 1
    app_env: str = "development"
    log_level: str = "INFO"

    # RAG
    rag_similarity_threshold: float = 0.75
    rag_top_k: int = 3

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()

"""Configuración centralizada del agente MENTOR."""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración vía variables de entorno y .env."""

    # -- General --
    app_name: str = "Mentor"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # -- API --
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]
    jwt_secret: str = "change-this-secret"

    # -- LLM --
    llm_provider: str = "openai"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    max_tokens: int = 4096
    temperature: float = 0.7

    # -- Base de Datos --
    database_url: str = "sqlite+aiosqlite:///./mentor.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # -- Redis --
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600

    # -- Vector Store --
    vector_db_path: str = "./data/vectorstore"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # -- Integraciones --
    slack_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    escalation_webhook_url: Optional[str] = None

    # -- Supabase (Opcional) --
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    use_supabase: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Retorna la configuración cacheada (singleton)."""
    return Settings()

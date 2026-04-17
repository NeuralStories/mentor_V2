from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Mentor by EgeAI"
    APP_VERSION: str = "2.0.0"
    # Keep compatibility with existing DEBUG env var while standardizing on APP_DEBUG.
    APP_DEBUG: bool = Field(
        default=False,
        validation_alias=AliasChoices("APP_DEBUG", "DEBUG"),
    )
    
    # Supabase
    SUPABASE_URL: str  # URL del proyecto Supabase
    SUPABASE_KEY: str  # anon key
    SUPABASE_SERVICE_KEY: str  # service_role key (para operaciones admin)
    
    # LLM - Ollama (local, gratuito)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.1:8b"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2048
    
    # Embeddings - Ollama (local, gratuito)
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # ChromaDB (local, gratuito)
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100
    
    # Whisper (local, gratuito)
    WHISPER_MODEL: str = "base"  # tiny/base/small

    # OCR
    OCR_ENABLED: bool = False
    OCR_LANGUAGE: str = "spa"
    TESSERACT_CMD: str | None = None
    
    # RAG
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.65
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    
    # Learning
    AUTO_LEARN: bool = True
    LEARNING_MIN_CONFIDENCE: float = 0.75
    REQUIRE_VALIDATION: bool = True
    
    # Knowledge Base
    KNOWLEDGE_BASE_PATH: str = "./knowledge_base"
    
    @field_validator("APP_DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False

        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on", "debug", "dev", "development"}:
            return True
        if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
            return False
        return False

    @field_validator("OCR_ENABLED", mode="before")
    @classmethod
    def normalize_ocr_enabled(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False

        normalized = str(value).strip().lower()
        return normalized in {"1", "true", "yes", "on", "enabled"}

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()

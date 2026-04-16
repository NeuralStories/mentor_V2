from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "CarpinteroAI"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    
    # LLM - Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.1:8b"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2048
    
    # Embeddings
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100
    
    # Whisper
    WHISPER_MODEL: str = "base"
    
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

    # Configuración Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # Esto ignora las variables sobrantes de la versión anterior
        case_sensitive=False
    )

settings = Settings()

"""
Proveedor de LLM y Embeddings usando Ollama (local, gratuito).

Modelos usados:
- LLM: llama3.1:8b (principal)
- Embeddings: nomic-embed-text (para RAG)

Ambos se ejecutan localmente via Ollama.
"""
from langchain_core.language_models import BaseLLM, BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings, OllamaLLM
from core.config import settings
import httpx
import logging

logger = logging.getLogger(__name__)


class LLMProvider:
    """
    Gestiona las instancias de LLM y Embeddings.
    Singleton pattern para reutilizar conexiones.
    """
    
    _chat_llm: BaseChatModel = None
    _fast_llm: BaseLLM = None
    _embeddings: Embeddings = None
    
    @classmethod
    def get_chat_llm(cls) -> BaseChatModel:
        """LLM principal para conversación (ChatOllama)."""
        if cls._chat_llm is None:
            cls._chat_llm = ChatOllama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                num_predict=settings.LLM_MAX_TOKENS,
                num_ctx=4096,
                repeat_penalty=1.1,
            )
            logger.info(f"Chat LLM inicializado: {settings.LLM_MODEL}")
        return cls._chat_llm
    
    @classmethod
    def get_fast_llm(cls) -> BaseLLM:
        """LLM rápido para clasificación y extracción (Ollama directo)."""
        if cls._fast_llm is None:
            cls._fast_llm = OllamaLLM(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.LLM_MODEL,
                temperature=0.1,
                num_predict=512,
                num_ctx=2048,
            )
            logger.info(f"Fast LLM inicializado: {settings.LLM_MODEL}")
        return cls._fast_llm
    
    @classmethod
    def get_embeddings(cls) -> Embeddings:
        """Embeddings para RAG."""
        if cls._embeddings is None:
            cls._embeddings = OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.EMBEDDING_MODEL,
            )
            logger.info(f"Embeddings inicializados: {settings.EMBEDDING_MODEL}")
        return cls._embeddings
    
    @classmethod
    def check_ollama_health(cls) -> dict:
        """Verifica que Ollama está disponible y los modelos descargados."""
        result = {
            "ollama_running": False,
            "models_available": [],
            "models_needed": [settings.LLM_MODEL, settings.EMBEDDING_MODEL],
            "models_missing": [],
        }
        
        try:
            response = httpx.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                timeout=5.0
            )
            if response.status_code == 200:
                result["ollama_running"] = True
                data = response.json()
                available = [m["name"] for m in data.get("models", [])]
                result["models_available"] = available
                
                for needed in result["models_needed"]:
                    # Comprobar con y sin tag
                    found = any(
                        needed in m or needed.split(":")[0] in m 
                        for m in available
                    )
                    if not found:
                        result["models_missing"].append(needed)
        except Exception as e:
            logger.error(f"Ollama no disponible: {e}")
        
        return result
    
    @classmethod
    def pull_model(cls, model_name: str) -> bool:
        """Descarga un modelo en Ollama."""
        try:
            logger.info(f"Descargando modelo: {model_name}")
            response = httpx.post(
                f"{settings.OLLAMA_BASE_URL}/api/pull",
                json={"name": model_name},
                timeout=600.0,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error descargando {model_name}: {e}")
            return False
    
    @classmethod
    def ensure_models(cls):
        """Asegura que los modelos necesarios están disponibles."""
        health = cls.check_ollama_health()
        
        if not health["ollama_running"]:
            raise ConnectionError(
                f"Ollama no está corriendo en {settings.OLLAMA_BASE_URL}. "
                "Ejecuta: ollama serve"
            )
        
        for model in health["models_missing"]:
            logger.info(f"Modelo {model} no encontrado, descargando...")
            success = cls.pull_model(model)
            if success:
                logger.info(f"Modelo {model} descargado correctamente")
            else:
                raise RuntimeError(f"No se pudo descargar el modelo {model}")

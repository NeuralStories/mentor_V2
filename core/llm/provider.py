from langchain_community.chat_models import ChatOllama
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.language_models import BaseLLM, BaseChatModel
from langchain_core.embeddings import Embeddings
from core.config import settings
import httpx
import logging

logger = logging.getLogger(__name__)

class LLMProvider:
    """
    Gestiona las instancias de LLM y Embeddings usando Ollama local.
    Implementa el patrón Singleton para reutilizar conexiones.
    """
    
    _chat_llm: BaseChatModel = None
    _fast_llm: BaseLLM = None
    _embeddings: Embeddings = None
    
    @classmethod
    def get_chat_llm(cls) -> BaseChatModel:
        """LLM principal para conversación interactiva."""
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
        """LLM optimizado para tareas de procesamiento rápido (clasificación, extracción)."""
        if cls._fast_llm is None:
            cls._fast_llm = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.LLM_MODEL,
                temperature=0.1,
                num_predict=512,
                num_ctx=2048,
            )
            logger.info("Fast LLM inicializado")
        return cls._fast_llm
    
    @classmethod
    def get_embeddings(cls) -> Embeddings:
        """Modelo de embeddings para el sistema RAG."""
        if cls._embeddings is None:
            cls._embeddings = OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.EMBEDDING_MODEL,
            )
            logger.info(f"Embeddings inicializados: {settings.EMBEDDING_MODEL}")
        return cls._embeddings

    @classmethod
    def check_ollama(cls):
        """Verifica disponibilidad de Ollama y sus modelos."""
        try:
            response = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
        except:
            return False

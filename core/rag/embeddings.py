from core.llm.provider import LLMProvider
from core.config import settings
from typing import List
import logging

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """
    Motor de embeddings usando Ollama.
    Gestiona la creación de embeddings para el RAG.
    """
    
    def __init__(self):
        self.embeddings = LLMProvider.get_embeddings()
    
    def embed_text(self, text: str) -> List[float]:
        """Genera embedding para un texto."""
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return []
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para múltiples textos (batch)."""
        try:
            return self.embeddings.embed_documents(texts)
        except Exception as e:
            logger.error(f"Error generando embeddings batch: {e}")
            return [[] for _ in texts]
    
    def embed_query(self, query: str) -> List[float]:
        """Embedding para query de búsqueda. 
        Preprocesa añadiendo contexto de dominio."""
        # Añadir contexto de carpintería a la query
        enriched_query = f"Carpintería instalación puertas parquet: {query}"
        
        try:
            return self.embeddings.embed_query(enriched_query)
        except Exception as e:
            logger.error(f"Error generando embedding para query: {e}")
            return []
import os
import hashlib
from pathlib import Path
from typing import Dict, List
from core.rag.chunking import SmartChunker
from core.rag.retriever import RAGRetriever
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class KnowledgeIndexer:
    """Gestiona la alimentación de la base de conocimiento en el sistema RAG."""
    
    def __init__(self):
        self.chunker = SmartChunker()
        self.retriever = RAGRetriever()
        
    def index_all(self, base_path: str = None):
        """Indexa recursivamente toda la carpeta de conocimiento base."""
        path = Path(base_path or settings.KNOWLEDGE_BASE_PATH)
        if not path.exists():
            logger.error(f"Ruta de conocimiento no encontrada: {path}")
            return

        # Mapeo de subdirectorios a colecciones
        folders = {
            "procedimientos": "procedimientos",
            "materiales": "materiales",
            "problemas_soluciones": "problemas_soluciones"
        }

        for folder, col_name in folders.items():
            folder_path = path / folder
            if not folder_path.exists(): continue
            
            for file_path in folder_path.rglob("*.md"):
                self.index_file(file_path, col_name)

    def index_file(self, file_path: Path, collection: str):
        """Procesa e indexa un archivo individual."""
        try:
            content = file_path.read_text(encoding="utf-8")
            metadata = {
                "archivo": file_path.stem,
                "ruta": str(file_path.relative_to(settings.KNOWLEDGE_BASE_PATH)),
                "fuente": "manual_tecnico"
            }
            
            chunks = self.chunker.chunk_document(content, metadata)
            self.retriever.add_documents(collection, chunks)
            logger.info(f"Indexado {file_path.name} en {collection} ({len(chunks)} chunks)")
        except Exception as e:
            logger.error(f"Error indexando {file_path}: {e}")

    def index_learned_item(self, title: str, content: str, metadata: Dict):
        """Indexa un nuevo conocimiento extraído dinámicamente."""
        full_text = f"Aprendizaje: {title}\n{content}"
        chunk = {
            "content": content,
            "enriched_content": full_text,
            "metadata": {**metadata, "title": title, "fuente": "conversacion"}
        }
        self.retriever.add_documents("aprendido", [chunk])

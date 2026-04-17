from core.rag.chunking import SmartChunker
from core.rag.retriever import RAGRetriever
from core.config import settings
from pathlib import Path
from typing import Dict, Any
import logging
import hashlib

logger = logging.getLogger(__name__)


class KnowledgeIndexer:
    """
    Indexador que conecta chunking con retriever.
    Gestiona la indexación de toda la base de conocimiento.
    """

    def __init__(self):
        self.chunker = SmartChunker()
        self.retriever = RAGRetriever()

    def index_knowledge_base(self, base_path: str = None):
        if base_path is None:
            base_path = settings.KNOWLEDGE_BASE_PATH

        base_dir = Path(base_path)
        if not base_dir.exists():
            logger.warning(f"Directorio de conocimiento no existe: {base_path}")
            return

        folder_mapping = {
            "procedimientos": "procedimientos",
            "materiales": "materiales",
            "problemas_soluciones": "problemas_soluciones",
        }

        total_chunks = 0
        for folder, collection in folder_mapping.items():
            folder_path = base_dir / folder
            if folder_path.exists():
                logger.info(f"Indexando carpeta: {folder} -> colección: {collection}")
                for md_file in folder_path.rglob("*.md"):
                    chunks = self.index_single_file(str(md_file), collection)
                    total_chunks += chunks
            else:
                logger.warning(f"Carpeta no existe: {folder_path}")

        logger.info(f"Indexación completa: {total_chunks} chunks totales")

    def index_single_file(self, file_path: str, collection: str) -> int:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            path_obj = Path(file_path)
            metadata = {
                "file_path": str(path_obj),
                "file_name": path_obj.name,
                "category": self._extract_category_from_path(file_path),
                "source": "knowledge_base",
            }

            return self.index_text_content(
                content=content,
                collection=collection,
                metadata=metadata,
                source_name=path_obj.name,
            )
        except Exception as e:
            logger.error(f"Error indexando archivo {file_path}: {e}")
            return 0

    def index_text_content(
        self,
        content: str,
        collection: str,
        metadata: Dict[str, Any],
        source_name: str,
    ) -> int:
        try:
            normalized_metadata = {
                **metadata,
                "file_name": source_name,
                "source": metadata.get("source", "uploaded_document"),
            }

            chunks = self.chunker.chunk_document(content, normalized_metadata)
            if not chunks:
                return 0

            documents = []
            for i, chunk in enumerate(chunks):
                chunk_hash = hashlib.md5(chunk["enriched_content"].encode()).hexdigest()[:8]
                doc_id = f"{Path(source_name).stem}_chunk_{i}_{chunk_hash}"
                documents.append({
                    "id": doc_id,
                    "content": chunk["enriched_content"],
                    "metadata": chunk["metadata"],
                })

            self.retriever.add_documents_batch(collection, documents)
            logger.info(f"Contenido indexado: {source_name} -> {len(chunks)} chunks")
            return len(chunks)
        except Exception as e:
            logger.error(f"Error indexando contenido parseado {source_name}: {e}")
            return 0

    def index_learned_knowledge(self, content: str, metadata: Dict[str, Any]):
        try:
            doc_id = f"learned_{hashlib.md5(content.encode()).hexdigest()[:12]}"
            enriched_metadata = {
                **metadata,
                "source": "learned",
                "type": "aprendido",
            }

            self.retriever.add_document(
                collection="aprendido",
                content=content,
                metadata=enriched_metadata,
                doc_id=doc_id,
            )
        except Exception as e:
            logger.error(f"Error indexando conocimiento aprendido: {e}")

    def index_incident(self, description: str, solution: str, metadata: Dict[str, Any]):
        try:
            content = f"Problema: {description}\n\nSolución: {solution}"
            doc_id = f"incident_{hashlib.md5(content.encode()).hexdigest()[:12]}"
            enriched_metadata = {
                **metadata,
                "source": "incident",
                "type": "incidencia_resuelta",
                "has_solution": bool(solution),
            }

            self.retriever.add_document(
                collection="incidencias",
                content=content,
                metadata=enriched_metadata,
                doc_id=doc_id,
            )
        except Exception as e:
            logger.error(f"Error indexando incidencia: {e}")

    def _extract_category_from_path(self, file_path: str) -> str:
        path_lower = file_path.lower()
        if "puertas" in path_lower:
            return "puertas"
        if "parquet" in path_lower or "suelos" in path_lower:
            return "parquet"
        if "materiales" in path_lower:
            return "materiales"
        if "problemas" in path_lower:
            return "problemas"
        return "general"

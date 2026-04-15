from src.utils.logger import get_logger

logger = get_logger(__name__)

class RAGService:
    def __init__(self):
        logger.info("Initializing RAG Service proxy (ChromaDB Integration pending)...")
        
    def ingest_document(self, doc_id: str, title: str, content: str, metadata: dict) -> int:
        """
        Mock method for ChromaDB ingestion.
        Splits content into simple chunks and returns chunk count.
        """
        logger.info(f"RAG: Ingesting doc {doc_id} with title '{title}'...")
        chunks = len(content) // 500 + 1
        return chunks

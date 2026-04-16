from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from core.config import settings

class SmartChunker:
    """Fragmentación inteligente de documentos markdown para carpintería."""
    
    def __init__(self):
        # Primero dividimos por encabezados de Markdown
        self.md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "categoria"),
                ("##", "seccion"),
                ("###", "subseccion"),
            ]
        )
        
        # Luego subdividimos chunks grandes
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    
    def chunk_document(self, content: str, metadata: Dict) -> List[Dict]:
        """Divide un documento en fragmentos enriquecidos con contexto."""
        # 1. Split por estructura MD
        md_docs = self.md_splitter.split_text(content)
        
        final_chunks = []
        for doc in md_docs:
            # Combinamos metadata del archivo con la extraída de los headers
            combined_metadata = {**metadata, **doc.metadata}
            
            # 2. Split por tamaño si es necesario
            sub_chunks = self.text_splitter.split_text(doc.page_content)
            
            for i, chunk_text in enumerate(sub_chunks):
                chunk_data = {
                    "content": chunk_text,
                    "metadata": {**combined_metadata, "chunk_index": i},
                    "enriched_content": self._enrich(chunk_text, combined_metadata)
                }
                final_chunks.append(chunk_data)
        
        return final_chunks
    
    def _enrich(self, text: str, metadata: Dict) -> str:
        """Añade contexto técnico al texto para mejorar la recuperación semántica."""
        prefix = f"[Contexto: {metadata.get('categoria', 'General')} > {metadata.get('seccion', 'General')}]\n"
        return prefix + text

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SmartChunker:
    """
    Fragmentación inteligente de documentos markdown.
    Usa MarkdownHeaderTextSplitter para respetar estructura,
    luego RecursiveCharacterTextSplitter para chunks grandes.
    """
    
    def __init__(self):
        # Configurar headers para markdown
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"), 
            ("###", "Header 3"),
        ]
        
        # Configurar text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Entrada: contenido markdown + metadata del archivo
        Salida: lista de dicts con:
            - "content": texto del chunk
            - "enriched_content": texto enriquecido (para embedding)
            - "metadata": metadata del chunk
        """
        try:
            # Primero dividir por headers
            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=self.headers_to_split_on
            )
            
            # Obtener secciones
            sections = markdown_splitter.split_text(content)
            
            chunks = []
            for section in sections:
                # Para cada sección, crear chunks más pequeños
                section_content = section.page_content
                section_metadata = section.metadata
                
                if len(section_content) <= 512:
                    # Si la sección es pequeña, usarla directamente
                    enriched = self._enrich_chunk({
                        "content": section_content,
                        "metadata": {**metadata, **section_metadata}
                    })
                    chunks.append(enriched)
                else:
                    # Dividir en chunks más pequeños
                    sub_chunks = self.text_splitter.split_text(section_content)
                    for sub_chunk in sub_chunks:
                        enriched = self._enrich_chunk({
                            "content": sub_chunk,
                            "metadata": {**metadata, **section_metadata}
                        })
                        chunks.append(enriched)
            
            logger.info(f"Documento fragmentado en {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error fragmentando documento: {e}")
            # Fallback: dividir por caracteres simples
            sub_chunks = self.text_splitter.split_text(content)
            return [
                self._enrich_chunk({
                    "content": chunk,
                    "metadata": metadata
                }) for chunk in sub_chunks
            ]
    
    def _enrich_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Añade contexto al chunk para mejor búsqueda semántica."""
        content = chunk["content"]
        metadata = chunk["metadata"]
        
        # Construir contexto
        context_parts = []
        
        if "category" in metadata:
            context_parts.append(f"Categoría: {metadata['category']}")
        
        if "Header 1" in metadata:
            context_parts.append(f"Sección principal: {metadata['Header 1']}")
        
        if "Header 2" in metadata:
            context_parts.append(f"Sección: {metadata['Header 2']}")
        
        # Añadir tipo de documento
        if "file_path" in metadata:
            doc_type = self._infer_doc_type(metadata["file_path"])
            context_parts.append(f"Tipo: {doc_type}")
        
        # Crear enriched content
        context_str = ". ".join(context_parts)
        enriched_content = f"{context_str}\n\n{content}" if context_parts else content
        
        return {
            "content": content,
            "enriched_content": enriched_content,
            "metadata": metadata
        }
    
    def _infer_doc_type(self, file_path: str) -> str:
        """Infere el tipo de documento desde el path."""
        path_lower = file_path.lower()
        
        if "instalacion_puertas" in path_lower:
            return "instalación puertas"
        elif "instalacion_parquet" in path_lower:
            return "instalación parquet"
        elif "materiales" in path_lower:
            return "materiales"
        elif "problemas" in path_lower:
            return "problemas y soluciones"
        else:
            return "documentación técnica"
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
from core.config import settings
from core.llm.provider import LLMProvider
import logging

logger = logging.getLogger(__name__)

class RAGRetriever:
    """Motor de búsqueda semántica en ChromaDB."""
    
    def __init__(self):
        self.embeddings = LLMProvider.get_embeddings()
        self.client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        
        # Colecciones principales
        self.collections = {
            "procedimientos": self.client.get_or_create_collection("procedimientos"),
            "materiales": self.client.get_or_create_collection("materiales"),
            "problemas_soluciones": self.client.get_or_create_collection("problemas_soluciones"),
            "incidencias": self.client.get_or_create_collection("incidencias"),
            "aprendido": self.client.get_or_create_collection("aprendido"),
        }
    
    def search(
        self, 
        query: str, 
        collections: List[str] = None, 
        top_k: int = 5,
        min_similarity: float = 0.65
    ) -> List[Dict]:
        """Busca en las colecciones especificadas y devuelve los resultados más relevantes."""
        if not collections:
            collections = list(self.collections.keys())
            
        # Generar embedding de la consulta
        query_embedding = self.embeddings.embed_query(f"Consulta técnica de carpintería: {query}")
        
        results = []
        for col_name in collections:
            if col_name not in self.collections: continue
            
            col = self.collections[col_name]
            res = col.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            if res["documents"] and res["documents"][0]:
                for i in range(len(res["documents"][0])):
                    # Chroma usa distancias (menor es mejor), convertimos a similitud aprox.
                    sim = 1 - res["distances"][0][i]
                    if sim >= min_similarity:
                        results.append({
                            "content": res["documents"][0][i],
                            "metadata": res["metadatas"][0][i],
                            "similarity": sim,
                            "collection": col_name
                        })
        
        # Ordenar por similitud de mayor a menor
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def add_documents(self, collection_name: str, docs: List[Dict]):
        """Añade documentos a una colección específica."""
        if collection_name not in self.collections:
            self.collections[collection_name] = self.client.get_or_create_collection(collection_name)
        
        col = self.collections[collection_name]
        
        ids = [f"{d['metadata'].get('archivo', 'doc')}_{i}" for i, d in enumerate(docs)]
        contents = [d.get("enriched_content", d["content"]) for d in docs]
        metadatas = [d["metadata"] for d in docs]
        embeddings = self.embeddings.embed_documents(contents)
        
        col.upsert(
            ids=ids,
            documents=contents,
            embeddings=embeddings,
            metadatas=metadatas
        )

import chromadb
from chromadb.config import Settings
from core.rag.embeddings import EmbeddingEngine
from core.config import settings
from typing import List, Dict, Any, Optional
import logging
import hashlib

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Búsqueda semántica en ChromaDB.
    Gestiona colecciones y búsqueda vectorial.
    """
    
    def __init__(self):
        self.embedding_engine = EmbeddingEngine()
        
        # Conectar con ChromaDB en modo local persistente
        self.client = chromadb.PersistentClient(
            path="./chroma_db"  # Directorio local para persistencia
        )
        
        # Crear colecciones si no existen
        self.collections = {}
        collection_names = [
            "procedimientos", "problemas_soluciones", 
            "materiales", "incidencias", "aprendido"
        ]
        
        for name in collection_names:
            try:
                self.collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={"description": f"Colección {name} para Mentor by EgeAI"}
                )
                logger.info(f"Colección {name} lista")
            except Exception as e:
                logger.error(f"Error creando colección {name}: {e}")
    
    def search(
        self,
        query: str,
        collections: List[str] = None,  # None = todas
        top_k: int = 5,
        filters: Dict[str, Any] = None,
        min_similarity: float = 0.65,
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda semántica en una o más colecciones.
        Retorna lista de resultados ordenados por similitud:
        [
            {
                "content": "...",
                "metadata": {...},
                "similarity": 0.87,
                "collection": "procedimientos"
            }
        ]
        """
        if collections is None:
            collections = list(self.collections.keys())

        if min_similarity is None:
            min_similarity = settings.RAG_SIMILARITY_THRESHOLD
        
        all_results = []
        
        for coll_name in collections:
            if coll_name not in self.collections:
                continue
                
            collection = self.collections[coll_name]
            
            try:
                # Generar embedding para la query
                query_embedding = self.embedding_engine.embed_query(query)
                if not query_embedding:
                    continue
                
                # Buscar en la colección
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=filters,
                    include=['documents', 'metadatas', 'distances']
                )
                
                # Procesar resultados
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i]

                    # Chroma can return cosine-style distances (~0..2) or large L2 distances
                    # depending on collection configuration. Preserve ranking in both cases.
                    if distance <= 2:
                        similarity = max(0.0, 1 - distance)
                        passes_threshold = similarity >= min_similarity
                    else:
                        similarity = 1 / (1 + distance)
                        passes_threshold = True

                    if passes_threshold:
                        all_results.append({
                            "content": doc,
                            "metadata": results['metadatas'][0][i],
                            "similarity": similarity,
                            "collection": coll_name
                        })
                        
            except Exception as e:
                logger.error(f"Error buscando en colección {coll_name}: {e}")
        
        # Ordenar por similitud descendente
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        return all_results[:top_k]
    
    def add_document(self, collection: str, content: str, 
                     metadata: Dict[str, Any], doc_id: str = None):
        """Añade un documento a una colección."""
        if collection not in self.collections:
            logger.error(f"Colección {collection} no existe")
            return
        
        if doc_id is None:
            doc_id = hashlib.md5(content.encode()).hexdigest()
        
        try:
            # Generar embedding
            embedding = self.embedding_engine.embed_text(content)
            if not embedding:
                return
            
            # Añadir a colección
            self.collections[collection].add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Documento añadido a {collection}: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error añadiendo documento: {e}")
    
    def add_documents_batch(self, collection: str, 
                            documents: List[Dict[str, Any]]):
        """Añade múltiples documentos (más eficiente)."""
        if collection not in self.collections:
            logger.error(f"Colección {collection} no existe")
            return
        
        if not documents:
            return
        
        try:
            # Preparar datos
            contents = [doc['content'] for doc in documents]
            embeddings = self.embedding_engine.embed_texts(contents)
            metadatas = [doc.get('metadata', {}) for doc in documents]
            ids = [doc.get('id', hashlib.md5(doc['content'].encode()).hexdigest()) 
                   for doc in documents]
            
            # Filtrar embeddings válidos
            valid_indices = [i for i, emb in enumerate(embeddings) if emb]
            if not valid_indices:
                return
                
            embeddings = [embeddings[i] for i in valid_indices]
            contents = [contents[i] for i in valid_indices]
            metadatas = [metadatas[i] for i in valid_indices]
            ids = [ids[i] for i in valid_indices]
            
            # Añadir batch
            self.collections[collection].add(
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Batch añadido a {collection}: {len(valid_indices)} documentos")
            
        except Exception as e:
            logger.error(f"Error añadiendo batch: {e}")

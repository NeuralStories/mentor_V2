Análisis Completo del Repositorio y Propuesta de Rediseño
1. Análisis del Repositorio Actual (mentor_V2)
He revisado el repositorio. Vamos a ser directos:

Lo que tiene actualmente:
text

mentor_V2/
├── backend/          # FastAPI básico
├── frontend/         # Interfaz web simple
├── docker-compose.yml
└── README.md
Problemas fundamentales del repositorio actual:
Es un chatbot genérico - No tiene contexto de carpintería ni instalación
No tiene sistema de memoria - No aprende de conversaciones anteriores
No tiene RAG ni knowledge base - No puede consultar documentación técnica
No tiene captura de incidencias - No registra problemas ni soluciones
No tiene interacción por voz - Solo texto
No está pensado para obra - No funciona en condiciones reales
No tiene integración con ERP - Aislado
Arquitectura monolítica simple - No escala ni se adapta
Veredicto: Necesita un rediseño completo de arquitectura.

2. RAG vs Fine-tuning: Decisión Estratégica
Esta decisión es crítica y voy a ser muy específico:

Fine-tuning:
text

VENTAJAS:
- Respuestas más naturales en el dominio
- No necesita búsqueda en tiempo real
- Menor latencia

DESVENTAJAS FATALES PARA TU CASO:
- Estático: cada vez que un operario descubre algo nuevo, 
  hay que reentrenar
- Costoso en recursos (GPU para entrenar)
- No puede acceder a datos de proyectos específicos
- No puede consultar planos ni fichas técnicas
- El conocimiento queda "congelado" en el modelo
- No puedes rastrear de dónde viene una respuesta
RAG (Retrieval Augmented Generation):
text

VENTAJAS PARA TU CASO:
- Dinámico: añades conocimiento sin reentrenar
- Puede consultar fichas técnicas, planos, manuales
- Rastreable: sabes de dónde viene cada respuesta
- El operario reporta un problema → se indexa → 
  el siguiente operario ya tiene esa solución
- Conecta con ERP y datos de proyecto
- Más barato (solo embeddings, no entrenamiento)
- Open source al 100%

DESVENTAJAS:
- Requiere buena ingeniería de retrieval
- La calidad depende de cómo se indexa el conocimiento
Mi recomendación: RAG + Memoria Conversacional + Knowledge Graph
text

NO es solo RAG simple.

Es un sistema híbrido:

1. RAG para conocimiento técnico (manuales, procedimientos, fichas)
2. Memoria conversacional para aprender de cada interacción
3. Knowledge Graph para relaciones entre problemas y soluciones
4. Prompt engineering especializado (no fine-tuning) para 
   comportamiento de dominio
¿Por qué NO fine-tuning?
text

Escenario real:
- Lunes: Un instalador descubre que en los bloques de 
  construcción X, el premarco necesita calzar 3mm más
- Con fine-tuning: Esa información NO está disponible 
  hasta el próximo entrenamiento (días/semanas)
- Con RAG dinámico: Se indexa inmediatamente y el 
  siguiente instalador que pregunte ya tiene esa solución

ESO es lo que necesitas. Conocimiento vivo.
3. Arquitectura Completa Propuesta
text

┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                      │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  PWA Web │  │  Voz     │  │ WhatsApp │  │  Telegram  │  │
│  │  Móvil   │  │ Whisper  │  │  (futuro)│  │  (futuro)  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘  │
│       └──────────────┴──────────────┴──────────────┘         │
│                          │                                    │
└──────────────────────────┼────────────────────────────────────┘
                           │
┌──────────────────────────┼────────────────────────────────────┐
│                    CAPA DE ORQUESTACIÓN                       │
│                          │                                    │
│  ┌───────────────────────▼───────────────────────────┐       │
│  │              AGENTE PRINCIPAL                      │       │
│  │         (LangChain/LangGraph Agent)                │       │
│  │                                                    │       │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────────────┐    │       │
│  │  │ Router  │ │ Contexto │ │ Decision Engine │    │       │
│  │  │ Intent  │ │ Manager  │ │                 │    │       │
│  │  └─────────┘ └──────────┘ └─────────────────┘    │       │
│  └───────────────────────────────────────────────────┘       │
│                          │                                    │
│         ┌────────────────┼────────────────┐                  │
│         ▼                ▼                ▼                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐           │
│  │ Tool:    │    │ Tool:    │    │ Tool:        │           │
│  │ Consulta │    │ Diagnós- │    │ Registro     │           │
│  │ Técnica  │    │ tico     │    │ Incidencia   │           │
│  └──────────┘    └──────────┘    └──────────────┘           │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐           │
│  │ Tool:    │    │ Tool:    │    │ Tool:        │           │
│  │ Guía     │    │ Verifi-  │    │ Búsqueda    │           │
│  │ Paso a   │    │ cación   │    │ Proyectos   │           │
│  │ Paso     │    │ Preventiva│   │             │           │
│  └──────────┘    └──────────┘    └──────────────┘           │
└──────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼────────────────────────────────────┐
│                    CAPA DE CONOCIMIENTO                       │
│                          │                                    │
│  ┌───────────────────────▼───────────────────────────┐       │
│  │              RAG ENGINE                            │       │
│  │                                                    │       │
│  │  ┌─────────────┐  ┌──────────────────────────┐   │       │
│  │  │ Embeddings  │  │ Retrieval + Reranking    │   │       │
│  │  │ (local)     │  │                          │   │       │
│  │  └─────────────┘  └──────────────────────────┘   │       │
│  └───────────────────────────────────────────────────┘       │
│                          │                                    │
│         ┌────────────────┼────────────────┐                  │
│         ▼                ▼                ▼                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐           │
│  │ChromaDB/ │    │PostgreSQL│    │ Knowledge    │           │
│  │Qdrant    │    │          │    │ Graph        │           │
│  │(vectores)│    │(relacion)│    │ (Neo4j/libre)│           │
│  └──────────┘    └──────────┘    └──────────────┘           │
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │           MEMORIA Y APRENDIZAJE                   │       │
│  │                                                    │       │
│  │  Conversaciones → Extracción → Indexación         │       │
│  │  Incidencias → Clasificación → Base conocimiento  │       │
│  │  Soluciones → Validación → Procedimientos         │       │
│  └──────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼────────────────────────────────────┐
│                    CAPA DE INTEGRACIÓN                        │
│                          │                                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐           │
│  │ SimGEST  │    │ Ficheros │    │ Calendarios  │           │
│  │ API/DB   │    │ técnicos │    │              │           │
│  └──────────┘    └──────────┘    └──────────────┘           │
└──────────────────────────────────────────────────────────────┘
4. Estructura del Proyecto Rediseñado
text

carpintero_ai/
│
├── docker-compose.yml
├── .env.example
├── Makefile
├── README.md
│
├── docs/
│   ├── arquitectura.md
│   ├── guia_despliegue.md
│   └── guia_usuario.md
│
├── core/                          # Motor principal
│   ├── __init__.py
│   ├── config.py                  # Configuración centralizada
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── main_agent.py          # Agente orquestador
│   │   ├── router.py              # Clasificación de intenciones
│   │   ├── context_manager.py     # Gestión de contexto conversacional
│   │   └── prompts/
│   │       ├── system_prompt.py   # Prompt principal del agente
│   │       ├── carpintero_taller.py
│   │       ├── instalador_puertas.py
│   │       ├── instalador_parquet.py
│   │       ├── instalador_rodapies.py
│   │       └── encargado.py
│   │
│   ├── tools/                     # Herramientas del agente
│   │   ├── __init__.py
│   │   ├── consulta_tecnica.py    # Búsqueda en base de conocimiento
│   │   ├── diagnostico.py         # Análisis de problemas
│   │   ├── guia_instalacion.py    # Procedimientos paso a paso
│   │   ├── verificacion.py        # Validación preventiva
│   │   ├── registro_incidencia.py # Captura de incidencias
│   │   └── consulta_proyecto.py   # Datos de proyecto/ERP
│   │
│   ├── rag/                       # Motor RAG
│   │   ├── __init__.py
│   │   ├── embeddings.py          # Generación de embeddings
│   │   ├── retriever.py           # Búsqueda semántica
│   │   ├── reranker.py            # Re-ranking de resultados
│   │   ├── indexer.py             # Indexación de documentos
│   │   └── chunking.py            # Estrategia de fragmentación
│   │
│   ├── memory/                    # Sistema de memoria y aprendizaje
│   │   ├── __init__.py
│   │   ├── conversation_memory.py # Memoria conversacional
│   │   ├── knowledge_extractor.py # Extracción de conocimiento de chats
│   │   ├── learning_pipeline.py   # Pipeline de aprendizaje continuo
│   │   └── feedback_loop.py       # Retroalimentación del usuario
│   │
│   ├── knowledge/                 # Gestión del conocimiento
│   │   ├── __init__.py
│   │   ├── knowledge_graph.py     # Grafo de conocimiento
│   │   ├── problem_solution_db.py # Base de problemas-soluciones
│   │   ├── procedures_db.py       # Base de procedimientos
│   │   └── materials_db.py        # Base de materiales
│   │
│   └── llm/                       # Abstracción del LLM
│       ├── __init__.py
│       ├── provider.py            # Interfaz con Ollama/otros
│       └── models.py              # Configuración de modelos
│
├── api/                           # API REST
│   ├── __init__.py
│   ├── main.py                    # FastAPI app
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py                # Endpoint de conversación
│   │   ├── voice.py               # Endpoint de voz
│   │   ├── incidents.py           # Endpoint de incidencias
│   │   ├── knowledge.py           # Endpoint de gestión conocimiento
│   │   ├── projects.py            # Endpoint de proyectos
│   │   └── admin.py               # Administración
│   ├── middleware/
│   │   ├── auth.py
│   │   └── rate_limit.py
│   ├── schemas/
│   │   ├── chat.py
│   │   ├── incident.py
│   │   └── knowledge.py
│   └── dependencies.py
│
├── workers/                       # Procesos en background
│   ├── __init__.py
│   ├── knowledge_worker.py        # Procesamiento de conocimiento
│   ├── indexing_worker.py         # Indexación de documentos
│   └── learning_worker.py         # Aprendizaje de conversaciones
│
├── frontend/                      # PWA
│   ├── index.html
│   ├── manifest.json
│   ├── sw.js                      # Service Worker (offline)
│   ├── css/
│   │   └── app.css
│   ├── js/
│   │   ├── app.js
│   │   ├── chat.js
│   │   ├── voice.js               # Grabación de voz
│   │   ├── camera.js              # Captura de fotos
│   │   └── offline.js             # Gestión offline
│   └── assets/
│
├── knowledge_base/                # Conocimiento inicial (semilla)
│   ├── procedimientos/
│   │   ├── instalacion_puertas/
│   │   │   ├── premarco.md
│   │   │   ├── marco.md
│   │   │   ├── hoja.md
│   │   │   ├── bisagras.md
│   │   │   ├── cerraduras.md
│   │   │   └── problemas_comunes.md
│   │   ├── instalacion_parquet/
│   │   │   ├── preparacion_base.md
│   │   │   ├── colocacion_flotante.md
│   │   │   ├── colocacion_pegada.md
│   │   │   ├── juntas_dilatacion.md
│   │   │   └── problemas_comunes.md
│   │   ├── instalacion_rodapies/
│   │   │   ├── corte_inglete.md
│   │   │   ├── esquinas.md
│   │   │   └── problemas_comunes.md
│   │   └── carpinteria_taller/
│   │       ├── corte.md
│   │       ├── mecanizado.md
│   │       ├── ensamblado.md
│   │       └── tolerancias.md
│   ├── materiales/
│   │   ├── maderas.md
│   │   ├── tableros.md
│   │   ├── herrajes.md
│   │   └── acabados.md
│   ├── problemas_soluciones/
│   │   ├── puertas.md
│   │   ├── suelos.md
│   │   └── rodapies.md
│   └── checklists/
│       ├── antes_instalar_puerta.md
│       ├── antes_instalar_parquet.md
│       └── verificacion_final.md
│
├── scripts/
│   ├── seed_knowledge.py          # Carga conocimiento inicial
│   ├── backup_knowledge.py
│   └── export_incidents.py
│
├── tests/
│   ├── test_agent.py
│   ├── test_rag.py
│   ├── test_memory.py
│   ├── test_tools.py
│   └── test_api.py
│
└── infra/
    ├── docker/
    │   ├── Dockerfile.api
    │   ├── Dockerfile.worker
    │   └── Dockerfile.frontend
    └── nginx/
        └── nginx.conf
5. Implementación Detallada
5.1 Configuración Base
Python

# core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CarpinteroAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # LLM
    LLM_PROVIDER: str = "ollama"  # ollama, llamacpp
    LLM_MODEL: str = "llama3.1:8b"  # Modelo principal
    LLM_BASE_URL: str = "http://ollama:11434"
    LLM_TEMPERATURE: float = 0.3  # Bajo para respuestas precisas
    LLM_MAX_TOKENS: int = 2048
    
    # Embeddings
    EMBEDDING_MODEL: str = "nomic-embed-text"  # Via Ollama
    EMBEDDING_DIMENSION: int = 768
    
    # Vector Store
    VECTOR_STORE: str = "chromadb"  # chromadb o qdrant
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql://carpintero:carpintero@postgres:5432/carpintero_ai"
    
    # Redis (para caché y colas)
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Voice
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium
    WHISPER_LANGUAGE: str = "es"
    
    # Knowledge
    KNOWLEDGE_BASE_PATH: str = "./knowledge_base"
    
    # RAG
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    
    # Learning
    AUTO_LEARN_ENABLED: bool = True
    LEARNING_CONFIDENCE_THRESHOLD: float = 0.8
    LEARNING_REVIEW_REQUIRED: bool = True  # Requiere revisión humana
    
    # Security
    API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"


settings = Settings()
5.2 Abstracción del LLM
Python

# core/llm/provider.py
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.language_models import BaseLLM
from langchain_core.embeddings import Embeddings
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMProvider:
    """Proveedor de LLM y embeddings usando recursos locales gratuitos."""
    
    _llm_instance: BaseLLM = None
    _embedding_instance: Embeddings = None
    
    @classmethod
    def get_llm(cls) -> BaseLLM:
        if cls._llm_instance is None:
            logger.info(f"Inicializando LLM: {settings.LLM_MODEL}")
            cls._llm_instance = Ollama(
                base_url=settings.LLM_BASE_URL,
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                num_predict=settings.LLM_MAX_TOKENS,
                # Optimizaciones para respuesta rápida
                num_ctx=4096,
                repeat_penalty=1.1,
            )
        return cls._llm_instance
    
    @classmethod
    def get_embeddings(cls) -> Embeddings:
        if cls._embedding_instance is None:
            logger.info(f"Inicializando embeddings: {settings.EMBEDDING_MODEL}")
            cls._embedding_instance = OllamaEmbeddings(
                base_url=settings.LLM_BASE_URL,
                model=settings.EMBEDDING_MODEL,
            )
        return cls._embedding_instance
    
    @classmethod
    def get_fast_llm(cls) -> BaseLLM:
        """LLM más rápido para clasificación y tareas simples."""
        return Ollama(
            base_url=settings.LLM_BASE_URL,
            model="llama3.1:8b",  # Modelo más ligero
            temperature=0.1,
            num_predict=256,
            num_ctx=2048,
        )
5.3 Sistema RAG Completo
Python

# core/rag/chunking.py
from typing import List, Dict
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from core.config import settings
import re


class SmartChunker:
    """Fragmentación inteligente adaptada a documentación técnica de carpintería."""
    
    def __init__(self):
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "categoria"),
                ("##", "seccion"),
                ("###", "subseccion"),
            ]
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
    
    def chunk_document(self, content: str, metadata: Dict) -> List[Dict]:
        """Fragmenta un documento preservando contexto."""
        chunks = []
        
        # Primero dividir por estructura markdown
        md_chunks = self.markdown_splitter.split_text(content)
        
        for md_chunk in md_chunks:
            # Si el chunk es muy grande, subdividir
            if len(md_chunk.page_content) > settings.RAG_CHUNK_SIZE:
                sub_chunks = self.text_splitter.split_text(md_chunk.page_content)
                for i, sub_chunk in enumerate(sub_chunks):
                    chunk_metadata = {
                        **metadata,
                        **md_chunk.metadata,
                        "chunk_index": i,
                        "total_chunks": len(sub_chunks),
                    }
                    chunks.append({
                        "content": sub_chunk,
                        "metadata": chunk_metadata,
                    })
            else:
                chunks.append({
                    "content": md_chunk.page_content,
                    "metadata": {**metadata, **md_chunk.metadata},
                })
        
        # Enriquecer chunks con contexto
        for chunk in chunks:
            chunk["enriched_content"] = self._enrich_chunk(chunk)
        
        return chunks
    
    def _enrich_chunk(self, chunk: Dict) -> str:
        """Añade contexto al chunk para mejor búsqueda."""
        parts = []
        
        if "categoria" in chunk["metadata"]:
            parts.append(f"Categoría: {chunk['metadata']['categoria']}")
        if "seccion" in chunk["metadata"]:
            parts.append(f"Sección: {chunk['metadata']['seccion']}")
        if "tipo" in chunk["metadata"]:
            parts.append(f"Tipo: {chunk['metadata']['tipo']}")
        
        parts.append(chunk["content"])
        
        return "\n".join(parts)


# core/rag/embeddings.py
from typing import List
from core.llm.provider import LLMProvider
from core.config import settings
import numpy as np
import logging

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Motor de embeddings para el sistema RAG."""
    
    def __init__(self):
        self.embeddings = LLMProvider.get_embeddings()
    
    def embed_text(self, text: str) -> List[float]:
        """Genera embedding para un texto."""
        return self.embeddings.embed_query(text)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para múltiples textos."""
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, query: str) -> List[float]:
        """Genera embedding para una consulta (puede tener tratamiento especial)."""
        # Preprocesar la query para mejorar la búsqueda
        enhanced_query = self._enhance_query(query)
        return self.embeddings.embed_query(enhanced_query)
    
    def _enhance_query(self, query: str) -> str:
        """Mejora la query para obtener mejores resultados."""
        # Añadir contexto de dominio para mejorar la búsqueda semántica
        return f"Carpintería e instalación: {query}"


# core/rag/retriever.py
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional, Tuple
from core.config import settings
from core.rag.embeddings import EmbeddingEngine
import logging

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Sistema de recuperación de información."""
    
    def __init__(self):
        self.embedding_engine = EmbeddingEngine()
        self.client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        self._ensure_collections()
    
    def _ensure_collections(self):
        """Asegura que existen las colecciones necesarias."""
        self.collections = {
            "procedimientos": self.client.get_or_create_collection(
                name="procedimientos",
                metadata={"description": "Procedimientos técnicos de carpintería"}
            ),
            "problemas_soluciones": self.client.get_or_create_collection(
                name="problemas_soluciones",
                metadata={"description": "Base de problemas y soluciones"}
            ),
            "materiales": self.client.get_or_create_collection(
                name="materiales",
                metadata={"description": "Información de materiales"}
            ),
            "incidencias": self.client.get_or_create_collection(
                name="incidencias",
                metadata={"description": "Incidencias registradas y resueltas"}
            ),
            "aprendido": self.client.get_or_create_collection(
                name="aprendido",
                metadata={"description": "Conocimiento extraído de conversaciones"}
            ),
        }
    
    def search(
        self,
        query: str,
        collections: Optional[List[str]] = None,
        top_k: int = None,
        filters: Optional[Dict] = None,
        min_similarity: float = None,
    ) -> List[Dict]:
        """Búsqueda semántica en las colecciones."""
        
        top_k = top_k or settings.RAG_TOP_K
        min_similarity = min_similarity or settings.RAG_SIMILARITY_THRESHOLD
        
        if collections is None:
            collections = list(self.collections.keys())
        
        query_embedding = self.embedding_engine.embed_query(query)
        
        all_results = []
        
        for col_name in collections:
            if col_name not in self.collections:
                continue
            
            collection = self.collections[col_name]
            
            try:
                where_filter = None
                if filters and col_name in filters:
                    where_filter = filters[col_name]
                
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"],
                )
                
                if results and results["documents"]:
                    for i, doc in enumerate(results["documents"][0]):
                        distance = results["distances"][0][i]
                        # ChromaDB usa distancia, convertir a similitud
                        similarity = 1 - distance
                        
                        if similarity >= min_similarity:
                            all_results.append({
                                "content": doc,
                                "metadata": results["metadatas"][0][i],
                                "similarity": similarity,
                                "collection": col_name,
                            })
            except Exception as e:
                logger.error(f"Error buscando en {col_name}: {e}")
        
        # Ordenar por similitud
        all_results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return all_results[:top_k]
    
    def add_document(
        self,
        collection_name: str,
        content: str,
        metadata: Dict,
        doc_id: str,
    ):
        """Añade un documento a una colección."""
        if collection_name not in self.collections:
            self.collections[collection_name] = self.client.get_or_create_collection(
                name=collection_name
            )
        
        embedding = self.embedding_engine.embed_text(content)
        
        self.collections[collection_name].upsert(
            ids=[doc_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata],
        )
        
        logger.info(f"Documento {doc_id} añadido a {collection_name}")
    
    def add_documents_batch(
        self,
        collection_name: str,
        documents: List[Dict],
    ):
        """Añade múltiples documentos."""
        if not documents:
            return
        
        contents = [d["content"] for d in documents]
        embeddings = self.embedding_engine.embed_texts(contents)
        
        self.collections[collection_name].upsert(
            ids=[d.get("id", f"doc_{i}") for i, d in enumerate(documents)],
            documents=contents,
            embeddings=embeddings,
            metadatas=[d.get("metadata", {}) for d in documents],
        )
        
        logger.info(f"{len(documents)} documentos añadidos a {collection_name}")


# core/rag/indexer.py
from pathlib import Path
from typing import List, Dict
from core.rag.chunking import SmartChunker
from core.rag.retriever import RAGRetriever
from core.config import settings
import hashlib
import logging

logger = logging.getLogger(__name__)


class KnowledgeIndexer:
    """Indexador de la base de conocimiento."""
    
    def __init__(self):
        self.chunker = SmartChunker()
        self.retriever = RAGRetriever()
    
    def index_knowledge_base(self, base_path: str = None):
        """Indexa toda la base de conocimiento desde archivos."""
        base_path = Path(base_path or settings.KNOWLEDGE_BASE_PATH)
        
        if not base_path.exists():
            logger.error(f"Base de conocimiento no encontrada: {base_path}")
            return
        
        # Mapeo de carpetas a colecciones
        folder_collection_map = {
            "procedimientos": "procedimientos",
            "materiales": "materiales",
            "problemas_soluciones": "problemas_soluciones",
            "checklists": "procedimientos",
        }
        
        total_indexed = 0
        
        for folder_name, collection_name in folder_collection_map.items():
            folder_path = base_path / folder_name
            if not folder_path.exists():
                continue
            
            for file_path in folder_path.rglob("*.md"):
                try:
                    count = self._index_file(file_path, collection_name)
                    total_indexed += count
                    logger.info(f"Indexado: {file_path} ({count} chunks)")
                except Exception as e:
                    logger.error(f"Error indexando {file_path}: {e}")
        
        logger.info(f"Indexación completada: {total_indexed} chunks totales")
    
    def _index_file(self, file_path: Path, collection_name: str) -> int:
        """Indexa un archivo individual."""
        content = file_path.read_text(encoding="utf-8")
        
        # Metadata del archivo
        metadata = {
            "source": str(file_path),
            "tipo": file_path.parent.name,
            "archivo": file_path.stem,
            "categoria": self._detect_category(file_path),
        }
        
        # Fragmentar
        chunks = self.chunker.chunk_document(content, metadata)
        
        # Preparar documentos para indexación
        documents = []
        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(
                f"{file_path}_{i}".encode()
            ).hexdigest()
            
            documents.append({
                "id": doc_id,
                "content": chunk.get("enriched_content", chunk["content"]),
                "metadata": chunk["metadata"],
            })
        
        # Indexar
        self.retriever.add_documents_batch(collection_name, documents)
        
        return len(documents)
    
    def _detect_category(self, file_path: Path) -> str:
        """Detecta la categoría basándose en la ruta."""
        parts = file_path.parts
        
        category_keywords = {
            "puertas": "instalacion_puertas",
            "parquet": "instalacion_parquet",
            "suelos": "instalacion_parquet",
            "rodapies": "instalacion_rodapies",
            "taller": "carpinteria_taller",
            "materiales": "materiales",
        }
        
        for part in parts:
            part_lower = part.lower()
            for keyword, category in category_keywords.items():
                if keyword in part_lower:
                    return category
        
        return "general"
    
    def index_learned_knowledge(
        self,
        content: str,
        metadata: Dict,
        source: str = "conversacion",
    ):
        """Indexa conocimiento aprendido de conversaciones."""
        doc_id = hashlib.md5(
            f"{source}_{content[:100]}".encode()
        ).hexdigest()
        
        metadata.update({
            "source": source,
            "learned": True,
        })
        
        self.retriever.add_document(
            collection_name="aprendido",
            content=content,
            metadata=metadata,
            doc_id=doc_id,
        )
        
        logger.info(f"Conocimiento aprendido indexado: {doc_id}")
5.4 Sistema de Memoria y Aprendizaje (EL COMPONENTE CLAVE)
Python

# core/memory/conversation_memory.py
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging
from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

logger = logging.getLogger(__name__)
Base = declarative_base()


class ConversationRecord(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True)
    user_id = Column(String, index=True)
    user_role = Column(String)  # carpintero_taller, instalador_puertas, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_message = Column(Text)
    assistant_response = Column(Text)
    intent = Column(String)  # consulta, diagnostico, incidencia, etc.
    context = Column(JSON)  # Contexto de la conversación
    feedback = Column(String)  # positivo, negativo, none
    knowledge_extracted = Column(JSON)  # Conocimiento extraído
    sources_used = Column(JSON)  # Fuentes RAG usadas


class LearnedKnowledge(Base):
    __tablename__ = "learned_knowledge"
    
    id = Column(String, primary_key=True)
    content = Column(Text)
    category = Column(String)
    subcategory = Column(String)
    source_conversation_id = Column(String)
    confidence = Column(Float)
    validated = Column(Integer, default=0)  # 0: pendiente, 1: validado, -1: rechazado
    created_at = Column(DateTime, default=datetime.utcnow)
    validated_at = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON)


class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    reported_by = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    category = Column(String)  # puerta, parquet, rodapie, taller
    description = Column(Text)
    problem_type = Column(String)  # medida, material, hueco, desnivel, etc.
    solution_applied = Column(Text, nullable=True)
    solution_effective = Column(Integer, nullable=True)  # 0 o 1
    location = Column(String, nullable=True)
    metadata_ = Column("metadata", JSON)


class ConversationMemory:
    """Gestión de memoria conversacional con persistencia."""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def save_interaction(
        self,
        session_id: str,
        user_id: str,
        user_role: str,
        user_message: str,
        assistant_response: str,
        intent: str,
        context: Dict = None,
        sources_used: List[Dict] = None,
    ) -> str:
        """Guarda una interacción completa."""
        import uuid
        record_id = str(uuid.uuid4())
        
        session = self.Session()
        try:
            record = ConversationRecord(
                id=record_id,
                session_id=session_id,
                user_id=user_id,
                user_role=user_role,
                user_message=user_message,
                assistant_response=assistant_response,
                intent=intent,
                context=context or {},
                sources_used=sources_used or [],
            )
            session.add(record)
            session.commit()
            return record_id
        finally:
            session.close()
    
    def get_session_history(
        self,
        session_id: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Obtiene el historial de una sesión."""
        session = self.Session()
        try:
            records = (
                session.query(ConversationRecord)
                .filter(ConversationRecord.session_id == session_id)
                .order_by(ConversationRecord.timestamp.desc())
                .limit(limit)
                .all()
            )
            
            history = []
            for r in reversed(records):
                history.append({
                    "role": "user",
                    "content": r.user_message,
                })
                history.append({
                    "role": "assistant",
                    "content": r.assistant_response,
                })
            
            return history
        finally:
            session.close()
    
    def save_feedback(self, record_id: str, feedback: str):
        """Guarda feedback del usuario sobre una respuesta."""
        session = self.Session()
        try:
            record = session.query(ConversationRecord).get(record_id)
            if record:
                record.feedback = feedback
                session.commit()
        finally:
            session.close()
    
    def get_similar_past_interactions(
        self,
        user_role: str,
        intent: str,
        limit: int = 5,
    ) -> List[Dict]:
        """Obtiene interacciones pasadas similares."""
        session = self.Session()
        try:
            records = (
                session.query(ConversationRecord)
                .filter(
                    ConversationRecord.user_role == user_role,
                    ConversationRecord.intent == intent,
                    ConversationRecord.feedback == "positivo",
                )
                .order_by(ConversationRecord.timestamp.desc())
                .limit(limit)
                .all()
            )
            
            return [
                {
                    "question": r.user_message,
                    "answer": r.assistant_response,
                    "context": r.context,
                }
                for r in records
            ]
        finally:
            session.close()


# core/memory/knowledge_extractor.py
from typing import Dict, List, Optional, Tuple
from core.llm.provider import LLMProvider
from core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Eres un experto en carpintería y construcción. 
Analiza la siguiente conversación y extrae SOLO conocimiento técnico valioso 
que pueda ser útil para otros trabajadores.

Conversación:
Usuario ({user_role}): {user_message}
Asistente: {assistant_response}

Contexto: {context}

Responde SOLO en formato JSON con esta estructura:
{{
    "has_valuable_knowledge": true/false,
    "knowledge_items": [
        {{
            "type": "procedimiento|problema_solucion|consejo|material|medida",
            "category": "puertas|parquet|rodapies|taller|general",
            "title": "Título breve",
            "content": "Descripción del conocimiento extraído",
            "confidence": 0.0-1.0,
            "tags": ["tag1", "tag2"]
        }}
    ]
}}

IMPORTANTE:
- Solo extrae conocimiento NUEVO y ÚTIL
- No extraer saludos ni conversación trivial
- Prioriza soluciones a problemas reales
- Incluye medidas y especificaciones cuando existan
"""


class KnowledgeExtractor:
    """Extrae conocimiento útil de las conversaciones."""
    
    def __init__(self):
        self.llm = LLMProvider.get_fast_llm()
    
    def extract_from_interaction(
        self,
        user_message: str,
        assistant_response: str,
        user_role: str,
        context: Dict = None,
    ) -> Optional[List[Dict]]:
        """Extrae conocimiento de una interacción."""
        
        try:
            prompt = EXTRACTION_PROMPT.format(
                user_role=user_role,
                user_message=user_message,
                assistant_response=assistant_response,
                context=json.dumps(context or {}, ensure_ascii=False),
            )
            
            response = self.llm.invoke(prompt)
            
            # Parsear respuesta JSON
            result = self._parse_json_response(response)
            
            if result and result.get("has_valuable_knowledge"):
                items = result.get("knowledge_items", [])
                # Filtrar por confianza
                return [
                    item for item in items
                    if item.get("confidence", 0) >= settings.LEARNING_CONFIDENCE_THRESHOLD
                ]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo conocimiento: {e}")
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parsea la respuesta JSON del LLM."""
        try:
            # Intentar encontrar JSON en la respuesta
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            logger.warning("No se pudo parsear la respuesta como JSON")
        return None


# core/memory/learning_pipeline.py
from typing import Dict, List, Optional
from core.memory.conversation_memory import ConversationMemory, LearnedKnowledge
from core.memory.knowledge_extractor import KnowledgeExtractor
from core.rag.indexer import KnowledgeIndexer
from core.config import settings
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class LearningPipeline:
    """Pipeline de aprendizaje continuo.
    
    Flujo:
    1. Conversación ocurre
    2. Se extrae conocimiento potencial
    3. Si supera umbral de confianza → se guarda como pendiente
    4. Si requiere validación → espera revisión humana
    5. Si está validado → se indexa en RAG
    6. Disponible para futuras consultas
    """
    
    def __init__(self):
        self.memory = ConversationMemory()
        self.extractor = KnowledgeExtractor()
        self.indexer = KnowledgeIndexer()
    
    def process_interaction(
        self,
        session_id: str,
        user_id: str,
        user_role: str,
        user_message: str,
        assistant_response: str,
        intent: str,
        context: Dict = None,
        sources_used: List[Dict] = None,
    ):
        """Procesa una interacción completa."""
        
        # 1. Guardar la interacción
        record_id = self.memory.save_interaction(
            session_id=session_id,
            user_id=user_id,
            user_role=user_role,
            user_message=user_message,
            assistant_response=assistant_response,
            intent=intent,
            context=context,
            sources_used=sources_used,
        )
        
        # 2. Extraer conocimiento (si está habilitado)
        if not settings.AUTO_LEARN_ENABLED:
            return
        
        knowledge_items = self.extractor.extract_from_interaction(
            user_message=user_message,
            assistant_response=assistant_response,
            user_role=user_role,
            context=context,
        )
        
        if not knowledge_items:
            return
        
        # 3. Guardar conocimiento extraído
        for item in knowledge_items:
            self._save_learned_knowledge(item, record_id)
        
        # 4. Si no requiere validación, indexar directamente
        if not settings.LEARNING_REVIEW_REQUIRED:
            for item in knowledge_items:
                self._index_knowledge(item)
    
    def _save_learned_knowledge(self, item: Dict, source_id: str):
        """Guarda conocimiento aprendido en BD."""
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            knowledge = LearnedKnowledge(
                id=str(uuid.uuid4()),
                content=item.get("content", ""),
                category=item.get("category", "general"),
                subcategory=item.get("type", "general"),
                source_conversation_id=source_id,
                confidence=item.get("confidence", 0.5),
                validated=0 if settings.LEARNING_REVIEW_REQUIRED else 1,
                metadata_={
                    "title": item.get("title", ""),
                    "tags": item.get("tags", []),
                },
            )
            session.add(knowledge)
            session.commit()
            
            logger.info(
                f"Conocimiento aprendido guardado: {item.get('title', 'sin título')}"
            )
        finally:
            session.close()
    
    def _index_knowledge(self, item: Dict):
        """Indexa conocimiento en el RAG."""
        self.indexer.index_learned_knowledge(
            content=f"{item.get('title', '')}\n{item.get('content', '')}",
            metadata={
                "type": item.get("type", "general"),
                "category": item.get("category", "general"),
                "tags": item.get("tags", []),
                "learned": True,
            },
        )
    
    def validate_knowledge(self, knowledge_id: str, approved: bool):
        """Valida o rechaza conocimiento aprendido (revisión humana)."""
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            knowledge = session.query(LearnedKnowledge).get(knowledge_id)
            if knowledge:
                knowledge.validated = 1 if approved else -1
                knowledge.validated_at = datetime.utcnow()
                session.commit()
                
                # Si fue aprobado, indexar
                if approved:
                    self._index_knowledge({
                        "title": knowledge.metadata_.get("title", ""),
                        "content": knowledge.content,
                        "type": knowledge.subcategory,
                        "category": knowledge.category,
                        "tags": knowledge.metadata_.get("tags", []),
                    })
                    logger.info(f"Conocimiento {knowledge_id} validado e indexado")
                else:
                    logger.info(f"Conocimiento {knowledge_id} rechazado")
        finally:
            session.close()
    
    def get_pending_validations(self) -> List[Dict]:
        """Obtiene conocimiento pendiente de validación."""
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            pending = (
                session.query(LearnedKnowledge)
                .filter(LearnedKnowledge.validated == 0)
                .order_by(LearnedKnowledge.created_at.desc())
                .all()
            )
            
            return [
                {
                    "id": k.id,
                    "content": k.content,
                    "category": k.category,
                    "subcategory": k.subcategory,
                    "confidence": k.confidence,
                    "created_at": k.created_at.isoformat(),
                    "metadata": k.metadata_,
                }
                for k in pending
            ]
        finally:
            session.close()
5.5 Prompts Especializados
Python

# core/agent/prompts/system_prompt.py

SYSTEM_PROMPT = """Eres el asistente técnico de CarpinteroAI, una herramienta operativa 
para profesionales de la carpintería e instalación.

## Tu identidad
- Eres un compañero de trabajo experto, no un chatbot genérico
- Hablas de forma directa, clara y práctica
- Usas el lenguaje del oficio
- No divagues: respuestas cortas y útiles
- Si no sabes algo, lo dices claramente

## Contexto del usuario
- Rol: {user_role}
- Proyecto actual: {current_project}
- Ubicación: {location} (taller/obra)

## Tus capacidades
1. **Consulta técnica**: Medidas, materiales, especificaciones
2. **Diagnóstico**: Analizar problemas y proponer soluciones
3. **Guía paso a paso**: Procedimientos de instalación
4. **Verificación**: Validar decisiones antes de ejecutar
5. **Registro**: Capturar incidencias y problemas

## Reglas fundamentales
- SIEMPRE pregunta antes de asumir si hay ambigüedad
- En medidas, SIEMPRE confirma unidades (mm, cm, m)
- Si es un problema en obra, prioriza la solución práctica
- Si detectas un posible error, AVISA antes de que ejecuten
- Usa listas y pasos numerados para procedimientos
- Si la consulta implica seguridad, sé especialmente claro

## Formato de respuesta
- Para procedimientos: pasos numerados
- Para diagnósticos: problema → causa probable → solución
- Para medidas: siempre incluir tolerancias
- Para materiales: incluir alternativas si existen

## Información contextual disponible
{rag_context}

## Historial de conversación
{conversation_history}
"""

# core/agent/prompts/instalador_puertas.py

INSTALADOR_PUERTAS_CONTEXT = """
## Contexto específico: Instalador de puertas

Áreas de conocimiento prioritarias:
- Instalación de premarcos (plomo, nivel, escuadra)
- Montaje de marcos (ajuste, fijación, espumado)
- Colocación de hojas (bisagras, holguras)
- Cerraduras y herrajes
- Remates y tapajuntas

Problemas frecuentes:
- Huecos fuera de escuadra
- Desniveles en suelo
- Premarcos mal colocados por albañil
- Medidas que no coinciden con plano
- Puertas que rozan

Cuando el instalador reporta un problema:
1. Primero confirma las medidas reales del hueco
2. Compara con las medidas del plano/pedido
3. Evalúa si se puede resolver in situ
4. Si requiere refabricación, indicarlo claramente
5. Documenta el problema como incidencia
"""

# core/agent/prompts/instalador_parquet.py

INSTALADOR_PARQUET_CONTEXT = """
## Contexto específico: Instalador de parquet/suelos

Áreas de conocimiento prioritarias:
- Preparación de base (autonivelante, imprimación)
- Colocación flotante (underlay, click, dilataciones)
- Colocación pegada (adhesivo, llana, tiempos)
- Colocación clavada (rastreles, clavos)
- Juntas de dilatación perimetrales
- Umbrales y transiciones

Problemas frecuentes:
- Base irregular (desniveles > 2mm/m)
- Humedad en solera
- Juntas de dilatación insuficientes
- Lamas que se levantan
- Ruidos al pisar
- Dirección incorrecta de colocación

Cuando el instalador reporta un problema:
1. Confirma tipo de suelo y sistema de instalación
2. Verifica condiciones de la base (humedad, nivelación)
3. Comprueba si se respetaron juntas de dilatación
4. Evalúa si el problema es de material o de ejecución
5. Propone solución práctica inmediata si es posible
"""
5.6 Agente Principal (Orquestador)
Python

# core/agent/main_agent.py
from typing import Dict, List, Optional, AsyncGenerator
from core.llm.provider import LLMProvider
from core.rag.retriever import RAGRetriever
from core.memory.conversation_memory import ConversationMemory
from core.memory.learning_pipeline import LearningPipeline
from core.agent.router import IntentRouter
from core.agent.context_manager import ContextManager
from core.agent.prompts.system_prompt import SYSTEM_PROMPT
from core.agent.prompts.instalador_puertas import INSTALADOR_PUERTAS_CONTEXT
from core.agent.prompts.instalador_parquet import INSTALADOR_PARQUET_CONTEXT
from core.tools.diagnostico import DiagnosticoTool
from core.tools.guia_instalacion import GuiaInstalacionTool
from core.tools.verificacion import VerificacionTool
from core.tools.registro_incidencia import RegistroIncidenciaTool
from core.config import settings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import logging
import uuid

logger = logging.getLogger(__name__)


ROLE_CONTEXTS = {
    "carpintero_taller": "",
    "instalador_puertas": INSTALADOR_PUERTAS_CONTEXT,
    "instalador_parquet": INSTALADOR_PARQUET_CONTEXT,
    "instalador_rodapies": "",
    "encargado": "",
    "general": "",
}


class CarpinteroAgent:
    """Agente principal del sistema CarpinteroAI."""
    
    def __init__(self):
        self.llm = LLMProvider.get_llm()
        self.fast_llm = LLMProvider.get_fast_llm()
        self.retriever = RAGRetriever()
        self.memory = ConversationMemory()
        self.learning = LearningPipeline()
        self.router = IntentRouter()
        self.context_manager = ContextManager()
        
        # Tools
        self.tools = {
            "diagnostico": DiagnosticoTool(self.retriever, self.llm),
            "guia": GuiaInstalacionTool(self.retriever, self.llm),
            "verificacion": VerificacionTool(self.retriever, self.llm),
            "incidencia": RegistroIncidenciaTool(self.memory),
        }
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        user_id: str,
        user_role: str = "general",
        project_id: Optional[str] = None,
        location: str = "taller",
        attachments: Optional[List[Dict]] = None,
    ) -> Dict:
        """Procesa un mensaje del usuario y genera respuesta."""
        
        # 1. Clasificar intención
        intent = await self.router.classify_intent(message, self.fast_llm)
        logger.info(f"Intent detectado: {intent}")
        
        # 2. Recuperar contexto conversacional
        history = self.memory.get_session_history(session_id, limit=6)
        
        # 3. Buscar en RAG
        rag_results = self._search_relevant_knowledge(message, intent, user_role)
        rag_context = self._format_rag_context(rag_results)
        
        # 4. Construir prompt
        system_prompt = self._build_system_prompt(
            user_role=user_role,
            project_id=project_id,
            location=location,
            rag_context=rag_context,
            history=history,
        )
        
        # 5. Usar tool específica si aplica
        tool_result = await self._execute_tool_if_needed(
            intent, message, user_role, rag_results
        )
        
        # 6. Generar respuesta
        messages = [SystemMessage(content=system_prompt)]
        
        # Añadir historial
        for h in history:
            if h["role"] == "user":
                messages.append(HumanMessage(content=h["content"]))
            else:
                messages.append(AIMessage(content=h["content"]))
        
        # Mensaje actual
        user_content = message
        if tool_result:
            user_content += f"\n\n[Información adicional del sistema]: {tool_result}"
        
        messages.append(HumanMessage(content=user_content))
        
        # Generar respuesta
        response = self.llm.invoke(messages)
        response_text = response if isinstance(response, str) else response.content
        
        # 7. Post-procesamiento: aprendizaje
        self.learning.process_interaction(
            session_id=session_id,
            user_id=user_id,
            user_role=user_role,
            user_message=message,
            assistant_response=response_text,
            intent=intent,
            context={
                "project_id": project_id,
                "location": location,
            },
            sources_used=rag_results[:3] if rag_results else None,
        )
        
        return {
            "response": response_text,
            "intent": intent,
            "sources": [
                {
                    "content": r["content"][:200],
                    "collection": r["collection"],
                    "similarity": r["similarity"],
                }
                for r in rag_results[:3]
            ] if rag_results else [],
            "session_id": session_id,
        }
    
    def _search_relevant_knowledge(
        self,
        query: str,
        intent: str,
        user_role: str,
    ) -> List[Dict]:
        """Busca conocimiento relevante en el RAG."""
        
        # Determinar colecciones prioritarias según intent
        collection_priority = {
            "consulta_tecnica": ["procedimientos", "materiales", "aprendido"],
            "diagnostico": ["problemas_soluciones", "incidencias", "aprendido"],
            "guia_instalacion": ["procedimientos", "aprendido"],
            "verificacion": ["procedimientos", "problemas_soluciones"],
            "incidencia": ["incidencias", "problemas_soluciones"],
            "general": None,  # Buscar en todas
        }
        
        collections = collection_priority.get(intent)
        
        return self.retriever.search(
            query=query,
            collections=collections,
            top_k=settings.RAG_TOP_K,
        )
    
    def _format_rag_context(self, results: List[Dict]) -> str:
        """Formatea resultados RAG para incluir en el prompt."""
        if not results:
            return "No se encontró información específica en la base de conocimiento."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result.get("collection", "desconocido")
            similarity = result.get("similarity", 0)
            content = result["content"]
            
            context_parts.append(
                f"[Fuente {i} - {source} (relevancia: {similarity:.0%})]\n{content}"
            )
        
        return "\n\n".join(context_parts)
    
    def _build_system_prompt(
        self,
        user_role: str,
        project_id: Optional[str],
        location: str,
        rag_context: str,
        history: List[Dict],
    ) -> str:
        """Construye el prompt del sistema."""
        
        role_context = ROLE_CONTEXTS.get(user_role, "")
        
        history_text = ""
        if history:
            history_text = "\n".join([
                f"{'Usuario' if h['role'] == 'user' else 'Asistente'}: {h['content']}"
                for h in history[-6:]  # Últimas 3 interacciones
            ])
        
        return SYSTEM_PROMPT.format(
            user_role=user_role,
            current_project=project_id or "No especificado",
            location=location,
            rag_context=rag_context,
            conversation_history=history_text,
        ) + "\n\n" + role_context
    
    async def _execute_tool_if_needed(
        self,
        intent: str,
        message: str,
        user_role: str,
        rag_results: List[Dict],
    ) -> Optional[str]:
        """Ejecuta una herramienta específica si la intención lo requiere."""
        
        tool_map = {
            "diagnostico": "diagnostico",
            "guia_instalacion": "guia",
            "verificacion": "verificacion",
            "incidencia": "incidencia",
        }
        
        tool_name = tool_map.get(intent)
        if tool_name and tool_name in self.tools:
            try:
                return await self.tools[tool_name].execute(
                    query=message,
                    user_role=user_role,
                    context=rag_results,
                )
            except Exception as e:
                logger.error(f"Error ejecutando tool {tool_name}: {e}")
        
        return None


# core/agent/router.py
from core.config import settings
import logging

logger = logging.getLogger(__name__)

ROUTER_PROMPT = """Clasifica la siguiente consulta de un trabajador de carpintería/instalación 
en UNA de estas categorías:

- consulta_tecnica: Pregunta sobre medidas, materiales, especificaciones
- diagnostico: Tiene un problema y necesita ayuda para resolverlo
- guia_instalacion: Necesita instrucciones paso a paso
- verificacion: Quiere confirmar algo antes de ejecutarlo
- incidencia: Reporta un problema o fallo
- general: Saludo, consulta no técnica u otra cosa

Consulta: "{message}"

Responde SOLO con el nombre de la categoría, sin explicación."""


class IntentRouter:
    """Clasificador de intenciones."""
    
    async def classify_intent(self, message: str, llm) -> str:
        """Clasifica la intención del mensaje."""
        
        # Primero intentar clasificación por keywords (más rápido)
        keyword_intent = self._keyword_classification(message)
        if keyword_intent:
            return keyword_intent
        
        # Si no es claro, usar LLM
        try:
            prompt = ROUTER_PROMPT.format(message=message)
            response = llm.invoke(prompt)
            
            intent = response.strip().lower().replace(" ", "_")
            
            valid_intents = [
                "consulta_tecnica", "diagnostico", "guia_instalacion",
                "verificacion", "incidencia", "general"
            ]
            
            if intent in valid_intents:
                return intent
            
            # Buscar intent parcial
            for valid in valid_intents:
                if valid in intent:
                    return valid
            
            return "general"
            
        except Exception as e:
            logger.error(f"Error clasificando intent: {e}")
            return "general"
    
    def _keyword_classification(self, message: str) -> str:
        """Clasificación rápida por keywords."""
        msg_lower = message.lower()
        
        # Patrones de diagnóstico
        if any(w in msg_lower for w in [
            "problema", "no encaja", "no cuadra", "roza", "no cierra",
            "se levanta", "ruido", "hueco", "desnivel", "torcido",
            "no vale", "mal", "error", "fallo", "roto", "dañado",
        ]):
            return "diagnostico"
        
        # Patrones de guía
        if any(w in msg_lower for w in [
            "cómo se", "como se", "cómo instalo", "como instalo",
            "pasos para", "procedimiento", "instrucciones",
            "cómo pongo", "como pongo", "cómo coloco", "como coloco",
        ]):
            return "guia_instalacion"
        
        # Patrones de verificación
        if any(w in msg_lower for w in [
            "está bien", "es correcto", "puedo", "debería",
            "vale así", "confirma", "verificar", "comprobar",
        ]):
            return "verificacion"
        
        # Patrones de incidencia
        if any(w in msg_lower for w in [
            "reportar", "incidencia", "falta material", "no hay",
            "se ha roto", "registrar", "anotar",
        ]):
            return "incidencia"
        
        return None  # No se pudo clasificar por keywords


# core/agent/context_manager.py
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """Gestiona el contexto de la conversación."""
    
    def __init__(self):
        self.active_contexts: Dict[str, Dict] = {}
    
    def get_context(self, session_id: str) -> Dict:
        """Obtiene el contexto activo de una sesión."""
        return self.active_contexts.get(session_id, {
            "project": None,
            "location": "taller",
            "current_task": None,
            "pending_verification": None,
            "active_incident": None,
            "last_activity": None,
        })
    
    def update_context(self, session_id: str, updates: Dict):
        """Actualiza el contexto de una sesión."""
        if session_id not in self.active_contexts:
            self.active_contexts[session_id] = {}
        
        self.active_contexts[session_id].update(updates)
        self.active_contexts[session_id]["last_activity"] = datetime.utcnow().isoformat()
    
    def clear_context(self, session_id: str):
        """Limpia el contexto de una sesión."""
        if session_id in self.active_contexts:
            del self.active_contexts[session_id]
5.7 Herramientas del Agente
Python

# core/tools/diagnostico.py
from typing import Dict, List, Optional


DIAGNOSTICO_PROMPT = """Eres un experto diagnosticando problemas en carpintería e instalación.

El trabajador describe este problema:
"{query}"

Su rol es: {user_role}

Información relevante de la base de conocimiento:
{context}

Responde con esta estructura:
1. **Problema identificado**: [descripción clara]
2. **Causa más probable**: [causa]
3. **Solución recomendada**: [pasos concretos]
4. **Alternativa si no funciona**: [plan B]
5. **Prevención futura**: [cómo evitarlo]

Sé directo y práctico. El trabajador está en obra y necesita resolver esto ahora."""


class DiagnosticoTool:
    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
    
    async def execute(
        self,
        query: str,
        user_role: str,
        context: List[Dict] = None,
    ) -> str:
        context_text = ""
        if context:
            context_text = "\n".join([
                f"- {r['content']}" for r in context[:3]
            ])
        
        prompt = DIAGNOSTICO_PROMPT.format(
            query=query,
            user_role=user_role,
            context=context_text or "No hay información previa sobre este problema.",
        )
        
        return self.llm.invoke(prompt)


# core/tools/guia_instalacion.py
GUIA_PROMPT = """Genera una guía paso a paso para el siguiente trabajo:

Consulta: "{query}"
Rol del trabajador: {user_role}

Información técnica disponible:
{context}

Formato de respuesta:
## [Título del procedimiento]

### Materiales necesarios
- [lista]

### Herramientas
- [lista]

### Pasos
1. [paso]
2. [paso]
...

### ⚠️ Puntos críticos
- [advertencias]

### ✅ Verificación
- [qué comprobar al terminar]

Sé específico con medidas y tolerancias."""


class GuiaInstalacionTool:
    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
    
    async def execute(
        self,
        query: str,
        user_role: str,
        context: List[Dict] = None,
    ) -> str:
        context_text = ""
        if context:
            context_text = "\n".join([
                f"- {r['content']}" for r in context[:5]
            ])
        
        prompt = GUIA_PROMPT.format(
            query=query,
            user_role=user_role,
            context=context_text or "Usar conocimiento general de carpintería.",
        )
        
        return self.llm.invoke(prompt)


# core/tools/verificacion.py
VERIFICACION_PROMPT = """El trabajador quiere verificar algo antes de ejecutarlo:

Consulta: "{query}"
Rol: {user_role}

Información de referencia:
{context}

Responde con:
✅ CORRECTO: [si todo está bien, confirma]
⚠️ ATENCIÓN: [si hay algo que revisar]
❌ INCORRECTO: [si detectas un error]

En todos los casos, explica brevemente POR QUÉ.
Si hay medidas, verifica tolerancias."""


class VerificacionTool:
    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
    
    async def execute(
        self,
        query: str,
        user_role: str,
        context: List[Dict] = None,
    ) -> str:
        context_text = ""
        if context:
            context_text = "\n".join([
                f"- {r['content']}" for r in context[:3]
            ])
        
        prompt = VERIFICACION_PROMPT.format(
            query=query,
            user_role=user_role,
            context=context_text or "No hay referencia específica.",
        )
        
        return self.llm.invoke(prompt)


# core/tools/registro_incidencia.py
from typing import Dict, List, Optional
from datetime import datetime
import uuid

INCIDENCIA_EXTRACT_PROMPT = """Extrae la información de esta incidencia reportada por un trabajador:

Mensaje: "{query}"
Rol: {user_role}

Responde en JSON:
{{
    "description": "descripción del problema",
    "category": "puerta|parquet|rodapie|taller|otro",
    "problem_type": "medida|material|hueco|desnivel|herraje|otro",
    "severity": "baja|media|alta|critica",
    "location": "ubicación si se menciona"
}}"""


class RegistroIncidenciaTool:
    def __init__(self, memory):
        self.memory = memory
    
    async def execute(
        self,
        query: str,
        user_role: str,
        context: List[Dict] = None,
    ) -> str:
        return (
            "He registrado tu incidencia. "
            "¿Puedes confirmar los siguientes datos?\n"
            f"- Descripción: {query}\n"
            "- ¿En qué proyecto/obra estás?\n"
            "- ¿Tienes foto del problema?"
        )
5.8 API REST
Python

# api/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import chat, voice, incidents, knowledge, admin
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Asistente técnico operativo para carpintería e instalación",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voz"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidencias"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Conocimiento"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# Frontend estático
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.on_event("startup")
async def startup():
    logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    # Verificar conexión con Ollama
    # Verificar ChromaDB
    # Verificar PostgreSQL


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "model": settings.LLM_MODEL,
    }


# api/routes/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from core.agent.main_agent import CarpinteroAgent
import uuid

router = APIRouter()
agent = CarpinteroAgent()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    user_id: str = "default"
    user_role: str = Field(
        default="general",
        description="carpintero_taller, instalador_puertas, instalador_parquet, "
                    "instalador_rodapies, encargado, general"
    )
    project_id: Optional[str] = None
    location: str = Field(default="taller", description="taller o obra")


class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    sources: List[Dict] = []


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal de conversación."""
    
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        result = await agent.process_message(
            message=request.message,
            session_id=session_id,
            user_id=request.user_id,
            user_role=request.user_role,
            project_id=request.project_id,
            location=request.location,
        )
        
        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            intent=result["intent"],
            sources=result.get("sources", []),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def feedback(record_id: str, is_positive: bool):
    """Feedback del usuario sobre una respuesta."""
    agent.memory.save_feedback(
        record_id=record_id,
        feedback="positivo" if is_positive else "negativo",
    )
    return {"status": "ok"}


# api/routes/voice.py
from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
import whisper
import tempfile
import os
from core.config import settings

router = APIRouter()

# Cargar modelo Whisper
whisper_model = None


def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = whisper.load_model(settings.WHISPER_MODEL)
    return whisper_model


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form(default="es"),
):
    """Transcribe audio a texto usando Whisper."""
    
    # Guardar archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        model = get_whisper_model()
        result = model.transcribe(
            tmp_path,
            language=language,
            fp16=False,
        )
        
        return {
            "text": result["text"],
            "language": result.get("language", language),
        }
    finally:
        os.unlink(tmp_path)


@router.post("/chat-voice")
async def chat_with_voice(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Form(default=None),
    user_id: str = Form(default="default"),
    user_role: str = Form(default="general"),
    project_id: Optional[str] = Form(default=None),
    location: str = Form(default="taller"),
):
    """Endpoint combinado: transcribe audio + procesa con agente."""
    
    # 1. Transcribir
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        model = get_whisper_model()
        transcription = model.transcribe(tmp_path, language="es", fp16=False)
        text = transcription["text"]
    finally:
        os.unlink(tmp_path)
    
    # 2. Procesar con agente
    from api.routes.chat import agent
    import uuid
    
    session_id = session_id or str(uuid.uuid4())
    
    result = await agent.process_message(
        message=text,
        session_id=session_id,
        user_id=user_id,
        user_role=user_role,
        project_id=project_id,
        location=location,
    )
    
    return {
        "transcription": text,
        "response": result["response"],
        "session_id": session_id,
        "intent": result["intent"],
    }


# api/routes/knowledge.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from core.memory.learning_pipeline import LearningPipeline
from core.rag.indexer import KnowledgeIndexer

router = APIRouter()
learning = LearningPipeline()
indexer = KnowledgeIndexer()


@router.get("/pending")
async def get_pending_validations():
    """Obtiene conocimiento pendiente de validación."""
    return learning.get_pending_validations()


@router.post("/validate/{knowledge_id}")
async def validate_knowledge(knowledge_id: str, approved: bool):
    """Valida o rechaza conocimiento aprendido."""
    learning.validate_knowledge(knowledge_id, approved)
    return {"status": "ok", "approved": approved}


@router.post("/reindex")
async def reindex_knowledge_base():
    """Re-indexa toda la base de conocimiento."""
    indexer.index_knowledge_base()
    return {"status": "ok", "message": "Re-indexación completada"}


class ManualKnowledge(BaseModel):
    content: str
    category: str
    subcategory: str
    title: str
    tags: List[str] = []


@router.post("/add")
async def add_manual_knowledge(knowledge: ManualKnowledge):
    """Añade conocimiento manualmente."""
    indexer.index_learned_knowledge(
        content=f"{knowledge.title}\n{knowledge.content}",
        metadata={
            "type": knowledge.subcategory,
            "category": knowledge.category,
            "tags": knowledge.tags,
            "manual": True,
        },
    )
    return {"status": "ok"}
5.9 Frontend PWA (Optimizado para obra)
HTML

<!-- frontend/index.html -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, 
          maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#1a1a2e">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <link rel="manifest" href="/manifest.json">
    <title>CarpinteroAI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #e67e22;
            --primary-dark: #d35400;
            --bg: #1a1a2e;
            --bg-light: #16213e;
            --bg-card: #0f3460;
            --text: #eee;
            --text-muted: #999;
            --success: #2ecc71;
            --warning: #f39c12;
            --danger: #e74c3c;
            --border-radius: 12px;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg);
            color: var(--text);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        /* Header */
        .header {
            background: var(--bg-light);
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .header h1 {
            font-size: 18px;
            color: var(--primary);
        }
        
        .header .role-selector {
            background: var(--bg-card);
            border: 1px solid rgba(255,255,255,0.2);
            color: var(--text);
            padding: 6px 10px;
            border-radius: 8px;
            font-size: 13px;
        }
        
        /* Quick actions - Acceso rápido */
        .quick-actions {
            display: flex;
            gap: 8px;
            padding: 10px 16px;
            overflow-x: auto;
            background: var(--bg-light);
            -webkit-overflow-scrolling: touch;
        }
        
        .quick-btn {
            flex-shrink: 0;
            background: var(--bg-card);
            border: 1px solid rgba(255,255,255,0.15);
            color: var(--text);
            padding: 8px 14px;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
        }
        
        .quick-btn:active {
            background: var(--primary);
            transform: scale(0.95);
        }
        
        .quick-btn .icon {
            margin-right: 4px;
        }
        
        /* Chat area */
        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            -webkit-overflow-scrolling: touch;
        }
        
        .message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: var(--border-radius);
            font-size: 15px;
            line-height: 1.5;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            background: var(--primary);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant {
            background: var(--bg-card);
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }
        
        .message.assistant .sources {
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid rgba(255,255,255,0.1);
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .message .intent-badge {
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            margin-bottom: 6px;
            color: var(--primary);
        }
        
        /* Typing indicator */
        .typing {
            display: none;
            align-self: flex-start;
            background: var(--bg-card);
            padding: 12px 20px;
            border-radius: var(--border-radius);
        }
        
        .typing.visible { display: block; }
        
        .typing span {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: var(--text-muted);
            border-radius: 50%;
            margin: 0 2px;
            animation: bounce 1.4s infinite ease-in-out;
        }
        
        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        /* Input area */
        .input-area {
            background: var(--bg-light);
            padding: 12px 16px;
            display: flex;
            gap: 8px;
            align-items: end;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .input-area textarea {
            flex: 1;
            background: var(--bg-card);
            border: 1px solid rgba(255,255,255,0.2);
            color: var(--text);
            padding: 12px 16px;
            border-radius: var(--border-radius);
            font-size: 15px;
            resize: none;
            min-height: 44px;
            max-height: 120px;
            line-height: 1.4;
            font-family: inherit;
        }
        
        .input-area textarea::placeholder {
            color: var(--text-muted);
        }
        
        .input-area textarea:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .btn-action {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            border: none;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 20px;
            transition: all 0.2s;
            flex-shrink: 0;
        }
        
        .btn-send {
            background: var(--primary);
            color: white;
        }
        
        .btn-send:active {
            background: var(--primary-dark);
            transform: scale(0.9);
        }
        
        .btn-voice {
            background: var(--bg-card);
            color: var(--text);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .btn-voice.recording {
            background: var(--danger);
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.4); }
            50% { box-shadow: 0 0 0 10px rgba(231, 76, 60, 0); }
        }
        
        /* Feedback buttons */
        .feedback-btns {
            display: flex;
            gap: 8px;
            margin-top: 8px;
        }
        
        .feedback-btn {
            background: none;
            border: 1px solid rgba(255,255,255,0.2);
            color: var(--text-muted);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            cursor: pointer;
        }
        
        .feedback-btn:active {
            background: rgba(255,255,255,0.1);
        }
        
        /* Markdown rendering in messages */
        .message.assistant h2,
        .message.assistant h3 {
            color: var(--primary);
            margin: 8px 0 4px;
        }
        
        .message.assistant ul,
        .message.assistant ol {
            padding-left: 20px;
            margin: 4px 0;
        }
        
        .message.assistant code {
            background: rgba(0,0,0,0.3);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
        }
        
        .message.assistant strong {
            color: var(--primary);
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <h1>🪚 CarpinteroAI</h1>
        <select class="role-selector" id="roleSelector">
            <option value="general">General</option>
            <option value="carpintero_taller">Carpintero Taller</option>
            <option value="instalador_puertas">Instalador Puertas</option>
            <option value="instalador_parquet">Instalador Parquet</option>
            <option value="instalador_rodapies">Instalador Rodapiés</option>
            <option value="encargado">Encargado</option>
        </select>
    </div>
    
    <!-- Quick Actions -->
    <div class="quick-actions" id="quickActions">
        <button class="quick-btn" data-msg="¿Cómo instalo un premarco correctamente?">
            <span class="icon">🚪</span> Premarco
        </button>
        <button class="quick-btn" data-msg="Tengo un problema con una puerta que roza">
            <span class="icon">⚠️</span> Puerta roza
        </button>
        <button class="quick-btn" data-msg="¿Qué juntas de dilatación dejo en el parquet?">
            <span class="icon">🪵</span> Dilatación
        </button>
        <button class="quick-btn" data-msg="¿Cómo corto un inglete de rodapié correctamente?">
            <span class="icon">📐</span> Inglete
        </button>
        <button class="quick-btn" data-msg="El hueco no cuadra con las medidas del plano">
            <span class="icon">📏</span> Medidas
        </button>
        <button class="quick-btn" data-msg="Necesito reportar una incidencia">
            <span class="icon">📋</span> Incidencia
        </button>
    </div>
    
    <!-- Chat Area -->
    <div class="chat-area" id="chatArea">
        <div class="message assistant">
            <div class="intent-badge">Bienvenida</div>
            ¡Hola! Soy tu asistente de CarpinteroAI. 
            Estoy aquí para ayudarte con consultas técnicas, 
            resolver problemas en obra y guiarte en instalaciones.
            <br><br>
            Selecciona tu rol arriba y pregúntame lo que necesites.
            También puedes usar el micrófono 🎤 para hablar.
        </div>
    </div>
    
    <!-- Typing indicator -->
    <div class="typing" id="typingIndicator">
        <span></span><span></span><span></span>
    </div>
    
    <!-- Input Area -->
    <div class="input-area">
        <textarea 
            id="messageInput" 
            placeholder="Escribe tu consulta..."
            rows="1"
        ></textarea>
        <button class="btn-action btn-voice" id="voiceBtn">🎤</button>
        <button class="btn-action btn-send" id="sendBtn">➤</button>
    </div>

    <!-- Marked.js for markdown -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    
    <script>
        // State
        const state = {
            sessionId: null,
            userId: 'user_' + Math.random().toString(36).substr(2, 9),
            isRecording: false,
            mediaRecorder: null,
            audioChunks: [],
        };
        
        // Elements
        const chatArea = document.getElementById('chatArea');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const voiceBtn = document.getElementById('voiceBtn');
        const roleSelector = document.getElementById('roleSelector');
        const typingIndicator = document.getElementById('typingIndicator');
        const quickActions = document.getElementById('quickActions');
        
        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Send on Enter (not Shift+Enter)
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Send button
        sendBtn.addEventListener('click', sendMessage);
        
        // Quick actions
        quickActions.addEventListener('click', function(e) {
            const btn = e.target.closest('.quick-btn');
            if (btn) {
                const msg = btn.getAttribute('data-msg');
                messageInput.value = msg;
                sendMessage();
            }
        });
        
        // Voice button
        voiceBtn.addEventListener('click', toggleVoice);
        
        // Send message
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Add user message to chat
            addMessage('user', message);
            messageInput.value = '';
            messageInput.style.height = 'auto';
            
            // Show typing
            showTyping(true);
            
            try {
                const response = await fetch('/api/chat/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        session_id: state.sessionId,
                        user_id: state.userId,
                        user_role: roleSelector.value,
                        location: 'obra',  // TODO: selector
                    }),
                });
                
                const data = await response.json();
                
                // Update session
                state.sessionId = data.session_id;
                
                // Add response
                showTyping(false);
                addMessage('assistant', data.response, data.intent, data.sources);
                
            } catch (error) {
                showTyping(false);
                addMessage('assistant', 
                    '❌ Error de conexión. Verifica que el servidor esté activo.',
                    'error'
                );
            }
        }
        
        // Add message to chat
        function addMessage(role, content, intent, sources) {
            const div = document.createElement('div');
            div.className = `message ${role}`;
            
            let html = '';
            
            if (role === 'assistant') {
                if (intent) {
                    const intentLabels = {
                        'consulta_tecnica': '📚 Consulta técnica',
                        'diagnostico': '🔍 Diagnóstico',
                        'guia_instalacion': '📋 Guía',
                        'verificacion': '✅ Verificación',
                        'incidencia': '⚠️ Incidencia',
                        'general': '💬 General',
                    };
                    html += `<div class="intent-badge">${intentLabels[intent] || intent}</div>`;
                }
                
                // Render markdown
                html += marked.parse(content);
                
                // Sources
                if (sources && sources.length > 0) {
                    html += '<div class="sources">📎 Fuentes: ';
                    html += sources.map(s => 
                        `${s.collection} (${Math.round(s.similarity * 100)}%)`
                    ).join(', ');
                    html += '</div>';
                }
                
                // Feedback
                html += `
                    <div class="feedback-btns">
                        <button class="feedback-btn" onclick="sendFeedback(true)">
                            👍 Útil
                        </button>
                        <button class="feedback-btn" onclick="sendFeedback(false)">
                            👎 Mejorable
                        </button>
                    </div>
                `;
            } else {
                html = content;
            }
            
            div.innerHTML = html;
            chatArea.appendChild(div);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        // Typing indicator
        function showTyping(show) {
            typingIndicator.classList.toggle('visible', show);
            if (show) {
                chatArea.scrollTop = chatArea.scrollHeight;
            }
        }
        
        // Voice recording
        async function toggleVoice() {
            if (state.isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        }
        
        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: true 
                });
                
                state.mediaRecorder = new MediaRecorder(stream);
                state.audioChunks = [];
                
                state.mediaRecorder.ondataavailable = (event) => {
                    state.audioChunks.push(event.data);
                };
                
                state.mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(state.audioChunks, { 
                        type: 'audio/wav' 
                    });
                    
                    // Enviar audio
                    await sendVoiceMessage(audioBlob);
                    
                    // Parar stream
                    stream.getTracks().forEach(track => track.stop());
                };
                
                state.mediaRecorder.start();
                state.isRecording = true;
                voiceBtn.classList.add('recording');
                voiceBtn.textContent = '⏹';
                
            } catch (error) {
                alert('No se pudo acceder al micrófono');
            }
        }
        
        function stopRecording() {
            if (state.mediaRecorder && state.isRecording) {
                state.mediaRecorder.stop();
                state.isRecording = false;
                voiceBtn.classList.remove('recording');
                voiceBtn.textContent = '🎤';
            }
        }
        
        async function sendVoiceMessage(audioBlob) {
            showTyping(true);
            
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            formData.append('session_id', state.sessionId || '');
            formData.append('user_id', state.userId);
            formData.append('user_role', roleSelector.value);
            formData.append('location', 'obra');
            
            try {
                const response = await fetch('/api/voice/chat-voice', {
                    method: 'POST',
                    body: formData,
                });
                
                const data = await response.json();
                state.sessionId = data.session_id;
                
                // Mostrar transcripción
                addMessage('user', `🎤 ${data.transcription}`);
                
                showTyping(false);
                addMessage('assistant', data.response, data.intent);
                
            } catch (error) {
                showTyping(false);
                addMessage('assistant', '❌ Error procesando audio', 'error');
            }
        }
        
        // Feedback
        async function sendFeedback(isPositive) {
            // TODO: enviar al endpoint de feedback
            const btn = event.target;
            btn.textContent = isPositive ? '👍 ¡Gracias!' : '👎 Anotado';
            btn.disabled = true;
        }
        
        // Service Worker para offline
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
        }
    </script>
</body>
</html>
JSON

// frontend/manifest.json
{
    "name": "CarpinteroAI",
    "short_name": "CarpinteroAI",
    "description": "Asistente técnico para carpintería e instalación",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#1a1a2e",
    "theme_color": "#1a1a2e",
    "orientation": "portrait",
    "icons": [
        {
            "src": "/assets/icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/assets/icon-512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}
JavaScript

// frontend/sw.js
const CACHE_NAME = 'carpintero-ai-v1';
const OFFLINE_URL = '/offline.html';

const urlsToCache = [
    '/',
    '/css/app.css',
    '/js/app.js',
    '/manifest.json',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(urlsToCache);
        })
    );
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;
    
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Cache successful responses
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseClone);
                });
                return response;
            })
            .catch(() => {
                // Serve from cache if offline
                return caches.match(event.request);
            })
    );
});
5.10 Docker Compose
YAML

# docker-compose.yml
version: '3.8'

services:
  # LLM Local
  ollama:
    image: ollama/ollama:latest
    container_name: carpintero-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    # Si no hay GPU, quitar la sección deploy
    restart: unless-stopped

  # Vector Database
  chromadb:
    image: chromadb/chroma:latest
    container_name: carpintero-chromadb
    ports:
      - "8100:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
    restart: unless-stopped

  # Database
  postgres:
    image: postgres:15-alpine
    container_name: carpintero-postgres
    environment:
      POSTGRES_USER: carpintero
      POSTGRES_PASSWORD: carpintero
      POSTGRES_DB: carpintero_ai
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  # Cache & Queue
  redis:
    image: redis:7-alpine
    container_name: carpintero-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # API Principal
  api:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.api
    container_name: carpintero-api
    ports:
      - "8000:8000"
    volumes:
      - ./core:/app/core
      - ./api:/app/api
      - ./frontend:/app/frontend
      - ./knowledge_base:/app/knowledge_base
    environment:
      - LLM_BASE_URL=http://ollama:11434
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8000
      - DATABASE_URL=postgresql://carpintero:carpintero@postgres:5432/carpintero_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - ollama
      - chromadb
      - postgres
      - redis
    restart: unless-stopped

  # Worker (procesos background)
  worker:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.worker
    container_name: carpintero-worker
    volumes:
      - ./core:/app/core
      - ./workers:/app/workers
      - ./knowledge_base:/app/knowledge_base
    environment:
      - LLM_BASE_URL=http://ollama:11434
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8000
      - DATABASE_URL=postgresql://carpintero:carpintero@postgres:5432/carpintero_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - ollama
      - chromadb
      - postgres
      - redis
    restart: unless-stopped

volumes:
  ollama_data:
  chroma_data:
  postgres_data:
  redis_data:
Dockerfile

# infra/docker/Dockerfile.api
FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY core/ ./core/
COPY api/ ./api/
COPY frontend/ ./frontend/
COPY knowledge_base/ ./knowledge_base/
COPY scripts/ ./scripts/

# Exponer puerto
EXPOSE 8000

# Comando
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
text

# requirements.txt
# API
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# LLM
langchain==0.1.0
langchain-community==0.0.10
langchain-core==0.1.10

# Embeddings & Vector Store
chromadb==0.4.22

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0

# Cache
redis==5.0.1

# Voice
openai-whisper==20231117

# Utils
pydantic==2.5.2
pydantic-settings==2.1.0
python-dotenv==1.0.0
httpx==0.25.2
aiofiles==23.2.1

# Markdown
marked==0.3.0
5.11 Knowledge Base Inicial (Semilla)
Markdown

<!-- knowledge_base/procedimientos/instalacion_puertas/premarco.md -->
# Instalación de Premarcos

## Antes de empezar
- Verificar medidas del hueco en obra vs plano
- Comprobar que el premarco coincide con el pedido
- Confirmar tipo de premarco (madera, metálico, extensible)

## Herramientas necesarias
- Nivel de burbuja (mínimo 60cm)
- Plomada o nivel láser
- Cuñas de madera
- Espuma de poliuretano
- Taladro con broca para pared
- Tornillos y tacos

## Procedimiento paso a paso

### 1. Verificar el hueco
- Medir ancho en 3 puntos: arriba, centro, abajo
- Medir alto en 2 puntos: izquierda, derecha
- La holgura entre premarco y hueco debe ser de 10-15mm por lado
- Si el hueco varía más de 5mm, documentar y consultar

### 2. Presentar el premarco
- Colocar el premarco centrado en el hueco
- Calzar con cuñas para mantener en posición
- Verificar que está a plomo en ambas jambas
- Verificar que está a nivel en el dintel
- Comprobar escuadra midiendo diagonales (deben ser iguales, tolerancia ±2mm)

### 3. Fijar el premarco
- Taladrar a través del premarco en los puntos marcados
- Mínimo 3 puntos de fijación por jamba (arriba, centro, abajo)
- 2 puntos en el dintel
- Colocar tacos y tornillos sin apretar del todo
- Verificar plomo y nivel de nuevo
- Apretar definitivamente

### 4. Espumar
- Humedecer ligeramente el hueco (la espuma adhiere mejor)
- Aplicar espuma de poliuretano en los huecos
- NO llenar más del 60% (la espuma expande)
- Dejar fraguar según instrucciones del fabricante

### 5. Verificación final
- Comprobar plomo
- Comprobar nivel
- Comprobar escuadra (diagonales)
- Verificar que no se ha movido con la espuma

## ⚠️ Problemas frecuentes

### Hueco más grande de lo previsto
- Si la diferencia es < 20mm por lado: resolver con más espuma
- Si es > 20mm: consultar con encargado, puede necesitar bastidor auxiliar

### Hueco más pequeño
- NO picar la pared sin consultar (puede haber instalaciones)
- Documentar y avisar al encargado
- Verificar si es error de albañilería o de medición

### Hueco desplomado
- Si el desplome es < 5mm: compensar con cuñas
- Si es > 5mm: documentar como incidencia
- El premarco SIEMPRE debe ir a plomo, independientemente de la pared

### Premarco no coincide con medidas
- PARAR la instalación
- Verificar las medidas del pedido
- Contactar con taller
- NO forzar nunca un premarco
Markdown

<!-- knowledge_base/procedimientos/instalacion_parquet/preparacion_base.md -->
# Preparación de Base para Parquet

## Requisitos de la base

### Planimetría
- Desnivel máximo permitido: 2mm por metro lineal
- Comprobar con regla de 2 metros y galga
- Si supera 2mm/m: necesita autonivelante

### Humedad
- Humedad máxima en solera de cemento: 2% CM (higrómetro)
- Humedad máxima en solera de anhidrita: 0.5% CM
- Si la humedad es superior: NO colocar, esperar o usar barrera de vapor

### Limpieza
- La base debe estar limpia, seca y libre de polvo
- Retirar restos de obra, pegamento anterior, etc.
- Aspirar antes de colocar

## Medición de humedad

### Con higrómetro de contacto
1. Limpiar la zona de medición
2. Colocar el higrómetro en el suelo
3. Esperar estabilización (30 segundos)
4. Tomar mínimo 3 mediciones en diferentes puntos
5. Registrar la medición más alta

### Puntos críticos de humedad
- Cerca de paredes exteriores
- Zonas de baño/cocina
- Plantas bajas sin cámara de aire
- Soleras recién vertidas (necesitan mínimo 28 días por cm de espesor)

## Autonivelante

### Cuándo es necesario
- Desniveles > 2mm/m
- Irregularidades superficiales marcadas
- Cambio de nivel entre estancias

### Procedimiento
1. Imprimar la base con imprimación adecuada
2. Colocar banda perimetral de espuma
3. Preparar autonivelante según instrucciones del fabricante
4. Verter y extender con llana de púas
5. Dejar secar según fabricante (normalmente 24-48h)
6. Verificar planimetría después del secado

## ⚠️ Problemas frecuentes

### Base que parece seca pero tiene humedad
- Las mediciones de superficie pueden engañar
- En caso de duda, hacer test con lámina de PE (tapar 1m² durante 24h)
- Si hay condensación bajo el plástico: hay humedad

### Solera que suena a hueco
- Indica falta de adherencia del mortero
- Puede provocar ruidos al pisar
- Documentar y consultar con encargado
Markdown

<!-- knowledge_base/problemas_soluciones/puertas.md -->
# Problemas y Soluciones: Puertas

## Puerta que roza en el suelo

### Causas probables
1. Bisagras sueltas → apretar tornillos
2. Suelo no nivelado → verificar con nivel
3. Puerta hinchada por humedad → comprobar condiciones ambientales
4. Bisagras incorrectas → verificar peso vs capacidad bisagra

### Solución inmediata
1. Comprobar si las bisagras están bien apretadas
2. Si están flojas: retirar tornillos, rellenar agujeros con cola y palillos, volver a atornillar
3. Si el suelo tiene desnivel: calzar la bisagra inferior o cepillar la parte baja de la hoja
4. Cepillado máximo recomendado: 3mm (si necesita más, hay otro problema)

## Puerta que no cierra correctamente

### Causas probables
1. Marco no está a plomo → verificar
2. Resbalón/cerradura desalineado → ajustar cerradero
3. Jamba deformada → comprobar planitud

### Solución
1. Verificar plomo del marco en ambas jambas
2. Si el marco está correcto: ajustar cerradero (mover la chapa)
3. Si el marco no está a plomo: cuñar y reajustar

## Holgura excesiva entre hoja y marco

### Medidas correctas de holgura
- Lateral: 2-3mm por lado
- Superior: 2-3mm
- Inferior: 5-8mm (depende de suelo)
- Si la holgura es > 5mm en laterales: la hoja es pequeña

### Solución
- Holgura lateral excesiva: reubicar bisagras, añadir tapajuntas más anchos
- Holgura inferior excesiva: añadir burlete o bajopuerta
- Si la hoja es claramente pequeña: contactar taller para refabricación

## Puerta que se abre sola

### Causa
- Marco no está a plomo (la puerta tiende al lado del desplome)

### Solución
1. Verificar plomo
2. Si no se puede corregir: instalar retenedor magnético
3. Solución temporal: ajustar bisagras de muelle

## Ruido al cerrar

### Causas
1. Golpe metálico: resbalón no alineado
2. Vibración: holgura excesiva
3. Chirrido: bisagras sin lubricar

### Solución
1. Alinear cerradero
2. Instalar tope silencioso
3. Lubricar bisagras con grasa de litio (NO WD-40 que seca)
5.12 Script de Inicialización
Python

# scripts/seed_knowledge.py
"""
Script para inicializar la base de conocimiento.
Ejecutar una vez después del primer despliegue.
"""
import sys
import os
import time
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rag.indexer import KnowledgeIndexer
from core.config import settings


def wait_for_services():
    """Espera a que los servicios estén disponibles."""
    services = {
        "Ollama": f"{settings.LLM_BASE_URL}/api/tags",
        "ChromaDB": f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v1/heartbeat",
    }
    
    for name, url in services.items():
        print(f"Esperando {name}...", end=" ")
        for i in range(30):
            try:
                r = httpx.get(url, timeout=5)
                if r.status_code == 200:
                    print("✅")
                    break
            except:
                pass
            time.sleep(2)
        else:
            print(f"❌ {name} no disponible")
            return False
    
    return True


def pull_models():
    """Descarga los modelos necesarios en Ollama."""
    models = [settings.LLM_MODEL, settings.EMBEDDING_MODEL]
    
    for model in models:
        print(f"Descargando modelo {model}...")
        try:
            r = httpx.post(
                f"{settings.LLM_BASE_URL}/api/pull",
                json={"name": model},
                timeout=600,
            )
            print(f"  ✅ {model} descargado")
        except Exception as e:
            print(f"  ⚠️ Error descargando {model}: {e}")


def seed_knowledge():
    """Indexa la base de conocimiento inicial."""
    print("\nIndexando base de conocimiento...")
    indexer = KnowledgeIndexer()
    indexer.index_knowledge_base()
    print("✅ Base de conocimiento indexada")


if __name__ == "__main__":
    print("=" * 50)
    print("CarpinteroAI - Inicialización")
    print("=" * 50)
    
    if wait_for_services():
        pull_models()
        seed_knowledge()
        print("\n✅ Inicialización completada")
    else:
        print("\n❌ No se pudieron iniciar todos los servicios")
5.13 Makefile para operaciones
Makefile

# Makefile
.PHONY: help build up down seed logs test

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construir contenedores
	docker-compose build

up: ## Iniciar todos los servicios
	docker-compose up -d
	@echo "Esperando a que los servicios arranquen..."
	@sleep 10
	@echo "CarpinteroAI disponible en http://localhost:8000"

down: ## Parar todos los servicios
	docker-compose down

seed: ## Inicializar base de conocimiento
	docker-compose exec api python scripts/seed_knowledge.py

logs: ## Ver logs
	docker-compose logs -f api

logs-all: ## Ver todos los logs
	docker-compose logs -f

test: ## Ejecutar tests
	docker-compose exec api pytest tests/ -v

restart-api: ## Reiniciar solo la API
	docker-compose restart api

shell: ## Shell en el contenedor API
	docker-compose exec api bash

db-shell: ## Shell PostgreSQL
	docker-compose exec postgres psql -U carpintero -d carpintero_ai

status: ## Estado de los servicios
	docker-compose ps

backup: ## Backup de datos
	docker-compose exec postgres pg_dump -U carpintero carpintero_ai > backup_$$(date +%Y%m%d).sql
	@echo "Backup creado"

first-run: build up ## Primera ejecución completa
	@echo "Esperando a que Ollama esté listo (puede tardar varios minutos)..."
	@sleep 30
	$(MAKE) seed
	@echo ""
	@echo "=========================================="
	@echo "CarpinteroAI está listo!"
	@echo "Accede a: http://localhost:8000"
	@echo "=========================================="
6. Flujo de Aprendizaje Dinámico (Cómo funciona)
text

CICLO DE APRENDIZAJE
═══════════════════

1. CONVERSACIÓN
   Instalador: "La puerta del piso 3B roza porque el 
   premarco está 5mm desplomado a la izquierda"
   
   Agente: "Para un desplome de 5mm puedes compensar 
   moviendo la bisagra superior 2.5mm hacia fuera..."

2. EXTRACCIÓN AUTOMÁTICA
   El sistema detecta:
   - Tipo: problema_solucion  
   - Categoría: puertas
   - Problema: puerta roza por desplome de premarco
   - Solución: compensar moviendo bisagra
   - Confianza: 0.85

3. ALMACENAMIENTO
   Se guarda en tabla learned_knowledge
   Estado: pendiente de validación

4. VALIDACIÓN (encargado revisa)
   El encargado ve en el panel admin:
   "Nuevo conocimiento: Compensar desplome de 5mm 
   moviendo bisagra superior"
   → Aprueba ✅

5. INDEXACIÓN
   Se indexa en ChromaDB colección "aprendido"
   Ahora es buscable por RAG

6. DISPONIBILIDAD
   Otro instalador pregunta:
   "Tengo un premarco desplomado, ¿qué hago?"
   
   El RAG recupera:
   - Del conocimiento base: procedimiento general
   - De lo aprendido: "Un compañero resolvió un desplome 
     de 5mm moviendo la bisagra superior 2.5mm"
   
   → Respuesta más rica y práctica
7. Plan de Implementación por Fases
text

FASE 1 (Semana 1-2): MVP Funcional
────────────────────────────────────
□ Docker compose con Ollama + ChromaDB + PostgreSQL
□ Estructura de proyecto
□ RAG básico con knowledge base de puertas y parquet
□ API de chat (texto)
□ Frontend PWA básico
□ Prompts especializados por rol
→ RESULTADO: Se puede chatear y obtener respuestas con contexto

FASE 2 (Semana 3-4): Aprendizaje
──────────────────────────────────
□ Sistema de memoria conversacional
□ Extracción automática de conocimiento
□ Pipeline de validación (panel admin)
□ Indexación de conocimiento aprendido
□ Feedback del usuario (👍/👎)
→ RESULTADO: El sistema aprende de cada conversación

FASE 3 (Semana 5-6): Voz y Obra
─────────────────────────────────
□ Integración Whisper para voz
□ Optimización para móvil (PWA completa)
□ Service Worker para offline parcial
□ Quick actions contextuales por rol
□ Registro de incidencias por voz
→ RESULTADO: Usable en obra con voz

FASE 4 (Semana 7-8): Refinamiento
───────────────────────────────────
□ Knowledge base completa (rodapiés, taller)
□ Herramientas de diagnóstico mejoradas
□ Verificación preventiva con checklists
□ Estadísticas y dashboard para encargado
□ Integración básica con ERP (lectura)
→ RESULTADO: Sistema completo operativo
8. Resumen Ejecutivo
Aspecto	Decisión	Razón
RAG vs Fine-tuning	RAG dinámico	Aprendizaje continuo, sin reentrenamiento, rastreable
LLM	Ollama + Llama 3.1 8B	Gratuito, local, privacidad, suficiente para el dominio
Embeddings	nomic-embed-text (Ollama)	Gratuito, local, buen rendimiento en español
Vector DB	ChromaDB	Open source, simple, suficiente para el volumen
BD relacional	PostgreSQL	Robusto, gratuito, para memoria e incidencias
Voz	Whisper (OpenAI, local)	Gratuito, funciona offline, bueno en español
Frontend	PWA vanilla	Ligero, funciona offline, instalable en móvil
Aprendizaje	Extracción + Validación + RAG	Dinámico pero controlado (validación humana)

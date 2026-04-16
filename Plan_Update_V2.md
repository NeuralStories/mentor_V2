Plan de Ejecución para LLM Implementador
Sí, se puede aplicar rápidamente. La clave es que Supabase reemplaza PostgreSQL + ofrece storage + auth gratis, lo cual simplifica bastante la infraestructura.

Voy a crear las tareas exactas, secuenciales, para que un LLM las ejecute una por una.

Mapa de Infraestructura Simplificado con Supabase
text

ANTES (complejo):
  PostgreSQL + ChromaDB + Redis + Ollama + API + Worker

AHORA (simplificado):
  Supabase (BD + Auth + Storage) + ChromaDB + Ollama + API
  
  ┌─────────────┐     ┌──────────┐     ┌──────────┐
  │   Frontend   │────▶│   API    │────▶│  Ollama  │
  │   PWA        │     │  FastAPI │     │  LLM     │
  └─────────────┘     └────┬─────┘     └──────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌──────────┐  ┌──────────┐
              │ Supabase │  │ ChromaDB │
              │ BD+Auth  │  │ Vectores │
              │ +Storage │  │          │
              └──────────┘  └──────────┘
TAREA 0: Estructura Inicial del Proyecto
text

PROMPT PARA LLM IMPLEMENTADOR:

Crea la siguiente estructura de proyecto desde cero. 
El proyecto se llama "carpintero_ai".
Usa Python 3.11, FastAPI, Supabase, ChromaDB y Ollama.
Todo debe ser open source y gratuito.

Estructura exacta a crear:

carpintero_ai/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
├── requirements.txt
├── README.md
│
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── supabase_client.py
│   ├── llm/
│   │   ├── __init__.py
│   │   └── provider.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── retriever.py
│   │   └── indexer.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── conversation_memory.py
│   │   ├── knowledge_extractor.py
│   │   └── learning_pipeline.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── main_agent.py
│   │   ├── router.py
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── system_prompt.py
│   │       ├── instalador_puertas.py
│   │       ├── instalador_parquet.py
│   │       └── diagnostico.py
│   └── tools/
│       ├── __init__.py
│       ├── consulta_tecnica.py
│       ├── diagnostico.py
│       ├── guia_instalacion.py
│       ├── verificacion.py
│       └── registro_incidencia.py
│
├── api/
│   ├── __init__.py
│   ├── main.py
│   └── routes/
│       ├── __init__.py
│       ├── chat.py
│       ├── voice.py
│       ├── knowledge.py
│       └── admin.py
│
├── frontend/
│   ├── index.html
│   ├── manifest.json
│   └── sw.js
│
├── knowledge_base/
│   ├── procedimientos/
│   │   ├── instalacion_puertas/
│   │   │   ├── premarco.md
│   │   │   ├── marco_y_hoja.md
│   │   │   └── problemas_comunes.md
│   │   └── instalacion_parquet/
│   │       ├── preparacion_base.md
│   │       ├── colocacion.md
│   │       └── problemas_comunes.md
│   ├── materiales/
│   │   └── guia_materiales.md
│   └── problemas_soluciones/
│       ├── puertas.md
│       └── suelos.md
│
├── scripts/
│   ├── seed_knowledge.py
│   └── setup_supabase.py
│
└── infra/
    └── docker/
        └── Dockerfile.api

Crea TODOS los archivos con contenido placeholder (__init__.py vacíos, 
.py con imports básicos y clases/funciones stub).
El .gitignore debe incluir: .env, __pycache__, *.pyc, .venv/
El .env.example debe tener todas las variables necesarias.
TAREA 1: Configuración y Supabase Client
text

PROMPT PARA LLM IMPLEMENTADOR:

Archivo: core/config.py
Archivo: core/supabase_client.py
Archivo: .env.example

CONTEXTO:
- Usamos Supabase como base de datos principal (reemplaza PostgreSQL standalone)
- Supabase proporciona: PostgreSQL, Auth, Storage, Realtime
- Es gratuito en el tier free (500MB BD, 1GB storage)
- Usamos Ollama local para LLM (gratuito, open source)
- Usamos ChromaDB para vectores (gratuito, open source)

REQUISITOS:

1. core/config.py - Configuración centralizada con pydantic-settings:

```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CarpinteroAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Supabase
    SUPABASE_URL: str  # URL del proyecto Supabase
    SUPABASE_KEY: str  # anon key
    SUPABASE_SERVICE_KEY: str  # service_role key (para operaciones admin)
    
    # LLM - Ollama (local, gratuito)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.1:8b"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2048
    
    # Embeddings - Ollama (local, gratuito)
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # ChromaDB (local, gratuito)
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100
    
    # Whisper (local, gratuito)
    WHISPER_MODEL: str = "base"  # tiny/base/small
    
    # RAG
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.65
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    
    # Learning
    AUTO_LEARN: bool = True
    LEARNING_MIN_CONFIDENCE: float = 0.75
    REQUIRE_VALIDATION: bool = True
    
    # Knowledge Base
    KNOWLEDGE_BASE_PATH: str = "./knowledge_base"
    
    class Config:
        env_file = ".env"


settings = Settings()
core/supabase_client.py - Cliente Supabase reutilizable:
Python

from supabase import create_client, Client
from core.config import settings

_client: Client = None
_admin_client: Client = None


def get_supabase() -> Client:
    """Cliente Supabase con anon key (para operaciones normales)."""
    global _client
    if _client is None:
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client


def get_supabase_admin() -> Client:
    """Cliente Supabase con service key (para operaciones admin)."""
    global _admin_client
    if _admin_client is None:
        _admin_client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_SERVICE_KEY
        )
    return _admin_client
.env.example:
text

# Supabase (obtener de https://app.supabase.com)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGci...
SUPABASE_SERVICE_KEY=eyJhbGci...

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8100

# Whisper
WHISPER_MODEL=base

# App
DEBUG=true
AUTO_LEARN=true
REQUIRE_VALIDATION=true
Genera estos archivos completos, funcionales, sin placeholders.

text


---

## TAREA 2: Setup de Tablas en Supabase
PROMPT PARA LLM IMPLEMENTADOR:

Archivo: scripts/setup_supabase.py

CONTEXTO:
Necesitamos crear las tablas en Supabase para el sistema CarpinteroAI.
Supabase usa PostgreSQL, así que usamos SQL estándar.
Este script se ejecuta UNA VEZ para inicializar la base de datos.

TABLAS NECESARIAS:

conversations - Historial de conversaciones
learned_knowledge - Conocimiento extraído de chats
incidents - Incidencias reportadas
feedback - Feedback de usuarios sobre respuestas
users_config - Configuración de usuarios (rol, preferencias)
REQUISITOS:

Crear el script que:
a) Se conecte a Supabase
b) Ejecute el SQL para crear las tablas
c) Cree los índices necesarios
d) Configure RLS (Row Level Security) básico
e) Verifique que todo se creó correctamente

SQL de las tablas:

SQL

-- Conversaciones
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    user_role TEXT NOT NULL DEFAULT 'general',
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    intent TEXT DEFAULT 'general',
    context JSONB DEFAULT '{}',
    sources_used JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_session 
    ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user 
    ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created 
    ON conversations(created_at DESC);

-- Conocimiento aprendido
CREATE TABLE IF NOT EXISTS learned_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT DEFAULT 'general',
    source_type TEXT DEFAULT 'conversation',
    source_conversation_id UUID REFERENCES conversations(id),
    confidence FLOAT DEFAULT 0.5,
    validation_status TEXT DEFAULT 'pending' 
        CHECK (validation_status IN ('pending', 'approved', 'rejected')),
    validated_by TEXT,
    tags TEXT[] DEFAULT '{}',
    usage_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    validated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_knowledge_category 
    ON learned_knowledge(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_status 
    ON learned_knowledge(validation_status);
CREATE INDEX IF NOT EXISTS idx_knowledge_confidence 
    ON learned_knowledge(confidence DESC);

-- Incidencias
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reported_by TEXT NOT NULL,
    project_id TEXT,
    category TEXT NOT NULL,
    problem_type TEXT,
    description TEXT NOT NULL,
    solution_applied TEXT,
    solution_effective BOOLEAN,
    severity TEXT DEFAULT 'media' 
        CHECK (severity IN ('baja', 'media', 'alta', 'critica')),
    status TEXT DEFAULT 'abierta' 
        CHECK (status IN ('abierta', 'en_proceso', 'resuelta', 'cerrada')),
    location TEXT,
    photos TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_incidents_category 
    ON incidents(category);
CREATE INDEX IF NOT EXISTS idx_incidents_status 
    ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_project 
    ON incidents(project_id);

-- Feedback
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    is_positive BOOLEAN NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_conversation 
    ON feedback(conversation_id);

-- Configuración de usuarios
CREATE TABLE IF NOT EXISTS users_config (
    user_id TEXT PRIMARY KEY,
    display_name TEXT,
    default_role TEXT DEFAULT 'general',
    default_location TEXT DEFAULT 'taller',
    current_project TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vista útil: conocimiento aprobado con stats
CREATE OR REPLACE VIEW knowledge_approved AS
SELECT 
    lk.*,
    COUNT(DISTINCT c.id) as times_referenced
FROM learned_knowledge lk
LEFT JOIN conversations c ON c.sources_used::text LIKE '%' || lk.id::text || '%'
WHERE lk.validation_status = 'approved'
GROUP BY lk.id;

-- Vista útil: resumen de incidencias por categoría
CREATE OR REPLACE VIEW incidents_summary AS
SELECT 
    category,
    problem_type,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'resuelta') as resueltas,
    COUNT(*) FILTER (WHERE solution_effective = true) as efectivas
FROM incidents
GROUP BY category, problem_type
ORDER BY total DESC;
El script Python debe:

Python

#!/usr/bin/env python3
"""
Setup inicial de Supabase para CarpinteroAI.
Ejecutar una vez: python scripts/setup_supabase.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import get_supabase_admin
from core.config import settings


def create_tables():
    """Crea todas las tablas necesarias en Supabase."""
    client = get_supabase_admin()
    
    # El SQL de arriba ejecutado via rpc o directamente
    # Supabase permite ejecutar SQL raw via la API de management
    # O se puede hacer desde el dashboard SQL Editor
    
    sql_statements = [
        # Incluir cada CREATE TABLE como string
    ]
    
    # Ejecutar cada statement
    for sql in sql_statements:
        try:
            client.postgrest.rpc('exec_sql', {'query': sql}).execute()
            # O alternativamente, dar instrucciones para ejecutar 
            # desde el Supabase Dashboard > SQL Editor
        except Exception as e:
            print(f"Nota: {e}")
    
    print("Tablas creadas correctamente")


def verify_tables():
    """Verifica que las tablas existen."""
    client = get_supabase_admin()
    
    tables = ['conversations', 'learned_knowledge', 'incidents', 
              'feedback', 'users_config']
    
    for table in tables:
        try:
            result = client.table(table).select("*").limit(1).execute()
            print(f"  ✅ {table}")
        except Exception as e:
            print(f"  ❌ {table}: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("CarpinteroAI - Setup Supabase")
    print("=" * 50)
    
    print("\n📋 INSTRUCCIONES:")
    print("1. Ve a tu proyecto en https://app.supabase.com")
    print("2. Abre SQL Editor")
    print("3. Copia y ejecuta el SQL que se muestra a continuación")
    print("4. Vuelve aquí y ejecuta la verificación")
    
    print("\n" + "=" * 50)
    print("SQL A EJECUTAR EN SUPABASE:")
    print("=" * 50)
    
    # Imprimir el SQL completo
    print(SQL_COMPLETE)
    
    print("\n" + "=" * 50)
    input("\nPresiona Enter después de ejecutar el SQL en Supabase...")
    
    print("\nVerificando tablas...")
    verify_tables()
IMPORTANTE:

El SQL debe poder ejecutarse en el SQL Editor de Supabase Dashboard
El script Python debe imprimir el SQL para copiar/pegar
También debe verificar que las tablas se crearon
Incluir el SQL completo como constante en el script
Generar el archivo completo y funcional
text


---

## TAREA 3: Proveedor LLM (Ollama)
PROMPT PARA LLM IMPLEMENTADOR:

Archivo: core/llm/provider.py

CONTEXTO:

Usamos Ollama como proveedor de LLM, que es local y gratuito
Ollama permite ejecutar modelos como Llama 3.1, Mistral, etc.
También usamos Ollama para generar embeddings con nomic-embed-text
Necesitamos dos tipos de LLM:
a) LLM principal: para respuestas completas (llama3.1:8b)
b) LLM rápido: para clasificación de intención (mismo modelo pero con menos tokens)
Los embeddings se usan para el RAG
DEPENDENCIAS:

langchain-community (para Ollama integration)
httpx (para verificar conexión)
CÓDIGO A IMPLEMENTAR:

Python

"""
Proveedor de LLM y Embeddings usando Ollama (local, gratuito).

Modelos usados:
- LLM: llama3.1:8b (principal) 
- Embeddings: nomic-embed-text (para RAG)

Ambos se ejecutan localmente via Ollama.
"""
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.language_models import BaseLLM, BaseChatModel
from langchain_core.embeddings import Embeddings
from core.config import settings
import httpx
import logging

logger = logging.getLogger(__name__)


class LLMProvider:
    """
    Gestiona las instancias de LLM y Embeddings.
    Singleton pattern para reutilizar conexiones.
    """
    
    _chat_llm: BaseChatModel = None
    _fast_llm: BaseLLM = None
    _embeddings: Embeddings = None
    
    @classmethod
    def get_chat_llm(cls) -> BaseChatModel:
        """LLM principal para conversación (ChatOllama)."""
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
        """LLM rápido para clasificación y extracción (Ollama directo)."""
        if cls._fast_llm is None:
            cls._fast_llm = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.LLM_MODEL,
                temperature=0.1,
                num_predict=512,
                num_ctx=2048,
            )
            logger.info(f"Fast LLM inicializado: {settings.LLM_MODEL}")
        return cls._fast_llm
    
    @classmethod
    def get_embeddings(cls) -> Embeddings:
        """Embeddings para RAG."""
        if cls._embeddings is None:
            cls._embeddings = OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.EMBEDDING_MODEL,
            )
            logger.info(f"Embeddings inicializados: {settings.EMBEDDING_MODEL}")
        return cls._embeddings
    
    @classmethod
    def check_ollama_health(cls) -> dict:
        """Verifica que Ollama está disponible y los modelos descargados."""
        result = {
            "ollama_running": False,
            "models_available": [],
            "models_needed": [settings.LLM_MODEL, settings.EMBEDDING_MODEL],
            "models_missing": [],
        }
        
        try:
            response = httpx.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                timeout=5.0
            )
            if response.status_code == 200:
                result["ollama_running"] = True
                data = response.json()
                available = [m["name"] for m in data.get("models", [])]
                result["models_available"] = available
                
                for needed in result["models_needed"]:
                    # Comprobar con y sin tag
                    found = any(
                        needed in m or needed.split(":")[0] in m 
                        for m in available
                    )
                    if not found:
                        result["models_missing"].append(needed)
        except Exception as e:
            logger.error(f"Ollama no disponible: {e}")
        
        return result
    
    @classmethod
    def pull_model(cls, model_name: str) -> bool:
        """Descarga un modelo en Ollama."""
        try:
            logger.info(f"Descargando modelo: {model_name}")
            response = httpx.post(
                f"{settings.OLLAMA_BASE_URL}/api/pull",
                json={"name": model_name},
                timeout=600.0,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error descargando {model_name}: {e}")
            return False
    
    @classmethod
    def ensure_models(cls):
        """Asegura que los modelos necesarios están disponibles."""
        health = cls.check_ollama_health()
        
        if not health["ollama_running"]:
            raise ConnectionError(
                f"Ollama no está corriendo en {settings.OLLAMA_BASE_URL}. "
                "Ejecuta: ollama serve"
            )
        
        for model in health["models_missing"]:
            logger.info(f"Modelo {model} no encontrado, descargando...")
            success = cls.pull_model(model)
            if success:
                logger.info(f"Modelo {model} descargado correctamente")
            else:
                raise RuntimeError(f"No se pudo descargar el modelo {model}")
Genera el archivo completo.
Asegúrate de que:

Los imports son correctos
La clase es reutilizable como singleton
El health check funciona
El pull de modelos maneja timeouts largos (modelos pueden pesar GBs)
Los logs son informativos
text


---

## TAREA 4: Sistema RAG Completo
PROMPT PARA LLM IMPLEMENTADOR:

Archivos a crear:

core/rag/chunking.py
core/rag/embeddings.py
core/rag/retriever.py
core/rag/indexer.py
CONTEXTO:
Este es el sistema RAG (Retrieval Augmented Generation) del proyecto CarpinteroAI.
Es el componente MÁS IMPORTANTE del sistema.
Su función es:

Indexar documentación técnica de carpintería (markdown)
Buscar información relevante cuando un trabajador hace una consulta
Indexar conocimiento aprendido de conversaciones
Permitir búsqueda semántica por similitud
STACK:

ChromaDB como base de datos vectorial (local, gratuito)
Ollama + nomic-embed-text para generar embeddings (local, gratuito)
LangChain text splitters para fragmentación
COLECCIONES EN CHROMADB:

"procedimientos" - Guías paso a paso de instalación
"problemas_soluciones" - Base de problemas conocidos y sus soluciones
"materiales" - Información sobre materiales
"incidencias" - Incidencias registradas (se indexan para buscar soluciones similares)
"aprendido" - Conocimiento extraído de conversaciones (el sistema aprende)
REQUISITOS DETALLADOS:

--- core/rag/chunking.py ---
Fragmentación inteligente de documentos markdown.

Usar MarkdownHeaderTextSplitter para respetar estructura
Usar RecursiveCharacterTextSplitter para chunks grandes
Tamaño de chunk: 512 caracteres con overlap de 50
Cada chunk debe mantener su metadata (categoría, sección, archivo origen)
Enriquecer el contenido del chunk añadiendo contexto
(ej: "Categoría: puertas\nSección: premarco\n[contenido]")
para que los embeddings capturen mejor el significado
Python

class SmartChunker:
    def __init__(self):
        # Configurar splitters
        
    def chunk_document(self, content: str, metadata: dict) -> list[dict]:
        """
        Entrada: contenido markdown + metadata del archivo
        Salida: lista de dicts con:
            - "content": texto del chunk
            - "enriched_content": texto enriquecido (para embedding)
            - "metadata": metadata del chunk
        """
        
    def _enrich_chunk(self, chunk: dict) -> str:
        """Añade contexto al chunk para mejor búsqueda semántica."""
--- core/rag/embeddings.py ---
Motor de embeddings usando Ollama.

Python

class EmbeddingEngine:
    def __init__(self):
        # Usar LLMProvider.get_embeddings()
        
    def embed_text(self, text: str) -> list[float]:
        """Genera embedding para un texto."""
        
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings para múltiples textos (batch)."""
        
    def embed_query(self, query: str) -> list[float]:
        """Embedding para query de búsqueda. 
        Preprocesa añadiendo contexto de dominio."""
--- core/rag/retriever.py ---
Búsqueda semántica en ChromaDB.

Python

class RAGRetriever:
    def __init__(self):
        # Conectar con ChromaDB
        # Crear/obtener colecciones
        
    def search(
        self,
        query: str,
        collections: list[str] = None,  # None = todas
        top_k: int = 5,
        filters: dict = None,
        min_similarity: float = 0.65,
    ) -> list[dict]:
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
        
    def add_document(self, collection: str, content: str, 
                     metadata: dict, doc_id: str):
        """Añade un documento a una colección."""
        
    def add_documents_batch(self, collection: str, 
                            documents: list[dict]):
        """Añade múltiples documentos (más eficiente)."""
--- core/rag/indexer.py ---
Indexador que conecta chunking con retriever.

Python

class KnowledgeIndexer:
    def __init__(self):
        # Inicializar chunker y retriever
        
    def index_knowledge_base(self, base_path: str = None):
        """
        Indexa toda la base de conocimiento desde archivos markdown.
        Recorre la carpeta knowledge_base/ y indexa cada archivo.
        
        Mapeo de carpetas a colecciones:
        - procedimientos/ → "procedimientos"
        - materiales/ → "materiales"  
        - problemas_soluciones/ → "problemas_soluciones"
        """
        
    def index_single_file(self, file_path: str, collection: str) -> int:
        """Indexa un archivo individual. Retorna número de chunks."""
        
    def index_learned_knowledge(self, content: str, metadata: dict):
        """Indexa conocimiento aprendido de conversaciones.
        Va a la colección 'aprendido'."""
        
    def index_incident(self, description: str, solution: str, 
                       metadata: dict):
        """Indexa una incidencia resuelta para futuras consultas.
        Va a la colección 'incidencias'."""
IMPORTANTE:

Todos los archivos deben ser completos y funcionales
Usar from core.config import settings para configuración
Usar from core.llm.provider import LLMProvider para embeddings
ChromaDB se conecta via HTTP (HttpClient)
Manejar errores de conexión gracefully
Logs informativos en cada operación
Los IDs de documentos se generan con hashlib.md5
Generar los 4 archivos completos
text


---

## TAREA 5: Sistema de Memoria y Aprendizaje
PROMPT PARA LLM IMPLEMENTADOR:

Archivos a crear:

core/memory/conversation_memory.py
core/memory/knowledge_extractor.py
core/memory/learning_pipeline.py
CONTEXTO:
Este es el sistema que hace que CarpinteroAI APRENDA de cada conversación.
Es lo que lo diferencia de un chatbot genérico.

FLUJO:

Un trabajador chatea con el sistema
La conversación se guarda en Supabase (tabla conversations)
Un extractor analiza la conversación buscando conocimiento útil
Si encuentra conocimiento valioso (confianza > 0.75):
a. Lo guarda en Supabase (tabla learned_knowledge)
b. Si no requiere validación → lo indexa en ChromaDB directamente
c. Si requiere validación → queda pendiente hasta que el encargado apruebe
Una vez aprobado, se indexa en ChromaDB colección "aprendido"
Las siguientes consultas ya tienen acceso a ese conocimiento
EJEMPLO REAL:

Instalador dice: "El premarco del piso 4A estaba desplomado 8mm,
tuve que calzar con cuñas de 4mm en la bisagra inferior y
4mm en la superior para compensar"
El sistema extrae:
{
tipo: "problema_solucion",
categoría: "puertas",
título: "Compensar desplome de premarco con cuñas en bisagras",
contenido: "Para un desplome de 8mm, calzar con cuñas de 4mm
en bisagra inferior y 4mm en superior",
confianza: 0.85
}
Se guarda y cuando otro instalador pregunte sobre premarcos
desplomados, esta solución aparecerá
IMPORTANTE: Usamos SUPABASE, no SQLAlchemy directo.

--- core/memory/conversation_memory.py ---

Python

"""
Gestión de memoria conversacional usando Supabase.
Guarda todas las conversaciones y permite recuperar historial.
"""
from typing import Optional
from core.supabase_client import get_supabase
from core.config import settings
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Memoria conversacional persistente en Supabase."""
    
    def __init__(self):
        self.client = get_supabase()
    
    def save_interaction(
        self,
        session_id: str,
        user_id: str,
        user_role: str,
        user_message: str,
        assistant_response: str,
        intent: str = "general",
        context: dict = None,
        sources_used: list = None,
    ) -> str:
        """
        Guarda una interacción completa en Supabase.
        Retorna el ID del registro.
        """
        record_id = str(uuid.uuid4())
        
        data = {
            "id": record_id,
            "session_id": session_id,
            "user_id": user_id,
            "user_role": user_role,
            "user_message": user_message,
            "assistant_response": assistant_response,
            "intent": intent,
            "context": context or {},
            "sources_used": sources_used or [],
        }
        
        try:
            self.client.table("conversations").insert(data).execute()
            logger.info(f"Conversación guardada: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"Error guardando conversación: {e}")
            return record_id
    
    def get_session_history(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Obtiene el historial de mensajes de una sesión.
        Retorna lista de dicts con role y content 
        (formato compatible con LangChain messages).
        """
        try:
            result = (
                self.client.table("conversations")
                .select("user_message, assistant_response, created_at")
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            history = []
            for record in reversed(result.data):
                history.append({
                    "role": "user",
                    "content": record["user_message"]
                })
                history.append({
                    "role": "assistant", 
                    "content": record["assistant_response"]
                })
            
            return history
        
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
    
    def save_feedback(
        self,
        conversation_id: str,
        is_positive: bool,
        comment: str = None,
    ):
        """Guarda feedback del usuario sobre una respuesta."""
        try:
            self.client.table("feedback").insert({
                "conversation_id": conversation_id,
                "is_positive": is_positive,
                "comment": comment,
            }).execute()
        except Exception as e:
            logger.error(f"Error guardando feedback: {e}")
    
    def save_incident(
        self,
        reported_by: str,
        category: str,
        description: str,
        problem_type: str = None,
        project_id: str = None,
        severity: str = "media",
        location: str = None,
    ) -> str:
        """Guarda una incidencia."""
        incident_id = str(uuid.uuid4())
        
        try:
            self.client.table("incidents").insert({
                "id": incident_id,
                "reported_by": reported_by,
                "category": category,
                "description": description,
                "problem_type": problem_type,
                "project_id": project_id,
                "severity": severity,
                "location": location,
            }).execute()
            
            logger.info(f"Incidencia guardada: {incident_id}")
            return incident_id
        except Exception as e:
            logger.error(f"Error guardando incidencia: {e}")
            return incident_id
--- core/memory/knowledge_extractor.py ---

Python

"""
Extrae conocimiento útil de las conversaciones usando el LLM.
Analiza cada interacción y determina si contiene información 
valiosa que debería ser aprendida por el sistema.
"""
from typing import Optional
from core.llm.provider import LLMProvider
import json
import logging

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Eres un experto en carpintería, instalación de puertas, 
parquet y rodapiés. 

Analiza esta conversación entre un trabajador y el asistente.
Determina si contiene CONOCIMIENTO TÉCNICO NUEVO Y ÚTIL que podría 
ayudar a otros trabajadores en el futuro.

== CONVERSACIÓN ==
Trabajador ({user_role}): {user_message}
Asistente: {assistant_response}
================

Responde ÚNICAMENTE con JSON válido:

Si NO hay conocimiento útil:
{{"has_knowledge": false}}

Si SÍ hay conocimiento útil:
{{
    "has_knowledge": true,
    "items": [
        {{
            "type": "procedimiento|problema_solucion|consejo|medida|material",
            "category": "puertas|parquet|rodapies|taller|general",
            "title": "Título breve y descriptivo",
            "content": "Descripción completa del conocimiento. Incluir medidas, pasos o detalles específicos.",
            "confidence": 0.0 a 1.0,
            "tags": ["tag1", "tag2"]
        }}
    ]
}}

REGLAS:
- NO extraer saludos ni charla trivial
- NO extraer información obvia o genérica
- SÍ extraer: soluciones a problemas reales, trucos del oficio, 
  medidas específicas, procedimientos descubiertos en obra
- La confianza debe reflejar qué tan útil y fiable es la información
- Responde SOLO con JSON, sin texto adicional"""


class KnowledgeExtractor:
    """Extrae conocimiento técnico de conversaciones."""
    
    def __init__(self):
        self.llm = LLMProvider.get_fast_llm()
    
    def extract(
        self,
        user_message: str,
        assistant_response: str,
        user_role: str = "general",
    ) -> Optional[list[dict]]:
        """
        Analiza una interacción y extrae conocimiento útil.
        
        Retorna None si no hay conocimiento útil.
        Retorna lista de items de conocimiento si los hay.
        """
        try:
            prompt = EXTRACTION_PROMPT.format(
                user_role=user_role,
                user_message=user_message,
                assistant_response=assistant_response,
            )
            
            response = self.llm.invoke(prompt)
            result = self._parse_json(response)
            
            if result and result.get("has_knowledge"):
                items = result.get("items", [])
                # Filtrar por confianza mínima
                valid_items = [
                    item for item in items
                    if item.get("confidence", 0) >= settings.LEARNING_MIN_CONFIDENCE
                ]
                return valid_items if valid_items else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error en extracción: {e}")
            return None
    
    def _parse_json(self, text: str) -> Optional[dict]:
        """Parsea JSON de la respuesta del LLM."""
        try:
            # Buscar JSON en la respuesta
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except json.JSONDecodeError as e:
            logger.warning(f"Error parseando JSON: {e}")
        return None
--- core/memory/learning_pipeline.py ---

Python

"""
Pipeline de aprendizaje continuo.
Orquesta el flujo completo: 
  conversación → extracción → almacenamiento → validación → indexación

Este es el cerebro del aprendizaje del sistema.
"""
from typing import Optional
from core.memory.conversation_memory import ConversationMemory
from core.memory.knowledge_extractor import KnowledgeExtractor
from core.rag.indexer import KnowledgeIndexer
from core.supabase_client import get_supabase
from core.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)


class LearningPipeline:
    """Pipeline completo de aprendizaje."""
    
    def __init__(self):
        self.memory = ConversationMemory()
        self.extractor = KnowledgeExtractor()
        self.indexer = KnowledgeIndexer()
        self.client = get_supabase()
    
    def process_interaction(
        self,
        session_id: str,
        user_id: str,
        user_role: str,
        user_message: str,
        assistant_response: str,
        intent: str = "general",
        context: dict = None,
        sources_used: list = None,
    ) -> str:
        """
        Procesa una interacción completa:
        1. Guarda la conversación
        2. Intenta extraer conocimiento
        3. Si hay conocimiento → lo guarda y opcionalmente lo indexa
        
        Retorna el ID de la conversación.
        """
        
        # 1. Guardar conversación
        conversation_id = self.memory.save_interaction(
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
        if settings.AUTO_LEARN:
            self._try_extract_knowledge(
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_response=assistant_response,
                user_role=user_role,
            )
        
        return conversation_id
    
    def _try_extract_knowledge(
        self,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        user_role: str,
    ):
        """Intenta extraer y almacenar conocimiento."""
        try:
            items = self.extractor.extract(
                user_message=user_message,
                assistant_response=assistant_response,
                user_role=user_role,
            )
            
            if not items:
                return
            
            for item in items:
                knowledge_id = self._store_knowledge(item, conversation_id)
                
                # Si no requiere validación, indexar directamente
                if not settings.REQUIRE_VALIDATION:
                    self._index_knowledge_item(item)
                    logger.info(
                        f"Conocimiento indexado directamente: "
                        f"{item.get('title', 'sin título')}"
                    )
                else:
                    logger.info(
                        f"Conocimiento pendiente de validación: "
                        f"{item.get('title', 'sin título')}"
                    )
                    
        except Exception as e:
            logger.error(f"Error en extracción de conocimiento: {e}")
    
    def _store_knowledge(self, item: dict, conversation_id: str) -> str:
        """Guarda un item de conocimiento en Supabase."""
        knowledge_id = str(uuid.uuid4())
        
        try:
            self.client.table("learned_knowledge").insert({
                "id": knowledge_id,
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "category": item.get("category", "general"),
                "subcategory": item.get("type", "general"),
                "source_conversation_id": conversation_id,
                "confidence": item.get("confidence", 0.5),
                "validation_status": "pending" if settings.REQUIRE_VALIDATION 
                                     else "approved",
                "tags": item.get("tags", []),
            }).execute()
            
            return knowledge_id
        except Exception as e:
            logger.error(f"Error almacenando conocimiento: {e}")
            return knowledge_id
    
    def _index_knowledge_item(self, item: dict):
        """Indexa un item de conocimiento en ChromaDB."""
        content = f"{item.get('title', '')}\n\n{item.get('content', '')}"
        
        self.indexer.index_learned_knowledge(
            content=content,
            metadata={
                "type": item.get("type", "general"),
                "category": item.get("category", "general"),
                "tags": item.get("tags", []),
                "source": "learned",
            },
        )
    
    # === MÉTODOS PARA VALIDACIÓN (usados por el encargado) ===
    
    def get_pending_validations(self) -> list[dict]:
        """Obtiene conocimiento pendiente de validar."""
        try:
            result = (
                self.client.table("learned_knowledge")
                .select("*")
                .eq("validation_status", "pending")
                .order("created_at", desc=True)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error obteniendo pendientes: {e}")
            return []
    
    def validate_knowledge(
        self, 
        knowledge_id: str, 
        approved: bool, 
        validated_by: str = "admin"
    ):
        """
        Aprueba o rechaza conocimiento.
        Si se aprueba, lo indexa en ChromaDB.
        """
        status = "approved" if approved else "rejected"
        
        try:
            # Actualizar estado
            self.client.table("learned_knowledge").update({
                "validation_status": status,
                "validated_by": validated_by,
                "validated_at": "now()",
            }).eq("id", knowledge_id).execute()
            
            # Si aprobado, indexar
            if approved:
                # Obtener el registro
                result = (
                    self.client.table("learned_knowledge")
                    .select("*")
                    .eq("id", knowledge_id)
                    .single()
                    .execute()
                )
                
                if result.data:
                    self._index_knowledge_item({
                        "title": result.data["title"],
                        "content": result.data["content"],
                        "type": result.data["subcategory"],
                        "category": result.data["category"],
                        "tags": result.data.get("tags", []),
                    })
                    logger.info(f"Conocimiento {knowledge_id} aprobado e indexado")
            else:
                logger.info(f"Conocimiento {knowledge_id} rechazado")
                
        except Exception as e:
            logger.error(f"Error validando conocimiento: {e}")
    
    def get_learning_stats(self) -> dict:
        """Estadísticas del sistema de aprendizaje."""
        try:
            total = self.client.table("learned_knowledge")\
                .select("id", count="exact").execute()
            approved = self.client.table("learned_knowledge")\
                .select("id", count="exact")\
                .eq("validation_status", "approved").execute()
            pending = self.client.table("learned_knowledge")\
                .select("id", count="exact")\
                .eq("validation_status", "pending").execute()
            rejected = self.client.table("learned_knowledge")\
                .select("id", count="exact")\
                .eq("validation_status", "rejected").execute()
            
            return {
                "total": total.count,
                "approved": approved.count,
                "pending": pending.count,
                "rejected": rejected.count,
            }
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {"total": 0, "approved": 0, "pending": 0, "rejected": 0}
IMPORTANTE:

Usar Supabase client, NO SQLAlchemy
from core.supabase_client import get_supabase
from core.config import settings
Manejar errores gracefully (el sistema no debe caer si falla el aprendizaje)
Logs informativos
Los 3 archivos deben ser completos y funcionales
text


---

## TAREA 6: Prompts Especializados
PROMPT PARA LLM IMPLEMENTADOR:

Archivos a crear:

core/agent/prompts/system_prompt.py
core/agent/prompts/instalador_puertas.py
core/agent/prompts/instalador_parquet.py
core/agent/prompts/diagnostico.py
CONTEXTO:
Estos son los prompts que definen el comportamiento del agente CarpinteroAI.
Son CRÍTICOS para la calidad de las respuestas.
El agente NO es un chatbot genérico - es un compañero de trabajo experto.

REQUISITOS:

--- system_prompt.py ---
Prompt principal del sistema. Define:

Identidad: compañero de trabajo experto en carpintería
Tono: directo, práctico, sin rodeos (como un jefe de obra hablaría)
Idioma: español castellano, con vocabulario del oficio
Formato: respuestas cortas y estructuradas
Variables que se inyectan: {user_role}, {location}, {rag_context}, {history}
Reglas: siempre confirmar medidas, avisar de errores, usar listas para pasos
Capacidades: consulta, diagnóstico, guía, verificación, incidencias
El prompt DEBE incluir estas variables entre llaves para ser formateado:

{user_role}: rol del trabajador
{current_project}: proyecto actual
{location}: taller u obra
{rag_context}: información del RAG
{conversation_history}: historial reciente
--- instalador_puertas.py ---
Contexto adicional cuando el usuario es instalador de puertas.
Incluir:

Conocimiento prioritario (premarcos, marcos, hojas, bisagras, cerraduras)
Problemas frecuentes específicos
Medidas estándar (holguras, tolerancias)
Protocolo ante problemas en obra
--- instalador_parquet.py ---
Contexto adicional cuando el usuario es instalador de parquet.
Incluir:

Sistemas de instalación (flotante, pegado, clavado)
Preparación de base (humedades, nivelación)
Juntas de dilatación (medidas estándar)
Problemas frecuentes
--- diagnostico.py ---
Prompt específico para la herramienta de diagnóstico.
Estructura de respuesta obligatoria:

Problema identificado
Causa más probable
Solución recomendada (pasos concretos)
Plan B si no funciona
Cómo evitarlo en el futuro
Cada archivo debe exportar el prompt como constante string.
Generar archivos completos con prompts detallados y realistas.
El conocimiento técnico incluido debe ser CORRECTO (medidas reales,
procedimientos reales de carpintería).

text


---

## TAREA 7: Router de Intenciones
PROMPT PARA LLM IMPLEMENTADOR:

Archivo: core/agent/router.py

CONTEXTO:
El router clasifica cada mensaje del usuario en una intención
para saber qué tipo de respuesta dar y qué herramienta usar.

INTENCIONES POSIBLES:

consulta_tecnica - Pregunta sobre medidas, materiales, especificaciones
diagnostico - Tiene un problema y necesita ayuda
guia_instalacion - Necesita instrucciones paso a paso
verificacion - Quiere confirmar algo antes de ejecutarlo
incidencia - Reporta un problema o fallo
general - Saludo u otra cosa
IMPLEMENTACIÓN:
Usar PRIMERO clasificación por keywords (rápido, sin LLM).
Si no es concluyente, usar LLM para clasificar.

Python

"""
Router de intenciones para CarpinteroAI.
Clasifica cada mensaje en una categoría para dirigirlo
a la herramienta correcta.

Estrategia dual:
1. Clasificación por keywords (< 1ms)
2. Clasificación por LLM (solo si keywords no es concluyente)
"""
from core.llm.provider import LLMProvider
import logging

logger = logging.getLogger(__name__)

VALID_INTENTS = [
    "consulta_tecnica",
    "diagnostico", 
    "guia_instalacion",
    "verificacion",
    "incidencia",
    "general",
]

# Keywords para clasificación rápida
INTENT_KEYWORDS = {
    "diagnostico": [
        "problema", "no encaja", "no cuadra", "roza", "no cierra",
        "se levanta", "ruido", "hueco mal", "desnivel", "torcido",
        "no vale", "mal", "error", "fallo", "roto", "dañado",
        "no funciona", "se ha roto", "no ajusta", "descuadrado",
        "se mueve", "flojo", "holgura", "cruje", "chirría",
    ],
    "guia_instalacion": [
        "cómo se", "como se", "cómo instalo", "como instalo",
        "pasos para", "procedimiento", "instrucciones",
        "cómo pongo", "como pongo", "cómo coloco", "como coloco",
        "cómo hago", "como hago", "explicame", "explícame",
        "tutorial", "guía", "guia",
    ],
    "verificacion": [
        "está bien", "esta bien", "es correcto", "puedo hacer",
        "debería", "vale así", "confirma", "verificar", "comprobar",
        "es normal", "es suficiente", "basta con",
    ],
    "incidencia": [
        "reportar", "incidencia", "falta material", "no hay stock",
        "se ha roto", "registrar", "anotar", "falta", "necesito pedir",
        "no ha llegado", "pieza equivocada",
    ],
    "consulta_tecnica": [
        "qué medida", "que medida", "cuánto", "cuanto",
        "qué material", "que material", "especificación",
        "ficha técnica", "tolerancia", "qué tipo", "que tipo",
        "cuál es", "cual es", "dimensiones",
    ],
}

ROUTER_PROMPT = """Clasifica esta consulta de un trabajador de 
carpintería/instalación en UNA categoría:

- consulta_tecnica: pregunta sobre medidas, materiales, especificaciones
- diagnostico: tiene un problema y necesita ayuda para resolverlo
- guia_instalacion: necesita instrucciones paso a paso
- verificacion: quiere confirmar algo antes de ejecutarlo
- incidencia: reporta un problema, falta de material o fallo
- general: saludo, consulta no técnica u otra cosa

Consulta: "{message}"

Responde SOLO con el nombre de la categoría."""


class IntentRouter:
    def __init__(self):
        self.fast_llm = LLMProvider.get_fast_llm()
    
    async def classify(self, message: str) -> str:
        """
        Clasifica la intención del mensaje.
        Primero intenta por keywords, luego por LLM.
        """
        # 1. Intentar por keywords
        intent = self._classify_by_keywords(message)
        if intent:
            logger.debug(f"Intent por keywords: {intent}")
            return intent
        
        # 2. Usar LLM
        intent = await self._classify_by_llm(message)
        logger.debug(f"Intent por LLM: {intent}")
        return intent
    
    def _classify_by_keywords(self, message: str) -> str | None:
        """Clasificación rápida por keywords."""
        msg = message.lower()
        
        scores = {}
        for intent, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in msg)
            if score > 0:
                scores[intent] = score
        
        if scores:
            # Retornar el intent con más coincidencias
            return max(scores, key=scores.get)
        
        return None
    
    async def _classify_by_llm(self, message: str) -> str:
        """Clasificación por LLM (más lenta pero más precisa)."""
        try:
            prompt = ROUTER_PROMPT.format(message=message)
            response = self.fast_llm.invoke(prompt)
            
            intent = response.strip().lower().replace(" ", "_")
            
            # Validar
            if intent in VALID_INTENTS:
                return intent
            
            # Buscar parcial
            for valid in VALID_INTENTS:
                if valid in intent:
                    return valid
            
            return "general"
        except Exception as e:
            logger.error(f"Error en clasificación LLM: {e}")
            return "general"
Genera el archivo completo y funcional.

text


---

## TAREA 8: Herramientas del Agente (Tools)
PROMPT PARA LLM IMPLEMENTADOR:

Archivos a crear:

core/tools/consulta_tecnica.py
core/tools/diagnostico.py
core/tools/guia_instalacion.py
core/tools/verificacion.py
core/tools/registro_incidencia.py
CONTEXTO:
Las tools son funciones especializadas que el agente usa según la intención.
Cada tool recibe la consulta + contexto RAG y genera una respuesta estructurada.

PATRÓN COMÚN para todas las tools:

Python

class NombreTool:
    def __init__(self, retriever, llm):
        self.retriever = retriever  # RAGRetriever
        self.llm = llm  # LLM para generar respuesta

    async def execute(
        self,
        query: str,           # Lo que preguntó el usuario
        user_role: str,       # Su rol
        rag_context: list[dict] = None,  # Resultados RAG
    ) -> str:
        """Ejecuta la herramienta y retorna texto adicional para el agente."""
DETALLE DE CADA TOOL:

consulta_tecnica.py

Para preguntas directas sobre medidas, materiales, especificaciones
Prompt: extraer respuesta precisa del contexto RAG
Si hay medidas, incluir tolerancias
Si hay alternativas, listarlas
diagnostico.py

Para problemas en taller u obra
Prompt obligatorio con estructura:
Problema identificado
Causa más probable
Solución paso a paso
Plan B
Prevención
Tono: urgente y práctico (el operario está en obra)
guia_instalacion.py

Para instrucciones paso a paso
Prompt que genera:
Materiales necesarios
Herramientas
Pasos numerados
Puntos críticos (⚠️)
Verificación final (✅)
verificacion.py

Para validar algo antes de ejecutar
Prompt que responde con:
✅ CORRECTO + explicación
⚠️ ATENCIÓN + qué revisar
❌ INCORRECTO + por qué y qué hacer
Especialmente estricto con medidas y tolerancias
registro_incidencia.py

Diferente a las demás: no usa LLM directamente
Extrae datos de la incidencia del mensaje
Guarda en Supabase via ConversationMemory
Indexa en ChromaDB para futuras consultas
Retorna confirmación y pide datos adicionales si faltan
Necesita: from core.memory.conversation_memory import ConversationMemory
Necesita: from core.rag.indexer import KnowledgeIndexer
Genera los 5 archivos completos y funcionales.
Cada tool debe tener su prompt especializado como constante.
Usar from core.config import settings donde sea necesario.

text


---

## TAREA 9: Agente Principal (Orquestador)
PROMPT PARA LLM IMPLEMENTADOR:

Archivo: core/agent/main_agent.py

CONTEXTO:
Este es el CEREBRO del sistema. El agente principal que:

Recibe un mensaje del usuario
Clasifica la intención (router)
Busca información relevante (RAG)
Recupera historial de conversación (memory)
Ejecuta la herramienta apropiada (tools)
Genera la respuesta final (LLM)
Lanza el proceso de aprendizaje (learning pipeline)
Es el componente que conecta TODOS los demás.

DEPENDENCIAS:

core.llm.provider.LLMProvider
core.rag.retriever.RAGRetriever
core.memory.conversation_memory.ConversationMemory
core.memory.learning_pipeline.LearningPipeline
core.agent.router.IntentRouter
core.agent.prompts.system_prompt
core.agent.prompts.instalador_puertas
core.agent.prompts.instalador_parquet
core.tools.* (todas las tools)
langchain_core.messages (HumanMessage, AIMessage, SystemMessage)
IMPLEMENTACIÓN:

Python

"""
Agente principal de CarpinteroAI.
Orquesta todos los componentes para responder consultas.
"""
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from core.llm.provider import LLMProvider
from core.rag.retriever import RAGRetriever
from core.memory.learning_pipeline import LearningPipeline
from core.agent.router import IntentRouter
from core.agent.prompts.system_prompt import SYSTEM_PROMPT
from core.agent.prompts.instalador_puertas import PUERTAS_CONTEXT
from core.agent.prompts.instalador_parquet import PARQUET_CONTEXT
from core.tools.consulta_tecnica import ConsultaTecnicaTool
from core.tools.diagnostico import DiagnosticoTool
from core.tools.guia_instalacion import GuiaInstalacionTool
from core.tools.verificacion import VerificacionTool
from core.tools.registro_incidencia import RegistroIncidenciaTool
from core.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)

# Mapeo de roles a contextos adicionales
ROLE_CONTEXTS = {
    "instalador_puertas": PUERTAS_CONTEXT,
    "instalador_parquet": PARQUET_CONTEXT,
    "carpintero_taller": "",  # TODO: crear prompt específico
    "instalador_rodapies": "",  # TODO
    "encargado": "",  # TODO
    "general": "",
}

# Mapeo de intenciones a colecciones RAG prioritarias
INTENT_COLLECTIONS = {
    "consulta_tecnica": ["procedimientos", "materiales", "aprendido"],
    "diagnostico": ["problemas_soluciones", "incidencias", "aprendido"],
    "guia_instalacion": ["procedimientos", "aprendido"],
    "verificacion": ["procedimientos", "problemas_soluciones"],
    "incidencia": ["incidencias", "problemas_soluciones"],
    "general": None,  # Todas
}

# Mapeo de intenciones a tools
INTENT_TOOLS = {
    "consulta_tecnica": "consulta",
    "diagnostico": "diagnostico",
    "guia_instalacion": "guia",
    "verificacion": "verificacion",
    "incidencia": "incidencia",
}


class CarpinteroAgent:
    """Agente principal del sistema."""
    
    def __init__(self):
        self.chat_llm = LLMProvider.get_chat_llm()
        self.retriever = RAGRetriever()
        self.learning = LearningPipeline()
        self.router = IntentRouter()
        
        # Inicializar tools
        llm = LLMProvider.get_fast_llm()
        self.tools = {
            "consulta": ConsultaTecnicaTool(self.retriever, llm),
            "diagnostico": DiagnosticoTool(self.retriever, llm),
            "guia": GuiaInstalacionTool(self.retriever, llm),
            "verificacion": VerificacionTool(self.retriever, llm),
            "incidencia": RegistroIncidenciaTool(),
        }
    
    async def process_message(
        self,
        message: str,
        session_id: str = None,
        user_id: str = "default",
        user_role: str = "general",
        project_id: str = None,
        location: str = "taller",
    ) -> dict:
        """
        Procesa un mensaje y genera una respuesta completa.
        
        Retorna:
        {
            "response": "texto de respuesta",
            "intent": "tipo de intención detectada",
            "sources": [...fuentes RAG usadas],
            "session_id": "id de sesión",
            "conversation_id": "id de la conversación guardada"
        }
        """
        session_id = session_id or str(uuid.uuid4())
        
        try:
            # 1. Clasificar intención
            intent = await self.router.classify(message)
            logger.info(f"Intent: {intent} | Rol: {user_role} | Msg: {message[:80]}...")
            
            # 2. Buscar en RAG
            collections = INTENT_COLLECTIONS.get(intent)
            rag_results = self.retriever.search(
                query=message,
                collections=collections,
                top_k=settings.RAG_TOP_K,
            )
            
            # 3. Obtener historial
            history = self.learning.memory.get_session_history(
                session_id, limit=6
            )
            
            # 4. Ejecutar tool si aplica
            tool_output = await self._run_tool(
                intent, message, user_role, rag_results
            )
            
            # 5. Construir prompt del sistema
            system_prompt = self._build_prompt(
                user_role=user_role,
                project_id=project_id,
                location=location,
                rag_results=rag_results,
                history=history,
            )
            
            # 6. Construir mensajes para el LLM
            messages = [SystemMessage(content=system_prompt)]
            
            for h in history:
                if h["role"] == "user":
                    messages.append(HumanMessage(content=h["content"]))
                else:
                    messages.append(AIMessage(content=h["content"]))
            
            # Mensaje actual (con output de tool si existe)
            user_content = message
            if tool_output:
                user_content += (
                    f"\n\n[Información del sistema - no mostrar este "
                    f"encabezado al usuario]:\n{tool_output}"
                )
            
            messages.append(HumanMessage(content=user_content))
            
            # 7. Generar respuesta
            response = self.chat_llm.invoke(messages)
            response_text = (
                response.content 
                if hasattr(response, 'content') 
                else str(response)
            )
            
            # 8. Guardar y aprender (async en background idealmente)
            conversation_id = self.learning.process_interaction(
                session_id=session_id,
                user_id=user_id,
                user_role=user_role,
                user_message=message,
                assistant_response=response_text,
                intent=intent,
                context={"project_id": project_id, "location": location},
                sources_used=[
                    {"content": r["content"][:200], 
                     "collection": r["collection"],
                     "similarity": r["similarity"]}
                    for r in rag_results[:3]
                ] if rag_results else None,
            )
            
            return {
                "response": response_text,
                "intent": intent,
                "sources": [
                    {
                        "content": r["content"][:200],
                        "collection": r["collection"],
                        "similarity": round(r["similarity"], 2),
                    }
                    for r in rag_results[:3]
                ] if rag_results else [],
                "session_id": session_id,
                "conversation_id": conversation_id,
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}", exc_info=True)
            return {
                "response": (
                    "Ha ocurrido un error procesando tu consulta. "
                    "Inténtalo de nuevo o reformula la pregunta."
                ),
                "intent": "error",
                "sources": [],
                "session_id": session_id,
                "conversation_id": None,
            }
    
    def _build_prompt(
        self,
        user_role: str,
        project_id: str,
        location: str,
        rag_results: list[dict],
        history: list[dict],
    ) -> str:
        """Construye el prompt completo del sistema."""
        
        # Formatear contexto RAG
        if rag_results:
            rag_context = "\n\n".join([
                f"[Fuente: {r['collection']} | "
                f"Relevancia: {r['similarity']:.0%}]\n{r['content']}"
                for r in rag_results[:5]
            ])
        else:
            rag_context = (
                "No se encontró información específica en la base "
                "de conocimiento. Usar conocimiento general."
            )
        
        # Formatear historial
        if history:
            history_text = "\n".join([
                f"{'Usuario' if h['role'] == 'user' else 'Asistente'}: "
                f"{h['content'][:300]}"
                for h in history[-6:]
            ])
        else:
            history_text = "Primera interacción de la sesión."
        
        # Prompt principal
        prompt = SYSTEM_PROMPT.format(
            user_role=user_role,
            current_project=project_id or "No especificado",
            location=location,
            rag_context=rag_context,
            conversation_history=history_text,
        )
        
        # Añadir contexto de rol
        role_context = ROLE_CONTEXTS.get(user_role, "")
        if role_context:
            prompt += "\n\n" + role_context
        
        return prompt
    
    async def _run_tool(
        self,
        intent: str,
        message: str,
        user_role: str,
        rag_results: list[dict],
    ) -> str | None:
        """Ejecuta la tool correspondiente a la intención."""
        tool_name = INTENT_TOOLS.get(intent)
        
        if not tool_name or tool_name not in self.tools:
            return None
        
        try:
            return await self.tools[tool_name].execute(
                query=message,
                user_role=user_role,
                rag_context=rag_results,
            )
        except Exception as e:
            logger.error(f"Error en tool {tool_name}: {e}")
            return None
Genera el archivo completo y funcional.
Asegúrate de que todos los imports existen en los archivos anteriores.
El manejo de errores debe ser robusto - el agente NUNCA debe caer.

text


---

## TAREA 10: API REST (FastAPI)
PROMPT PARA LLM IMPLEMENTADOR:

Archivos a crear:

api/main.py
api/routes/chat.py
api/routes/voice.py
api/routes/knowledge.py
api/routes/admin.py
CONTEXTO:
API REST con FastAPI que expone el agente CarpinteroAI.
Endpoints simples y directos.

--- api/main.py ---
App FastAPI con:

CORS habilitado para todos los orígenes
Rutas montadas
Endpoint /api/health
Montar frontend estático desde ./frontend
Evento startup que:
Verifica Ollama
Verifica ChromaDB
Verifica Supabase
Loga el estado
--- api/routes/chat.py ---
POST /api/chat/
Request body:
{
"message": str (requerido),
"session_id": str (opcional, se genera si no viene),
"user_id": str (default "default"),
"user_role": str (default "general"),
"project_id": str (opcional),
"location": str (default "taller")
}

Response:
{
"response": str,
"session_id": str,
"intent": str,
"sources": list,
"conversation_id": str
}

POST /api/chat/feedback
Request: conversation_id, is_positive, comment (opcional)

--- api/routes/voice.py ---
POST /api/voice/transcribe
Recibe archivo audio (multipart)
Usa Whisper para transcribir
Retorna: {"text": str}

POST /api/voice/chat
Recibe audio + session_id + user_id + user_role
Transcribe + envía al agente
Retorna: transcripción + respuesta del agente

--- api/routes/knowledge.py ---
GET /api/knowledge/pending - Lista conocimiento pendiente de validar
POST /api/knowledge/validate/{id} - Aprobar/rechazar conocimiento
POST /api/knowledge/add - Añadir conocimiento manualmente
GET /api/knowledge/stats - Estadísticas de aprendizaje
POST /api/knowledge/reindex - Re-indexar base de conocimiento

--- api/routes/admin.py ---
GET /api/admin/health - Estado detallado del sistema
GET /api/admin/incidents - Lista de incidencias
GET /api/admin/stats - Estadísticas generales

IMPORTANTE:

Usar Pydantic models para request/response
Manejo de errores con HTTPException
El agente se instancia UNA vez (no por request)
Whisper se carga UNA vez (lazy loading)
Generar todos los archivos completos y funcionales
Import de CarpinteroAgent: from core.agent.main_agent import CarpinteroAgent
text


---

## TAREA 11: Frontend PWA
PROMPT PARA LLM IMPLEMENTADOR:

Archivos a crear:

frontend/index.html
frontend/manifest.json
frontend/sw.js
CONTEXTO:
PWA (Progressive Web App) optimizada para uso en OBRA.
Eso significa:

Pantallas pequeñas (móvil)
Manos sucias/guantes → botones GRANDES
Poco tiempo → interfaz SIMPLE
Posible mala conexión → funcionar offline parcial
Ruido → entrada por voz
DISEÑO:

Dark theme (var --bg: #1a1a2e, --primary: #e67e22)
Fuente grande y legible
Botones mínimo 44px de alto
Sin scroll horizontal
Área de chat ocupa el máximo espacio
Input fijo abajo con botón voz y enviar
COMPONENTES DEL index.html:

HEADER (fijo arriba)

Logo/nombre "🪚 CarpinteroAI"
Selector de rol (dropdown)
Indicador de conexión (verde/rojo)
QUICK ACTIONS (scroll horizontal)

Botones de acciones rápidas predefinidas
Cada botón tiene emoji + texto corto
Al pulsar, envía el mensaje directamente
Ejemplos:
🚪 Premarco → "¿Cómo instalo un premarco correctamente?"
⚠️ Puerta roza → "Tengo un problema con una puerta que roza"
🪵 Dilatación → "¿Qué juntas de dilatación dejo en el parquet?"
📐 Inglete → "¿Cómo corto un inglete de rodapié?"
📏 Medidas → "El hueco no cuadra con las medidas del plano"
📋 Incidencia → "Necesito reportar una incidencia"
🔍 Diagnosticar → "Tengo un problema y necesito ayuda"
CHAT AREA (scroll vertical, flex-grow)

Mensajes del usuario a la derecha (naranja)
Mensajes del asistente a la izquierda (azul oscuro)
Cada mensaje del asistente muestra:
Badge de intención (consulta, diagnóstico, etc.)
Contenido renderizado como markdown (usar marked.js)
Fuentes usadas (si las hay)
Botones de feedback (👍 Útil / 👎 Mejorable)
Indicador de "escribiendo" (3 puntos animados)
INPUT AREA (fijo abajo)

Textarea que crece automáticamente (max 120px)
Botón micrófono 🎤 (se vuelve rojo cuando graba)
Botón enviar ➤
Enter para enviar, Shift+Enter para nueva línea
JAVASCRIPT (todo inline en el HTML para simplicidad):

Estado: sessionId, userId, isRecording, mediaRecorder
Funciones: sendMessage(), addMessage(), toggleVoice(), sendFeedback()
Auto-scroll al último mensaje
Textarea auto-resize
Voice: usar MediaRecorder API → enviar a /api/voice/chat
Markdown: usar marked.js desde CDN
Service Worker para offline básico
CSS (inline en el HTML para simplicidad):

CSS custom properties para theming
Flexbox para layout
Animaciones CSS para fadeIn de mensajes y typing indicator
Media queries no necesarias (diseño mobile-first)
-webkit-overflow-scrolling: touch para iOS
manifest.json:

name: CarpinteroAI
short_name: CarpinteroAI
display: standalone
theme_color: #1a1a2e
background_color: #1a1a2e
orientation: portrait
Icons: mencionar paths aunque no existan aún
sw.js:

Caché de archivos estáticos
Strategy: network-first con fallback a cache
Para API requests: no cachear (solo estáticos)
IMPORTANTE:

TODO en español
El HTML debe ser un archivo COMPLETO y funcional
NO frameworks, NO npm, NO build step
Solo HTML + CSS + JS vanilla + marked.js desde CDN
Debe funcionar abriendo el archivo directamente o desde FastAPI
Los botones deben ser fáciles de pulsar con guantes/manos sucias
Generar los 3 archivos completos
text


---

## TAREA 12: Knowledge Base Inicial (Semilla)
PROMPT PARA LLM IMPLEMENTADOR:

Archivos a crear (contenido técnico REAL de carpintería):

knowledge_base/procedimientos/instalacion_puertas/premarco.md
knowledge_base/procedimientos/instalacion_puertas/marco_y_hoja.md
knowledge_base/procedimientos/instalacion_puertas/problemas_comunes.md
knowledge_base/procedimientos/instalacion_parquet/preparacion_base.md
knowledge_base/procedimientos/instalacion_parquet/colocacion.md
knowledge_base/procedimientos/instalacion_parquet/problemas_comunes.md
knowledge_base/materiales/guia_materiales.md
knowledge_base/problemas_soluciones/puertas.md
knowledge_base/problemas_soluciones/suelos.md
CONTEXTO:
Esta es la base de conocimiento INICIAL del sistema.
Se indexa en ChromaDB al hacer el setup.
Es el conocimiento "día 1" antes de que el sistema aprenda de conversaciones.

REQUISITOS:

Contenido técnico REAL y CORRECTO de carpintería
Medidas en milímetros donde aplique
Tolerancias reales
Problemas que ocurren DE VERDAD en obra
Soluciones prácticas (no teóricas)
Formato markdown con headers (para que el chunker los use)
Cada archivo: 300-600 palabras
Estructura: # Título > ## Secciones > ### Subsecciones
Incluir listas de verificación donde aplique
EJEMPLO de estructura para premarco.md:

Instalación de Premarcos
Verificación previa
Medir hueco: ancho en 3 puntos, alto en 2 puntos
Holgura necesaria: 10-15mm por lado
...
Herramientas necesarias
...
Procedimiento
1. Presentar el premarco
...

2. Nivelar y aplomar
...

⚠️ Problemas frecuentes
Hueco más grande
...

Hueco desplomado
...

✅ Checklist final
 Plomo verificado
 Nivel verificado
...
Genera los 9 archivos con contenido REAL y ÚTIL.
Un carpintero profesional debería poder validar esta información.

text


---

## TAREA 13: Docker y Scripts de Despliegue
PROMPT PARA LLM IMPLEMENTADOR:

Archivos a crear:

docker-compose.yml
infra/docker/Dockerfile.api
requirements.txt
scripts/seed_knowledge.py
Makefile
CONTEXTO:
Despliegue con Docker Compose.
Servicios: Ollama + ChromaDB + API (FastAPI)
Supabase es externo (cloud), no se dockeriza.

--- docker-compose.yml ---
Servicios:

ollama:

imagen: ollama/ollama:latest
puerto: 11434
volumen para modelos
GPU si disponible (con deploy.resources)
chromadb:

imagen: chromadb/chroma:latest
puerto: 8100:8000
volumen persistente
ANONYMIZED_TELEMETRY=FALSE
api:

build desde Dockerfile.api
puerto: 8000
volúmenes: core, api, frontend, knowledge_base, scripts
env: apuntar a ollama y chromadb por nombre de servicio
depends_on: ollama, chromadb
env_file: .env
--- Dockerfile.api ---

Base: python:3.11-slim
Instalar ffmpeg (para Whisper)
pip install requirements.txt
COPY código
CMD uvicorn
--- requirements.txt ---
Todas las dependencias con versiones fijadas:

fastapi, uvicorn, python-multipart
langchain, langchain-community, langchain-core
chromadb
supabase (python client)
openai-whisper
pydantic, pydantic-settings
httpx
python-dotenv
marked (no, esto es JS)
aiofiles
--- scripts/seed_knowledge.py ---
Script que:

Verifica que Ollama está corriendo
Verifica que los modelos están descargados (si no, los descarga)
Verifica que ChromaDB está corriendo
Indexa toda la knowledge_base en ChromaDB
Muestra resumen de chunks indexados
--- Makefile ---
Comandos:

make build : docker-compose build
make up : docker-compose up -d
make down : docker-compose down
make seed : ejecutar seed_knowledge.py
make logs : docker-compose logs -f api
make first-run : build + up + esperar + seed
make status : docker-compose ps
make shell : docker-compose exec api bash
make restart : docker-compose restart api
Genera todos los archivos completos y funcionales.

text


---

## TAREA 14: README Principal
PROMPT PARA LLM IMPLEMENTADOR:

Archivo: README.md

Crear un README completo para el proyecto CarpinteroAI con:

Nombre y descripción (qué es, para quién, qué hace)

Arquitectura (diagrama ASCII)

Requisitos previos:

Docker y Docker Compose
Cuenta gratuita en Supabase
Ollama instalado (o usar Docker)
Mínimo 8GB RAM (para LLM)
GPU recomendada pero no obligatoria
Instalación paso a paso:
a. Clonar repositorio
b. Crear proyecto en Supabase (con screenshots/links)
c. Ejecutar SQL en Supabase SQL Editor
d. Configurar .env
e. make first-run
f. Verificar en http://localhost:8000

Uso:

Acceder a la interfaz web
Seleccionar rol
Tipos de consultas que puede hacer
Uso por voz
Reportar incidencias
Sistema de aprendizaje:

Cómo funciona
Panel de validación (para encargado)
Cómo añadir conocimiento manualmente
API endpoints (tabla con método, URL, descripción)

Personalización:

Cómo añadir más conocimiento base
Cómo cambiar el modelo LLM
Cómo añadir nuevos roles
Stack tecnológico:

Todo open source y gratuito
Tabla con componente → herramienta → licencia
Troubleshooting común

Formato: markdown limpio, sin excesos, directo al punto.
Generar el archivo completo.

text


---

## Orden de Ejecución
EJECUTAR EN ESTE ORDEN EXACTO:

TAREA 0 → Estructura de carpetas y archivos placeholder
TAREA 1 → Config y Supabase client
TAREA 2 → Setup tablas Supabase (SQL)
TAREA 3 → Proveedor LLM (Ollama)
TAREA 4 → Sistema RAG (chunking + embeddings + retriever + indexer)
TAREA 5 → Memoria y aprendizaje (memory + extractor + pipeline)
TAREA 6 → Prompts especializados
TAREA 7 → Router de intenciones
TAREA 8 → Herramientas (tools)
TAREA 9 → Agente principal
TAREA 10 → API REST
TAREA 11 → Frontend PWA
TAREA 12 → Knowledge base inicial
TAREA 13 → Docker y scripts
TAREA 14 → README

Cada tarea depende de las anteriores.
El LLM implementador debe generar archivos COMPLETOS, no fragmentos.

text


---

## Notas para el LLM Implementador
REGLAS GLOBALES:

TODO el código en español (comentarios, logs, variables descriptivas)
Python 3.11+ (usar type hints modernos: list[dict] en vez de List[Dict])
Imports explícitos (no usar *)
Logging en todas las operaciones importantes
Manejo de errores: NUNCA dejar que el sistema caiga por un error
Si falla el RAG → responder sin contexto
Si falla el aprendizaje → responder y loguear
Si falla una tool → responder sin la tool
Supabase client se importa de: core.supabase_client
Configuración se importa de: core.config
LLM se importa de: core.llm.provider
NO usar SQLAlchemy (usamos Supabase client directamente)
NO usar Redis (simplificamos, las colas las maneja FastAPI directo)
NO usar LangGraph (complejidad innecesaria, orquestar manualmente)
SÍ usar LangChain para LLM y text splitting
Cada archivo debe poder ejecutarse sin errores de import
Tests no son obligatorios en la primera iteración
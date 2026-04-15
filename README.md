# MENTOR - Agente Empresarial de Consultas y Guiado

Sistema de IA para resolver consultas de trabajadores sobre politicas, procesos, sistemas y procedimientos corporativos.

> [!TIP]
> **Consulta el [Manual Completo de Usuario (MANUAL_MENTOR.md)](MANUAL_MENTOR.md)** para una guía detallada sobre cómo configurar cuentas, instalar y operar el sistema.

## Caracteristicas

- Clasificacion inteligente de consultas (RRHH, IT, Seguridad, Finanzas, etc.)
- Base de conocimiento con politicas, SOPs y manuales
- 6 estrategias de respuesta adaptativas
- Escalamiento automatico a equipos humanos con tickets
- Deteccion y redaccion de datos sensibles (SSN, RFC, emails)
- Analiticas de uso y satisfaccion
- Cache inteligente de respuestas frecuentes
- Guia especial para empleados nuevos (onboarding)
- Autenticacion JWT + API Keys
- Middleware de logging y rate limiting
- Integraciones: Slack, Microsoft Teams, Webhooks

## Arquitectura

```
Trabaja -> Clasificador -> Router de Area -> KB Search -> Estrategia -> LLM -> Respuesta
                                                              |
                                                    Escalamiento (si necesario)
```

## Inicio Rapido

```bash
# 1. Instalar dependencias
pip install -e ".[dev,test]"

# 2. Configurar entorno
cp .env.example .env
# Editar .env con tus API keys

# 3. Ejecutar
make run
# -> http://localhost:8000/api/v1/docs

# 4. Tests
make test
```

## API Endpoints

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | /api/v1/query | Enviar consulta al agente |
| POST | /api/v1/workers/register | Registrar trabajador |
| POST | /api/v1/feedback | Enviar feedback de satisfaccion |
| GET | /api/v1/analytics | Ver analiticas generales |
| GET | /api/v1/tickets/open | Ver tickets de escalamiento abiertos |
| GET | /api/v1/kb/stats | Estadisticas de la base de conocimiento |
| GET | /api/v1/cache/stats | Estadisticas del cache |
| DELETE | /api/v1/cache | Limpiar cache |
| DELETE | /api/v1/session/{id} | Limpiar sesion de conversacion |
| GET | /health | Health check |
| GET | /metrics | Metricas Prometheus |

## Docker

```bash
# Levantar todos los servicios (API + Redis + Postgres + Prometheus)
make docker-up

# Detener
make docker-down
```

## Estructura del Proyecto

```
Mentor/
 src/
    main.py                    # FastAPI app entry point
    core/
       engine.py              # Motor principal (orquestador)
       query_classifier.py    # Clasificador de consultas
       knowledge_base.py      # Base de conocimiento
       worker_context.py      # Perfil del trabajador
       response_strategies.py # 6 estrategias de respuesta
       escalation.py          # Sistema de escalamiento
       memory.py              # Memoria conversacional
       llm_providers.py       # OpenAI, Anthropic, Ollama
    api/
       routes.py              # Endpoints principales
       schemas.py             # Schemas Pydantic
       auth.py                # JWT + API keys
       middleware.py           # Logging y rate limiting
       metrics_endpoint.py    # Prometheus /metrics
    db/
       database.py            # SQLAlchemy async setup
       models.py              # Modelos de DB
       repositories.py        # CRUD operations
    services/
       cache_service.py       # Cache inteligente Redis/local
       document_ingestion.py  # Ingestion de documentos
       rag_service.py         # RAG con ChromaDB
       metrics.py             # Prometheus metrics
    integrations/
       slack.py               # Notificaciones Slack
       teams.py               # Notificaciones Teams
       webhooks.py            # Webhooks genericos
    utils/
       config.py              # Pydantic settings
       logger.py              # Structured logging
 tests/
    conftest.py               # Fixtures + MockLLM
    test_api.py               # Tests de API
    unit/
       test_query_classifier.py
       test_knowledge_base.py
       test_worker_profile.py
       test_engine.py
       test_escalation.py
       test_cache.py
       test_memory.py
 data/
    knowledge_base.json       # KB inicial
    sample_workers.json       # Trabajadores de ejemplo
 docker/
    Dockerfile
    docker-compose.yml
    prometheus.yml
 .github/workflows/
    ci.yml                    # CI pipeline
    cd.yml                    # CD pipeline
 .env.example
 pyproject.toml
 Makefile
 README.md
```

## Variables de Entorno

Ver `.env.example` para la lista completa. Las principales:

- `LLM_PROVIDER`: openai, anthropic, ollama
- `OPENAI_API_KEY`: Tu clave de API de OpenAI
- `DATABASE_URL`: URI de conexion a base de datos
- `REDIS_URL`: URI de conexion a Redis
- `JWT_SECRET`: Secreto para tokens JWT

## Licencia

Uso interno empresarial.

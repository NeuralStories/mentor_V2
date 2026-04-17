"""
API principal de Mentor by EgeAI.
Servidor FastAPI con todas las rutas del sistema.
"""
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.admin import router as admin_router
from api.routes.chat import router as chat_router
from api.routes.knowledge import router as knowledge_router
from api.routes.voice import router as voice_router
from core.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.INGESTION_DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    from core.ingestion.service import get_store

    get_store()
    logger.info(
        "Mentor AI arrancando | supabase=%s | ocr=%s | debug=%s",
        settings.supabase_enabled,
        settings.OCR_ENABLED,
        settings.APP_DEBUG,
    )
    yield
    logger.info("Mentor AI cerrando")


app = FastAPI(
    title=settings.APP_NAME,
    description="API para asistente de IA avanzado de mentoría técnica y educativa",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])


@app.get("/")
async def root():
    """Endpoint raíz con información básica."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Asistente de IA para trabajadores de carpintería",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Verificación general de salud de la API."""
    return {
        "status": "healthy",
        "service": "api",
        "version": settings.APP_VERSION,
        "supabase": "enabled" if settings.supabase_enabled else "degraded",
        "ocr": "enabled" if settings.OCR_ENABLED else "disabled",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8765,
        reload=True,
        log_level="info",
    )

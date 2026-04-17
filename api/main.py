"""
API principal de Mentor by EgeAI.
Servidor FastAPI con todas las rutas del sistema.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Importar rutas
from api.routes.chat import router as chat_router
from api.routes.voice import router as voice_router
from api.routes.knowledge import router as knowledge_router
from api.routes.admin import router as admin_router

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Mentor by EgeAI API",
    description="API para asistente de IA avanzado de mentoría técnica y educativa",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(
    chat_router,
    prefix="/api/chat",
    tags=["chat"]
)

app.include_router(
    voice_router,
    prefix="/api/voice",
    tags=["voice"]
)

app.include_router(
    knowledge_router,
    prefix="/api/knowledge",
    tags=["knowledge"]
)

app.include_router(
    admin_router,
    prefix="/api/admin",
    tags=["admin"]
)


@app.get("/")
async def root():
    """Endpoint raíz con información básica."""
    return {
        "name": "Mentor by EgeAI API",
        "version": "1.0.0",
        "description": "Asistente de IA para trabajadores de carpintería",
        "docs": "/docs",
        "health": "/api/chat/health"
    }


@app.get("/health")
async def health_check():
    """Verificación general de salud de la API."""
    return {
        "status": "healthy",
        "service": "api",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
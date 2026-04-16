from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from core.config import settings
from core.llm.provider import LLMProvider
from api.routes import chat, voice, knowledge

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para asistente técnico de carpintería"
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
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Conocimiento"])

# Servir Frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

@app.on_event("startup")
async def startup_event():
    """Verificaciones iniciales."""
    logger.info("Iniciando CarpinteroAI V2...")
    
    # Verificar Ollama
    if not LLMProvider.check_ollama():
        logger.error("Ollama no responde. Verifica que esté corriendo en " + settings.OLLAMA_BASE_URL)
    else:
        logger.info("Conexión con Ollama: OK")

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

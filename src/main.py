"""Punto de entrada de la aplicación MENTOR."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.api.metrics_endpoint import router as metrics_router
from src.api.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación: inicio y apagado."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Database: {settings.database_url}")
    yield
    logger.info("Shutting down MENTOR...")


app = FastAPI(
    title=settings.app_name,
    description="Agente empresarial de consultas y guiado para trabajadores",
    version=settings.app_version,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    lifespan=lifespan,
)

# Middleware (orden inverso de ejecución: el último añadido se ejecuta primero)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)

# Routers
app.include_router(router, prefix=settings.api_prefix)
app.include_router(metrics_router)


@app.get("/health")
async def health_check():
    """Health check para load balancers y monitoreo."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }

"""
Rutas administrativas para Mentor by EgeAI.
Endpoints para gestión del sistema, validación de conocimiento, estadísticas.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from core.memory.learning_pipeline import LearningPipeline
from core.llm.provider import LLMProvider
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Instancias de servicios
learning = LearningPipeline()
llm_provider = LLMProvider()


class ValidationRequest(BaseModel):
    """Modelo para solicitud de validación."""
    knowledge_id: str
    approved: bool
    validated_by: str = "admin"
    comments: Optional[str] = None


class ValidationResponse(BaseModel):
    """Modelo para respuesta de validación."""
    knowledge_id: str
    status: str
    action: str
    message: str


@router.get("/pending-validations")
async def get_pending_validations(limit: int = 50):
    """
    Obtiene conocimiento pendiente de validación por el administrador.
    """
    try:
        pending = learning.get_pending_validations()

        return {
            "pending_validations": pending[:limit],
            "total_pending": len(pending),
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Error obteniendo validaciones pendientes: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener validaciones pendientes"
        )


@router.post("/validate-knowledge", response_model=ValidationResponse)
async def validate_knowledge(request: ValidationRequest):
    """
    Aprueba o rechaza conocimiento aprendido.
    Solo para administradores.
    """
    try:
        learning.validate_knowledge(
            knowledge_id=request.knowledge_id,
            approved=request.approved,
            validated_by=request.validated_by
        )

        action = "aprobado" if request.approved else "rechazado"
        message = f"Conocimiento {request.knowledge_id} {action}"

        if request.approved:
            message += " e indexado en la base de conocimientos"
        else:
            message += " y descartado"

        logger.info(f"Validación: {message}")

        return ValidationResponse(
            knowledge_id=request.knowledge_id,
            status="success",
            action=action,
            message=message
        )

    except Exception as e:
        logger.error(f"Error en validación: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al validar el conocimiento"
        )


@router.get("/learning-stats")
async def get_learning_stats():
    """
    Obtiene estadísticas detalladas del sistema de aprendizaje.
    """
    try:
        stats = learning.get_learning_stats()

        # Añadir estadísticas adicionales
        stats["efectividad_aprendizaje"] = (
            stats.get("approved", 0) / max(stats.get("total", 1), 1) * 100
        )

        return {
            "learning_stats": stats,
            "status": "active"
        }

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener estadísticas de aprendizaje"
        )


@router.get("/system-health")
async def get_system_health():
    """
    Verificación completa de salud del sistema.
    """
    try:
        health_status = {
            "overall_status": "healthy",
            "components": {}
        }

        # Verificar LLM
        try:
            llm_health = llm_provider.check_ollama_health()
            health_status["components"]["llm"] = {
                "status": "healthy" if llm_health["ollama_running"] else "unhealthy",
                "details": llm_health
            }
        except Exception as e:
            health_status["components"]["llm"] = {
                "status": "error",
                "error": str(e)
            }

        # Verificar aprendizaje
        try:
            learning_stats = learning.get_learning_stats()
            health_status["components"]["learning"] = {
                "status": "healthy",
                "stats": learning_stats
            }
        except Exception as e:
            health_status["components"]["learning"] = {
                "status": "error",
                "error": str(e)
            }

        # Verificar base de datos
        try:
            # Simple query de prueba
            test_result = learning.client.table("conversations").select("id").limit(1).execute()
            health_status["components"]["database"] = {
                "status": "healthy",
                "test_query": "success"
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "error",
                "error": str(e)
            }

        # Determinar estado general
        component_statuses = [comp["status"] for comp in health_status["components"].values()]
        if "error" in component_statuses:
            health_status["overall_status"] = "degraded"
        elif "unhealthy" in component_statuses:
            health_status["overall_status"] = "warning"

        return health_status

    except Exception as e:
        logger.error(f"Error en system health: {e}")
        return {
            "overall_status": "error",
            "error": str(e),
            "components": {}
        }


@router.post("/force-learn")
async def force_learning_trigger(
    conversation_text: str,
    user_role: str = "general"
):
    """
    Fuerza el proceso de aprendizaje con un texto específico.
    Útil para testing o aprendizaje manual.
    """
    try:
        # Simular una conversación para extraer conocimiento
        extracted = learning.extractor.extract(
            user_message=conversation_text,
            assistant_response="Entendido, gracias por la información.",
            user_role=user_role
        )

        if extracted:
            for item in extracted:
                knowledge_id = learning._store_knowledge(item, "manual_learning")
                learning._index_knowledge_item(item)

            return {
                "status": "learning_triggered",
                "extracted_items": len(extracted),
                "message": f"Extraído y aprendido {len(extracted)} item(s) de conocimiento"
            }
        else:
            return {
                "status": "no_learning",
                "message": "No se encontró conocimiento útil para aprender"
            }

    except Exception as e:
        logger.error(f"Error en aprendizaje forzado: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al procesar el aprendizaje forzado"
        )


@router.delete("/clear-session/{session_id}")
async def clear_session(session_id: str):
    """
    Limpia datos de una sesión específica (para testing).
    """
    try:
        # Nota: Implementación simplificada
        # En producción, requeriría lógica más compleja
        logger.warning(f"Limpieza de sesión solicitada: {session_id}")

        return {
            "status": "session_clear_requested",
            "session_id": session_id,
            "message": "Limpieza de sesión solicitada (implementación pendiente)"
        }

    except Exception as e:
        logger.error(f"Error limpiando sesión: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al limpiar la sesión"
        )


@router.get("/config")
async def get_system_config():
    """
    Obtiene configuración actual del sistema (sin datos sensibles).
    """
    try:
        from core.config import settings

        # Solo configuración no sensible
        safe_config = {
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "debug": settings.APP_DEBUG,
            "ollama_base_url": settings.OLLAMA_BASE_URL,
            "llm_model": settings.LLM_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
            "chroma_host": settings.CHROMA_HOST,
            "chroma_port": settings.CHROMA_PORT,
            "rag_top_k": settings.RAG_TOP_K,
            "rag_chunk_size": settings.RAG_CHUNK_SIZE,
            "auto_learn": settings.AUTO_LEARN,
            "require_validation": settings.REQUIRE_VALIDATION,
        }

        return {
            "config": safe_config,
            "status": "config_retrieved"
        }

    except Exception as e:
        logger.error(f"Error obteniendo configuración: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener la configuración"
        )

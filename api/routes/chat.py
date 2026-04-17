"""
Rutas de chat para Mentor by EgeAI.
Endpoint principal para conversaciones con el agente.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.agent.main_agent import MainAgent
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Instancia global del agente (podría ser singleton o injectado)
agent = MainAgent()


class ChatRequest(BaseModel):
    """Modelo para solicitud de chat."""
    message: str
    user_id: Optional[str] = "anonymous"
    user_role: Optional[str] = "general"
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Modelo para respuesta de chat."""
    response: str
    intent: str
    sources_used: list
    conversation_id: Optional[str]
    processing_time: Optional[float] = None


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Endpoint principal para enviar mensajes al agente.

    - Procesa el mensaje usando el MainAgent
    - Retorna respuesta estructurada
    - Registra conversación en background
    """
    try:
        logger.info(f"Mensaje recibido de user {request.user_id}: {request.message[:50]}...")

        # Procesar mensaje con el agente
        result = await agent.process_message(
            message=request.message,
            user_id=request.user_id,
            user_role=request.user_role,
            session_id=request.session_id,
            context=request.context,
        )

        # Preparar respuesta
        response = ChatResponse(
            response=result["response"],
            intent=result["intent"],
            sources_used=result["sources_used"],
            conversation_id=result["conversation_id"],
        )

        logger.info(f"Respuesta enviada para intent: {result['intent']}")

        return response

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al procesar el mensaje"
        )


@router.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servicio de chat."""
    return {
        "status": "healthy",
        "service": "chat",
        "agent_status": "active" if agent else "inactive"
    }


@router.post("/feedback")
async def send_feedback(
    conversation_id: str,
    is_positive: bool,
    comment: Optional[str] = None,
    user_id: Optional[str] = "anonymous"
):
    """
    Endpoint para enviar feedback sobre una respuesta.
    """
    try:
        # Usar el pipeline de aprendizaje para guardar feedback
        agent.learning.memory.save_feedback(
            conversation_id=conversation_id,
            is_positive=is_positive,
            comment=comment,
        )

        logger.info(f"Feedback recibido: {conversation_id} - {'positivo' if is_positive else 'negativo'}")

        return {
            "status": "feedback_saved",
            "conversation_id": conversation_id,
            "message": "Gracias por tu feedback. Nos ayuda a mejorar."
        }

    except Exception as e:
        logger.error(f"Error guardando feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al guardar el feedback"
        )


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 10):
    """
    Obtiene el historial de una sesión de conversación.
    """
    try:
        history = agent.learning.memory.get_session_history(session_id, limit=limit)

        return {
            "session_id": session_id,
            "history": history,
            "count": len(history)
        }

    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener el historial de conversación"
        )
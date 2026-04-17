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
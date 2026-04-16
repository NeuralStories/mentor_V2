from typing import List, Dict, Optional
from core.supabase_client import get_supabase
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Gestiona la persistencia de las conversaciones en Supabase."""
    
    def __init__(self):
        self.supabase = get_supabase()
        
    def save_interaction(
        self,
        session_id: str,
        user_id: str,
        user_role: str,
        user_message: str,
        assistant_response: str,
        intent: str = "general",
        context: Dict = None,
        sources_used: List[Dict] = None
    ) -> str:
        """Guarda la interacción en la tabla conversations."""
        data = {
            "session_id": session_id,
            "user_id": user_id,
            "user_role": user_role,
            "user_message": user_message,
            "assistant_response": assistant_response,
            "intent": intent,
            "context": context or {},
            "sources_used": sources_used or []
        }
        
        try:
            res = self.supabase.table("conversations").insert(data).execute()
            if res.data:
                return res.data[0]["id"]
            return None
        except Exception as e:
            logger.error(f"Error guardando conversación: {e}")
            return None
            
    def get_session_history(self, session_id: str, limit: int = 6) -> List[Dict]:
        """Recupera los últimos mensajes de una sesión."""
        try:
            res = self.supabase.table("conversations")\
                .select("user_message, assistant_response")\
                .eq("session_id", session_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
                
            history = []
            # Invertimos para que queden en orden cronológico
            for row in reversed(res.data):
                history.append({"role": "user", "content": row["user_message"]})
                history.append({"role": "assistant", "content": row["assistant_response"]})
            return history
        except Exception as e:
            logger.error(f"Error recuperando historial: {e}")
            return []

    def log_incident(self, data: Dict) -> str:
        """Guarda un reporte de incidencia registrado en la obra o taller."""
        try:
            res = self.supabase.table("incidents").insert(data).execute()
            return res.data[0]["id"] if res.data else None
        except Exception as e:
            logger.error(f"Error reportando incidencia: {e}")
            return None

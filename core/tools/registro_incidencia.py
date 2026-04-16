from typing import List, Dict
from core.memory.conversation_memory import ConversationMemory
import json

class RegistroIncidenciaTool:
    def __init__(self, retriever=None, llm=None):
        self.memory = ConversationMemory()

    async def execute(self, query: str, user_role: str, rag_context: List[Dict] = None) -> str:
        # En una versión real, usaríamos un LLM para extraer estos campos
        # Por ahora, simulamos el registro con los datos del mensaje
        incidencia_data = {
            "reported_by": user_role,
            "category": "tecnica",
            "description": query,
            "status": "abierta",
            "severity": "media"
        }
        
        try:
            incidid = self.memory.log_incident(incidencia_data)
            return (
                f"SISTEMA: Incidencia registrada con ID {incidid}. "
                "Informar al usuario de que se ha notificado al encargado."
            )
        except:
            return "Error al registrar la incidencia en base de datos."

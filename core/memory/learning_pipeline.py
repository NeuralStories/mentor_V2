from typing import Dict, List, Optional
from core.memory.conversation_memory import ConversationMemory
from core.memory.knowledge_extractor import KnowledgeExtractor
from core.supabase_client import get_supabase_admin
from core.config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

class LearningPipeline:
    """
    Orquesta el aprendizaje continuo:
    1. Guarda interacción
    2. Extrae conocimiento
    3. Registra para validación (si es necesario)
    """
    
    def __init__(self):
        self.memory = ConversationMemory()
        self.extractor = KnowledgeExtractor()
        self.supabase = get_supabase_admin()
        
    async def process_interaction(
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
        """Pipeline principal post-respuesta."""
        # 1. Persistir conversación
        conv_id = self.memory.save_interaction(
            session_id, user_id, user_role, user_message, 
            assistant_response, intent, context, sources_used
        )
        
        # 2. Intentar aprendizaje asíncrono si está activado
        if settings.AUTO_LEARN:
            asyncio.create_task(
                self._learn_step(user_message, assistant_response, conv_id)
            )
            
        return conv_id

    async def _learn_step(self, user_msg: str, assistant_resp: str, conv_id: str):
        """Extrae y guarda conocimiento pendiente de validar."""
        knowledge = await self.extractor.extract(user_msg, assistant_resp)
        
        if knowledge:
            logger.info(f"¡Nuevo conocimiento detectado!: {knowledge['title']}")
            
            # Preparar para Supabase
            status = 'pending' if settings.REQUIRE_VALIDATION else 'approved'
            
            data = {
                "title": knowledge["title"],
                "content": knowledge["content"],
                "category": knowledge["category"],
                "subcategory": knowledge.get("subcategory", "general"),
                "source_conversation_id": conv_id,
                "confidence": knowledge.get("confidence", 0.7),
                "validation_status": status,
                "tags": knowledge.get("tags", [])
            }
            
            try:
                self.supabase.table("learned_knowledge").insert(data).execute()
                # Si es aprobado directo, podrías indexar en RAG aquí tmb
            except Exception as e:
                logger.error(f"Error al registrar conocimiento aprendido: {e}")

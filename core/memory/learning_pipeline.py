"""
Pipeline de aprendizaje continuo.
Orquesta el flujo completo:
  conversación → extracción → almacenamiento → validación → indexación

Este es el cerebro del aprendizaje del sistema.
"""
from typing import Optional
from core.memory.conversation_memory import ConversationMemory
from core.memory.knowledge_extractor import KnowledgeExtractor
from core.rag.indexer import KnowledgeIndexer
from core.supabase_client import get_supabase
from core.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)


class LearningPipeline:
    """Pipeline completo de aprendizaje."""
    
    def __init__(self):
        self.memory = ConversationMemory()
        self.extractor = KnowledgeExtractor()
        self.indexer = KnowledgeIndexer()
        self.client = get_supabase()
    
    def process_interaction(
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
        Procesa una interacción completa:
        1. Guarda la conversación
        2. Intenta extraer conocimiento
        3. Si hay conocimiento → lo guarda y opcionalmente lo indexa
        
        Retorna el ID de la conversación.
        """
        
        # 1. Guardar conversación
        conversation_id = self.memory.save_interaction(
            session_id=session_id,
            user_id=user_id,
            user_role=user_role,
            user_message=user_message,
            assistant_response=assistant_response,
            intent=intent,
            context=context,
            sources_used=sources_used,
        )
        
        # 2. Extraer conocimiento (si está habilitado)
        if settings.AUTO_LEARN:
            self._try_extract_knowledge(
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_response=assistant_response,
                user_role=user_role,
            )
        
        return conversation_id
    
    def _try_extract_knowledge(
        self,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        user_role: str,
    ):
        """Intenta extraer y almacenar conocimiento."""
        try:
            items = self.extractor.extract(
                user_message=user_message,
                assistant_response=assistant_response,
                user_role=user_role,
            )
            
            if not items:
                return
            
            for item in items:
                knowledge_id = self._store_knowledge(item, conversation_id)
                
                # Si no requiere validación, indexar directamente
                if not settings.REQUIRE_VALIDATION:
                    self._index_knowledge_item(item)
                    logger.info(
                        f"Conocimiento indexado directamente: "
                        f"{item.get('title', 'sin título')}"
                    )
                else:
                    logger.info(
                        f"Conocimiento pendiente de validación: "
                        f"{item.get('title', 'sin título')}"
                    )
                    
        except Exception as e:
            logger.error(f"Error en extracción de conocimiento: {e}")
    
    def _store_knowledge(self, item: dict, conversation_id: str) -> str:
        """Guarda un item de conocimiento en Supabase."""
        knowledge_id = str(uuid.uuid4())
        
        try:
            self.client.table("learned_knowledge").insert({
                "id": knowledge_id,
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "category": item.get("category", "general"),
                "subcategory": item.get("type", "general"),
                "source_conversation_id": conversation_id,
                "confidence": item.get("confidence", 0.5),
                "validation_status": "pending" if settings.REQUIRE_VALIDATION 
                                     else "approved",
                "tags": item.get("tags", []),
            }).execute()
            
            return knowledge_id
        except Exception as e:
            logger.error(f"Error almacenando conocimiento: {e}")
            return knowledge_id
    
    def _index_knowledge_item(self, item: dict):
        """Indexa un item de conocimiento en ChromaDB."""
        content = f"{item.get('title', '')}\n\n{item.get('content', '')}"
        
        self.indexer.index_learned_knowledge(
            content=content,
            metadata={
                "type": item.get("type", "general"),
                "category": item.get("category", "general"),
                "tags": item.get("tags", []),
                "source": "learned",
            },
        )
    
    # === MÉTODOS PARA VALIDACIÓN (usados por el encargado) ===
    
    def get_pending_validations(self) -> list[dict]:
        """Obtiene conocimiento pendiente de validar."""
        try:
            result = (
                self.client.table("learned_knowledge")
                .select("*")
                .eq("validation_status", "pending")
                .order("created_at", desc=True)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error obteniendo pendientes: {e}")
            return []
    
    def validate_knowledge(
        self, 
        knowledge_id: str, 
        approved: bool, 
        validated_by: str = "admin"
    ):
        """
        Aprueba o rechaza conocimiento.
        Si se aprueba, lo indexa en ChromaDB.
        """
        status = "approved" if approved else "rejected"
        
        try:
            # Actualizar estado
            self.client.table("learned_knowledge").update({
                "validation_status": status,
                "validated_by": validated_by,
                "validated_at": "now()",
            }).eq("id", knowledge_id).execute()
            
            # Si aprobado, indexar
            if approved:
                # Obtener el registro
                result = (
                    self.client.table("learned_knowledge")
                    .select("*")
                    .eq("id", knowledge_id)
                    .single()
                    .execute()
                )
                
                if result.data:
                    self._index_knowledge_item({
                        "title": result.data["title"],
                        "content": result.data["content"],
                        "type": result.data["subcategory"],
                        "category": result.data["category"],
                        "tags": result.data.get("tags", []),
                    })
                    logger.info(f"Conocimiento {knowledge_id} aprobado e indexado")
            else:
                logger.info(f"Conocimiento {knowledge_id} rechazado")
                
        except Exception as e:
            logger.error(f"Error validando conocimiento: {e}")
    
    def get_learning_stats(self) -> dict:
        """Estadísticas del sistema de aprendizaje."""
        try:
            total = self.client.table("learned_knowledge")\
                .select("id", count="exact").execute()
            approved = self.client.table("learned_knowledge")\
                .select("id", count="exact")\
                .eq("validation_status", "approved").execute()
            pending = self.client.table("learned_knowledge")\
                .select("id", count="exact")\
                .eq("validation_status", "pending").execute()
            rejected = self.client.table("learned_knowledge")\
                .select("id", count="exact")\
                .eq("validation_status", "rejected").execute()
            
            return {
                "total": total.count,
                "approved": approved.count,
                "pending": pending.count,
                "rejected": rejected.count,
            }
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {"total": 0, "approved": 0, "pending": 0, "rejected": 0}
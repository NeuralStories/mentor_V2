import uuid
import logging
from typing import Optional, List, Dict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from core.llm.provider import LLMProvider
from core.rag.retriever import RAGRetriever
from core.memory.learning_pipeline import LearningPipeline
from core.agent.router import IntentRouter
from core.agent.prompts.system_prompt import SYSTEM_PROMPT
from core.agent.prompts.instalador_puertas import PUERTAS_CONTEXT
from core.agent.prompts.instalador_parquet import PARQUET_CONTEXT
from core.tools.consulta_tecnica import ConsultaTecnicaTool
from core.tools.diagnostico import DiagnosticoTool
from core.tools.guia_instalacion import GuiaInstalacionTool
from core.tools.verificacion import VerificacionTool
from core.tools.registro_incidencia import RegistroIncidenciaTool
from core.config import settings

logger = logging.getLogger(__name__)

# Mapeo de roles a contextos adicionales
ROLE_CONTEXTS = {
    "instalador_puertas": PUERTAS_CONTEXT,
    "instalador_parquet": PARQUET_CONTEXT,
    "carpintero_taller": "CONSEJO: Priorizar seguridad de máquinas y orden en el despiece.",
    "encargado": "NOTA: El encargado tiene visión global de la obra y presupuestos.",
    "general": "",
}

# Mapeo de intenciones a colecciones RAG prioritarias
INTENT_COLLECTIONS = {
    "consulta_tecnica": ["procedimientos", "materiales", "aprendido"],
    "diagnostico": ["problemas_soluciones", "incidencias", "aprendido"],
    "guia_instalacion": ["procedimientos", "aprendido"],
    "verificacion": ["procedimientos", "problemas_soluciones"],
    "incidencia": ["incidencias", "problemas_soluciones"],
    "general": None,
}

# Mapeo de intenciones a tools
INTENT_TOOLS = {
    "consulta_tecnica": "consulta",
    "diagnostico": "diagnostico",
    "guia_instalacion": "guia",
    "verificacion": "verificacion",
    "incidencia": "incidencia",
}

class CarpinteroAgent:
    """Agente principal de CarpinteroAI."""
    
    def __init__(self):
        self.chat_llm = LLMProvider.get_chat_llm()
        self.retriever = RAGRetriever()
        self.learning = LearningPipeline()
        self.router = IntentRouter()
        
        # Inicializar tools
        shared_llm = LLMProvider.get_fast_llm()
        self.tools = {
            "consulta": ConsultaTecnicaTool(self.retriever, shared_llm),
            "diagnostico": DiagnosticoTool(self.retriever, shared_llm),
            "guia": GuiaInstalacionTool(self.retriever, shared_llm),
            "verificacion": VerificacionTool(self.retriever, shared_llm),
            "incidencia": RegistroIncidenciaTool(),
        }
    
    async def process_message(
        self,
        message: str,
        session_id: str = None,
        user_id: str = "default",
        user_role: str = "general",
        project_id: str = None,
        location: str = "obra",
    ) -> dict:
        """Procesa un mensaje y coordina la respuesta."""
        session_id = session_id or str(uuid.uuid4())
        
        try:
            # 1. Clasificar intención
            intent = await self.router.classify(message)
            logger.info(f"Intent detectado: {intent} | Rol: {user_role}")
            
            # 2. RAG - Búsqueda de contexto
            collections = INTENT_COLLECTIONS.get(intent)
            rag_results = self.retriever.search(
                query=message,
                collections=collections,
                top_k=settings.RAG_TOP_K
            )
            
            # 3. Herramienta (Tool)
            tool_output = await self._run_tool(intent, message, user_role, rag_results)
            
            # 4. Historial
            history = self.learning.memory.get_session_history(session_id, limit=6)
            
            # 5. Construir prompt del sistema completo
            system_prompt = self._build_prompt(
                user_role=user_role,
                project_id=project_id,
                location=location,
                rag_results=rag_results,
                history=history
            )
            
            # 6. Preparar mensajes
            messages = [SystemMessage(content=system_prompt)]
            for h in history:
                if h["role"] == "user":
                    messages.append(HumanMessage(content=h["content"]))
                else:
                    messages.append(AIMessage(content=h["content"]))
            
            # Añadir mensaje actual + output de tool
            user_input = message
            if tool_output:
                user_input += f"\n\n[INFO SISTEMA - NO MOSTRAR]:\n{tool_output}"
            messages.append(HumanMessage(content=user_input))
            
            # 7. Generar respuesta
            response = self.chat_llm.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # 8. Post-procesamiento (Guardado y Aprendizaje)
            conv_id = await self.learning.process_interaction(
                session_id=session_id,
                user_id=user_id,
                user_role=user_role,
                user_message=message,
                assistant_response=response_text,
                intent=intent,
                context={"project_id": project_id, "location": location},
                sources_used=[{
                    "content": r["content"][:200], 
                    "coll": r["collection"], 
                    "sim": round(r["similarity"], 2)
                } for r in rag_results[:3]]
            )
            
            return {
                "response": response_text,
                "intent": intent,
                "sources": [
                    {"content": r["content"][:200], "collection": r["collection"], "similarity": r["similarity"]}
                    for r in rag_results[:3]
                ],
                "session_id": session_id,
                "conversation_id": conv_id
            }
            
        except Exception as e:
            logger.error(f"Error crítico en agente: {e}", exc_info=True)
            return {
                "response": "Lo siento, ha ocurrido un error técnico interno. Por favor, intenta reformular tu pregunta.",
                "intent": "error",
                "sources": [],
                "session_id": session_id
            }

    def _build_prompt(self, user_role, project_id, location, rag_results, history) -> str:
        """Ensambla el prompt del sistema dinámico."""
        # Formatear contexto RAG
        rag_text = "\n\n".join([
            f"[Manual: {r['collection']}]\n{r['content']}" 
            for r in rag_results[:4]
        ]) if rag_results else "No hay información específica en manuales."
        
        # Formatear historial
        hist_text = "\n".join([
            f"{'Op' if h['role'] == 'user' else 'AI'}: {h['content'][:150]}" 
            for h in history
        ]) if history else "Inicio de conversación."
        
        prompt = SYSTEM_PROMPT.format(
            user_role=user_role,
            location=location,
            current_project=project_id or "Sin asignar",
            rag_context=rag_text,
            conversation_history=hist_text
        )
        
        # Añadir prompt específico de rol
        prompt += "\n" + ROLE_CONTEXTS.get(user_role, "")
        return prompt

    async def _run_tool(self, intent, query, user_role, rag_results) -> Optional[str]:
        """Ejecuta la herramienta si la intención lo requiere."""
        tool_key = INTENT_TOOLS.get(intent)
        if not tool_key or tool_key not in self.tools:
            return None
            
        try:
            return await self.tools[tool_key].execute(query, user_role, rag_results)
        except Exception as e:
            logger.error(f"Error ejecutando tool {tool_key}: {e}")
            return None

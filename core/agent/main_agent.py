"""
Agente principal de Mentor by EgeAI.
Orquesta todos los componentes: router, RAG, LLM, aprendizaje.
"""
from typing import Dict, Any, Optional
from core.agent.router import IntentRouter
from core.rag.retriever import RAGRetriever
from core.llm.provider import LLMProvider
from core.memory.learning_pipeline import LearningPipeline
from core.agent.prompts.system_prompt import SYSTEM_PROMPT
from core.agent.prompts.instalador_puertas import INSTALADOR_PUERTAS_PROMPT
from core.agent.prompts.instalador_parquet import INSTALADOR_PARQUET_PROMPT
from core.agent.prompts.diagnostico import DIAGNOSTICO_PROMPT
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class MainAgent:
    """
    Agente principal que coordina todas las funcionalidades.
    Procesa mensajes de usuarios y genera respuestas contextuales.
    """

    def __init__(self):
        self.router = IntentRouter()
        self.rag = RAGRetriever()
        self.llm = LLMProvider.get_chat_llm()
        self.learning = LearningPipeline()

    async def process_message(
        self,
        message: str,
        user_id: str = "anonymous",
        user_role: str = "general",
        session_id: str = None,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje completo del usuario.

        Retorna dict con:
        - response: respuesta del agente
        - intent: intención detectada
        - sources_used: fuentes consultadas
        - conversation_id: ID de la conversación
        """
        try:
            # 1. Clasificar intención
            intent = await self.router.classify(message)
            logger.info(f"Intención detectada: {intent} para usuario {user_id}")

            # 2. Obtener contexto relevante
            rag_context = self._get_rag_context(message, intent)

            # 3. Preparar prompt
            prompt = self._build_prompt(
                user_role=user_role,
                current_project=context.get("project", "general") if context else "general",
                location=context.get("location", "taller") if context else "taller",
                rag_context=rag_context,
                conversation_history=self._get_history(session_id) if session_id else [],
            )

            # 4. Generar respuesta
            response = await self._generate_response(prompt, message)

            # 5. Procesar aprendizaje
            conversation_id = self.learning.process_interaction(
                session_id=session_id or f"session_{user_id}",
                user_id=user_id,
                user_role=user_role,
                user_message=message,
                assistant_response=response,
                intent=intent,
                context=context,
                sources_used=self._extract_sources_used(rag_context),
            )

            return {
                "response": response,
                "intent": intent,
                "sources_used": self._extract_sources_used(rag_context),
                "conversation_id": conversation_id,
            }

        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            return {
                "response": "Lo siento, ha ocurrido un error interno. Por favor, inténtalo de nuevo.",
                "intent": "general",
                "sources_used": [],
                "conversation_id": None,
            }

    def _get_rag_context(self, message: str, intent: str) -> str:
        """Obtiene contexto relevante del RAG basado en intención."""
        try:
            # Determinar colecciones según intención
            collections = self._get_collections_for_intent(intent)

            # Buscar información relevante
            results = self.rag.search(
                query=message,
                collections=collections,
                top_k=3,
            )

            if not results:
                return "No se encontró información específica en la base de conocimientos."

            # Formatear contexto
            context_parts = []
            for result in results:
                source = f"[{result['collection'].title()}]"
                content = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                context_parts.append(f"{source}: {content}")

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error obteniendo contexto RAG: {e}")
            return "Error consultando base de conocimientos."

    def _get_collections_for_intent(self, intent: str) -> list:
        """Determina qué colecciones consultar según la intención."""
        mappings = {
            "consulta_tecnica": ["procedimientos", "materiales"],
            "diagnostico": ["problemas_soluciones", "incidencias", "aprendido"],
            "guia_instalacion": ["procedimientos", "aprendido"],
            "verificacion": ["procedimientos", "aprendido"],
            "incidencia": ["incidencias", "problemas_soluciones"],
            "general": ["procedimientos", "aprendido"],
        }
        return mappings.get(intent, ["procedimientos"])

    def _build_prompt(
        self,
        user_role: str,
        current_project: str,
        location: str,
        rag_context: str,
        conversation_history: list,
    ) -> str:
        """Construye el prompt completo para el LLM."""
        # Prompt base
        prompt = SYSTEM_PROMPT

        # Añadir contexto específico del rol
        if user_role == "instalador_puertas":
            prompt += "\n\n" + INSTALADOR_PUERTAS_PROMPT
        elif user_role == "instalador_parquet":
            prompt += "\n\n" + INSTALADOR_PARQUET_PROMPT

        # Formatear con variables
        prompt = prompt.format(
            user_role=user_role,
            current_project=current_project,
            location=location,
            rag_context=rag_context,
            conversation_history=self._format_history(conversation_history),
        )

        return prompt

    def _format_history(self, history: list) -> str:
        """Formatea el historial de conversación."""
        if not history:
            return "Sin historial previo."

        formatted = []
        for msg in history[-5:]:  # Últimos 5 mensajes
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            formatted.append(f"{role}: {msg['content']}")

        return "\n".join(formatted)

    def _get_history(self, session_id: str) -> list:
        """Obtiene historial de conversación."""
        try:
            return self.learning.memory.get_session_history(session_id, limit=10)
        except Exception:
            return []

    async def _generate_response(self, prompt: str, user_message: str) -> str:
        """Genera respuesta usando el LLM."""
        try:
            full_prompt = f"{prompt}\n\nUsuario: {user_message}\n\nAsistente:"
            response = await self.llm.ainvoke(full_prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return "Lo siento, no pude generar una respuesta en este momento."

    def _extract_sources_used(self, rag_context: str) -> list:
        """Extrae IDs de fuentes usadas del contexto."""
        # Por ahora, retornar vacío. Se puede mejorar para trackear fuentes específicas
        return []
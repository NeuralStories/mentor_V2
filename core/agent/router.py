from typing import Optional
from core.llm.provider import LLMProvider
import logging

logger = logging.getLogger(__name__)

ROUTER_PROMPT = """
SISTEMA: Clasifica la intención de la siguiente consulta de un operario de carpintería.
INTENCIONES POSIBLES:
- 'consulta_tecnica': Preguntas sobre medidas, materiales, qué usar, etc.
- 'diagnostico': El usuario describe un problema y quiere saber la causa y solución.
- 'guia_instalacion': Pide pasos para montar algo.
- 'verificacion': Pregunta si algo que ha hecho o planea hacer es correcto.
- 'incidencia': Quiere reportar algo que ha salido mal, una rotura o falta de material.
- 'general': Saludos, agradecimientos o temas no técnicos.

CONSULTA: "{query}"

RESPUESTA (solo la palabra de la intención):"""

class IntentRouter:
    """Clasifica la intención del usuario para optimizar la estrategia de respuesta."""
    
    def __init__(self):
        self.llm = LLMProvider.get_fast_llm()
        
    async def classify(self, query: str) -> str:
        """Determina la intención de la consulta."""
        try:
            prompt = ROUTER_PROMPT.format(query=query)
            response = self.llm.invoke(prompt)
            intent = response.content if hasattr(response, 'content') else str(response)
            intent = intent.strip().lower()
            
            valid_intents = [
                'consulta_tecnica', 'diagnostico', 'guia_instalacion', 
                'verificacion', 'incidencia', 'general'
            ]
            
            for valid in valid_intents:
                if valid in intent:
                    return valid
            
            return "general"
        except Exception as e:
            logger.error(f"Error en router: {e}")
            return "general"

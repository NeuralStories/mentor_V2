"""
Extrae conocimiento útil de las conversaciones usando el LLM.
Analiza cada interacción y determina si contiene información
valiosa que debería ser aprendida por el sistema.
"""
from typing import Optional
from core.llm.provider import LLMProvider
from core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Eres un experto en carpintería, instalación de puertas,
parquet y rodapiés.

Analiza esta conversación entre un trabajador y el asistente.
Determina si contiene CONOCIMIENTO TÉCNICO NUEVO Y ÚTIL que podría
ayudar a otros trabajadores en el futuro.

== CONVERSACIÓN ==
Trabajador ({user_role}): {user_message}
Asistente: {assistant_response}
===============

Responde ÚNICAMENTE con JSON válido:

Si NO hay conocimiento útil:
{{"has_knowledge": false}}

Si SÍ hay conocimiento útil:
{{
    "has_knowledge": true,
    "items": [
        {{
            "type": "procedimiento|problema_solucion|consejo|medida|material",
            "category": "puertas|parquet|rodapies|taller|general",
            "title": "Título breve y descriptivo",
            "content": "Descripción completa del conocimiento. Incluir medidas, pasos o detalles específicos.",
            "confidence": 0.0 a 1.0,
            "tags": ["tag1", "tag2"]
        }}
    ]
}}

REGLAS:
- NO extraer saludos ni charla trivial
- NO extraer información obvia o genérica
- SÍ extraer: soluciones a problemas reales, trucos del oficio,
  medidas específicas, procedimientos descubiertos en obra
- La confianza debe reflejar qué tan útil y fiable es la información
- Responde SOLO con JSON, sin texto adicional"""


class KnowledgeExtractor:
    """Extrae conocimiento técnico de conversaciones."""
    
    def __init__(self):
        self.llm = LLMProvider.get_fast_llm()
    
    def extract(
        self,
        user_message: str,
        assistant_response: str,
        user_role: str = "general",
    ) -> Optional[list[dict]]:
        """
        Analiza una interacción y extrae conocimiento útil.
        
        Retorna None si no hay conocimiento útil.
        Retorna lista de items de conocimiento si los hay.
        """
        try:
            prompt = EXTRACTION_PROMPT.format(
                user_role=user_role,
                user_message=user_message,
                assistant_response=assistant_response,
            )
            
            response = self.llm.invoke(prompt)
            raw_text = response if isinstance(response, str) else getattr(response, "content", str(response))
            result = self._parse_json(raw_text)
            
            if result and result.get("has_knowledge"):
                items = result.get("items", [])
                # Filtrar por confianza mínima
                valid_items = [
                    item for item in items
                    if item.get("confidence", 0) >= settings.LEARNING_MIN_CONFIDENCE
                ]
                return valid_items if valid_items else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error en extracción: {e}")
            return None
    
    def _parse_json(self, text: str) -> Optional[dict]:
        """Parsea JSON de la respuesta del LLM."""
        try:
            # Buscar JSON en la respuesta
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except json.JSONDecodeError as e:
            logger.warning(f"Error parseando JSON: {e}")
        return None

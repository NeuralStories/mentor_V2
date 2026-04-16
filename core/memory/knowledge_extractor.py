import json
from typing import Optional, Dict
from core.llm.provider import LLMProvider
from core.config import settings
import logging

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """
SISTEMA: Eres un experto en carpintería encargado de extraer conocimiento técnico de las conversaciones.
TU TAREA: Analizar el diálogo y extraer INFORMACIÓN REUTILIZABLE (procedimientos, trucos, soluciones) 
que sea ÚTIL para otros operarios.

INSTRUCCIONES:
1. Solo extrae si hay información técnica concreta (medidas, pasos, soluciones a errores).
2. Ignorar saludos y charlas generales.
3. Formato de salida: JSON puro.

JSON de salida esperado:
{
  "has_technical_knowledge": true/false,
  "knowledge": {
    "title": "Título corto y descriptivo",
    "content": "Contenido detallado y claro (markdown)",
    "category": "puertas/parquet/taller/materiales/seguridad",
    "subcategory": "especificar si aplica",
    "tags": ["tag1", "tag2"],
    "confidence": 0.0 a 1.0 (nivel de detalle/certeza)
  }
}

DIALOGO A ANALIZAR:
Usuario: {user_msg}
Asistente: {assistant_resp}
"""

class KnowledgeExtractor:
    """Extrae perlas de sabiduría técnica de las conversaciones usando el LLM."""
    
    def __init__(self):
        self.llm = LLMProvider.get_fast_llm()
        
    async def extract(self, user_msg: str, assistant_resp: str) -> Optional[Dict]:
        """Analiza la interacción y devuelve conocimiento estructurado si se detecta."""
        prompt = EXTRACTION_PROMPT.format(
            user_msg=user_msg, 
            assistant_resp=assistant_resp
        )
        
        try:
            response = self.llm.invoke(prompt)
            # Limpiar por si el LLM pone texto fuera del JSON
            clean_resp = response.content if hasattr(response, 'content') else str(response)
            if "```json" in clean_resp:
                clean_resp = clean_resp.split("```json")[1].split("```")[0].strip()
            elif "{" in clean_resp:
                clean_resp = "{" + clean_resp.split("{", 1)[1].rsplit("}", 1)[0] + "}"
                
            data = json.loads(clean_resp)
            
            if data.get("has_technical_knowledge") and data.get("knowledge"):
                if data["knowledge"].get("confidence", 0) >= settings.LEARNING_MIN_CONFIDENCE:
                    return data["knowledge"]
            return None
        except Exception as e:
            logger.error(f"Error extrayendo conocimiento: {e}")
            return None

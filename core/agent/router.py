"""
Router de intenciones para Mentor by EgeAI.
Clasifica cada mensaje en una categoría para dirigirlo
a la herramienta correcta.

Estrategia dual:
1. Clasificación por keywords (< 1ms)
2. Clasificación por LLM (solo si keywords no es concluyente)
"""
from core.llm.provider import LLMProvider
import logging

logger = logging.getLogger(__name__)

VALID_INTENTS = [
    "consulta_tecnica",
    "diagnostico",
    "guia_instalacion",
    "verificacion",
    "incidencia",
    "general",
]

# Keywords para clasificación rápida
INTENT_KEYWORDS = {
    "diagnostico": [
        "problema", "no encaja", "no cuadra", "roza", "no cierra",
        "se levanta", "ruido", "hueco mal", "desnivel", "torcido",
        "no vale", "mal", "error", "fallo", "roto", "dañado",
        "no funciona", "se ha roto", "no ajusta", "descuadrado",
        "se mueve", "flojo", "holgura", "cruje", "chirría",
    ],
    "guia_instalacion": [
        "cómo se", "como se", "cómo instalo", "como instalo",
        "pasos para", "procedimiento", "instrucciones",
        "cómo pongo", "como pongo", "cómo coloco", "como coloco",
        "cómo hago", "como hago", "explicame", "explícame",
        "tutorial", "guía", "guia",
    ],
    "verificacion": [
        "está bien", "esta bien", "es correcto", "puedo hacer",
        "debería", "vale así", "confirma", "verificar", "comprobar",
        "es normal", "es suficiente", "basta con",
    ],
    "incidencia": [
        "reportar", "incidencia", "falta material", "no hay stock",
        "se ha roto", "registrar", "anotar", "falta", "necesito pedir",
        "no ha llegado", "pieza equivocada",
    ],
    "consulta_tecnica": [
        "qué medida", "que medida", "cuánto", "cuanto",
        "qué material", "que material", "especificación",
        "ficha técnica", "tolerancia", "qué tipo", "que tipo",
        "cuál es", "cual es", "dimensiones",
    ],
}

ROUTER_PROMPT = """Clasifica esta consulta de un trabajador de
carpintería/instalación en UNA categoría:

- consulta_tecnica: pregunta sobre medidas, materiales, especificaciones
- diagnostico: tiene un problema y necesita ayuda para resolverlo
- guia_instalacion: necesita instrucciones paso a paso
- verificacion: quiere confirmar algo antes de ejecutarlo
- incidencia: reporta un problema, falta de material o fallo
- general: saludo, consulta no técnica u otra cosa

Consulta: "{message}"

Responde SOLO con el nombre de la categoría."""


class IntentRouter:
    def __init__(self):
        self.fast_llm = LLMProvider.get_fast_llm()
    
    async def classify(self, message: str) -> str:
        """
        Clasifica la intención del mensaje.
        Primero intenta por keywords, luego por LLM.
        """
        # 1. Intentar por keywords
        intent = self._classify_by_keywords(message)
        if intent:
            logger.debug(f"Intent por keywords: {intent}")
            return intent
        
        # 2. Usar LLM
        intent = await self._classify_by_llm(message)
        logger.debug(f"Intent por LLM: {intent}")
        return intent
    
    def _classify_by_keywords(self, message: str) -> str | None:
        """Clasificación rápida por keywords."""
        msg = message.lower()
        
        scores = {}
        for intent, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in msg)
            if score > 0:
                scores[intent] = score
        
        if scores:
            # Retornar el intent con más coincidencias
            return max(scores, key=scores.get)
        
        return None
    
    async def _classify_by_llm(self, message: str) -> str:
        """Clasificación por LLM (más lenta pero más precisa)."""
        try:
            prompt = ROUTER_PROMPT.format(message=message)
            response = self.fast_llm.invoke(prompt)
            
            intent = response.strip().lower().replace(" ", "_")
            
            # Validar
            if intent in VALID_INTENTS:
                return intent
            
            # Buscar parcial
            for valid in VALID_INTENTS:
                if valid in intent:
                    return valid
            
            return "general"
        except Exception as e:
            logger.error(f"Error en clasificación LLM: {e}")
            return "general"
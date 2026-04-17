"""
Herramienta para verificaciones y confirmaciones.
Confirma procedimientos, medidas o decisiones.
"""
from core.rag.retriever import RAGRetriever
from core.llm.provider import LLMProvider
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class VerificacionTool:
    """
    Herramienta especializada en verificaciones.
    Confirma si un procedimiento, medida o decisión es correcta.
    """

    def __init__(self):
        self.rag = RAGRetriever()
        self.llm = LLMProvider.get_fast_llm()

    async def verificar(
        self,
        consulta: str,
        contexto: str = None,
        tipo_verificacion: str = "general",  # medida, procedimiento, material, etc.
        user_role: str = "general",
    ) -> Dict[str, Any]:
        """
        Realiza verificación de una consulta específica.

        Args:
            consulta: Lo que se quiere verificar
            contexto: Información adicional del contexto
            tipo_verificacion: tipo de verificación
            user_role: rol del usuario para adaptar respuesta

        Returns:
            Dict con verificación y confianza
        """
        try:
            # Buscar información relevante
            info_relevante = self._buscar_informacion_verificacion(consulta, tipo_verificacion)

            # Construir prompt de verificación
            prompt = self._build_verification_prompt(consulta, contexto, tipo_verificacion, info_relevante, user_role)

            # Generar verificación
            verificacion_raw = await self.llm.ainvoke(prompt)
            resultado = self._parse_verification_response(verificacion_raw.content)

            return {
                "verificacion": resultado,
                "informacion_relevante": info_relevante,
                "tipo": tipo_verificacion,
                "confianza": self._calcular_confianza(resultado, info_relevante),
            }

        except Exception as e:
            logger.error(f"Error en verificación: {e}")
            return {
                "verificacion": {
                    "es_correcto": False,
                    "explicacion": "Error en verificación automática",
                    "recomendacion": "Consultar manual o especialista",
                    "alternativas": ["Revisar documentación oficial"],
                },
                "informacion_relevante": [],
                "tipo": tipo_verificacion,
                "confianza": "baja",
            }

    def _buscar_informacion_verificacion(self, consulta: str, tipo: str) -> List[Dict]:
        """Busca información relevante para la verificación."""
        try:
            collections = ["procedimientos", "aprendido", "problemas_soluciones"]

            results = self.rag.search(
                query=f"verificar {consulta}",
                collections=collections,
                top_k=3,
                min_similarity=0.6,
            )

            return [
                {
                    "contenido": r["content"][:250] + "...",
                    "fuente": r["collection"],
                    "confianza": r["similarity"],
                }
                for r in results
            ]
        except Exception:
            return []

    def _build_verification_prompt(
        self,
        consulta: str,
        contexto: str,
        tipo: str,
        info_relevante: List[Dict],
        user_role: str,
    ) -> str:
        """Construye prompt para verificación."""
        prompt = f"""Eres un verificador técnico especializado en carpintería.

CONSULTA A VERIFICAR: {consulta}
TIPO: {tipo}
CONTEXTO: {contexto or 'No proporcionado'}
ROL DEL USUARIO: {user_role}

INFORMACIÓN RELEVANTE ENCONTRADA:
"""

        if info_relevante:
            for i, info in enumerate(info_relevante, 1):
                prompt += f"{i}. {info['fuente'].title()}: {info['contenido']}\n"
        else:
            prompt += "No se encontró información específica en la base de conocimientos.\n"

        prompt += """
INSTRUCCIONES:
Evalúa si la consulta es correcta basándote en estándares profesionales de carpintería.
Sé directo pero constructivo.

Responde en formato JSON:
{
    "es_correcto": true/false,
    "explicacion": "Explicación técnica detallada",
    "recomendacion": "Qué hacer si es correcto, o cómo corregir si no",
    "alternativas": ["Alternativa 1", "Alternativa 2"],
    "nivel_confianza": "alto/medio/bajo",
    "razones_tecnicas": ["Razón 1", "Razón 2"]
}

IMPORTANTE: Si no tienes información suficiente, indica bajo nivel de confianza."""

        return prompt

    def _parse_verification_response(self, response: str) -> Dict[str, Any]:
        """Parsea respuesta de verificación."""
        try:
            import json
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                parsed = json.loads(response[start:end])
                return parsed
        except Exception:
            pass

        # Fallback: extraer información básica
        es_correcto = "correcto" in response.lower() or "sí" in response.lower() or "true" in response.lower()

        return {
            "es_correcto": es_correcto,
            "explicacion": response[:300] + "..." if len(response) > 300 else response,
            "recomendacion": "Seguir el procedimiento estándar" if es_correcto else "Revisar y corregir",
            "alternativas": ["Consultar especialista si hay dudas"],
            "nivel_confianza": "medio",
            "razones_tecnicas": ["Basado en análisis automático"],
        }

    def _calcular_confianza(self, resultado: Dict, info_relevante: List[Dict]) -> str:
        """Calcula nivel de confianza en la verificación."""
        nivel = resultado.get("nivel_confianza", "medio")

        if info_relevante and any(r.get("confianza", 0) > 0.8 for r in info_relevante):
            return "alto"
        elif info_relevante:
            return "medio"
        else:
            return "bajo"
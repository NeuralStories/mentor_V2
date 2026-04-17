"""
Herramienta para guías de instalación paso a paso.
Proporciona instrucciones detalladas para procedimientos.
"""
from core.rag.retriever import RAGRetriever
from core.llm.provider import LLMProvider
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class GuiaInstalacionTool:
    """
    Herramienta especializada en guías de instalación.
    Proporciona instrucciones paso a paso detalladas.
    """

    def __init__(self):
        self.rag = RAGRetriever()
        self.llm = LLMProvider.get_chat_llm()

    async def generar_guia(
        self,
        procedimiento: str,
        categoria: str = None,
        nivel_experiencia: str = "intermedio",  # principiante, intermedio, avanzado
        herramientas_disponibles: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Genera guía de instalación completa y detallada.

        Args:
            procedimiento: Tipo de instalación (puerta, parquet, etc.)
            categoria: Subcategoría específica
            nivel_experiencia: Ajusta complejidad de instrucciones
            herramientas_disponibles: Lista de herramientas que tiene el usuario

        Returns:
            Dict con guía estructurada
        """
        try:
            # Buscar procedimientos existentes
            guia_base = self._buscar_procedimiento_base(procedimiento, categoria)

            # Si hay guía en base de conocimientos, enriquecerla
            if guia_base:
                guia_completa = await self._enriquecer_guia(
                    guia_base, procedimiento, nivel_experiencia, herramientas_disponibles
                )
            else:
                # Generar guía desde cero
                guia_completa = await self._generar_guia_nueva(
                    procedimiento, categoria, nivel_experiencia, herramientas_disponibles
                )

            return {
                "guia": guia_completa,
                "procedimiento": procedimiento,
                "categoria": categoria or "general",
                "nivel": nivel_experiencia,
                "basado_en_conocimiento": bool(guia_base),
            }

        except Exception as e:
            logger.error(f"Error generando guía: {e}")
            return {
                "guia": {
                    "titulo": f"Guía de instalación: {procedimiento}",
                    "pasos": ["Contactar especialista para instalación segura"],
                    "advertencias": ["Este procedimiento requiere experiencia profesional"],
                    "herramientas_requeridas": ["Herramientas especializadas"],
                },
                "procedimiento": procedimiento,
                "categoria": "error",
                "nivel": "desconocido",
                "basado_en_conocimiento": False,
            }

    def _buscar_procedimiento_base(self, procedimiento: str, categoria: str) -> Dict:
        """Busca procedimiento existente en RAG."""
        try:
            query = f"procedimiento instalación {procedimiento}"
            if categoria:
                query += f" {categoria}"

            results = self.rag.search(
                query=query,
                collections=["procedimientos", "aprendido"],
                top_k=2,
                min_similarity=0.7,
            )

            if results:
                result = results[0]
                return {
                    "titulo": result["metadata"].get("title", f"Instalación de {procedimiento}"),
                    "contenido": result["content"],
                    "fuente": result["collection"],
                    "confianza": result["similarity"],
                }

        except Exception as e:
            logger.error(f"Error buscando procedimiento: {e}")

        return None

    async def _enriquecer_guia(
        self,
        guia_base: Dict,
        procedimiento: str,
        nivel: str,
        herramientas: List[str],
    ) -> Dict[str, Any]:
        """Enriquece guía existente con adaptaciones."""
        prompt = f"""Tienes esta guía base de instalación. Adáptala y expándela:

GUÍA BASE:
{guia_base['contenido']}

PROCEDIMIENTO: {procedimiento}
NIVEL DE EXPERIENCIA: {nivel}
HERRAMIENTAS DISPONIBLES: {', '.join(herramientas) if herramientas else 'No especificadas'}

INSTRUCCIONES:
1. Reestructura en pasos numerados claros
2. Añade tiempos estimados por paso
3. Incluye medidas de seguridad
4. Adapta complejidad al nivel de experiencia
5. Considera herramientas disponibles
6. Añade consejos profesionales
7. Incluye puntos de verificación

Formato de respuesta JSON:
{{
    "titulo": "Título descriptivo",
    "duracion_estimada": "X horas",
    "dificultad": "{nivel}",
    "herramientas_requeridas": ["herramienta1", "herramienta2"],
    "materiales_necesarios": ["material1", "material2"],
    "pasos": [
        {{
            "numero": 1,
            "descripcion": "Descripción detallada",
            "duracion": "X min",
            "seguridad": "Precauciones específicas",
            "consejo": "Tip profesional"
        }}
    ],
    "advertencias": ["Advertencia importante"],
    "verificacion_final": "Cómo verificar que quedó bien"
}}"""

        try:
            response = await self.llm.ainvoke(prompt)
            # Parsear JSON (simplificado)
            import json
            start = response.content.find('{')
            end = response.content.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response.content[start:end])
            else:
                # Fallback si no es JSON válido
                return self._formato_fallback(guia_base)
        except Exception:
            return self._formato_fallback(guia_base)

    async def _generar_guia_nueva(
        self,
        procedimiento: str,
        categoria: str,
        nivel: str,
        herramientas: List[str],
    ) -> Dict[str, Any]:
        """Genera guía completa desde cero."""
        prompt = f"""Genera una guía de instalación profesional para: {procedimiento}

CATEGORÍA: {categoria or 'general'}
NIVEL: {nivel}
HERRAMIENTAS: {', '.join(herramientas) if herramientas else 'Estándar de carpintería'}

La guía debe ser:
- Paso a paso detallada
- Con medidas específicas
- Incluyendo seguridad
- Adaptada al nivel de experiencia
- Profesional y precisa

Usa el mismo formato JSON que en el ejemplo anterior."""

        try:
            response = await self.llm.ainvoke(prompt)
            import json
            start = response.content.find('{')
            end = response.content.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response.content[start:end])
        except Exception:
            pass

        # Fallback simple
        return {
            "titulo": f"Guía de instalación: {procedimiento}",
            "duracion_estimada": "2-4 horas",
            "dificultad": nivel,
            "herramientas_requeridas": ["Herramientas básicas de carpintería"],
            "materiales_necesarios": ["Materiales específicos del procedimiento"],
            "pasos": [
                {
                    "numero": 1,
                    "descripcion": "Preparar materiales y herramientas",
                    "duracion": "15 min",
                    "seguridad": "Usar equipo de protección",
                    "consejo": "Verificar medidas antes de cortar"
                },
                {
                    "numero": 2,
                    "descripcion": "Ejecutar procedimiento principal",
                    "duracion": "1-2 horas",
                    "seguridad": "Trabajar con cuidado",
                    "consejo": "Ir paso a paso sin apresurarse"
                }
            ],
            "advertencias": ["Seguir normas de seguridad"],
            "verificacion_final": "Verificar alineación y funcionamiento"
        }

    def _formato_fallback(self, guia_base: Dict) -> Dict[str, Any]:
        """Formato fallback cuando falla el parsing."""
        return {
            "titulo": guia_base.get("titulo", "Guía de instalación"),
            "duracion_estimada": "1-2 horas",
            "dificultad": "intermedio",
            "herramientas_requeridas": ["Herramientas estándar"],
            "materiales_necesarios": ["Materiales del procedimiento"],
            "pasos": [
                {
                    "numero": 1,
                    "descripcion": guia_base.get("contenido", "Seguir procedimiento estándar")[:200],
                    "duracion": "30 min",
                    "seguridad": "Usar protección personal",
                    "consejo": "Trabajar con precisión"
                }
            ],
            "advertencias": ["Verificar medidas"],
            "verificacion_final": "Comprobar resultado final"
        }
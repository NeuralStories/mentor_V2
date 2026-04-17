"""
Herramienta de diagnóstico para problemas en obra.
Estructura respuestas según protocolo de diagnóstico.
"""
from core.rag.retriever import RAGRetriever
from core.llm.provider import LLMProvider
from core.agent.prompts.diagnostico import DIAGNOSTICO_PROMPT
from core.memory.learning_pipeline import LearningPipeline
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DiagnosticoTool:
    """
    Herramienta especializada en diagnóstico de problemas.
    Usa protocolo estructurado para identificar causas y soluciones.
    """

    def __init__(self):
        self.rag = RAGRetriever()
        self.llm = LLMProvider.get_chat_llm()
        self.learning = LearningPipeline()

    async def diagnosticar(
        self,
        problema: str,
        categoria: str = None,
        contexto_adicional: str = None,
        user_id: str = None,
    ) -> Dict[str, Any]:
        """
        Realiza diagnóstico completo de un problema.

        Args:
            problema: Descripción del problema
            categoria: puertas, parquet, etc.
            contexto_adicional: Información extra
            user_id: Para registrar incidencia si aplica

        Returns:
            Dict con diagnóstico estructurado
        """
        try:
            # Buscar soluciones similares en la base de conocimientos
            soluciones_similares = self._buscar_soluciones_similares(problema, categoria)

            # Construir prompt de diagnóstico
            prompt = self._build_diagnostic_prompt(problema, categoria, contexto_adicional, soluciones_similares)

            # Generar diagnóstico
            diagnostico_raw = await self.llm.ainvoke(prompt)
            diagnostico = self._parse_diagnostic_response(diagnostico_raw.content)

            # Si se identifica como incidencia, registrarla
            if self._es_incidencia_grave(diagnostico) and user_id:
                self._registrar_incidencia(problema, diagnostico, user_id, categoria)

            return {
                "diagnostico": diagnostico,
                "soluciones_similares": soluciones_similares,
                "categoria_detectada": categoria or "general",
                "registrado_como_incidencia": self._es_incidencia_grave(diagnostico),
            }

        except Exception as e:
            logger.error(f"Error en diagnóstico: {e}")
            return {
                "diagnostico": {
                    "problema_identificado": "Error en diagnóstico",
                    "causa_probable": "Problema técnico",
                    "solucion_recomendada": "Contactar soporte técnico",
                    "plan_b": "Revisar manuales del fabricante",
                    "prevencion": "Documentar el problema para análisis",
                },
                "soluciones_similares": [],
                "categoria_detectada": "error",
                "registrado_como_incidencia": False,
            }

    def _buscar_soluciones_similares(self, problema: str, categoria: str) -> List[Dict]:
        """Busca soluciones similares en RAG."""
        try:
            collections = ["problemas_soluciones", "incidencias", "aprendido"]
            if categoria:
                collections.append("procedimientos")

            results = self.rag.search(
                query=f"problema: {problema}",
                collections=collections,
                top_k=3,
                min_similarity=0.6,
            )

            return [
                {
                    "titulo": r["metadata"].get("title", "Solución similar"),
                    "contenido": r["content"][:200] + "...",
                    "similitud": r["similarity"],
                    "fuente": r["collection"],
                }
                for r in results
            ]
        except Exception:
            return []

    def _build_diagnostic_prompt(
        self,
        problema: str,
        categoria: str,
        contexto: str,
        soluciones_similares: List[Dict],
    ) -> str:
        """Construye prompt completo para diagnóstico."""
        prompt = DIAGNOSTICO_PROMPT

        # Añadir información específica
        prompt += f"\n\nPROBLEMA REPORTADO: {problema}"
        if categoria:
            prompt += f"\nCATEGORÍA: {categoria}"
        if contexto:
            prompt += f"\nCONTEXTO ADICIONAL: {contexto}"

        # Añadir soluciones similares si existen
        if soluciones_similares:
            prompt += "\n\nSOLUCIONES SIMILARES ENCONTRADAS:"
            for sol in soluciones_similares:
                prompt += f"\n- {sol['titulo']}: {sol['contenido']}"

        prompt += "\n\nProporciona el diagnóstico siguiendo EXACTAMENTE la estructura especificada."

        return prompt

    def _parse_diagnostic_response(self, response: str) -> Dict[str, str]:
        """Parsea la respuesta del LLM en estructura de diagnóstico."""
        # Dividir por secciones
        sections = {
            "problema_identificado": "",
            "causa_probable": "",
            "solucion_recomendada": "",
            "plan_b": "",
            "prevencion": "",
        }

        lines = response.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detectar secciones
            if "PROBLEMA IDENTIFICADO" in line.upper():
                current_section = "problema_identificado"
            elif "CAUSA MÁS PROBABLE" in line.upper() or "CAUSA PROBABLE" in line.upper():
                current_section = "causa_probable"
            elif "SOLUCIÓN RECOMENDADA" in line.upper():
                current_section = "solucion_recomendada"
            elif "PLAN B" in line.upper():
                current_section = "plan_b"
            elif "CÓMO EVITARLO" in line.upper() or "PREVENCIÓN" in line.upper() or "PREVENIR" in line.upper():
                current_section = "prevencion"
            elif current_section and line:
                # Añadir contenido a la sección actual
                if sections[current_section]:
                    sections[current_section] += " "
                sections[current_section] += line

        return sections

    def _es_incidencia_grave(self, diagnostico: Dict[str, str]) -> bool:
        """Determina si el problema debe registrarse como incidencia."""
        # Lógica simple: si la causa sugiere defecto de material o instalación crítica
        causa = diagnostico.get("causa_probable", "").lower()
        problema = diagnostico.get("problema_identificado", "").lower()

        indicadores_graves = [
            "defecto", "fabricante", "calidad", "dañado", "roto",
            "seguridad", "estructural", "grave", "critico"
        ]

        return any(indicador in causa or indicador in problema for indicador in indicadores_graves)

    def _registrar_incidencia(self, problema: str, diagnostico: Dict, user_id: str, categoria: str):
        """Registra el problema como incidencia."""
        try:
            descripcion = f"{problema}\n\nDiagnóstico: {diagnostico.get('problema_identificado', '')}"

            self.learning.memory.save_incident(
                reported_by=user_id,
                category=categoria or "general",
                description=descripcion,
                problem_type="diagnostico_automatico",
                severity="media",  # Los diagnósticos automáticos son media por defecto
            )

            logger.info(f"Incidencia registrada automáticamente para user {user_id}")
        except Exception as e:
            logger.error(f"Error registrando incidencia: {e}")
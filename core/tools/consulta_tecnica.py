"""
Herramienta para consultas técnicas.
Busca especificaciones, medidas y datos técnicos.
"""
from core.rag.retriever import RAGRetriever
from core.llm.provider import LLMProvider
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ConsultaTecnicaTool:
    """
    Herramienta especializada en consultas técnicas.
    Busca información específica sobre medidas, materiales, especificaciones.
    """

    def __init__(self):
        self.rag = RAGRetriever()
        self.llm = LLMProvider.get_fast_llm()

    async def consultar(
        self,
        query: str,
        categoria: str = None,
        tipo: str = None,
    ) -> Dict[str, Any]:
        """
        Realiza una consulta técnica específica.

        Args:
            query: La consulta del usuario
            categoria: puertas, parquet, materiales, etc.
            tipo: medida, material, especificacion, etc.

        Returns:
            Dict con respuesta técnica y fuentes
        """
        try:
            # Determinar colecciones relevantes
            collections = self._get_collections_for_query(categoria)

            # Buscar en RAG
            results = self.rag.search(
                query=query,
                collections=collections,
                top_k=5,
                min_similarity=0.7,
            )

            if results:
                # Si hay resultados directos del RAG
                response = self._format_technical_response(results, query)
                sources = [{"collection": r["collection"], "similarity": r["similarity"]} for r in results]
            else:
                # Si no hay resultados, generar respuesta basada en conocimiento general
                response = await self._generate_general_response(query, categoria, tipo)
                sources = []

            return {
                "response": response,
                "sources": sources,
                "confidence": "high" if results else "medium",
            }

        except Exception as e:
            logger.error(f"Error en consulta técnica: {e}")
            return {
                "response": "No pude encontrar información específica. Te recomiendo consultar las especificaciones del fabricante.",
                "sources": [],
                "confidence": "low",
            }

    def _get_collections_for_query(self, categoria: str = None) -> List[str]:
        """Determina colecciones según categoría."""
        if categoria == "puertas":
            return ["procedimientos", "problemas_soluciones", "aprendido"]
        elif categoria == "parquet":
            return ["procedimientos", "problemas_soluciones", "aprendido"]
        elif categoria == "materiales":
            return ["materiales", "procedimientos"]
        else:
            return ["procedimientos", "materiales", "aprendido"]

    def _format_technical_response(self, results: List[Dict], query: str) -> str:
        """Formatea respuesta técnica desde resultados del RAG."""
        response_parts = [f"Información técnica sobre: {query}\n"]

        for i, result in enumerate(results, 1):
            collection_name = result["collection"].replace("_", " ").title()
            content = result["content"][:300] + "..." if len(result["content"]) > 300 else result["content"]
            similarity = result["similarity"]

            response_parts.append(f"{i}. {collection_name} (confianza: {similarity:.1%})")
            response_parts.append(f"   {content}\n")

        return "\n".join(response_parts)

    async def _generate_general_response(self, query: str, categoria: str, tipo: str) -> str:
        """Genera respuesta basada en conocimiento general cuando no hay RAG."""
        prompt = f"""Como experto en carpintería, responde esta consulta técnica de manera precisa y profesional:

Consulta: {query}
Categoría: {categoria or 'general'}
Tipo: {tipo or 'general'}

Proporciona medidas exactas, especificaciones técnicas o recomendaciones basadas en estándares de la industria.
Si no tienes información específica, indícalo claramente."""

        try:
            response = await self.llm.ainvoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generando respuesta general: {e}")
            return "No tengo información específica sobre esta consulta técnica."
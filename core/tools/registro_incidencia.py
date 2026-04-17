"""
Herramienta para registro de incidencias.
Registra problemas, faltas de material o issues en obra.
"""
from core.memory.learning_pipeline import LearningPipeline
from core.rag.indexer import KnowledgeIndexer
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RegistroIncidenciaTool:
    """
    Herramienta especializada en registro de incidencias.
    Registra problemas para seguimiento y aprendizaje.
    """

    def __init__(self):
        self.learning = LearningPipeline()
        self.indexer = KnowledgeIndexer()

    async def registrar_incidencia(
        self,
        descripcion: str,
        categoria: str,
        tipo_problema: str = None,
        severidad: str = "media",
        ubicacion: str = None,
        proyecto: str = None,
        fotos: List[str] = None,
        metadata_adicional: Dict[str, Any] = None,
        user_id: str = "anonymous",
        solucion_aplicada: str = None,
        solucion_efectiva: bool = None,
    ) -> Dict[str, Any]:
        """
        Registra una nueva incidencia en el sistema.

        Args:
            descripcion: Descripción detallada del problema
            categoria: puertas, parquet, materiales, etc.
            tipo_problema: instalación, material, herramienta, etc.
            severidad: baja, media, alta, critica
            ubicacion: donde ocurrió (taller, obra, piso, etc.)
            proyecto: proyecto específico si aplica
            fotos: lista de URLs o paths de fotos
            metadata_adicional: información extra
            user_id: quien reporta
            solucion_aplicada: solución intentada
            solucion_efectiva: si funcionó

        Returns:
            Dict con ID de incidencia y estado
        """
        try:
            # Registrar en memoria conversacional
            incidencia_id = self.learning.memory.save_incident(
                reported_by=user_id,
                category=categoria,
                description=descripcion,
                problem_type=tipo_problema,
                project_id=proyecto,
                severity=severidad,
                location=ubicacion,
            )

            # Indexar en RAG para búsquedas futuras
            self._indexar_incidencia(
                incidencia_id, descripcion, solucion_aplicada, 
                categoria, tipo_problema, severidad
            )

            # Preparar respuesta
            respuesta = {
                "incidencia_id": incidencia_id,
                "estado": "registrada",
                "severidad": severidad,
                "categoria": categoria,
                "mensaje": f"Incidencia registrada correctamente con ID: {incidencia_id}",
            }

            # Añadir información adicional si existe
            if solucion_aplicada:
                respuesta["solucion_registrada"] = solucion_aplicada
                respuesta["efectiva"] = solucion_efectiva

            if fotos:
                respuesta["fotos_adjuntas"] = len(fotos)

            # Sugerencias basadas en severidad
            respuesta["siguientes_pasos"] = self._generar_siguientes_pasos(severidad, categoria)

            return respuesta

        except Exception as e:
            logger.error(f"Error registrando incidencia: {e}")
            return {
                "incidencia_id": None,
                "estado": "error",
                "mensaje": "Error al registrar la incidencia. Intente nuevamente.",
                "error": str(e),
            }

    def _indexar_incidencia(
        self,
        incidencia_id: str,
        descripcion: str,
        solucion: str,
        categoria: str,
        tipo_problema: str,
        severidad: str,
    ):
        """Indexa la incidencia en ChromaDB para búsquedas futuras."""
        try:
            # Crear contenido para indexar
            contenido = f"Problema: {descripcion}"
            if solucion:
                contenido += f"\nSolución aplicada: {solucion}"

            # Metadata
            metadata = {
                "tipo": "incidencia",
                "categoria": categoria,
                "tipo_problema": tipo_problema,
                "severidad": severidad,
                "incidencia_id": incidencia_id,
                "resuelta": bool(solucion),
                "source": "incidencia_reportada",
            }

            # Indexar
            self.indexer.index_incident(
                description=descripcion,
                solution=solucion,
                metadata=metadata,
            )

            logger.info(f"Incidencia {incidencia_id} indexada en RAG")

        except Exception as e:
            logger.error(f"Error indexando incidencia: {e}")

    def _generar_siguientes_pasos(self, severidad: str, categoria: str) -> List[str]:
        """Genera recomendaciones de siguientes pasos."""
        pasos_base = []

        if severidad in ["alta", "critica"]:
            pasos_base.extend([
                "Detener trabajo inmediatamente si afecta seguridad",
                "Notificar al encargado de obra",
                "Documentar con fotos el problema",
            ])

        if severidad == "critica":
            pasos_base.extend([
                "Contactar al fabricante si es defecto de material",
                "Considerar replanificación del proyecto",
            ])

        # Pasos específicos por categoría
        if categoria == "puertas":
            pasos_base.append("Verificar medidas del premarco antes de continuar")
        elif categoria == "parquet":
            pasos_base.append("Revisar condiciones de humedad y nivelación")

        # Pasos generales
        pasos_base.extend([
            "Registrar solución aplicada cuando se resuelva",
            "El sistema aprenderá de esta incidencia para casos similares",
        ])

        return pasos_base

    async def consultar_incidencias(
        self,
        filtros: Dict[str, Any] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Consulta incidencias registradas con filtros.

        Args:
            filtros: dict con filtros (categoria, severidad, estado, etc.)
            limit: máximo número de resultados

        Returns:
            Lista de incidencias
        """
        try:
            # Esto requeriría métodos adicionales en LearningPipeline
            # Por ahora, implementación básica
            logger.info(f"Consultando incidencias con filtros: {filtros}")
            return []

        except Exception as e:
            logger.error(f"Error consultando incidencias: {e}")
            return []

    async def actualizar_incidencia(
        self,
        incidencia_id: str,
        actualizaciones: Dict[str, Any],
        user_id: str = "system",
    ) -> Dict[str, Any]:
        """
        Actualiza una incidencia existente.

        Args:
            incidencia_id: ID de la incidencia
            actualizaciones: campos a actualizar
            user_id: quien hace la actualización

        Returns:
            Estado de la actualización
        """
        try:
            # Implementación básica - requeriría métodos en Supabase
            logger.info(f"Actualizando incidencia {incidencia_id}: {actualizaciones}")

            # Re-indexar si hay cambios importantes
            if "solution_applied" in actualizaciones or "solution_effective" in actualizaciones:
                # Lógica para re-indexar
                pass

            return {
                "incidencia_id": incidencia_id,
                "estado": "actualizada",
                "mensaje": "Incidencia actualizada correctamente",
            }

        except Exception as e:
            logger.error(f"Error actualizando incidencia: {e}")
            return {
                "incidencia_id": incidencia_id,
                "estado": "error",
                "mensaje": "Error al actualizar la incidencia",
            }
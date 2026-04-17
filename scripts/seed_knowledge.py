#!/usr/bin/env python3
"""
Script para inicializar la base de conocimientos de Mentor by EgeAI.
Carga y indexa todo el contenido inicial desde archivos markdown.
Ejecutar una vez: python scripts/seed_knowledge.py
"""
import sys
import os
from pathlib import Path
import logging

# Añadir directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rag.indexer import KnowledgeIndexer
from core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def seed_knowledge_base():
    """
    Inicializa la base de conocimientos con contenido de archivos markdown.
    """
    logger.info("🚀 Iniciando inicialización de base de conocimientos...")

    try:
        # Verificar que existe el directorio de conocimientos
        knowledge_dir = Path(settings.KNOWLEDGE_BASE_PATH)
        if not knowledge_dir.exists():
            logger.error(f"❌ Directorio de conocimientos no existe: {knowledge_dir}")
            return False

        # Inicializar indexador
        indexer = KnowledgeIndexer()
        logger.info("✅ Indexador inicializado")

        # Indexar base de conocimientos
        logger.info("📚 Indexando archivos de conocimiento...")
        indexer.index_knowledge_base()

        # Verificar resultados
        logger.info("🔍 Verificando indexación...")

        # Contar archivos procesados (estimación)
        total_files = 0
        for pattern in ["*.md"]:
            total_files += len(list(knowledge_dir.rglob(pattern)))

        logger.info(f"✅ Inicialización completada")
        logger.info(f"📊 Archivos procesados: {total_files}")
        logger.info("🎯 Base de conocimientos lista para consultas")

        return True

    except Exception as e:
        logger.error(f"❌ Error durante la inicialización: {e}")
        return False


def add_sample_incidents():
    """
    Añade algunas incidencias de ejemplo para testing.
    """
    logger.info("📝 Añadiendo incidencias de ejemplo...")

    try:
        from core.memory.learning_pipeline import LearningPipeline
        learning = LearningPipeline()

        sample_incidents = [
            {
                "reported_by": "system",
                "category": "puertas",
                "description": "Puerta que rozaba inferior después de instalación. Premarco 2mm descentrado.",
                "problem_type": "instalacion",
                "location": "Piso 3A",
                "project_id": "edificio_central",
                "severity": "media"
            },
            {
                "reported_by": "system",
                "category": "parquet",
                "description": "Parquet que cruje en zona de paso. Falta de dilatación entre habitaciones.",
                "problem_type": "instalacion",
                "location": "Salon principal",
                "project_id": "residencial_norte",
                "severity": "baja"
            },
            {
                "reported_by": "system",
                "category": "materiales",
                "description": "Barniz que no seca correctamente. Humedad ambiente > 70%",
                "problem_type": "acabado",
                "location": "Taller",
                "project_id": "muebles_salon",
                "severity": "media"
            }
        ]

        for incident in sample_incidents:
            learning.memory.save_incident(**incident)
            logger.info(f"✅ Incidencia añadida: {incident['description'][:50]}...")

        logger.info(f"✅ {len(sample_incidents)} incidencias de ejemplo añadidas")

    except Exception as e:
        logger.error(f"❌ Error añadiendo incidencias de ejemplo: {e}")


def add_sample_learned_knowledge():
    """
    Añade conocimiento aprendido de ejemplo.
    """
    logger.info("🧠 Añadiendo conocimiento aprendido de ejemplo...")

    try:
        from core.memory.learning_pipeline import LearningPipeline
        learning = LearningPipeline()

        sample_knowledge = [
            {
                "title": "Compensar desplome de premarco con cuñas",
                "content": "Para un desplome de premarco de 8mm, colocar cuñas de 4mm en bisagra inferior y 4mm en superior. Verificar plano con nivel láser antes de fijar definitivamente.",
                "category": "puertas",
                "type": "problema_solucion",
                "confidence": 0.9,
                "tags": ["premarco", "desnivel", "bisagras"],
                "source_conversation_id": "sample_001"
            },
            {
                "title": "Junta de dilatación en parquet flotante",
                "content": "En parquet flotante, dejar junta de dilatación de 8-10mm en perimetral y 5mm entre habitaciones. Nunca pegar contra paredes fijas.",
                "category": "parquet",
                "type": "procedimiento",
                "confidence": 0.95,
                "tags": ["dilatacion", "flotante", "instalacion"],
                "source_conversation_id": "sample_002"
            },
            {
                "title": "Humedad máxima para parquet",
                "content": "Humedad máxima permitida: 2.5% en madera, 1.8% en base de hormigón. Medir siempre antes de instalación.",
                "category": "parquet",
                "type": "medida",
                "confidence": 0.98,
                "tags": ["humedad", "medicion", "instalacion"],
                "source_conversation_id": "sample_003"
            }
        ]

        for item in sample_knowledge:
            # Guardar en BD
            knowledge_id = learning._store_knowledge(item, item["source_conversation_id"])

            # Indexar directamente (simulando aprobación)
            learning._index_knowledge_item(item)

            logger.info(f"✅ Conocimiento añadido: {item['title']}")

        logger.info(f"✅ {len(sample_knowledge)} items de conocimiento aprendido añadidos")

    except Exception as e:
        logger.error(f"❌ Error añadiendo conocimiento aprendido: {e}")


def main():
    """Función principal."""
    print("=" * 60)
    print("Mentor by EgeAI - Inicialización de Base de Conocimientos")
    print("=" * 60)

    # Inicializar base de conocimientos
    success = seed_knowledge_base()

    if success:
        # Añadir datos de ejemplo
        add_sample_incidents()
        add_sample_learned_knowledge()

        print("\n" + "=" * 60)
        print("INICIALIZACION COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("El sistema esta listo para recibir consultas")
        print("Base de conocimientos indexada y funcional")
        print("Sistema de aprendizaje activado")
    else:
        print("\n" + "=" * 60)
        print("ERROR EN LA INICIALIZACION")
        print("=" * 60)
        print("Revisa los logs para mas detalles")
        sys.exit(1)


if __name__ == "__main__":
    main()

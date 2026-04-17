#!/usr/bin/env python3
"""
Script de prueba para la zona de ingesta de Mentor by EgeAI.
Crea un archivo de prueba y lo procesa completamente.
"""
import os
import sys
import time
from pathlib import Path

# Añadir directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tools.document_parser import DocumentParser
from core.rag.indexer import KnowledgeIndexer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_document():
    """Crea un documento de prueba en formato Markdown."""
    test_content = """# Guía de Instalación de Puertas

## Introducción
Esta guía proporciona instrucciones detalladas para la instalación profesional de puertas.

## Herramientas Necesarias
- Nivel láser
- Taladro eléctrico
- Destornilladores
- Sierra circular
- Metro y lápiz

## Preparación
Antes de instalar la puerta, verifica que el marco esté nivelado y las medidas sean correctas.

### Medidas Estándar
- Alto de puerta: 210 cm
- Ancho estándar: 70-90 cm
- Grosor marco: 4-5 cm

## Proceso de Instalación

### Paso 1: Verificación del Marco
Verifica que el marco esté perfectamente nivelado usando el nivel láser.

### Paso 2: Colocación de la Puerta
1. Levanta la puerta con ayuda
2. Coloca los goznes superiores primero
3. Ajusta la puerta para que quede centrada

### Paso 3: Ajustes Finales
- Verifica que la puerta no roce
- Ajusta los goznes si es necesario
- Instala el pomo y cerradura

## Consejos Profesionales
- Siempre usa protección ocular
- Trabaja con calma y precisión
- Verifica medidas dos veces antes de cortar

## Solución de Problemas
Si la puerta roza inferior: calza el marco con cuñas de madera."""

    # Crear directorio de prueba si no existe
    test_dir = Path("test_documents")
    test_dir.mkdir(exist_ok=True)

    # Crear archivo de prueba
    test_file = test_dir / "guia_puertas_prueba.md"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)

    logger.info(f"Documento de prueba creado: {test_file}")
    return test_file

def test_document_parsing():
    """Prueba el parsing de documentos."""
    logger.info("🧪 Probando parsing de documentos...")

    # Crear documento de prueba
    test_file = create_test_document()

    try:
        # Parsear documento
        content, metadata = DocumentParser.parse_file(str(test_file))

        logger.info("✅ Parsing exitoso:")
        logger.info(f"   - Archivo: {metadata['file_name']}")
        logger.info(f"   - Formato: {metadata['file_format']}")
        logger.info(f"   - Tamaño: {metadata['file_size']} bytes")
        logger.info(f"   - Palabras: {metadata.get('word_count', 0)}")
        logger.info(f"   - Caracteres: {metadata.get('char_count', 0)}")
        logger.info(f"   - Contenido extraído: {len(content)} caracteres")

        return content, metadata

    except Exception as e:
        logger.error(f"❌ Error en parsing: {e}")
        return None, None

def test_document_indexing(content, metadata):
    """Prueba la indexación de documentos."""
    logger.info("🧪 Probando indexación de documentos...")

    try:
        indexer = KnowledgeIndexer()

        # Indexar documento
        file_path = str(Path("test_documents/guia_puertas_prueba.md"))
        chunks_created = indexer.index_single_file(file_path, "procedimientos")

        logger.info("✅ Indexación exitosa:")
        logger.info(f"   - Chunks creados: {chunks_created}")
        logger.info(f"   - Colección: procedimientos")

        return True

    except Exception as e:
        logger.error(f"❌ Error en indexación: {e}")
        return False

def test_document_search():
    """Prueba la búsqueda en documentos indexados."""
    logger.info("🧪 Probando búsqueda en documentos...")

    try:
        from core.rag.retriever import RAGRetriever

        retriever = RAGRetriever()

        # Buscar información
        results = retriever.search(
            query="instalación puerta marco",
            collections=["procedimientos"],
            top_k=3
        )

        logger.info("Búsqueda exitosa:")
        logger.info(f"   - Resultados encontrados: {len(results)}")

        for i, result in enumerate(results, 1):
            logger.info(f"   Resultado {i}:")
            logger.info(f"     - Similitud: {result['similarity']:.1%}")
            logger.info(f"     - Contenido: {result['content'][:100]}...")

        return len(results) > 0

    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        return False

def cleanup_test_files():
    """Limpia archivos de prueba."""
    logger.info("🧹 Limpiando archivos de prueba...")

    import shutil

    # Eliminar directorio de prueba
    test_dir = Path("test_documents")
    if test_dir.exists():
        shutil.rmtree(test_dir)
        logger.info("✅ Archivos de prueba eliminados")

def main():
    """Función principal de pruebas."""
    print("=" * 60)
    print("PRUEBAS DE ZONA DE INGESTA - Mentor by EgeAI")
    print("=" * 60)

    success_count = 0
    total_tests = 3

    # Prueba 1: Parsing de documentos
    content, metadata = test_document_parsing()
    if content and metadata:
        success_count += 1
        print("Parsing: PASO")
    else:
        print("Parsing: FALLO")

    # Prueba 2: Indexación
    if content and metadata:
        if test_document_indexing(content, metadata):
            success_count += 1
            print("Indexación: PASO")
        else:
            print("Indexación: FALLO")

    # Prueba 3: Búsqueda
    if test_document_search():
        success_count += 1
        print("Búsqueda: PASO")
    else:
        print("Búsqueda: FALLO")

    # Limpiar
    cleanup_test_files()

    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS: {success_count}/{total_tests} pruebas pasaron")

    if success_count == total_tests:
        print("¡Zona de ingesta funcionando perfectamente!")
        print("El sistema está listo para subir y procesar documentos")
    else:
        print("Algunas pruebas fallaron. Revisa los logs para más detalles")

    print("=" * 60)

if __name__ == "__main__":
    main()
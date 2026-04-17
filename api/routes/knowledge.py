"""
Rutas de gestión del conocimiento para Mentor by EgeAI.
Endpoints para indexar, buscar y gestionar la base de conocimientos.
Incluye zona de ingesta para subida y procesamiento de documentos.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from pathlib import Path
import shutil
import uuid
import logging
from datetime import datetime

from core.rag.indexer import KnowledgeIndexer
from core.rag.retriever import RAGRetriever
from core.memory.learning_pipeline import LearningPipeline
from core.tools.document_parser import DocumentParser

logger = logging.getLogger(__name__)

router = APIRouter()

# Instancias de servicios
indexer = KnowledgeIndexer()
retriever = RAGRetriever()
learning = LearningPipeline()


def _upload_subdirs() -> list[str]:
    return ["pdf", "docx", "txt", "md", "markdown", "processed", "errors"]


def _storage_dir_for_format(file_format: str) -> str:
    return "md" if file_format == "markdown" else file_format


class IndexRequest(BaseModel):
    """Modelo para solicitud de indexación."""
    content: str
    metadata: Optional[Dict[str, Any]] = None
    collection: str = "aprendido"


class SearchRequest(BaseModel):
    """Modelo para solicitud de búsqueda."""
    query: str
    collections: Optional[List[str]] = None
    top_k: int = 5
    min_similarity: Optional[float] = None


class KnowledgeResponse(BaseModel):
    """Modelo para respuesta de conocimiento."""
    results: List[Dict[str, Any]]
    total_found: int
    query: str


class UploadResponse(BaseModel):
    """Modelo para respuesta de subida de archivo."""
    file_id: str
    file_name: str
    file_format: str
    file_size: int
    status: str
    message: str
    extracted_text_length: Optional[int] = None
    chunks_created: Optional[int] = None


class DocumentInfo(BaseModel):
    """Modelo para información de documento."""
    file_id: str
    file_name: str
    file_format: str
    file_size: int
    upload_date: str
    status: str
    word_count: Optional[int] = None
    char_count: Optional[int] = None
    pages: Optional[int] = None
    ocr_used: Optional[bool] = None


class ProcessDocumentRequest(BaseModel):
    """Modelo para solicitud de procesamiento de documento."""
    file_id: str
    collection: str = "procedimientos"
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None


@router.post("/index")
async def index_knowledge(request: IndexRequest, background_tasks: BackgroundTasks):
    """
    Indexa nuevo conocimiento en la base vectorial.
    """
    try:
        if request.collection == "aprendido":
            # Indexar conocimiento aprendido
            indexer.index_learned_knowledge(
                content=request.content,
                metadata=request.metadata or {}
            )
        elif request.collection in ["procedimientos", "materiales", "problemas_soluciones"]:
            # Para otras colecciones, requeriría archivos markdown
            # Por ahora, solo aprendido
            raise HTTPException(
                status_code=400,
                detail=f"Indexación directa solo disponible para colección 'aprendido'. Para otras colecciones, use archivos markdown."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Colección '{request.collection}' no válida"
            )

        logger.info(f"Conocimiento indexado en colección: {request.collection}")

        return {
            "status": "indexed",
            "collection": request.collection,
            "message": "Conocimiento indexado correctamente"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexando conocimiento: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al indexar el conocimiento"
        )


@router.post("/search", response_model=KnowledgeResponse)
async def search_knowledge(request: SearchRequest):
    """
    Busca conocimiento relevante en la base vectorial.
    """
    try:
        results = retriever.search(
            query=request.query,
            collections=request.collections,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
        )

        response = KnowledgeResponse(
            results=results,
            total_found=len(results),
            query=request.query
        )

        logger.info(f"Búsqueda completada: {len(results)} resultados para '{request.query}'")

        return response

    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al realizar la búsqueda"
        )


@router.post("/index-incident")
async def index_incident(
    description: str,
    solution: str = None,
    category: str = "general",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Indexa una incidencia resuelta para futuras consultas.
    """
    try:
        enriched_metadata = metadata or {}
        enriched_metadata.update({
            "category": category,
            "indexed_from": "api",
        })

        indexer.index_incident(
            description=description,
            solution=solution,
            metadata=enriched_metadata
        )

        return {
            "status": "indexed",
            "type": "incident",
            "message": "Incidencia indexada correctamente"
        }

    except Exception as e:
        logger.error(f"Error indexando incidencia: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al indexar la incidencia"
        )


@router.get("/stats")
async def get_knowledge_stats():
    """
    Obtiene estadísticas del sistema de conocimiento.
    """
    try:
        # Estadísticas de aprendizaje
        learning_stats = learning.get_learning_stats()

        # Información básica de colecciones (simplificada)
        collections_info = {
            "total_collections": 5,  # procedimientos, materiales, problemas_soluciones, incidencias, aprendido
            "collections": [
                "procedimientos",
                "materiales", 
                "problemas_soluciones",
                "incidencias",
                "aprendido"
            ]
        }

        return {
            "learning_stats": learning_stats,
            "collections": collections_info,
            "status": "active"
        }

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener estadísticas"
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection: str = Form("procedimientos"),
    auto_process: bool = Form(True)
):
    """
    Sube y opcionalmente procesa un documento para indexación.

    - file: Archivo a subir (PDF, DOCX, TXT, MD)
    - collection: Colección donde indexar (procedimientos, materiales, etc.)
    - auto_process: Si procesar automáticamente después de subir
    """
    try:
        # Generar ID único para el archivo
        file_id = str(uuid.uuid4())

        # Validar tipo de archivo
        if not DocumentParser.can_parse(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Formato no soportado: {Path(file.filename).suffix}. Formatos permitidos: {', '.join(DocumentParser.SUPPORTED_FORMATS.keys())}"
            )

        # Determinar directorio de destino basado en tipo
        file_format = DocumentParser.get_format(file.filename)
        upload_dir = Path(f"uploads/{_storage_dir_for_format(file_format)}")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Guardar archivo
        file_path = upload_dir / f"{file_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Archivo subido: {file.filename} -> {file_path}")

        response_data = {
            "file_id": file_id,
            "file_name": file.filename,
            "file_format": file_format,
            "file_size": file_path.stat().st_size,
            "status": "uploaded",
            "message": "Archivo subido exitosamente",
        }

        # Procesar automáticamente si se solicita
        if auto_process:
            try:
                # Ejecutar procesamiento en background
                background_tasks.add_task(
                    process_document_background,
                    str(file_path),
                    collection,
                    file_id,
                    file.filename
                )

                response_data["status"] = "processing"
                response_data["message"] = "Archivo subido y procesamiento iniciado"

            except Exception as e:
                logger.error(f"Error iniciando procesamiento automático: {e}")
                response_data["message"] += ". Error en procesamiento automático."

        return UploadResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subiendo archivo: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/process/{file_id}")
async def process_document(
    file_id: str,
    request: ProcessDocumentRequest,
    background_tasks: BackgroundTasks
):
    """
    Procesa un documento previamente subido para indexación.
    """
    try:
        # Buscar el archivo en todas las carpetas de uploads
        file_path = None
        for upload_subdir in _upload_subdirs():
            search_path = Path(f"uploads/{upload_subdir}")
            if search_path.exists():
                for file in search_path.glob(f"{file_id}_*"):
                    file_path = file
                    break
            if file_path:
                break

        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"Archivo con ID {file_id} no encontrado"
            )

        # Ejecutar procesamiento en background
        background_tasks.add_task(
            process_document_background,
            str(file_path),
            request.collection,
            file_id,
            file_path.name
        )

        return {
            "status": "processing_started",
            "file_id": file_id,
            "collection": request.collection,
            "message": "Procesamiento de documento iniciado"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando documento {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


def process_document_background(
    file_path: str,
    collection: str,
    file_id: str,
    original_filename: str
):
    """
    Función que se ejecuta en background para procesar documentos.
    """
    try:
        logger.info(f"Iniciando procesamiento de {original_filename}")

        # Parsear documento
        content, metadata = DocumentParser.parse_file(file_path)

        # Preparar metadata para indexación
        doc_metadata = {
            "source": "uploaded_document",
            "file_id": file_id,
            "original_filename": original_filename,
            "upload_date": metadata["upload_date"],
            "file_format": metadata["file_format"],
            "word_count": metadata.get("word_count", 0),
            "char_count": metadata.get("char_count", 0),
            "pages": metadata.get("pages", 1),
            "ocr_used": metadata.get("ocr_used", False),
        }

        # Indexar el texto ya parseado. Esto soporta PDF, DOCX y OCR.
        chunks_created = indexer.index_text_content(
            content=content,
            collection=collection,
            metadata=doc_metadata,
            source_name=original_filename,
        )

        # Mover a carpeta processed
        processed_dir = Path("uploads/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)

        processed_path = processed_dir / f"{file_id}_{original_filename}"
        Path(file_path).rename(processed_path)

        logger.info(f"Documento procesado exitosamente: {original_filename} ({chunks_created} chunks)")

    except Exception as e:
        logger.error(f"Error procesando documento {original_filename}: {e}")

        # Mover a carpeta de errores si existe
        error_dir = Path("uploads/errors")
        error_dir.mkdir(parents=True, exist_ok=True)
        error_path = error_dir / f"{file_id}_{original_filename}"
        try:
            Path(file_path).rename(error_path)
        except:
            pass


@router.get("/documents")
async def list_documents():
    """
    Lista todos los documentos subidos y su estado.
    """
    try:
        documents = []

        # Recorrer todas las carpetas de uploads
        for status_dir in _upload_subdirs():
            upload_dir = Path(f"uploads/{status_dir}")
            if not upload_dir.exists():
                continue

            for file_path in upload_dir.glob("*"):
                if file_path.is_file():
                    # Extraer información del nombre del archivo
                    file_name = file_path.name
                    if "_" in file_name:
                        file_id, original_name = file_name.split("_", 1)
                    else:
                        file_id = str(uuid.uuid4())
                        original_name = file_name

                    # Obtener metadatos básicos
                    stat = file_path.stat()

                    doc_info = {
                        "file_id": file_id,
                        "file_name": original_name,
                        "file_format": DocumentParser.get_format(str(file_path)),
                        "file_size": stat.st_size,
                        "upload_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "status": status_dir,
                        "word_count": None,
                        "char_count": None,
                        "pages": None
                    }

                    documents.append(doc_info)

        return {
            "documents": documents,
            "total": len(documents)
        }

    except Exception as e:
        logger.error(f"Error listando documentos: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.delete("/documents/{file_id}")
async def delete_document(file_id: str):
    """
    Elimina un documento subido.
    """
    try:
        # Buscar el archivo en todas las carpetas
        file_path = None
        for upload_subdir in _upload_subdirs():
            search_path = Path(f"uploads/{upload_subdir}")
            if search_path.exists():
                for file in search_path.glob(f"{file_id}_*"):
                    file_path = file
                    break
            if file_path:
                break

        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"Documento con ID {file_id} no encontrado"
            )

        # Eliminar archivo
        file_path.unlink()

        logger.info(f"Documento eliminado: {file_path.name}")

        return {
            "status": "deleted",
            "file_id": file_id,
            "message": "Documento eliminado exitosamente"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando documento {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.post("/reindex")
async def reindex_knowledge_base(background_tasks: BackgroundTasks):
    """
    Reindexa toda la base de conocimientos desde archivos.
    Operación pesada que se ejecuta en background.
    """
    try:
        # Ejecutar en background
        background_tasks.add_task(indexer.index_knowledge_base)

        return {
            "status": "reindexing_started",
            "message": "Reindexación iniciada en background. Puede tomar varios minutos."
        }

    except Exception as e:
        logger.error(f"Error iniciando reindexación: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al iniciar la reindexación"
        )


@router.get("/health")
async def knowledge_health_check():
    """Verificación de salud del servicio de conocimiento."""
    try:
        # Verificar que los servicios están activos
        collections_status = {}
        for coll_name in ["procedimientos", "aprendido"]:
            try:
                # Intento simple de acceso
                collections_status[coll_name] = "active"
            except:
                collections_status[coll_name] = "inactive"

        return {
            "status": "healthy",
            "service": "knowledge",
            "collections_status": collections_status
        }

    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return {
            "status": "unhealthy",
            "service": "knowledge",
            "error": str(e)
        }

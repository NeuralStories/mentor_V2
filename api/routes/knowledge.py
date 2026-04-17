"""
Rutas de gestión del conocimiento e ingesta documental.
"""
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from core.config import settings
from core.ingestion import IngestionStatus, get_store
from core.memory.learning_pipeline import LearningPipeline
from core.rag.indexer import KnowledgeIndexer
from core.rag.retriever import RAGRetriever
from core.tools.document_parser import DocumentParser

logger = logging.getLogger(__name__)

router = APIRouter()

indexer = KnowledgeIndexer()
retriever = RAGRetriever()
learning = LearningPipeline()

VALID_COLLECTIONS = {
    "procedimientos",
    "materiales",
    "problemas_soluciones",
    "incidencias",
    "aprendido",
}


def _storage_dir_for_format(file_format: str) -> str:
    return "md" if file_format == "markdown" else file_format


def _validate_collection(collection: str) -> None:
    if collection not in VALID_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Colección '{collection}' no válida")


def _validate_size(size_bytes: int) -> None:
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Archivo demasiado grande ({size_bytes / 1_048_576:.1f} MB > "
                f"{settings.MAX_UPLOAD_SIZE_MB} MB)"
            ),
        )


class IndexRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None
    collection: str = "aprendido"


class SearchRequest(BaseModel):
    query: str
    collections: Optional[List[str]] = None
    top_k: int = 5
    min_similarity: Optional[float] = None


class KnowledgeResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    query: str


class UploadResponse(BaseModel):
    file_id: str
    file_name: str
    file_format: str
    file_size: int
    status: str
    message: str
    sha256: Optional[str] = None


class ProcessDocumentRequest(BaseModel):
    collection: str = "procedimientos"


@router.post("/index")
async def index_knowledge(request: IndexRequest):
    _validate_collection(request.collection)
    if request.collection != "aprendido":
        raise HTTPException(
            status_code=400,
            detail="Indexación directa solo disponible para 'aprendido'. Para el resto, usa /upload.",
        )

    try:
        indexer.index_learned_knowledge(
            content=request.content,
            metadata=request.metadata or {},
        )
        return {"status": "indexed", "collection": request.collection}
    except Exception as exc:
        logger.exception("Error indexando conocimiento")
        raise HTTPException(status_code=500, detail=f"Error al indexar: {exc}") from exc


@router.post("/search", response_model=KnowledgeResponse)
async def search_knowledge(request: SearchRequest):
    try:
        results = retriever.search(
            query=request.query,
            collections=request.collections,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
        )
        return KnowledgeResponse(
            results=results,
            total_found=len(results),
            query=request.query,
        )
    except Exception as exc:
        logger.exception("Error en búsqueda")
        raise HTTPException(status_code=500, detail="Error al realizar la búsqueda") from exc


@router.post("/index-incident")
async def index_incident(
    description: str,
    solution: str | None = None,
    category: str = "general",
    metadata: Optional[Dict[str, Any]] = None,
):
    try:
        enriched_metadata = (metadata or {}) | {
            "category": category,
            "indexed_from": "api",
        }
        indexer.index_incident(
            description=description,
            solution=solution,
            metadata=enriched_metadata,
        )
        return {"status": "indexed", "type": "incident"}
    except Exception as exc:
        logger.exception("Error indexando incidencia")
        raise HTTPException(status_code=500, detail="Error al indexar la incidencia") from exc


@router.get("/stats")
async def get_knowledge_stats():
    try:
        store = get_store()
        return {
            "learning_stats": learning.get_learning_stats(),
            "collections": {
                "total_collections": len(VALID_COLLECTIONS),
                "collections": sorted(VALID_COLLECTIONS),
            },
            "ingestion": store.count_by_status(),
            "status": "active",
        }
    except Exception as exc:
        logger.exception("Error obteniendo estadísticas")
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas") from exc


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection: str = Form("procedimientos"),
    auto_process: bool = Form(True),
):
    _validate_collection(collection)

    if not file.filename or not DocumentParser.can_parse(file.filename):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Formato no soportado: {Path(file.filename or '').suffix}. "
                f"Permitidos: {', '.join(DocumentParser.SUPPORTED_FORMATS.keys())}"
            ),
        )

    data = await file.read()
    _validate_size(len(data))

    sha256 = hashlib.sha256(data).hexdigest()
    store = get_store()
    existing = store.find_by_sha(sha256)
    if existing and existing.status == IngestionStatus.READY:
        return UploadResponse(
            file_id=existing.file_id,
            file_name=existing.filename,
            file_format=existing.file_format,
            file_size=existing.size_bytes,
            status="duplicate",
            message="Documento ya indexado (mismo SHA-256)",
            sha256=sha256,
        )

    file_id = sha256[:16]
    file_format = DocumentParser.get_format(file.filename)
    upload_dir = Path(settings.UPLOAD_DIR) / _storage_dir_for_format(file_format)
    upload_dir.mkdir(parents=True, exist_ok=True)
    storage_path = upload_dir / f"{file_id}__{file.filename}"
    storage_path.write_bytes(data)

    from core.ingestion.models import IngestionRecord

    record = IngestionRecord(
        file_id=file_id,
        sha256=sha256,
        filename=file.filename,
        mime=file.content_type or "application/octet-stream",
        file_format=file_format,
        size_bytes=len(data),
        collection=collection,
        storage_path=str(storage_path),
    )
    store.upsert(record)

    if auto_process:
        background_tasks.add_task(process_document_background, file_id)

    return UploadResponse(
        file_id=file_id,
        file_name=file.filename,
        file_format=file_format,
        file_size=len(data),
        status="processing" if auto_process else "uploaded",
        message="Subida OK y procesamiento en curso" if auto_process else "Subida OK",
        sha256=sha256,
    )


@router.post("/process/{file_id}")
async def process_document(
    file_id: str,
    request: ProcessDocumentRequest,
    background_tasks: BackgroundTasks,
):
    _validate_collection(request.collection)
    store = get_store()
    record = store.get(file_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"file_id {file_id} no encontrado")

    if record.collection != request.collection:
        store.transition(file_id, record.status, collection=request.collection)

    background_tasks.add_task(process_document_background, file_id)
    return {
        "status": "processing_started",
        "file_id": file_id,
        "collection": request.collection,
    }


def process_document_background(file_id: str) -> None:
    store = get_store()
    record = store.get(file_id)
    if not record:
        logger.error("No existe registro de ingestión para %s", file_id)
        return

    if not record.storage_path or not Path(record.storage_path).exists():
        store.transition(file_id, IngestionStatus.FAILED, error="Fichero físico no encontrado")
        return

    try:
        store.transition(file_id, IngestionStatus.PARSING)
        content, metadata = DocumentParser.parse_file(record.storage_path)

        if metadata.get("ocr_used"):
            store.transition(
                file_id,
                IngestionStatus.OCR,
                ocr_used=True,
                ocr_pages=metadata.get("ocr_pages"),
            )

        store.transition(
            file_id,
            IngestionStatus.CHUNKING,
            pages=metadata.get("pages"),
            word_count=metadata.get("word_count"),
            char_count=metadata.get("char_count"),
            parser=metadata.get("parser") or record.file_format,
        )

        if not content.strip():
            raise ValueError("Documento sin contenido extraíble")

        store.transition(file_id, IngestionStatus.INDEXING)
        chunks_created = indexer.index_text_content(
            content=content,
            collection=record.collection,
            metadata={
                "source": "uploaded_document",
                "file_id": file_id,
                "sha256": record.sha256,
                "original_filename": record.filename,
                "file_format": record.file_format,
                "pages": metadata.get("pages"),
                "ocr_used": metadata.get("ocr_used", False),
                "word_count": metadata.get("word_count", 0),
                "char_count": metadata.get("char_count", 0),
            },
            source_name=record.filename,
        )
        store.transition(file_id, IngestionStatus.READY, chunks=chunks_created)
    except Exception as exc:
        logger.exception("Fallo en ingesta %s", file_id)
        store.transition(file_id, IngestionStatus.FAILED, error=str(exc)[:500])


@router.get("/documents")
async def list_documents(
    status: IngestionStatus | None = None,
    collection: str | None = None,
):
    if collection:
        _validate_collection(collection)

    records = get_store().list(status=status, collection=collection)
    return {
        "documents": [record.model_dump(mode="json") for record in records],
        "total": len(records),
    }


@router.get("/documents/{file_id}/status")
async def document_status(file_id: str):
    record = get_store().get(file_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"file_id {file_id} no encontrado")
    return record.model_dump(mode="json")


@router.delete("/documents/{file_id}")
async def delete_document(file_id: str):
    store = get_store()
    record = store.get(file_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"file_id {file_id} no encontrado")

    if record.storage_path:
        Path(record.storage_path).unlink(missing_ok=True)

    store.delete(file_id)
    return {"status": "deleted", "file_id": file_id}


@router.post("/reindex")
async def reindex_knowledge_base(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(indexer.index_knowledge_base)
        return {"status": "reindexing_started"}
    except Exception as exc:
        logger.exception("Error iniciando reindexación")
        raise HTTPException(status_code=500, detail="Error al iniciar la reindexación") from exc


@router.get("/health")
async def knowledge_health_check():
    try:
        return {
            "status": "healthy",
            "service": "knowledge",
            "ingestion_counts": get_store().count_by_status(),
            "supabase": "enabled" if settings.supabase_enabled else "degraded",
        }
    except Exception as exc:
        logger.exception("Error en health check")
        return {
            "status": "unhealthy",
            "service": "knowledge",
            "error": str(exc),
        }

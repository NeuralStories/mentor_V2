"""Endpoints principales de la API de MENTOR."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.engine import MentorEngine
from src.core.worker_context import WorkerProfile
from src.db.database import get_db
from src.api.schemas import (
    WorkerRegistration, QueryRequest, QueryResponse,
    FeedbackRequest, FeedbackResponse, TicketListResponse,
    TicketResponse,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["mentor-enterprise"])

_engine: Optional[MentorEngine] = None


def get_engine() -> MentorEngine:
    """Factory del motor MENTOR con carga de KB."""
    global _engine
    if _engine is None:
        _engine = MentorEngine()
        try:
            count = _engine.kb.load_from_json("data/knowledge_base.json")
            logger.info(f"Loaded {count} KB documents")
        except FileNotFoundError:
            logger.warning("No KB file found at data/knowledge_base.json")
    return _engine


# ---- Worker Management ----

@router.post("/workers/register")
async def register_worker(
    data: WorkerRegistration,
    engine: MentorEngine = Depends(get_engine),
    db: AsyncSession = Depends(get_db)
):
    """Registra un nuevo trabajador en el sistema."""
    profile = WorkerProfile(
        worker_id=data.worker_id, name=data.name, department=data.department,
        role=data.role, location=data.location, hire_date=data.hire_date, manager=data.manager,
    )
    await engine.register_worker(profile, db_session=db)
    return {"status": "registered", "worker_id": data.worker_id}


# ---- Query Processing ----

@router.post("/query", response_model=QueryResponse)
async def handle_query(
    request: QueryRequest,
    engine: MentorEngine = Depends(get_engine),
    db: AsyncSession = Depends(get_db)
):
    """Procesa una consulta de un trabajador a través del pipeline completo."""
    try:
        response = await engine.handle_query(
            message=request.message, worker_id=request.worker_id,
            session_id=request.session_id, db_session=db,
        )
        return QueryResponse(
            content=response.content, session_id=response.session_id,
            strategy_used=response.strategy_used, category=response.category,
            urgency=response.urgency, sources_used=response.sources_used,
            was_escalated=response.was_escalated, escalation_ticket=response.escalation_ticket,
            suggested_actions=response.suggested_actions, collect_feedback=response.collect_feedback,
            latency_ms=response.latency_ms, metadata=response.metadata,
        )
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---- Feedback ----

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    engine: MentorEngine = Depends(get_engine),
    db: AsyncSession = Depends(get_db)
):
    """Registra feedback de satisfacción del trabajador."""
    result = await engine.handle_feedback(
        session_id=request.session_id, worker_id=request.worker_id,
        score=request.score, comment=request.comment, db_session=db,
    )
    return FeedbackResponse(**result)


# ---- Analytics ----

@router.get("/analytics")
async def get_analytics(engine: MentorEngine = Depends(get_engine)):
    """Obtiene analíticas generales del agente."""
    return await engine.get_analytics()


# ---- Tickets ----

@router.get("/tickets/open", response_model=TicketListResponse)
async def get_open_tickets(
    worker_id: Optional[str] = None,
    engine: MentorEngine = Depends(get_engine),
    db: AsyncSession = Depends(get_db)
):
    """Lista tickets de escalamiento abiertos."""
    from src.db.repositories import TicketRepository
    repo = TicketRepository(db)
    tickets = await repo.get_open(worker_id)
    return TicketListResponse(
        count=len(tickets),
        tickets=[
            TicketResponse(
                ticket_id=t.ticket_id, category=t.category, urgency=t.urgency,
                status=t.status, assigned_to=t.assigned_to, created_at=t.created_at.isoformat() if hasattr(t.created_at, "isoformat") else str(t.created_at),
            )
            for t in tickets
        ],
    )


# ---- Knowledge Base ----

@router.get("/kb/stats")
async def get_kb_stats(engine: MentorEngine = Depends(get_engine)):
    """Obtiene estadísticas de la base de conocimiento."""
    return engine.kb.get_stats()


# ---- Cache ----

@router.get("/cache/stats")
async def get_cache_stats(engine: MentorEngine = Depends(get_engine)):
    """Obtiene estadísticas del caché de respuestas."""
    return engine.cache.get_stats()


@router.delete("/cache")
async def clear_cache(category: Optional[str] = None, engine: MentorEngine = Depends(get_engine)):
    """Limpia el caché de respuestas, opcionalmente por categoría."""
    count = await engine.cache.invalidate(category=category)
    return {"cleared": count, "category": category}


# ---- Session ----

@router.delete("/session/{session_id}")
async def clear_session(session_id: str, engine: MentorEngine = Depends(get_engine)):
    """Limpia el historial de una sesión de conversación."""
    await engine.memory.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


# ---- Ticket Resolution ----

@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    resolution_notes: str = "Resuelto",
    engine: MentorEngine = Depends(get_engine),
    db: AsyncSession = Depends(get_db)
):
    """Marca un ticket de escalamiento como resuelto."""
    from src.db.repositories import TicketRepository
    engine.escalation._repo = TicketRepository(db)
    result = await engine.escalation.resolve_ticket(ticket_id, resolution_notes)
    if not result:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} no encontrado")
    return {"status": "resolved", "ticket_id": ticket_id}


# ---- Worker Bulk Load ----

@router.post("/workers/load")
async def load_workers_from_json(
    engine: MentorEngine = Depends(get_engine),
    db: AsyncSession = Depends(get_db)
):
    """Carga trabajadores de ejemplo desde data/sample_workers.json."""
    import json
    try:
        with open("data/sample_workers.json", "r", encoding="utf-8") as f:
            workers_data = json.load(f)
        count = 0
        for w in workers_data:
            profile = WorkerProfile(
                worker_id=w["worker_id"], name=w.get("name", ""),
                department=w.get("department", ""), role=w.get("role", ""),
                location=w.get("location", ""), hire_date=w.get("hire_date"),
                manager=w.get("manager", ""),
            )
            await engine.register_worker(profile, db_session=db)
            count += 1
        return {"status": "loaded", "workers_loaded": count}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="data/sample_workers.json not found")


# ---- Document Ingestion ----

@router.post("/kb/ingest")
async def ingest_documents(directory: str = "docs/ingestion/", engine: MentorEngine = Depends(get_engine)):
    """Ingesta documentos desde un directorio usando DocumentIngestionService."""
    from src.services.document_ingestion import DocumentIngestionService
    service = DocumentIngestionService()
    result = await service.ingest_directory(directory)
    return result


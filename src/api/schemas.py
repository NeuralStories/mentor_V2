"""Schemas Pydantic para la API de MENTOR."""

from pydantic import BaseModel, Field
from typing import Optional


class WorkerRegistration(BaseModel):
    """Schema para registrar un trabajador."""
    worker_id: str = Field(..., description="Identificador único del trabajador")
    name: str = Field("", description="Nombre completo")
    department: str = Field("", description="Departamento")
    role: str = Field("", description="Rol o puesto")
    location: str = Field("", description="Ubicación (oficina, planta, sede)")
    hire_date: Optional[str] = Field(None, description="Fecha de contratación ISO")
    manager: str = Field("", description="Nombre del supervisor directo")


class QueryRequest(BaseModel):
    """Schema para enviar una consulta al agente."""
    message: str = Field(..., min_length=1, max_length=5000, description="Mensaje del trabajador")
    worker_id: str = Field(..., description="ID del trabajador que consulta")
    session_id: Optional[str] = Field(None, description="ID de sesión para continuidad")


class QueryResponse(BaseModel):
    """Schema de respuesta del agente."""
    content: str
    session_id: str
    strategy_used: str
    category: str
    urgency: str
    sources_used: list[str]
    was_escalated: bool
    escalation_ticket: Optional[str] = None
    suggested_actions: list[str]
    collect_feedback: bool
    latency_ms: float
    metadata: dict


class FeedbackRequest(BaseModel):
    """Schema para enviar feedback de satisfacción."""
    session_id: str
    worker_id: str
    score: int = Field(..., ge=1, le=5, description="Puntuación de 1 a 5")
    comment: Optional[str] = Field(None, description="Comentario opcional")


class FeedbackResponse(BaseModel):
    """Schema de respuesta al feedback."""
    session_id: str
    worker_id: str
    score: int
    comment: Optional[str] = None
    avg_satisfaction: float


class TicketResponse(BaseModel):
    """Schema para un ticket de escalamiento."""
    ticket_id: str
    category: str
    urgency: str
    status: str
    assigned_to: str
    created_at: str


class TicketListResponse(BaseModel):
    """Schema para lista de tickets."""
    count: int
    tickets: list[TicketResponse]


class CacheStatsResponse(BaseModel):
    """Schema para estadísticas de caché."""
    backend: str
    total_entries: int
    hit_rate: float


class HealthResponse(BaseModel):
    """Schema para health check."""
    status: str
    version: str
    environment: str

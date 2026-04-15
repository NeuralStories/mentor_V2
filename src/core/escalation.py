"""Sistema de escalamiento con notificaciones a Slack/Teams/Webhooks."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import uuid

from src.core.query_classifier import ClassifiedQuery
from src.core.worker_context import WorkerProfile
from src.db.repositories import TicketRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EscalationTicket:
    """Ticket de escalamiento a un equipo humano."""
    ticket_id: str
    worker_id: str
    worker_name: str
    department: str
    category: str
    urgency: str
    reason: str
    original_message: str
    conversation_summary: str
    assigned_to: str = ""
    status: str = "open"
    created_at: str = ""
    resolved_at: Optional[str] = None
    resolution_notes: str = ""


class EscalationManager:
    """Gestiona tickets de escalamiento a equipos humanos con notificaciones."""

    # Mapa de escalamiento: categoría → equipo responsable + canal
    ESCALATION_MAP = {
        "hr": {
            "team": "RRHH",
            "email": "rrhh@empresa.com",
            "channel": "#rrhh-soporte",
            "sla_hours": 24,
        },
        "it_support": {
            "team": "Mesa de Ayuda IT",
            "email": "helpdesk@empresa.com",
            "channel": "#it-soporte",
            "sla_hours": 4,
        },
        "safety": {
            "team": "Seguridad e Higiene",
            "email": "seguridad@empresa.com",
            "channel": "#seguridad-urgente",
            "sla_hours": 1,
        },
        "compliance": {
            "team": "Legal y Compliance",
            "email": "legal@empresa.com",
            "channel": "#legal-privado",
            "sla_hours": 48,
        },
        "finance": {
            "team": "Finanzas",
            "email": "finanzas@empresa.com",
            "channel": "#finanzas-soporte",
            "sla_hours": 24,
        },
    }

    DEFAULT_ESCALATION = {
        "team": "Soporte General",
        "email": "soporte@empresa.com",
        "channel": "#soporte-general",
        "sla_hours": 24,
    }

    def __init__(self, slack=None, teams=None, webhook=None, ticket_repo: Optional[TicketRepository] = None):
        self._tickets: dict[str, EscalationTicket] = {}
        self._stats = {
            "total_created": 0,
            "total_resolved": 0,
            "by_category": {},
            "by_urgency": {},
        }
        # Integraciones opcionales
        self._slack = slack
        self._teams = teams
        self._webhook = webhook
        self._repo = ticket_repo

    async def create_ticket(
        self,
        worker: WorkerProfile,
        query: ClassifiedQuery,
        conversation_history: list[dict],
        original_message: str,
    ) -> str:
        """Crea un ticket de escalamiento y notifica al equipo correspondiente."""
        ticket_id = f"ESC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        conv_summary = self._summarize_conversation(conversation_history)

        escalation_info = self.ESCALATION_MAP.get(
            query.category.value, self.DEFAULT_ESCALATION
        )

        ticket = EscalationTicket(
            ticket_id=ticket_id,
            worker_id=worker.worker_id,
            worker_name=worker.name or worker.worker_id,
            department=worker.department,
            category=query.category.value,
            urgency=query.urgency.value,
            reason=query.escalation_reason,
            original_message=original_message,
            conversation_summary=conv_summary,
            assigned_to=escalation_info["team"],
            created_at=datetime.utcnow().isoformat(),
        )

        self._tickets[ticket_id] = ticket

        # Persistencia en DB si el repo está disponible
        if self._repo:
            try:
                await self._repo.save(ticket)
            except Exception as e:
                logger.error(f"Failed to persist ticket {ticket_id}: {e}")

        # Estadísticas
        self._stats["total_created"] += 1
        cat = query.category.value
        self._stats["by_category"][cat] = self._stats["by_category"].get(cat, 0) + 1
        urg = query.urgency.value
        self._stats["by_urgency"][urg] = self._stats["by_urgency"].get(urg, 0) + 1

        # Registrar en el perfil del trabajador
        worker.unresolved_tickets.append(ticket_id)

        # Notificar al equipo por todos los canales configurados
        await self._notify_team(ticket, escalation_info)

        logger.info(
            f"Escalation ticket created: {ticket_id} -> "
            f"{escalation_info['team']} (SLA: {escalation_info['sla_hours']}h)"
        )
        return ticket_id

    async def resolve_ticket(self, ticket_id: str, resolution_notes: str) -> bool:
        """Marca un ticket como resuelto."""
        found = False
        
        # Primero intentar en memoria
        if ticket_id in self._tickets:
            ticket = self._tickets[ticket_id]
            ticket.status = "resolved"
            ticket.resolved_at = datetime.utcnow().isoformat()
            ticket.resolution_notes = resolution_notes
            self._stats["total_resolved"] += 1
            found = True

        # Luego intentar en DB (o solo en DB si no está en memoria)
        if self._repo:
            db_result = await self._repo.resolve(ticket_id, resolution_notes)
            if db_result:
                found = True
                if ticket_id not in self._tickets:
                    self._stats["total_resolved"] += 1

        if found:
            logger.info(f"Ticket resolved: {ticket_id}")
        return found

    async def _notify_team(self, ticket: EscalationTicket, team_info: dict):
        """Notifica al equipo responsable por Slack, Teams y/o Webhook."""
        urgency_emoji = {
            "low": "[INFO]", "medium": "[MEDIUM]",
            "high": "[HIGH]", "critical": "[CRITICAL]",
        }
        emoji = urgency_emoji.get(ticket.urgency, "[INFO]")

        notification_text = (
            f"{emoji} Nuevo ticket de escalamiento\n"
            f"Ticket: {ticket.ticket_id}\n"
            f"Trabajador: {ticket.worker_name} ({ticket.department})\n"
            f"Categoria: {ticket.category}\n"
            f"Urgencia: {ticket.urgency}\n"
            f"Razon: {ticket.reason}\n"
            f"Asignado a: {team_info['team']}\n"
            f"SLA: {team_info['sla_hours']} horas"
        )

        # 1. Notificar por Slack
        if self._slack:
            channel = team_info.get("channel", "#soporte-general")
            try:
                await self._slack.send_message(channel=channel, message=notification_text)
                logger.info(f"Slack notification sent to {channel} for {ticket.ticket_id}")
            except Exception as e:
                logger.error(f"Slack notification failed for {ticket.ticket_id}: {e}")

        # 2. Notificar por Teams
        if self._teams:
            try:
                await self._teams.send_adaptive_card(
                    title=f"{emoji} Escalamiento: {ticket.ticket_id}",
                    text=notification_text,
                )
                logger.info(f"Teams notification sent for {ticket.ticket_id}")
            except Exception as e:
                logger.error(f"Teams notification failed for {ticket.ticket_id}: {e}")

        # 3. Notificar por Webhook genérico
        if self._webhook:
            webhook_payload = {
                "event": "escalation_created",
                "ticket_id": ticket.ticket_id,
                "worker_id": ticket.worker_id,
                "worker_name": ticket.worker_name,
                "department": ticket.department,
                "category": ticket.category,
                "urgency": ticket.urgency,
                "reason": ticket.reason,
                "assigned_to": ticket.assigned_to,
                "sla_hours": team_info["sla_hours"],
                "created_at": ticket.created_at,
            }
            try:
                # El webhook URL vendría de configuración
                from src.utils.config import get_settings
                settings = get_settings()
                webhook_url = getattr(settings, "escalation_webhook_url", None)
                if webhook_url:
                    await self._webhook.trigger(url=webhook_url, payload=webhook_payload)
                    logger.info(f"Webhook notification sent for {ticket.ticket_id}")
            except Exception as e:
                logger.error(f"Webhook notification failed for {ticket.ticket_id}: {e}")

        # Siempre logueamos aunque no haya integraciones configuradas
        if not any([self._slack, self._teams, self._webhook]):
            logger.info(
                f"[NOTIFICATION MOCK] Ticket {ticket.ticket_id} -> "
                f"{team_info['team']} ({team_info['email']})"
            )

    def get_open_tickets(self, worker_id: Optional[str] = None) -> list[EscalationTicket]:
        """Lista tickets abiertos, opcionalmente filtrados por trabajador."""
        tickets = [t for t in self._tickets.values() if t.status in ("open", "in_progress")]
        if worker_id:
            tickets = [t for t in tickets if t.worker_id == worker_id]
        return tickets

    def get_stats(self) -> dict:
        """Retorna estadísticas del sistema de escalamiento."""
        open_count = sum(1 for t in self._tickets.values() if t.status in ("open", "in_progress"))
        return {**self._stats, "currently_open": open_count}

    def _summarize_conversation(self, history: list[dict]) -> str:
        """Resume el historial de conversación para incluir en el ticket."""
        if not history:
            return "Sin conversacion previa."
        parts = []
        for msg in history[-10:]:
            role = "Trabajador" if msg["role"] == "user" else "Agente"
            parts.append(f"{role}: {msg['content'][:300]}")
        return "\n".join(parts)

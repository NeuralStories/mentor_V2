import pytest
from src.core.escalation import EscalationManager
from src.core.query_classifier import ClassifiedQuery, QueryCategory, QueryUrgency


class TestEscalationManager:
    @pytest.fixture
    def escalation(self):
        return EscalationManager()

    @pytest.fixture
    def critical_query(self):
        return ClassifiedQuery(
            category=QueryCategory.HR, urgency=QueryUrgency.CRITICAL,
            requires_escalation=True, escalation_reason="Reporte de acoso", raw_message="Quiero reportar acoso",
        )

    @pytest.mark.asyncio
    async def test_create_ticket(self, escalation, sample_worker, critical_query):
        ticket_id = await escalation.create_ticket(worker=sample_worker, query=critical_query, conversation_history=[], original_message="test")
        assert ticket_id.startswith("ESC-")
        assert len(escalation._tickets) == 1

    @pytest.mark.asyncio
    async def test_ticket_assignment(self, escalation, sample_worker, critical_query):
        ticket_id = await escalation.create_ticket(worker=sample_worker, query=critical_query, conversation_history=[], original_message="test")
        ticket = escalation._tickets[ticket_id]
        assert ticket.assigned_to == "RRHH"
        assert ticket.status == "open"

    @pytest.mark.asyncio
    async def test_resolve_ticket(self, escalation, sample_worker, critical_query):
        ticket_id = await escalation.create_ticket(worker=sample_worker, query=critical_query, conversation_history=[], original_message="test")
        result = await escalation.resolve_ticket(ticket_id, "Caso atendido")
        assert result is True
        assert escalation._tickets[ticket_id].status == "resolved"

    @pytest.mark.asyncio
    async def test_get_open_tickets(self, escalation, sample_worker, critical_query):
        await escalation.create_ticket(worker=sample_worker, query=critical_query, conversation_history=[], original_message="test")
        assert len(escalation.get_open_tickets()) == 1
        assert len(escalation.get_open_tickets(sample_worker.worker_id)) == 1

    def test_stats(self, escalation):
        stats = escalation.get_stats()
        assert "total_created" in stats
        assert "currently_open" in stats

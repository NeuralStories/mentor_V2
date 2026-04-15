import pytest
from src.core.engine import MentorEngine


class TestMentorEngine:
    @pytest.mark.asyncio
    async def test_handle_basic_query(self, engine, sample_worker):
        await engine.register_worker(sample_worker)
        response = await engine.handle_query(message="¿Cuántos días de vacaciones tengo?", worker_id=sample_worker.worker_id)
        assert response.content != ""
        assert response.session_id != ""
        assert response.category != ""
        assert response.latency_ms > 0

    @pytest.mark.asyncio
    async def test_query_count_increments(self, engine, sample_worker):
        await engine.register_worker(sample_worker)
        await engine.handle_query(message="pregunta 1", worker_id=sample_worker.worker_id)
        await engine.handle_query(message="pregunta 2", worker_id=sample_worker.worker_id)
        worker = await engine._get_worker(sample_worker.worker_id)
        assert worker.total_queries == 2

    @pytest.mark.asyncio
    async def test_session_continuity(self, engine, sample_worker):
        await engine.register_worker(sample_worker)
        r1 = await engine.handle_query(message="pregunta 1", worker_id=sample_worker.worker_id, session_id="sess-123")
        r2 = await engine.handle_query(message="pregunta 2", worker_id=sample_worker.worker_id, session_id="sess-123")
        assert r1.session_id == r2.session_id == "sess-123"
        history = await engine.memory.get_history("sess-123")
        assert len(history) >= 4

    @pytest.mark.asyncio
    async def test_feedback(self, engine, sample_worker):
        await engine.register_worker(sample_worker)
        result = await engine.handle_feedback(session_id="sess-123", worker_id=sample_worker.worker_id, score=5, comment="Muy útil")
        assert result["score"] == 5
        worker = await engine._get_worker(sample_worker.worker_id)
        assert worker.avg_satisfaction == 5.0

    @pytest.mark.asyncio
    async def test_analytics(self, engine, sample_worker):
        await engine.register_worker(sample_worker)
        await engine.handle_query(message="test", worker_id=sample_worker.worker_id)
        analytics = await engine.get_analytics()
        assert analytics["total_workers_served"] >= 1
        assert analytics["total_queries"] >= 1

    @pytest.mark.asyncio
    async def test_unregistered_worker(self, engine):
        response = await engine.handle_query(message="hola", worker_id="unknown-worker")
        assert response.content != ""
        worker = await engine._get_worker("unknown-worker")
        assert worker is not None

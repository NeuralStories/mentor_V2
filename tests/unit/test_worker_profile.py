import pytest
from src.core.worker_context import WorkerProfile


class TestWorkerProfile:
    def test_new_employee(self, new_employee):
        assert new_employee.is_new_employee is True

    def test_senior_employee(self, sample_worker):
        assert sample_worker.is_new_employee is False

    def test_record_query(self, sample_worker):
        sample_worker.record_query("hr")
        sample_worker.record_query("hr")
        sample_worker.record_query("it_support")
        assert sample_worker.total_queries == 3
        assert sample_worker.queries_by_category["hr"] == 2

    def test_satisfaction(self, sample_worker):
        sample_worker.record_satisfaction(5)
        sample_worker.record_satisfaction(4)
        sample_worker.record_satisfaction(3)
        assert sample_worker.avg_satisfaction == 4.0

    def test_satisfaction_clamping(self, sample_worker):
        sample_worker.record_satisfaction(0)
        sample_worker.record_satisfaction(10)
        assert sample_worker.satisfaction_scores == [1, 5]

    def test_context_summary(self, sample_worker):
        summary = sample_worker.get_context_summary()
        assert "Juan Pérez" in summary
        assert "ventas" in summary

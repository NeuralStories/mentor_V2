"""Tests de integración para la API de MENTOR."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_check(self):
        from src.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data


class TestWorkerEndpoints:
    @pytest.mark.asyncio
    async def test_register_worker(self, client: AsyncClient):
        response = await client.post("/api/v1/workers/register", json={
            "worker_id": "test-api-001",
            "name": "Test Worker",
            "department": "ti",
            "role": "developer",
            "location": "Remote",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "registered"
        assert data["worker_id"] == "test-api-001"


class TestAnalyticsEndpoints:
    @pytest.mark.asyncio
    async def test_get_analytics(self, client: AsyncClient):
        response = await client.get("/api/v1/analytics")
        assert response.status_code == 200
        data = response.json()
        assert "total_workers_served" in data
        assert "total_queries" in data

    @pytest.mark.asyncio
    async def test_get_kb_stats(self, client: AsyncClient):
        response = await client.get("/api/v1/kb/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, client: AsyncClient):
        response = await client.get("/api/v1/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "backend" in data

    @pytest.mark.asyncio
    async def test_get_open_tickets(self, client: AsyncClient):
        response = await client.get("/api/v1/tickets/open")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "tickets" in data


class TestSessionManagement:
    def test_clear_session(self):
        from src.main import app
        client = TestClient(app)
        response = client.delete("/api/v1/session/test-session-123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cleared"

    def test_clear_cache(self):
        from src.main import app
        client = TestClient(app)
        response = client.delete("/api/v1/cache")
        assert response.status_code == 200
        data = response.json()
        assert "cleared" in data


class TestMetricsEndpoint:
    def test_metrics(self):
        from src.main import app
        client = TestClient(app)
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")

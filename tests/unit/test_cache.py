import pytest
from src.services.cache_service import CacheService


class TestCacheService:
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        await cache.set(query="¿Cuántos días de vacaciones?", category="hr", response_content="8 días según política.", sources=["Política de Vacaciones"])
        result = await cache.get(query="¿Cuántos días de vacaciones?", category="hr")
        assert result is not None
        assert "8 días" in result["content"]
        assert result["cache_hit"] is True

    @pytest.mark.asyncio
    async def test_normalized_match(self, cache):
        await cache.set(query="¿Cuántos días de vacaciones tengo?", category="hr", response_content="8 días")
        result = await cache.get(query="cuantos dias vacaciones tengo", category="hr")
        assert result is not None

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        result = await cache.get(query="pregunta que no existe", category="hr")
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_category(self, cache):
        await cache.set("q1", "hr", "r1")
        await cache.set("q2", "it", "r2")
        count = await cache.invalidate(category="hr")
        assert count == 1
        assert await cache.get("q1", "hr") is None
        assert await cache.get("q2", "it") is not None

    @pytest.mark.asyncio
    async def test_invalidate_all(self, cache):
        await cache.set("q1", "hr", "r1")
        await cache.set("q2", "it", "r2")
        count = await cache.invalidate()
        assert count == 2

    def test_stats(self, cache):
        stats = cache.get_stats()
        assert "backend" in stats
        assert "hit_rate" in stats

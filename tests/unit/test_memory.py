import pytest
from src.core.memory import ConversationMemory


class TestConversationMemory:
    @pytest.mark.asyncio
    async def test_add_and_retrieve(self, memory):
        await memory.add_message("sess-1", "user", "Hola")
        await memory.add_message("sess-1", "assistant", "¡Hola!")
        history = await memory.get_history("sess-1")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_max_messages(self):
        mem = ConversationMemory(max_messages=3)
        for i in range(10):
            await mem.add_message("sess", "user", f"msg {i}")
        history = await mem.get_history("sess")
        assert len(history) == 3
        assert history[0]["content"] == "msg 7"

    @pytest.mark.asyncio
    async def test_clear_session(self, memory):
        await memory.add_message("sess-1", "user", "Hola")
        await memory.clear_session("sess-1")
        history = await memory.get_history("sess-1")
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_separate_sessions(self, memory):
        await memory.add_message("sess-1", "user", "Hola 1")
        await memory.add_message("sess-2", "user", "Hola 2")
        h1 = await memory.get_history("sess-1")
        h2 = await memory.get_history("sess-2")
        assert len(h1) == 1
        assert len(h2) == 1
        assert h1[0]["content"] == "Hola 1"

    @pytest.mark.asyncio
    async def test_session_summary(self, memory):
        await memory.add_message("sess-1", "user", "msg")
        summary = await memory.get_session_summary("sess-1")
        assert summary["message_count"] == 1

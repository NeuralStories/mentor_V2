from collections import defaultdict
from typing import Optional
from datetime import datetime
import json

from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ConversationMemory:
    def __init__(self, max_messages: int = 50, use_redis: bool = False):
        self.max_messages = max_messages
        self.use_redis = use_redis
        self._local_store: dict[str, list[dict]] = defaultdict(list)
        self._redis_client = None
        if use_redis:
            self._init_redis()

    def _init_redis(self):
        try:
            import redis.asyncio as redis
            self._redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            logger.info("Redis memory backend initialized")
        except Exception as e:
            logger.warning(f"Redis unavailable, falling back to local: {e}")
            self.use_redis = False

    async def add_message(self, session_id: str, role: str, content: str, metadata: Optional[dict] = None) -> None:
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        if self.use_redis and self._redis_client:
            key = f"mentor:session:{session_id}"
            await self._redis_client.rpush(key, json.dumps(message))
            await self._redis_client.ltrim(key, -self.max_messages, -1)
            await self._redis_client.expire(key, settings.cache_ttl)
        else:
            self._local_store[session_id].append(message)
            if len(self._local_store[session_id]) > self.max_messages:
                self._local_store[session_id] = self._local_store[session_id][-self.max_messages:]

    async def get_history(self, session_id: str, limit: Optional[int] = None) -> list[dict]:
        limit = limit or self.max_messages
        if self.use_redis and self._redis_client:
            key = f"mentor:session:{session_id}"
            raw_messages = await self._redis_client.lrange(key, -limit, -1)
            messages = [json.loads(m) for m in raw_messages]
        else:
            messages = self._local_store.get(session_id, [])[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    async def clear_session(self, session_id: str) -> None:
        if self.use_redis and self._redis_client:
            await self._redis_client.delete(f"mentor:session:{session_id}")
        else:
            self._local_store.pop(session_id, None)

    async def get_session_summary(self, session_id: str) -> dict:
        if self.use_redis and self._redis_client:
            count = await self._redis_client.llen(f"mentor:session:{session_id}")
        else:
            count = len(self._local_store.get(session_id, []))
        return {"session_id": session_id, "message_count": count, "max_messages": self.max_messages}

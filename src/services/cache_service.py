from typing import Optional
from datetime import datetime
import hashlib
import json

from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class CacheService:
    def __init__(self, use_redis: bool = False, max_local_entries: int = 500, default_ttl: int = 3600):
        self.use_redis = use_redis
        self.max_entries = max_local_entries
        self.default_ttl = default_ttl
        self._local_cache: dict[str, dict] = {}
        self._hit_count = 0
        self._miss_count = 0
        self._redis_client = None
        if use_redis:
            self._init_redis()

    def _init_redis(self):
        try:
            import redis
            self._redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            self._redis_client.ping()
            logger.info("Cache: Redis backend connected")
        except Exception as e:
            logger.warning(f"Cache: Redis unavailable, using local: {e}")
            self.use_redis = False

    def _normalize_query(self, query: str) -> str:
        import re
        import unicodedata
        normalized = query.lower().strip()
        normalized = ''.join(c for c in unicodedata.normalize('NFD', normalized) if unicodedata.category(c) != 'Mn')
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = " ".join(normalized.split())
        stop_words = {"el", "la", "los", "las", "un", "una", "de", "del", "en", "por", "para", "con", "que", "me", "mi", "yo", "hola", "buenas", "por favor", "gracias", "disculpa"}
        words = normalized.split()
        words = [w for w in words if w not in stop_words]
        return " ".join(words)

    def _generate_key(self, query: str, category: str = "") -> str:
        normalized = self._normalize_query(query)
        raw = f"{category}:{normalized}"
        return hashlib.md5(raw.encode()).hexdigest()

    async def get(self, query: str, category: str = "") -> Optional[dict]:
        key = self._generate_key(query, category)
        if self.use_redis and self._redis_client:
            cached = self._redis_client.get(f"mentor:cache:{key}")
            if cached:
                self._hit_count += 1
                data = json.loads(cached)
                data["cache_hit"] = True
                return data
        else:
            if key in self._local_cache:
                entry = self._local_cache[key]
                created = datetime.fromisoformat(entry["cached_at"])
                elapsed = (datetime.utcnow() - created).seconds
                if elapsed < self.default_ttl:
                    self._hit_count += 1
                    entry["cache_hit"] = True
                    return entry
                else:
                    del self._local_cache[key]
        self._miss_count += 1
        return None

    async def set(self, query: str, category: str, response_content: str, sources: list[str] = None, strategy: str = "", ttl: int = None) -> None:
        key = self._generate_key(query, category)
        ttl = ttl or self.default_ttl
        data = {
            "content": response_content,
            "sources": sources or [],
            "strategy": strategy,
            "category": category,
            "cached_at": datetime.utcnow().isoformat(),
            "original_query": query,
        }
        if self.use_redis and self._redis_client:
            self._redis_client.setex(f"mentor:cache:{key}", ttl, json.dumps(data))
        else:
            if len(self._local_cache) >= self.max_entries:
                self._evict_oldest()
            self._local_cache[key] = data

    def _evict_oldest(self) -> None:
        if not self._local_cache:
            return
        entries = sorted(self._local_cache.items(), key=lambda x: x[1].get("cached_at", ""))
        to_remove = max(1, len(entries) // 5)
        for key, _ in entries[:to_remove]:
            del self._local_cache[key]

    async def invalidate(self, category: Optional[str] = None) -> int:
        count = 0
        if self.use_redis and self._redis_client:
            keys = self._redis_client.keys("mentor:cache:*")
            if category:
                for key in keys:
                    data = self._redis_client.get(key)
                    if data:
                        parsed = json.loads(data)
                        if parsed.get("category") == category:
                            self._redis_client.delete(key)
                            count += 1
            else:
                count = len(keys)
                if keys:
                    self._redis_client.delete(*keys)
        else:
            if category:
                to_delete = [k for k, v in self._local_cache.items() if v.get("category") == category]
                for k in to_delete:
                    del self._local_cache[k]
                count = len(to_delete)
            else:
                count = len(self._local_cache)
                self._local_cache.clear()
        return count

    def get_stats(self) -> dict:
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0
        size = len(self._local_cache)
        return {
            "backend": "redis" if self.use_redis else "local",
            "entries": size,
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": f"{hit_rate:.1f}%",
            "default_ttl_seconds": self.default_ttl,
        }

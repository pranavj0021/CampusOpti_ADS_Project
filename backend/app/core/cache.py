import json
import time
from typing import Any, Optional
import redis
from app.core.config import settings

class MemoryCache:
    def __init__(self):
        self._store = {}
        self._expiry = {}

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        if key in self._store:
            if key in self._expiry and self._expiry[key] < now:
                del self._store[key]
                del self._expiry[key]
                return None
            return self._store[key]
        return None

    def set(self, key: str, value: Any, ex: int = 3600):
        self._store[key] = value
        self._expiry[key] = time.time() + ex

    def delete(self, key: str):
        self._store.pop(key, None)
        self._expiry.pop(key, None)

    def clear(self):
        self._store.clear()
        self._expiry.clear()

class CacheManager:
    def __init__(self):
        self.redis_client = None
        self.memory_cache = MemoryCache()
        self.use_redis = False
        self._init_redis()

    def _init_redis(self):
        try:
            client = redis.from_url(settings.REDIS_URL, socket_timeout=1, decode_responses=True)
            client.ping()
            self.redis_client = client
            self.use_redis = True
        except Exception:
            self.redis_client = None
            self.use_redis = False

    def get(self, key: str) -> Optional[Any]:
        if self.use_redis and self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    return json.loads(val)
                return None
            except Exception:
                return self.memory_cache.get(key)
        return self.memory_cache.get(key)

    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None):
        ex = expire_seconds or settings.CACHE_EXPIRATION_SECONDS
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.set(key, json.dumps(value), ex=ex)
                return
            except Exception:
                pass
        self.memory_cache.set(key, value, ex=ex)

    def delete(self, key: str):
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception:
                pass
        self.memory_cache.delete(key)

cache = CacheManager()

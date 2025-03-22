from typing import Optional
from redis.asyncio import Redis
from ..utils import get_app_settings

settings = get_app_settings()

class RedisClient:
    _instance: Optional[Redis] = None

    @classmethod
    def get_instance(cls) -> Redis:
        if cls._instance is None:
            cls._instance = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return cls._instance


def get_redis_client() -> Redis:
    return RedisClient.get_instance()

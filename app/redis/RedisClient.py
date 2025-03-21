import redis.asyncio as redis
from ..utils.config import settings

class RedisClient():
    _instance=None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance=redis.from_url(settings.REDIS_URL, decode_responses=True)
        return cls._instance
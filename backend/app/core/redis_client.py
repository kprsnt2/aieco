"""AIEco - Redis Client"""
import redis.asyncio as redis
from app.config import settings

_redis = None

async def init_redis():
    global _redis
    _redis = redis.from_url(settings.redis_url)

async def close_redis():
    if _redis:
        await _redis.close()

async def get_redis():
    return _redis

async def check_redis_connection() -> bool:
    try:
        return await _redis.ping()
    except:
        return False

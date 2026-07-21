from redis.asyncio import Redis
from app.config import settings

# Create global async Redis client. Defaults to decoding responses as string UTF-8.
redis_client = Redis.from_url(
    settings.redis_url, 
    decode_responses=True,
    socket_timeout=2.0 # Non-blocking fallback if redis is down
)

async def cache_get(key: str) -> str | None:
    try:
        return await redis_client.get(key)
    except Exception:
        return None

async def cache_set(key: str, value: str, ttl: int = 600):
    try:
        await redis_client.set(key, value, ex=ttl)
    except Exception:
        pass

async def cache_delete(key: str):
    try:
        await redis_client.delete(key)
    except Exception:
        pass

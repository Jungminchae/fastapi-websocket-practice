from redis import asyncio as aioredis

async def get_redis_pool():
    return await aioredis.from_url("redis://redis:6379/0")



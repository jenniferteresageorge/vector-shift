import os
import redis.asyncio as redis
from kombu.utils.url import safequote

redis_client = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)

async def add_key_value_redis(key, value, expire=None):
    result = await redis_client.set(key, value)
    print(f"✅ Redis SET Result for {key}: {result}")  # Debugging log
    if expire:
        await redis_client.expire(key, expire)
    return result
async def get_value_redis(key):
    return await redis_client.get(key)

async def delete_key_redis(key):
    await redis_client.delete(key)
async def test_redis_connection():
    try:
        pong = await redis_client.ping()
        print("✅ Redis Connected! Ping Response:", pong)
    except Exception as e:
        print("❌ Redis Connection Failed:", str(e))
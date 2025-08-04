from redis import asyncio as aioredis
from redis.asyncio import Redis
from typing import Optional
from .helpers import logger
from .settings import settings


class RedisConnectionManager:
    """
    Redis connection manager for handling the Redis connection pool.
    """

    _redis_client: Optional[Redis] = None

    def __init__(self, host: str):
        self._host = host

    async def connect(self) -> None:
        """
        Connect to Redis and initialize the client.
        This should be called at application startup.
        """
        logger.info("Connecting to Redis...")
        self._redis_client = aioredis.from_url(
            self._host,
            encoding="utf-8",
            decode_responses=True,
            password=settings.redis_password or None,
            db=settings.redis_db or 0,
        )
        try:
            # Ping Redis to test the connection
            await self._redis_client.ping()
            logger.info("Connection to Redis successful.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis_client = None  # Ensure client is None if connection fails
            raise e

    async def close(self) -> None:
        """
        Close the Redis connection pool gracefully.
        This should be called at application shutdown.
        """
        if self._redis_client is None:
            logger.warning("Redis client is not initialized, nothing to close.")
            return

        logger.info("Closing connection to Redis...")
        await self._redis_client.close()
        self._redis_client = None
        logger.info("Connection to Redis closed.")

    def get_client(self) -> Redis:
        """
        Returns the Redis client instance.
        """
        if self._redis_client is None:
            raise Exception("Redis client is not initialized.")
        return self._redis_client

redis_manager = RedisConnectionManager(f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}")

async def get_redis_client() -> Redis:
    """
    Get the Redis client instance.
    This function should be used to access the Redis client in the application.
    """
    if redis_manager._redis_client is None:
        await redis_manager.connect()
    return redis_manager.get_client()

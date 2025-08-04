from typing import Optional
import uuid
from redis.asyncio import Redis
from ..config.settings import settings
from ..utils.otp_helper import hash_otp_code


class OTPRepository:
    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    async def cache_otp(self, user_id: uuid.UUID, code: str) -> None:
        """
        Store the OTP for a user in Redis.
        """
        hashed_otp = hash_otp_code(code)

        key = f"otp:{user_id}"
        await self.redis_client.set(key, hashed_otp, ex=settings.otp_expires_seconds)

    async def get_otp(self, user_id: uuid.UUID) -> Optional[str]:
        """
        Retrieve the OTP for a user from Redis.
        """
        key = f"otp:{user_id}"
        return await self.redis_client.get(key)

    async def delete_otp(self, user_id: uuid.UUID) -> None:
        """
        Delete the OTP for a user from Redis.
        """
        key = f"otp:{user_id}"
        await self.redis_client.delete(key)

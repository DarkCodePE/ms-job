# redis_service.py
import json
from typing import Optional, Dict, Any
import logging
from redis.asyncio import Redis

from app.core.datastore.redis_connector import get_redis_connection

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def set_user_info(self, user_id: str, user_data: dict):
        """Almacena información del usuario en Redis"""
        try:
            name = f"user:{user_id}"
            await self.redis.set(
                name,
                json.dumps(user_data),
                ex=86400  # 24 horas de expiración
            )
        except Exception as e:
            logger.error(f"Error setting user in Redis: {str(e)}")
            raise e

    async def get_user_info(self, user_id: str) -> Optional[dict]:
        """Obtiene la información del usuario desde Redis"""
        try:
            name = f"user:{user_id}"
            data = await self.redis.get(name)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting user from Redis: {str(e)}")
            return None

async def get_redis_service() -> RedisService:
    """Factory para obtener una instancia de RedisService"""
    redis = await get_redis_connection()
    return RedisService(redis)
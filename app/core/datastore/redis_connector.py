# redis_connector.py
from redis.asyncio import Redis, ConnectionPool
import os


class RedisConnector:
    def __init__(self):
        self.pool = None

    async def init_redis_pool(self) -> ConnectionPool:
        """Inicializa el pool de conexiones Redis"""
        if not self.pool:
            self.pool = ConnectionPool(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                password=os.getenv("REDIS_PASSWORD"),
                decode_responses=True,
                max_connections=10
            )
        return self.pool

    async def get_redis_connection(self) -> Redis:
        """Obtiene una conexión Redis del pool"""
        if not self.pool:
            await self.init_redis_pool()
        return Redis(connection_pool=self.pool)


# Instancia global del conector
redis_connector = RedisConnector()


async def get_redis_connection() -> Redis:
    """Función helper para obtener una conexión Redis"""
    return await redis_connector.get_redis_connection()

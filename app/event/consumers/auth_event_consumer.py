# auth_event_consumer.py
import json
import logging
from typing import Dict, Any
import aiokafka
import redis

from app.cache.redis_service import RedisService

logger = logging.getLogger(__name__)


class AuthEventConsumer:
    def __init__(self, redis_service: RedisService):
        self.consumer = aiokafka.AIOKafkaConsumer(
            'auth-events',
            bootstrap_servers='localhost:9092',
            group_id='jobs-auth-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest'
        )
        self.redis_service = redis_service

    async def process_auth_event(self, event: Dict[str, Any]):
        """
        Procesa eventos de autenticación y actualiza Redis.
        """
        try:
            event_type = event.get('type')

            if event_type == 'USERS_LIST_UPDATED':
                # Actualizar múltiples usuarios
                for user_data in event.get('users', []):
                    await self.redis_service.set_user_info(
                        user_data['userId'],
                        user_data
                    )
                logger.info("Lista de usuarios actualizada en Redis")

            elif event_type in ['LOGIN', 'REGISTER', 'ROLE_UPDATE']:
                # Actualizar un solo usuario
                user_data = {
                    'userId': event.get('userId'),
                    'username': event.get('username'),
                    'email': event.get('email'),
                    'roles': event.get('roles', []),
                    'courseIds': event.get('courseIds', [])
                }
                await self.redis_service.set_user_info(
                    user_data['userId'],
                    user_data
                )
                logger.info(f"Usuario actualizado en Redis para evento {event_type}")

        except Exception as e:
            logger.error(f"Error procesando evento: {str(e)}")

    async def start(self):
        """Inicia el consumo de eventos"""
        logger.info("Iniciando consumidor de eventos de autenticación...")
        try:
            await self.consumer.start()
            logger.info("Consumidor iniciado y esperando mensajes...")

            async for message in self.consumer:
                logger.info(f"Mensaje recibido: {message.value}")
                await self.process_auth_event(message.value)

        except Exception as e:
            logger.error(f"Error en el consumidor: {str(e)}")
        finally:
            await self.consumer.stop()
# job_event_consumer.py
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
import aiokafka

from app.core.exceptions.kafka_exception import KafkaError
from app.db.database import async_session
from app.model.schemas import JobCreate
from app.services.job_service import save_job_to_db

logger = logging.getLogger(__name__)


class JobEventConsumer:
    def __init__(self):
        self.consumer = aiokafka.AIOKafkaConsumer(
            'job-events',
            bootstrap_servers='localhost:9092',
            group_id='jobs-processor-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            max_poll_records=10
        )

    async def start(self):
        """Inicia el consumo de eventos"""
        logger.info("Iniciando consumidor de eventos de trabajos...")
        try:
            await self.consumer.start()
            logger.info("Consumidor iniciado y esperando mensajes...")

            while True:  # Loop continuo
                try:
                    async for message in self.consumer:
                        try:
                            logger.info(f"Mensaje recibido: {message.value}")
                            await self.process_job_event(message.value)
                            # Solo hacemos commit si el procesamiento fue exitoso
                            await self.consumer.commit()
                        except Exception as e:
                            logger.error(f"Error procesando mensaje individual: {str(e)}")
                            # Continuamos con el siguiente mensaje en caso de error
                            continue

                except Exception as e:
                    logger.error(f"Error en el consumo de mensajes: {str(e)}")
                    # Esperar un poco antes de reintentar
                    await asyncio.sleep(5)
                    continue

        except Exception as e:
            logger.error(f"Error fatal en el consumidor: {str(e)}")
            raise
        finally:
            await self.consumer.stop()

    async def process_job_event(self, event: Dict[str, Any]):
        """
        Procesa eventos relacionados con trabajos.
        """
        try:
            event_type = event.get('type')
            job_data = event.get('data')
            metadata = event.get('metadata', {})

            if event_type == 'JOB_CREATED':
                await self._handle_job_created(job_data, metadata)
            elif event_type == 'JOB_UPDATED':
                await self._handle_job_updated(job_data, metadata)
            elif event_type == 'JOB_DELETED':
                await self._handle_job_deleted(job_data, metadata)
            else:
                logger.warning(f"Tipo de evento no reconocido: {event_type}")

            logger.info(f"Evento {event_type} procesado exitosamente")
            await self.consumer.commit()
        except Exception as e:
            logger.error(f"Error procesando evento de trabajo: {str(e)}")
            raise KafkaError(f"Error procesando evento de trabajo: {str(e)}")

    async def _handle_job_created(self, job_data: Dict[str, Any], metadata: Dict[str, Any]):
        """Maneja la creación de nuevos trabajos."""
        try:
            job_data = process_job_data(job_data)

            async with async_session() as session:
                async with session.begin():  # Usar transaction context
                    job = JobCreate(
                        id=job_data['id'],
                        title=job_data.get('title'),
                        description=job_data.get('description'),
                        requirements=job_data.get('requirements', []),
                        location=job_data.get('location'),
                        salary_range=job_data.get('salary_range'),
                        company=job_data.get('company'),
                        job_type=job_data.get('job_type', 'NOT_SPECIFIED'),
                        level=job_data.get('level', 'NOT_SPECIFIED'),
                        is_remote=job_data.get('is_remote', False),
                        source_url=job_data.get('source_url'),
                        source=metadata.get('source'),
                        processed_at=metadata.get('processed_at'),
                        raw_job_id=job_data.get('raw_job_id')
                    )

                    await save_job_to_db(job, session)
                    logger.info(f"Trabajo {job.title} de {job.company} guardado exitosamente.")

        except Exception as e:
            logger.error(f"Error procesando nuevo trabajo: {str(e)}")
            raise

    async def _handle_job_updated(self, job_data: Dict[str, Any], metadata: Dict[str, Any]):
        """
        Maneja actualizaciones de trabajos existentes.
        """
        try:
            # Implementar lógica de actualización
            logger.info(f"Actualizando trabajo ID: {job_data.get('source_job_id')}")
            # TODO: Implementar lógica específica
            pass
        except Exception as e:
            logger.error(f"Error actualizando trabajo: {str(e)}")
            raise

    async def _handle_job_deleted(self, job_data: Dict[str, Any], metadata: Dict[str, Any]):
        """
        Maneja la eliminación de trabajos.
        """
        try:
            # Implementar lógica de eliminación
            logger.info(f"Eliminando trabajo ID: {job_data.get('source_job_id')}")
            # TODO: Implementar lógica específica
            pass
        except Exception as e:
            logger.error(f"Error eliminando trabajo: {str(e)}")
            raise

    async def start(self):
        """Inicia el consumo de eventos"""
        logger.info("Iniciando consumidor de eventos de trabajos...")
        try:
            await self.consumer.start()
            logger.info("Consumidor iniciado y esperando mensajes...")

            async for message in self.consumer:
                logger.info(f"Mensaje recibido: {message.value}")
                await self.process_job_event(message.value)
                #await self.consumer.commit()
        except Exception as e:
            logger.error(f"Error en el consumidor: {str(e)}")
            raise KafkaError(f"Error en el consumidor de eventos de trabajo: {str(e)}")
        finally:
            await self.consumer.stop()


def process_job_data(job_data: dict) -> dict:
    job_data['id'] = job_data.get('source_job_id', str(uuid.uuid4()))
    job_data['creator_id'] = "default_creator"  # Asigna un valor por defecto
    job_data['created_at'] = datetime.utcnow()  # Fecha de creación
    job_data['updated_at'] = datetime.utcnow()  # Fecha de última actualización
    job_data['active'] = True  # Valor por defecto para 'active'
    # Asigna un valor predeterminado si la descripción está vacía o no tiene suficientes caracteres
    job_data['description'] = job_data.get('description', "").strip()
    if len(job_data['description']) < 20:
        job_data['description'] = "Descripción no disponible. Por favor, contáctenos para más información."

    return job_data

from fastapi import FastAPI

import asyncio
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import jobs
from app.cache.redis_service import get_redis_service
from app.core.datastore.redis_connector import redis_connector
from app.db.database import init_db
from app.event.consumers.auth_event_consumer import AuthEventConsumer
from app.event.consumers.job_event_consumer import JobEventConsumer
import logging

from app.services.job_service import kafka_producer

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    jobs.router
)

# Inicializa la base de datos
init_db()


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "langsmith_enabled": True
    }


@app.on_event("startup")
async def startup_event():
    """
    Evento de inicio de la aplicación.
    - Inicializa la conexión a Redis.
    - Crea la tarea asíncrona para el consumidor de eventos.
    """
    # Inicializar el pool de conexiones Redis
    await redis_connector.init_redis_pool()

    # Inicializar el productor de Kafka
    try:
        await kafka_producer.start()
        logging.info("Kafka producer started successfully.")
    except Exception as e:
        logging.error(f"Error initializing Kafka producer: {str(e)}")
        raise

    # Instanciar los consumidores de eventos
    auth_consumer = AuthEventConsumer(await get_redis_service())
    job_consumer = JobEventConsumer()

    # Crear las tareas asíncronas para que los consumidores empiecen a escuchar
    # y almacenarlas en el estado de la aplicación
    app.state.consumer_tasks = [
        asyncio.create_task(auth_consumer.start()),
        asyncio.create_task(job_consumer.start())
    ]

    # Agregar manejador de errores para las tareas
    for task in app.state.consumer_tasks:
        task.add_done_callback(lambda t: handle_consumer_task_result(t))


def handle_consumer_task_result(task):
    """
    Maneja el resultado de las tareas de los consumidores.
    Si una tarea termina con error, lo registra.
    """
    try:
        task.result()
    except asyncio.CancelledError:
        pass  # La tarea fue cancelada normalmente durante el apagado
    except Exception as e:
        logging.error(f"Consumer task failed with error: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento de cierre de la aplicación.
    - Cancela las tareas de los consumidores.
    - Cierra la conexión al pool de Redis.
    """
    # Cancelar todas las tareas de los consumidores
    if hasattr(app.state, 'consumer_tasks'):
        for task in app.state.consumer_tasks:
            if not task.done():
                task.cancel()
        # Esperar a que todas las tareas se cancelen
        await asyncio.gather(*app.state.consumer_tasks, return_exceptions=True)

    if redis_connector.pool:
        await redis_connector.pool.disconnect()


    # Detener el productor de Kafka
    try:
        await kafka_producer.stop()
        logging.info("Kafka producer stopped successfully.")
    except Exception as e:
        logging.error(f"Error stopping Kafka producer: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Elimina la coma y el texto adicional que tenías para evitar errores
    uvicorn.run(app, host="0.0.0.0", port=8091, workers=2)

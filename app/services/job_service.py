# services/job_service.py
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from datetime import datetime

from app.event.producers.producer import KafkaProducer
from app.model.models import JobOffer, JobApplication
from app.model.schemas import Job, JobUpdate, JobCreate, JobApplicationCreate
import logging

logger = logging.getLogger(__name__)

# Instancia global de KafkaProducer (puedes ajustarlo según tus necesidades)
kafka_producer = KafkaProducer()


async def create_job(db: Session, job_data: JobCreate) -> Job:
    job = JobOffer(
        title=job_data.title,
        company=job_data.company,
        description=job_data.description,
        requirements=job_data.requirements,
        job_type=job_data.job_type.value,
        level=job_data.level.value,
        salary_range=job_data.salary_range,
        location=job_data.location,
        is_remote=job_data.is_remote
    )

    db.add(job)
    db.commit()
    db.refresh(job)
    return job


async def get_job(db: Session, job_id: str) -> Optional[Job]:
    job = db.query(JobOffer).filter(JobOffer.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


async def get_job_by_id(db: Session, job_id: str) -> Optional[JobOffer]:
    """
    Recupera un trabajo específico por su ID.
    """
    return db.query(JobOffer).filter(JobOffer.id == job_id).first()


async def get_job_offer_by_application_id(db: Session, application_id: str) -> Optional[JobOffer]:
    """
    Recupera una oferta de trabajo usando el ID de una aplicación.
    """
    application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    job_offer = db.query(JobOffer).filter(JobOffer.id == application.job_offer_id).first()

    return job_offer


async def get_jobs(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        active_only: bool = True
) -> List[Job]:
    query = db.query(JobOffer)
    if active_only:
        query = query.filter(JobOffer.active == True)
    return query.offset(skip).limit(limit).all()


def search_jobs(
        db: Session,
        q: Optional[str] = None,
        location: Optional[str] = None,
        offset: int = 0,
        limit: int = 10,
        page: int = 1
) -> Dict[str, Any]:
    print(f"q: {q}")
    jobs_query = db.query(JobOffer)
    print(f"jobs_query: {jobs_query}")
    if q:
        jobs_query = jobs_query.filter(JobOffer.title.ilike(f"%{q}%"))
    if location:
        jobs_query = jobs_query.filter(JobOffer.location.ilike(f"%{location}%"))

    total_jobs = jobs_query.count()
    jobs = jobs_query.offset(offset).limit(limit).all()
    print(f"jobs: {jobs}")
    return {
        "jobs": jobs,
        "total": total_jobs,
        "page": page,
        "totalPages": (total_jobs + limit - 1) // limit
    }


async def update_job(
        db: Session,
        job_id: str,
        job_data: JobUpdate
) -> Job:
    job = await get_job(db, job_id)

    update_data = job_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


async def create_application(db: Session,
                             application_data: JobApplicationCreate,
                             user_id: str,
                             profile_data: dict):
    # Verificar si la oferta existe
    job_offer = db.query(JobOffer).filter_by(id=application_data.job_offer_id).first()
    if not job_offer:
        raise ValueError("La oferta de trabajo no existe")

    # Crear la aplicación
    application = JobApplication(
        job_offer_id=application_data.job_offer_id,
        id_user=user_id,
        applicant_name=application_data.applicant_name,
        applicant_email=application_data.applicant_email
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Preparar evento
    event = {
        "type": "job-application-created",
        "data": {
            "application_id": application.id,
            "job_offer_id": application.job_offer_id,
            "user_id": user_id,
            "applicant_name": application_data.applicant_name,
            "applicant_email": application_data.applicant_email,
            "profile": profile_data,  # Incluir los datos del perfil
            "job_offer": {
                "title": job_offer.title,
                "company": job_offer.company,
                "description": job_offer.description,
                "requirements": job_offer.requirements,
                "location": job_offer.location,
                "is_remote": job_offer.is_remote
            }
        },
        "metadata": {
            "source": "ms-job",
            "timestamp": application.created_at.isoformat()
        }
    }

    # Publicar evento en Kafka
    try:
        await kafka_producer.send_event("job-events", event)
        logger.info(f"Evento enviado al tópico 'job-events': {event}")
    except Exception as e:
        logger.error(f"Error al enviar evento a Kafka: {e}")

    return application


async def save_job_to_db(job: JobCreate, session):
    try:
        # Crear el insert statement con ON CONFLICT DO NOTHING
        insert_stmt = insert(JobOffer).values(
            id=job.id,
            title=job.title,
            company=job.company,
            description=job.description,
            requirements=job.requirements,
            job_type=job.job_type,
            level=job.level,
            salary_range=job.salary_range,
            location=job.location,
            is_remote=job.is_remote,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Agregar la cláusula DO NOTHING
        do_update_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['id'],  # Índice único
            set_={
                'title': job.title,
                'description': job.description,
                'updated_at': datetime.utcnow(),
            }
        )

        # Ejecutar la sentencia
        await session.execute(do_update_stmt)
        await session.commit()

        logger.info(f"Trabajo guardado/actualizado exitosamente: {job.id}")

    except Exception as e:
        logger.error(f"Error al guardar el trabajo: {str(e)}")
        await session.rollback()
        raise

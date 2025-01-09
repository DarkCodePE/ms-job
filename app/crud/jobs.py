# app/crud/jobs.py
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.model.models import JobOffer
from app.model.schemas import JobCreate, JobUpdate


class JobCRUD:
    @staticmethod
    def create_job(db: Session, *, job_data: JobCreate, creator_id: str) -> JobOffer:
        """Crea una nueva oferta de trabajo"""
        db_job = JobOffer(**job_data.dict(), creator_id=creator_id)
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job

    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[JobOffer]:
        """Obtiene una oferta de trabajo por su ID"""
        return db.query(JobOffer).filter(JobOffer.id == job_id).first()

    @staticmethod
    def get_jobs(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 10,
        active_only: bool = True
    ) -> List[JobOffer]:
        """Lista las ofertas de trabajo con paginación y filtros"""
        query = db.query(JobOffer)
        if active_only:
            query = query.filter(JobOffer.active == True)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_job(
        db: Session,
        *,
        job_id: str,
        job_data: JobUpdate
    ) -> Optional[JobOffer]:
        """Actualiza una oferta de trabajo"""
        job = JobCRUD.get_job(db, job_id)
        if job:
            job_data_dict = job_data.dict(exclude_unset=True)
            for key, value in job_data_dict.items():
                setattr(job, key, value)
            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    def delete_job(db: Session, *, job_id: str) -> bool:
        """Elimina una oferta de trabajo"""
        job = JobCRUD.get_job(db, job_id)
        if job:
            db.delete(job)
            db.commit()
            return True
        return False

# Instancia global para operaciones CRUD de trabajos
job_crud = JobCRUD()
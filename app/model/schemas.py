# model/schemas.py
import uuid

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class JobBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., min_length=20)
    requirements: list[str]
    location: str
    salary_range: Optional[str] = None
    is_active: bool = True


# job_create_data = JobCreate(
#             title=job_data['title'],
#             company=job_data['company'],
#             description=job_data.get('description', ''),
#             requirements=job_data.get('requirements', []),
#             job_type=job_data.get('job_type', 'NOT_SPECIFIED'),
#             level=job_data.get('level', 'NOT_SPECIFIED'),
#             salary_range=job_data.get('salary_range'),
#             location=job_data.get('location', ''),
#             is_remote=job_data.get('is_remote', False),
#         )

class JobCreate(BaseModel):
    id: str = str(uuid.uuid4())  # Genera un ID único por defecto
    title: str
    company: str
    description: Optional[str] = None
    requirements: List[str] = []
    job_type: str = "NOT_SPECIFIED"
    level: str = "NOT_SPECIFIED"
    salary_range: Optional[str] = None
    location: str
    is_remote: bool = False
    active: bool = True
    created_at: datetime = datetime.utcnow()  # Fecha de creación
    updated_at: datetime = datetime.utcnow()  # Fecha de actualización
    source_url: Optional[str] = None
    source: Optional[str] = None
    processed_at: Optional[datetime] = None  # Campo `processed_at` agregado
    raw_job_id: Optional[str] = None  # Campo `raw_job_id` agregado
    creator_id: str = "default_creator"  # Agregar campo `creator_id`


class SearchResponse(BaseModel):
    jobs: List[JobCreate]  # Usamos JobCreate para representar cada trabajo
    total: int  # Total de trabajos encontrados
    page: int  # Página actual
    totalPages: int  # Total de páginas disponibles


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[list[str]] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    is_active: Optional[bool] = None


class Job(JobBase):
    title: str = Field(..., min_length=5, max_length=100)
    description: Optional[str] = Field(None, min_length=0)  # Permite un valor vacío como predeterminado
    requirements: list[str]
    location: str
    salary_range: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class ProfileData(BaseModel):
    first_name: str
    last_name: str
    headline: Optional[str]
    about: Optional[str]
    location: Optional[str]
    contact_info: dict
    skills: List[str]
    languages: List[dict]
    experiences: List[dict]
    education: List[dict]


class JobApplicationCreate(BaseModel):
    job_offer_id: str
    applicant_name: str
    applicant_email: EmailStr


class ApplicationRequest(BaseModel):
    application_data: JobApplicationCreate
    profile_data: ProfileData


class JobApplicationResponse(BaseModel):
    id: str
    job_offer_id: str
    applicant_name: str
    applicant_email: EmailStr
    status: str
    created_at: datetime

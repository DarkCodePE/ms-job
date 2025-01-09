# models.py
from datetime import datetime
from typing import List
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.base import Base


class JobOffer(Base):
    __tablename__ = "job_offers"
    __table_args__ = {"schema": "public"}

    id: str = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title: str = Column(String, nullable=False)
    company: str = Column(String, nullable=False)
    description: str = Column(String, nullable=False)
    requirements: List[str] = Column(ARRAY(String), nullable=False)
    job_type: str = Column(String, nullable=False)
    level: str = Column(String, nullable=False)
    salary_range: str = Column(String, nullable=True)
    location: str = Column(String, nullable=False)
    is_remote: bool = Column(Boolean, default=False)
    active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    applications_count: int = Column(Integer, default=0)

    # Relaciones
    applications = relationship("JobApplication", back_populates="job_offer")


class JobApplication(Base):
    __tablename__ = "job_applications"
    __table_args__ = {"schema": "public"}

    id: str = Column(String, primary_key=True, default=lambda: str(uuid4()))
    job_offer_id: str = Column(String, ForeignKey("public.job_offers.id"), nullable=False)
    id_user: str = Column(String, nullable=False)  # ID del usuario
    applicant_name: str = Column(String, nullable=False)
    applicant_email: str = Column(String, nullable=False)
    status: str = Column(String, default="PENDING")
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    # Relación con JobOffer
    job_offer = relationship("JobOffer", back_populates="applications")

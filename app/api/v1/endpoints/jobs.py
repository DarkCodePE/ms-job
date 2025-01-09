# routers/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.middleware.auth_middleware import require_auth
from app.model.models import JobOffer, JobApplication
from app.model.schemas import JobCreate, Job, JobUpdate, SearchResponse, JobApplicationResponse, JobApplicationCreate, \
    ApplicationRequest
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=List[Job])
async def list_jobs(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        active_only: bool = Query(True),
        db: Session = Depends(get_db),
):
    jobs = await job_service.get_jobs(db, skip, limit, active_only)

    return jobs


@router.get("/{job_id}", response_model=Job)
async def get_job_by_id(
        job_id: str,
        db: Session = Depends(get_db)
):
    """
    Recupera un trabajo específico por su ID.
    """
    job = await job_service.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/search/val", response_model=SearchResponse)
async def search_jobs(
        q: Optional[str] = None,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
        db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    print(f"offset: {offset}")
    print(f"q: {q}")
    print(f"location: {location}")
    result = job_service.search_jobs(db, q, location, offset, limit)
    return result


@router.get("/jobs/suggest", response_model=List[str])
async def suggest_terms(
        query: str,
        db: Session = Depends(get_db)
):
    terms = db.query(JobOffer.title).distinct().filter(JobOffer.title.ilike(f"%{query}%")).all()
    return [term[0] for term in terms]


@router.get("/locations/suggest", response_model=List[str])
async def suggest_locations(
        query: str,
        db: Session = Depends(get_db)
):
    locations = db.query(JobOffer.location).distinct().filter(JobOffer.location.ilike(f"%{query}%")).all()
    return [location[0] for location in locations]


@router.post("/apply", response_model=JobApplicationResponse)
async def apply_to_job(
        request: ApplicationRequest,
        db: Session = Depends(get_db),
        user: dict = Depends(require_auth())
):
    try:
        user_id = user.get("userId")
        print(f"user_id: {user_id}")
        application_data = request.application_data
        profile_data = request.profile_data.dict()

        print(f"application_data: {application_data}")
        print(f"profile_data: {profile_data}")

        application = await job_service.create_application(db, application_data, user_id, profile_data)
        return application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error interno: {e}")
        raise HTTPException(status_code=500, detail="Error interno al procesar la solicitud")


@router.get("/application/{application_id}/job-offer", response_model=Job)
async def get_job_offer_by_application_id(
        application_id: str,
        db: Session = Depends(get_db)
):
    """
    Recupera la oferta de trabajo asociada a un ID de aplicación.
    """
    job_offer = await job_service.get_job_offer_by_application_id(db, application_id)
    if not job_offer:
        raise HTTPException(status_code=404, detail="Job Offer not found")
    return job_offer

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Job
from backend.app.schemas import JobResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("", response_model=list[JobResponse])
def list_jobs(q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Job).filter(Job.is_active.is_(True))
    if q:
        query = query.filter(Job.title.ilike(f"%{q[:80]}%"))
    return query.limit(100).all()

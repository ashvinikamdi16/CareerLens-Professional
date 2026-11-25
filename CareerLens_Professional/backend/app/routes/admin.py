from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.dependencies import require_admin
from backend.app.models import User, Resume, AnalysisResult, Job

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
def stats(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "total_users": db.query(func.count(User.id)).scalar() or 0,
        "active_users": db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0,
        "total_resumes": db.query(func.count(Resume.id)).scalar() or 0,
        "completed_resumes": db.query(func.count(Resume.id)).filter(Resume.status == "completed").scalar() or 0,
        "failed_resumes": db.query(func.count(Resume.id)).filter(Resume.status == "failed").scalar() or 0,
        "analysis_reports": db.query(func.count(AnalysisResult.id)).scalar() or 0,
        "active_jobs": db.query(func.count(Job.id)).filter(Job.is_active.is_(True)).scalar() or 0,
    }

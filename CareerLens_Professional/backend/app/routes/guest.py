from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.rate_limit import limit_guest_analysis
from backend.app.models import Job
from backend.app.services.storage import validate_and_store, remove_file, materialize_file, cleanup_materialized_file
from backend.app.services.resume_parser import extract_text, ResumeParseError
from backend.app.services.analyzer import build_analysis, match_jobs

router = APIRouter(prefix="/guest", tags=["Guest analysis"])

@router.post("/analyze")
def guest_analyze(file: UploadFile = File(...), _: None = Depends(limit_guest_analysis), db: Session = Depends(get_db)):
    data = file.file.read(5 * 1024 * 1024 + 1)
    # Guest files are held in a temporary owner folder and removed after processing.
    try:
        saved = validate_and_store(data, file.filename or "guest-resume", owner_id="guest", max_mb=5)
    except HTTPException:
        raise
    try:
        try:
            local_path, temporary = materialize_file(saved["file_path"])
            try:
                text, metadata = extract_text(local_path, saved["mime_type"])
            finally:
                cleanup_materialized_file(local_path, temporary)
        except ResumeParseError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        analysis = build_analysis(text, metadata)
        jobs = db.query(Job).filter(Job.is_active.is_(True)).all()
        job_dicts = [{"id": j.id, "title": j.title, "company": j.company, "location": j.location, "experience_level": j.experience_level, "description": j.description, "required_skills": j.required_skills, "apply_url": j.apply_url, "source": j.source} for j in jobs]
        recommendations = match_jobs(text, analysis["skills"], job_dicts)
        return {"filename": (file.filename or "resume")[:255], "analysis": analysis, "recommendations": recommendations, "storage": "temporary; uploaded file is deleted after this request"}
    finally:
        remove_file(saved["file_path"])

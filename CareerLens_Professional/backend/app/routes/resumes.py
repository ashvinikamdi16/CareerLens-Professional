from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.rate_limit import apply_rate_limit
from backend.app.dependencies import get_current_user
from backend.app.models import User, Resume, AnalysisResult, Job
from backend.app.schemas import ResumeResponse, ResumeCorrectionRequest
from backend.app.services.storage import validate_and_store, remove_file, materialize_file, cleanup_materialized_file, read_stored_file
from backend.app.services.analyzer import match_jobs
from backend.app.services.report import create_report
from backend.app.services.resume_parser import extract_text
from backend.app.services.analyzer import build_analysis

router = APIRouter(prefix="/resumes", tags=["Resume management"])


def _analyse_resume_now(resume: Resume, db: Session) -> None:
    """Process the uploaded file inside the API service so no separate Celery worker is required."""
    try:
        resume.status = "processing"
        resume.error_message = None
        db.commit()
        local_path, temporary = materialize_file(resume.file_path)
        try:
            extracted_text, metadata = extract_text(local_path, resume.mime_type)
        finally:
            cleanup_materialized_file(local_path, temporary)
        result = build_analysis(extracted_text, metadata)
        db.add(AnalysisResult(resume_id=resume.id, extracted_text=extracted_text, result_json=result))
        resume.status = "completed"
        resume.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        current = db.get(Resume, resume.id)
        if current:
            current.status = "failed"
            current.error_message = str(exc)[:1000]
            db.commit()

@router.post("/upload", response_model=ResumeResponse, status_code=202)
async def upload_resume(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    apply_rate_limit("user-upload", str(user.id), limit=settings.user_uploads_per_hour, window_seconds=3600)
    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    saved = validate_and_store(data, file.filename or "resume", user.id)
    duplicate = db.query(Resume).filter(Resume.owner_id == user.id, Resume.sha256 == saved["sha256"]).first()
    if duplicate:
        remove_file(saved["file_path"])
        raise HTTPException(409, "You have already uploaded this exact file.")
    resume = Resume(owner_id=user.id, original_filename=(file.filename or "resume")[:255], **saved)
    db.add(resume)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        remove_file(saved["file_path"])
        raise HTTPException(409, "You have already uploaded this exact file.")
    db.refresh(resume)
    _analyse_resume_now(resume, db)
    db.refresh(resume)
    return resume

@router.get("", response_model=list[ResumeResponse])
def list_resumes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Resume).filter(Resume.owner_id == user.id).order_by(desc(Resume.created_at)).all()

@router.get("/{resume_id}")
def get_resume(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.owner_id == user.id).first()
    if not resume: raise HTTPException(404, "Resume not found.")
    latest = db.query(AnalysisResult).filter(AnalysisResult.resume_id == resume.id).order_by(desc(AnalysisResult.created_at)).first()
    return {"resume": ResumeResponse.model_validate(resume).model_dump(mode="json"), "analysis": latest.result_json if latest else None, "extracted_text": latest.extracted_text if latest else None, "analysis_created_at": latest.created_at.isoformat() if latest else None}

@router.patch("/{resume_id}/correction")
def correct_extracted_text(resume_id: int, payload: ResumeCorrectionRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.owner_id == user.id).first()
    if not resume: raise HTTPException(404, "Resume not found.")
    latest = db.query(AnalysisResult).filter(AnalysisResult.resume_id == resume.id).order_by(desc(AnalysisResult.created_at)).first()
    if not latest: raise HTTPException(409, "There is no completed analysis to correct yet.")
    corrected = payload.corrected_text.strip()
    if len(corrected) < 30: raise HTTPException(422, "Corrected text is too short to analyse.")
    previous_metadata = latest.result_json.get("parser_metadata", {})
    previous_metadata["manually_corrected"] = True
    from backend.app.services.analyzer import build_analysis
    latest.extracted_text = corrected
    latest.result_json = build_analysis(corrected, previous_metadata)
    db.commit()
    return {"message": "Corrected text saved and analysis refreshed.", "analysis": latest.result_json}

@router.post("/{resume_id}/reanalyze", response_model=ResumeResponse, status_code=202)
def reanalyze(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.owner_id == user.id).first()
    if not resume: raise HTTPException(404, "Resume not found.")
    resume.status = "queued"; resume.error_message = None; db.commit(); db.refresh(resume)
    _analyse_resume_now(resume, db)
    db.refresh(resume)
    if resume.status == "failed":
        raise HTTPException(422, resume.error_message or "Resume analysis failed.")
    return resume

@router.get("/{resume_id}/recommendations")
def recommendations(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.owner_id == user.id).first()
    if not resume: raise HTTPException(404, "Resume not found.")
    latest = db.query(AnalysisResult).filter(AnalysisResult.resume_id == resume.id).order_by(desc(AnalysisResult.created_at)).first()
    if not latest: raise HTTPException(409, "Resume analysis is not complete yet.")
    jobs = db.query(Job).filter(Job.is_active.is_(True)).all()
    job_dicts = [{"id": j.id, "title": j.title, "company": j.company, "location": j.location, "experience_level": j.experience_level, "description": j.description, "required_skills": j.required_skills, "apply_url": j.apply_url, "source": j.source} for j in jobs]
    return {"recommendations": match_jobs(latest.extracted_text, latest.result_json.get("skills", []), job_dicts)}

@router.get("/{resume_id}/download")
def download_resume(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.owner_id == user.id).first()
    if not resume: raise HTTPException(404, "Resume not found.")
    try:
        content = read_stored_file(resume.file_path)
    except HTTPException:
        raise
    except OSError:
        raise HTTPException(404, "Stored file is unavailable.")
    safe_name = resume.original_filename.replace("\\", "_").replace('"', "")
    return Response(content=content, media_type=resume.mime_type, headers={"Content-Disposition": f'attachment; filename="{safe_name}"'})

@router.get("/{resume_id}/report")
def download_report(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.owner_id == user.id).first()
    if not resume: raise HTTPException(404, "Resume not found.")
    latest = db.query(AnalysisResult).filter(AnalysisResult.resume_id == resume.id).order_by(desc(AnalysisResult.created_at)).first()
    if not latest: raise HTTPException(409, "Analysis is not complete yet.")
    pdf = create_report(resume.original_filename, latest.result_json)
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="CareerLens_Report_{resume.id}.pdf"'})

@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.owner_id == user.id).first()
    if not resume: raise HTTPException(404, "Resume not found.")
    path = resume.file_path
    db.delete(resume); db.commit(); remove_file(path)
    return Response(status_code=204)

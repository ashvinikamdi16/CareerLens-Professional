from backend.app.celery_app import celery_app
from backend.app.core.database import SessionLocal
from backend.app.models import Resume, AnalysisResult
from backend.app.services.resume_parser import extract_text
from backend.app.services.analyzer import build_analysis

@celery_app.task(name="backend.app.tasks.process_resume")
def process_resume(resume_id: int):
    db = SessionLocal()
    try:
        resume = db.get(Resume, resume_id)
        if not resume:
            return {"status": "missing"}
        resume.status = "processing"; resume.error_message = None; db.commit()
        text, metadata = extract_text(resume.file_path, resume.mime_type)
        result = build_analysis(text, metadata)
        db.add(AnalysisResult(resume_id=resume.id, extracted_text=text, result_json=result))
        resume.status = "completed"; resume.error_message = None
        db.commit()
        return {"status": "completed", "resume_id": resume_id}
    except Exception as exc:
        db.rollback()
        resume = db.get(Resume, resume_id)
        if resume:
            resume.status = "failed"
            resume.error_message = str(exc)[:1000]
            db.commit()
        return {"status": "failed", "error": str(exc)[:500]}
    finally:
        db.close()

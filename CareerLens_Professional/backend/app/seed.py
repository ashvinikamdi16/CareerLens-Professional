from pathlib import Path
import csv
from backend.app.core.database import SessionLocal
from backend.app.core.config import settings
from backend.app.core.security import hash_password
from backend.app.models import User, Job


def load_jobs_from_csv() -> list[dict]:
    dataset = Path(__file__).resolve().parents[2] / "data" / "jobs.csv"
    jobs: list[dict] = []
    if not dataset.exists():
        return jobs
    with dataset.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            required_skills = [value.strip() for value in row.get("required_skills", "").split("|") if value.strip()]
            jobs.append({
                "title": row["title"].strip(),
                "company": row["company"].strip(),
                "location": row.get("location", "India").strip(),
                "experience_level": row.get("experience_level", "Entry level").strip(),
                "description": row.get("description", "").strip(),
                "required_skills": required_skills,
                "apply_url": (row.get("apply_url") or "").strip() or None,
                "source": "CareerLens sample dataset",
            })
    return jobs


def initialize_database():
    # Schema is created/updated by Alembic migrations before the API starts.
    db = SessionLocal()
    try:
        admin_email = settings.admin_email.lower().strip()
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(email=admin_email, full_name="CareerLens Admin", password_hash=hash_password(settings.admin_password), is_admin=True)
            db.add(admin)
        if db.query(Job).count() == 0:
            for job in load_jobs_from_csv():
                db.add(Job(**job))
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    initialize_database()

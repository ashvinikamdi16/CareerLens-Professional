from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.routes import auth, resumes, guest, jobs, admin
from backend.app.seed import initialize_database

app = FastAPI(title=settings.app_name, version="1.0.0", description="Multi-user resume analysis and career recommendation API")

origins = [settings.frontend_url, "http://localhost:8501"]
app.add_middleware(CORSMiddleware, allow_origins=list(set(origins)), allow_credentials=True, allow_methods=["GET", "POST", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])

app.include_router(auth.router, prefix="/api/v1")
app.include_router(resumes.router, prefix="/api/v1")
app.include_router(guest.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

@app.on_event("startup")
def startup():
    if settings.app_env.lower() == "production":
        if len(settings.secret_key) < 32 or settings.secret_key == "development-only-change-me":
            raise RuntimeError("Set a unique SECRET_KEY of at least 32 characters before production deployment.")
        if settings.admin_password == "ChangeThisAdminPassword!123":
            raise RuntimeError("Set a unique ADMIN_PASSWORD before production deployment.")
    initialize_database()

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}

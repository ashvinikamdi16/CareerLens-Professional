from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.app.core.database import get_db
from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.models import User
from backend.app.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse, DeleteAccountRequest
from backend.app.dependencies import get_current_user
from backend.app.models import Resume
from backend.app.services.storage import remove_file
from fastapi import Response
from backend.app.core.rate_limit import apply_rate_limit, get_client_ip
from backend.app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    apply_rate_limit("register", ip, limit=settings.registration_attempts_per_hour, window_seconds=3600)
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists.")
    user = User(email=email, full_name=payload.full_name.strip(), password_hash=hash_password(payload.password), is_admin=False)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists.")
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    apply_rate_limit("login", f"{ip}:{payload.email.lower()}", limit=settings.login_attempts_per_15min, window_seconds=900)
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password.")
    return TokenResponse(access_token=create_access_token(str(user.id)))

@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.delete("/me", status_code=204)
def delete_my_account(
    payload: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.is_admin:
        raise HTTPException(403, "The administrator account cannot be deleted through this endpoint.")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(403, "Password confirmation failed.")
    resumes = db.query(Resume).filter(Resume.owner_id == user.id).all()
    file_paths = [resume.file_path for resume in resumes]
    db.delete(user)
    db.commit()
    for file_path in file_paths:
        remove_file(file_path)
    return Response(status_code=204)

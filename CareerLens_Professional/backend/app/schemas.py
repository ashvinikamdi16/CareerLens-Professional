from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_admin: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResumeResponse(BaseModel):
    id: int
    original_filename: str
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    experience_level: str
    description: str
    required_skills: list
    apply_url: str | None = None
    source: str
    model_config = ConfigDict(from_attributes=True)


class ResumeCorrectionRequest(BaseModel):
    corrected_text: str = Field(min_length=30, max_length=30000)


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "CareerLens Professional API"
    app_env: str = "development"
    database_url: str = "sqlite:///./careerlens.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "development-only-change-me"
    access_token_expire_minutes: int = 720
    storage_dir: str = "./storage"
    max_upload_mb: int = 10
    frontend_url: str = "http://localhost:8501"
    admin_email: str = "admin@careerlens.local"
    admin_password: str = "ChangeThisAdminPassword!123"
    ocr_languages: str = "eng"
    guest_uploads_per_hour: int = 5
    user_uploads_per_hour: int = 20
    login_attempts_per_15min: int = 10
    registration_attempts_per_hour: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

from pathlib import Path

import pytest
pytest.importorskip("celery")
pytest.importorskip("redis")
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.core.config import settings
from backend.app.main import app
import backend.app.main as main_module
import backend.app.routes.auth as auth_routes
import backend.app.routes.resumes as resume_routes


@pytest.fixture()
def client(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(main_module, "initialize_database", lambda: None)
    monkeypatch.setattr(auth_routes, "apply_rate_limit", lambda *args, **kwargs: None)
    monkeypatch.setattr(resume_routes, "apply_rate_limit", lambda *args, **kwargs: None)
    monkeypatch.setattr(resume_routes.process_resume, "delay", lambda resume_id: None)
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path / "storage"))

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register_and_login(client: TestClient, email: str) -> str:
    register = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Test User", "email": email, "password": "StrongPass123!"},
    )
    assert register.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123!"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def test_resume_data_is_private_between_users(client: TestClient):
    token_a = register_and_login(client, "user-a@example.com")
    token_b = register_and_login(client, "user-b@example.com")

    upload = client.post(
        "/api/v1/resumes/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("sample.pdf", b"%PDF-1.4\nsynthetic resume content for privacy test", "application/pdf")},
    )
    assert upload.status_code == 202
    resume_id = upload.json()["id"]

    own_resume = client.get(
        f"/api/v1/resumes/{resume_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert own_resume.status_code == 200

    other_user_resume = client.get(
        f"/api/v1/resumes/{resume_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert other_user_resume.status_code == 404

    other_user_download = client.get(
        f"/api/v1/resumes/{resume_id}/download",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert other_user_download.status_code == 404


def test_guest_endpoint_is_available_but_not_persisted(client: TestClient):
    # The guest quota dependency is patched here; upload storage is still temporary.
    import backend.app.routes.guest as guest_routes

    # The dependency itself is attached to the route at definition time, so override it.
    app.dependency_overrides[guest_routes.limit_guest_analysis] = lambda: None
    response = client.post(
        "/api/v1/guest/analyze",
        files={"file": ("guest.pdf", b"%PDF-1.4\nSkills Python SQL Git Projects Experience Education", "application/pdf")},
    )
    # A header-only PDF has no parseable page structure, so parsing should fail cleanly.
    assert response.status_code in (400, 422)
    assert not list((Path(settings.storage_dir) / "guest").glob("*"))


def test_user_can_delete_account_and_resume_file(client, tmp_path):
    token = register_and_login(client, "delete-user@example.com")
    upload = client.post(
        "/api/v1/resumes/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("delete-me.pdf", b"%PDF-1.4\nsynthetic resume content for deletion test", "application/pdf")},
    )
    assert upload.status_code == 202
    resume_id = upload.json()["id"]
    stored_files = list((tmp_path / "storage" / "1").glob("*"))
    assert stored_files

    deleted = client.request(
        "DELETE",
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "StrongPass123!"},
    )
    assert deleted.status_code == 204
    assert not stored_files[0].exists()
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401

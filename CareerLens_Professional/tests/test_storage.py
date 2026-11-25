import pytest
from pathlib import Path
from fastapi import HTTPException
from backend.app.services.storage import validate_and_store

def test_rejects_empty_upload():
    with pytest.raises(HTTPException) as exc:
        validate_and_store(b"", "resume.pdf", "test")
    assert exc.value.status_code == 400

def test_rejects_wrong_extension():
    with pytest.raises(HTTPException) as exc:
        validate_and_store(b"hello", "resume.exe", "test")
    assert exc.value.status_code == 415

def test_rejects_fake_pdf():
    with pytest.raises(HTTPException) as exc:
        validate_and_store(b"not a pdf", "resume.pdf", "test")
    assert exc.value.status_code == 400

def test_accepts_valid_png_resume(tmp_path, monkeypatch):
    import io
    from PIL import Image
    from backend.app.core.config import settings

    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    image_bytes = io.BytesIO()
    Image.new("RGB", (400, 600), "white").save(image_bytes, format="PNG")
    stored = validate_and_store(image_bytes.getvalue(), "resume.png", owner_id=42)
    assert stored["mime_type"] == "image/png"
    assert Path(stored["file_path"]).exists()


def test_rejects_image_extension_content_mismatch(tmp_path, monkeypatch):
    import io
    from PIL import Image
    from backend.app.core.config import settings

    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    image_bytes = io.BytesIO()
    Image.new("RGB", (400, 600), "white").save(image_bytes, format="JPEG")
    with pytest.raises(HTTPException) as exc:
        validate_and_store(image_bytes.getvalue(), "resume.png", owner_id=42)
    assert exc.value.status_code == 400

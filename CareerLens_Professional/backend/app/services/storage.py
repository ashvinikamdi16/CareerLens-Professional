from pathlib import Path
from uuid import uuid4
import hashlib, io, zipfile
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException
from backend.app.core.config import settings

ALLOWED = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}

def validate_and_store(data: bytes, original_filename: str, owner_id: int | str, max_mb: int | None = None) -> dict:
    suffix = Path(original_filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(415, "Unsupported format. Upload PDF, DOCX, JPG, JPEG or PNG.")
    limit = (max_mb or settings.max_upload_mb) * 1024 * 1024
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    if len(data) > limit:
        raise HTTPException(413, f"File is larger than the {max_mb or settings.max_upload_mb} MB limit.")

    mime = ALLOWED[suffix]
    if suffix == ".pdf" and not data.startswith(b"%PDF-"):
        raise HTTPException(400, "The file does not appear to be a valid PDF.")
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names = zf.namelist()
                if "word/document.xml" not in names:
                    raise ValueError("Missing Word document content")
                # Guard against oversized compressed entries (basic ZIP-bomb defence).
                total_uncompressed = sum(info.file_size for info in zf.infolist())
                if total_uncompressed > 50 * 1024 * 1024:
                    raise ValueError("DOCX expands beyond the 50 MB processing limit")
        except Exception:
            raise HTTPException(400, "The DOCX file is invalid or corrupted.")
    if suffix in {".jpg", ".jpeg", ".png"}:
        try:
            with Image.open(io.BytesIO(data)) as img:
                expected_format = "JPEG" if suffix in {".jpg", ".jpeg"} else "PNG"
                if img.format != expected_format:
                    raise HTTPException(400, f"File extension does not match image content. Expected {expected_format}.")
                width, height = img.size
                img.verify()
                if width < 150 or height < 150:
                    raise HTTPException(400, "Image resolution is too small. Upload a clearer image.")
                if width * height > 40_000_000:
                    raise HTTPException(413, "Image dimensions are too large.")
        except HTTPException:
            raise
        except (UnidentifiedImageError, OSError, Exception):
            raise HTTPException(400, "The image is invalid or corrupted.")

    digest = hashlib.sha256(data).hexdigest()
    stored_name = f"{uuid4().hex}{suffix}"
    folder = Path(settings.storage_dir) / str(owner_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / stored_name
    path.write_bytes(data)
    return {"file_path": str(path), "stored_filename": stored_name, "mime_type": mime, "sha256": digest}

def remove_file(path: str) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass

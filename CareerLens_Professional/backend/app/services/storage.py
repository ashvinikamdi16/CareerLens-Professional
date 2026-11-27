from pathlib import Path
from uuid import uuid4
import hashlib, io, os, tempfile, zipfile
from urllib.parse import quote
import requests
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException
from backend.app.core.config import settings

ALLOWED = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
REMOTE_PREFIX = "supabase://"

def _supabase_config():
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    bucket = os.getenv("SUPABASE_BUCKET", "resumes")
    return (url, key, bucket) if url and key else None

def _headers(key: str):
    return {"Authorization": f"Bearer {key}", "apikey": key}

def _remote_parts(file_path: str):
    if not file_path.startswith(REMOTE_PREFIX):
        return None
    rest = file_path[len(REMOTE_PREFIX):]
    bucket, separator, object_name = rest.partition("/")
    if not separator or not bucket or not object_name:
        raise HTTPException(500, "Invalid cloud storage reference.")
    return bucket, object_name

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
                if sum(info.file_size for info in zf.infolist()) > 50 * 1024 * 1024:
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
        except Exception:
            raise HTTPException(400, "The image is invalid or corrupted.")

    digest = hashlib.sha256(data).hexdigest()
    stored_name = f"{uuid4().hex}{suffix}"
    remote = _supabase_config()
    if remote:
        url, key, bucket = remote
        object_name = f"{owner_id}/{stored_name}"
        endpoint = f"{url}/storage/v1/object/{quote(bucket, safe='')}/{quote(object_name, safe='/')}"
        headers = {**_headers(key), "Content-Type": mime, "x-upsert": "false"}
        try:
            response = requests.post(endpoint, headers=headers, data=data, timeout=45)
            if response.status_code not in (200, 201):
                raise HTTPException(502, f"Cloud storage upload failed ({response.status_code}). Check the Supabase bucket and service key.")
        except requests.RequestException as exc:
            raise HTTPException(502, "Could not connect to cloud storage. Please try again.") from exc
        return {"file_path": f"{REMOTE_PREFIX}{bucket}/{object_name}", "stored_filename": stored_name, "mime_type": mime, "sha256": digest}

    # Local fallback is useful for development, but Render's free filesystem is ephemeral.
    folder = Path(settings.storage_dir) / str(owner_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / stored_name
    path.write_bytes(data)
    return {"file_path": str(path), "stored_filename": stored_name, "mime_type": mime, "sha256": digest}

def materialize_file(file_path: str) -> tuple[str, bool]:
    parts = _remote_parts(file_path)
    if not parts:
        return file_path, False
    bucket, object_name = parts
    config = _supabase_config()
    if not config:
        raise HTTPException(503, "Supabase Storage is not configured on the backend.")
    url, key, _ = config
    endpoint = f"{url}/storage/v1/object/{quote(bucket, safe='')}/{quote(object_name, safe='/')}"
    try:
        response = requests.get(endpoint, headers=_headers(key), timeout=45)
        if response.status_code != 200:
            raise HTTPException(502, f"Cloud resume download failed ({response.status_code}).")
        suffix = Path(object_name).suffix
        with tempfile.NamedTemporaryFile(prefix="careerlens-", suffix=suffix, delete=False) as tmp:
            tmp.write(response.content)
            return tmp.name, True
    except requests.RequestException as exc:
        raise HTTPException(502, "Could not connect to cloud storage.") from exc

def cleanup_materialized_file(path: str, is_temporary: bool) -> None:
    if is_temporary:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass

def read_stored_file(file_path: str) -> bytes:
    path, temporary = materialize_file(file_path)
    try:
        return Path(path).read_bytes()
    finally:
        cleanup_materialized_file(path, temporary)

def remove_file(path: str) -> None:
    parts = _remote_parts(path)
    if parts:
        config = _supabase_config()
        if not config:
            return
        bucket, object_name = parts
        url, key, _ = config
        endpoint = f"{url}/storage/v1/object/{quote(bucket, safe='')}"
        try:
            requests.delete(endpoint, headers={**_headers(key), "Content-Type": "application/json"}, json={"prefixes": [object_name]}, timeout=30)
        except requests.RequestException:
            pass
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass

# Render deployment notes for CareerLens

This repository keeps the application under `CareerLens_Professional/`. Configure the Render API service with that directory as its **Root Directory**.

## API service

- Runtime: Python 3
- Root Directory: `CareerLens_Professional`
- Build Command:

```bash
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin && pip install -r requirements.txt
```

- Start Command:

```bash
alembic upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

The Tesseract packages are required for scanned PDFs and JPG/PNG resume OCR. Text-based PDFs and DOCX files do not require OCR.

## Persistent resume files

Render services have an ephemeral filesystem by default. Without a persistent disk, uploaded originals can disappear after a restart or deploy even though their database rows remain.

For a single-instance demo deployment:

1. Open the `careerlens-backend` service in Render.
2. Open **Disks** and add a disk with mount path `/var/data`.
3. In the service's Environment settings, set `STORAGE_DIR=/var/data/resumes`.
4. Save and wait for the service to redeploy.

Only files written under the disk mount path persist. A Render disk is attached to one service instance and prevents scaling that service to multiple instances. For horizontally scaled production use private object storage (S3-compatible) instead.

## Required API environment variables

Set these in the Render API service's Environment page (never commit real values):

- `APP_ENV=production`
- `DATABASE_URL`: Render PostgreSQL internal connection URL
- `REDIS_URL`: Render Redis/Key Value connection URL (used for rate limiting)
- `SECRET_KEY`: unique random secret, at least 32 characters
- `ADMIN_PASSWORD`: unique strong password
- `STORAGE_DIR=/var/data/resumes`
- `FRONTEND_URL`: deployed Streamlit URL

Keep `API_BASE_URL` in Streamlit Cloud secrets and set it to the Render API base URL ending in `/api/v1`. Do not paste secret values into GitHub or chat.

## Streamlit frontend

- Repository: `ashvinikamdi16/CareerLens-Professional`
- Branch: `main` after the fix PR is merged
- Main file path: `CareerLens_Professional/frontend/app.py`
- Streamlit secrets: `API_BASE_URL = "https://YOUR-RENDER-API.onrender.com/api/v1"`

After deploying, test registration/login, then upload a small text-based PDF and confirm:
- Upload returns a completed status.
- Resume History lists the file.
- Opening the record shows analysis.
- Download original resume works.
- The file remains downloadable after a backend redeploy.

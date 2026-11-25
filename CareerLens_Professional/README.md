# CareerLens Professional

A multi-user resume analysis and career recommendation web application built with Streamlit, FastAPI, PostgreSQL, Redis/Celery, OCR and NLP/ML techniques.

> **Status:** This is a runnable academic/professional starter implementation. It includes the main application flow, authentication, private per-user resume records, PDF/DOCX/image parsing, OCR, hybrid job matching, reports, admin statistics, tests and Docker deployment. A real public production launch still requires hosting, domain, secure secrets, monitoring, backups, privacy/legal review and load testing.

## Main capabilities

- Public website interface; anyone can open it using the deployed URL.
- Guest resume analysis without creating an account (temporary processing; no resume history saved).
- Registration/login for saved resume history.
- Per-user authorization: users can only view, download, analyse or delete their own resumes.
- PDF, DOCX, JPG, JPEG and PNG uploads. Scanned PDFs and images use Tesseract OCR.
- Upload validation: extension, file signature/content, size, image verification, duplicate detection and empty-text handling.
- Background resume analysis through Celery + Redis.
- NLP-assisted skill extraction and normalization, a transparent CareerLens Readiness Score, TF-IDF job matching and explainable recommendations.
- Resume history, re-analysis, downloadable original files, PDF analysis reports and owner-only manual correction of OCR/extracted text.
- Redis-backed starter quotas: 5 guest analyses per IP/hour, 20 signed-in uploads per user/hour and login/register abuse throttles.
- Admin statistics endpoint/UI.
- Docker Compose stack: PostgreSQL, Redis, FastAPI API, Celery worker and Streamlit frontend.

## Architecture

```text
Browser (Chrome / Edge / Firefox / Brave / Opera / Safari)
                         |
                  Streamlit frontend
                         | HTTP API
                      FastAPI
              /           |           \\
       PostgreSQL     Private files     Redis queue
                          |                |
                    PDF/DOCX/OCR       Celery worker
                          |                |
                     NLP/ML analysis -----+
```

Streamlit and FastAPI are separate services. A deployed Streamlit app calls the deployed API URL. The Celery worker and API share the private storage volume and database.

## 1. Run locally with Docker (recommended)

### Requirements

- Docker Desktop with Docker Compose enabled
- Git (for team collaboration)

### Steps

1. Copy `.env.example` to `.env` (`Copy-Item .env.example .env` in Windows PowerShell, or `cp .env.example .env` on macOS/Linux).
2. Change `SECRET_KEY` and `ADMIN_PASSWORD` to long, unique values. Do not commit `.env` to GitHub.
3. Open a terminal in this folder and run:

```bash
docker compose up --build
```

4. Open the frontend at **http://localhost:8501**.
5. Open interactive API docs at **http://localhost:8000/docs**.
6. Register a normal user in the website. The admin account is created from `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env`.

To stop the application:

```bash
docker compose down
```

To stop and delete local database, Redis and uploaded-resume volumes (destructive):

```bash
docker compose down -v
```

## Public website deployment on one VPS

For a first public deployment, use a Linux VPS with Docker Compose and a domain name. Point the domain's DNS A record to the VPS public IP, set `DOMAIN` and `FRONTEND_URL` in `.env`, change all passwords/secrets, allow inbound ports 80 and 443, then run:

```bash
docker compose --profile public up --build -d
```

Caddy reverse-proxies the website and API and obtains HTTPS certificates for a real domain automatically. The public URL is `https://YOUR_DOMAIN`. Do not publish a public site until secrets, database credentials, backups, retention policy, storage permissions and resource limits have been reviewed. Keep the database and Redis ports private; this Compose file exposes only the API/UI ports for local development and the optional Caddy entrypoint for public deployment. The API and frontend host ports are bound to localhost only; only Caddy exposes ports 80/443 in public mode.

This single-host arrangement is suitable for an initial controlled release. For multi-server scaling, replace the shared local resume volume with private object storage (S3-compatible), use managed PostgreSQL/Redis, and add monitoring, backup/restore drills and an external rate-limit/abuse layer.

## 2. Run without Docker (developer mode)

Use Python 3.11. Create and activate a virtual environment, then:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

Install and start PostgreSQL and Redis separately, configure `.env`, run `alembic upgrade head`, and make sure the Tesseract executable is installed. For English OCR install the English language data; for Hindi OCR also install Hindi language data. The included API Docker image installs English and Hindi Tesseract language packs. Then start three terminals:

```bash
# Terminal 1: API
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: background worker
celery -A backend.app.celery_app.celery_app worker --loglevel=INFO

# Terminal 3: Streamlit
streamlit run frontend/app.py
```

On Windows, Celery's prefork pool can be problematic. For local Windows-only development use `celery -A backend.app.celery_app.celery_app worker --pool=solo --loglevel=INFO`, or use Docker Desktop/WSL2.

## Supported uploads

- PDF (`.pdf`)
- Microsoft Word DOCX (`.docx`)
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)

Legacy `.doc`, HEIC and handwritten resumes are not supported in this version. Image-only/scanned PDF pages are sent through OCR. OCR output depends on image quality and installed language packs. Users can review the extracted information and correct mistakes in a future enhancement; the current version reports extraction warnings when no readable text is found.

Default maximum file size is 10 MB for signed-in users and 5 MB for guest analysis. Change `MAX_UPLOAD_MB` in `.env` carefully after capacity testing.

## Multi-user behaviour

- Each account has its own user ID.
- Resume rows are linked to their owner in the database.
- All resume read/download/delete/report endpoints check ownership.
- Uploaded originals are stored under generated UUID names, not user-supplied paths.
- Signed-in resume analysis is queued and processed by Celery workers, so multiple users can submit work without making every browser wait for the entire analysis. The included Compose setup starts with two worker processes; tune `WORKER_CONCURRENCY` to the server's CPU/RAM after testing.
- Guest analysis is temporary and synchronous; its temporary file is deleted after processing. Guest uploads are limited by a shared Redis counter.
- An account owner can delete an individual resume or delete their entire account and associated resume records/files.

**Concurrent user capacity is not a fixed number in source code.** It depends on CPU/RAM, database connection limits, worker count, file size, OCR load and hosting. Use `locustfile.py` to measure it on the actual deployed server before claiming a capacity such as 25, 50 or 100 concurrent users. Start with a small test and increase gradually.

## Environment variables

See `.env.example`. Important settings:

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Docker PostgreSQL credentials. Use a long URL-safe password for this starter Compose URL.
- `DATABASE_URL`: PostgreSQL connection string.
- `REDIS_URL`: Redis connection string for Celery.
- `SECRET_KEY`: private JWT signing secret; change before deployment.
- `ADMIN_EMAIL`, `ADMIN_PASSWORD`: first admin account.
- `STORAGE_DIR`: private resume storage path.
- `FRONTEND_URL`: allowed frontend origin for CORS.
- `MAX_UPLOAD_MB`: signed-in upload limit.
- `GUEST_UPLOADS_PER_HOUR` and `USER_UPLOADS_PER_HOUR`: shared upload quotas.
- `LOGIN_ATTEMPTS_PER_15MIN` and `REGISTRATION_ATTEMPTS_PER_HOUR`: authentication abuse controls.
- `WORKER_CONCURRENCY`: Celery worker parallelism in Docker Compose.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Create user |
| POST | `/api/v1/auth/login` | Login and receive JWT |
| GET | `/api/v1/auth/me` | Current user |
| DELETE | `/api/v1/auth/me` | Delete current account and owned resume data (password confirmation) |
| POST | `/api/v1/guest/analyze` | Temporary guest analysis |
| POST | `/api/v1/resumes/upload` | Save and queue a resume |
| GET | `/api/v1/resumes` | List current user's resumes |
| GET | `/api/v1/resumes/{id}` | Resume status and latest analysis |
| POST | `/api/v1/resumes/{id}/reanalyze` | Queue a new analysis |
| GET | `/api/v1/resumes/{id}/recommendations` | Matched jobs |
| GET | `/api/v1/resumes/{id}/download` | Download original (owner only) |
| GET | `/api/v1/resumes/{id}/report` | Download PDF report (owner only) |
| DELETE | `/api/v1/resumes/{id}` | Delete resume and associated analysis |
| GET | `/api/v1/jobs` | Browse sample jobs |
| GET | `/api/v1/admin/stats` | Admin-only system statistics |

## AI/ML transparency

This implementation uses a skill taxonomy with rule-based/NLP extraction, scikit-learn TF-IDF vectorization and cosine similarity, plus a transparent weighted ranking score. It does **not** claim to be a generative AI model or a proprietary ATS. The readiness score is CareerLens's own heuristic score and must be validated against a reviewed dataset before being treated as a reliable assessment. Results are decision support, not a hiring decision.

## Tests

```bash
python -m pytest -q
```

## Load testing

Install `locust` (included in `requirements-dev.txt`) and run:

```bash
locust -f locustfile.py --host http://localhost:8000
```

Open the Locust UI URL shown in the terminal, start with a small number of users, and measure error rate, median/95th percentile latency and throughput. Do not run aggressive load tests against a public site without permission.

## GitHub team workflow

See `docs/TEAM_WORKFLOW.md`. Each member uses a separate branch and owns separate folders. Changes are merged to `main` through Pull Requests after local tests and review. Never push `.env`, real resumes, secrets or private user data.

## Before public production launch

1. Use managed PostgreSQL, Redis and private object storage with backups.
2. Deploy the API and worker privately; expose only HTTPS endpoints.
3. Configure real domain, TLS, CORS allowlist and production secret values.
4. Add CAPTCHA/bot protection, file malware scanning, monitoring and alerting; the starter already has Redis-backed guest and signed-in upload quotas, which must still be tuned for the selected hosting plan.
5. Review privacy notice, consent, retention/deletion policy and applicable law before accepting real people's resumes.
6. Run security testing and load testing on the selected hosting plan.
7. Configure database migrations and automated backups/restore drills.
8. Do not put the API, database or resume storage credentials in frontend code.

The code is deployable, but a live public URL cannot be created from this source package alone: it requires a domain, server/hosting account, credentials and deployment configuration controlled by the project team. The included sample job catalogue is demonstration data with placeholder `example.com` application links; load verified, licensed job data before presenting it as live vacancies.

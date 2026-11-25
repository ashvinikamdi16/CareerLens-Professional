# Viva preparation notes

## Explain the project

CareerLens is a multi-user web application that accepts PDF, DOCX and image resumes, extracts content, identifies skills, estimates resume readiness, finds skill gaps and recommends sample jobs. It has separate frontend, API, database and background-worker services.

## Technologies

- Streamlit: browser UI.
- FastAPI: REST API.
- PostgreSQL/SQLAlchemy: persistent user, resume, job and analysis records.
- JWT + Argon2 password hashing: authentication.
- Redis + Celery: queued background processing.
- PyMuPDF/python-docx: PDF and DOCX extraction.
- Tesseract OCR: text recognition from JPG/JPEG/PNG images and scanned PDF pages.
- Argon2id: password hashing before storage.
- Redis fixed-window counters: shared rate limits for public guest analysis and authenticated uploads.
- scikit-learn TF-IDF + cosine similarity: text matching.
- ReportLab: downloadable report generation.
- Docker Compose: local multi-service environment.

## What makes the system multi-user?

Each registered account has a distinct database user ID. Resume records store `owner_id`; all user-facing access routes filter by the authenticated owner. Upload tasks are queued separately and handled by workers. Guest analysis is available without login but the temporary upload is deleted after processing. The actual simultaneous-user limit is measured through load testing on the selected hosting resources, not assumed.

## Is it fully AI?

Do not claim that every part is AI or that the project uses a proprietary ATS. This implementation combines conventional software engineering, OCR, NLP skill extraction and ML-style TF-IDF/cosine similarity. The readiness score is a custom heuristic. Explain the algorithm honestly and show source code and test results.

## Team contributions

Member 1: Streamlit user experience and API integration.
Member 2: FastAPI endpoints, authentication and authorization.
Member 3: document extraction, OCR and skill/job matching functions.
Member 4: database, test cases, Docker, load testing and deployment verification.

Each member should be able to explain the module they actually implemented and show their commits/PRs.

## Important limitations to state honestly

- The starter uses sample job records, not live verified vacancies or a production job API.
- The readiness score is a transparent project-defined heuristic, not an employer's ATS score.
- OCR can misread low-quality images; users should review extracted text.
- The current parser extracts contact fields and education mentions, but is not a perfect structured CV parser.
- Email verification, password reset, CAPTCHA, antivirus scanning and an external job feed are production enhancements, not included claims.
- The tested concurrent-user capacity must be measured on the actual deployed host with the included Locust script.

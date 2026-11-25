# CareerLens implementation status and remaining work

## Implemented in this source package

- Public web UI entry point with guest analysis and registered-user workflows.
- JWT login/register, Argon2id password hashing and admin role.
- Owner-scoped resume history, download, re-analysis, deletion and account deletion.
- PDF, DOCX, JPG, JPEG and PNG uploads with file-size, extension, signature/content, duplicate and basic ZIP expansion checks.
- Digital PDF and DOCX text extraction, plus Tesseract OCR for images and scanned PDF pages.
- OCR confidence metadata, parse errors and owner-only extracted-text correction.
- Celery/Redis background processing for saved resumes.
- Skill taxonomy/alias matching, contact and education-mention extraction, a transparent readiness heuristic and TF-IDF/cosine plus skill-overlap job ranking.
- Sample job browser, user dashboard, admin aggregate statistics and PDF analysis report.
- Shared Redis rate limits, PostgreSQL migrations, Docker Compose and optional Caddy HTTPS reverse proxy.
- Unit tests, API multi-user privacy tests (run when all app dependencies are installed), OCR/PDF parser tests and a Locust load-test script.

## Known limitations / future production work

1. The bundled job catalogue is demonstration data. It is not a live vacancy feed, and its `example.com` links are placeholders. Load a verified and licensed source before using it as a real job service.
2. Job matching is currently explainable TF-IDF/cosine similarity plus skill overlap. A transformer embedding model, trained ranking model or LLM explanation layer is not included. Do not describe it as a generative-AI model.
3. The CareerLens Readiness Score is a project-defined heuristic, not a proprietary ATS score. It needs labelled evaluation data and expert review before being presented as reliable.
4. Contact and education extraction are rule-based/regex-assisted and may miss unusual resume formats. Users must review extracted details.
5. OCR depends on image quality and installed Tesseract language packs. Handwriting, rotated/blurred images, HEIC, legacy DOC and multi-image batch resumes are not supported by this release.
6. Email verification, password reset, CAPTCHA, malware scanning, formal audit monitoring and a complete legal/privacy workflow are not included yet.
7. Docker Compose uses a shared local volume for uploaded files and is intended for a single host. Multi-node deployment needs private shared object storage, managed Redis/PostgreSQL, backup/restore drills and monitoring.
8. The default worker concurrency is two. Simultaneous-user capacity depends on CPU, RAM, OCR intensity, worker count, DB connections and hosting. It must be measured using Locust on the actual server before publishing a capacity claim.
9. A live public URL is not included. The team must supply a domain, VPS/cloud account, secrets, DNS and deployment access.

## Acceptance tests before a public demo

- Guest can upload a sample PDF, DOCX and clear image; guest file is removed after processing.
- Two normal users can register and upload distinct test resumes at the same time.
- User A cannot list, view, download, edit or delete User B's resume by guessing an ID.
- Blank, corrupt, unsupported, oversized and duplicate files return understandable errors.
- A scanned PDF and a JPG image are OCR-processed; the user can correct OCR text.
- Queued, processing, completed and failed states are visible in the UI.
- Account deletion removes that account's resumes and stored original files.
- Worker restart and database backup/restore procedures are tested.
- Locust results are recorded with host size, test duration, concurrent users, error rate, median latency and p95 latency.

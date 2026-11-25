# Publish CareerLens on the public internet

This package includes a public-mode Docker Compose profile with Caddy as the HTTPS reverse proxy. This is a first single-VPS deployment pattern, not a promise of unlimited capacity.

## Needed

- Linux VPS with enough CPU/RAM/disk for OCR + worker processing.
- Domain name with DNS A record pointing to the VPS IP.
- Docker Engine and Compose plugin installed.
- Inbound TCP 80/443 allowed in the VPS firewall.

## Steps

1. Upload the repository to the VPS or clone it from GitHub.
2. Copy `.env.example` to `.env`.
3. Set `APP_ENV=production`, `DOMAIN=your-real-domain.example`, `FRONTEND_URL=https://your-real-domain.example`, a unique `SECRET_KEY` of at least 32 characters, a new `ADMIN_PASSWORD`, and unique `POSTGRES_PASSWORD` (use URL-safe alphanumeric characters for this starter Compose connection string). Production startup rejects the known development secret and default admin password.
4. Keep PostgreSQL, Redis, API and frontend internal to Docker. API and frontend are bound to host loopback only; Caddy reaches them over the internal Docker network.
5. Run `docker compose --profile public up --build -d`.
6. Visit `https://your-real-domain.example`; Caddy requests and renews certificates automatically when DNS and ports are correct.
7. Verify `/health`, register a normal user, upload synthetic test files, test cross-account privacy and inspect worker/API logs.

## Operational checklist

- Set a strong secret and admin password; rotate them if exposed.
- Configure encrypted backups for PostgreSQL and resume storage, and test restoration.
- Set disk monitoring and a retention/deletion policy for resumes and guest temp files.
- Keep logs free of resume text, passwords and tokens.
- Apply OS security updates and restrict SSH.
- Do not claim a concurrent-user limit until Locust tests are run on this exact VPS size using representative synthetic files (including OCR-heavy scanned PDFs). For authenticated upload load tests, create a dedicated test account, set `CL_LOADTEST_EMAIL` and `CL_LOADTEST_PASSWORD`, and raise `USER_UPLOADS_PER_HOUR` and `LOGIN_ATTEMPTS_PER_15MIN` only in the isolated test environment.
- For multi-node API/worker scaling, replace local `resume_storage` with private shared object storage and use managed PostgreSQL/Redis.
- Publish a privacy notice explaining what data is collected, why, where it is stored, retention period and how users can request deletion.

# Four-member GitHub workflow

Use one shared GitHub repository. Give each member Write access. Protect `main` so direct pushes are discouraged and changes arrive through Pull Requests.

## Ownership

| Member | Area | Example branch |
|---|---|---|
| 1 | Streamlit frontend and API client | `feature/frontend` |
| 2 | FastAPI routes, authentication and API integration | `feature/backend` |
| 3 | Resume parsing, OCR and NLP/ML matching | `feature/ai-engine` |
| 4 | Database, tests, Docker and deployment checks | `feature/database-qa` |

## Safe working steps

```bash
git clone YOUR_REPOSITORY_URL
cd CareerLens_Professional
git checkout -b feature/your-module
# Edit only your assigned folder, then run relevant tests.
git add .
git commit -m "Implement your module"
git push -u origin feature/your-module
```

Open a Pull Request on GitHub, add a team member as reviewer, resolve comments, then merge. Before starting new work:

```bash
git checkout main
git pull origin main
git checkout feature/your-module
git merge main
```

Avoid editing the same file simultaneously. Agree on API contracts before integration. Member 2 owns endpoint contracts; Member 3 exposes pure Python functions; Member 4 owns schema changes/migrations and verifies tests; Member 1 calls the API through `frontend/app.py`.

## Shared API contract

- JSON uses `snake_case` field names.
- Signed-in routes use `Authorization: Bearer <JWT>`.
- Resume upload uses multipart form field `file`.
- Upload returns a resume ID and status `queued`.
- Frontend polls `GET /api/v1/resumes/{id}` for status and analysis.
- Do not commit `.env`, API keys, production passwords, real resumes or user data.

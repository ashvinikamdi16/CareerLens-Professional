# Architecture and data flow

## Signed-in flow

1. Browser renders the Streamlit application.
2. User registers/logs in; FastAPI returns a signed JWT.
3. Frontend sends the JWT in the Authorization header.
4. User uploads PDF/DOCX/JPG/JPEG/PNG; API validates extension, signature, content and size.
5. API stores the file under a generated name in private storage and creates a `Resume` row tied to `owner_id`.
6. API submits the resume ID to Celery through Redis and returns `queued`.
7. Worker loads the file, extracts text (PDF/DOCX parser or OCR), runs the analysis and writes an `AnalysisResult` row.
8. User refreshes history; API checks ownership and returns status/result.

## Guest flow

Guest analysis is limited to 5 MB, processed synchronously and stored only in a temporary generated path. The file is deleted in a `finally` block. No history is created.

## Data model

- `users`: identity, password hash and role.
- `resumes`: owner, generated file location, checksum, processing state.
- `analysis_results`: versioned structured results and extracted text.
- `jobs`: demonstration jobs and required skills.

## Multi-user isolation

Every user-specific resume query filters by both resume ID and authenticated owner ID. Original files are not placed in a public static directory. Storage names are UUIDs, not user-provided filenames. Admin statistics contain aggregate counts only.

## Processing limitations

The current worker extracts skills using a maintained alias taxonomy. Text similarity uses scikit-learn TF-IDF and cosine similarity. It does not include a trained deep neural network or an LLM call. Add and evaluate those models only when there is a clear labelled dataset, licensing approval and deployment capacity.

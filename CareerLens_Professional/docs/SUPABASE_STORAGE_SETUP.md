# Supabase Storage setup for CareerLens

CareerLens can store uploaded resume files in a private Supabase Storage bucket instead of the Render web service filesystem. The PostgreSQL database continues to store user accounts, resume metadata and analysis results.

## 1. Create a private bucket

1. Create or open a project at https://supabase.com/dashboard.
2. Open **Storage** and choose **New bucket**.
3. Name it exactly `resumes`.
4. Keep **Public bucket** turned OFF (private bucket).
5. Create the bucket. Do not add public read policies; the backend accesses it with its server-side service-role key.

## 2. Add Render environment variables

Open Render → `careerlens-backend` → **Environment** and add:

- `SUPABASE_URL`: Project URL from Supabase → Project Settings → API.
- `SUPABASE_SERVICE_ROLE_KEY`: service_role key from Supabase → Project Settings → API Keys. Treat this as a password; never put it in Streamlit secrets, GitHub, or frontend code.
- `SUPABASE_BUCKET`: `resumes`

Save changes and wait for the backend to redeploy. Do not share the service-role key in chat or screenshots.

## 3. Verify

1. Open the deployed CareerLens website and sign in.
2. Upload a small PDF or DOCX.
3. Confirm analysis completes and the resume appears in Resume History.
4. Download the resume from its history entry.
5. In Supabase → Storage → resumes, confirm an object appears under the user's numeric folder.

## Important notes

- New uploads are stored in Supabase only after all three environment variables are set and the backend has redeployed.
- Existing files that were uploaded to Render's temporary local filesystem are not copied automatically. Their database records may remain, but the old file itself may already be unavailable after a restart/redeploy.
- Guest uploads remain temporary and are deleted after analysis.
- Never expose the service-role key in the Streamlit app or browser.
- Supabase Storage has plan-specific quotas and limits; monitor usage in the Supabase dashboard.
- The backend retains local storage as a development fallback when Supabase variables are absent. On Render Free, that fallback is ephemeral and should not be used for permanent resume storage.

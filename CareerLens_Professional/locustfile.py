import os
import uuid
from locust import HttpUser, task, between
import fitz


def synthetic_pdf(label: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), f"Synthetic test resume {label}. Skills Python SQL Git FastAPI. Education BTech Computer Science. Projects built REST APIs and data dashboards. Experience entry level.")
    content = document.tobytes()
    document.close()
    return content


class CareerLensUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.token = None
        self.counter = 0
        self.client.get("/health", name="health")
        email = os.getenv("CL_LOADTEST_EMAIL")
        password = os.getenv("CL_LOADTEST_PASSWORD")
        if email and password:
            response = self.client.post("/api/v1/auth/login", json={"email": email, "password": password}, name="login")
            if response.status_code == 200:
                self.token = response.json().get("access_token")

    @task(4)
    def health_check(self):
        self.client.get("/health", name="health")

    @task(3)
    def browse_jobs(self):
        self.client.get("/api/v1/jobs", name="list jobs")

    @task(1)
    def upload_synthetic_resume(self):
        if not self.token:
            return
        self.counter += 1
        token = self.token
        payload = synthetic_pdf(f"{uuid.uuid4().hex}-{self.counter}")
        self.client.post(
            "/api/v1/resumes/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (f"synthetic-{self.counter}.pdf", payload, "application/pdf")},
            name="upload synthetic resume",
        )

# Create a dedicated test account first, then set CL_LOADTEST_EMAIL and
# CL_LOADTEST_PASSWORD. Tune USER_UPLOADS_PER_HOUR in a separate test environment.
# Never use real resumes or run high-volume tests against a site without permission.

import os
import time
import requests
import streamlit as st

st.set_page_config(page_title="CareerLens | Resume Intelligence", page_icon="🎯", layout="wide")
API = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px;}
.hero {padding: 1.5rem 1.7rem; border-radius: 18px; background: linear-gradient(120deg,#101c3a,#243f73); color: white; margin-bottom: 1rem;}
.hero p {color:#d9e4ff; margin-bottom:0;}
.small-muted {color:#718096; font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

if "token" not in st.session_state: st.session_state.token = None
if "user" not in st.session_state: st.session_state.user = None
if "selected_resume" not in st.session_state: st.session_state.selected_resume = None

def api(method, path, **kwargs):
    headers = kwargs.pop("headers", {})
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        response = requests.request(method, f"{API}{path}", headers=headers, timeout=90, **kwargs)
        if response.status_code >= 400:
            try: detail = response.json().get("detail", response.text)
            except Exception: detail = response.text
            st.error(f"{detail}")
            return None
        return response
    except requests.RequestException as exc:
        st.error(f"Could not reach the CareerLens server: {exc}")
        return None

def show_analysis(result):
    score = result.get("readiness_score", 0)
    a, b, c = st.columns(3)
    a.metric("Resume readiness", f"{score}/100")
    b.metric("Skills identified", result.get("skill_count", 0))
    c.metric("Word count", result.get("word_count", 0))
    st.caption(result.get("score_label", "CareerLens heuristic score"))
    st.subheader("Extracted skills")
    skills = result.get("skills", [])
    st.write(" · ".join(skills) if skills else "No skills confidently identified.")
    profile = result.get("profile_summary", {})
    with st.expander("Review extracted profile details"):
        st.write("**Email:**", profile.get("email") or "Not detected")
        st.write("**Phone:**", profile.get("phone") or "Not detected")
        st.write("**Education mentions:**", "; ".join(profile.get("education_mentions", [])) or "Not detected")
        st.write("**Estimated experience:**", f"{profile['estimated_experience_years']} years" if profile.get("estimated_experience_years") is not None else "Not detected")
    st.subheader("Score breakdown")
    for key, value in result.get("score_breakdown", {}).items():
        st.write(f"**{key.replace('_', ' ').title()}** — {value}/100")
        st.progress(max(0, min(100, int(value))))
    not_detected = result.get("possible_missing_skills", [])
    if not_detected:
        st.caption("Other known skills not detected (these are not automatically required for your target role): " + ", ".join(not_detected))
    st.subheader("Improvement suggestions")
    for item in result.get("improvement_suggestions", []): st.write(f"- {item}")
    meta = result.get("parser_metadata", {})
    st.caption(f"Parser: {meta.get('parser', 'N/A')} | OCR used: {meta.get('ocr_used', False)}")
    for warning in result.get("limitations", []): st.caption(f"Note: {warning}")

def show_recommendations(items):
    st.subheader("Job recommendations")
    if not items:
        st.info("No sample jobs are currently available.")
        return
    for item in items:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{item['title']} — {item['company']}**")
            left.caption(f"{item['location']} · {item['experience_level']} · Source: {item.get('source','')}")
            right.metric("Match", f"{item['match_percentage']}%")
            st.write(item.get("match_explanation", ""))
            st.write("**Matched:** " + (", ".join(item.get("matched_skills", [])) or "None identified"))
            st.write("**Skills to build:** " + (", ".join(item.get("missing_skills", [])) or "No listed skill gaps"))
            url = item.get("apply_url")
            if url and "example.com" not in url:
                st.link_button("View opportunity", url)
            else:
                st.caption("Demonstration dataset entry — replace with verified live job listings before production.")

st.sidebar.title("🎯 CareerLens")
st.sidebar.caption("Resume Intelligence & Career Assistant")
if st.session_state.user:
    st.sidebar.success(f"Signed in: {st.session_state.user.get('full_name', '')}")
    pages = ["Dashboard", "Upload Resume", "Resume History", "Job Explorer", "Account Settings"]
    if st.session_state.user.get("is_admin"): pages.append("Admin Dashboard")
    page = st.sidebar.radio("Navigation", pages)
    if st.sidebar.button("Log out", use_container_width=True):
        st.session_state.token = None; st.session_state.user = None; st.session_state.selected_resume = None
        st.rerun()
else:
    page = st.sidebar.radio("Navigation", ["Home / Guest Analysis", "Login", "Register"])

if page == "Home / Guest Analysis":
    st.markdown('<div class="hero"><h1>CareerLens</h1><p>Understand your resume. Discover skill gaps. Explore career opportunities.</p></div>', unsafe_allow_html=True)
    st.write("Upload a PDF, Word document or a clear resume image. Guest analysis is temporary and the uploaded file is deleted after processing.")
    uploaded = st.file_uploader("Choose your resume", type=["pdf", "docx", "jpg", "jpeg", "png"], key="guest_file")
    if st.button("Analyze as guest", type="primary", disabled=uploaded is None):
        with st.spinner("Reading and analysing your resume. Image and scanned PDF files may take longer..."):
            response = api("POST", "/guest/analyze", files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")})
        if response:
            payload = response.json()
            st.success("Guest analysis completed. This result is not saved to a user account.")
            show_analysis(payload["analysis"])
            show_recommendations(payload.get("recommendations", []))
    st.info("Create a free account to save resumes, view analysis history, re-analyse files and download reports.")

elif page == "Login":
    st.title("Welcome back")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", type="primary")
    if submit:
        response = api("POST", "/auth/login", json={"email": email, "password": password})
        if response:
            st.session_state.token = response.json()["access_token"]
            me = api("GET", "/auth/me")
            if me: st.session_state.user = me.json(); st.rerun()

elif page == "Register":
    st.title("Create your CareerLens account")
    with st.form("register_form"):
        full_name = st.text_input("Full name")
        email = st.text_input("Email")
        password = st.text_input("Password (at least 10 characters)", type="password")
        submit = st.form_submit_button("Create account", type="primary")
    if submit:
        response = api("POST", "/auth/register", json={"full_name": full_name, "email": email, "password": password})
        if response:
            st.success("Account created. Please log in.")

elif page == "Dashboard":
    st.title("Your CareerLens dashboard")
    response = api("GET", "/resumes")
    resumes = response.json() if response else []
    a, b, c = st.columns(3)
    a.metric("Saved resumes", len(resumes))
    b.metric("Completed analyses", sum(1 for r in resumes if r["status"] == "completed"))
    c.metric("Pending / processing", sum(1 for r in resumes if r["status"] in ("queued", "processing")))
    st.write("Use **Upload Resume** to analyse a new document, or open **Resume History** to view past results.")
    st.caption("Your saved resumes are private to your account.")

elif page == "Upload Resume":
    st.title("Upload and save a resume")
    uploaded = st.file_uploader("PDF, DOCX, JPG, JPEG or PNG", type=["pdf", "docx", "jpg", "jpeg", "png"], key="signed_file")
    if st.button("Upload and analyse", type="primary", disabled=uploaded is None):
        with st.spinner("Uploading securely and submitting analysis job..."):
            response = api("POST", "/resumes/upload", files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")})
        if response:
            st.session_state.selected_resume = response.json()["id"]
            st.success(f"Resume saved. Analysis job queued (ID {response.json()['id']}). Open Resume History and refresh its status.")

elif page == "Resume History":
    st.title("Your resume history")
    if st.button("Refresh history"): st.rerun()
    response = api("GET", "/resumes")
    resumes = response.json() if response else []
    if not resumes: st.info("No saved resumes yet.")
    for item in resumes:
        with st.container(border=True):
            cols = st.columns([4, 2, 2, 2])
            cols[0].write(f"**{item['original_filename']}**")
            cols[1].write(item["status"].title())
            cols[2].write(item["created_at"][:10])
            if cols[3].button("Open", key=f"open_{item['id']}"):
                st.session_state.selected_resume = item["id"]
            if item.get("error_message"): st.warning(item["error_message"])
    selected = st.session_state.selected_resume
    if selected:
        detail = api("GET", f"/resumes/{selected}")
        if detail:
            payload = detail.json(); resume = payload["resume"]
            st.divider(); st.subheader(resume["original_filename"])
            if resume["status"] in ["queued", "processing"]:
                st.info("Analysis is still processing. Select Refresh history in a moment.")
            elif resume["status"] == "failed":
                st.error(resume.get("error_message") or "Analysis failed.")
                if st.button("Try analysis again", key=f"reanalyze_{selected}"):
                    api("POST", f"/resumes/{selected}/reanalyze"); st.rerun()
            elif payload.get("analysis"):
                show_analysis(payload["analysis"])
                with st.expander("Review or correct extracted resume text"):
                    corrected_text = st.text_area("Extracted text", value=payload.get("extracted_text") or "", height=220, key=f"correct_text_{selected}")
                    if st.button("Save correction and refresh analysis", key=f"correct_{selected}"):
                        correction = api("PATCH", f"/resumes/{selected}/correction", json={"corrected_text": corrected_text})
                        if correction:
                            st.success("Your corrected text was saved and re-analysed.")
                            st.rerun()
                rec = api("GET", f"/resumes/{selected}/recommendations")
                if rec: show_recommendations(rec.json().get("recommendations", []))
                d1, d2 = st.columns(2)
                if d1.button("Download original resume", key=f"dl_{selected}"):
                    file_response = api("GET", f"/resumes/{selected}/download")
                    if file_response: st.download_button("Save original file", file_response.content, file_name=resume["original_filename"])
                if d2.button("Prepare PDF analysis report", key=f"report_{selected}"):
                    report = api("GET", f"/resumes/{selected}/report")
                    if report: st.download_button("Download analysis report", report.content, file_name=f"CareerLens_Report_{selected}.pdf", mime="application/pdf")
            if st.button("Delete this resume and its analysis", key=f"delete_{selected}"):
                deleted = api("DELETE", f"/resumes/{selected}")
                if deleted is not None:
                    st.session_state.selected_resume = None; st.success("Resume deleted."); st.rerun()

elif page == "Job Explorer":
    st.title("Job explorer")
    q = st.text_input("Search job titles")
    response = api("GET", "/jobs", params={"q": q} if q else {})
    if response:
        for job in response.json():
            with st.container(border=True):
                st.markdown(f"**{job['title']} — {job['company']}**")
                st.caption(f"{job['location']} · {job['experience_level']} · {job['source']}")
                st.write(job["description"])
                st.write("Required skills: " + ", ".join(job["required_skills"]))
                st.caption("Sample demonstration data; replace with a verified job feed before production.")

elif page == "Account Settings":
    st.title("Account settings")
    st.write(f"Signed in as **{st.session_state.user.get('full_name', '')}** ({st.session_state.user.get('email', '')}).")
    st.warning("Deleting your account permanently deletes your saved resumes and analysis history. This cannot be undone.")
    with st.form("delete_account_form"):
        confirm_password = st.text_input("Confirm your password", type="password")
        confirm_delete = st.checkbox("I understand that my account data will be permanently deleted.")
        submitted = st.form_submit_button("Delete my account", type="secondary")
    if submitted:
        if not confirm_delete:
            st.error("Please confirm that you understand the deletion is permanent.")
        else:
            deletion = api("DELETE", "/auth/me", json={"password": confirm_password})
            if deletion is not None:
                st.session_state.token = None
                st.session_state.user = None
                st.session_state.selected_resume = None
                st.success("Your account and saved resume data have been deleted.")
                st.rerun()

elif page == "Admin Dashboard":
    st.title("Administrator dashboard")
    response = api("GET", "/admin/stats")
    if response:
        stats = response.json()
        cols = st.columns(4)
        for col, key in zip(cols, ["total_users", "total_resumes", "completed_resumes", "failed_resumes"]):
            col.metric(key.replace("_", " ").title(), stats[key])
        st.json(stats)

st.divider()
st.caption("CareerLens is a decision-support tool. Resume scores and job matches are estimates, not guarantees of employment or employer ATS decisions.")

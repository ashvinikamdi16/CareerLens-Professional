import os
import requests
import streamlit as st

st.set_page_config(page_title="CareerLens | Resume Intelligence", page_icon="🎯", layout="wide")

# Streamlit Community Cloud stores secrets in st.secrets; local/Render environments can use env vars.
try:
    API = str(st.secrets.get("API_BASE_URL", os.getenv("API_BASE_URL", "http://localhost:8000/api/v1"))).rstrip("/")
except Exception:
    API = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');
:root { --cl-ink:#18213d; --cl-muted:#77819b; --cl-purple:#7657e8; --cl-blue:#4d83ee; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background: radial-gradient(ellipse at 85% 0%, rgba(128,103,239,.14), transparent 34%), linear-gradient(145deg,#f7f8ff 0%,#eef2ff 52%,#f9f7ff 100%); color:var(--cl-ink); }
[data-testid="stHeader"] { background:rgba(247,248,255,.82); }
.block-container { padding-top:2rem; padding-bottom:3rem; max-width:1320px; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#101a34 0%,#1b2850 58%,#29234f 100%); border-right:1px solid rgba(255,255,255,.10); box-shadow:8px 0 28px rgba(24,32,70,.08); }
[data-testid="stSidebar"] * { color:#f4f5ff !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:11px 13px; margin:3px 0; border:1px solid transparent; border-radius:12px; transition:background .18s ease,border-color .18s ease; font-weight:650; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:rgba(255,255,255,.10); border-color:rgba(255,255,255,.12); }
[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"] { background:rgba(143,133,255,.22); border-color:rgba(183,177,255,.36); }
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p { font-weight:650; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color:#c8d0f0 !important; font-size:.70rem; letter-spacing:1.4px; font-weight:800; }
[data-testid="stSidebar"] button { border:1px solid rgba(255,255,255,.2); border-radius:12px; }
.hero { padding:34px 38px; border-radius:25px; color:white; background:linear-gradient(110deg,rgba(17,25,54,.96),rgba(67,61,139,.90)),url('https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1800&q=85') center/cover; box-shadow:0 18px 45px rgba(36,42,91,.18); margin:4px 0 24px; }
.hero h1 { font-family:'Manrope',sans-serif; font-size:2.6rem; font-weight:800; letter-spacing:-1.4px; margin:0 0 8px; }
.hero p { color:#e4e8ff; font-size:1.05rem; margin:0; }
.eyebrow { color:#bfc8ff; text-transform:uppercase; letter-spacing:2px; font-size:.72rem; font-weight:800; margin-bottom:10px; }
.section-kicker { color:#7565c9; font-size:.75rem; font-weight:800; letter-spacing:1.6px; text-transform:uppercase; }
div[data-testid="stMetric"] { background:rgba(255,255,255,.86); border:1px solid #e6e8f5; padding:17px 18px; border-radius:18px; box-shadow:0 8px 25px rgba(45,52,99,.055); }
div[data-testid="stMetricLabel"] { color:#78819b; }
div[data-testid="stMetricValue"] { color:#242b4c; font-family:'Manrope',sans-serif; font-weight:800; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:rgba(255,255,255,.8); border:1px solid #e7e9f5; border-radius:18px; }
.stButton>button, .stFormSubmitButton>button { border-radius:12px; font-weight:700; min-height:44px; border:0; background:linear-gradient(100deg,#6655df,#4e83e9); color:white; box-shadow:0 7px 17px rgba(91,91,218,.18); }
.stButton>button:hover, .stFormSubmitButton>button:hover { color:white; border:0; filter:brightness(1.06); }
.stTextInput input, .stTextArea textarea, [data-testid="stFileUploader"] { border-radius:13px; }
hr { border-color:#e4e7f3; }
[data-testid="stCaptionContainer"] { color:#7b849d; }
</style>
""", unsafe_allow_html=True)

# One theme selector for guest and signed-in users. The URL preference is browser/device-local
# because each browser keeps its own address; it also survives a refresh or a later visit.
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = st.query_params.get("cl_theme", "light").lower() == "dark"

def _save_theme_preference():
    st.query_params["cl_theme"] = "dark" if st.session_state.dark_mode else "light"

dark_mode = st.sidebar.toggle(
    "🌙 Dark theme",
    key="dark_mode",
    on_change=_save_theme_preference,
)
if dark_mode:
    st.markdown("""
    <style>
    /* Apply a consistent dark palette to Streamlit's main canvas and widgets. */
    .stApp, [data-testid="stAppViewContainer"] {
        background: linear-gradient(145deg,#0b1020 0%,#111a2e 55%,#17142b 100%) !important;
        color: #edf1ff !important;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: rgba(11,16,32,.92) !important;
    }
    [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
        color: #edf1ff !important;
    }
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li, [data-testid="stCaptionContainer"],
    [data-testid="stText"], label, .stText, .stCaption,
    h1,h2,h3,h4,h5,h6 {
        color: #edf1ff !important;
    }
    [data-testid="stMetric"], [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stExpander"], [data-testid="stForm"],
    [data-testid="stFileUploader"], [data-testid="stAlert"] {
        background: #17213a !important;
        color: #edf1ff !important;
        border-color: #34415f !important;
    }
    [data-testid="stMetricLabel"] { color: #b7c1dc !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    input, textarea, [data-baseweb="select"] > div,
    [data-baseweb="input"] > div, [data-baseweb="textarea"] {
        background: #101a30 !important;
        color: #f4f6ff !important;
        border-color: #455473 !important;
    }
    input::placeholder, textarea::placeholder { color: #aab5d0 !important; }
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploader"] button {
        background: #17213a !important;
        color: #f4f6ff !important;
        border-color: #455473 !important;
    }
    [data-testid="stAlert"] p, [data-testid="stAlert"] div {
        color: #f4f6ff !important;
    }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        filter: invert(.88) hue-rotate(180deg);
    }
    hr { border-color: #34415f !important; }
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
        response = requests.request(method, f"{API}{path}", headers=headers, timeout=180, **kwargs)
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
    authenticity = result.get("authenticity_check", {})
    st.markdown('<div class="section-kicker">Your resume insights</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.metric("Resume readiness", f"{score}/100")
    b.metric("Skills identified", result.get("skill_count", 0))
    c.metric("Words extracted", result.get("word_count", 0))
    st.caption(result.get("score_label", "CareerLens heuristic score"))

    if authenticity:
        risk = int(authenticity.get("risk_score", 0))
        st.markdown("### Resume authenticity screening")
        left, right = st.columns([1, 2])
        left.metric("Review risk", f"{risk}/100", authenticity.get("risk_level", ""))
        if risk >= 55:
            right.error("High review needed — please verify the details below.")
        elif risk >= 25:
            right.warning("Some review signals were found. Please check the details.")
        else:
            right.success("No strong warning signals detected by this screening.")
        signals = authenticity.get("signals", [])
        if signals:
            for signal in signals: st.write("• " + signal)
        else:
            st.write("No configured placeholder, repetition or short-text warning signals were detected.")
        st.caption(authenticity.get("disclaimer", "Heuristic screening only; not proof of authenticity."))

    st.markdown("### Extracted skills")
    skills = result.get("skills", [])
    st.write(" · ".join(skills) if skills else "No skills confidently identified.")
    profile = result.get("profile_summary", {})
    with st.expander("Review extracted profile details"):
        st.write("**Email:**", profile.get("email") or "Not detected")
        st.write("**Phone:**", profile.get("phone") or "Not detected")
        st.write("**Education mentions:**", "; ".join(profile.get("education_mentions", [])) or "Not detected")
        st.write("**Estimated experience:**", f"{profile['estimated_experience_years']} years" if profile.get("estimated_experience_years") is not None else "Not detected")
    st.markdown("### Score breakdown")
    for key, value in result.get("score_breakdown", {}).items():
        st.write(f"**{key.replace('_', ' ').title()}** — {value}/100")
        st.progress(max(0, min(100, int(value))))
    not_detected = result.get("possible_missing_skills", [])
    if not_detected:
        st.caption("Other known skills not detected (not automatically required): " + ", ".join(not_detected))
    st.markdown("### Recommended improvements")
    for item in result.get("improvement_suggestions", []): st.write("• " + item)
    meta = result.get("parser_metadata", {})
    st.caption(f"Parser: {meta.get('parser', 'N/A')} | OCR used: {meta.get('ocr_used', False)}")
    for warning in result.get("limitations", []): st.caption("Note: " + warning)

def show_recommendations(items):
    st.markdown("### Career matches")
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
            if url and "example.com" not in url: st.link_button("View opportunity", url)
            else: st.caption("Demonstration dataset entry — replace with verified live job listings before production.")

st.sidebar.markdown("<div style='padding:12px 4px 22px'><div style='font-size:2rem'>✦</div><div style='font-size:1.35rem;font-weight:800;letter-spacing:-.5px'>CareerLens</div><div style='font-size:.76rem;opacity:.72'>RESUME INTELLIGENCE</div></div>", unsafe_allow_html=True)
if st.session_state.user:
    st.sidebar.success(f"Signed in: {st.session_state.user.get('full_name', '')}")
    pages = ["🏠  Dashboard", "📄  Upload Resume", "🗂️  Resume History", "💼  Job Explorer", "⚙️  Account Settings"]
    if st.session_state.user.get("is_admin"): pages.append("🛡️  Admin Dashboard")
    selected_page = st.sidebar.radio("WORKSPACE", pages, label_visibility="visible")
    page = selected_page.split("  ", 1)[-1]
    if st.sidebar.button("↪  Log out", use_container_width=True):
        st.session_state.token = None; st.session_state.user = None; st.session_state.selected_resume = None
        st.rerun()
else:
    st.sidebar.markdown("**Welcome to CareerLens**")
    st.sidebar.caption("Choose a workspace option below.")
    selected_page = st.radio(
        "GET STARTED",
        ["🏠  Home / Guest Analysis", "🔐  Login", "✨  Register"],
        horizontal=True,
        label_visibility="visible",
        key="public_navigation",
    )
    page = selected_page.split("  ", 1)[-1]

# Give each page its own light-mode background while keeping dark mode consistent.
if not dark_mode:
    light_page_backgrounds = {
        "Home / Guest Analysis": "radial-gradient(ellipse at 85% 0%, rgba(128,103,239,.16), transparent 34%), linear-gradient(145deg,#f7f8ff 0%,#eef2ff 52%,#f9f7ff 100%)",
        "Login": "radial-gradient(ellipse at 12% 10%, rgba(79,140,220,.16), transparent 36%), linear-gradient(145deg,#f2f8ff,#eaf2ff 55%,#f7fbff)",
        "Register": "radial-gradient(ellipse at 88% 8%, rgba(36,170,145,.15), transparent 36%), linear-gradient(145deg,#f0fbf8,#e5f6f0 55%,#f8fffb)",
        "Dashboard": "radial-gradient(ellipse at 10% 0%, rgba(232,166,75,.15), transparent 35%), linear-gradient(145deg,#fff9ef,#fff1df 55%,#fffdf7)",
        "Upload Resume": "radial-gradient(ellipse at 88% 0%, rgba(74,145,210,.15), transparent 35%), linear-gradient(145deg,#f1f9ff,#e7f3fb 55%,#fbfdff)",
        "Resume History": "radial-gradient(ellipse at 12% 0%, rgba(156,117,205,.15), transparent 35%), linear-gradient(145deg,#faf5ff,#f1eafd 55%,#fffaff)",
        "Job Explorer": "radial-gradient(ellipse at 88% 0%, rgba(60,170,120,.15), transparent 35%), linear-gradient(145deg,#f1fbf4,#e8f6eb 55%,#fbfffc)",
        "Account Settings": "radial-gradient(ellipse at 12% 0%, rgba(220,125,125,.14), transparent 35%), linear-gradient(145deg,#fff5f4,#fbeceb 55%,#fffafa)",
        "Admin Dashboard": "radial-gradient(ellipse at 88% 0%, rgba(90,115,190,.16), transparent 35%), linear-gradient(145deg,#f2f5ff,#e8edff 55%,#fbfcff)",
    }
    page_bg = light_page_backgrounds.get(page, light_page_backgrounds["Home / Guest Analysis"])
    st.markdown(f"<style>.stApp {{ background: {page_bg} !important; }}</style>", unsafe_allow_html=True)

if page == "Home / Guest Analysis":
    st.markdown('<div class="hero"><div class="eyebrow">Your next career move starts here</div><h1>See your potential.<br>Shape your future.</h1><p>Understand your resume, uncover skill gaps and discover opportunities with CareerLens.</p></div>', unsafe_allow_html=True)
    st.markdown("### Start with your resume")
    st.write("Upload a PDF, Word document or clear resume image. Guest analysis is temporary; the uploaded file is deleted after processing.")
    uploaded = st.file_uploader("Choose your resume", type=["pdf", "docx", "jpg", "jpeg", "png"], key="guest_file")
    if st.button("✦  Analyze my resume", type="primary", disabled=uploaded is None):
        with st.spinner("Reading and analysing your resume. Scanned documents may take longer..."):
            response = api("POST", "/guest/analyze", files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")})
        if response:
            payload = response.json()
            st.success("Analysis completed. This guest result is not saved to an account.")
            show_analysis(payload["analysis"])
            show_recommendations(payload.get("recommendations", []))
    st.info("Create a free account to save resumes, view analysis history, re-analyse files and download reports.")

elif page == "Login":
    st.markdown('<div class="hero"><div class="eyebrow">Your career workspace</div><h1>Welcome back.</h1><p>Pick up where your career journey left off.</p></div>', unsafe_allow_html=True)
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
    st.markdown('<div class="hero"><div class="eyebrow">Create your free account</div><h1>Make your next move.</h1><p>Save your progress and keep your resume journey organised.</p></div>', unsafe_allow_html=True)
    with st.form("register_form"):
        full_name = st.text_input("Full name")
        email = st.text_input("Email")
        password = st.text_input("Password (at least 10 characters)", type="password")
        submit = st.form_submit_button("Create account", type="primary")
    if submit:
        response = api("POST", "/auth/register", json={"full_name": full_name, "email": email, "password": password})
        if response: st.success("Account created. Please log in.")

elif page == "Dashboard":
    st.markdown('<div class="hero"><div class="eyebrow">Personal workspace</div><h1>Your career at a glance.</h1><p>Track your resumes, analysis progress and next steps.</p></div>', unsafe_allow_html=True)
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
        with st.spinner("Saving your resume and analysing it now..."):
            response = api("POST", "/resumes/upload", files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")})
        if response:
            saved = response.json()
            st.session_state.selected_resume = saved["id"]
            if saved.get("status") == "completed":
                st.success(f"Resume saved and analysed successfully (ID {saved['id']}). Open Resume History to view your results.")
            else:
                st.error(saved.get("error_message") or "Resume was saved, but analysis could not be completed. Open Resume History for details.")

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
            if cols[3].button("Open", key=f"open_{item['id']}"): st.session_state.selected_resume = item["id"]
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
                        if correction: st.success("Your corrected text was saved and re-analysed."); st.rerun()
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
        if not confirm_delete: st.error("Please confirm that you understand the deletion is permanent.")
        else:
            deletion = api("DELETE", "/auth/me", json={"password": confirm_password})
            if deletion is not None:
                st.session_state.token = None; st.session_state.user = None; st.session_state.selected_resume = None
                st.success("Your account and saved resume data have been deleted."); st.rerun()

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
st.caption("CareerLens is a decision-support tool. Readiness scores, authenticity indicators and job matches are estimates, not guarantees or proof of employer ATS decisions.")

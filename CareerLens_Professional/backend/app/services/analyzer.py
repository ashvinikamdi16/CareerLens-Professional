import re
from collections import OrderedDict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILL_ALIASES = OrderedDict({
    "Python": ["python", "python3"], "Java": ["java", "core java"], "C++": ["c++", "cpp"],
    "JavaScript": ["javascript", "js"], "TypeScript": ["typescript", "ts"], "HTML": ["html", "html5"],
    "CSS": ["css", "css3"], "React": ["react", "reactjs"], "Node.js": ["node.js", "nodejs", "node js"],
    "FastAPI": ["fastapi"], "Django": ["django"], "Flask": ["flask"], "Streamlit": ["streamlit"],
    "SQL": ["sql", "structured query language"], "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"], "MongoDB": ["mongodb", "mongo db"], "SQLite": ["sqlite"],
    "Machine Learning": ["machine learning", "ml"], "Deep Learning": ["deep learning"],
    "NLP": ["natural language processing", "nlp"], "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"], "Scikit-learn": ["scikit-learn", "sklearn"],
    "Pandas": ["pandas"], "NumPy": ["numpy"], "Power BI": ["power bi"],
    "Tableau": ["tableau"], "Excel": ["excel", "microsoft excel"], "Git": ["git", "github"],
    "Docker": ["docker"], "Kubernetes": ["kubernetes"], "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"], "Linux": ["linux"], "REST API": ["rest api", "restful api"],
    "Communication": ["communication skills", "communication"], "Problem Solving": ["problem solving", "problem-solving"]
})

JOB_SKILLS = {
    "Python Developer": ["Python", "SQL", "Django", "FastAPI", "Git", "REST API"],
    "Data Analyst": ["Python", "SQL", "Excel", "Power BI", "Pandas", "NumPy"],
    "Frontend Developer": ["HTML", "CSS", "JavaScript", "React", "Git"],
    "Machine Learning Engineer": ["Python", "Machine Learning", "Scikit-learn", "Pandas", "NumPy", "SQL"],
}

def _contains(text: str, term: str) -> bool:
    escaped = re.escape(term)
    if re.fullmatch(r"[a-zA-Z0-9+#. ]+", term):
        pattern = r"(?<![a-zA-Z0-9])" + escaped + r"(?![a-zA-Z0-9])"
        return re.search(pattern, text, flags=re.IGNORECASE) is not None
    return term.lower() in text.lower()

def extract_skills(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(_contains(lower, alias) for alias in aliases):
            found.append(canonical)
    return found

def estimate_experience_years(text: str) -> float | None:
    patterns = [r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?(?:experience|exp)", r"experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*years?"]
    values = []
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            try: values.append(float(match))
            except ValueError: pass
    return max(values) if values else None

def build_analysis(text: str, parser_metadata: dict | None = None) -> dict:
    skills = extract_skills(text)
    words = re.findall(r"\b[\w+#.\-]+\b", text)
    lower = text.lower()
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
    phone_match = re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", text)
    has_contact = bool(email_match or phone_match)
    education_patterns = [
        r"\bB\.?Tech\b", r"\bB\.?E\b", r"\bB\.?Sc\b", r"\bBCA\b",
        r"\bM\.?Tech\b", r"\bMCA\b", r"\bMBA\b", r"\bM\.?Sc\b",
        r"\bPh\.?D\b", r"\bBachelor(?:'s)?\b", r"\bMaster(?:'s)?\b",
        r"\b12th\b", r"\b10th\b",
    ]
    education_mentions = []
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned and any(re.search(pattern, cleaned, re.IGNORECASE) for pattern in education_patterns):
            education_mentions.append(cleaned[:180])
    headings = ["education", "experience", "skills", "projects"]
    heading_count = sum(1 for h in headings if re.search(rf"\b{h}\b", lower))
    structure_score = min(100, 25 + heading_count * 18 + (10 if has_contact else 0))
    skill_score = min(100, len(skills) * 12)
    experience_years = estimate_experience_years(text)
    experience_score = 55 if experience_years is None else min(100, 55 + experience_years * 9)
    project_score = 85 if "project" in lower or "developed" in lower else 35
    readability_score = 85 if 150 <= len(words) <= 1800 else (60 if len(words) >= 60 else 30)
    readiness = round(skill_score * .30 + structure_score * .25 + experience_score * .15 + project_score * .15 + readability_score * .15)
    all_known = list(SKILL_ALIASES.keys())
    suggestions = []
    if not has_contact: suggestions.append("Add a clearly visible professional email address and phone number.")
    if heading_count < 3: suggestions.append("Use clear sections such as Summary, Skills, Experience, Education and Projects.")
    if "project" not in lower: suggestions.append("Add 2–3 relevant projects with technologies and measurable outcomes.")
    if len(skills) < 4: suggestions.append("Add relevant technical skills that you can confidently demonstrate.")
    if not suggestions: suggestions.append("Tailor keywords and achievements to each target job; keep all claims accurate.")
    missing_common = [s for s in all_known if s not in skills][:8]
    return {
        "readiness_score": readiness,
        "score_label": "CareerLens Resume Readiness Score (heuristic; not a proprietary ATS score)",
        "score_breakdown": {"skills_coverage": round(skill_score), "section_structure": round(structure_score), "experience_signal": round(experience_score), "project_signal": round(project_score), "readability": round(readability_score)},
        "skills": skills,
        "skill_count": len(skills),
        "estimated_experience_years": experience_years,
        "word_count": len(words),
        "has_contact_information": has_contact,
        "profile_summary": {
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0).strip() if phone_match else None,
            "education_mentions": education_mentions[:8],
            "estimated_experience_years": experience_years,
        },
        "detected_sections": [h.title() for h in headings if re.search(rf"\b{h}\b", lower)],
        "possible_missing_skills": missing_common,
        "improvement_suggestions": suggestions,
        "parser_metadata": parser_metadata or {},
        "limitations": ["Skill extraction uses a maintained taxonomy and can miss synonyms or domain-specific skills.", "The readiness score is a transparent heuristic, not an employer ATS result.", "Always review extracted information before relying on recommendations."]
    }

def match_jobs(resume_text: str, skills: list[str], jobs: list[dict], limit: int = 10) -> list[dict]:
    if not jobs:
        return []
    documents = [resume_text] + [f"{j.get('title','')} {j.get('description','')} {' '.join(j.get('required_skills') or [])}" for j in jobs]
    try:
        matrix = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=20000).fit_transform(documents)
        similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    except ValueError:
        similarities = [0.0] * len(jobs)
    user_set = {s.lower() for s in skills}
    results = []
    for job, text_similarity in zip(jobs, similarities):
        required = job.get("required_skills") or []
        required_set = {s.lower() for s in required}
        overlap = sorted([s for s in required if s.lower() in user_set])
        skill_ratio = len(overlap) / len(required_set) if required_set else 0.0
        score = round(100 * (0.65 * skill_ratio + 0.35 * float(text_similarity)))
        missing = [s for s in required if s.lower() not in user_set]
        results.append({**job, "match_percentage": min(100, score), "matched_skills": overlap, "missing_skills": missing, "match_explanation": f"Matched {len(overlap)} of {len(required_set)} listed skills; text similarity contributes to ranking."})
    return sorted(results, key=lambda x: x["match_percentage"], reverse=True)[:limit]

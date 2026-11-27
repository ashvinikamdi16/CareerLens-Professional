from backend.app.services.analyzer import extract_skills, build_analysis, match_jobs

def test_extract_skills_normalizes_aliases():
    skills = extract_skills("Built APIs using Python3, PostgreSQL, and ReactJS.")
    assert "Python" in skills
    assert "PostgreSQL" in skills
    assert "React" in skills

def test_build_analysis_returns_transparent_score():
    text = "Email: person@example.com\nSkills\nPython SQL Git\nProjects\nDeveloped a Python API. Education\nBTech"
    result = build_analysis(text)
    assert 0 <= result["readiness_score"] <= 100
    assert "heuristic" in result["score_label"].lower()
    assert "Python" in result["skills"]

def test_job_matcher_ranks_skill_overlap():
    jobs = [
        {"id": 1, "title": "Python Developer", "description": "Python APIs and SQL", "required_skills": ["Python", "SQL"]},
        {"id": 2, "title": "Frontend Developer", "description": "CSS and React web UI", "required_skills": ["CSS", "React"]},
    ]
    ranked = match_jobs("Python SQL developer", ["Python", "SQL"], jobs)
    assert ranked[0]["id"] == 1
    assert ranked[0]["match_percentage"] > ranked[1]["match_percentage"]


def test_authenticity_screen_flags_template_placeholders():
    from backend.app.services.analyzer import assess_resume_authenticity
    result = assess_resume_authenticity("Your Name Here\nEmail: your email here\nLorem ipsum dolor sit amet.")
    assert result["risk_score"] >= 25
    assert result["signals"]
    assert "not proof" in result["disclaimer"].lower()


def test_authenticity_screen_does_not_claim_resume_is_fake():
    from backend.app.services.analyzer import assess_resume_authenticity
    text = ("Alex Morgan\nEmail: alex.morgan@example.org\n" +
            " ".join(["Developed and maintained software projects with Python and SQL."] * 20))
    result = assess_resume_authenticity(text)
    assert result["risk_level"] in {"Low indicators", "Review recommended", "High review needed"}
    assert "fake" not in result["status"].lower()

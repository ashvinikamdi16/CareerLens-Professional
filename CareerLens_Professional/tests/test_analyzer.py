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

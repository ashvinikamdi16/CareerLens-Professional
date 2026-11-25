from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

def create_report(filename: str, result: dict) -> bytes:
    buffer = BytesIO()
    page = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 22 * mm
    page.setTitle("CareerLens Resume Analysis Report")
    page.setFont("Helvetica-Bold", 18); page.drawString(18 * mm, y, "CareerLens Resume Analysis")
    y -= 12 * mm
    page.setFont("Helvetica", 10); page.drawString(18 * mm, y, f"Resume: {filename[:80]}")
    y -= 9 * mm
    page.setFont("Helvetica-Bold", 14); page.drawString(18 * mm, y, f"Readiness Score: {result.get('readiness_score', 0)}/100")
    y -= 10 * mm
    page.setFont("Helvetica-Bold", 11); page.drawString(18 * mm, y, "Extracted skills")
    y -= 6 * mm; page.setFont("Helvetica", 10)
    skills = result.get("skills", [])
    lines = [", ".join(skills[i:i+7]) for i in range(0, len(skills), 7)] or ["No skills confidently identified"]
    for line in lines:
        page.drawString(20 * mm, y, line[:110]); y -= 5 * mm
    y -= 4 * mm; page.setFont("Helvetica-Bold", 11); page.drawString(18 * mm, y, "Score breakdown")
    y -= 6 * mm; page.setFont("Helvetica", 10)
    for key, value in result.get("score_breakdown", {}).items():
        page.drawString(20 * mm, y, f"{key.replace('_', ' ').title()}: {value}/100"); y -= 5 * mm
    y -= 4 * mm; page.setFont("Helvetica-Bold", 11); page.drawString(18 * mm, y, "Improvement suggestions")
    y -= 6 * mm; page.setFont("Helvetica", 9)
    for suggestion in result.get("improvement_suggestions", []):
        if y < 25 * mm:
            page.showPage(); y = height - 22 * mm; page.setFont("Helvetica", 9)
        page.drawString(20 * mm, y, ("• " + suggestion)[:115]); y -= 6 * mm
    y -= 5 * mm; page.setFont("Helvetica-Oblique", 8)
    disclaimer = "CareerLens provides decision-support estimates only. This is not a proprietary ATS score or a hiring decision. Review all extracted details."
    page.drawString(18 * mm, max(y, 15 * mm), disclaimer)
    page.save()
    return buffer.getvalue()

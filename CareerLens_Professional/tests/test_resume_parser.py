from io import BytesIO
import shutil

import fitz
import pytest
from PIL import Image, ImageDraw

from backend.app.services.resume_parser import extract_text


def test_extracts_text_from_digital_pdf(tmp_path):
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Resume Skills Python SQL Git Projects Education Experience Backend Developer with software engineering experience")
    path = tmp_path / "resume.pdf"
    document.save(path)
    document.close()

    text, metadata = extract_text(str(path), "application/pdf")
    assert "Python" in text
    assert metadata["parser"] == "PyMuPDF"
    assert metadata["ocr_used"] is False


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract OCR is not installed")
def test_extracts_text_from_image_resume(tmp_path):
    image = Image.new("RGB", (1200, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.text((60, 80), "RESUME", fill="black")
    draw.text((60, 180), "Skills: Python SQL Git", fill="black")
    draw.text((60, 280), "Education: BTech Computer Science", fill="black")
    draw.text((60, 380), "Projects: Developed web applications", fill="black")
    path = tmp_path / "resume.png"
    image.save(path)

    text, metadata = extract_text(str(path), "image/png")
    assert "Python" in text
    assert metadata["ocr_used"] is True
    assert metadata["ocr_confidence_percent"] is not None

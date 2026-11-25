from pathlib import Path
import io
import fitz
import pytesseract
from PIL import Image, ImageOps, ImageEnhance
from docx import Document
from backend.app.core.config import settings

class ResumeParseError(Exception):
    pass

def _ocr_pil(image: Image.Image) -> tuple[str, float | None]:
    image = ImageOps.exif_transpose(image).convert("RGB")
    image = ImageOps.grayscale(image)
    image = ImageEnhance.Contrast(image).enhance(1.6)
    try:
        data = pytesseract.image_to_data(image, lang=settings.ocr_languages, config="--psm 6", output_type=pytesseract.Output.DICT)
        words = [word.strip() for word in data.get("text", []) if word and word.strip()]
        confidence_values = []
        for value in data.get("conf", []):
            try:
                number = float(value)
                if number >= 0: confidence_values.append(number)
            except (TypeError, ValueError):
                continue
        confidence = round(sum(confidence_values) / len(confidence_values), 1) if confidence_values else None
        return " ".join(words), confidence
    except pytesseract.TesseractNotFoundError as exc:
        raise ResumeParseError("OCR engine is not installed on the server. Please contact the administrator.") from exc
    except Exception as exc:
        raise ResumeParseError(f"OCR could not read this image: {exc}") from exc

def extract_text(file_path: str, mime_type: str) -> tuple[str, dict]:
    path = Path(file_path)
    if not path.exists():
        raise ResumeParseError("Stored resume file is missing.")
    metadata = {"ocr_used": False, "pages": 0, "parser": "unknown"}
    try:
        if mime_type == "application/pdf":
            doc = fitz.open(path)
            if doc.is_encrypted:
                raise ResumeParseError("Password-protected PDFs are not supported. Upload an unlocked PDF.")
            if len(doc) > 12:
                raise ResumeParseError("PDF has more than 12 pages. Upload a shorter resume.")
            chunks = [page.get_text("text") for page in doc]
            text = "\n".join(chunks).strip()
            metadata.update({"pages": len(doc), "parser": "PyMuPDF"})
            if len(text) < 60:
                metadata["ocr_used"] = True
                ocr_chunks = []
                confidence_values = []
                for page in doc:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    image = Image.open(io.BytesIO(pix.tobytes("png")))
                    page_text, confidence = _ocr_pil(image)
                    ocr_chunks.append(page_text)
                    if confidence is not None: confidence_values.append(confidence)
                text = "\n".join(ocr_chunks).strip()
                metadata["ocr_confidence_percent"] = round(sum(confidence_values) / len(confidence_values), 1) if confidence_values else None
            doc.close()
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            document = Document(str(path))
            blocks = [p.text for p in document.paragraphs if p.text.strip()]
            for table in document.tables:
                for row in table.rows:
                    blocks.append(" | ".join(cell.text for cell in row.cells))
            text = "\n".join(blocks).strip()
            metadata.update({"parser": "python-docx", "pages": 0})
        elif mime_type.startswith("image/"):
            with Image.open(path) as image:
                text, confidence = _ocr_pil(image)
            metadata.update({"parser": "Tesseract OCR", "ocr_used": True, "pages": 1, "ocr_confidence_percent": confidence})
        else:
            raise ResumeParseError("Unsupported document type.")
    except ResumeParseError:
        raise
    except Exception as exc:
        raise ResumeParseError(f"Could not process the resume: {exc}") from exc

    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(text) < 30:
        raise ResumeParseError("No readable resume text found. The file may be blank, scanned unclearly or unsupported.")
    metadata["character_count"] = len(text)
    return text, metadata

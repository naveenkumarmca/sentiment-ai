import io
import re
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes

def extract_feedbacks(pdf_bytes: io.BytesIO) -> list:
    text = ""
    pdf_bytes.seek(0)

    # Try pdfplumber first
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # OCR fallback if no text found
    if not text.strip():
        pdf_bytes.seek(0)
        images = convert_from_bytes(pdf_bytes.read())
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"

    pattern = r"Feedback ID:\s*([a-z]+_\d+)\s*Comment:\s*(.*?)(?=\nFeedback ID:|\Z)"
    matches = re.findall(pattern, text, flags=re.DOTALL | re.IGNORECASE)

    if not matches:
        raise ValueError(f"No feedback found. Extracted text: {text[:200]}...")

    return [{"fb_id": m[0].lower(), "comment": m[1].strip()} for m in matches]
import pdfplumber, re, io

def extract_feedbacks(pdf_bytes: io.BytesIO) -> list:
    text = ""
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    pattern = r"Feedback ID:\s*(fb_\d+)\s*Comment:\s*(.+?)(?=Feedback ID:|$)"
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    return [{"fb_id": m[0].lower(), "comment": m[1].strip()} for m in matches]
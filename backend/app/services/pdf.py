import io
import re

import pdfplumber


class PdfParseError(Exception):
    pass


def extract_text(data: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
    except Exception as exc:
        raise PdfParseError(f"could not read PDF: {exc}") from exc
    text = "\n".join(pages)
    text = "\n".join(re.sub(r"[ \t]+", " ", line).rstrip() for line in text.splitlines())
    if not text.strip():
        raise PdfParseError("PDF contained no extractable text")
    return text.strip()

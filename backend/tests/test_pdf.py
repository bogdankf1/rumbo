import io

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.services.pdf import PdfParseError, extract_text


def make_pdf(lines: list[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 750
    for line in lines:
        c.drawString(72, y, line)
        y -= 20
    c.save()
    return buf.getvalue()


def test_extracts_known_lines() -> None:
    data = make_pdf(["Maya Chen", "Senior Frontend Engineer"])
    text = extract_text(data)
    assert "Maya Chen" in text
    assert "Senior Frontend Engineer" in text


def test_rejects_non_pdf() -> None:
    with pytest.raises(PdfParseError):
        extract_text(b"definitely not a pdf")

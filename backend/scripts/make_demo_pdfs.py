"""Render a few demo documents as PDFs so the live upload pipeline can be demoed.

Run once from backend/: uv run python scripts/make_demo_pdfs.py
The output PDFs are committed to the repo.
"""

import json
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

BACKEND = Path(__file__).resolve().parents[1]
DEMO = BACKEND / "data" / "demo"
OUT = DEMO / "pdfs"

SOURCES = {
    "maya-chen-resume.pdf": DEMO / "resumes" / "r1.json",
    "nimbus-retail-vue-jd.pdf": DEMO / "jobs" / "j1.json",
    "finch-health-backend-jd.pdf": DEMO / "jobs" / "j2.json",
}


def render(text: str, path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    _, height = letter
    y = height - 72
    for line in text.splitlines():
        if y < 72:
            c.showPage()
            y = height - 72
        c.setFont("Helvetica", 10)
        c.drawString(72, y, line)
        y -= 14
    c.save()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, src in SOURCES.items():
        doc = json.loads(src.read_text())
        render(doc["raw_text"], OUT / name)
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()

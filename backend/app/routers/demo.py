import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import ChatMessage, Chunk, JobDescription, Resume
from app.services.ingestion import store_chunks

log = structlog.get_logger()
router = APIRouter(prefix="/api/demo", tags=["demo"])

DEMO_DIR = Path(__file__).resolve().parents[2] / "data" / "demo"


def _load(folder: str) -> list[dict]:
    files = sorted((DEMO_DIR / folder).glob("*.json"))
    return [json.loads(f.read_text()) for f in files]


@router.post("")
async def load_demo(session: AsyncSession = Depends(get_session)) -> dict:
    # Chat history goes too: old citations must not outlive their source documents.
    for table in (ChatMessage, Chunk, JobDescription, Resume):
        await session.execute(delete(table))

    # Explicit, strictly increasing timestamps: rows inserted in one transaction
    # would otherwise share now() and the sidebar order would not be stable.
    base = datetime.now(timezone.utc)
    resumes = _load("resumes")
    for i, doc in enumerate(resumes):
        extracted = doc["extracted"]
        resume = Resume(
            name=extracted["full_name"],
            source_filename=None,
            raw_text=doc["raw_text"],
            extracted=extracted,
            is_active=i == 0,
            created_at=base + timedelta(milliseconds=i),
        )
        session.add(resume)
        await session.flush()
        await store_chunks(
            session,
            "resume",
            resume.id,
            doc["raw_text"],
            [r["title"] for r in extracted.get("roles", [])],
        )

    jobs = _load("jobs")
    for i, doc in enumerate(jobs):
        extracted = doc["extracted"]
        job = JobDescription(
            seq=i + 1,
            title=extracted["title"],
            company=extracted["company"],
            source="demo",
            raw_text=doc["raw_text"],
            extracted=extracted,
        )
        session.add(job)
        await session.flush()
        await store_chunks(session, "job", job.id, doc["raw_text"], [])

    await session.commit()
    log.info("demo_loaded", resumes=len(resumes), jobs=len(jobs))
    return {"resumes": len(resumes), "jobs": len(jobs)}

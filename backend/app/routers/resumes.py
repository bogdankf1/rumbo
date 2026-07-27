import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Resume
from app.schemas import ResumeOut
from app.services.ingestion import delete_owned_chunks, ingest_resume
from app.services.pdf import PdfParseError

log = structlog.get_logger()
router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("", response_model=ResumeOut)
async def upload(file: UploadFile, session: AsyncSession = Depends(get_session)):
    data = await file.read()
    try:
        return await ingest_resume(session, file.filename, data)
    except PdfParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        log.exception("resume_ingest_failed")
        raise HTTPException(
            status_code=502, detail=f"Could not process the resume: {exc}"
        ) from exc


@router.get("", response_model=list[ResumeOut])
async def list_resumes(session: AsyncSession = Depends(get_session)):
    # Secondary sort on id: demo rows can share a created_at, and ties must
    # never reshuffle after activation updates.
    rows = (
        await session.execute(select(Resume).order_by(Resume.created_at, Resume.id))
    ).scalars()
    return list(rows)


@router.post("/{resume_id}/activate", response_model=ResumeOut)
async def activate(resume_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    resume = await session.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="resume not found")
    await session.execute(update(Resume).values(is_active=False))
    resume.is_active = True
    await session.commit()
    await session.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=204)
async def delete_resume(
    resume_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    resume = await session.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="resume not found")
    await delete_owned_chunks(session, resume_id)
    await session.delete(resume)
    await session.commit()

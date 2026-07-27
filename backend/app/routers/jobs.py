import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import JobDescription, Resume
from app.schemas import JobCreateText, JobOut
from app.services.extraction import JDExtract, ResumeExtract
from app.services.ingestion import delete_owned_chunks, ingest_job
from app.services.matching import match
from app.services.pdf import PdfParseError, extract_text

log = structlog.get_logger()
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


async def active_resume(session: AsyncSession) -> Resume | None:
    return (
        await session.execute(select(Resume).where(Resume.is_active.is_(True)))
    ).scalar_one_or_none()


def job_out(job: JobDescription, resume: Resume | None) -> JobOut:
    out = JobOut.model_validate(job)
    if resume is not None:
        out.fit = match(
            ResumeExtract.model_validate(resume.extracted),
            JDExtract.model_validate(job.extracted),
        ).model_dump()
    return out


@router.post("", response_model=JobOut)
async def create_job(request: Request, session: AsyncSession = Depends(get_session)):
    ctype = request.headers.get("content-type", "")
    if ctype.startswith("multipart/form-data"):
        form = await request.form()
        file = form.get("file")
        if file is None or isinstance(file, str):
            raise HTTPException(status_code=422, detail="file field required")
        data = await file.read()
        try:
            text = extract_text(data)
        except PdfParseError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        source, filename, title_hint = "pdf", file.filename, None
    else:
        body = JobCreateText.model_validate(await request.json())
        if not body.text.strip():
            raise HTTPException(status_code=422, detail="text is required")
        source, filename, title_hint = "text", None, body.title
        text = body.text
    try:
        job = await ingest_job(
            session, source, text, filename=filename, title_hint=title_hint
        )
    except Exception as exc:
        log.exception("job_ingest_failed")
        raise HTTPException(
            status_code=502, detail=f"Could not process the posting: {exc}"
        ) from exc
    return job_out(job, await active_resume(session))


@router.get("", response_model=list[JobOut])
async def list_jobs(session: AsyncSession = Depends(get_session)):
    jobs = (
        (await session.execute(select(JobDescription).order_by(JobDescription.seq)))
        .scalars()
        .all()
    )
    resume = await active_resume(session)
    return [job_out(job, resume) for job in jobs]


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    job = await session.get(JobDescription, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job_out(job, await active_resume(session))


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    job = await session.get(JobDescription, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    await delete_owned_chunks(session, job_id)
    await session.delete(job)
    await session.commit()

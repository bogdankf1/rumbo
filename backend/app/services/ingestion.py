import uuid

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chunk, JobDescription, Resume
from app.services import extraction, pdf
from app.services.chunking import chunk_text
from app.services.embeddings import get_provider

log = structlog.get_logger()


async def store_chunks(
    session: AsyncSession,
    owner_type: str,
    owner_id: uuid.UUID,
    text: str,
    sections: list[str],
) -> int:
    drafts = chunk_text(text, sections=sections)
    if not drafts:
        return 0
    vectors = await get_provider().embed([d.content for d in drafts])
    for draft, vector in zip(drafts, vectors):
        session.add(
            Chunk(
                owner_type=owner_type,
                owner_id=owner_id,
                idx=draft.idx,
                section=draft.section,
                content=draft.content,
                embedding=vector,
            )
        )
    return len(drafts)


async def ingest_resume(
    session: AsyncSession, filename: str | None, pdf_bytes: bytes
) -> Resume:
    text = pdf.extract_text(pdf_bytes)
    extract = await extraction.extract_resume(text)
    existing = (await session.execute(select(func.count(Resume.id)))).scalar_one()
    resume = Resume(
        name=extract.full_name,
        source_filename=filename,
        raw_text=text,
        extracted=extract.model_dump(),
        is_active=existing == 0,
    )
    session.add(resume)
    await session.flush()
    chunks = await store_chunks(
        session, "resume", resume.id, text, [r.title for r in extract.roles]
    )
    await session.commit()
    await session.refresh(resume)
    log.info("resume_ingested", resume_id=str(resume.id), chunks=chunks)
    return resume


async def ingest_job(
    session: AsyncSession,
    source: str,
    text: str,
    filename: str | None = None,
    title_hint: str | None = None,
) -> JobDescription:
    extract = await extraction.extract_jd(text)
    seq = (
        await session.execute(select(func.coalesce(func.max(JobDescription.seq), 0)))
    ).scalar_one() + 1
    job = JobDescription(
        seq=seq,
        title=extract.title or title_hint or "Untitled role",
        company=extract.company,
        source=source,
        source_filename=filename,
        raw_text=text,
        extracted=extract.model_dump(),
    )
    session.add(job)
    await session.flush()
    chunks = await store_chunks(session, "job", job.id, text, [])
    await session.commit()
    await session.refresh(job)
    log.info("job_ingested", job_id=str(job.id), seq=job.seq, chunks=chunks)
    return job


async def delete_owned_chunks(session: AsyncSession, owner_id: uuid.UUID) -> None:
    await session.execute(delete(Chunk).where(Chunk.owner_id == owner_id))

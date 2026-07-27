import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal, get_session
from app.models import ChatMessage, JobDescription, Resume
from app.schemas import ChatMessageOut, ChatRequest
from app.services import chat_pipeline as cp

log = structlog.get_logger()
router = APIRouter(prefix="/api/chat", tags=["chat"])

HISTORY_WINDOW = 10


@router.get("/messages", response_model=list[ChatMessageOut])
async def messages(session: AsyncSession = Depends(get_session)):
    rows = (
        (await session.execute(select(ChatMessage).order_by(ChatMessage.created_at)))
        .scalars()
        .all()
    )
    return list(rows)


async def _refuse(session: AsyncSession, text: str):
    yield cp.sse("delta", {"text": text})
    yield cp.sse("refusal", {})
    assistant = ChatMessage(
        role="assistant", content=text, intent="out_of_scope", citations=[]
    )
    session.add(assistant)
    await session.commit()
    yield cp.sse("done", {"message_id": str(assistant.id), "meta": {}})


@router.post("")
async def chat(req: ChatRequest) -> StreamingResponse:
    async def gen():
        async with SessionLocal() as session:
            try:
                resume = (
                    await session.execute(
                        select(Resume).where(Resume.is_active.is_(True))
                    )
                ).scalar_one_or_none()
                jobs = list(
                    (
                        await session.execute(
                            select(JobDescription).order_by(JobDescription.seq)
                        )
                    ).scalars()
                )
                history_rows = list(
                    (
                        await session.execute(
                            select(ChatMessage)
                            .order_by(ChatMessage.created_at.desc())
                            .limit(HISTORY_WINDOW)
                        )
                    ).scalars()
                )[::-1]
                history = [
                    {"role": m.role, "content": m.content} for m in history_rows
                ]

                session.add(ChatMessage(role="user", content=req.message))
                await session.commit()

                if resume is None or not jobs:
                    async for frame in _refuse(session, cp.NO_DOCUMENTS_TEXT):
                        yield frame
                    return

                route = await cp.route(req.message, history, jobs)
                yield cp.sse(
                    "router", {"intent": route.intent, "job_seqs": route.job_seqs}
                )

                if route.intent == "out_of_scope":
                    async for frame in _refuse(session, cp.REFUSAL_TEXT):
                        yield frame
                    return

                target = [j for j in jobs if j.seq in route.job_seqs]
                if route.all_jobs or route.intent == "comparison" or not target:
                    target = jobs

                if route.intent == "narrative":
                    evidences, context, meta = await cp.build_narrative_pack(
                        session, req.message, resume, target
                    )
                else:
                    evidences, context, meta = cp.build_match_pack(
                        resume, target, route.intent
                    )

                full_text = ""
                async for delta in cp.generate(
                    req.message, history, evidences, context
                ):
                    full_text += delta
                    yield cp.sse("delta", {"text": delta})

                citations = cp.citations_for(full_text, evidences)
                yield cp.sse("citations", citations)
                assistant = ChatMessage(
                    role="assistant",
                    content=full_text,
                    intent=route.intent,
                    citations=citations,
                )
                session.add(assistant)
                await session.commit()
                yield cp.sse(
                    "done", {"message_id": str(assistant.id), "meta": meta}
                )
            except Exception as exc:
                log.exception("chat_failed")
                yield cp.sse("error", {"detail": str(exc)})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

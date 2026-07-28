import json
import re
from dataclasses import asdict, dataclass
from typing import AsyncIterator, Literal

import structlog
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import JobDescription, Resume
from app.services.extraction import JDExtract, ResumeExtract, client
from app.services.matching import match
from app.services.retrieval import retrieve

log = structlog.get_logger()


class RouteResult(BaseModel):
    intent: Literal[
        "fit_assessment",
        "skill_gap",
        "comparison",
        "interview_prep",
        "narrative",
        "out_of_scope",
    ]
    job_seqs: list[int] = []
    all_jobs: bool = False


@dataclass
class Evidence:
    id: str
    doc_type: str
    doc_id: str
    doc_label: str
    quote: str


REFUSAL_TEXT = (
    "That question is outside what I can answer well. I only work from the documents "
    "you have loaded: your resume and the job descriptions in the sidebar. Ask me about "
    "fit, skill gaps, comparisons between the roles, or interview preparation for one of them."
)

NO_DOCUMENTS_TEXT = (
    "I need documents to work from. Add a resume and at least one job description "
    "in the sidebar, or press Load demo data, and then ask again."
)

ROUTER_PROMPT = """You route questions for a career analysis assistant. The user has loaded one active resume and these job descriptions:

{inventory}

Recent conversation (oldest first):
{history}

Classify the new user message into exactly one intent:
- fit_assessment: how well the candidate fits a specific role or roles overall
- skill_gap: what skills are missing for a role
- comparison: ranking or choosing between several loaded roles ("which fits best")
- interview_prep: preparing for an interview for one of the loaded roles
- narrative: other questions answerable from the resume or job description text (experience details, alignment stories, what a role involves)
- out_of_scope: anything not answerable from the loaded documents (salary advice, market trends, whether to quit, general career coaching, anything unrelated)

Also resolve which jobs the message refers to, as their # numbers, in job_seqs. Follow-ups inherit context: if the previous exchange was about skill gaps for one job and the user now says "what about Job #3?", the intent stays skill_gap with job_seqs [3]. Set all_jobs true when the message spans every loaded job ("which of these roles...", "across all the positions").

New user message: {message}"""

GENERATION_SYSTEM = """You are Rumbo, a career intelligence assistant. You analyze one resume against saved job descriptions.

Grounding rules:
- Answer only from the evidence pack and the conversation. Never invent skills, requirements, scores, or numbers.
- Fit scores and matched or missing skills in the evidence pack were computed deterministically. Report them exactly as given; never recompute or adjust them.
- Cite evidence for every factual claim using its id in square brackets, like [E3], placed right after the claim. Only cite ids that exist in the pack.
- You may note when a missing requirement is adjacent to something the candidate knows (for example React experience when the role wants Vue), but label it clearly as commentary; it never changes the score.
- The user can switch the active resume between turns. Earlier answers in the conversation may describe a different resume, so differing numbers there are not errors: never apologize for them or write corrections. Simply answer from the current evidence pack, which always reflects the resume named in it.

Format rules. Use simple markdown with this same structure every time:
- Open with a one-line verdict; bold the key fact, for example **62/100, good fit**.
- Then short sections, each introduced by a bold label on its own line, for example **Missing required skills**, **What already matches**, **Commentary**, **Next steps**. Pick only the sections that fit the question.
- Under each label use hyphen bullets. Start a skill bullet with the bold skill name, for example - **Kubernetes**: the JD asks for it [E4].
- Citations [En] stay inline right after the claims they support.
- Never use markdown headers, tables, code blocks, links, or em dashes.
- Keep the whole answer under roughly 250 words unless the question truly needs more."""


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def route(
    message: str, history: list[dict], jobs: list[JobDescription]
) -> RouteResult:
    inventory = (
        "\n".join(f"#{j.seq} {j.title} at {j.company}" for j in jobs)
        or "(no jobs loaded)"
    )
    history_text = (
        "\n".join(f"{m['role']}: {m['content'][:300]}" for m in history) or "(none)"
    )
    prompt = ROUTER_PROMPT.format(
        inventory=inventory, history=history_text, message=message
    )
    resp = await client().messages.parse(
        model=settings.claude_model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
        output_format=RouteResult,
    )
    result = resp.parsed_output
    log.info("routed", intent=result.intent, job_seqs=result.job_seqs)
    return result


def build_match_pack(
    resume: Resume, jobs: list[JobDescription], intent: str
) -> tuple[list[Evidence], str, dict]:
    evidences: list[Evidence] = []
    lines: list[str] = []
    meta: dict = {}
    resume_model = ResumeExtract.model_validate(resume.extracted)
    resume_label = f"Resume ({resume.name})"

    def add(doc_type: str, doc_id: object, doc_label: str, quote: str) -> str:
        eid = f"E{len(evidences) + 1}"
        evidences.append(
            Evidence(
                id=eid,
                doc_type=doc_type,
                doc_id=str(doc_id),
                doc_label=doc_label,
                quote=quote,
            )
        )
        return eid

    scores: list[dict] = []
    last_result = None
    for job in jobs:
        jd = JDExtract.model_validate(job.extracted)
        result = match(resume_model, jd)
        last_result = result
        scores.append({"job_seq": job.seq, "score": result.score})
        label = f"Job #{job.seq} ({job.title} at {job.company})"
        lines.append(
            f"\n{label}: deterministic fit score {result.score}/100, verdict: {result.verdict}."
        )
        if result.experience.required_years:
            lines.append(
                f"Experience: the role asks for {result.experience.required_years:g} years, "
                f"the candidate has {result.experience.candidate_years:g}."
            )
        for m in result.matched_required:
            jd_id = add("job", job.id, label, m.jd_evidence)
            re_id = add("resume", resume.id, resume_label, m.resume_evidence)
            lines.append(
                f"MATCHED required skill {m.skill}: the JD asks for it [{jd_id}] and the resume shows it [{re_id}]"
            )
        for m in result.missing_required:
            jd_id = add("job", job.id, label, m.jd_evidence)
            lines.append(
                f"MISSING required skill {m.skill}: the JD line is [{jd_id}] and the resume never mentions it"
            )
        for m in result.matched_nice:
            jd_id = add("job", job.id, label, m.jd_evidence)
            re_id = add("resume", resume.id, resume_label, m.resume_evidence)
            lines.append(
                f"MATCHED nice-to-have {m.skill}: JD [{jd_id}], resume [{re_id}]"
            )
        for m in result.missing_nice:
            jd_id = add("job", job.id, label, m.jd_evidence)
            lines.append(f"MISSING nice-to-have {m.skill}: JD line [{jd_id}]")
        if intent == "interview_prep":
            for resp_line in jd.responsibilities:
                r_id = add("job", job.id, label, resp_line)
                lines.append(f"RESPONSIBILITY of the role: {resp_line} [{r_id}]")

    if intent == "skill_gap" and len(jobs) == 1 and last_result is not None:
        meta["missing_required"] = [m.skill for m in last_result.missing_required]
    if intent == "comparison":
        meta["scores"] = scores
    return evidences, "\n".join(lines), meta


async def build_narrative_pack(
    session: AsyncSession,
    question: str,
    resume: Resume,
    jobs: list[JobDescription],
) -> tuple[list[Evidence], str, dict]:
    labels = {str(resume.id): f"Resume ({resume.name})"}
    for job in jobs:
        labels[str(job.id)] = f"Job #{job.seq} ({job.title} at {job.company})"
    chunks = await retrieve(
        session, question, [resume.id, *[j.id for j in jobs]], k=6
    )
    evidences: list[Evidence] = []
    lines: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        eid = f"E{i}"
        label = labels.get(str(chunk.owner_id), chunk.owner_type)
        evidences.append(
            Evidence(
                id=eid,
                doc_type=chunk.owner_type,
                doc_id=str(chunk.owner_id),
                doc_label=label,
                quote=chunk.content,
            )
        )
        lines.append(f"PASSAGE from {label} [{eid}]:\n{chunk.content}")
    return evidences, "\n\n".join(lines), {}


async def generate(
    question: str,
    history: list[dict],
    evidences: list[Evidence],
    context: str,
) -> AsyncIterator[str]:
    quotes = "\n".join(f'[{e.id}] ({e.doc_label}) "{e.quote}"' for e in evidences)
    user_content = (
        f"<evidence_pack>\n{context}\n\nEvidence quotes:\n{quotes}\n</evidence_pack>\n\n"
        f"Question: {question}"
    )
    messages = [*history, {"role": "user", "content": user_content}]
    async with client().messages.stream(
        model=settings.claude_model,
        max_tokens=16000,
        system=GENERATION_SYSTEM,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text
        final = await stream.get_final_message()
        if final.stop_reason == "refusal":
            raise RuntimeError("the model declined to answer")
        log.info(
            "generated",
            output_tokens=final.usage.output_tokens,
            input_tokens=final.usage.input_tokens,
        )


def citations_for(full_text: str, evidences: list[Evidence]) -> list[dict]:
    cited_ids = set(re.findall(r"\[(E\d+)\]", full_text))
    return [asdict(e) for e in evidences if e.id in cited_ids]

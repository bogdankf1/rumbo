from typing import Literal

import structlog
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from app.config import settings
from app.services.aliases import canonicalize

log = structlog.get_logger()

_client: AsyncAnthropic | None = None


def client() -> AsyncAnthropic:
    global _client
    if _client is None:
        # max_retries raised from the default 2: transient 529 overloaded
        # bursts were the only failure mode observed under sustained load.
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key, max_retries=5)
    return _client


SkillCategory = Literal["language", "framework", "database", "cloud", "tool", "practice"]


class SkillItem(BaseModel):
    name: str
    category: SkillCategory
    evidence: str = Field(description="Verbatim contiguous quote from the resume")
    years: float | None = None
    verified: bool = True


class RoleItem(BaseModel):
    title: str
    company: str
    start: str
    end: str
    summary: str
    technologies: list[str] = []


class EducationItem(BaseModel):
    degree: str
    institution: str
    year: str


class ResumeExtract(BaseModel):
    full_name: str
    headline: str
    total_years_experience: float
    seniority: Literal["junior", "mid", "senior", "lead", "principal"]
    skills: list[SkillItem]
    roles: list[RoleItem]
    education: list[EducationItem] = []


class ReqSkill(BaseModel):
    name: str
    evidence: str = Field(description="Verbatim contiguous quote from the job description")
    verified: bool = True


class JDExtract(BaseModel):
    title: str
    company: str
    location: str | None = None
    seniority: str | None = None
    min_years_experience: float | None = None
    required_skills: list[ReqSkill]
    nice_to_have_skills: list[ReqSkill] = []
    responsibilities: list[str] = []


RESUME_PROMPT = """You are extracting structured data from a resume for a career analysis tool.

Rules:
- Skill names must be canonical: "PostgreSQL" not "Postgres", "React" not "React.js", \
"Kubernetes" not "k8s", "Node.js" not "node", "JavaScript" not "JS".
- Every skill's evidence field must be a verbatim contiguous quote copied exactly from the \
resume text (the line or phrase where the skill appears). Never paraphrase, never invent.
- Only list skills the resume actually mentions. Do not infer skills that are not written down.
- total_years_experience: professional experience only, computed from role dates when not stated.
- seniority: junior (<3y), mid (3-5y), senior (5-9y or senior title), lead/principal only when \
the title says so.

Extract from the resume below."""

JD_PROMPT = """You are extracting structured data from a job description for a career analysis tool.

Rules:
- Skill names must be canonical: "PostgreSQL" not "Postgres", "React" not "React.js", \
"Kubernetes" not "k8s", "Node.js" not "node", "JavaScript" not "JS".
- Every skill's evidence field must be a verbatim contiguous quote copied exactly from the \
job description text (the requirement line where the skill appears). Never paraphrase, never invent.
- required_skills: skills the posting demands ("must have", "required", "you have", "strong \
experience with"). nice_to_have_skills: explicitly optional ones ("nice to have", "bonus", \
"a plus", "preferred").
- min_years_experience: only when the posting states a number of years; otherwise null.
- responsibilities: the main duties, short verbatim-ish phrases.

Extract from the job description below."""


def normalize(s: str) -> str:
    return " ".join(s.split()).lower()


def evidence_ok(evidence: str, raw_text: str) -> bool:
    return bool(evidence) and normalize(evidence) in normalize(raw_text)


def canonicalize_resume(extract: ResumeExtract) -> None:
    for skill in extract.skills:
        skill.name = canonicalize(skill.name)
    for role in extract.roles:
        role.technologies = [canonicalize(t) for t in role.technologies]


def canonicalize_jd(extract: JDExtract) -> None:
    for skill in [*extract.required_skills, *extract.nice_to_have_skills]:
        skill.name = canonicalize(skill.name)


def validate_resume_evidence(extract: ResumeExtract, raw_text: str) -> None:
    for skill in extract.skills:
        if not evidence_ok(skill.evidence, raw_text):
            skill.verified = False
            log.warning("evidence_unverified", doc="resume", skill=skill.name)


def validate_jd_evidence(extract: JDExtract, raw_text: str) -> None:
    for skill in [*extract.required_skills, *extract.nice_to_have_skills]:
        if not evidence_ok(skill.evidence, raw_text):
            skill.verified = False
            log.warning("evidence_unverified", doc="jd", skill=skill.name)


async def extract_resume(text: str) -> ResumeExtract:
    resp = await client().messages.parse(
        model=settings.claude_model,
        max_tokens=16000,
        messages=[{"role": "user", "content": f"{RESUME_PROMPT}\n\n<resume>\n{text}\n</resume>"}],
        output_format=ResumeExtract,
    )
    extract = resp.parsed_output
    canonicalize_resume(extract)
    validate_resume_evidence(extract, text)
    return extract


async def extract_jd(text: str) -> JDExtract:
    resp = await client().messages.parse(
        model=settings.claude_model,
        max_tokens=16000,
        messages=[{"role": "user", "content": f"{JD_PROMPT}\n\n<job_description>\n{text}\n</job_description>"}],
        output_format=JDExtract,
    )
    extract = resp.parsed_output
    canonicalize_jd(extract)
    validate_jd_evidence(extract, text)
    return extract

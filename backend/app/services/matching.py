"""Deterministic skill matching. Pure functions, no I/O, no model calls.

Score = weighted mean of required-skill coverage (0.70), nice-to-have
coverage (0.20), and experience fit (0.10). Components a JD does not
define drop out and their weight redistributes proportionally.
"""

from pydantic import BaseModel

from app.services.aliases import same_skill
from app.services.extraction import JDExtract, ReqSkill, ResumeExtract, SkillItem


class MatchedSkill(BaseModel):
    skill: str
    jd_evidence: str
    resume_evidence: str


class MissingSkill(BaseModel):
    skill: str
    jd_evidence: str


class ExperienceFit(BaseModel):
    required_years: float | None
    candidate_years: float
    fit: float | None


class MatchResult(BaseModel):
    score: int
    verdict: str
    matched_required: list[MatchedSkill]
    missing_required: list[MissingSkill]
    matched_nice: list[MatchedSkill]
    missing_nice: list[MissingSkill]
    experience: ExperienceFit


def verdict_for(score: int) -> str:
    if score >= 80:
        return "strong fit"
    if score >= 60:
        return "good fit"
    if score >= 40:
        return "partial fit"
    return "weak fit"


def _split(
    requirements: list[ReqSkill], resume_skills: list[SkillItem]
) -> tuple[list[MatchedSkill], list[MissingSkill]]:
    matched: list[MatchedSkill] = []
    missing: list[MissingSkill] = []
    for req in requirements:
        hit = next((s for s in resume_skills if same_skill(s.name, req.name)), None)
        if hit is not None:
            matched.append(
                MatchedSkill(
                    skill=req.name,
                    jd_evidence=req.evidence,
                    resume_evidence=hit.evidence,
                )
            )
        else:
            missing.append(MissingSkill(skill=req.name, jd_evidence=req.evidence))
    return matched, missing


def match(resume: ResumeExtract, jd: JDExtract) -> MatchResult:
    matched_req, missing_req = _split(jd.required_skills, resume.skills)
    matched_nice, missing_nice = _split(jd.nice_to_have_skills, resume.skills)

    components: list[tuple[float, float]] = []
    if jd.required_skills:
        components.append((0.70, len(matched_req) / len(jd.required_skills)))
    if jd.nice_to_have_skills:
        components.append((0.20, len(matched_nice) / len(jd.nice_to_have_skills)))
    exp_fit: float | None = None
    if jd.min_years_experience:
        exp_fit = min(resume.total_years_experience / jd.min_years_experience, 1.0)
        components.append((0.10, exp_fit))

    if components:
        total_weight = sum(w for w, _ in components)
        score = round(100 * sum(w * v for w, v in components) / total_weight)
    else:
        score = 0

    return MatchResult(
        score=score,
        verdict=verdict_for(score),
        matched_required=matched_req,
        missing_required=missing_req,
        matched_nice=matched_nice,
        missing_nice=missing_nice,
        experience=ExperienceFit(
            required_years=jd.min_years_experience,
            candidate_years=resume.total_years_experience,
            fit=exp_fit,
        ),
    )

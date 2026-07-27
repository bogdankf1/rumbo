import uuid
from datetime import datetime, timezone

from app.models import JobDescription, Resume
from app.services import chat_pipeline as cp


def _resume_row() -> Resume:
    return Resume(
        id=uuid.uuid4(),
        name="Diego Alvarez",
        raw_text="",
        extracted={
            "full_name": "Diego Alvarez",
            "headline": "Backend Engineer",
            "total_years_experience": 5.0,
            "seniority": "senior",
            "skills": [
                {
                    "name": "Python",
                    "category": "language",
                    "evidence": "Shipped APIs in Python.",
                    "years": None,
                    "verified": True,
                }
            ],
            "roles": [],
            "education": [],
        },
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


def _job_row() -> JobDescription:
    return JobDescription(
        id=uuid.uuid4(),
        seq=2,
        title="Backend Engineer",
        company="Finch Health",
        source="demo",
        raw_text="",
        extracted={
            "title": "Backend Engineer",
            "company": "Finch Health",
            "location": None,
            "seniority": None,
            "min_years_experience": 4.0,
            "required_skills": [
                {"name": "Python", "evidence": "Strong Python skills in production services.", "verified": True},
                {"name": "Kubernetes", "evidence": "Experience deploying and operating services on Kubernetes.", "verified": True},
            ],
            "nice_to_have_skills": [],
            "responsibilities": ["Design and ship the scheduling API surface."],
        },
        created_at=datetime.now(timezone.utc),
    )


def test_match_pack_carries_jd_evidence_for_missing_skills() -> None:
    evidences, context, meta = cp.build_match_pack(_resume_row(), [_job_row()], "skill_gap")
    quotes = [e.quote for e in evidences]
    assert "Experience deploying and operating services on Kubernetes." in quotes
    assert "MISSING required skill Kubernetes" in context
    assert meta["missing_required"] == ["Kubernetes"]


def test_comparison_meta_carries_scores() -> None:
    _, _, meta = cp.build_match_pack(_resume_row(), [_job_row()], "comparison")
    assert meta["scores"][0]["job_seq"] == 2
    assert isinstance(meta["scores"][0]["score"], int)


def test_interview_prep_includes_responsibilities() -> None:
    evidences, context, _ = cp.build_match_pack(_resume_row(), [_job_row()], "interview_prep")
    assert any("scheduling API surface" in e.quote for e in evidences)
    assert "RESPONSIBILITY" in context


def test_citations_only_for_cited_ids() -> None:
    evidences, _, _ = cp.build_match_pack(_resume_row(), [_job_row()], "skill_gap")
    text = f"You are missing Kubernetes [{evidences[2].id}] and that is that."
    cited = cp.citations_for(text, evidences)
    assert [c["id"] for c in cited] == [evidences[2].id]


def test_citations_empty_when_none_cited() -> None:
    evidences, _, _ = cp.build_match_pack(_resume_row(), [_job_row()], "skill_gap")
    assert cp.citations_for("No markers here.", evidences) == []


def test_refusal_text_is_plain() -> None:
    assert "—" not in cp.REFUSAL_TEXT
    assert "—" not in cp.GENERATION_SYSTEM

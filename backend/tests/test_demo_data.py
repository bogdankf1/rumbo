import json
from pathlib import Path

from app.services.aliases import canonicalize
from app.services.extraction import evidence_ok

DEMO = Path(__file__).resolve().parents[1] / "data" / "demo"


def _docs(folder: str) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((DEMO / folder).glob("*.json"))]


def test_counts() -> None:
    assert len(_docs("resumes")) == 7
    assert len(_docs("jobs")) == 7


def test_resume_evidence_is_verbatim() -> None:
    for doc in _docs("resumes"):
        for skill in doc["extracted"]["skills"]:
            assert evidence_ok(skill["evidence"], doc["raw_text"]), (
                doc["extracted"]["full_name"],
                skill["name"],
            )


def test_jd_evidence_is_verbatim() -> None:
    for doc in _docs("jobs"):
        extracted = doc["extracted"]
        for skill in [
            *extracted["required_skills"],
            *extracted["nice_to_have_skills"],
        ]:
            assert evidence_ok(skill["evidence"], doc["raw_text"]), (
                extracted["title"],
                skill["name"],
            )


def test_skill_names_are_canonical() -> None:
    for doc in _docs("resumes"):
        for skill in doc["extracted"]["skills"]:
            assert canonicalize(skill["name"]) == skill["name"]
    for doc in _docs("jobs"):
        extracted = doc["extracted"]
        for skill in [
            *extracted["required_skills"],
            *extracted["nice_to_have_skills"],
        ]:
            assert canonicalize(skill["name"]) == skill["name"]

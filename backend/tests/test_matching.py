from app.services.extraction import JDExtract, ReqSkill, ResumeExtract, SkillItem
from app.services.matching import match, verdict_for


def resume_with(skills: list[str], years: float = 5.0) -> ResumeExtract:
    return ResumeExtract(
        full_name="Test Person",
        headline="Engineer",
        total_years_experience=years,
        seniority="senior",
        skills=[
            SkillItem(name=s, category="tool", evidence=f"used {s}") for s in skills
        ],
        roles=[],
    )


def jd_with(
    required: list[str],
    nice: list[str] | None = None,
    min_years: float | None = None,
) -> JDExtract:
    return JDExtract(
        title="Role",
        company="Co",
        min_years_experience=min_years,
        required_skills=[
            ReqSkill(name=s, evidence=f"must know {s}") for s in required
        ],
        nice_to_have_skills=[
            ReqSkill(name=s, evidence=f"bonus {s}") for s in (nice or [])
        ],
    )


def test_perfect_required_only_scores_100() -> None:
    result = match(resume_with(["React"]), jd_with(["React"]))
    assert result.score == 100
    assert result.verdict == "strong fit"


def test_half_required_scores_50() -> None:
    result = match(resume_with(["A", "B"]), jd_with(["A", "B", "C", "D"]))
    assert result.score == 50
    assert result.verdict == "partial fit"


def test_weight_redistribution_required_plus_years() -> None:
    # req 1.0 at weight 0.7, exp 0.5 at weight 0.1 -> (0.7 + 0.05) / 0.8 = 0.9375
    result = match(resume_with(["A"], years=3), jd_with(["A"], min_years=6))
    assert result.score == 94
    assert result.experience.fit == 0.5


def test_experience_component_absent_without_min_years() -> None:
    result = match(resume_with(["A"]), jd_with(["A"]))
    assert result.experience.fit is None
    assert result.score == 100


def test_alias_level_matching() -> None:
    result = match(resume_with(["Postgres"]), jd_with(["PostgreSQL"]))
    assert result.score == 100
    assert result.missing_required == []


def test_adjacent_skills_never_match() -> None:
    result = match(resume_with(["React"]), jd_with(["Vue"]))
    assert [m.skill for m in result.missing_required] == ["Vue"]
    assert result.score == 0


def test_verdict_bands() -> None:
    assert verdict_for(80) == "strong fit"
    assert verdict_for(79) == "good fit"
    assert verdict_for(60) == "good fit"
    assert verdict_for(59) == "partial fit"
    assert verdict_for(40) == "partial fit"
    assert verdict_for(39) == "weak fit"


def test_evidence_travels_with_every_entry() -> None:
    result = match(
        resume_with(["A"]),
        jd_with(["A", "B"], nice=["C"]),
    )
    assert result.matched_required[0].jd_evidence == "must know A"
    assert result.matched_required[0].resume_evidence == "used A"
    assert result.missing_required[0].jd_evidence == "must know B"
    assert result.missing_nice[0].jd_evidence == "bonus C"

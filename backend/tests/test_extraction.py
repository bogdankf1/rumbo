from app.services import extraction as ex


def _resume() -> ex.ResumeExtract:
    return ex.ResumeExtract(
        full_name="Test Person",
        headline="Engineer",
        total_years_experience=5,
        seniority="senior",
        skills=[
            ex.SkillItem(
                name="postgres",
                category="database",
                evidence="Built dashboards on Postgres.",
            ),
            ex.SkillItem(
                name="React",
                category="framework",
                evidence="This quote is fabricated.",
            ),
        ],
        roles=[],
    )


def test_evidence_validation_flags_fabricated_quotes() -> None:
    raw = "Five years of experience.\nBuilt dashboards on   Postgres."
    resume = _resume()
    ex.validate_resume_evidence(resume, raw)
    assert resume.skills[0].verified is True
    assert resume.skills[1].verified is False


def test_canonicalization_applied() -> None:
    resume = _resume()
    ex.canonicalize_resume(resume)
    assert resume.skills[0].name == "PostgreSQL"


def test_jd_evidence_validation() -> None:
    jd = ex.JDExtract(
        title="Backend Engineer",
        company="Acme",
        required_skills=[
            ex.ReqSkill(name="Python", evidence="Strong Python experience required."),
            ex.ReqSkill(name="Kafka", evidence="Invented requirement line."),
        ],
    )
    ex.validate_jd_evidence(jd, "We need you. Strong Python experience required.")
    assert jd.required_skills[0].verified is True
    assert jd.required_skills[1].verified is False


def test_prompts_demand_verbatim_evidence() -> None:
    assert "verbatim" in ex.RESUME_PROMPT.lower()
    assert "verbatim" in ex.JD_PROMPT.lower()

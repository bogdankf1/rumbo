from app.services.aliases import canonicalize, same_skill


def test_alias_lookup() -> None:
    assert canonicalize("postgres") == "PostgreSQL"
    assert canonicalize("React.js") == "React"
    assert canonicalize("k8s") == "Kubernetes"


def test_canonical_casing_normalized() -> None:
    assert canonicalize("REACT") == "React"
    assert canonicalize("fastapi") == "FastAPI"


def test_unknown_skill_passes_through_trimmed() -> None:
    assert canonicalize(" Elixir ") == "Elixir"


def test_same_skill_across_aliases() -> None:
    assert same_skill("k8s", "Kubernetes") is True
    assert same_skill("Postgres", "PostgreSQL") is True


def test_adjacent_skills_never_match() -> None:
    assert same_skill("React", "Vue") is False

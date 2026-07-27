"""Canonical skill naming.

Skill matching is exact (case-insensitive) on canonical names. The extraction
prompt already asks for canonical names; this map is the deterministic safety
net for common variants. Deliberately no fuzzy or embedding matching here:
"React" and "Vue" must never match.
"""

ALIASES: dict[str, str] = {
    "postgres": "PostgreSQL",
    "psql": "PostgreSQL",
    "postgresql database": "PostgreSQL",
    "react.js": "React",
    "reactjs": "React",
    "react js": "React",
    "js": "JavaScript",
    "ecmascript": "JavaScript",
    "ts": "TypeScript",
    "k8s": "Kubernetes",
    "kube": "Kubernetes",
    "gcp": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "amazon web services": "AWS",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "golang": "Go",
    "py": "Python",
    "python3": "Python",
    "tf": "Terraform",
    "cicd": "CI/CD",
    "ci-cd": "CI/CD",
    "ci/cd pipelines": "CI/CD",
    "continuous integration": "CI/CD",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "next": "Next.js",
    "nextjs": "Next.js",
    "vue.js": "Vue",
    "vuejs": "Vue",
    "express.js": "Express",
    "expressjs": "Express",
    "mongo": "MongoDB",
    "mongo db": "MongoDB",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "react-native": "React Native",
    "graph ql": "GraphQL",
    "ml flow": "MLflow",
    "rest api": "REST",
    "rest apis": "REST",
    "restful apis": "REST",
}

CANONICAL: dict[str, str] = {
    c.lower(): c
    for c in [
        "PostgreSQL", "React", "Vue", "Pinia", "Vitest", "JavaScript", "TypeScript",
        "Kubernetes", "Google Cloud", "AWS", "Node.js", "Go", "Python", "Terraform",
        "CI/CD", "scikit-learn", "Next.js", "Express", "MongoDB", "Tailwind CSS",
        "React Native", "GraphQL", "MLflow", "REST", "FastAPI", "Redis", "Docker",
        "Kafka", "Spark", "Airflow", "dbt", "Snowflake", "SQL", "Jest", "Prometheus",
        "PyTorch", "Swift", "Grafana", "SageMaker", "GitHub Actions", "Django",
        "GraphQL", "Cypress", "Kotlin", "Datadog",
    ]
}


def canonicalize(name: str) -> str:
    stripped = " ".join(name.split())
    lower = stripped.lower()
    if lower in ALIASES:
        return ALIASES[lower]
    if lower in CANONICAL:
        return CANONICAL[lower]
    return stripped


def same_skill(a: str, b: str) -> bool:
    return canonicalize(a).lower() == canonicalize(b).lower()

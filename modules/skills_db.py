"""Skill taxonomy, role profiles and extraction helpers (all rule-based, no AI needed)."""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, Iterable, List, Pattern, Tuple

# canonical skill -> (category, aliases). Aliases are matched case-insensitively on token boundaries.
SKILLS: Dict[str, Tuple[str, List[str]]] = {
    "Python": ("Language", ["python", "python3"]),
    "Java": ("Language", ["java"]),
    "JavaScript": ("Language", ["javascript", "js", "ecmascript"]),
    "TypeScript": ("Language", ["typescript"]),
    "C++": ("Language", ["c++", "cpp"]),
    "C": ("Language", ["c programming", "c language"]),
    "C#": ("Language", ["c#", "csharp"]),
    "Go": ("Language", ["golang", "go language"]),
    "R": ("Language", ["r programming", "r language"]),
    "SQL": ("Data", ["sql", "t-sql", "pl/sql"]),
    "HTML": ("Web", ["html", "html5"]),
    "CSS": ("Web", ["css", "css3"]),
    "React": ("Web", ["react", "react.js", "reactjs"]),
    "Node.js": ("Web", ["node.js", "nodejs", "node js"]),
    "Django": ("Web", ["django"]),
    "Flask": ("Web", ["flask"]),
    "FastAPI": ("Web", ["fastapi"]),
    "Spring Boot": ("Web", ["spring boot", "springboot", "spring"]),
    "REST APIs": ("Web", ["rest api", "rest apis", "restful", "rest"]),
    "Streamlit": ("Web", ["streamlit"]),
    "Pandas": ("Data", ["pandas"]),
    "NumPy": ("Data", ["numpy"]),
    "Matplotlib": ("Data", ["matplotlib", "seaborn"]),
    "Power BI": ("Data", ["power bi", "powerbi"]),
    "Tableau": ("Data", ["tableau"]),
    "Excel": ("Data", ["excel", "microsoft excel", "advanced excel"]),
    "Statistics": ("Data", ["statistics", "statistical analysis", "hypothesis testing"]),
    "Data Visualization": ("Data", ["data visualization", "data visualisation", "dashboards"]),
    "ETL": ("Data", ["etl", "data pipeline", "data pipelines"]),
    "Machine Learning": ("AI/ML", ["machine learning", "ml", "scikit-learn", "sklearn"]),
    "Deep Learning": ("AI/ML", ["deep learning", "neural network", "neural networks", "cnn", "lstm"]),
    "NLP": ("AI/ML", ["nlp", "natural language processing", "text classification"]),
    "Computer Vision": ("AI/ML", ["computer vision", "opencv", "image classification"]),
    "TensorFlow": ("AI/ML", ["tensorflow", "keras"]),
    "PyTorch": ("AI/ML", ["pytorch", "torch"]),
    "LLMs": ("AI/ML", ["llm", "llms", "large language model", "large language models", "langchain", "prompt engineering", "rag"]),
    "MongoDB": ("Database", ["mongodb", "mongo"]),
    "MySQL": ("Database", ["mysql"]),
    "PostgreSQL": ("Database", ["postgresql", "postgres"]),
    "Git": ("Tools", ["git", "github", "gitlab"]),
    "Docker": ("Tools", ["docker"]),
    "Linux": ("Tools", ["linux", "unix", "bash", "shell scripting"]),
    "AWS": ("Cloud", ["aws", "amazon web services", "ec2", "s3"]),
    "Azure": ("Cloud", ["azure"]),
    "GCP": ("Cloud", ["gcp", "google cloud"]),
    "Testing": ("Practice", ["pytest", "unit testing", "unit tests", "junit", "test-driven", "tdd"]),
    "Data Structures": ("CS", ["data structures", "dsa", "data structures and algorithms"]),
    "Algorithms": ("CS", ["algorithms", "algorithm design", "problem solving"]),
    "OOP": ("CS", ["oop", "object-oriented", "object oriented"]),
    "System Design": ("CS", ["system design", "distributed systems", "microservices"]),
    "Agile": ("Practice", ["agile", "scrum"]),
    "CI/CD": ("Practice", ["ci/cd", "github actions", "jenkins"]),
}

# role -> core skills (required) and nice-to-have skills
ROLE_PROFILES: Dict[str, Dict[str, List[str]]] = {
    "Python Developer": {
        "core": ["Python", "OOP", "Git", "SQL", "REST APIs", "Data Structures"],
        "nice": ["Django", "Flask", "FastAPI", "Testing", "Docker", "Linux"],
    },
    "Data Analyst": {
        "core": ["SQL", "Excel", "Python", "Pandas", "Statistics", "Data Visualization"],
        "nice": ["Power BI", "Tableau", "NumPy", "ETL", "Matplotlib"],
    },
    "AI/ML Engineer": {
        "core": ["Python", "Machine Learning", "Deep Learning", "NumPy", "Pandas", "Git"],
        "nice": ["PyTorch", "TensorFlow", "NLP", "LLMs", "Docker", "Computer Vision", "Statistics"],
    },
    "Software Engineer": {
        "core": ["Data Structures", "Algorithms", "OOP", "Git", "SQL", "REST APIs"],
        "nice": ["Python", "Java", "System Design", "Testing", "Docker", "CI/CD"],
    },
    "Web Developer": {
        "core": ["HTML", "CSS", "JavaScript", "REST APIs", "Git", "SQL"],
        "nice": ["React", "Node.js", "TypeScript", "MongoDB", "Testing"],
    },
}

# Single-letter / very short skills are only matched through their explicit aliases.
_AMBIGUOUS = {"C", "R", "Go"}


def _escape_alias(alias: str) -> str:
    return re.escape(alias).replace(r"\ ", r"\s+")


@lru_cache(maxsize=1)
def _patterns() -> Dict[str, Pattern[str]]:
    out: Dict[str, Pattern[str]] = {}
    for skill, (_cat, aliases) in SKILLS.items():
        names = set(aliases)
        if skill not in _AMBIGUOUS:
            names.add(skill.lower())
        alts = "|".join(_escape_alias(a) for a in sorted(names, key=len, reverse=True))
        # Boundaries: not preceded/followed by an alphanumeric or + # (so "java" != "javascript", "c" != "c++")
        out[skill] = re.compile(rf"(?<![A-Za-z0-9+#])(?:{alts})(?![A-Za-z0-9+#])", re.IGNORECASE)
    return out


def extract_skills(text: str) -> List[str]:
    """Return canonical skills found in ``text`` (ordered by taxonomy order)."""
    if not text:
        return []
    return [skill for skill, pat in _patterns().items() if pat.search(text)]


def skill_category(skill: str) -> str:
    return SKILLS.get(skill, ("Other", []))[0]


def normalize_skill(name: str) -> str:
    """Map a free-text skill name to its canonical form when known; otherwise keep it trimmed."""
    hits = extract_skills(name)
    return hits[0] if hits else name.strip()


def normalize_many(names: Iterable[str]) -> List[str]:
    seen: List[str] = []
    for n in names:
        c = normalize_skill(n)
        if c and c not in seen:
            seen.append(c)
    return seen

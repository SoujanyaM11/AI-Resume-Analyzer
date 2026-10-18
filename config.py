"""Central configuration. Secrets are read from the environment or Streamlit secrets only."""
from __future__ import annotations

import os
from typing import Dict

try:  # optional: load a local .env file during development
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass

APP_NAME = "AI Career Coach"

# ---- Upload limits -------------------------------------------------------
MAX_UPLOAD_MB = 5
ALLOWED_EXTENSIONS = (".pdf", ".docx")
MAX_RESUME_CHARS = 20_000          # hard cap on extracted text
MIN_RESUME_CHARS = 80              # below this we treat the resume as empty/unreadable
MAX_ANSWER_CHARS = 4_000

# ---- Gemini --------------------------------------------------------------
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
# Model names change often and old ones are shut down. Leave GEMINI_MODEL unset to
# auto-discover a current Flash model from the API; set it to pin a specific model.
GEMINI_MODEL_ENV = "GEMINI_MODEL"
GEMINI_DEFAULT_MODEL = "gemini-flash-latest"
GEMINI_TIMEOUT_SECONDS = 30
GEMINI_MAX_RETRIES = 2


def get_api_key() -> str:
    """Return the Gemini API key from env vars or Streamlit secrets ('' if absent)."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    try:  # Streamlit secrets (Community Cloud). Guarded: raises if no secrets file.
        import streamlit as st

        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return ""


# ---- Interview -----------------------------------------------------------
ROLES = ["Python Developer", "Data Analyst", "AI/ML Engineer", "Software Engineer", "Web Developer"]
DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]
DEFAULT_QUESTION_COUNT = 6
MAX_QUESTION_COUNT = 12

# ---- Job matching --------------------------------------------------------
# Weights are normalised to sum to 1 before use, so any positive numbers work.
DEFAULT_MATCH_WEIGHTS: Dict[str, float] = {
    "skills": 0.50,       # required-skill overlap
    "experience": 0.20,   # years + skills used in work history
    "education": 0.10,    # degree level vs. requirement
    "projects": 0.20,     # required skills demonstrated in projects
}
# Required skills count fully; preferred skills only give a small bonus inside the skills component.
PREFERRED_SKILL_WEIGHT = 0.25

LIVE_JOBS_CACHE_SECONDS = 3600
LIVE_JOBS_MAX = 100

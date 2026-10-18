"""Generate resume- and role-grounded interview questions (AI first, local fallback)."""
from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass, field
from typing import Any, List, Optional, Tuple

import config
from modules import question_bank
from modules.llm_client import (SYSTEM_GUARD, GeminiClient, LLMError, redact_pii, wrap)
from modules.resume_analyzer import ResumeProfile, role_gap
from modules.skills_db import extract_skills

CATEGORIES = {"Technical", "Project", "Experience", "Behavioral", "Follow-up"}
_ids = itertools.count(1)


@dataclass
class Question:
    text: str
    category: str = "Technical"
    difficulty: str = "Intermediate"
    concepts: List[str] = field(default_factory=list)
    source: str = "local-bank"          # "ai" | "local-bank" | "resume-template" | "follow-up"
    skill: Optional[str] = None
    id: int = field(default_factory=lambda: next(_ids))

    def to_dict(self):
        return asdict(self)


def profile_digest(profile: ResumeProfile, max_chars: int = 3500) -> str:
    """Compact, PII-redacted description of the resume sent to the AI (not the full raw resume)."""
    lines = [f"Experience level: {profile.experience_level}", f"Skills: {', '.join(profile.skills) or 'none found'}"]
    if profile.education:
        lines.append("Education: " + " | ".join(profile.education[:3]))
    for e in profile.experience[:4]:
        lines.append(f"Experience: {e.title}. " + " ".join(e.details[:4]))
    for e in profile.projects[:4]:
        lines.append(f"Project: {e.title}. " + " ".join(e.details[:4]))
    if profile.certifications:
        lines.append("Certifications: " + "; ".join(profile.certifications[:5]))
    return redact_pii("\n".join(lines), profile.name)[:max_chars]


# ------------------------------------------------------------------ local
def _short(title: str) -> str:
    return title.split(" — ")[0].split("|")[0].strip(" :-")[:80]


def local_questions(profile: ResumeProfile, role: str, difficulty: str, n: int) -> List[Question]:
    out: List[Question] = []
    beh = question_bank.behavioral(difficulty)
    out.append(Question(beh[0][2], "Behavioral", beh[0][1], beh[0][3], "local-bank"))

    # Resume-grounded questions (projects first, then experience)
    for proj in profile.projects[:3]:
        name = _short(proj.title)
        skills = extract_skills(proj.text)
        concepts = [s.lower() for s in skills[:3]] + ["problem|challenge", "result|outcome|accuracy|improv"]
        out.append(Question(
            f"In your project “{name}”, what was the hardest technical problem you faced and how did you solve it?",
            "Project", difficulty, concepts, "resume-template"))
        if skills:
            out.append(Question(
                f"In “{name}” you used {', '.join(skills[:3])}. Why did you choose these over alternatives, and what would you change today?",
                "Project", difficulty, [s.lower() for s in skills[:3]] + ["alternative|trade-off|instead", "improve|change"],
                "resume-template"))
    for exp in profile.experience[:2]:
        name = _short(exp.title)
        out.append(Question(
            f"Walk me through your responsibilities in “{name}” and one result you are proud of.",
            "Experience", difficulty, ["responsib|task|worked on", "tool|technology|used", "result|impact|outcome", "team|collaborat"],
            "resume-template"))

    # Technical questions: role skills the candidate lists first, then core gaps
    strengths, missing_core, _ = role_gap(profile, role)
    ordered = list(dict.fromkeys(strengths + missing_core))
    tech: List[Question] = []
    for skill in ordered:
        for _s, lvl, text, concepts in question_bank.questions_for(skill, difficulty)[:1]:
            tech.append(Question(text, "Technical", lvl, concepts, "local-bank", skill))
    # also include skills from the resume that the role list does not cover
    for skill in profile.skills:
        if skill not in ordered:
            for _s, lvl, text, concepts in question_bank.questions_for(skill, difficulty)[:1]:
                tech.append(Question(text, "Technical", lvl, concepts, "local-bank", skill))

    closing = Question(beh[1][2], "Behavioral", beh[1][1], beh[1][3], "local-bank") if len(beh) > 1 else None
    body_slots = max(0, n - 1 - (1 if closing and n >= 4 else 0))
    resume_qs = [q for q in out[1:]]
    # interleave: keep roughly 1/3 resume-grounded, rest technical
    r_take = min(len(resume_qs), max(1, body_slots // 3)) if resume_qs else 0
    picked = resume_qs[:r_take] + tech[: body_slots - r_take]
    if len(picked) < body_slots:  # not enough technical: top up with remaining resume questions
        picked += [q for q in resume_qs[r_take:]][: body_slots - len(picked)]
    result = [out[0], *picked]
    if closing and n >= 4:
        result.append(closing)
    return result[:n]


# ------------------------------------------------------------------ AI
def _validate(raw: Any, difficulty: str, limit: int) -> List[Question]:
    items = raw.get("questions") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise ValueError("questions missing")
    out: List[Question] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        text = str(it.get("text", "")).strip()
        if not (10 <= len(text) <= 500):
            continue
        cat = str(it.get("category", "Technical")).strip().title()
        cat = cat if cat in CATEGORIES else "Technical"
        concepts = [str(c).strip()[:60] for c in it.get("key_concepts", []) if str(c).strip()][:6]
        diff = str(it.get("difficulty", difficulty)).strip().title()
        out.append(Question(text, cat, diff if diff in config.DIFFICULTIES else difficulty, concepts, "ai",
                            str(it.get("skill", "")).strip() or None))
    return out[:limit]


def ai_questions(client: GeminiClient, profile: ResumeProfile, role: str, difficulty: str, n: int) -> List[Question]:
    prompt = (
        f"Target role: {role}\nDifficulty: {difficulty}\nNumber of questions: {n}\n\n"
        "Write interview questions grounded in the candidate's resume digest below. Include: 1 opening "
        "behavioral question, questions about specific projects/experience BY NAME, technical questions for the "
        "role and the skills listed, and 1 closing behavioral question. Do not ask about anything not supported "
        "by the data unless it is a core skill for the role. Each question must be answerable in 1–3 minutes.\n\n"
        + wrap("resume_data", profile_digest(profile))
        + '\n\nReturn JSON: {"questions":[{"text":str,"category":"Technical|Project|Experience|Behavioral",'
        '"difficulty":"Beginner|Intermediate|Advanced","skill":str,"key_concepts":[3-5 short keywords a good answer covers]}]}'
    )
    return _validate(client.generate_json(prompt, system=SYSTEM_GUARD), difficulty, n)


def build_questions(profile: ResumeProfile, role: str, difficulty: str, n: int,
                    client: Optional[GeminiClient] = None) -> Tuple[List[Question], Optional[str]]:
    """Return (questions, notice). ``notice`` explains any fallback so the UI can show it."""
    n = max(3, min(n, config.MAX_QUESTION_COUNT))
    notice: Optional[str] = None
    if client is not None and client.is_configured:
        try:
            qs = ai_questions(client, profile, role, difficulty, n)
            if len(qs) >= 3:
                if len(qs) < n:
                    have = {q.text for q in qs}
                    qs += [q for q in local_questions(profile, role, difficulty, n) if q.text not in have][: n - len(qs)]
                return qs[:n], None
            notice = "The AI returned too few usable questions, so the local question bank was used."
        except (LLMError, ValueError) as exc:
            notice = f"{exc} Using the local question bank instead."
    else:
        notice = "AI is not configured. Using the local question bank (resume-aware templates, no AI)."
    return local_questions(profile, role, difficulty, n), notice

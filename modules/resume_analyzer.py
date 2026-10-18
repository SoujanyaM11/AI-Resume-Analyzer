"""Rule-based resume analysis. Works fully offline; AI only adds an optional summary on top.

Nothing is inferred that is not in the text: fields that cannot be found stay empty and the UI
shows "Not found".
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from modules.skills_db import ROLE_PROFILES, extract_skills

SECTION_HEADINGS = {
    "summary": r"(professional\s+)?summary|objective|profile|about\s+me",
    "education": r"education(al)?(\s+(background|qualifications?))?|academics?",
    "experience": r"(work\s+|professional\s+)?experience|internships?|employment(\s+history)?|work\s+history",
    "projects": r"(academic\s+|personal\s+|key\s+)?projects?",
    "skills": r"(technical\s+|key\s+|core\s+)?skills|technologies|tech\s+stack|competencies",
    "certifications": r"certifications?(\s+(and|&)\s+\w+)?|licen[sc]es|courses|achievements?|awards?",
}
_HEADING_RES = {k: re.compile(rf"^\s*(?:{v})\s*[:\-]?\s*$", re.I) for k, v in SECTION_HEADINGS.items()}

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?\(?\d{3,5}\)?[\s-]?\d{3,5}(?:[\s-]?\d{3,5})?(?!\d)")
_URL = re.compile(r"(?:https?://|www\.)\S+|(?:linkedin\.com|github\.com)/\S+", re.I)
_DEGREE = re.compile(
    r"\b(b\.?\s?tech|b\.?\s?e\.?|b\.?\s?sc|b\.?\s?c\.?a|bachelor[s']?|m\.?\s?tech|m\.?\s?sc|m\.?\s?c\.?a|"
    r"master[s']?|mba|ph\.?\s?d|doctorate|diploma|b\.?\s?s\b|m\.?\s?s\b)",
    re.I,
)
_BULLET = re.compile(r"^\s*([•\-\*–·▪●◦]|\d+[.)])\s+")
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_DATE_RANGE = re.compile(
    r"(?:(?P<m1>[A-Za-z]{3})[a-z]*\.?\s+)?(?P<y1>(?:19|20)\d{2})\s*(?:-|–|—|to)\s*"
    r"(?:(?P<present>present|current|ongoing|now)|(?:(?P<m2>[A-Za-z]{3})[a-z]*\.?\s+)?(?P<y2>(?:19|20)\d{2}))",
    re.I,
)
_QUANT = re.compile(r"\d+\s?%|\b\d{2,}\b|\$\s?\d|₹\s?\d|\b\d+x\b", re.I)

DEGREE_RANK = {"diploma": 1, "bachelor": 2, "master": 3, "phd": 4}


@dataclass
class Entry:
    title: str
    details: List[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join([self.title, *self.details])


@dataclass
class ResumeProfile:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    links: List[str] = field(default_factory=list)
    summary_text: str = ""
    education: List[str] = field(default_factory=list)
    experience: List[Entry] = field(default_factory=list)
    projects: List[Entry] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)              # whole-resume skills
    skills_in_experience: List[str] = field(default_factory=list)
    skills_in_projects: List[str] = field(default_factory=list)
    years_experience: float = 0.0
    has_internship: bool = False
    experience_level: str = "Not determined"
    education_level: Optional[str] = None
    word_count: int = 0
    is_demo: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------- sectioning
def split_sections(text: str) -> Dict[str, List[str]]:
    """Split resume text into named sections using heading lines. Unknown lead text -> 'header'."""
    sections: Dict[str, List[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        matched = None
        if len(stripped) <= 40:
            for name, rx in _HEADING_RES.items():
                if rx.match(stripped.strip("#*_ ")):
                    matched = name
                    break
        if matched:
            current = matched
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(stripped)
    return sections


def _group_entries(lines: List[str]) -> List[Entry]:
    """Group lines into entries. A short non-bullet line starts a new entry; bullets and long lines are
    details. A date line directly under a title (e.g. "Company | Jan 2023 - Present") joins that title."""
    entries: List[Entry] = []
    for line in lines:
        is_bullet = bool(_BULLET.match(line))
        clean = _BULLET.sub("", line).strip()
        title_like = not is_bullet and len(clean) <= 110 and not clean.endswith(".")
        if title_like:
            prev = entries[-1] if entries else None
            if prev and not prev.details and _DATE_RANGE.search(clean) and not _DATE_RANGE.search(prev.title):
                prev.title = f"{prev.title} — {clean}"
            else:
                entries.append(Entry(title=clean))
        elif entries:
            entries[-1].details.append(clean)
        else:
            entries.append(Entry(title=clean))
    return entries


# ---------------------------------------------------------------- experience
def _months_between(y1: int, m1: int, y2: int, m2: int) -> int:
    return max(0, (y2 - y1) * 12 + (m2 - m1) + 1)


def estimate_years(experience_lines: List[str], today: Optional[date] = None) -> float:
    """Sum date ranges found in the experience section (merging nothing; overlaps are rare for fresher resumes)."""
    today = today or date.today()
    months = 0
    for line in experience_lines:
        for m in _DATE_RANGE.finditer(line):
            y1 = int(m.group("y1"))
            mo1 = _MONTHS.get((m.group("m1") or "jan")[:3].lower(), 1)
            if m.group("present"):
                y2, mo2 = today.year, today.month
            else:
                y2 = int(m.group("y2"))
                mo2 = _MONTHS.get((m.group("m2") or "dec")[:3].lower(), 12)
            if 1990 <= y1 <= today.year and y2 >= y1:
                months += _months_between(y1, mo1, min(y2, today.year), mo2 if y2 < today.year else min(mo2, today.month))
    return round(months / 12, 1)


def level_from_years(years: float, has_entries: bool) -> str:
    if not has_entries:
        return "Student / Fresher (no work experience found)"
    if years < 1:
        return "Fresher / Intern (< 1 year)"
    if years < 3:
        return "Junior (1–3 years)"
    if years < 6:
        return "Mid-level (3–6 years)"
    return "Senior (6+ years)"


def _education_level(lines: List[str]) -> Optional[str]:
    best = 0
    label = None
    for line in lines:
        low = line.lower()
        rank = 0
        if re.search(r"ph\.?\s?d|doctorate", low):
            rank = 4
        elif re.search(r"m\.?\s?tech|m\.?\s?sc|m\.?\s?c\.?a|master|mba|\bm\.?\s?s\b", low):
            rank = 3
        elif re.search(r"b\.?\s?tech|b\.?\s?e\b|b\.?\s?sc|b\.?\s?c\.?a|bachelor|\bb\.?\s?s\b", low):
            rank = 2
        elif "diploma" in low:
            rank = 1
        if rank > best:
            best = rank
            label = {1: "diploma", 2: "bachelor", 3: "master", 4: "phd"}[rank]
    return label


# ---------------------------------------------------------------- main API
def analyze_resume(text: str, is_demo: bool = False, today: Optional[date] = None) -> ResumeProfile:
    sections = split_sections(text)
    header = sections.get("header", [])
    profile = ResumeProfile(is_demo=is_demo, word_count=len(text.split()))

    email = _EMAIL.search(text)
    profile.email = email.group(0) if email else None
    head_blob = "\n".join(header[:8])
    phone = _PHONE.search(_URL.sub(" ", _EMAIL.sub(" ", head_blob)))
    profile.phone = phone.group(0).strip() if phone and sum(c.isdigit() for c in phone.group(0)) >= 10 else None
    profile.links = list(dict.fromkeys(m.group(0).rstrip(".,);") for m in _URL.finditer(text)))[:5]

    for line in header[:5]:
        words = line.split()
        if (1 < len(words) <= 5 and not any(ch.isdigit() for ch in line) and "@" not in line
                and re.fullmatch(r"[A-Za-z.'\- ]+", line)):
            profile.name = line.title() if line.isupper() else line
            break

    profile.summary_text = " ".join(sections.get("summary", []))[:600]
    edu_lines = sections.get("education", [])
    profile.education = [l for l in edu_lines if _DEGREE.search(l) or re.search(r"universit|college|institute|school", l, re.I)]
    profile.education_level = _education_level(edu_lines)

    exp_lines = sections.get("experience", [])
    profile.experience = _group_entries(exp_lines)
    profile.has_internship = bool(re.search(r"intern", " ".join(exp_lines), re.I))
    profile.years_experience = estimate_years(exp_lines, today)
    profile.experience_level = level_from_years(profile.years_experience, bool(profile.experience))

    profile.projects = _group_entries(sections.get("projects", []))
    cert_lines = sections.get("certifications", [])
    profile.certifications = [_BULLET.sub("", l).strip() for l in cert_lines][:12]

    skills_section = "\n".join(sections.get("skills", []))
    exp_text = "\n".join(exp_lines)
    proj_text = "\n".join(e.text for e in profile.projects)
    profile.skills = list(dict.fromkeys(extract_skills(skills_section) + extract_skills(text)))
    profile.skills_in_experience = extract_skills(exp_text)
    profile.skills_in_projects = extract_skills(proj_text)
    return profile


def role_gap(profile: ResumeProfile, role: str) -> Tuple[List[str], List[str], List[str]]:
    """Return (strengths, missing_core, missing_nice) for a target role."""
    prof = ROLE_PROFILES.get(role, ROLE_PROFILES["Software Engineer"])
    have = set(profile.skills)
    strengths = [s for s in prof["core"] + prof["nice"] if s in have]
    return strengths, [s for s in prof["core"] if s not in have], [s for s in prof["nice"] if s not in have]


def suggest_improvements(profile: ResumeProfile, raw_text: str) -> List[str]:
    """Deterministic, evidence-based resume tips."""
    tips: List[str] = []
    if not profile.email:
        tips.append("No email address was detected. Make sure contact details are in plain text, not an image.")
    if not any("github" in l.lower() for l in profile.links):
        tips.append("No GitHub link found. Add one that points to your best projects.")
    if not any("linkedin" in l.lower() for l in profile.links):
        tips.append("No LinkedIn link found. Recruiters often look for one.")
    if not profile.projects:
        tips.append("No projects section was detected. Add 2–3 projects with the tech stack and your specific contribution.")
    if not profile.experience:
        tips.append("No work or internship section was detected. If you have any, add it; otherwise lead with projects.")
    if profile.projects or profile.experience:
        bullets = [l for l in raw_text.splitlines() if _BULLET.match(l)]
        quantified = [l for l in bullets if _QUANT.search(l)]
        if bullets and len(quantified) / len(bullets) < 0.25:
            tips.append("Few bullet points include numbers (users, accuracy, speed-ups, dataset size). Quantify results where you honestly can.")
    if len(profile.skills) < 5:
        tips.append("Few technical skills were detected. List the tools you actually use in a dedicated Skills section.")
    if not profile.summary_text:
        tips.append("No summary or objective found. A 2-line summary targeting your desired role can help.")
    if not profile.certifications:
        tips.append("No certifications/courses section was detected. Add relevant ones if you have them.")
    if profile.word_count > 900:
        tips.append("The resume is long. One page is usually enough for early-career candidates.")
    if profile.word_count < 150:
        tips.append("The resume is very short, so there may be too little detail for recruiters to judge your work.")
    return tips


def ai_resume_summary(client, profile: ResumeProfile, role: str) -> str:
    """Optional AI summary of the (redacted) profile digest. Raises LLMError on failure."""
    from modules.llm_client import SYSTEM_GUARD, wrap
    from modules.question_generator import profile_digest
    prompt = (f"Target role: {role}\nWrite a concise 3-4 sentence summary of this candidate's resume for the role, "
              "then list up to 3 concrete improvements. Mention only facts present in the data.\n\n"
              + wrap("resume_data", profile_digest(profile)))
    return client.generate(prompt, system=SYSTEM_GUARD).strip()[:1500]

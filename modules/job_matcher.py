"""Transparent, rule-based job matching (no AI or network needed).

Score (0-100) = 100 * sum(weight_i * component_i) with weights normalised to sum to 1.
Each component is in [0, 1]:

* skills      required-skill overlap (75%) blended with preferred-skill overlap (25%) when listed
* experience  50% years-of-experience fit + 50% required skills seen in work history
* education   candidate degree level vs. the job's minimum (1.0 if the job asks for none)
* projects    share of required skills demonstrated in projects

This is a compatibility estimate for exploring options, NOT a probability of being hired.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional

import config
from modules.resume_analyzer import DEGREE_RANK, ResumeProfile


@dataclass
class MatchResult:
    job: Dict[str, Any]
    score: float                                   # 0-100
    components: Dict[str, float]                   # each 0-1
    weights: Dict[str, float]                      # normalised
    matching_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    preferred_matching: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_weights(weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    base = dict(config.DEFAULT_MATCH_WEIGHTS)
    if weights:
        base.update({k: max(0.0, float(v)) for k, v in weights.items() if k in base})
    total = sum(base.values())
    if total <= 0:
        base = dict(config.DEFAULT_MATCH_WEIGHTS)
        total = sum(base.values())
    return {k: v / total for k, v in base.items()}


def _ratio(num: int, den: int) -> float:
    return num / den if den else 0.0


def match_job(profile: ResumeProfile, job: Dict[str, Any],
              weights: Optional[Dict[str, float]] = None) -> MatchResult:
    w = normalize_weights(weights)
    required: List[str] = list(dict.fromkeys(job.get("required_skills") or []))
    preferred: List[str] = list(dict.fromkeys(job.get("preferred_skills") or []))
    have = set(profile.skills)
    matched = [s for s in required if s in have]
    missing = [s for s in required if s not in have]
    pref_matched = [s for s in preferred if s in have]
    notes: List[str] = []

    # skills: required overlap, blended with preferred overlap when the job lists preferred skills
    if required:
        req_ratio = _ratio(len(matched), len(required))
        if preferred:
            pw = config.PREFERRED_SKILL_WEIGHT
            skills_c = (1 - pw) * req_ratio + pw * _ratio(len(pref_matched), len(preferred))
        else:
            skills_c = req_ratio
    else:
        skills_c = 0.0
        notes.append("This listing has no recognisable required skills, so skill overlap is 0.")

    # experience
    min_years = float(job.get("min_years") or 0)
    year_fit = 1.0 if min_years <= 0 else min(1.0, profile.years_experience / min_years)
    exp_skill = _ratio(len([s for s in required if s in set(profile.skills_in_experience)]), len(required))
    exp_c = 0.5 * year_fit + 0.5 * exp_skill
    if min_years > profile.years_experience:
        notes.append(f"Asks for about {min_years:g} year(s); your resume shows about {profile.years_experience:g}.")

    # education
    req_edu = job.get("min_education")
    if not req_edu:
        edu_c = 1.0
    elif profile.education_level is None:
        edu_c = 0.0
        notes.append("No degree was detected on the resume, so education scores 0.")
    else:
        edu_c = min(1.0, DEGREE_RANK[profile.education_level] / DEGREE_RANK.get(req_edu, 2))

    # projects
    proj_c = _ratio(len([s for s in required if s in set(profile.skills_in_projects)]), len(required))

    comps = {"skills": skills_c, "experience": exp_c, "education": edu_c, "projects": proj_c}
    score = round(100 * sum(w[k] * comps[k] for k in comps), 1)
    score = max(0.0, min(100.0, score))
    return MatchResult(job=job, score=score, components={k: round(v, 3) for k, v in comps.items()},
                       weights={k: round(v, 3) for k, v in w.items()}, matching_skills=matched,
                       missing_skills=missing, preferred_matching=pref_matched, notes=notes)


def rank_jobs(profile: ResumeProfile, jobs: Iterable[Dict[str, Any]],
              weights: Optional[Dict[str, float]] = None) -> List[MatchResult]:
    return sorted((match_job(profile, j, weights) for j in jobs), key=lambda r: r.score, reverse=True)


def filter_results(results: List[MatchResult], role: Optional[str] = None, location: str = "",
                   remote_only: bool = False, min_score: float = 0.0) -> List[MatchResult]:
    out = []
    loc = location.strip().lower()
    for r in results:
        j = r.job
        if r.score < min_score:
            continue
        if role and role != "Any" and j.get("role_tags") and role not in j["role_tags"]:
            continue
        if remote_only and not j.get("remote"):
            continue
        if loc and loc not in str(j.get("location", "")).lower():
            continue
        out.append(r)
    return out


def missing_skills_across(results: List[MatchResult], top: int = 8) -> List[str]:
    """Skills most often missing in the top matches (feeds the learning roadmap)."""
    from collections import Counter
    c: Counter = Counter()
    for r in results[:10]:
        c.update(r.missing_skills)
    return [s for s, _ in c.most_common(top)]

"""Job data sources.

1. Live: Arbeitnow's public job-board JSON API (no key, no account). Used only on explicit user request,
   cached in memory for an hour, and every listing links back to its source URL.
   I could not verify Arbeitnow's current terms directly: third-party summaries say it asks API users not to abuse
   the service and to link back. Review https://www.arbeitnow.com before public/commercial use.
2. Sample: a bundled, clearly labelled fictional dataset so the app works offline.

Remotive was deliberately NOT included because of its reported redistribution restrictions and robots.txt rules.
Nothing is scraped, and no listing, company or link is ever invented.
"""
from __future__ import annotations

import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

import config
from modules.skills_db import extract_skills

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_jobs.json"
ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"

_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}


class JobSourceError(Exception):
    """User-friendly failure while loading jobs."""


def load_sample_jobs(path: Path = SAMPLE_PATH) -> List[Dict[str, Any]]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise JobSourceError("The bundled sample job file could not be read.") from exc
    jobs = data.get("jobs", [])
    for j in jobs:
        j["is_sample"] = True
        j["source"] = "sample"
        j["url"] = None
    return jobs


def _strip_html(raw: str) -> str:
    text = re.sub(r"<(script|style).*?</\1>", " ", raw or "", flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>|</p>|</li>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", html.unescape(text)).strip()


def _years_required(text: str) -> float:
    m = re.search(r"(\d{1,2})\s*\+?\s*(?:-\s*\d+\s*)?years?", text, re.I)
    return float(m.group(1)) if m else 0.0


def parse_arbeitnow(payload: Dict[str, Any], retrieved_at: Optional[str] = None) -> List[Dict[str, Any]]:
    """Normalise an Arbeitnow response. Listings without any recognised tech skill are dropped."""
    retrieved_at = retrieved_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    jobs: List[Dict[str, Any]] = []
    for item in payload.get("data", []) if isinstance(payload, dict) else []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()
        company = str(item.get("company_name", "")).strip()
        if not (title and company and url.startswith("http")):
            continue                                            # never show listings without a verifiable link
        desc = _strip_html(str(item.get("description", "")))
        skills = extract_skills(f"{title}\n{desc}")
        if not skills:
            continue
        jobs.append({
            "id": f"arbeitnow-{item.get('slug', len(jobs))}", "title": title, "company": company,
            "location": str(item.get("location", "")).strip() or "Not specified",
            "remote": bool(item.get("remote", False)), "description": desc[:1500],
            "required_skills": skills, "preferred_skills": [],      # detected from text; not split into required/preferred
            "min_years": _years_required(desc), "min_education": None, "role_tags": [],
            "source": "arbeitnow", "is_sample": False, "url": url, "retrieved_at": retrieved_at,
        })
    return jobs


def fetch_live_jobs(force: bool = False, session: Optional[requests.Session] = None) -> List[Dict[str, Any]]:
    """Fetch one page of live listings (cached for an hour). Raises JobSourceError with a friendly message."""
    cached = _cache.get("arbeitnow")
    if cached and not force and time.time() - cached[0] < config.LIVE_JOBS_CACHE_SECONDS:
        return cached[1]
    http = session or requests
    try:
        resp = http.get(ARBEITNOW_URL, timeout=15, headers={"User-Agent": "ai-career-coach-demo/1.0"})
    except requests.RequestException as exc:
        raise JobSourceError("Could not reach the live job feed. Showing sample jobs instead is available.") from exc
    if resp.status_code == 429:
        raise JobSourceError("The live job feed is rate-limiting requests. Try again later.")
    if resp.status_code != 200:
        raise JobSourceError(f"The live job feed returned HTTP {resp.status_code}.")
    try:
        jobs = parse_arbeitnow(resp.json())[: config.LIVE_JOBS_MAX]
    except ValueError as exc:
        raise JobSourceError("The live job feed returned an unexpected response.") from exc
    if not jobs:
        raise JobSourceError("The live feed had no listings with recognisable tech skills right now.")
    _cache["arbeitnow"] = (time.time(), jobs)
    return jobs

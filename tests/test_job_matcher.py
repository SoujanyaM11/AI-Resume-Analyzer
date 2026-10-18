import pytest

from modules.job_matcher import filter_results, match_job, normalize_weights, rank_jobs
from modules.job_sources import load_sample_jobs, parse_arbeitnow
from modules.resume_analyzer import analyze_resume
from pathlib import Path

RESUME = (Path(__file__).resolve().parent.parent / "data" / "sample_resume.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def profile():
    return analyze_resume(RESUME)


def test_weights_normalise_to_one():
    w = normalize_weights({"skills": 5, "experience": 5, "education": 0, "projects": 0})
    assert abs(sum(w.values()) - 1) < 1e-9 and w["skills"] == 0.5
    assert abs(sum(normalize_weights({"skills": 0, "experience": 0, "education": 0, "projects": 0}).values()) - 1) < 1e-9


def test_scores_are_bounded_and_explainable(profile):
    for r in rank_jobs(profile, load_sample_jobs()):
        assert 0 <= r.score <= 100
        assert all(0 <= v <= 1 for v in r.components.values())
        recomputed = round(100 * sum(r.weights[k] * r.components[k] for k in r.components), 1)
        assert abs(recomputed - r.score) < 0.5     # weights are rounded to 3 dp in the output


def test_matching_and_missing_partition_required(profile):
    job = {"title": "x", "company": "y", "required_skills": ["Python", "Kubernetes", "SQL"], "preferred_skills": []}
    r = match_job(profile, job)
    assert r.matching_skills == ["Python", "SQL"] and r.missing_skills == ["Kubernetes"]


def test_ranking_is_sorted_and_relevant(profile):
    ranked = rank_jobs(profile, load_sample_jobs())
    assert [r.score for r in ranked] == sorted((r.score for r in ranked), reverse=True)
    assert "Machine Learning" in ranked[0].job["title"] or "ML" in ranked[0].job["title"]


def test_weights_change_ranking(profile):
    job = {"required_skills": ["Python"], "preferred_skills": [], "min_education": "phd", "min_years": 0}
    skills_heavy = match_job(profile, job, {"skills": 1, "experience": 0, "education": 0, "projects": 0}).score
    edu_heavy = match_job(profile, job, {"skills": 0, "experience": 0, "education": 1, "projects": 0}).score
    assert skills_heavy == 100.0 and edu_heavy == 50.0


def test_empty_resume_scores_low():
    p = analyze_resume("Nothing relevant here at all, just gardening and cooking tips for the weekend. " * 2)
    for r in rank_jobs(p, load_sample_jobs()):
        assert r.score <= 35


def test_filters(profile):
    ranked = rank_jobs(profile, load_sample_jobs())
    assert all(r.job["remote"] for r in filter_results(ranked, remote_only=True))
    assert all(r.score >= 60 for r in filter_results(ranked, min_score=60))
    assert all("Data Analyst" in r.job["role_tags"] for r in filter_results(ranked, role="Data Analyst"))
    assert all("bengaluru" in r.job["location"].lower() for r in filter_results(ranked, location="Bengaluru"))


def test_sample_jobs_are_labelled_and_have_no_links():
    jobs = load_sample_jobs()
    assert jobs and all(j["is_sample"] and j["url"] is None and "(sample)" in j["company"] for j in jobs)


def test_live_parser_never_invents_links_or_companies():
    payload = {"data": [
        {"title": "Python Dev", "company_name": "Real Co", "url": "https://example.com/j/1", "description": "<p>Python, SQL</p>", "slug": "a"},
        {"title": "No url", "company_name": "Real Co", "description": "Python"},
        {"title": "No company", "url": "https://example.com/j/2", "description": "Python"},
        {"title": "No skills", "company_name": "Real Co", "url": "https://example.com/j/3", "description": "Cooking"},
        "garbage",
    ]}
    jobs = parse_arbeitnow(payload, retrieved_at="2026-01-01")
    assert len(jobs) == 1 and jobs[0]["url"] == "https://example.com/j/1" and jobs[0]["is_sample"] is False
    assert parse_arbeitnow({"unexpected": 1}) == [] and parse_arbeitnow([]) == []

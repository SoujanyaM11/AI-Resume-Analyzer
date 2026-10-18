"""Rule-based learning roadmap built from role gaps, job gaps and interview results.

Resources are listed by NAME ONLY. I could not verify URLs from this environment, so none are invented.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from modules.answer_evaluator import Report
from modules.resume_analyzer import ResumeProfile, role_gap
from modules.skills_db import skill_category

# skill -> (practice project idea, free resource names, practice prompt)
TOPICS: Dict[str, Dict[str, object]] = {
    "Python": {"project": "A command-line expense tracker with file storage and tests", "resources": ["Official Python Tutorial", "CS50P (Harvard, free)"], "practice": "Solve 20 beginner problems on loops, dicts and string handling."},
    "SQL": {"project": "Analyse a public dataset in SQLite with joins and window functions", "resources": ["SQLBolt", "Mode SQL Tutorial"], "practice": "Write 15 queries covering JOIN, GROUP BY, HAVING and subqueries."},
    "Pandas": {"project": "Clean and explore a messy CSV; publish the notebook", "resources": ["pandas official user guide", "Kaggle Learn: Pandas"], "practice": "Practice merge, groupby, pivot_table and missing-value handling."},
    "NumPy": {"project": "Implement linear regression from scratch with NumPy", "resources": ["NumPy official quickstart"], "practice": "Rewrite three loops as vectorised array operations."},
    "Machine Learning": {"project": "End-to-end classifier with train/validation split, metrics and a short write-up", "resources": ["Kaggle Learn: Intro to ML", "scikit-learn user guide"], "practice": "Explain precision/recall/F1 and bias-variance aloud in 2 minutes each."},
    "Deep Learning": {"project": "Train a small CNN on an image dataset and plot learning curves", "resources": ["PyTorch official tutorials", "fast.ai free course"], "practice": "Explain backpropagation and vanishing gradients without notes."},
    "NLP": {"project": "Text classifier using TF-IDF, then compare with a pretrained model", "resources": ["Hugging Face NLP Course"], "practice": "Describe a text-preprocessing pipeline step by step."},
    "LLMs": {"project": "A small RAG question-answering app over your own notes", "resources": ["Hugging Face NLP Course", "Provider prompt-engineering guides"], "practice": "Explain RAG vs fine-tuning and when to use each."},
    "Statistics": {"project": "A/B test analysis on a public or simulated dataset", "resources": ["Khan Academy Statistics", "StatQuest (YouTube)"], "practice": "Interpret a p-value and a confidence interval in plain language."},
    "Data Visualization": {"project": "A dashboard that tells one clear story from a public dataset", "resources": ["Kaggle Learn: Data Visualization"], "practice": "Pick the chart type for five different questions and justify each."},
    "Excel": {"project": "A sales workbook with pivot tables and lookups", "resources": ["Microsoft Excel training (free)"], "practice": "Build a pivot table and an XLOOKUP from scratch."},
    "Power BI": {"project": "Recreate a business dashboard with slicers and measures", "resources": ["Microsoft Learn: Power BI"], "practice": "Build 3 measures with DAX basics."},
    "Git": {"project": "Contribute a small fix to an open-source repo via pull request", "resources": ["Pro Git book (free)"], "practice": "Practise branch, merge, rebase and resolving a conflict."},
    "REST APIs": {"project": "A CRUD API with authentication and input validation", "resources": ["FastAPI official tutorial", "MDN HTTP guide"], "practice": "Explain HTTP methods, status codes and idempotency."},
    "Data Structures": {"project": "Implement a hash map, linked list and binary tree from scratch", "resources": ["NeetCode roadmap (free)", "CS50x"], "practice": "Solve 2 easy problems daily on arrays, hashing and linked lists."},
    "Algorithms": {"project": "Visualiser for sorting and graph algorithms", "resources": ["NeetCode roadmap (free)", "MIT OpenCourseWare 6.006"], "practice": "Explain time complexity for each solution you write."},
    "OOP": {"project": "Model a library or parking-lot system with clear classes", "resources": ["Official Python Tutorial: Classes"], "practice": "Explain the four pillars with a small example each."},
    "Docker": {"project": "Containerise one of your projects with a Dockerfile", "resources": ["Docker official Get Started"], "practice": "Explain image vs container and write a Dockerfile from memory."},
    "JavaScript": {"project": "An interactive to-do app using fetch and the DOM", "resources": ["MDN JavaScript Guide", "javascript.info"], "practice": "Explain closures, hoisting and promises with examples."},
    "React": {"project": "A small dashboard that fetches data from an API", "resources": ["React official docs (react.dev)"], "practice": "Explain state, props and effects with an example."},
    "HTML": {"project": "A responsive, accessible personal portfolio page", "resources": ["MDN Learn Web Development"], "practice": "Rewrite a page using semantic elements."},
    "CSS": {"project": "Recreate a layout with flexbox and grid", "resources": ["MDN Learn Web Development"], "practice": "Build the same layout once with flexbox and once with grid."},
    "Testing": {"project": "Add a pytest suite with mocks to an existing project", "resources": ["pytest official docs"], "practice": "Write tests for three edge cases in your own code."},
    "System Design": {"project": "Write a design doc for a URL shortener", "resources": ["System Design Primer (GitHub)"], "practice": "Talk through requirements, API, storage and scaling in 10 minutes."},
}
_DEFAULT = {"project": "A small project that uses this skill end to end", "resources": ["Official documentation"], "practice": "Explain the basics aloud and write 5 short practice questions."}


def build_roadmap(profile: ResumeProfile, role: str, job_gaps: Optional[List[str]] = None,
                  report: Optional[Report] = None, max_topics: int = 6) -> Dict[str, object]:
    _strengths, missing_core, missing_nice = role_gap(profile, role)
    reasons: Dict[str, str] = {}
    if report:
        for s in report.skills_to_revise:
            reasons.setdefault(s, "Scored low in your mock interview")
    for s in missing_core:
        reasons.setdefault(s, f"Core skill for {role} not found on your resume")
    for s in (job_gaps or []):
        reasons.setdefault(s, "Often missing in your best job matches")
    for s in missing_nice[:3]:
        reasons.setdefault(s, f"Useful extra skill for {role}")
    topics = list(reasons)[:max_topics]
    items = []
    for t in topics:
        info = TOPICS.get(t, _DEFAULT)
        items.append({"skill": t, "category": skill_category(t), "why": reasons[t], **info})

    schedule = []
    for i in range(7):
        if not items:
            schedule.append({"day": f"Day {i+1}", "plan": "Mock interview practice and resume polish."})
            continue
        t = items[i % len(items)]
        if i < len(items):
            plan = f"Study {t['skill']}, then practise: {t['practice']}"
        else:
            plan = f"Build with {t['skill']}: {t['project']}"
        schedule.append({"day": f"Day {i+1}", "plan": plan})

    portfolio = []
    if not profile.projects:
        portfolio.append("Add 2–3 projects with a README, screenshots and a live demo link.")
    if not any("github" in l.lower() for l in profile.links):
        portfolio.append("Create a GitHub profile README and pin your best repositories.")
    if items:
        portfolio.append(f"Build one project featuring {items[0]['skill']} and describe measurable results.")
    portfolio.append("Write a short README for each project: problem, approach, results, how to run.")
    return {"topics": items, "schedule": schedule, "portfolio": portfolio}

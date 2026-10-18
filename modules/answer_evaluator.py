"""Score interview answers and build the final report.

Two engines:
* AI (Gemini): scores, feedback, sample answer. ``source == "ai"``.
* Fallback: keyword-coverage + structure heuristics. ``source == "fallback"``. It cannot judge
  technical correctness, so that field is ``None`` and the UI labels the result as non-AI.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple

import config
from modules.llm_client import SYSTEM_GUARD, GeminiClient, LLMError, wrap
from modules.question_generator import Question

DISCLAIMER = ("Scores are AI-generated (or heuristic) practice guidance, not an official hiring assessment. "
              "Real interviewers weigh many other factors.")

_STAR = {"situation": r"situation|context|when i|at that time", "task": r"task|goal|responsib|needed to",
         "action": r"\bi (built|wrote|decided|led|created|implemented|used|analy[sz]ed|fixed)|action|so i",
         "result": r"result|outcome|improv|reduced|increased|achieved|learned|%"}
_CONNECTORS = r"\b(because|therefore|first|second|then|finally|for example|for instance|however|so that|in order to)\b"


@dataclass
class Evaluation:
    score: float                                   # 0-10
    correctness: Optional[float] = None            # 0-10, None when it can't be judged (fallback)
    relevance: Optional[float] = None
    clarity: Optional[float] = None
    feedback: str = ""
    missing_concepts: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    sample_answer: str = ""
    needs_followup: bool = False
    followup_question: Optional[str] = None
    source: str = "fallback"                        # "ai" | "fallback"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _clamp(x: Any, lo: float = 0.0, hi: float = 10.0) -> float:
    try:
        return max(lo, min(hi, float(x)))
    except (TypeError, ValueError):
        return lo


def concept_hits(answer: str, concepts: List[str]) -> Tuple[List[str], List[str]]:
    low = answer.lower()
    covered, missing = [], []
    for c in concepts:
        alts = [a.strip().lower() for a in c.split("|") if a.strip()]
        ok = any(re.search(rf"(?<![a-z0-9]){re.escape(a)}", low) for a in alts) if alts else False
        (covered if ok else missing).append(c.split("|")[0].strip())
    return covered, missing


# ---------------------------------------------------------------- fallback
def fallback_evaluate(question: Question, answer: str) -> Evaluation:
    answer = (answer or "").strip()
    words = len(answer.split())
    if words < 5:
        return Evaluation(score=0.0, feedback="No meaningful answer was provided.",
                          missing_concepts=[c.split("|")[0] for c in question.concepts],
                          suggestions=["Write at least a few sentences that address the question directly."],
                          needs_followup=False, source="fallback")
    concepts = question.concepts
    covered, missing = concept_hits(answer, concepts)
    coverage = len(covered) / len(concepts) if concepts else 0.5

    structure = 0.0
    if question.category in ("Behavioral", "Experience", "Project"):
        hit = sum(1 for rx in _STAR.values() if re.search(rx, answer, re.I))
        structure = hit / len(_STAR)
    else:
        structure = min(1.0, len(re.findall(_CONNECTORS, answer, re.I)) / 3)
    length_ok = min(1.0, words / 60) if words < 60 else (1.0 if words <= 250 else 0.8)
    clarity = 10 * (0.5 * structure + 0.5 * length_ok)
    relevance = 10 * min(1.0, coverage * 1.2 + 0.1)
    score = round(10 * (0.55 * coverage + 0.25 * (structure) + 0.20 * length_ok), 1)

    suggestions: List[str] = []
    if missing:
        suggestions.append("Cover these points: " + ", ".join(missing[:4]) + ".")
    if words < 40:
        suggestions.append("Your answer is short. Add a concrete example or a bit more explanation.")
    if question.category in ("Behavioral", "Experience", "Project") and structure < 0.75:
        suggestions.append("Use the STAR structure: Situation, Task, Action, Result (with a measurable outcome).")
    if question.category == "Technical" and structure < 0.34:
        suggestions.append("Structure your reasoning with connecting words (because, for example, however, finally).")
    if words > 250:
        suggestions.append("Aim for a focused 1–2 minute answer (roughly 100–200 words).")

    sample = ("Non-AI template: a strong answer would clearly cover "
              + (", ".join(c.split("|")[0] for c in concepts) if concepts else "the key ideas")
              + ", give one concrete example, and end with the outcome or trade-off.")
    return Evaluation(
        score=score, correctness=None, relevance=round(relevance, 1), clarity=round(clarity, 1),
        feedback=(f"Keyword check: you touched on {len(covered)} of {len(concepts)} expected points. "
                  "This heuristic cannot verify technical correctness. Enable the AI for deeper feedback."),
        missing_concepts=missing, suggestions=suggestions, sample_answer=sample,
        needs_followup=bool(missing) and score < 6.5,
        followup_question=(f"You didn't mention {missing[0]}. Can you explain how it applies here?" if missing else None),
        source="fallback")


# ---------------------------------------------------------------- AI
def _validate_eval(raw: Any) -> Evaluation:
    if not isinstance(raw, dict) or "score" not in raw:
        raise ValueError("evaluation missing score")
    def strs(key: str, limit: int) -> List[str]:
        v = raw.get(key, [])
        return [str(x).strip()[:300] for x in v if str(x).strip()][:limit] if isinstance(v, list) else []
    follow = str(raw.get("followup_question") or "").strip()[:300] or None
    return Evaluation(
        score=round(_clamp(raw["score"]), 1), correctness=_clamp(raw.get("correctness", raw["score"])),
        relevance=_clamp(raw.get("relevance", raw["score"])), clarity=_clamp(raw.get("clarity", raw["score"])),
        feedback=str(raw.get("feedback", ""))[:800], missing_concepts=strs("missing_concepts", 6),
        suggestions=strs("suggestions", 5), sample_answer=str(raw.get("sample_answer", ""))[:1500],
        needs_followup=bool(raw.get("needs_followup", False)) and follow is not None,
        followup_question=follow, source="ai")


def ai_evaluate(client: GeminiClient, question: Question, answer: str, role: str, difficulty: str) -> Evaluation:
    prompt = (
        f"Role: {role}\nDifficulty: {difficulty}\nQuestion: {question.text}\n"
        f"Concepts a good answer may cover: {', '.join(c.split('|')[0] for c in question.concepts) or 'n/a'}\n\n"
        "Evaluate the candidate's answer honestly and strictly but constructively. Score 0-10 (5 = adequate, 8+ = strong). "
        "Judge only what is written.\n\n" + wrap("candidate_answer", answer[: config.MAX_ANSWER_CHARS]) +
        '\n\nReturn JSON: {"score":number,"correctness":number,"relevance":number,"clarity":number,'
        '"feedback":str,"missing_concepts":[str],"suggestions":[str],"sample_answer":str,'
        '"needs_followup":bool,"followup_question":str|null}'
    )
    return _validate_eval(client.generate_json(prompt, system=SYSTEM_GUARD))


def evaluate_answer(question: Question, answer: str, role: str, difficulty: str,
                    client: Optional[GeminiClient] = None) -> Tuple[Evaluation, Optional[str]]:
    """Return (evaluation, notice). A notice is set whenever the fallback evaluator was used."""
    answer = (answer or "")[: config.MAX_ANSWER_CHARS]
    if len(answer.split()) < 5:
        return fallback_evaluate(question, answer), None
    if client is not None and client.is_configured:
        try:
            return ai_evaluate(client, question, answer, role, difficulty), None
        except (LLMError, ValueError) as exc:
            return fallback_evaluate(question, answer), f"{exc} Showing the non-AI keyword evaluation instead."
    return fallback_evaluate(question, answer), "AI is not configured. Showing the non-AI keyword evaluation."


# ---------------------------------------------------------------- report
@dataclass
class Report:
    overall: float
    answered: int
    by_category: Dict[str, float]
    strongest: List[str]
    weakest: List[str]
    recurring_missing: List[Tuple[str, int]]
    skills_to_revise: List[str]
    seven_day_plan: List[Dict[str, str]]
    coach_summary: Optional[str] = None
    ai_used: bool = False
    disclaimer: str = DISCLAIMER


def build_seven_day_plan(weak_skills: List[str], missing_concepts: List[str], role: str) -> List[Dict[str, str]]:
    ws = (weak_skills + ["core fundamentals"] * 3)[:3]
    mc = (missing_concepts + ["the topics you missed"] * 2)[:2]
    return [
        {"day": "Day 1", "focus": f"Review {ws[0]}", "tasks": f"Re-read notes on {ws[0]}; write 5 short answers from memory; compare with the key points you missed."},
        {"day": "Day 2", "focus": f"Practice {ws[1]}", "tasks": f"Solve 5 practice problems or write a small script that uses {ws[1]}."},
        {"day": "Day 3", "focus": "Missed concepts", "tasks": f"Study and explain aloud: {', '.join(mc)}. Record yourself and listen back."},
        {"day": "Day 4", "focus": f"Project deep-dive", "tasks": "Pick your strongest project; prepare a 2-minute story (problem, approach, result, trade-offs)."},
        {"day": "Day 5", "focus": f"Practice {ws[2]}", "tasks": f"Redo the questions you scored lowest on, then add one new question about {ws[2]}."},
        {"day": "Day 6", "focus": "Behavioral (STAR)", "tasks": "Write 3 STAR stories: a challenge, a teamwork moment, a mistake you learned from."},
        {"day": "Day 7", "focus": "Full mock interview", "tasks": f"Take a fresh mock interview for {role} here and compare your scores with this report."},
    ]


def build_report(records: List[Dict[str, Any]], role: str, client: Optional[GeminiClient] = None) -> Optional[Report]:
    """records: [{question: Question, answer: str, evaluation: Evaluation}, ...]"""
    scored = [r for r in records if r.get("evaluation") and r["answer"].strip()]
    if not scored:
        return None
    overall = round(mean(r["evaluation"].score for r in scored), 1)
    cats: Dict[str, List[float]] = defaultdict(list)
    skill_scores: Dict[str, List[float]] = defaultdict(list)
    missing = Counter()
    for r in scored:
        q: Question = r["question"]; ev: Evaluation = r["evaluation"]
        cats[q.category].append(ev.score)
        if q.skill:
            skill_scores[q.skill].append(ev.score)
        missing.update(m.lower() for m in ev.missing_concepts)
    by_cat = {c: round(mean(v), 1) for c, v in cats.items()}
    ranked = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)
    strongest = [f"{c} ({s}/10)" for c, s in ranked[:2] if s >= 5] or ["No area scored 5/10 or higher yet"]
    weakest = [f"{c} ({s}/10)" for c, s in ranked[::-1][:2] if s < 8] or ["No clearly weak area"]
    weak_skills = [s for s, v in sorted(skill_scores.items(), key=lambda kv: mean(kv[1])) if mean(v) < 7][:5]
    recurring = [(k, v) for k, v in missing.most_common(6) if v >= 2] or missing.most_common(3)
    plan = build_seven_day_plan(weak_skills, [k for k, _ in missing.most_common(3)], role)
    report = Report(overall, len(scored), by_cat, strongest, weakest, recurring, weak_skills, plan,
                    ai_used=any(r["evaluation"].source == "ai" for r in scored))
    if client is not None and client.is_configured and report.ai_used:
        try:
            digest = "\n".join(f"- [{r['question'].category}] score {r['evaluation'].score}: "
                               f"{'; '.join(r['evaluation'].suggestions[:2])}" for r in scored)
            text = client.generate(
                "Write a 3-4 sentence, encouraging but honest coaching summary of this mock interview for a "
                f"{role} candidate. Use only the data below.\n\n" + wrap("job_data", digest), system=SYSTEM_GUARD)
            report.coach_summary = text.strip()[:900]
        except LLMError:
            pass
    return report

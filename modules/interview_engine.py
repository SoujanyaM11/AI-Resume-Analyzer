"""Interview session logic: question queue, answer submission, follow-ups, progress."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import config
from modules.answer_evaluator import Evaluation, evaluate_answer
from modules.llm_client import GeminiClient
from modules.question_generator import Question, build_questions
from modules.resume_analyzer import ResumeProfile

MAX_FOLLOWUPS = 3


@dataclass
class InterviewSession:
    role: str
    difficulty: str
    questions: List[Question]
    notice: Optional[str] = None
    index: int = 0
    records: List[Dict[str, Any]] = field(default_factory=list)   # question, answer, evaluation, time
    pending_eval: Optional[Evaluation] = None                      # evaluation awaiting "Next"
    ended: bool = False
    followups_used: int = 0

    # ---- derived ------------------------------------------------------
    @property
    def current(self) -> Optional[Question]:
        return self.questions[self.index] if self.index < len(self.questions) else None

    @property
    def total(self) -> int:
        return len(self.questions)

    @property
    def progress(self) -> float:
        return min(1.0, len(self.records) / self.total) if self.total else 0.0

    @property
    def finished(self) -> bool:
        return self.ended or (self.index >= len(self.questions) and self.pending_eval is None)


def start_session(profile: ResumeProfile, role: str, difficulty: str, n: int,
                  client: Optional[GeminiClient] = None) -> InterviewSession:
    questions, notice = build_questions(profile, role, difficulty, n, client)
    return InterviewSession(role=role, difficulty=difficulty, questions=questions, notice=notice)


def submit_answer(session: InterviewSession, answer: str,
                  client: Optional[GeminiClient] = None) -> Optional[str]:
    """Evaluate the current answer and store it. Returns a notice about fallback use, if any."""
    q = session.current
    if q is None or session.pending_eval is not None:
        return None
    answer = (answer or "").strip()[: config.MAX_ANSWER_CHARS]
    ev, notice = evaluate_answer(q, answer, session.role, session.difficulty, client)
    session.records.append({"question": q, "answer": answer, "evaluation": ev,
                            "time": datetime.now().strftime("%H:%M:%S")})
    session.pending_eval = ev
    return notice


def next_question(session: InterviewSession) -> None:
    """Advance after an evaluation was shown; inserts a follow-up when the evaluation asks for one."""
    ev = session.pending_eval
    q = session.current
    if ev is not None and q is not None and ev.needs_followup and ev.followup_question \
            and q.category != "Follow-up" and session.followups_used < MAX_FOLLOWUPS:
        follow = Question(ev.followup_question, "Follow-up", q.difficulty,
                          (ev.missing_concepts or q.concepts)[:2], "follow-up", q.skill)
        session.questions.insert(session.index + 1, follow)
        session.followups_used += 1
    session.index += 1
    session.pending_eval = None


def skip_question(session: InterviewSession) -> None:
    if session.current is not None and session.pending_eval is None:
        session.index += 1


def end_interview(session: InterviewSession) -> None:
    session.ended = True
    session.pending_eval = None

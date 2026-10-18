"""Streamlit pages. All business logic is delegated to ``modules``."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import List, Optional

import pandas as pd
import streamlit as st

import config
from modules import interview_engine as engine
from modules import job_sources, voice_utils
from modules.answer_evaluator import DISCLAIMER, build_report
from modules.job_matcher import filter_results, missing_skills_across, rank_jobs
from modules.learning_roadmap import build_roadmap
from modules.llm_client import GeminiClient, LLMError
from modules.resume_analyzer import (ai_resume_summary, analyze_resume, role_gap, suggest_improvements)
from modules.resume_parser import ResumeParseError, clean_pasted_text, extract_text

PAGES = ["Home", "Resume analysis", "Mock interview", "Performance report",
         "Job recommendations", "Learning roadmap", "Settings & API status"]
SAMPLE_RESUME = Path(__file__).resolve().parent.parent / "data" / "sample_resume.txt"


# ------------------------------------------------------------------ state helpers
def init_state() -> None:
    ss = st.session_state
    ss.setdefault("page", "Home")
    ss.setdefault("client", GeminiClient())
    ss.setdefault("use_ai", True)
    ss.setdefault("role", config.ROLES[0])
    ss.setdefault("difficulty", "Intermediate")
    for k in ("resume_text", "profile", "interview", "report", "live_jobs", "job_results", "ai_summary"):
        ss.setdefault(k, None)
    ss.setdefault("weights", dict(config.DEFAULT_MATCH_WEIGHTS))


def active_client() -> Optional[GeminiClient]:
    c: GeminiClient = st.session_state.client
    return c if (st.session_state.use_ai and c.is_configured) else None


def clear_session_data() -> None:
    for k in ("resume_text", "profile", "interview", "report", "live_jobs", "job_results", "ai_summary"):
        st.session_state[k] = None
    for k in [k for k in st.session_state if str(k).startswith("ans_")]:
        del st.session_state[k]


def go(page: str) -> None:
    st.session_state.page = page


def badge(kind: str, label: str) -> str:
    return f'<span class="cc-badge {kind}">{html.escape(label)}</span>'


def pills(items: List[str], kind: str = "") -> str:
    if not items:
        return '<span class="cc-muted">None found</span>'
    return "".join(f'<span class="cc-pill {kind}">{html.escape(i)}</span>' for i in items)


def notice(msg: Optional[str]) -> None:
    if msg:
        st.info(msg)


# ------------------------------------------------------------------ sidebar
def sidebar() -> None:
    with st.sidebar:
        st.markdown(f'<div class="cc-brand"><div class="cc-logo">🧠</div><div><div class="cc-brand-title">'
                    f'{html.escape(config.APP_NAME)}</div><div class="cc-brand-sub">Your Growth Partner</div></div></div>',
                    unsafe_allow_html=True)
        st.radio("Navigate", PAGES, key="page", label_visibility="collapsed")
        st.divider()
        st.selectbox("Target role", config.ROLES, key="role")
        st.selectbox("Difficulty", config.DIFFICULTIES, key="difficulty")
        c: GeminiClient = st.session_state.client
        if c.is_configured:
            st.toggle("Use AI (Gemini)", key="use_ai", help="Turn off to use rule-based fallback mode only.")
        mode = "AI enabled" if active_client() else "Fallback mode (no AI)"
        st.markdown(badge("ai" if active_client() else "fallback", mode), unsafe_allow_html=True)
        if not c.is_configured:
            st.caption("No API key found. Everything still works with local rules.")
        if st.session_state.profile is not None:
            st.divider()
            st.button("Clear my data", on_click=clear_session_data, width="stretch",
                      help="Removes the resume, interview and report from this session.")


# ------------------------------------------------------------------ home
def _metric(cls: str, icon: str, label: str, value: str, hint: str) -> str:
    return (f'<div class="cc-metric {cls}"><div class="dot">{icon}</div><div class="lbl">{html.escape(label)}</div>'
            f'<div class="val">{html.escape(value)}</div><div class="hint">{html.escape(hint)}</div></div>')


def _row(bg: str, icon: str, title: str, status: str, when: str = "") -> str:
    return (f'<div class="cc-row"><div class="ic" style="background:{bg}">{icon}</div><div style="flex:1"><div class="t">'
            f'{html.escape(title)}</div><div class="s">{html.escape(status)}</div></div>'
            f'<div class="s">{html.escape(when)}</div></div>')


def page_home() -> None:
    ss = st.session_state
    who = (ss.profile.name.split()[0] if ss.profile is not None and ss.profile.name else "there")
    st.markdown(
        f'<div class="cc-hero"><div class="hi">Hey {html.escape(who)} 👋</div><h1>Your career, our priority.</h1>'
        '<p>Upload a resume, practise role-specific questions, get scored feedback and see jobs that fit. '
        'Works without an API key using rule-based fallbacks.</p>'
        f'<div class="cc-hero-pills"><span>Target Role:<b>{html.escape(str(ss.role))}</b></span>'
        f'<span>Difficulty:<b>{html.escape(str(ss.difficulty))}</b></span></div>'
        '<div class="cc-hero-art">Better<br>Skills,<br>Bigger<br>Opportunities ♡</div></div>',
        unsafe_allow_html=True)

    cards = [("card_resume", "Resume analysis", "Resume Analysis", "Skills found & suggestions"),
             ("card_interview", "Mock interview", "Mock Interview", "Practise with AI feedback"),
             ("card_report", "Performance report", "Performance Report", "Track your progress"),
             ("card_jobs", "Job recommendations", "Job Recommendations", "Find jobs that fit you"),
             ("card_roadmap", "Learning roadmap", "Learning Roadmap", "Personalised plan for you")]
    for col, (key, page, title, desc) in zip(st.columns(5), cards):
        col.button(f"**{title}**\n\n{desc}", key=key, on_click=go, args=(page,), width="stretch")

    s = ss.interview
    answered = len(s.records) if s is not None else 0
    n_jobs = len(ss.job_results or [])
    left, right = st.columns([3, 2])
    with left:
        metrics = "".join([
            _metric("pink", "📄", "Resume", f"{len(ss.profile.skills)} skills" if ss.profile is not None else "Not analysed",
                    "Resume analysed" if ss.profile is not None else "Upload a resume"),
            _metric("blue", "👥", "Mock Interview", f"{answered} of {s.total} answered" if answered else "Not attempted",
                    "Keep practising" if answered else "Start now"),
            _metric("peach", "💼", "Job Matches", str(n_jobs), "New recommendations" if n_jobs else "Open job recommendations"),
            _metric("lav", "🗺️", "Learning Roadmap", "Available" if ss.profile is not None else "Needs a resume",
                    "Built from your resume" if ss.profile is not None else "Analyse a resume first"),
        ])
        st.markdown('<div class="cc-card"><div class="cc-panel-title">📈 Your Progress</div>'
                    '<div class="cc-panel-sub">At a glance, how you\'re doing</div>'
                    f'<div class="cc-metrics">{metrics}</div></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="cc-card"><div class="cc-panel-title">💡 Quick Tips</div><div class="cc-panel-sub">Small steps, big progress</div>'
            '<div class="cc-tips"><div><b>Focus on:</b><ul><li>Improving your resume (ATS keywords)</li>'
            '<li>Practising core DSA topics</li><li>Building real projects</li><li>Learning system design basics</li></ul></div>'
            '<div class="cc-note">You got this! ♡</div></div></div>', unsafe_allow_html=True)
    with right:
        last = s.records[-1]["time"] if answered else ""
        rows = "".join([
            _row("#EAF3FF", "📄", "Resume analysis", "Resume analysed" if ss.profile is not None else "No resume uploaded"),
            _row("#E8F8F0", "👥", "Mock interview", f"{answered} answered" if answered else "Not attempted yet", str(last)),
            _row("#F1ECFF", "🗺️", "Learning roadmap", "Your personalised plan" if ss.profile is not None else "Needs a resume"),
            _row("#FFF1E4", "💼", "Job recommendations", f"{n_jobs} matches" if n_jobs else "No jobs found yet"),
        ])
        st.markdown(f'<div class="cc-card"><div class="cc-panel-title">🕒 Recent Activity</div>{rows}</div>', unsafe_allow_html=True)
        st.markdown('<div class="cc-goal"><b>✨ Turn your goals into achievements</b>'
                    '<span>Your next opportunity is just a step away.</span></div>', unsafe_allow_html=True)

    st.subheader("Get started")
    steps = [
        ("Upload your resume", ss.profile is not None, "Resume analysis", "Go to resume analysis"),
        ("Choose a target role in the sidebar", ss.profile is not None, None, None),
        ("Practise a mock interview", bool(ss.interview and ss.interview.records), "Mock interview", "Start practising"),
        ("Explore job matches", bool(ss.job_results), "Job recommendations", "See job matches"),
    ]
    st.markdown('<div class="cc-card">', unsafe_allow_html=True)
    for i, (label, done, page, btn) in enumerate(steps, 1):
        c1, c2 = st.columns([5, 2])
        c1.markdown(f'<div class="cc-step"><div class="cc-dot {"done" if done else ""}">{"✓" if done else i}</div>'
                    f'<div>{html.escape(label)}</div></div>', unsafe_allow_html=True)
        if page:
            c2.button(btn, key=f"home_{i}", on_click=go, args=(page,), width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

    if ss.profile is None:
        st.button("Try it with a sample resume", on_click=load_sample, type="primary")
        st.caption("The sample resume is fictional demo data.")
    with st.expander("Privacy: what is sent where"):
        st.markdown(
            "- Your resume is processed in memory for this browser session and is not stored by this app.\n"
            "- With AI enabled, only a **redacted digest** (skills, project and experience text; no email, phone, links "
            "or your name) and your interview answers are sent to Google's Gemini API.\n"
            "- On Gemini's free tier, Google may use submitted content to improve its products. Do not submit "
            "anything confidential. Turn AI off in the sidebar to keep everything local.\n"
            "- Use **Clear my data** in the sidebar at any time.")


def load_sample() -> None:
    text = SAMPLE_RESUME.read_text(encoding="utf-8")
    st.session_state.resume_text = text
    st.session_state.profile = analyze_resume(text, is_demo=True)
    st.session_state.page = "Resume analysis"


# ------------------------------------------------------------------ resume
def page_resume() -> None:
    st.title("Resume analysis")
    ss = st.session_state
    tab_up, tab_paste = st.tabs(["Upload PDF or DOCX", "Paste text"])
    with tab_up:
        f = st.file_uploader("Resume file", type=["pdf", "docx"], help=f"Max {config.MAX_UPLOAD_MB} MB. Text-based files only.")
        if f is not None and st.button("Analyse resume", type="primary", key="an_file"):
            try:
                text = extract_text(f.name, f.getvalue())
                ss.resume_text, ss.profile = text, analyze_resume(text)
                ss.interview = ss.report = ss.ai_summary = None
            except ResumeParseError as exc:
                st.error(str(exc))
    with tab_paste:
        pasted = st.text_area("Paste your resume text", height=200, key="pasted_resume")
        if st.button("Analyse pasted text", key="an_paste"):
            try:
                text = clean_pasted_text(pasted)
                ss.resume_text, ss.profile = text, analyze_resume(text)
                ss.interview = ss.report = ss.ai_summary = None
            except ResumeParseError as exc:
                st.error(str(exc))
    st.button("Load sample resume (demo)", on_click=load_sample)

    p = ss.profile
    if p is None:
        st.info("Upload or paste a resume to see your analysis. Nothing is stored after this session.")
        return
    if p.is_demo:
        st.warning("Showing the fictional sample resume (demo data).")

    st.subheader("Details found")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Name:** {p.name or 'Not found'}")
        st.markdown(f"**Email:** {p.email or 'Not found'}")
        st.markdown(f"**Phone:** {p.phone or 'Not found'}")
        st.markdown(f"**Links:** {', '.join(p.links) if p.links else 'Not found'}")
    with c2:
        st.markdown(f"**Estimated experience level:** {p.experience_level}")
        st.markdown(f"**Years in work history (from dates):** {p.years_experience:g}")
        st.markdown(f"**Highest degree detected:** {p.education_level.title() if p.education_level else 'Not found'}")
        st.caption("The experience level is an estimate based on date ranges found in the text.")

    with st.expander("Education", expanded=True):
        for e in p.education or ["Not found"]:
            st.write(e)
    with st.expander("Experience and internships", expanded=True):
        if not p.experience:
            st.write("Not found")
        for e in p.experience:
            st.markdown(f"**{e.title}**")
            for d in e.details:
                st.markdown(f"- {d}")
    with st.expander("Projects", expanded=True):
        if not p.projects:
            st.write("Not found")
        for e in p.projects:
            st.markdown(f"**{e.title}**")
            for d in e.details:
                st.markdown(f"- {d}")
    with st.expander("Certifications"):
        for c in p.certifications or ["Not found"]:
            st.write(c)

    st.subheader(f"Fit for {ss.role}")
    strengths, miss_core, miss_nice = role_gap(p, ss.role)
    st.markdown("**Skills found that matter for this role**")
    st.markdown(pills(strengths, "ok"), unsafe_allow_html=True)
    st.markdown("**Core skills not found on the resume**")
    st.markdown(pills(miss_core, "miss"), unsafe_allow_html=True)
    st.markdown("**Other skills detected**")
    st.markdown(pills([s for s in p.skills if s not in strengths]), unsafe_allow_html=True)

    st.subheader("Suggested improvements")
    tips = suggest_improvements(p, ss.resume_text or "")
    for t in tips or ["No rule-based issues found."]:
        st.markdown(f"- {t}")
    st.caption("These tips come from simple rules, not AI.")

    st.subheader("Summary")
    st.write(p.summary_text or "The resume has no summary section.")
    client = active_client()
    if client:
        if st.button("Generate AI summary", help="Sends a redacted digest of your resume to Gemini."):
            try:
                with st.spinner("Asking Gemini..."):
                    ss.ai_summary = ai_resume_summary(client, p, ss.role)
            except LLMError as exc:
                st.error(f"{exc} The rule-based analysis above is still available.")
        if ss.ai_summary:
            st.markdown(badge("ai", "AI-generated"), unsafe_allow_html=True)
            st.write(ss.ai_summary)


# ------------------------------------------------------------------ interview
def _start_interview(n: int) -> None:
    ss = st.session_state
    ss.interview = engine.start_session(ss.profile, ss.role, ss.difficulty, n, active_client())
    ss.report = None


def _submit(q_id: int) -> None:
    ss = st.session_state
    answer = ss.get(f"ans_{q_id}", "")
    if len(answer.strip()) < 1:
        ss["_answer_error"] = "Write an answer first, or use Skip."
        return
    ss["_answer_error"] = None
    ss["_eval_notice"] = engine.submit_answer(ss.interview, answer, active_client())


def _next() -> None:
    engine.next_question(st.session_state.interview)
    st.session_state["_eval_notice"] = None


def _skip() -> None:
    engine.skip_question(st.session_state.interview)


def _end() -> None:
    engine.end_interview(st.session_state.interview)


def _render_eval(ev) -> None:
    st.markdown(badge("ai", "AI evaluation") if ev.source == "ai" else badge("fallback", "Non-AI keyword evaluation"),
                unsafe_allow_html=True)
    c = st.columns(4)
    c[0].metric("Score", f"{ev.score:g}/10")
    c[1].metric("Correctness", f"{ev.correctness:g}/10" if ev.correctness is not None else "n/a")
    c[2].metric("Relevance", f"{ev.relevance:g}/10" if ev.relevance is not None else "n/a")
    c[3].metric("Clarity", f"{ev.clarity:g}/10" if ev.clarity is not None else "n/a")
    if ev.feedback:
        st.write(ev.feedback)
    if ev.missing_concepts:
        st.markdown("**Missing concepts:** " + ", ".join(ev.missing_concepts))
    if ev.suggestions:
        st.markdown("**How to improve**")
        for s in ev.suggestions:
            st.markdown(f"- {s}")
    if ev.sample_answer:
        with st.expander("Sample strong answer" if ev.source == "ai" else "What a strong answer covers"):
            st.write(ev.sample_answer)


def page_interview() -> None:
    st.title("Mock interview")
    ss = st.session_state
    if ss.profile is None:
        st.info("Analyse a resume first so questions can be based on your experience.")
        st.button("Go to resume analysis", on_click=go, args=("Resume analysis",))
        return
    s = ss.interview
    if s is None:
        st.write(f"Role: **{ss.role}** · Difficulty: **{ss.difficulty}** (change both in the sidebar)")
        n = st.slider("Number of questions", 3, config.MAX_QUESTION_COUNT, config.DEFAULT_QUESTION_COUNT)
        st.button("Start interview", type="primary", on_click=_start_interview, args=(n,))
        return

    notice(s.notice)
    st.progress(s.progress, text=f"{len(s.records)} of {s.total} answered")

    if s.finished:
        st.success("Interview finished. Your report is ready.")
        c1, c2 = st.columns(2)
        c1.button("View performance report", type="primary", on_click=go, args=("Performance report",))
        c2.button("Start a new interview", on_click=lambda: ss.update(interview=None, report=None))
    else:
        q = s.current
        st.markdown(f'<div class="cc-card"><span class="cc-muted">{html.escape(q.category)} · {html.escape(q.difficulty)}'
                    f' · question {min(s.index + 1, s.total)} of {s.total}</span>'
                    f'<div class="cc-question">{html.escape(q.text)}</div></div>', unsafe_allow_html=True)
        if s.pending_eval is None:
            with st.expander("Voice options (optional)"):
                st.components.v1.html(voice_utils.speak_component_html(q.text), height=50)
                if hasattr(st, "audio_input"):
                    audio = st.audio_input("Record your answer", key=f"audio_{q.id}")
                    client = active_client()
                    if audio is not None:
                        if client is None:
                            st.caption("Transcription needs an API key and AI enabled. Type your answer instead.")
                        elif st.button("Transcribe recording", key=f"tr_{q.id}",
                                       help="Sends the audio to Gemini for transcription."):
                            try:
                                text = voice_utils.transcribe_audio(client, audio.getvalue(), audio.type or "audio/wav")
                                if text:
                                    ss[f"ans_{q.id}"] = text
                                    st.rerun()
                                else:
                                    st.warning("No speech was detected. Type your answer instead.")
                            except LLMError as exc:
                                st.error(f"{exc} Type your answer instead.")
                else:
                    st.caption("Voice recording is not available in this Streamlit version. Use text input.")
            st.text_area("Your answer", key=f"ans_{q.id}", height=180, max_chars=config.MAX_ANSWER_CHARS,
                         help="Aim for 1–2 minutes of speaking (about 100–200 words).")
            if ss.get("_answer_error"):
                st.warning(ss["_answer_error"])
            c1, c2, c3 = st.columns(3)
            c1.button("Submit answer", type="primary", on_click=_submit, args=(q.id,), width="stretch")
            c2.button("Skip question", on_click=_skip, width="stretch")
            c3.button("End interview", on_click=_end, width="stretch")
        else:
            notice(ss.get("_eval_notice"))
            _render_eval(s.pending_eval)
            last = s.index + 1 >= s.total
            c1, c2 = st.columns(2)
            c1.button("Finish interview" if last else "Next question", type="primary", on_click=_next, width="stretch")
            c2.button("End interview", on_click=_end, width="stretch")

    if s.records:
        with st.expander(f"Session history ({len(s.records)})"):
            for i, r in enumerate(s.records, 1):
                ev = r["evaluation"]
                st.markdown(f"**{i}. {r['question'].text}**  \nScore: {ev.score:g}/10 · {r['time']}")
                st.caption((r["answer"] or "(skipped)")[:300])


# ------------------------------------------------------------------ report
def report_markdown(rep, role: str) -> str:
    lines = [f"# Mock interview report ({role})", f"Overall score: {rep.overall}/10 across {rep.answered} answers", "",
             "## Strongest areas", *[f"- {x}" for x in rep.strongest], "", "## Weakest areas", *[f"- {x}" for x in rep.weakest], "",
             "## Skills to revise", *[f"- {x}" for x in (rep.skills_to_revise or ["None flagged"])], "", "## Seven-day plan",
             *[f"- **{d['day']} – {d['focus']}:** {d['tasks']}" for d in rep.seven_day_plan], "", f"_{rep.disclaimer}_"]
    return "\n".join(lines)


def page_report() -> None:
    st.title("Interview performance report")
    ss = st.session_state
    s = ss.interview
    if s is None or not s.records:
        st.info("Answer at least one interview question to see your report.")
        st.button("Go to mock interview", on_click=go, args=("Mock interview",))
        return
    rep = build_report(s.records, s.role, active_client())
    ss.report = rep
    if rep is None:
        st.info("No answered questions yet.")
        return
    st.caption(DISCLAIMER)
    c1, c2 = st.columns(2)
    c1.metric("Overall score", f"{rep.overall}/10")
    c2.metric("Questions answered", rep.answered)
    st.markdown(badge("ai", "Includes AI evaluation") if rep.ai_used else badge("fallback", "Non-AI keyword evaluation only"),
                unsafe_allow_html=True)
    if rep.coach_summary:
        st.write(rep.coach_summary)
    st.subheader("Score by category")
    st.bar_chart(pd.Series(rep.by_category, name="Average score"), horizontal=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Strongest areas")
        for x in rep.strongest:
            st.markdown(f"- {x}")
    with c2:
        st.subheader("Weakest areas")
        for x in rep.weakest:
            st.markdown(f"- {x}")
    st.subheader("Recurring gaps")
    if rep.recurring_missing:
        for k, v in rep.recurring_missing:
            st.markdown(f"- {k} (missed in {v} answer{'s' if v != 1 else ''})")
    else:
        st.write("No missing concepts recorded.")
    st.subheader("Skills to revise")
    st.markdown(pills(rep.skills_to_revise, "miss"), unsafe_allow_html=True)
    st.subheader("Seven-day preparation plan")
    for d in rep.seven_day_plan:
        st.markdown(f"**{d['day']} – {d['focus']}**  \n{d['tasks']}")
    st.download_button("Download report (Markdown)", report_markdown(rep, s.role), "interview_report.md", "text/markdown")


# ------------------------------------------------------------------ jobs
def page_jobs() -> None:
    st.title("Job recommendations")
    ss = st.session_state
    if ss.profile is None:
        st.info("Analyse a resume first to compare it with job descriptions.")
        st.button("Go to resume analysis", on_click=go, args=("Resume analysis",))
        return
    src = st.radio("Job data", ["Sample jobs (offline demo)", "Live listings (Arbeitnow)"], horizontal=True)
    jobs = None
    if src.startswith("Sample"):
        st.markdown(badge("sample", "SAMPLE DATA"), unsafe_allow_html=True)
        st.caption("Fictional listings for demonstration. Companies and links are not real, and there is nothing to apply to.")
        try:
            jobs = job_sources.load_sample_jobs()
        except job_sources.JobSourceError as exc:
            st.error(str(exc))
    else:
        st.caption("Live listings come from Arbeitnow's public API and link back to the original posting. "
                   "Skills are detected from the text, so required and preferred skills are not distinguished.")
        if st.button("Fetch live listings"):
            try:
                with st.spinner("Contacting the job feed..."):
                    ss.live_jobs = job_sources.fetch_live_jobs(force=True)
            except job_sources.JobSourceError as exc:
                st.error(f"{exc} Switch to sample jobs to keep exploring.")
        jobs = ss.live_jobs
        if jobs is None:
            st.info("Click “Fetch live listings” to load current postings, or use the sample jobs.")
            return

    with st.expander("Matching weights (advanced)"):
        w = ss.weights
        cols = st.columns(4)
        for col, key in zip(cols, ["skills", "experience", "education", "projects"]):
            w[key] = col.slider(key.title(), 0.0, 1.0, float(w[key]), 0.05, key=f"w_{key}")
        st.caption("Weights are normalised to sum to 100%, so only their ratios matter.")

    f1, f2, f3, f4 = st.columns([2, 2, 1, 2])
    role = f1.selectbox("Job role", ["Any", *config.ROLES], index=0)
    loc = f2.text_input("Location contains")
    remote = f3.checkbox("Remote only")
    min_score = f4.slider("Minimum match", 0, 100, 0)

    results = rank_jobs(ss.profile, jobs, w)
    ss.job_results = results
    shown = filter_results(results, role if src.startswith("Sample") else "Any", loc, remote, float(min_score))
    st.caption("The match score is a compatibility estimate from your resume text. It is not the probability of being hired.")
    if not shown:
        st.warning("No jobs match these filters. Lower the minimum match or clear the filters.")
    for r in shown[:25]:
        j = r.job
        tag = badge("sample", "SAMPLE") if j.get("is_sample") else badge("live", "LIVE")
        loc_txt = ("Remote" if j.get("remote") else j.get("location", "")) or "Location not specified"
        with st.expander(f"{r.score:g}%  ·  {j['title']}  ·  {j['company']}  ·  {loc_txt}"):
            st.markdown(f"{tag} {html.escape(str(j.get('source', '')))}", unsafe_allow_html=True)
            st.write((j.get("description") or "")[:500])
            st.markdown("**Matching skills**")
            st.markdown(pills(r.matching_skills, "ok"), unsafe_allow_html=True)
            st.markdown("**Missing skills**")
            st.markdown(pills(r.missing_skills, "miss"), unsafe_allow_html=True)
            comp = pd.DataFrame({"Component": [k.title() for k in r.components],
                                 "Score (0–1)": list(r.components.values()),
                                 "Weight": [f"{r.weights[k]:.0%}" for k in r.components]})
            st.dataframe(comp, hide_index=True, width="stretch")
            for n in r.notes:
                st.caption(n)
            if j.get("url"):
                st.link_button("View original posting", j["url"])
                st.caption(f"Source: {j['source']} · retrieved {j.get('retrieved_at')}")
            else:
                st.caption("Sample listing: no application link.")


# ------------------------------------------------------------------ roadmap
def page_roadmap() -> None:
    st.title("Learning roadmap")
    ss = st.session_state
    if ss.profile is None:
        st.info("Analyse a resume first to build a roadmap.")
        st.button("Go to resume analysis", on_click=go, args=("Resume analysis",))
        return
    gaps = missing_skills_across(ss.job_results or [])
    road = build_roadmap(ss.profile, ss.role, gaps, ss.report)
    used = ["target role", "resume skills"] + (["job gaps"] if gaps else []) + (["interview results"] if ss.report else [])
    st.caption("Built from: " + ", ".join(used) + ". Rule-based, not AI. Resource names are listed without links because I could not verify URLs.")
    st.subheader("Priority topics")
    for t in road["topics"] or []:
        with st.expander(f"{t['skill']} · {t['why']}", expanded=False):
            st.markdown(f"**Project:** {t['project']}")
            st.markdown(f"**Practice:** {t['practice']}")
            st.markdown("**Free resources (search by name):** " + ", ".join(t["resources"]))
    if not road["topics"]:
        st.success("No gaps found for this role from the resume text. Practise interviews and polish projects.")
    st.subheader("Seven-day study schedule")
    for d in road["schedule"]:
        st.markdown(f"**{d['day']}:** {d['plan']}")
    st.subheader("Portfolio improvements")
    for p in road["portfolio"]:
        st.markdown(f"- {p}")


# ------------------------------------------------------------------ settings
def page_settings() -> None:
    st.title("Settings and API status")
    c: GeminiClient = st.session_state.client
    st.markdown(f"**API key configured:** {'Yes' if c.is_configured else 'No'}  \n"
                "The key is read from the `GEMINI_API_KEY` environment variable or hosting secrets and is never shown.")
    if st.button("Check connection", disabled=not c.is_configured):
        with st.spinner("Checking..."):
            status = c.check_status()
        (st.success if status["ok"] else st.error)(status["message"] + (f" Model: {status['model']}" if status["model"] else ""))
    if not c.is_configured:
        st.info("Set `GEMINI_API_KEY` (see README) to enable AI features. Without it the app uses local question banks, "
                "keyword evaluation and rule-based job matching.")
    st.markdown(f"**Requests sent this session:** {c.calls_made}")
    st.caption("Free-tier limits change and are shown in Google AI Studio's rate-limit page for your project. "
               "If you hit a limit, the app falls back to non-AI mode.")
    st.subheader("Your data")
    st.write("Resume text lives only in this browser session. Nothing is written to disk by this app.")
    st.button("Clear resume, interview and report", on_click=clear_session_data)

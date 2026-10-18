# AI Career Coach

Upload a resume, practise interview questions based on your own projects and experience, get scored feedback, and see job matches with transparent scoring. Built with Streamlit and Python. It **works fully without an API key** using rule-based fallbacks, and uses Google's Gemini API when a key is provided.

> Status: runs locally and passes the test suite. It has **not** been deployed anywhere, and nothing here promises permanent free hosting or unlimited API usage.

## Features

| Area | With a Gemini key | Without a key (fallback) |
|---|---|---|
| Resume analysis | Rule-based extraction + optional AI summary | Rule-based extraction (PDF, DOCX, or pasted text) |
| Questions | Generated from a redacted resume digest | Local question bank + templates that name your real projects and experience |
| Answer evaluation | Score, sub-scores, missing concepts, sample answer | Keyword and structure heuristics, labelled **non-AI**; correctness shows "n/a" |
| Follow-ups | AI-suggested | Generated when key concepts are missed (max 1 per question) |
| Report | Adds an AI coaching summary | Scores, weak areas, recurring gaps, 7-day plan |
| Jobs | Same | Weighted, explainable matching on sample or live jobs |
| Roadmap | Same | Rule-based topics, projects, schedule |
| Voice | Spoken questions (browser); optional Gemini transcription of recorded answers | Spoken questions work in supporting browsers; typing always works |

Every AI-derived result is badged "AI", and every fallback result is badged as non-AI. The app never switches provider silently.

## Project structure

```
ai-career-coach/
  app.py                  Streamlit entry point
  config.py               Limits, roles, default match weights, env handling
  requirements.txt / requirements-dev.txt
  .env.example  .gitignore  .streamlit/config.toml
  data/sample_resume.txt  Fictional demo resume
  data/sample_jobs.json   Fictional sample jobs (clearly labelled, no links)
  modules/
    resume_parser.py      PDF/DOCX validation + text extraction
    resume_analyzer.py    Sections, skills, level estimate, tips
    skills_db.py          Skill taxonomy and role profiles
    llm_client.py         Gemini REST client, typed errors, redaction helpers
    question_bank.py      Local questions with key concepts
    question_generator.py AI + local question generation
    interview_engine.py   Session state machine
    answer_evaluator.py   AI + fallback scoring, final report
    job_sources.py        Sample data + optional live Arbeitnow feed
    job_matcher.py        Weighted, explainable scoring
    learning_roadmap.py   Roadmap builder
    voice_utils.py        Browser TTS component, optional transcription
  ui/pages.py  ui/styles.py
  tests/                  36 tests (parser, matcher, fallbacks, failures, UI flow)
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 and click **Try it with a sample resume** to see everything working with no key.

### Enable AI (optional)

1. Create a key in [Google AI Studio](https://aistudio.google.com/) (the free tier does not require a billing setup, according to current third-party guides; confirm on Google's pages).
2. Copy `.env.example` to `.env` and set `GEMINI_API_KEY=...` (`.env` is git-ignored), or export it:
   ```bash
   export GEMINI_API_KEY="your-key"      # Windows PowerShell: $env:GEMINI_API_KEY="your-key"
   ```
3. Open **Settings & API status** and click **Check connection**.

Model names change and older ones get shut down, so the app asks the API for a current Flash model. To pin one, set `GEMINI_MODEL`.

## Deploy on Streamlit Community Cloud (free tier)

1. Push this folder to a public GitHub repo. Confirm `.env` and `.streamlit/secrets.toml` are not committed.
2. Go to https://share.streamlit.io, sign in with GitHub, choose **Create app**, pick the repo and branch, and set the main file to `app.py`.
3. Under **Advanced settings → Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your-key"
   ```
4. Deploy. If you skip the secret, the app runs in fallback mode.

Community Cloud's resource limits and sleeping behaviour are set by Streamlit and can change. Check their current docs. A public app that uses your key shares **your** quota among all visitors.

## Free-tier facts and caveats

- **Gemini:** Free, no expiry for eligible models, but limits are per project and shown in AI Studio's rate-limit page. Google no longer publishes a fixed table, and sources disagree on exact numbers, so none are hard-coded here. Quota errors (HTTP 429) trigger fallback mode with a visible message.
- **Privacy on the free tier:** Google's terms reportedly allow free-tier inputs and outputs to be used to improve its products, and humans may review them. The app sends only a redacted digest (no name, email, phone or links) plus your answers, but still avoid confidential content, or turn AI off in the sidebar.
- **Live jobs:** Optional, from Arbeitnow's public API (no key). Third-party summaries say it asks API users not to abuse it and to link back. I could not read its terms directly, so review them before public use. Results are cached for an hour, every listing links to its source, and listings without a link are dropped. Remotive is intentionally excluded because of reported redistribution and robots.txt restrictions.
- **Sample jobs** are fictional, labelled SAMPLE, and have no application links.
- **Resource names** in the roadmap have no URLs on purpose. They could not be verified from the build environment.

## How match scores work

`score = 100 × Σ(weight × component)`, with weights normalised to sum to 1 (adjustable in the UI; defaults in `config.py`):

| Component | Default | Calculation |
|---|---|---|
| Skills | 50% | 75% required-skill overlap + 25% preferred-skill overlap (required only if none listed) |
| Experience | 20% | Half years-of-experience fit, half required skills seen in work history |
| Education | 10% | Your degree level vs. the job's minimum (full marks if none required) |
| Projects | 20% | Required skills demonstrated in projects |

The score is a compatibility estimate, **not** a probability of being hired. Experience years are estimated from date ranges in the text, and skills come from a fixed taxonomy, so unlisted skills are invisible to it.

## Security and privacy

- Keys come from environment variables or hosting secrets only, and are never logged, shown, or sent anywhere except Google's API header.
- Uploads are size-limited, extension and magic-byte checked, and only parsed as documents, never executed.
- Resume and answer text is treated as untrusted data: it is delimited, tag-escaped, and the system prompt tells the model not to follow instructions inside it. AI output is parsed as JSON and validated and clamped before use.
- Nothing is written to disk. Resume, interview and report live in the browser session. **Clear my data** wipes them.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q
```

The tests cover parsing PDF/DOCX and bad files, bounded and explainable scores, no-key behaviour, simulated quota, key, timeout and bad-JSON failures, prompt redaction, and a headless run of the whole UI flow. No test calls the network.



## Known limitations

- Skill extraction is keyword-based. Resume layouts with columns or unusual headings may be sectioned imperfectly.
- Fallback evaluation checks keywords and structure only. It cannot judge whether an answer is correct.
- English resumes only. No OCR. No user accounts or saved history by design.

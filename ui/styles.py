"""Custom CSS: pastel lavender / blush / mint / powder-blue / peach dashboard theme (presentation only)."""
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root {
  --ink:#1B1F4B; --muted:#6B7394; --line:#E7E3F5; --accent:#6D4AFF; --accent-soft:#EDE8FF;
  --ok:#2F7D4F; --warn:#9A6A12; --bad:#B23A5A;
  --lav:#F1ECFF; --lav-b:#DDD3FB; --mint:#E8F8F0; --mint-b:#C7EBD9; --blue:#EAF3FF; --blue-b:#CBE0FA;
  --peach:#FFF1E4; --peach-b:#FAD9BC; --pink:#FFEAF1; --pink-b:#F8CCDB; --bg:#FBF9FF;
  --shadow:0 1px 2px rgba(60,40,140,.04), 0 6px 20px rgba(60,40,140,.06);
}
html, body, [class*="css"], .stMarkdown, .stButton button, .stTextArea textarea, input, label {
  font-family:'Plus Jakarta Sans', system-ui, sans-serif; }
.stApp { background: linear-gradient(180deg,#FBF9FF 0%,#FFFDFB 100%); color:var(--ink); }
.block-container { padding-top: 3.6rem; max-width: 1180px; }
h1, h2, h3 { letter-spacing: -0.015em; color: var(--ink); }
h1 { font-weight: 800; font-size: 1.9rem; }
h2, h3 { font-weight: 700; }
.cc-muted, .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted); }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background:#F7F4FF; border-right:1px solid var(--line); min-width:290px; }
[data-testid="stSidebar"] > div:first-child { padding-top:.6rem; }
.cc-brand { display:flex; gap:.7rem; align-items:center; padding:.2rem .3rem 1rem; }
.cc-logo { width:42px; height:42px; border-radius:13px; display:flex; align-items:center; justify-content:center; font-size:1.35rem;
           background:linear-gradient(135deg,#C9B8FF,#F9C6DA 55%,#BDEBD3); box-shadow:var(--shadow); }
.cc-brand-title { font-weight:800; font-size:1.2rem; color:var(--ink); line-height:1.15; }
.cc-brand-sub { font-size:.78rem; color:var(--muted); }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] { gap:.15rem; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div > label { padding:.62rem .8rem .62rem 2.7rem; border-radius:12px; width:100%;
   position:relative; transition:background .15s ease; cursor:pointer; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div > label > div > div:first-child { display:none; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div > label:hover { background:#EFE9FF; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div > label[data-selected="true"] { background:var(--lav-b); }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div > label[data-selected="true"] p { color:var(--accent); font-weight:700; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div > label p { color:var(--ink); font-weight:500; font-size:.95rem; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div > label::before { content:""; position:absolute; left:.85rem; top:50%; width:20px; height:20px;
   transform:translateY(-50%); background-color:#4A4F7A; -webkit-mask:var(--i) center/contain no-repeat; mask:var(--i) center/contain no-repeat; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div > label[data-selected="true"]::before { background-color:var(--accent); }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(1) > label { --i:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 11l9-8 9 8'/%3E%3Cpath d='M5 10v10h14V10'/%3E%3Cpath d='M10 20v-6h4v6'/%3E%3C/svg%3E"); }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(2) > label { --i:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z'/%3E%3Cpath d='M14 3v5h5M9 13h6M9 17h6'/%3E%3C/svg%3E"); }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(3) > label { --i:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='9' cy='8' r='3.5'/%3E%3Cpath d='M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6'/%3E%3Cpath d='M16 4.5a3.5 3.5 0 010 7M18 14.5c2 .7 3.5 2.6 3.5 5.5'/%3E%3C/svg%3E"); }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(4) > label { --i:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 20V10M10 20V4M16 20v-8M22 20H2'/%3E%3C/svg%3E"); }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(5) > label { --i:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='7' width='18' height='13' rx='2'/%3E%3Cpath d='M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2M3 13h18'/%3E%3C/svg%3E"); }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(6) > label { --i:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 5l6-2 6 2 6-2v16l-6 2-6-2-6 2z'/%3E%3Cpath d='M9 3v16M15 5v16'/%3E%3C/svg%3E"); }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(7) > label { --i:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3Cpath d='M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z'/%3E%3C/svg%3E"); }
[data-testid="stSidebar"] [data-baseweb="select"] > div { border-radius:12px; border:1px solid var(--line); background:#fff; }
[data-testid="stSidebar"] hr { border-color:var(--line); }
[data-testid="stSidebar"] .stButton button { border-radius:12px; border:1px solid var(--lav-b); background:#fff; color:var(--ink); font-weight:600; }
[data-testid="stSidebar"] .stButton button:hover { border-color:var(--accent); color:var(--accent); background:var(--lav); }

/* ---------- buttons, inputs ---------- */
.stButton button, .stDownloadButton button, .stLinkButton a { border-radius:12px; border:1px solid var(--lav-b); font-weight:600;
   transition:border-color .15s ease, background .15s ease, box-shadow .15s ease; }
.stButton button:hover, .stDownloadButton button:hover, .stLinkButton a:hover { border-color:var(--accent); color:var(--accent); }
.stButton button[kind="primary"] { background:linear-gradient(135deg,#7C5CFF,#9B7BFF); border:none; color:#fff; box-shadow:0 6px 16px rgba(109,74,255,.25); }
.stButton button[kind="primary"]:hover { color:#fff; filter:brightness(1.05); }
.stTextArea textarea, .stTextInput input { border-radius:12px; border:1px solid var(--line); background:#fff; }
[data-testid="stExpander"] { border:1px solid var(--line); border-radius:16px; background:#fff; box-shadow:var(--shadow); overflow:hidden; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:16px; padding:.8rem 1rem; box-shadow:var(--shadow); }
[data-testid="stTabs"] [aria-selected="true"] { color:var(--accent); }
[data-testid="stAlert"] { border-radius:14px; }

/* ---------- shared components ---------- */
.cc-card { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1.1rem 1.3rem; margin-bottom:.9rem; box-shadow:var(--shadow); }
.cc-panel-title { display:flex; align-items:center; gap:.6rem; font-weight:700; font-size:1.1rem; color:var(--ink); }
.cc-panel-sub { color:var(--muted); font-size:.82rem; margin:.1rem 0 .8rem; }
.cc-step { display:flex; gap:.9rem; align-items:flex-start; padding:.8rem 0; border-bottom:1px solid var(--line); }
.cc-step:last-child { border-bottom:none; }
.cc-dot { min-width:1.7rem; height:1.7rem; border-radius:50%; display:flex; align-items:center; justify-content:center;
          font-weight:700; font-size:.85rem; background:var(--lav); color:var(--accent); }
.cc-dot.done { background:#5BC391; color:#fff; }
.cc-pill { display:inline-block; padding:.14rem .65rem; margin:.15rem .25rem .15rem 0; border-radius:999px; font-size:.82rem;
           border:1px solid var(--line); background:#fff; color:var(--ink); }
.cc-pill.ok { border-color:var(--mint-b); background:var(--mint); color:#1F5C39; }
.cc-pill.miss { border-color:var(--pink-b); background:var(--pink); color:#8E2A4A; }
.cc-badge { display:inline-block; padding:.12rem .6rem; border-radius:999px; font-size:.78rem; font-weight:700; }
.cc-badge.sample { background:var(--peach); color:#8A5200; border:1px solid var(--peach-b); }
.cc-badge.live { background:var(--mint); color:#1F5C39; border:1px solid var(--mint-b); }
.cc-badge.ai { background:var(--lav); color:#4A2FC4; border:1px solid var(--lav-b); }
.cc-badge.fallback { background:#F3F2F8; color:#4A4F6E; border:1px solid var(--line); }
.cc-muted { color: var(--muted); font-size:.9rem; }
.cc-question { font-size:1.2rem; font-weight:700; line-height:1.45; color:var(--ink); margin-top:.3rem; }

/* ---------- home: hero ---------- */
.cc-hero { position:relative; overflow:hidden; border-radius:22px; padding:1.9rem 2rem; margin-bottom:1.1rem; border:1px solid #F6DCD0;
   background:radial-gradient(120% 140% at 100% 0%, #FFD9C2 0%, rgba(255,217,194,0) 55%), linear-gradient(120deg,#FFEAF1 0%,#FFF6EC 55%,#FFE8D6 100%); box-shadow:var(--shadow); }
.cc-hero .hi { color:var(--ink); font-size:.98rem; margin-bottom:.25rem; }
.cc-hero h1 { font-size:2.15rem; font-weight:800; margin:0 0 .5rem; line-height:1.15; }
.cc-hero p { color:#3A3F6B; max-width:30rem; margin:0 0 1rem; font-size:.98rem; }
.cc-hero-pills { display:inline-flex; flex-wrap:wrap; gap:.4rem 1rem; background:rgba(255,255,255,.85); border:1px solid #F1E3EE; border-radius:999px; padding:.4rem 1rem; font-size:.84rem; color:var(--muted); }
.cc-hero-pills b { color:var(--ink); font-weight:600; margin-left:.25rem; }
.cc-hero-art { position:absolute; right:2rem; top:50%; transform:translateY(-50%) rotate(4deg); width:190px; padding:1rem 1.1rem 1.2rem; border-radius:14px;
   background:#fff; box-shadow:0 10px 30px rgba(120,70,60,.18); border-left:8px dotted #D9D5E8; font-family:'Segoe Script','Bradley Hand','Comic Sans MS',cursive;
   color:#3F51B5; font-size:.95rem; line-height:1.35; }
.cc-hero-art::after { content:"🌿"; position:absolute; right:-18px; top:-26px; font-size:2rem; }
@media (max-width: 900px) { .cc-hero-art { display:none; } }

/* ---------- home: feature cards (real st.button navigation, styled as cards) ---------- */
[class*="st-key-card_"] button { width:100%; min-height:150px; text-align:left; justify-content:flex-start; align-items:flex-end;
   border-radius:18px; padding:1rem; position:relative; box-shadow:none; border:1px solid var(--lav-b); background:var(--lav); }
[class*="st-key-card_"] button > div, [class*="st-key-card_"] button span { width:100%; text-align:left; justify-content:flex-start; }
[class*="st-key-card_"] [data-testid="stMarkdownContainer"] { white-space:normal !important; overflow:visible !important; text-overflow:clip !important; display:block !important; padding-right:1rem; }
[class*="st-key-card_"] button p { display:block !important; width:100%; margin:0 0 .15rem; font-size:.78rem; color:var(--muted); font-weight:400; line-height:1.35; text-align:left; white-space:normal; }
[class*="st-key-card_"] button p:first-child, [class*="st-key-card_"] button strong { color:var(--ink); font-size:.92rem; font-weight:700; }
[class*="st-key-card_"] button::before { content:""; position:absolute; left:1rem; top:.9rem; width:40px; height:40px; border-radius:50%;
   background:var(--ic) center/20px no-repeat, rgba(255,255,255,.8); }
[class*="st-key-card_"] button::after { content:"›"; position:absolute; right:.9rem; bottom:1rem; font-size:1.4rem; line-height:1; color:var(--accent); }
[class*="st-key-card_"] button:hover { transform:translateY(-2px); box-shadow:var(--shadow); }
.st-key-card_resume { --ic:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237C5CFF' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z'/%3E%3Cpath d='M14 3v5h5M9 13h6M9 17h6'/%3E%3C/svg%3E"); }
.st-key-card_interview { --ic:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232FA36B' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='9' cy='8' r='3.5'/%3E%3Cpath d='M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6'/%3E%3Cpath d='M16 4.5a3.5 3.5 0 010 7M18 14.5c2 .7 3.5 2.6 3.5 5.5'/%3E%3C/svg%3E"); }
.st-key-card_report { --ic:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%233B82D9' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 20V10M10 20V4M16 20v-8M22 20H2'/%3E%3C/svg%3E"); }
.st-key-card_jobs { --ic:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23E8892B' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='7' width='18' height='13' rx='2'/%3E%3Cpath d='M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2M3 13h18'/%3E%3C/svg%3E"); }
.st-key-card_roadmap { --ic:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23C2417A' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 5l6-2 6 2 6-2v16l-6 2-6-2-6 2z'/%3E%3Cpath d='M9 3v16M15 5v16'/%3E%3C/svg%3E"); }
.st-key-card_resume button { background:var(--lav); border-color:var(--lav-b); }
.st-key-card_interview button { background:var(--mint); border-color:var(--mint-b); }
.st-key-card_report button { background:var(--blue); border-color:var(--blue-b); }
.st-key-card_jobs button { background:var(--peach); border-color:var(--peach-b); }
.st-key-card_roadmap button { background:var(--pink); border-color:var(--pink-b); }

/* ---------- home: progress + activity ---------- */
.cc-metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.7rem; }
.cc-metric { border-radius:16px; padding:.9rem .8rem; border:1px solid var(--line); }
.cc-metric .dot { width:34px; height:34px; border-radius:50%; background:rgba(255,255,255,.8); display:flex; align-items:center; justify-content:center; margin-bottom:.6rem; }
.cc-metric .lbl { font-size:.82rem; color:var(--ink); font-weight:600; }
.cc-metric .val { font-size:1rem; font-weight:700; margin:.2rem 0; overflow-wrap:break-word; word-break:normal; line-height:1.25; }
.cc-metric .hint { font-size:.74rem; color:var(--muted); }
.cc-metric.pink { background:var(--pink); border-color:var(--pink-b); } .cc-metric.pink .val { color:#D63A6A; }
.cc-metric.blue { background:var(--blue); border-color:var(--blue-b); } .cc-metric.blue .val { color:#2563B8; }
.cc-metric.peach { background:var(--peach); border-color:var(--peach-b); } .cc-metric.peach .val { color:#B26A1B; }
.cc-metric.lav { background:var(--lav); border-color:var(--lav-b); } .cc-metric.lav .val { color:var(--accent); }
.cc-row { display:flex; align-items:center; gap:.8rem; padding:.65rem 0; border-bottom:1px solid var(--line); }
.cc-row:last-child { border-bottom:none; }
.cc-row .ic { min-width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1rem; }
.cc-row .t { font-weight:600; font-size:.9rem; color:var(--ink); } .cc-row .s { font-size:.78rem; color:var(--muted); }
.cc-tips { background:linear-gradient(135deg,#EEF2FF,#F3EDFF); border:1px solid var(--lav-b); border-radius:16px; padding:1rem 1.2rem; display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap; }
.cc-tips ul { margin:.3rem 0 0 1.1rem; padding:0; color:#3A3F6B; font-size:.88rem; line-height:1.8; }
.cc-note { font-family:'Segoe Script','Bradley Hand','Comic Sans MS',cursive; color:#5B4FD6; align-self:center; transform:rotate(-6deg); font-size:1.05rem; }
.cc-goal { background:linear-gradient(120deg,#F0E8FF,#FFE6EF); border:1px solid var(--lav-b); border-radius:16px; padding:.9rem 1.2rem; }
.cc-goal b { color:var(--ink); } .cc-goal span { color:var(--muted); font-size:.8rem; display:block; }

:focus-visible { outline:2px solid var(--accent) !important; outline-offset:2px; }
@media (max-width: 900px) { .cc-metrics { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width: 640px) { .block-container { padding: 1rem .8rem; } h1 { font-size:1.5rem; } .cc-hero { padding:1.3rem 1.2rem; } .cc-hero h1 { font-size:1.6rem; } .cc-metrics { grid-template-columns:1fr; } }
@media (prefers-reduced-motion: reduce) { * { transition:none !important; animation:none !important; } }
</style>
"""

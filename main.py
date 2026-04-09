"""
StudyOS — Multi-Agent Study Assistant
Enterprise Edition · Powered by Google Gemini 2.5 Flash Lite
"""

import hashlib
import os
import random
import time
import urllib.parse
import streamlit.components.v1 as stc

import streamlit as st
from orchestrator import run_study_assistant
from utils.quiz_parser import parse_quiz_markdown
from utils.components import render_interactive_quiz, format_study_notes

# ─────────────────────────────────────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _make_status_callback(status_box, progress_bar, status_log: list):
    """
    Factory that returns a live-status callback bound to the active
    Streamlit UI elements. Defined at module level so it is not nested
    inside conditional or context-manager blocks.
    """
    def callback(msg: str) -> None:
        status_log.append(msg)
        status_box.update(label=msg, state="running")
        pct = min(int(len(status_log) / 4 * 100), 95)
        progress_bar.progress(pct, text=msg)
        st.markdown(f"&nbsp;&nbsp;&rsaquo; {msg}")
        time.sleep(0.04)
    return callback


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be the very first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudyOS — Multi-Agent Study Assistant",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "StudyOS — Multi-Agent AI Study Platform powered by Google Gemini 2.5 Flash Lite",
    },
)

# Parse share links to pre-load topic
if "share_topic" in st.query_params and not st.session_state.get("shared_loaded"):
    st.session_state.topic_input_state = st.query_params["share_topic"]
    st.session_state.shared_loaded = True
    st.session_state.generate_requested = True

if "topic_input_state" not in st.session_state:
    st.session_state.topic_input_state = ""
if "topic_widget_key" not in st.session_state:
    st.session_state.topic_widget_key = ""
if "study_result" not in st.session_state:
    st.session_state.study_result = None
if "study_difficulty" not in st.session_state:
    st.session_state.study_difficulty = "Medium"
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0  # 0=Notes, 1=Quiz, 2=Research

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN SYSTEM — Slate & Navy, GitHub/Notion/Stripe aesthetic
# Color palette:
#   --bg-base       : #0f1117   (page background — near-black slate)
#   --bg-surface    : #161b22   (cards, panels — GitHub dark surface)
#   --bg-elevated   : #1c2128   (hover states, sidebars)
#   --border-subtle : #30363d   (GitHub-style subtle border)
#   --border-default: #484f58   (interactive element borders)
# ─────────────────────────────────────────────────────────────────────────────
DESIGN_CSS = """
<style>

/* === TYPEFACE === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* === BASE === */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    -webkit-font-smoothing: antialiased;
}
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* === ICON FIX — preserve Material Symbols for Streamlit nav === */
i.material-symbols-rounded,
span.material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
}

/* === STREAMLIT CHROME === */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
    border-bottom: none !important;
}
[data-testid="collapsedControl"] { display: none !important; }

/* === APP BACKGROUND === */
.stApp {
    background-color: #0f172a;
    color: #f1f5f9;
    min-height: 100vh;
}

/* === SIDEBAR === */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background-color: #0f172a !important;
    border-right: 1px solid #1e293b !important;
}

/* Sidebar brand block */
.sb-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
}
.sb-brand-mark {
    width: 34px;
    height: 34px;
    background-color: #2563eb;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    font-weight: 700;
    color: #ffffff;
    flex-shrink: 0;
}
.sb-brand-name {
    font-size: 1rem;
    font-weight: 600;
    color: #f1f5f9;
}
.sb-label {
    font-size: 0.62rem;
    letter-spacing: 0.1em;
    color: #475569;
    text-transform: uppercase;
    font-weight: 600;
    margin: 1.25rem 0 0.4rem;
}

/* Sidebar status badges */
.status-badge {
    display: inline-block;
    padding: 0.18rem 0.55rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.02em;
}
.badge-ok   {
    background: rgba(34,197,94,0.1);
    color: #22c55e;
    border: 1px solid rgba(34,197,94,0.2);
}
.badge-info {
    background: rgba(37,99,235,0.12);
    color: #60a5fa;
    border: 1px solid rgba(37,99,235,0.2);
}

/* === BUTTONS === */
/* Primary action buttons */
.stButton > button {
    background-color: #2563eb !important;
    border: none !important;
    border-radius: 6px !important;
    color: #ffffff !important;
    font-weight: 500 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.01em !important;
    text-transform: none !important;
    padding: 0.6rem 1.25rem !important;
    box-shadow: none !important;
    transition: background-color 0.15s ease, transform 0.15s ease !important;
}
.stButton > button:hover {
    background-color: #1d4ed8 !important;
    transform: translateY(-1px) !important;
    box-shadow: none !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* === DOWNLOAD BUTTONS — ghost style === */
.stDownloadButton > button {
    background-color: transparent !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
    color: #94a3b8 !important;
    font-weight: 500 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-size: 0.875rem !important;
    text-transform: none !important;
    padding: 0.6rem 1.25rem !important;
    box-shadow: none !important;
    transition: border-color 0.15s ease, color 0.15s ease !important;
}
.stDownloadButton > button:hover {
    border-color: #3b82f6 !important;
    color: #f1f5f9 !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

/* === TEXT INPUTS === */
.stTextInput > div > div > input {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.65rem 0.875rem !important;
    box-shadow: none !important;
    transition: border-color 0.15s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: none !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder {
    color: #475569 !important;
}

/* === CARDS / DS-CARD === */
.ds-card,
.metric-block,
.empty-state,
.pipeline-step {
    background-color: #1e293b;
    border: 1px solid #1e293b;
    border-radius: 8px;
    box-shadow: none;
    transition: border-color 0.15s ease;
}
.ds-card:hover,
.metric-block:hover {
    border-color: #334155;
}
.ds-card {
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    color: #f1f5f9;
}
.ds-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}
.ds-card-title {
    font-size: 1rem;
    font-weight: 600;
    color: #f1f5f9;
    margin: 0;
}
.ds-card-meta {
    font-size: 0.78rem;
    color: #94a3b8;
    margin-top: 0.2rem;
}
.ds-card-tag {
    display: inline-block;
    background-color: rgba(37,99,235,0.12);
    color: #60a5fa;
    font-size: 0.65rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-weight: 600;
    border: 1px solid rgba(37,99,235,0.2);
}

/* === TABS === */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid #1e293b;
    gap: 2rem;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"] {
    color: #475569;
    font-weight: 500;
    font-size: 0.875rem;
    letter-spacing: 0.01em;
    text-transform: none;
    padding: 0.75rem 0;
    border-bottom: 2px solid transparent;
    background: transparent !important;
    transition: color 0.15s ease;
}
.stTabs [aria-selected="true"] {
    color: #f1f5f9 !important;
    border-bottom-color: #2563eb !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #94a3b8;
}

/* === METRICS === */
.metric-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1.5rem;
}
.metric-block {
    border-radius: 8px;
    padding: 1rem 1.25rem;
    flex: 1;
    min-width: 120px;
}
.metric-label {
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 0.4rem;
    font-weight: 600;
}
.metric-value {
    font-size: 1.4rem;
    font-weight: 600;
    color: #f1f5f9;
}
.metric-value.accent { color: #60a5fa; }

/* === DIFFICULTY CLASSES === */
.diff-easy   { color: #22c55e; }
.diff-medium { color: #f59e0b; }
.diff-hard   { color: #ef4444; }

/* === AGENT STATUS CARDS — three states === */
/* Idle state (default ds-card border) */
.agent-card-idle {
    border-color: #1e293b;
}
/* Running state */
.agent-card-running {
    border-color: #3b82f6;
    background-color: rgba(59,130,246,0.04);
}
/* Done state — left accent bar via box-shadow inset */
.agent-card-done {
    border-color: #1e293b;
    border-left: 3px solid #22c55e;
}

/* === PIPELINE STRIP === */
.pipeline-strip {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 1.25rem 0 2rem;
    overflow-x: auto;
    padding: 0.25rem 0;
}
.pipeline-step {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    font-weight: 500;
    color: #94a3b8;
    white-space: nowrap;
    border: 1px solid #1e293b;
}
.pipeline-step-active {
    border-color: #3b82f6 !important;
    color: #f1f5f9 !important;
}
.pipeline-step-index {
    width: 20px;
    height: 20px;
    background-color: #273549;
    border-radius: 50%;
    font-size: 0.68rem;
    font-weight: 700;
    color: #475569;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.pipeline-step-active .pipeline-step-index {
    background-color: #2563eb;
    color: #ffffff;
}
.pipeline-arrow {
    font-size: 0.9rem;
    color: #334155;
    flex-shrink: 0;
}

/* === PAGE HEADER === */
.page-header {
    padding: 2rem 0 1.75rem;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 2rem;
}
.page-header-eyebrow {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 0.6rem;
}
.page-header-title {
    font-size: 2rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.025em;
    line-height: 1.15;
    margin-bottom: 0.6rem;
}
.page-header-sub {
    font-size: 0.9rem;
    color: #94a3b8;
    max-width: 560px;
    line-height: 1.65;
}

/* === EMPTY STATE === */
.empty-state {
    text-align: center;
    padding: 5rem 2rem;
    border-radius: 8px;
    margin-top: 1rem;
    border-color: #1e293b;
}
.empty-state-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.02em;
    margin-bottom: 0.75rem;
}
.empty-state-sub {
    color: #94a3b8;
    font-size: 0.95rem;
    max-width: 480px;
    margin: 0 auto;
    line-height: 1.65;
}

/* === MARQUEE CHIPS === */
.marquee-wrapper {
    overflow: hidden;
    width: 100%;
    margin-top: 2rem;
    white-space: nowrap;
    -webkit-mask-image: linear-gradient(to right, transparent, black 12%, black 88%, transparent);
    mask-image: linear-gradient(to right, transparent, black 12%, black 88%, transparent);
}
@keyframes marqueeScroll {
    0%   { transform: translateX(0%); }
    100% { transform: translateX(-50%); }
}
.marquee-track {
    display: inline-block;
    animation: marqueeScroll 30s linear infinite;
}
.marquee-track:hover { animation-play-state: paused; }
.topic-chip {
    display: inline-block;
    background-color: #1e293b;
    border: 1px solid #273549;
    border-radius: 999px;
    padding: 0.3rem 0.85rem;
    font-size: 0.8rem;
    color: #475569;
    margin: 0.3rem;
    font-weight: 500;
    transition: border-color 0.15s ease, color 0.15s ease;
}
.topic-chip:hover {
    border-color: #334155;
    color: #94a3b8;
}

/* === COMPONENT TAGS === */
.k-term {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 0.1rem 0.35rem;
    color: #94a3b8;
    font-size: 0.85rem;
    font-family: 'Inter', monospace;
}
.q-card-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 0.875rem;
}

/* === STUDY NOTES === */
.study-notes-container {
    font-size: 15px;
    line-height: 1.75;
    color: #f1f5f9;
}
.note-section-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: #f1f5f9;
    border-bottom: 1px solid #1e293b;
    margin-top: 2rem;
    margin-bottom: 0.875rem;
    padding-bottom: 0.5rem;
}
@keyframes fadeInSlide {
    0%   { opacity: 0; transform: translateY(6px); }
    100% { opacity: 1; transform: translateY(0); }
}
.study-notes-container p, .study-notes-container li {
    animation: fadeInSlide 0.35s ease backwards;
}
.study-notes-container p:nth-child(1) { animation-delay: 0.05s; }
.study-notes-container p:nth-child(2) { animation-delay: 0.1s; }
.study-notes-container p:nth-child(3) { animation-delay: 0.15s; }
.study-notes-container li { animation-delay: 0.2s; }

/* === COMMAND BAR === */
.command-bar-wrapper {
    position: sticky;
    top: 50px;
    z-index: 1000;
    background-color: rgba(15, 23, 42, 0.92);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    padding-bottom: 20px;
    border-bottom: 1px solid #1e293b;
}

/* === PAGE FOOTER === */
.page-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: rgba(15,23,42,0.92);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-top: 1px solid #1e293b;
    padding: 0.6rem 2rem;
    z-index: 999;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.page-footer-text {
    font-size: 0.72rem;
    color: #475569;
    letter-spacing: 0.03em;
    margin: 0;
}

/* === SCROLLBAR === */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb {
    background-color: #334155;
    border-radius: 2px;
}

</style>
"""

st.markdown(DESIGN_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-brand"><div class="sb-brand-mark">S</div><span class="sb-brand-name">StudyOS</span></div><p style="font-size:0.8rem;color:#8b949e;margin-top:-0.5rem;margin-bottom:0;">Multi-Agent Study Assistant</p>', unsafe_allow_html=True)
    # st.divider()  # removed: was separating hidden Auth section

    # # ── Authentication ────────────────────────────────────────────────────────
    # st.markdown('<p class="sb-label">Authentication</p>', unsafe_allow_html=True)
    # api_key_input = st.text_input(
    #     "Gemini API Key",
    #     type="password",
    #     placeholder="Optional — overrides .env key",
    #     help="Get a free key at aistudio.google.com",
    #     label_visibility="collapsed",
    # )
    # if api_key_input:
    #     st.markdown('<span class="status-badge badge-ok">Active — custom key</span>', unsafe_allow_html=True)
    # else:
    #     st.markdown('<span class="status-badge badge-info">Using .env key</span>', unsafe_allow_html=True)
    api_key_input = os.getenv("GEMINI_API_KEY")

    # st.divider()  # removed: was separating hidden Auth section

    # ── Quiz configuration ────────────────────────────────────────────────────
    st.markdown('<p class="sb-label">Quiz Configuration</p>', unsafe_allow_html=True)
    difficulty = st.select_slider(
        "Difficulty",
        options=["Easy", "Medium", "Hard"],
        value="Medium",
        help="Controls MCQ complexity and plausibility of distractors",
    )
    diff_class_map = {"Easy": "diff-easy", "Medium": "diff-medium", "Hard": "diff-hard"}
    st.markdown(
        f'<p style="font-size:0.8rem;margin-top:0.4rem;">'
        f'<span class="{diff_class_map[difficulty]}" style="font-weight:700;">{difficulty}</span>'
        f'<span style="color:#484f58;"> mode selected</span></p>',
        unsafe_allow_html=True,
    )

    st.divider()

    # ── System info ───────────────────────────────────────────────────────────
    st.markdown('<p class="sb-label">System</p>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-size:0.78rem;color:#8b949e;line-height:1.8;">
            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="color:#484f58;font-weight:600;padding-right:0.5rem;">Agents</td>
                    <td>3 (Research, Summarizer, Quiz)</td>
                </tr>
                <tr>
                    <td style="color:#484f58;font-weight:600;padding-right:0.5rem;">Model</td>
                    <td>Gemini 2.5 Flash Lite</td>
                </tr>
                <tr>
                    <td style="color:#484f58;font-weight:600;padding-right:0.5rem;">Cache TTL</td>
                    <td>60 minutes</td>
                </tr>
                <tr>
                    <td style="color:#484f58;font-weight:600;padding-right:0.5rem;">Framework</td>
                    <td>Streamlit</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="page-header"><div class="page-header-eyebrow">Multi-Agent AI Platform</div><div class="page-header-title">Study Assistant</div><div class="page-header-sub">Three coordinated AI agents research a topic, distill it into structured notes, and generate assessed quiz questions — fully automated.</div></div>',
    unsafe_allow_html=True,
)

# Agent pipeline
st.markdown(
    '<div class="pipeline-strip"><div class="pipeline-step"><div class="pipeline-step-index">1</div>Research Agent</div><div class="pipeline-arrow">&#8594;</div><div class="pipeline-step"><div class="pipeline-step-index">2</div>Summarizer Agent</div><div class="pipeline-arrow">&#8594;</div><div class="pipeline-step"><div class="pipeline-step-index">3</div>Quiz Agent</div></div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# INPUT ROW
# ─────────────────────────────────────────────────────────────────────────────

# Initialize session state for programmatic input manipulation
if "topic_input_state" not in st.session_state:
    st.session_state.topic_input_state = ""

with st.form(key="topic_form", border=False):
    col_input, col_btn = st.columns([5, 1], gap="small")

    with col_input:
        topic = st.text_input(
            "Topic",
            value=st.session_state.topic_input_state,
            placeholder="Enter a topic — e.g. Transformer Architecture, French Revolution, CRISPR...",
            label_visibility="collapsed",
            key="topic_widget_key",
        )

    with col_btn:
        generate_clicked = st.form_submit_button(
            "Generate",
            use_container_width=True,
            type="primary",
        )

# Sync topic value back to session state after form interaction
if topic:
    st.session_state.topic_input_state = topic

# ─────────────────────────────────────────────────────────────────────────────
# CACHING  — keyed on (topic, difficulty, api_key_hash) — 1-hour TTL
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def cached_study_package(topic: str, difficulty: str, _key_hash: str):
    """
    Wraps the orchestrator with Streamlit's cache layer.
    The underscore prefix on _key_hash tells Streamlit not to hash this param
    separately (we already hashed it ourselves).
    """
    return run_study_assistant(topic, difficulty=difficulty)


# ─────────────────────────────────────────────────────────────────────────────
# GENERATION PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
if generate_clicked or st.session_state.get("generate_requested", False):
    st.session_state.generate_requested = False
    
    # Input validation
    if not topic or not topic.strip():
        st.warning("Please enter a topic before generating.", icon=None)
        st.stop()

    topic = topic.strip()
    api_key_hash = hashlib.md5(b"env").hexdigest()

    # Real-time agent status panel
    with st.status("Initializing agent pipeline...", expanded=True) as status_box:
        progress_bar = st.progress(0, text="Starting...")
        st.caption(f"Topic: {topic}  |  Difficulty: {difficulty}")

        status_log: list[str] = []
        live_status = _make_status_callback(status_box, progress_bar, status_log)

        live_status("🔍 Research Agent — scanning knowledge bases")
        live_status("📝 Summarizer Agent — distilling key concepts")
        live_status(f"🧠 Quiz Agent — composing {difficulty} questions")

        try:
            result = cached_study_package(topic, difficulty, api_key_hash)

            progress_bar.progress(100, text="Complete")
            status_box.update(
                label=f"All agents completed — {result.get('elapsed_time', '—')}s elapsed",
                state="complete",
                expanded=False,
            )

            # ── Persist result in session state so it survives reruns ──────────
            st.session_state.study_result = result
            st.session_state.study_difficulty = difficulty
            # Reset quiz state for the new topic
            st.session_state.quiz_score = 0
            st.session_state.answered_questions = set()
            st.session_state.revealed_questions = set()

        except EnvironmentError as exc:
            status_box.update(label="Configuration error", state="error")
            st.error(
                f"**API Key Error:** {exc}\n\n"
                "Add your Gemini API key to the `.env` file "
                "or paste it in the sidebar under Authentication."
            )
            st.stop()

        except RuntimeError as exc:
            status_box.update(label="Agent pipeline failed", state="error")
            st.error(
                f"**Agent Error:** {exc}\n\n"
                "This is often a transient API timeout. Please try again."
            )
            st.stop()

        except Exception as exc:
            status_box.update(label="Unexpected error", state="error")
            st.error(
                f"**Error:** {exc}\n\n"
                "Check your internet connection and API key configuration."
            )
            st.stop()

    st.toast(f"Study package ready for: {topic}")

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS DASHBOARD — renders whenever a result is stored in session state
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.study_result is not None:
    result = st.session_state.study_result
    difficulty = st.session_state.study_difficulty

    st.divider()

    # Metrics
    word_count_research = len(result["research"].split())
    word_count_notes    = len(result["notes"].split())
    quiz_q_count        = result["quiz"].count("**Q")
    elapsed             = result.get("elapsed_time", "—")

    diff_metric_class = {"Easy": "success", "Medium": "warn", "Hard": "danger"}
    diff_cls = diff_metric_class.get(difficulty, "accent")

    st.markdown(
        f"""
        <div class="metric-row">
            <div class="metric-block">
                <div class="metric-label">Research Words</div>
                <div class="metric-value">{word_count_research:,}</div>
            </div>
            <div class="metric-block">
                <div class="metric-label">Notes Words</div>
                <div class="metric-value">{word_count_notes:,}</div>
            </div>
            <div class="metric-block">
                <div class="metric-label">Quiz Questions</div>
                <div class="metric-value accent">{quiz_q_count}</div>
            </div>
            <div class="metric-block">
                <div class="metric-label">Difficulty</div>
                <div class="metric-value {diff_cls}">{difficulty}</div>
            </div>
            <div class="metric-block">
                <div class="metric-label">Time (seconds)</div>
                <div class="metric-value">{elapsed}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Tabbed Interface ───────────────────────────────────────────────────────
    tab_notes, tab_quiz, tab_research = st.tabs(["📝 Study Notes", "🧠 Interactive Quiz", "🔬 Raw Research"])

    with tab_notes:
        st.markdown(
            """
            <div class="ds-card" style="margin-bottom: 2rem;">
                <div class="ds-card-header">
                    <div>
                        <div class="ds-card-title">Study Notes</div>
                        <div class="ds-card-meta">AI-distilled concepts from Research Agent output</div>
                    </div>
                    <div class="ds-card-tag">Summarizer Agent</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Apply CSS animation delays via the format wrapper
        st.markdown(format_study_notes(result["notes"]), unsafe_allow_html=True)

    with tab_quiz:
        st.markdown(
            f"""
            <div class="ds-card" style="margin-bottom: 2rem;">
                <div class="ds-card-header">
                    <div>
                        <div class="ds-card-title">Knowledge Check</div>
                        <div class="ds-card-meta">Assessed MCQ questions generated organically from the Study Notes</div>
                    </div>
                    <div class="ds-card-tag">Quiz Agent</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        parsed_quiz = parse_quiz_markdown(result["quiz"])
        if not parsed_quiz:
             st.warning("Could not parse quiz into interactive mode. Falling back to plain text.")
             st.markdown(result["quiz"])
        else:
             render_interactive_quiz(parsed_quiz, difficulty)

    with tab_research:
        st.markdown(
            """
            <div class="ds-card" style="margin-bottom: 2rem;">
                <div class="ds-card-header">
                    <div>
                        <div class="ds-card-title">Raw Intelligence Report</div>
                        <div class="ds-card-meta">Unabridged reference material used as context for the study notes</div>
                    </div>
                    <div class="ds-card-tag">Research Agent</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(result["research"])

    # ── Tab persistence — re-select the correct tab after every rerun ──────────
    # Streamlit always renders tab-0 on rerun; this JS clicks the persisted tab.
    _active = st.session_state.get("active_tab", 0)
    if _active != 0:
        stc.html(
            f"""
            <script>
            (function() {{
                var idx = {_active};
                function _click() {{
                    var tabs = window.parent.document.querySelectorAll(
                        '[data-baseweb="tab"]'
                    );
                    if (tabs && tabs.length > idx) {{
                        tabs[idx].click();
                    }} else {{
                        setTimeout(_click, 80);
                    }}
                }}
                setTimeout(_click, 80);
            }})();
            </script>
            """,
            height=0,
        )

    # Export row
    st.markdown(
        '<p style="font-size:0.85rem;font-weight:600;color:#8b949e;'
        'letter-spacing:0.02em;margin-bottom:0.6rem;">Export</p>',
        unsafe_allow_html=True,
    )

    dl_col1, dl_col2, dl_spacer = st.columns([2, 1.2, 2])

    full_output = (
        f"StudyOS — Study Package\n"
        f"{'=' * 60}\n"
        f"Topic      : {result['topic']}\n"
        f"Difficulty : {difficulty}\n"
        f"Generated  : {time.strftime('%Y-%m-%d %H:%M')}\n"
        f"{'=' * 60}\n\n"
        f"RESEARCH REPORT\n{'-' * 40}\n{result['research']}\n\n"
        f"STUDY NOTES\n{'-' * 40}\n{result['notes']}\n\n"
        f"QUIZ QUESTIONS\n{'-' * 40}\n{result['quiz']}\n"
    )

    with dl_col1:
        st.download_button(
            label="Download full package (.txt)",
            data=full_output,
            file_name=f"{topic[:40].replace(' ', '_')}_StudyOS.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            label="Notes only",
            data=result["notes"],
            file_name=f"{topic[:40].replace(' ', '_')}_notes.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # Share block
    st.markdown('<p style="font-size:0.85rem;font-weight:600;color:#8b949e;'
        'letter-spacing:0.02em;margin-top:1rem;margin-bottom:0.6rem;">Share Session</p>',
        unsafe_allow_html=True)
    share_state_url = f"?share_topic={urllib.parse.quote(result['topic'])}"
    st.code(share_state_url, language="text")

# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.study_result is None:
    SUGGESTIONS = [
        "Machine Learning Vectors", "Quantum Cryptography", "The Fall of Rome", 
        "CRISPR Gene Editing", "Zero Knowledge Proofs", "Neural Networks",
        "Transformer Architecture", "French Revolution", "String Theory",
        "Macroeconomics", "Cognitive Behavioral Therapy", "Stoicism"
    ]
    
    def set_random_topic():
        chosen = random.choice(SUGGESTIONS)
        st.session_state.topic_widget_key = chosen
        st.session_state.topic_input_state = chosen
    
    # We duplicate the array 2x visually so the marquee can stitch seamlessly
    marquee_html = "".join([f'<span class="topic-chip">{topic}</span>' for topic in (SUGGESTIONS + SUGGESTIONS)])
    
    # Inject empty state safely without multi-line indentation parsing risks
    st.markdown(
        f'<div class="empty-state"><div class="empty-state-title">Enter a topic to get started</div><div class="empty-state-sub">Type any academic or technical topic in the field above. The three-agent pipeline will research, summarize, and produce a quiz automatically.</div><div class="marquee-wrapper"><div class="marquee-track">{marquee_html}</div></div></div>',
        unsafe_allow_html=True,
    )
    
    # Inject a Streamlit button disguised within the empty state context
    col_e1, col_e2, col_e3 = st.columns([1, 1, 1])
    with col_e2:
        st.button("🎲 Try a random topic", on_click=set_random_topic, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE FOOTER
# ─────────────────────────────────────────────────────────────────────────────

token_count_str = ""
if "result" in locals() and isinstance(result, dict) and "notes" in result:
    # Rough ~4 characters per token heuristic
    total_chars = len(result["research"]) + len(result["notes"]) + len(result["quiz"])
    approx_tokens = total_chars // 4
    token_count_str = f"&nbsp;&nbsp;&middot;&nbsp;&nbsp;Live Session Context: ~{approx_tokens:,} tokens"

st.markdown(
    f'<div class="page-footer"><span class="page-footer-text">StudyOS &nbsp;&middot;&nbsp; Powered by Google Gemini 2.5 Flash Lite &nbsp;&middot;&nbsp; Built with Streamlit{token_count_str}</span></div>',
    unsafe_allow_html=True,
)
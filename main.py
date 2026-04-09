"""
Nexus Agent Platform — Multi-Agent AI Dashboard v2
Enterprise Edition · Powered by Google Gemini 2.5 Flash Lite
Phase 2 Overhaul: Manrope/Inter fonts · Cyan accent · Animated pipeline · Glassmorphism v2
"""

import hashlib
import os
import random
import time
import urllib.parse

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
    Streamlit UI elements.
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
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus — Multi-Agent AI Platform",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Nexus Agent Platform — Multi-Agent AI Dashboard powered by Google Gemini 2.5 Flash Lite",
    },
)

# Share-link pre-load
if "share_topic" in st.query_params and not st.session_state.get("shared_loaded"):
    st.session_state.topic_input_state  = st.query_params["share_topic"]
    st.session_state.topic_widget_key   = st.query_params["share_topic"]
    st.session_state.shared_loaded      = True
    st.session_state.generate_requested = True

# Session state defaults
for _k, _v in [
    ("topic_input_state", ""),
    ("topic_widget_key",  ""),
    ("study_result",      None),
    ("study_difficulty",  "Medium"),
    ("active_tab",        0),
    ("agent_run_count",   0),
    ("quiz_score",        0),
    ("answered_questions", set()),
    ("revealed_questions", set()),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ═════════════════════════════════════════════════════════════════════════════
# NEXUS v2 DESIGN SYSTEM
# Phase 2: Manrope/Inter · Cyan accent · Charcoal base · Animated pipeline
# ═════════════════════════════════════════════════════════════════════════════
DESIGN_CSS = """
<style>

/* ── Google Fonts ────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Design Tokens ───────────────────────────────────────────────────────── */
:root {
  /* Core Palette — deep navy-charcoal, NOT pure black */
  --bg-void:        #080C12;
  --bg-base:        #0D1117;
  --bg-surface:     #111827;
  --bg-elevated:    #161F2E;
  --bg-overlay:     #1C2840;
  --bg-glass:       rgba(13, 20, 35, 0.65);
  --bg-glass-light: rgba(22, 32, 52, 0.50);

  /* Accent — refined cyan/sky (not neon) */
  --accent-primary:   #38BDF8;   /* sky-400 — main CTA, focus, active */
  --accent-glow:      rgba(56, 189, 248, 0.16);
  --accent-soft:      rgba(56, 189, 248, 0.08);
  --accent-secondary: #2DD4BF;   /* teal — success, secondary */
  --accent-warn:      #FBBF24;   /* amber */
  --accent-danger:    #F87171;   /* soft red */
  --accent-agent:     #A78BFA;   /* soft purple — agent identity */
  --accent-agent-glow: rgba(167, 139, 250, 0.14);

  /* Typography */
  --text-primary:   #EEF2FC;
  --text-secondary: #8899BB;
  --text-muted:     #4A5870;
  --text-inverse:   #080C12;

  /* Borders */
  --border-subtle:  rgba(255, 255, 255, 0.05);
  --border-default: rgba(255, 255, 255, 0.08);
  --border-active:  rgba(56, 189, 248, 0.40);
  --border-agent:   rgba(167, 139, 250, 0.30);

  /* Shadows */
  --shadow-sm:         0 1px 4px rgba(0,0,0,0.45);
  --shadow-md:         0 4px 20px rgba(0,0,0,0.55), 0 2px 8px rgba(0,0,0,0.35);
  --shadow-lg:         0 12px 48px rgba(0,0,0,0.65), 0 6px 20px rgba(0,0,0,0.40);
  --shadow-glow-cyan:  0 0 28px rgba(56,189,248,0.22), 0 0 10px rgba(56,189,248,0.12);
  --shadow-glow-agent: 0 0 28px rgba(167,139,250,0.18), 0 0 10px rgba(167,139,250,0.10);

  /* Spacing — 8pt grid */
  --sp-1: 4px;  --sp-2: 8px;   --sp-3: 12px;  --sp-4: 16px;
  --sp-5: 20px; --sp-6: 24px;  --sp-8: 32px;  --sp-10: 40px;
  --sp-12: 48px;--sp-16: 64px; --sp-20: 80px;

  /* Radius */
  --r-sm:   8px;
  --r-md:   12px;
  --r-lg:   18px;
  --r-xl:   26px;
  --r-pill: 9999px;

  /* Animation */
  --ease-expo:   cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-quart:  cubic-bezier(0.25, 1, 0.5, 1);
  --t-fast:  100ms;
  --t-base:  220ms;
  --t-slow:  380ms;
  --t-enter: 520ms;

  /* Typography */
  --font-display: 'Manrope', 'Inter', sans-serif;
  --font-body:    'Inter', 'Manrope', sans-serif;
  --font-mono:    'JetBrains Mono', monospace;

  /* Type scale */
  --ts-xs: 11px; --ts-sm: 13px; --ts-base: 15px;
  --ts-lg: 17px; --ts-xl: 20px; --ts-2xl: 24px;
  --ts-3xl: 32px; --ts-4xl: 44px;
  --lh-tight: 1.2; --lh-base: 1.55; --lh-relax: 1.75;
  --ls-tight: -0.025em; --ls-wide: 0.06em; --ls-wider: 0.10em;

  /* Shimmer */
  --shimmer-a: #161F2E;
  --shimmer-b: #1E2E46;
}

/* ── Reduced motion ──────────────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration:       0.01ms !important;
    animation-iteration-count: 1     !important;
    transition-duration:      0.01ms !important;
  }
}

/* ── Base ────────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: var(--font-body) !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── Streamlit chrome suppression ────────────────────────────────────────── */
#MainMenu, footer { visibility: hidden !important; }
header[data-testid="stHeader"] {
  background: transparent !important;
  box-shadow: none !important;
  height: 0 !important;
  min-height: 0 !important;
  overflow: hidden !important;
}
[data-testid="collapsedControl"] { display: none !important; }

/* ── App canvas + mesh + noise ───────────────────────────────────────────── */
.stApp {
  background-color: var(--bg-void) !important;
  color: var(--text-primary) !important;
  min-height: 100vh;
}
.stApp::before {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 70% 55% at 10% 20%, rgba(56,189,248,0.055) 0%, transparent 60%),
    radial-gradient(ellipse 60% 70% at 88% 78%, rgba(167,139,250,0.060) 0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 50% 50%, rgba(45,212,191,0.020) 0%, transparent 55%);
}
.stApp::after {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: 1;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='256' height='256'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.88' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='256' height='256' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
  background-size: 256px 256px;
  opacity: 0.028;
}

/* ═══════════════════════════════════════════════════════════════════════════
   FIXED TOP NAV (56px)
   ═══════════════════════════════════════════════════════════════════════════ */
.n-topnav {
  position: fixed; top: 0; left: 0; right: 0; height: 56px;
  background: rgba(8, 12, 18, 0.90);
  backdrop-filter: blur(28px) saturate(160%);
  -webkit-backdrop-filter: blur(28px) saturate(160%);
  border-bottom: 1px solid var(--border-subtle);
  display: flex; align-items: center;
  padding: 0 var(--sp-8); gap: var(--sp-3); z-index: 9998;
}
.n-topnav-mark {
  width: 30px; height: 30px; flex-shrink: 0;
  background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-agent) 100%);
  border-radius: var(--r-sm); display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-weight: 800; font-size: 13px;
  color: var(--text-inverse);
  box-shadow: var(--shadow-glow-cyan);
}
.n-topnav-logo {
  font-family: var(--font-display); font-weight: 800; font-size: var(--ts-lg);
  color: var(--text-primary); letter-spacing: var(--ls-tight);
}
.n-topnav-div {
  width: 1px; height: 16px; background: var(--border-default);
}
.n-topnav-sub {
  font-size: 11px; font-weight: 600; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: var(--ls-wider);
  font-family: var(--font-body);
}
.n-topnav-spacer { flex: 1; }
.n-badge {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: 3px var(--sp-3);
  background: rgba(22,32,52,0.80);
  border: 1px solid var(--border-subtle);
  border-radius: var(--r-pill);
  font-size: var(--ts-xs); font-family: var(--font-mono);
  color: var(--text-secondary);
}
.n-badge + .n-badge { margin-left: var(--sp-2); }

/* ═══════════════════════════════════════════════════════════════════════════
   FIXED STATUS BAR (32px)
   ═══════════════════════════════════════════════════════════════════════════ */
.n-statusbar {
  position: fixed; bottom: 0; left: 0; right: 0; height: 32px;
  background: var(--bg-overlay);
  border-top: 1px solid var(--border-subtle);
  display: flex; align-items: center;
  padding: 0 var(--sp-6); gap: var(--sp-5);
  z-index: 9998;
  font-family: var(--font-mono); font-size: var(--ts-xs); color: var(--text-muted);
}
.sb-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: var(--accent-secondary);
}
.sb-sep { color: var(--border-default); }

/* pulse */
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50%       { transform: scale(1.6); opacity: 0.4; }
}
.pulse { animation: pulse 1.6s ease-in-out infinite; }

/* ═══════════════════════════════════════════════════════════════════════════
   LAYOUT PADDING
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stMainBlockContainer"],
section.main > div:first-child {
  padding-top: 70px !important;
  padding-bottom: 52px !important;
}
[data-testid="stMainBlockContainer"] {
  max-width: 1380px !important;
  padding-left: var(--sp-10) !important;
  padding-right: var(--sp-10) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SIDEBAR — Floating navigation panel
   ═══════════════════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
  background: rgba(8, 14, 22, 0.97) !important;
  border-right: 1px solid var(--border-subtle) !important;
  backdrop-filter: blur(28px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(28px) saturate(160%) !important;
}
section[data-testid="stSidebar"] > div {
  padding-top: 70px !important;
  padding-left: var(--sp-5) !important;
  padding-right: var(--sp-5) !important;
}

/* brand */
.sb-brand {
  display: flex; align-items: center; gap: var(--sp-3);
  margin-bottom: var(--sp-1);
}
.sb-mark {
  width: 36px; height: 36px; flex-shrink: 0;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-agent));
  border-radius: var(--r-md);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-weight: 800; font-size: 15px;
  color: var(--text-inverse);
  box-shadow: var(--shadow-glow-cyan);
}
.sb-name {
  font-family: var(--font-display); font-weight: 800; font-size: var(--ts-base);
  color: var(--text-primary); letter-spacing: var(--ls-tight);
}
.sb-tagline {
  font-size: var(--ts-xs); color: var(--text-muted);
  text-transform: uppercase; letter-spacing: var(--ls-wider); font-weight: 600;
  margin-top: 2px;
}

/* section labels */
.sb-label {
  font-size: var(--ts-xs); letter-spacing: var(--ls-wider);
  color: var(--text-muted); text-transform: uppercase; font-weight: 700;
  margin: var(--sp-6) 0 var(--sp-3); display: block;
}

/* status badge */
.n-status {
  display: inline-flex; align-items: center; gap: var(--sp-2);
  padding: 4px var(--sp-3); border-radius: var(--r-pill);
  font-size: var(--ts-xs); font-weight: 600;
}
.n-status-ok  { background: rgba(45,212,191,0.10); color: var(--accent-secondary); border: 1px solid rgba(45,212,191,0.20); }
.n-status-inf { background: rgba(56,189,248,0.10); color: var(--accent-primary);   border: 1px solid rgba(56,189,248,0.20); }

/* ── Agent cards in sidebar ─── */
.agent-card {
  background: var(--bg-glass);
  backdrop-filter: blur(18px) saturate(150%);
  -webkit-backdrop-filter: blur(18px) saturate(150%);
  border: 1px solid var(--border-subtle);
  border-left: 3px solid var(--accent-agent);
  border-radius: var(--r-lg);
  padding: var(--sp-4) var(--sp-5);
  margin-bottom: var(--sp-3);
  position: relative; overflow: hidden;
  transition: transform var(--t-base) var(--ease-expo),
              box-shadow var(--t-base) var(--ease-expo),
              border-color var(--t-base) ease;
}
.agent-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, var(--accent-agent), transparent);
  opacity: 0.45;
}
.agent-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow-agent);
  border-color: var(--border-agent);
}
.agent-name {
  font-family: var(--font-display); font-size: var(--ts-base); font-weight: 700;
  color: var(--text-primary); letter-spacing: var(--ls-tight);
  margin-bottom: 2px;
}
.agent-role {
  font-size: var(--ts-xs); color: var(--text-muted);
  text-transform: uppercase; letter-spacing: var(--ls-wider); font-weight: 600;
  margin-bottom: var(--sp-3);
}
.agent-footer {
  display: flex; align-items: center; justify-content: space-between;
}
.agent-id { font-size: var(--ts-xs); color: var(--text-muted); font-family: var(--font-mono); }

/* ── Status Pill ─── */
.pill {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: var(--r-pill);
  font-size: var(--ts-xs); font-weight: 700;
  font-family: var(--font-mono); letter-spacing: 0.05em;
}
.pill-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.p-idle    { background: rgba(74,88,112,0.18); color: var(--text-muted);      border: 1px solid rgba(74,88,112,0.25); }
.p-idle    .pill-dot { background: var(--text-muted); }
.p-running { background: rgba(56,189,248,0.10); color: var(--accent-primary); border: 1px solid rgba(56,189,248,0.22); }
.p-running .pill-dot { background: var(--accent-primary); animation: pulse 1.3s ease-in-out infinite; }
.p-success { background: rgba(45,212,191,0.10); color: var(--accent-secondary);border: 1px solid rgba(45,212,191,0.20); }
.p-success .pill-dot { background: var(--accent-secondary); }
.p-warning { background: rgba(251,191,36,0.10); color: var(--accent-warn);    border: 1px solid rgba(251,191,36,0.22); }
.p-warning .pill-dot { background: var(--accent-warn); }
.p-error   { background: rgba(248,113,113,0.10); color: var(--accent-danger);  border: 1px solid rgba(248,113,113,0.22); }
.p-error   .pill-dot { background: var(--accent-danger); }
.p-queued  { background: rgba(167,139,250,0.10); color: var(--accent-agent);   border: 1px solid rgba(167,139,250,0.22); }
.p-queued  .pill-dot { background: var(--accent-agent); }

/* ── Difficulty pills ─── */
.diff-easy   { color: var(--accent-secondary); }
.diff-medium { color: var(--accent-warn); }
.diff-hard   { color: var(--accent-danger); }

/* ═══════════════════════════════════════════════════════════════════════════
   BUTTONS
   ═══════════════════════════════════════════════════════════════════════════ */
.stButton > button {
  background: var(--accent-primary) !important;
  border: none !important;
  border-radius: var(--r-md) !important;
  color: var(--text-inverse) !important;
  font-family: var(--font-display) !important;
  font-weight: 700 !important; font-size: var(--ts-sm) !important;
  letter-spacing: 0.02em !important;
  padding: var(--sp-3) var(--sp-5) !important;
  box-shadow: var(--shadow-glow-cyan) !important;
  transition: transform var(--t-base) var(--ease-spring),
              filter var(--t-fast) ease,
              box-shadow var(--t-base) var(--ease-expo) !important;
}
.stButton > button:hover {
  filter: brightness(1.12) !important;
  transform: scale(1.025) translateY(-1px) !important;
  box-shadow: 0 0 36px rgba(56,189,248,0.40), 0 0 14px rgba(56,189,248,0.20) !important;
}
.stButton > button:active {
  transform: scale(0.97) !important;
  transition-duration: 80ms !important;
}

.stDownloadButton > button {
  background: transparent !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--r-md) !important;
  color: var(--text-secondary) !important;
  font-family: var(--font-body) !important; font-weight: 500 !important;
  font-size: var(--ts-sm) !important;
  padding: var(--sp-3) var(--sp-5) !important;
  transition: border-color var(--t-base) ease,
              color var(--t-base) ease,
              transform var(--t-base) var(--ease-spring),
              background var(--t-base) ease !important;
}
.stDownloadButton > button:hover {
  border-color: var(--border-active) !important;
  color: var(--text-primary) !important;
  transform: scale(1.02) !important;
  background: var(--accent-soft) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   TEXT INPUT — CommandInput variant
   ═══════════════════════════════════════════════════════════════════════════ */
.stTextInput > div[data-baseweb="input"] {
  align-items: center !important;
}

.stTextInput > div > div > input {
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--r-md) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-body) !important; font-size: var(--ts-base) !important;
  /* Adjusting padding and line-height for perfect vertical centering inside 56px box */
  padding: 14px var(--sp-5) !important;
  line-height: 1.5 !important;
  height: 56px !important;
  transition: border-color var(--t-fast) ease,
              box-shadow var(--t-fast) ease,
              transform var(--t-fast) ease !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--border-active) !important;
  box-shadow: var(--shadow-glow-cyan) !important;
  transform: scale(1.004) !important;
  outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: var(--text-muted) !important; }

/* ═══════════════════════════════════════════════════════════════════════════
   TABS
   ═══════════════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  border-bottom: 1px solid var(--border-subtle) !important;
  gap: var(--sp-8) !important; background: transparent !important;
}
.stTabs [data-baseweb="tab"] {
  color: var(--text-muted) !important;
  font-family: var(--font-body) !important; font-weight: 500 !important;
  font-size: var(--ts-sm) !important;
  padding: var(--sp-3) 0 !important;
  border-bottom: 2px solid transparent !important;
  background: transparent !important;
  transition: color var(--t-base) ease !important;
}
.stTabs [aria-selected="true"] {
  color: var(--accent-primary) !important;
  border-bottom-color: var(--accent-primary) !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text-secondary) !important; }
[data-testid="stTabContent"] { padding-top: var(--sp-6) !important; }

/* ═══════════════════════════════════════════════════════════════════════════
   GLASS CARD — base component
   ═══════════════════════════════════════════════════════════════════════════ */
.g-card {
  background: var(--bg-glass);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  border: 1px solid var(--border-subtle);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-md);
  padding: var(--sp-6);
  margin-bottom: var(--sp-6);
  transition: transform var(--t-base) var(--ease-expo),
              box-shadow var(--t-base) var(--ease-expo),
              border-color var(--t-base) ease;
}
.g-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-default);
  box-shadow: var(--shadow-lg);
}

/* ds-card alias for backward compat */
.ds-card { background: var(--bg-glass); backdrop-filter: blur(24px) saturate(160%); -webkit-backdrop-filter: blur(24px) saturate(160%); border: 1px solid var(--border-subtle); border-radius: var(--r-lg); box-shadow: var(--shadow-md); padding: var(--sp-6); margin-bottom: var(--sp-6); transition: transform var(--t-base) var(--ease-expo), border-color var(--t-base) ease; }
.ds-card:hover { transform: translateY(-2px); border-color: var(--border-default); }
.ds-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--sp-5); padding-bottom: var(--sp-4); border-bottom: 1px solid var(--border-subtle); }
.ds-card-title { font-family: var(--font-display); font-size: var(--ts-xl); font-weight: 700; color: var(--text-primary); letter-spacing: var(--ls-tight); margin: 0; }
.ds-card-meta  { font-size: var(--ts-sm); color: var(--text-secondary); margin-top: var(--sp-1); }
.ds-card-tag   { display: inline-flex; align-items: center; gap: 6px; background: rgba(167,139,250,0.10); color: var(--accent-agent); font-size: var(--ts-xs); letter-spacing: var(--ls-wider); text-transform: uppercase; padding: 4px var(--sp-3); border-radius: var(--r-pill); font-weight: 700; border: 1px solid rgba(167,139,250,0.20); white-space: nowrap; }

/* ═══════════════════════════════════════════════════════════════════════════
   METRIC TILES — Phase 2 redesign
   ═══════════════════════════════════════════════════════════════════════════ */
.metric-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--sp-4); margin-bottom: var(--sp-8);
}
@keyframes tileIn {
  from { opacity: 0; transform: translateY(14px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.metric-tile {
  background: var(--bg-glass);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  border: 1px solid var(--border-subtle);
  border-radius: var(--r-lg);
  padding: var(--sp-5) var(--sp-5) var(--sp-4);
  position: relative; overflow: hidden;
  animation: tileIn var(--t-enter) var(--ease-expo) backwards;
  transition: transform var(--t-base) var(--ease-expo),
              border-color var(--t-base) ease,
              box-shadow var(--t-base) ease;
}
.metric-tile::after {
  content: '';
  position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
  opacity: 0;
  transition: opacity var(--t-base) ease;
}
.metric-tile:hover { transform: translateY(-3px); border-color: var(--border-default); box-shadow: var(--shadow-md); }
.metric-tile:hover::after { opacity: 0.6; }
.metric-tile:nth-child(1) { animation-delay: 60ms; }
.metric-tile:nth-child(2) { animation-delay: 110ms; }
.metric-tile:nth-child(3) { animation-delay: 160ms; }
.metric-tile:nth-child(4) { animation-delay: 210ms; }
.metric-tile:nth-child(5) { animation-delay: 260ms; }

.metric-label {
  font-size: var(--ts-xs); letter-spacing: var(--ls-wider); text-transform: uppercase;
  color: var(--text-muted); font-weight: 700; display: block; margin-bottom: var(--sp-2);
}
.metric-value {
  font-family: var(--font-display); font-size: var(--ts-3xl); font-weight: 800;
  color: var(--text-primary); letter-spacing: var(--ls-tight); line-height: var(--lh-tight);
}
.mv-cyan   { color: var(--accent-primary); }
.mv-teal   { color: var(--accent-secondary); }
.mv-amber  { color: var(--accent-warn); }
.mv-red    { color: var(--accent-danger); }
.mv-purple { color: var(--accent-agent); }
.metric-sub { font-size: var(--ts-xs); color: var(--text-muted); margin-top: var(--sp-1); font-family: var(--font-mono); }

/* ═══════════════════════════════════════════════════════════════════════════
   ANIMATED PIPELINE TRACK
   ═══════════════════════════════════════════════════════════════════════════ */
.pipeline-track {
  display: flex; align-items: center; gap: var(--sp-2);
  margin: var(--sp-5) 0 var(--sp-8);
  padding: var(--sp-2) 0; overflow-x: auto; scrollbar-width: none;
}
.pipeline-track::-webkit-scrollbar { display: none; }

/* Connector line between steps */
.pipeline-line {
  flex: 1; min-width: 32px; max-width: 64px; height: 2px;
  background: var(--border-default);
  border-radius: 1px; position: relative; overflow: hidden;
}
.pipeline-line::after {
  content: '';
  position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, var(--accent-primary), var(--accent-agent), transparent);
  animation: lineFlow 2.8s ease-in-out infinite;
}
@keyframes lineFlow {
  0%   { left: -100%; }
  100% { left: 100%; }
}

.pipeline-node {
  display: flex; align-items: center; gap: var(--sp-2);
  background: var(--bg-glass);
  backdrop-filter: blur(14px);
  border: 1px solid var(--border-default);
  border-radius: var(--r-md);
  padding: 10px var(--sp-4);
  font-family: var(--font-body); font-size: var(--ts-sm); font-weight: 600;
  color: var(--text-secondary); white-space: nowrap;
  transition: all var(--t-base) var(--ease-expo);
  flex-shrink: 0;
}
.pipeline-node:hover {
  border-color: var(--border-default);
  color: var(--text-secondary);
  transform: translateY(-1px);
}
.pipeline-node-num {
  width: 22px; height: 22px; border-radius: 50%;
  background: var(--bg-overlay);
  font-size: var(--ts-xs); font-weight: 700;
  color: var(--text-muted); font-family: var(--font-mono);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all var(--t-base) ease;
}

/* Active node glow effect */
.pipeline-node-active {
  border-color: rgba(56,189,248,0.45) !important;
  color: var(--accent-primary) !important;
  background: rgba(56,189,248,0.07) !important;
  box-shadow: var(--shadow-glow-cyan) !important;
}
.pipeline-node-active .pipeline-node-num {
  background: var(--accent-primary);
  color: var(--text-inverse);
}
.pipeline-node-done {
  border-color: rgba(45,212,191,0.35) !important;
  color: var(--accent-secondary) !important;
  background: rgba(45,212,191,0.05) !important;
}
.pipeline-node-done .pipeline-node-num {
  background: var(--accent-secondary);
  color: var(--text-inverse);
}

/* ═══════════════════════════════════════════════════════════════════════════
   PAGE HEADER
   ═══════════════════════════════════════════════════════════════════════════ */
.page-header {
  padding: var(--sp-8) 0 var(--sp-6);
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: var(--sp-6);
}
.page-eyebrow {
  font-size: var(--ts-xs); font-weight: 700; letter-spacing: var(--ls-wider);
  text-transform: uppercase; color: var(--accent-primary);
  display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-3);
}
.page-eyebrow-rule {
  display: inline-block; width: 22px; height: 2px;
  background: var(--accent-primary); border-radius: 1px;
}
.page-title {
  font-family: var(--font-display); font-size: var(--ts-4xl); font-weight: 800;
  letter-spacing: var(--ls-tight); line-height: var(--lh-tight);
  margin-bottom: var(--sp-4);
  /* Gradient text fill */
  background: linear-gradient(135deg, var(--text-primary) 40%, var(--accent-primary) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.page-sub {
  font-size: var(--ts-base); color: var(--text-secondary);
  max-width: 560px; line-height: var(--lh-relax);
}

/* ═══════════════════════════════════════════════════════════════════════════
   STICKY COMMAND BAR
   ═══════════════════════════════════════════════════════════════════════════ */
.command-bar {
  position: sticky; top: 56px; z-index: 100;
  background: rgba(8, 12, 18, 0.90);
  backdrop-filter: blur(28px) saturate(160%);
  -webkit-backdrop-filter: blur(28px) saturate(160%);
  padding: var(--sp-4) 0 var(--sp-4);
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: var(--sp-6);
}

/* ═══════════════════════════════════════════════════════════════════════════
   SKELETON LOADER — shimmer
   ═══════════════════════════════════════════════════════════════════════════ */
@keyframes shimmer {
  0%   { background-position: -700px 0; }
  100% { background-position:  700px 0; }
}
.skel {
  background: linear-gradient(90deg,
    var(--shimmer-a) 25%, var(--shimmer-b) 50%, var(--shimmer-a) 75%);
  background-size: 1400px 100%;
  animation: shimmer 1.8s infinite;
  border-radius: var(--r-sm);
}
.skel-sm   { height: 12px; }
.skel-base { height: 16px; }
.skel-lg   { height: 24px; }
.skel-xl   { height: 48px; }
.skel-card {
  background: var(--bg-glass); border: 1px solid var(--border-subtle);
  border-radius: var(--r-lg); padding: var(--sp-6); margin-bottom: var(--sp-4);
}

/* ═══════════════════════════════════════════════════════════════════════════
   EMPTY STATE
   ═══════════════════════════════════════════════════════════════════════════ */
@keyframes emptyIn {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
.empty-state {
  text-align: center; padding: var(--sp-20) var(--sp-8);
  background: var(--bg-glass);
  backdrop-filter: blur(24px) saturate(160%); -webkit-backdrop-filter: blur(24px) saturate(160%);
  border: 1px solid var(--border-subtle); border-radius: var(--r-xl);
  margin-top: var(--sp-4); position: relative; overflow: hidden;
  animation: emptyIn var(--t-enter) var(--ease-expo) backwards;
}
.empty-state::before {
  content: ''; position: absolute; top: -30%; left: 50%; transform: translateX(-50%);
  width: 480px; height: 480px;
  background: radial-gradient(circle, rgba(56,189,248,0.04) 0%, transparent 70%);
  pointer-events: none;
}
.empty-icon { font-size: 54px; display: block; margin-bottom: var(--sp-5); }
.empty-title {
  font-family: var(--font-display); font-size: var(--ts-3xl); font-weight: 800;
  color: var(--text-primary); letter-spacing: var(--ls-tight); margin-bottom: var(--sp-3);
}
.empty-sub {
  font-size: var(--ts-base); color: var(--text-secondary);
  max-width: 480px; margin: 0 auto var(--sp-8); line-height: var(--lh-relax);
}

/* ═══════════════════════════════════════════════════════════════════════════
   MARQUEE CHIPS
   ═══════════════════════════════════════════════════════════════════════════ */
.marquee-wrap {
  overflow: hidden; width: 100%; margin-top: var(--sp-6); white-space: nowrap;
  -webkit-mask-image: linear-gradient(to right, transparent, black 10%, black 90%, transparent);
  mask-image: linear-gradient(to right, transparent, black 10%, black 90%, transparent);
}
@keyframes marquee { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
.marquee-track { display: inline-block; animation: marquee 34s linear infinite; }
.marquee-track:hover { animation-play-state: paused; }
.topic-chip {
  display: inline-block;
  background: var(--bg-elevated); border: 1px solid var(--border-default);
  border-radius: var(--r-pill); padding: 5px var(--sp-4);
  font-size: var(--ts-sm); font-family: var(--font-body); font-weight: 500;
  color: var(--text-secondary); margin: 4px;
  transition: border-color var(--t-base) ease, color var(--t-base) ease; cursor: pointer;
}
.topic-chip:hover { border-color: rgba(56,189,248,0.40); color: var(--accent-primary); }

/* ═══════════════════════════════════════════════════════════════════════════
   STUDY NOTES
   ═══════════════════════════════════════════════════════════════════════════ */
.study-notes-container {
  font-family: var(--font-body); font-size: var(--ts-base);
  line-height: var(--lh-relax); color: var(--text-primary);
}
.note-section-title {
  font-family: var(--font-display); font-size: var(--ts-xl); font-weight: 700;
  color: var(--text-primary); letter-spacing: var(--ls-tight);
  border-bottom: 1px solid var(--border-subtle);
  margin-top: var(--sp-8); margin-bottom: var(--sp-4); padding-bottom: var(--sp-3);
}
@keyframes noteIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
.study-notes-container p  { animation: noteIn var(--t-slow) var(--ease-expo) backwards; }
.study-notes-container li { animation: noteIn var(--t-slow) var(--ease-expo) backwards; animation-delay: 180ms; }
.study-notes-container p:nth-child(1) { animation-delay: 40ms; }
.study-notes-container p:nth-child(2) { animation-delay: 90ms; }
.study-notes-container p:nth-child(3) { animation-delay: 140ms; }

/* ═══════════════════════════════════════════════════════════════════════════
   QUIZ — Custom radio buttons + feedback states
   ═══════════════════════════════════════════════════════════════════════════ */
.q-card-title {
  font-family: var(--font-body); font-size: var(--ts-base); font-weight: 600;
  color: var(--text-primary); line-height: var(--lh-base); margin-bottom: var(--sp-4);
}
/* Streamlit radio button overrides */
[data-testid="stRadio"] > div { gap: var(--sp-2) !important; }
[data-testid="stRadio"] label {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--r-md) !important;
  padding: var(--sp-3) var(--sp-4) !important;
  transition: border-color var(--t-base) ease, background var(--t-base) ease !important;
  cursor: pointer !important;
}
[data-testid="stRadio"] label:hover {
  border-color: rgba(56,189,248,0.35) !important;
  background: rgba(56,189,248,0.05) !important;
}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
  border-color: var(--border-active) !important;
  background: var(--accent-soft) !important;
}
/* answer feedback */
.quiz-feedback-correct {
  padding: var(--sp-4) var(--sp-5); border-radius: var(--r-md);
  border-left: 3px solid var(--accent-secondary);
  background: rgba(45,212,191,0.06);
  border-top: 1px solid rgba(45,212,191,0.12);
  border-right: 1px solid rgba(45,212,191,0.08);
  border-bottom: 1px solid rgba(45,212,191,0.08);
  box-shadow: 0 0 20px rgba(45,212,191,0.08);
  animation: feedbackIn var(--t-base) var(--ease-expo) backwards;
}
.quiz-feedback-wrong {
  padding: var(--sp-4) var(--sp-5); border-radius: var(--r-md);
  border-left: 3px solid var(--accent-danger);
  background: rgba(248,113,113,0.05);
  border-top: 1px solid rgba(248,113,113,0.10);
  border-right: 1px solid rgba(248,113,113,0.08);
  border-bottom: 1px solid rgba(248,113,113,0.08);
  opacity: 0.9;
  animation: feedbackIn var(--t-base) var(--ease-expo) backwards;
}
@keyframes feedbackIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
.quiz-feedback-label {
  font-family: var(--font-display); font-size: var(--ts-sm); font-weight: 700;
  margin-bottom: var(--sp-2);
}
.quiz-feedback-exp {
  font-size: var(--ts-sm); color: var(--text-secondary); line-height: var(--lh-relax);
}
.k-term {
  background: var(--bg-surface); border: 1px solid var(--border-default);
  border-radius: var(--r-sm); padding: 2px var(--sp-2);
  color: var(--accent-primary); font-size: var(--ts-sm); font-family: var(--font-mono);
}

/* ═══════════════════════════════════════════════════════════════════════════
   SECTION LABEL
   ═══════════════════════════════════════════════════════════════════════════ */
.section-label {
  font-size: var(--ts-xs); letter-spacing: var(--ls-wider); text-transform: uppercase;
  color: var(--text-muted); font-weight: 700; display: block; margin-bottom: var(--sp-3);
}

/* ═══════════════════════════════════════════════════════════════════════════
   STREAMLIT NATIVE OVERRIDES
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stProgress"] > div > div {
  background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)) !important;
  border-radius: var(--r-pill) !important;
}
[data-testid="stStatusWidget"] {
  background: var(--bg-glass) !important; border: 1px solid var(--border-subtle) !important;
  border-radius: var(--r-lg) !important; backdrop-filter: blur(20px) !important;
}
[data-testid="stCodeBlock"] {
  background: var(--bg-surface) !important; border: 1px solid var(--border-subtle) !important;
  border-radius: var(--r-md) !important;
}
[data-testid="stCodeBlock"] pre { font-family: var(--font-mono) !important; color: var(--text-secondary) !important; }
[data-testid="stAlert"] {
  background: var(--bg-overlay) !important; border: 1px solid var(--border-default) !important;
  border-radius: var(--r-md) !important;
}
[data-testid="stToast"] {
  background: var(--bg-glass) !important; border: 1px solid var(--border-default) !important;
  backdrop-filter: blur(24px) !important; border-radius: var(--r-lg) !important;
}
[data-testid="stWidgetLabel"] p {
  color: var(--text-secondary) !important; font-size: var(--ts-sm) !important;
  font-family: var(--font-body) !important;
}
[data-testid="stForm"] { background: transparent !important; border: none !important; padding: 0 !important; }
[data-testid="stDivider"], hr { border-color: var(--border-subtle) !important; }

/* Global color resets */
p, li, span { color: var(--text-primary) !important; }
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-display) !important;
  color: var(--text-primary) !important;
  letter-spacing: var(--ls-tight) !important;
}
code {
  font-family: var(--font-mono) !important; background: var(--bg-surface) !important;
  color: var(--accent-primary) !important; border-radius: var(--r-sm) !important;
  padding: 2px var(--sp-2) !important;
}

/* Streamlit icon fix */
i.material-symbols-rounded, span.material-symbols-rounded {
  font-family: 'Material Symbols Rounded' !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-void); }
::-webkit-scrollbar-thumb { background: var(--border-default); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-active); }

/* Focus ring */
:focus-visible { outline: 2px solid var(--accent-primary) !important; outline-offset: 3px !important; }

/* Count-up target */
.count-up { display: inline-block; }

</style>
"""

st.markdown(DESIGN_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FIXED TOP NAV
# ─────────────────────────────────────────────────────────────────────────────
_run_ct  = st.session_state.agent_run_count
_run_lbl = f"{_run_ct} run{'s' if _run_ct != 1 else ''}" if _run_ct > 0 else "Ready"

st.markdown(
    f"""
    <div class="n-topnav">
      <div class="n-topnav-mark">N</div>
      <span class="n-topnav-logo">Nexus</span>
      <div class="n-topnav-div"></div>
      <span class="n-topnav-sub">Agent Platform</span>
      <div class="n-topnav-spacer"></div>
      <div class="n-badge"><span class="sb-dot pulse"></span>Connected</div>
      <div class="n-badge">⬡ 3 Agents &nbsp;&middot;&nbsp; {_run_lbl}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Floating navigation panel
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="sb-brand">
          <div class="sb-mark">N</div>
          <div>
            <div class="sb-name">Nexus</div>
            <div class="sb-tagline">Agent Platform</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Agent Status ──────────────────────────────────────────────────────────
    st.markdown('<span class="sb-label">Agent Status</span>', unsafe_allow_html=True)

    agents = [
        ("Research Agent",   "Knowledge Acquisition",  "#1"),
        ("Summarizer Agent", "Concept Distillation",   "#2"),
        ("Quiz Agent",       "Assessment Generation",  "#3"),
    ]
    for name, role, num in agents:
        st.markdown(
            f"""
            <div class="agent-card">
              <div class="agent-name">{name}</div>
              <div class="agent-role">{role}</div>
              <div class="agent-footer">
                <span class="pill p-idle"><span class="pill-dot"></span>IDLE</span>
                <span class="agent-id">Agent {num}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Quiz Configuration ─────────────────────────────────────────────────────
    st.markdown('<span class="sb-label">Quiz Configuration</span>', unsafe_allow_html=True)
    difficulty = st.select_slider(
        "Difficulty",
        options=["Easy", "Medium", "Hard"],
        value="Medium",
        help="Controls MCQ complexity and plausibility of distractors",
    )
    _pill_map = {"Easy": "p-success", "Medium": "p-warning", "Hard": "p-error"}
    st.markdown(
        f"""
        <div style="margin-top:var(--sp-2);">
          <span class="pill {_pill_map[difficulty]}">
            <span class="pill-dot"></span>{difficulty.upper()}
          </span>
          <span style="font-size:var(--ts-xs);color:var(--text-muted);margin-left:var(--sp-2);">
            mode active
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── System status widget (compact) ────────────────────────────────────────
    st.markdown('<span class="sb-label">System</span>', unsafe_allow_html=True)
    api_key_input = os.getenv("GEMINI_API_KEY")
    st.markdown(
        f"""
        <div style="display:flex;flex-direction:column;gap:var(--sp-2);">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:var(--ts-xs);color:var(--text-muted);font-weight:600;">Model</span>
            <span style="font-size:var(--ts-xs);font-family:var(--font-mono);color:var(--text-secondary);">Gemini 2.5 Flash</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:var(--ts-xs);color:var(--text-muted);font-weight:600;">Agents</span>
            <span style="font-size:var(--ts-xs);font-family:var(--font-mono);color:var(--text-secondary);">3 active</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:var(--ts-xs);color:var(--text-muted);font-weight:600;">Cache TTL</span>
            <span style="font-size:var(--ts-xs);font-family:var(--font-mono);color:var(--text-secondary);">60 min</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:var(--ts-xs);color:var(--text-muted);font-weight:600;">API Key</span>
            <span class="n-status {'n-status-ok' if api_key_input else 'n-status-inf'}">
              {'● Active' if api_key_input else '● .env'}
            </span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="page-header">
      <div class="page-eyebrow">
        <span class="page-eyebrow-rule"></span>
        Multi-Agent AI Platform
      </div>
      <div class="page-title">Study Intelligence</div>
      <div class="page-sub">
        Three coordinated AI agents research any topic, distil it into structured
        study notes, and generate assessed quiz questions — fully automated.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Animated Pipeline Track ───────────────────────────────────────────────────
st.markdown(
    """
    <div class="pipeline-track">
      <div class="pipeline-node">
        <div class="pipeline-node-num">1</div>
        🔍 Research Agent
      </div>
      <div class="pipeline-line"></div>
      <div class="pipeline-node">
        <div class="pipeline-node-num">2</div>
        📝 Summarizer Agent
      </div>
      <div class="pipeline-line"></div>
      <div class="pipeline-node">
        <div class="pipeline-node-num">3</div>
        🧠 Quiz Agent
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# STICKY COMMAND BAR — Topic input
# ─────────────────────────────────────────────────────────────────────────────
if "topic_input_state" not in st.session_state:
    st.session_state.topic_input_state = ""

# Apply sticky command-bar styling directly to the form's Streamlit block
st.markdown(
    """
    <style>
    /* Sticky command bar — targets the form block wrapper */
    [data-testid="stForm"] {
      position: sticky !important;
      top: 56px !important;
      z-index: 100 !important;
      background: rgba(8, 12, 18, 0.92) !important;
      backdrop-filter: blur(28px) saturate(160%) !important;
      -webkit-backdrop-filter: blur(28px) saturate(160%) !important;
      padding: 12px 0 10px !important;
      border-bottom: 1px solid rgba(255,255,255,0.05) !important;
      margin-bottom: 24px !important;
      border-radius: 0 !important;
    }
    /* Force horizontal layout for columns inside the form */
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        align-items: flex-end !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.form(key="topic_form", border=False):
    # Setting ratio [5, 1] and aligning bottoms
    col_inp, col_btn = st.columns([5, 1], gap="small", vertical_alignment="bottom")
    with col_inp:
        topic = st.text_input(
            "Topic",
            placeholder="Enter any topic — e.g. Transformer Architecture, French Revolution, CRISPR…  ⌘↵",
            label_visibility="collapsed",
            key="topic_widget_key",
        )
    with col_btn:
        generate_clicked = st.form_submit_button(
            "Generate ⚡", use_container_width=True, type="primary"
        )

if topic:
    st.session_state.topic_input_state = topic

# ─────────────────────────────────────────────────────────────────────────────
# CACHING — 1h TTL
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def cached_study_package(topic: str, difficulty: str, _key_hash: str):
    """Wraps the orchestrator with Streamlit's cache layer."""
    return run_study_assistant(topic, difficulty=difficulty)


# ─────────────────────────────────────────────────────────────────────────────
# GENERATION PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
if generate_clicked or st.session_state.get("generate_requested", False):
    st.session_state.generate_requested = False

    if not topic or not topic.strip():
        st.warning("Please enter a topic before generating.", icon=None)
        st.stop()

    topic        = topic.strip()
    api_key_hash = hashlib.md5(b"env").hexdigest()

    # Skeleton loading state
    _skel = st.empty()
    _skel.markdown(
        """
        <div class="skel-card">
          <div class="skel skel-lg" style="width:42%;margin-bottom:var(--sp-4);"></div>
          <div class="skel skel-base" style="width:76%;margin-bottom:var(--sp-2);"></div>
          <div class="skel skel-base" style="width:60%;margin-bottom:var(--sp-2);"></div>
          <div class="skel skel-sm"   style="width:48%;margin-bottom:var(--sp-6);"></div>
          <div style="display:flex;gap:var(--sp-4);">
            <div class="skel skel-xl" style="flex:1;border-radius:var(--r-md);"></div>
            <div class="skel skel-xl" style="flex:1;border-radius:var(--r-md);"></div>
            <div class="skel skel-xl" style="flex:1;border-radius:var(--r-md);"></div>
            <div class="skel skel-xl" style="flex:1;border-radius:var(--r-md);"></div>
            <div class="skel skel-xl" style="flex:1;border-radius:var(--r-md);"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.status("Initialising Nexus agent pipeline…", expanded=True) as status_box:
        progress_bar = st.progress(0, text="Booting agents…")
        st.caption(f"Topic: **{topic}** ·  Difficulty: **{difficulty}**")

        status_log: list[str] = []
        live_status = _make_status_callback(status_box, progress_bar, status_log)

        live_status("🔍 Research Agent — acquiring knowledge")
        live_status("📝 Summarizer Agent — distilling concepts")
        live_status(f"🧠 Quiz Agent — composing {difficulty} questions")

        try:
            result = cached_study_package(topic, difficulty, api_key_hash)

            progress_bar.progress(100, text="Complete")
            status_box.update(
                label=f"✅ All agents completed — {result.get('elapsed_time', '—')}s elapsed",
                state="complete", expanded=False,
            )

            st.session_state.study_result      = result
            st.session_state.study_difficulty  = difficulty
            st.session_state.quiz_score         = 0
            st.session_state.answered_questions = set()
            st.session_state.revealed_questions = set()
            st.session_state.agent_run_count   += 1

        except EnvironmentError as exc:
            _skel.empty()
            status_box.update(label="Configuration error", state="error")
            st.error(f"**API Key Error:** {exc}\n\nAdd your Gemini API key to the `.env` file.")
            st.stop()

        except RuntimeError as exc:
            _skel.empty()
            status_box.update(label="Agent pipeline failed", state="error")
            st.error(f"**Agent Error:** {exc}\n\nThis is often a transient API timeout. Please try again.")
            st.stop()

        except Exception as exc:
            _skel.empty()
            status_box.update(label="Unexpected error", state="error")
            st.error(f"**Error:** {exc}\n\nCheck your internet connection and API key configuration.")
            st.stop()

    _skel.empty()
    st.toast(f"⚡ Study package ready — {topic}", icon=None)


# ─────────────────────────────────────────────────────────────────────────────
# RESULTS DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.study_result is not None:
    result     = st.session_state.study_result
    difficulty = st.session_state.study_difficulty

    st.divider()

    # ── Metric Tiles ─────────────────────────────────────────────────────────
    wc_research = len(result["research"].split())
    wc_notes    = len(result["notes"].split())
    q_count     = result["quiz"].count("**Q")
    elapsed     = result.get("elapsed_time", "—")

    _diff_mv = {"Easy": "mv-teal", "Medium": "mv-amber", "Hard": "mv-red"}
    _dv_cls  = _diff_mv.get(difficulty, "mv-cyan")

    st.markdown(
        f"""
        <div class="metric-row">
          <div class="metric-tile">
            <span class="metric-label">Research Words</span>
            <div class="metric-value mv-cyan count-up" data-target="{wc_research}">{wc_research:,}</div>
            <div class="metric-sub">raw intelligence</div>
          </div>
          <div class="metric-tile">
            <span class="metric-label">Notes Words</span>
            <div class="metric-value count-up" data-target="{wc_notes}">{wc_notes:,}</div>
            <div class="metric-sub">distilled output</div>
          </div>
          <div class="metric-tile">
            <span class="metric-label">Quiz Questions</span>
            <div class="metric-value mv-purple count-up" data-target="{q_count}">{q_count}</div>
            <div class="metric-sub">MCQs generated</div>
          </div>
          <div class="metric-tile">
            <span class="metric-label">Difficulty</span>
            <div class="metric-value {_dv_cls}" style="font-size:var(--ts-2xl);">{difficulty}</div>
            <div class="metric-sub">selected mode</div>
          </div>
          <div class="metric-tile">
            <span class="metric-label">Elapsed (s)</span>
            <div class="metric-value count-up" data-target="{elapsed}">{elapsed}</div>
            <div class="metric-sub">pipeline time</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Count-up JS
    st.iframe(
        """
        <script>
        (function(){
          function easeOutExpo(t){ return t===1?1:1-Math.pow(2,-10*t); }
          function animateCount(el, target, dur){
            var start=null, isFloat=String(target).includes('.');
            function step(ts){
              if(!start) start=ts;
              var p=Math.min((ts-start)/dur,1), v=easeOutExpo(p)*target;
              el.textContent=isFloat?v.toFixed(2):Math.round(v).toLocaleString();
              if(p<1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
          }
          function init(){
            var els=window.parent.document.querySelectorAll('.count-up[data-target]');
            els.forEach(function(el){
              var t=parseFloat(el.getAttribute('data-target'));
              if(!isNaN(t)) animateCount(el,t,820);
            });
          }
          setTimeout(init,120);
        })();
        </script>
        """,
        height=1,
    )

    # ── Tabbed Output Panels ──────────────────────────────────────────────────
    tab_notes, tab_quiz, tab_research = st.tabs(
        ["📝  Study Notes", "🧠  Interactive Quiz", "🔬  Raw Research"]
    )

    with tab_notes:
        st.markdown(
            """
            <div class="ds-card">
              <div class="ds-card-header">
                <div>
                  <div class="ds-card-title">Study Notes</div>
                  <div class="ds-card-meta">AI-distilled concepts from Research Agent output</div>
                </div>
                <span class="ds-card-tag">⬡ Summarizer Agent</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(format_study_notes(result["notes"]), unsafe_allow_html=True)

    with tab_quiz:
        _diff_label_mv = {"Easy": "mv-teal", "Medium": "mv-amber", "Hard": "mv-red"}
        st.markdown(
            f"""
            <div class="ds-card">
              <div class="ds-card-header">
                <div>
                  <div class="ds-card-title">Knowledge Check</div>
                  <div class="ds-card-meta">
                    {q_count} MCQ questions at
                    <span class="{_diff_label_mv.get(difficulty,'')}">{difficulty}</span>
                    difficulty
                  </div>
                </div>
                <span class="ds-card-tag">⬡ Quiz Agent</span>
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
            <div class="ds-card">
              <div class="ds-card-header">
                <div>
                  <div class="ds-card-title">Raw Intelligence Report</div>
                  <div class="ds-card-meta">Unabridged reference material from Research Agent</div>
                </div>
                <span class="ds-card-tag">⬡ Research Agent</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(result["research"])

    # Tab persistence
    _active = st.session_state.get("active_tab", 0)
    if _active != 0:
        st.iframe(
            f"""
            <script>
            (function(){{
              function _click(){{
                var tabs=window.parent.document.querySelectorAll('[data-baseweb="tab"]');
                if(tabs&&tabs.length>{_active}){{ tabs[{_active}].click(); }}
                else{{ setTimeout(_click,80); }}
              }}
              setTimeout(_click,80);
            }})();
            </script>
            """,
            height=1,
        )

    # ── Export ────────────────────────────────────────────────────────────────
    st.divider()
    st.markdown('<span class="section-label">Export Package</span>', unsafe_allow_html=True)

    dl1, dl2, _ = st.columns([2, 1.2, 2])

    full_output = (
        f"Nexus Agent Platform — Study Package\n{'='*60}\n"
        f"Topic      : {result['topic']}\nDifficulty : {difficulty}\n"
        f"Generated  : {time.strftime('%Y-%m-%d %H:%M')}\n{'='*60}\n\n"
        f"RESEARCH REPORT\n{'-'*40}\n{result['research']}\n\n"
        f"STUDY NOTES\n{'-'*40}\n{result['notes']}\n\n"
        f"QUIZ QUESTIONS\n{'-'*40}\n{result['quiz']}\n"
    )

    with dl1:
        st.download_button(
            label="⬇ Download Full Package (.txt)",
            data=full_output,
            file_name=f"{topic[:40].replace(' ','_')}_Nexus.txt",
            mime="text/plain", use_container_width=True,
        )
    with dl2:
        st.download_button(
            label="⬇ Notes Only",
            data=result["notes"],
            file_name=f"{topic[:40].replace(' ','_')}_notes.txt",
            mime="text/plain", use_container_width=True,
        )

    # st.markdown(
    #     '<span class="section-label" style="margin-top:var(--sp-4);display:block;">Share Session</span>',
    #     unsafe_allow_html=True,
    # )
    # st.code(f"?share_topic={urllib.parse.quote(result['topic'])}", language="text")


# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.study_result is None:
    SUGGESTIONS = [
        "Machine Learning Vectors", "Quantum Cryptography", "The Fall of Rome",
        "CRISPR Gene Editing", "Zero Knowledge Proofs", "Neural Networks",
        "Transformer Architecture", "French Revolution", "String Theory",
        "Macroeconomics", "Cognitive Behavioral Therapy", "Stoicism",
        "Dijkstra's Algorithm", "Black Holes", "Byzantine Fault Tolerance",
        "Reinforcement Learning", "Renaissance Art", "Plate Tectonics",
    ]

    def _set_random():
        chosen = random.choice(SUGGESTIONS)
        st.session_state.topic_widget_key  = chosen
        st.session_state.topic_input_state = chosen

    chips = "".join(
        f'<span class="topic-chip">{t}</span>' for t in (SUGGESTIONS + SUGGESTIONS)
    )
    st.markdown(
        f"""
        <div class="empty-state">
          <span class="empty-icon">⬡</span>
          <div class="empty-title">Enter a topic to begin</div>
          <div class="empty-sub">
            Type any academic or technical subject above. The three-agent pipeline will
            research, summarise, and generate an assessed quiz — fully automated.
          </div>
          <div class="marquee-wrap">
            <div class="marquee-track">{chips}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _c1, _c2, _c3 = st.columns([1, 1, 1])
    with _c2:
        st.button("🎲 Try a random topic", on_click=_set_random, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# FIXED STATUS BAR
# ─────────────────────────────────────────────────────────────────────────────
_ctx = ""
if st.session_state.study_result is not None:
    _r   = st.session_state.study_result
    _tok = (len(_r.get("research","")) + len(_r.get("notes","")) + len(_r.get("quiz",""))) // 4
    _ctx = f'<span class="sb-sep">&middot;</span> Context: ~{_tok:,} tokens'

st.markdown(
    f"""
    <div class="n-statusbar">
      <span class="sb-dot pulse"></span>
      Connected
      <span class="sb-sep">&middot;</span>
      3 Agents Active
      <span class="sb-sep">&middot;</span>
      Gemini 2.5 Flash Lite
      <span class="sb-sep">&middot;</span>
      {st.session_state.agent_run_count} pipeline run{'s' if st.session_state.agent_run_count != 1 else ''}
      {_ctx}
    </div>
    """,
    unsafe_allow_html=True,
)
import os
import re
import html
import json
import socket
import ipaddress
from pathlib import Path
from urllib.parse import urlparse, quote

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

from i18n import t, get_lang
from engine.analyzer import analyze_customers
from engine.scorer import score_prospects
from engine.intelligence import run_intelligence_pipeline

load_dotenv()

MAX_CSV_BYTES = 5 * 1024 * 1024  # 5 MB

st.set_page_config(page_title="ICP Identifier", page_icon="target", layout="wide")

# ── Language detection ──
# Priority: query param > Accept-Language header > default EN
if "_lang" not in st.session_state:
    lang_param = st.query_params.get("lang", None)
    if lang_param and lang_param in ("pt", "en"):
        st.session_state["_lang"] = lang_param
    else:
        # Auto-detect: only PT if Portuguese is the PRIMARY browser language
        try:
            accept_lang = st.context.headers.get("Accept-Language", "")
            # Accept-Language format: "pt-BR,pt;q=0.9,en;q=0.8" — first entry is primary
            primary = accept_lang.split(",")[0].strip().lower() if accept_lang else ""
            st.session_state["_lang"] = "pt" if primary.startswith("pt") else "en"
        except Exception:
            st.session_state["_lang"] = "en"

L = get_lang(st.session_state)


def _t(key, **kwargs):
    return t(key, L, **kwargs)


def _safe(val) -> str:
    """HTML-escape any value before injecting into unsafe_allow_html markup."""
    return html.escape(str(val))


def _validate_url(url: str) -> str | None:
    """Validate URL: must be http(s), no private/loopback IPs (SSRF protection)."""
    if not url:
        return None
    if not url.startswith("http"):
        url = "https://" + url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    hostname = parsed.hostname
    if not hostname:
        return None
    try:
        ip = socket.gethostbyname(hostname)
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local:
            return None
    except (socket.gaierror, ValueError):
        return None
    return url


def _validate_csv(uploaded_file) -> bool:
    """Validate CSV file size."""
    if uploaded_file is None:
        return False
    if uploaded_file.size > MAX_CSV_BYTES:
        st.error(_t("file_too_large", size=f"{uploaded_file.size / 1024 / 1024:.1f}"))
        return False
    return True

# ── Load cached companies ──
CACHE_DIR = Path("data/cache")
CACHED_COMPANIES = {}

def _country_tag(hq: str) -> str:
    """Derive country tag from headquarters string."""
    hq_lower = hq.lower()
    # Use word boundaries: ", SP" / ", SC" etc. to avoid matching "San Francisco"
    br_keywords = ["brazil", "brasil", "sao paulo", "jaragua"]
    br_states = [", sp", ", sc", ", rj", ", mg", ", pr", ", rs", ", ba", ", ce", ", pe"]
    if any(x in hq_lower for x in br_keywords) or any(hq_lower.endswith(x) or (x + ",") in hq_lower or (x + " ") in hq_lower for x in br_states):
        return "BR"
    if any(x in hq_lower for x in ["france", "paris", "bezons", "roubaix", "velizy"]):
        return "FR"
    if any(x in hq_lower for x in ["canada", "ontario", "ottawa", "toronto"]):
        return "CA"
    return "US"

if CACHE_DIR.exists():
    for f in sorted(CACHE_DIR.glob("*.json")):
        with open(f) as fh:
            data = json.load(fh)
        raw_dna = data.get("dna", {})
        # Handle bilingual cache: dna can be {"pt":{...},"en":{...}} or flat dict
        if "pt" in raw_dna and "en" in raw_dna:
            flat_dna = raw_dna.get("en", {})  # use EN for label (company names are the same)
        else:
            flat_dna = raw_dna
        name = flat_dna.get("company_name", f.stem.title())
        hq = flat_dna.get("headquarters", "")
        tag = _country_tag(hq)
        label = f"{name} ({tag})"
        CACHED_COMPANIES[label] = data

# ── Dark Theme CSS ──
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
    :root {
        --neu-bg: #0f1220;
        --neu-bg2: #0c0f1a;
        --neu-dark: #070910;
        --neu-light: #1a2035;
        --primary: #0000FF;
        --primary-dark: #0033CC;
    }

    *:not([class*="material"]):not([class*="icon"]):not([data-testid="stIconMaterial"]) {
        font-family: 'Inter', system-ui, sans-serif !important;
    }

    /* Global background */
    .stApp {
        background: var(--neu-bg2) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--neu-bg2) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--primary) !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* Hide streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Top Navbar (brunoseixas.com style) ── */
    .bs-navbar {
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 2.5rem;
        background: rgba(7,9,15,0.92);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        transition: all 0.35s ease;
    }
    .bs-navbar .bs-logo {
        font-size: 1rem;
        font-weight: 700;
        color: #ffffff;
        text-decoration: none;
        letter-spacing: -0.02em;
        display: flex;
        align-items: center;
        gap: 2px;
    }
    .bs-navbar .bs-logo .plus {
        color: var(--primary);
        font-weight: 800;
        margin-right: 2px;
    }
    .bs-navbar nav {
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    .bs-navbar nav a {
        font-size: 0.8rem;
        font-weight: 500;
        color: #8892a4;
        text-decoration: none;
        transition: color 0.2s ease;
        letter-spacing: 0.01em;
    }
    .bs-navbar nav a:hover {
        color: #ffffff;
    }
    .bs-navbar .bs-cta {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 20px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white !important;
        background: linear-gradient(135deg, #0000FF, #0033CC);
        border-radius: 50px;
        text-decoration: none;
        transition: all 0.2s ease;
    }
    .bs-navbar .bs-cta:hover {
        transform: translateY(-1px);
    }
    .bs-navbar .bs-lang {
        font-size: 0.65rem;
        color: #64748b;
        letter-spacing: 0.05em;
    }
    .bs-navbar .bs-lang span {
        cursor: pointer;
        transition: color 0.2s;
    }
    .bs-navbar .bs-lang span:hover,
    .bs-navbar .bs-lang span.active {
        color: var(--primary);
        font-weight: 600;
    }

    /* Push content below fixed navbar */
    .navbar-spacer { height: 20px; }

    /* ── Dark Surfaces (keep class names for compatibility) ── */
    .neu-raised {
        background: #0f1220;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
    }
    .neu-raised-sm {
        background: #0f1220;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
    }
    .neu-inset {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
    }

    /* ── Header ── */
    .header-container {
        text-align: center;
        padding: 2.5rem 0 2rem 0;
        margin-bottom: 1.5rem;
    }
    .header-pre-label {
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.25em;
        text-transform: uppercase;
        color: #8892a4;
        margin-bottom: 1rem;
    }
    .header-container h1 {
        font-size: clamp(3.5rem, 8vw, 6.5rem);
        font-weight: 900;
        color: #ffffff;
        letter-spacing: -0.04em;
        text-transform: uppercase;
        margin: 0;
        line-height: 1;
    }
    .header-container h1 .header-dot {
        color: #0000FF;
    }
    .header-accent-line {
        width: 56px;
        height: 3px;
        background: #0000FF;
        margin: 1.25rem auto 1.5rem auto;
        border-radius: 2px;
    }
    .header-container p {
        color: #8892a4;
        font-size: 1rem;
        margin: 0;
        letter-spacing: 0.01em;
    }

    /* ── Metric Cards ── */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .m-card {
        padding: 1.5rem;
        background: #0f1220;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        transition: transform 0.15s ease;
    }
    .m-card:hover {
        transform: translateY(-2px);
    }
    .m-card .m-label {
        color: #8892a4;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.5rem;
    }
    .m-card .m-value {
        color: #e8edf8;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .m-card .m-value.purple { color: var(--primary); }

    /* ── Section Titles ── */
    .s-header {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 20px;
        border-radius: 50px;
        background: #0f1220;
        border: 1px solid rgba(255,255,255,0.08);
        margin: 2rem 0 1.5rem 0;
        font-size: 0.7rem;
        font-weight: 600;
        color: #8892a4;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .s-header .s-icon {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: var(--primary);
    }

    /* ── Chart Explanation ── */
    .chart-explain {
        padding: 12px 16px;
        margin-top: 8px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        font-size: 0.78rem;
        color: #8892a4;
        line-height: 1.6;
    }
    .chart-explain strong {
        color: var(--primary);
        font-weight: 700;
    }
    .chart-explain .insight {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        margin-top: 6px;
    }
    .chart-explain .insight-dot {
        width: 5px; height: 5px;
        border-radius: 50%;
        background: var(--primary);
        flex-shrink: 0;
        margin-top: 7px;
    }

    /* ── ICP / Anti-ICP Cards ── */
    .icp-card {
        padding: 2rem;
        background: #0f1220;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        margin-bottom: 1.5rem;
    }
    .icp-card.positive {
        background: rgba(0,0,255,0.06);
        border: 1px solid rgba(0,0,255,0.4);
        box-shadow: 0 0 30px rgba(0,0,255,0.1);
    }
    .icp-card .card-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 1rem;
    }
    .icp-card.positive .card-badge {
        background: linear-gradient(135deg, #0000FF, #0033CC);
        color: white;
    }
    .icp-card.negative .card-badge {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
    }
    .icp-card h2 {
        color: #e8edf8;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0 0 0.75rem 0;
        letter-spacing: -0.02em;
    }
    .icp-card p {
        color: #8892a4;
        font-size: 0.9rem;
        line-height: 1.6;
        margin: 0;
    }

    /* ── Detail Items ── */
    .detail-group { margin-bottom: 1.25rem; }
    .dg-title {
        color: var(--primary);
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.75rem;
    }
    .detail-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        margin-bottom: 6px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        color: #cbd5e1;
        font-size: 0.85rem;
    }
    .detail-item .di-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: var(--primary);
        flex-shrink: 0;
    }

    /* ── Pattern Pills ── */
    .pattern-pill {
        display: inline-block;
        padding: 8px 14px;
        margin: 4px;
        background: linear-gradient(135deg, #0000FF, #0033CC);
        color: white;
        font-size: 0.75rem;
        font-weight: 500;
        border-radius: 50px;
    }

    /* ── Alert Items (Anti-ICP) ── */
    .alert-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 12px 14px;
        margin-bottom: 6px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        color: #cbd5e1;
        font-size: 0.85rem;
        line-height: 1.4;
    }
    .alert-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #ef4444;
        flex-shrink: 0;
        margin-top: 6px;
    }

    /* ── Score Rows ── */
    .score-row {
        display: flex;
        align-items: center;
        padding: 14px 18px;
        margin-bottom: 8px;
        background: #0f1220;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        transition: transform 0.15s ease;
    }
    .score-row:hover { transform: translateY(-1px); }
    .score-row .sr-name {
        flex: 1;
        color: #e8edf8;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .score-row .sr-score {
        font-size: 1.2rem;
        font-weight: 700;
        margin-right: 12px;
        font-variant-numeric: tabular-nums;
    }
    .sr-score.hot { color: var(--primary); }
    .sr-score.warm { color: #8892a4; }
    .sr-score.cold { color: #64748b; }
    .sr-score.avoid { color: #ef4444; }

    .sr-badge {
        padding: 4px 12px;
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        border-radius: 50px;
        color: white;
    }
    .sr-badge.hot { background: linear-gradient(135deg, #0000FF, #0033CC); }
    .sr-badge.warm { background: linear-gradient(135deg, #f59e0b, #d97706); }
    .sr-badge.cold { background: linear-gradient(135deg, #9ca3af, #6b7280); }
    .sr-badge.avoid { background: linear-gradient(135deg, #ef4444, #dc2626); }

    /* ── Pills (sidebar selectors) ── */
    [data-testid="stSidebar"] [data-testid="stPills"] [role="tablist"] {
        gap: 6px !important;
    }
    [data-testid="stSidebar"] [data-testid="stPills"] button[role="tab"] {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        font-size: 0.72rem !important;
        font-weight: 500 !important;
        color: #8892a4 !important;
        padding: 8px 14px !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] [data-testid="stPills"] button[role="tab"]:hover {
        transform: translateY(-1px) !important;
        color: #e8edf8 !important;
    }
    [data-testid="stSidebar"] [data-testid="stPills"] button[role="tab"][aria-selected="true"] {
        background: #0000FF !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stPills"] label {
        font-size: 0.65rem !important;
        font-weight: 600 !important;
        color: var(--primary) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
    }

    /* ── Button Override ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0000FF, #0033CC) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(1px) !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        border-radius: 16px !important;
    }
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        font-size: 0.75rem !important;
        overflow: visible !important;
        white-space: nowrap !important;
    }
    [data-testid="stSidebar"] .streamlit-expanderHeader p {
        font-size: 0.75rem !important;
        overflow: visible !important;
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        background: var(--neu-bg2);
    }
    .empty-icon {
        width: 64px; height: 64px;
        margin: 0 auto 1.5rem auto;
        border-radius: 20px;
        background: #0f1220;
        border: 1px solid rgba(255,255,255,0.08);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }

    /* Spinner */
    .stSpinner > div > div {
        border-top-color: var(--primary) !important;
    }

    /* ── Company Profile Card ── */
    .company-card {
        padding: 2rem;
        background: #0f1220;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        margin-bottom: 1.5rem;
    }
    .company-card .cc-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1rem;
    }
    .company-card .cc-icon {
        width: 48px; height: 48px;
        border-radius: 16px;
        background: linear-gradient(135deg, #0000FF, #0033CC);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.25rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .company-card .cc-name {
        font-size: 1.25rem;
        font-weight: 700;
        color: #e8edf8;
        letter-spacing: -0.02em;
    }
    .company-card .cc-industry {
        font-size: 0.75rem;
        color: var(--primary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .company-card .cc-desc {
        color: #8892a4;
        font-size: 0.9rem;
        line-height: 1.6;
        margin-bottom: 1.25rem;
    }
    .cc-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }
    .cc-section-title {
        color: var(--primary);
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }
    .cc-tag {
        display: inline-block;
        padding: 5px 12px;
        margin: 3px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 50px;
        font-size: 0.75rem;
        color: #cbd5e1;
    }
    .cc-tag.purple {
        background: linear-gradient(135deg, #0000FF, #0033CC);
        border: none;
        color: white;
    }
    .cc-list-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 6px 0;
        font-size: 0.8rem;
        color: #cbd5e1;
        line-height: 1.4;
    }
    .cc-list-item .cc-bullet {
        width: 5px; height: 5px;
        border-radius: 50%;
        background: var(--primary);
        flex-shrink: 0;
        margin-top: 6px;
    }

    /* ── Pipeline Progress ── */
    .pipeline-container {
        padding: 2rem;
        background: #0f1220;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        margin-bottom: 1.5rem;
    }
    .pipeline-title {
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--primary);
        margin-bottom: 1.25rem;
    }
    .phase-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .phase-row:last-child { border-bottom: none; }
    .phase-num {
        width: 28px; height: 28px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.7rem; font-weight: 700;
        flex-shrink: 0;
    }
    .phase-num.done {
        background: linear-gradient(135deg, #0000FF, #0033CC);
        color: white;
    }
    .phase-num.active {
        background: rgba(0,0,255,0.15);
        border: 1px solid rgba(0,0,255,0.5);
        color: #0000FF;
        animation: pulse-phase 1.5s ease-in-out infinite;
    }
    .phase-num.pending {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        color: #4a5568;
    }
    @keyframes pulse-phase {
        0%, 100% { box-shadow: 0 0 0 0 rgba(0,0,255,0.2); }
        50% { box-shadow: 0 0 12px rgba(0,0,255,0.4); }
    }
    .phase-info { flex: 1; }
    .phase-name {
        font-size: 0.8rem;
        font-weight: 600;
        color: #e8edf8;
    }
    .phase-status {
        font-size: 0.7rem;
        color: #64748b;
        margin-top: 2px;
    }
    .phase-status.done { color: #22c55e; }

    /* ── Dossier Card ── */
    .dossier-card {
        padding: 1.25rem 1.5rem;
        background: #0f1220;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1rem;
        transition: transform 0.15s;
    }
    .dossier-card:hover { transform: translateY(-1px); }
    .dossier-icon {
        width: 40px; height: 40px;
        border-radius: 12px;
        background: linear-gradient(135deg, #0000FF, #0033CC);
        display: flex; align-items: center; justify-content: center;
        color: white; font-size: 1.1rem; flex-shrink: 0;
    }
    .dossier-info .dossier-name {
        font-size: 0.85rem; font-weight: 600; color: #e8edf8;
    }
    .dossier-info .dossier-meta {
        font-size: 0.7rem; color: #64748b; margin-top: 2px;
    }

    /* ── Instant Load Badge ── */
    .instant-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 50px;
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: white;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.75rem;
    }

    /* ── Health Matrix ── */
    .health-cell {
        padding: 10px 14px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        text-align: center;
        margin: 4px;
    }
    .health-good {
        background: rgba(0,0,255,0.12);
        color: #6699ff;
    }
    .health-bad {
        background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05));
        color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)


# ── Header ──
st.markdown(f"""
<div class="header-container">
    <div class="header-pre-label">ICP Tool</div>
    <h1>{_t("header_title")}<span class="header-dot">.</span></h1>
    <div class="header-accent-line"></div>
    <p>{_t("header_subtitle")}</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──
api_key = os.getenv("GROQ_API_KEY", "")

with st.sidebar:
    # ── Language toggle (pills) ──
    _lang_map = {"🇧🇷 PT-BR": "pt", "🇺🇸 EN": "en"}
    _lang_default = "🇧🇷 PT-BR" if L == "pt" else "🇺🇸 EN"
    _lang_pick = st.pills(
        _t("language"), options=list(_lang_map.keys()),
        default=_lang_default, key="lang_pills",
    )
    if _lang_pick and _lang_map[_lang_pick] != L:
        st.session_state["_lang"] = _lang_map[_lang_pick]
        st.query_params["lang"] = _lang_map[_lang_pick]
        st.rerun()

    st.markdown(f"### {_t('data_source')}")

    # ── Data source toggle (pills) ──
    if "_data_source" not in st.session_state:
        st.session_state["_data_source"] = "preloaded"

    _ds_map = {
        f"📦 {_t('preloaded_company')}": "preloaded",
        f"🔍 {_t('research_new')}": "research",
        f"📄 {_t('upload_csv')}": "csv",
    }
    _ds_reverse = {v: k for k, v in _ds_map.items()}
    _ds_default = _ds_reverse[st.session_state["_data_source"]]
    _ds_pick = st.pills(
        "", options=list(_ds_map.keys()),
        default=_ds_default, key="ds_pills",
    )
    if _ds_pick:
        new_ds = _ds_map[_ds_pick]
        if new_ds != st.session_state["_data_source"]:
            st.session_state["_data_source"] = new_ds
            st.rerun()

    data_source_key = st.session_state["_data_source"]

    # ── Option 1: Pre-loaded cache ──
    selected_cached = _t("select_placeholder")
    company_url = ""
    research_btn = False
    customers_file = None
    use_sample = False
    prospects_file = None

    if data_source_key == "preloaded":
        cached_labels = list(CACHED_COMPANIES.keys())
        selected_cached = st.selectbox(
            _t("instant_loading"),
            options=[_t("select_placeholder")] + cached_labels,
            key="cached_select",
            help=_t("instant_help"),
        )

        if selected_cached != _t("select_placeholder"):
            cache_data = CACHED_COMPANIES[selected_cached]
            if st.session_state.get("_loaded_cache") != selected_cached or st.session_state.get("_loaded_lang") != L:
                for key in ["icp", "scored"]:
                    st.session_state.pop(key, None)
                # Support bilingual cache: dna/market can be {"pt":{...},"en":{...}} or flat dict
                raw_dna = cache_data["dna"]
                raw_market = cache_data["market"]
                st.session_state["intel_dna"] = raw_dna.get(L, raw_dna) if "pt" in raw_dna and "en" in raw_dna else raw_dna
                st.session_state["intel_market"] = raw_market.get(L, raw_market) if "pt" in raw_market and "en" in raw_market else raw_market
                clients_df = pd.DataFrame(cache_data["clients"])
                clients_df["churned"] = clients_df["churned"].apply(
                    lambda x: str(x).strip().lower() in ("true", "1", "yes")
                )
                st.session_state["generated_clients"] = clients_df
                st.session_state["intel_dossier"] = ""
                st.session_state["intel_dossier_path"] = ""
                st.session_state["company_source"] = None
                st.session_state["_loaded_cache"] = selected_cached
                st.session_state["_loaded_lang"] = L

            st.markdown(f"""
            <div class="instant-badge">{_t("preloaded_data")}</div>
            <div style="padding:10px 12px; border-radius:12px;
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.06);
                font-size:0.75rem; color:#cbd5e1; line-height:1.6;">
                <strong style="color:#0000FF;">{selected_cached}</strong><br>
                DNA + {'Mercado' if L == 'pt' else 'Market'} + {len(cache_data['clients'])} {_t("customers").lower()}<br>
                <span style="color:#64748b; font-size:0.65rem;">{_t("source_cache")}</span>
            </div>
            <div style="margin-top:8px;padding:8px 12px;border-radius:10px;
                background:rgba(245,158,11,0.08);border-left:3px solid #f59e0b;
                font-size:0.68rem;color:#92400e;line-height:1.5;">
                ⚠️ {_t("demo_data_disclaimer")}
            </div>
            """, unsafe_allow_html=True)

    # ── Option 2: Research new company ──
    elif data_source_key == "research":
        company_url = st.text_input(_t("type_url"), placeholder=_t("url_placeholder"))

        # Validate URL for SSRF
        if company_url:
            validated = _validate_url(company_url)
            if not validated:
                st.warning(_t("url_invalid"))
                company_url = ""
            else:
                company_url = validated

        research_btn = st.button(_t("research_btn"), type="primary", use_container_width=True, key="research")

    # ── Option 3: Upload CSV ──
    elif data_source_key == "csv":
        # Template download
        _tpl_customers = Path("data/template_customers.csv")
        if _tpl_customers.exists():
            st.download_button(
                label=_t("download_template_customers"),
                data=_tpl_customers.read_bytes(),
                file_name="icp_customers_template.csv",
                mime="text/csv",
                use_container_width=True,
            )
        customers_file_raw = st.file_uploader(_t("upload_customers"), type=["csv"], key="customers")
        if customers_file_raw and not _validate_csv(customers_file_raw):
            customers_file_raw = None
        customers_file = customers_file_raw
        use_sample = st.checkbox(_t("use_sample"), value=False)

    st.markdown("---")
    st.markdown(f"### {_t('prospects_label')}")
    # Prospects template download
    _tpl_prospects = Path("data/template_prospects.csv")
    if _tpl_prospects.exists():
        st.download_button(
            label=_t("download_template_prospects"),
            data=_tpl_prospects.read_bytes(),
            file_name="icp_prospects_template.csv",
            mime="text/csv",
            use_container_width=True,
        )
    prospects_file_raw = st.file_uploader(_t("upload_prospects"), type=["csv"], key="prospects")
    if prospects_file_raw and not _validate_csv(prospects_file_raw):
        prospects_file_raw = None
    prospects_file = prospects_file_raw

    # ── Security info ──
    st.markdown("---")
    with st.expander(_t('security_badge'), expanded=False, icon="🔒"):
        st.markdown(f"""
        <div style="font-size:0.78rem;color:#cbd5e1;line-height:1.7;">
            <div style="font-weight:700;color:var(--primary);font-size:0.8rem;margin-bottom:8px;">{_t("security_title")}</div>
            <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
                <span style="color:#22c55e;font-size:0.9rem;">✓</span>
                <span>{_t("security_no_storage")}</span>
            </div>
            <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
                <span style="color:#22c55e;font-size:0.9rem;">✓</span>
                <span>{_t("security_no_logs")}</span>
            </div>
            <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
                <span style="color:#22c55e;font-size:0.9rem;">✓</span>
                <span>{_t("security_ssrf")}</span>
            </div>
            <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
                <span style="color:#22c55e;font-size:0.9rem;">✓</span>
                <span>{_t("security_xss")}</span>
            </div>
            <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
                <span style="color:#22c55e;font-size:0.9rem;">✓</span>
                <span>{_t("security_csv_limit")}</span>
            </div>
            <div style="display:flex;align-items:flex-start;gap:8px;">
                <span style="color:#22c55e;font-size:0.9rem;">✓</span>
                <span>{_t("security_session")}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Company Research ──
# ── Intelligence Pipeline ──
PHASE_NAMES = {
    1: _t("phase_1"),
    2: _t("phase_2"),
    3: _t("phase_3"),
    4: _t("phase_4"),
    5: _t("phase_5"),
}

if research_btn and company_url:
    if not api_key:
        st.error(_t("configure_api"))
    else:
        # Clear previous state
        for key in ["icp", "scored", "generated_clients", "intel_dna", "intel_market", "intel_dossier", "intel_dossier_path", "_loaded_cache"]:
            st.session_state.pop(key, None)

        # Progress UI
        progress_placeholder = st.empty()
        phases_status = {i: ("pending", "") for i in range(1, 6)}

        def render_progress(phases):
            rows = ""
            for i in range(1, 6):
                state, msg = phases[i]
                rows += f"""
                <div class="phase-row">
                    <div class="phase-num {state}">{i}</div>
                    <div class="phase-info">
                        <div class="phase-name">{PHASE_NAMES[i]}</div>
                        <div class="phase-status {state}">{msg}</div>
                    </div>
                </div>"""
            return f'<div class="pipeline-container"><div class="pipeline-title">{_t("pipeline_title")}</div>{rows}</div>'

        def on_progress(phase, name, status):
            # Mark previous phases as done
            for i in range(1, phase):
                if phases_status[i][0] != "done":
                    phases_status[i] = ("done", phases_status[i][1])
            phases_status[phase] = ("active", status)
            progress_placeholder.markdown(render_progress(phases_status), unsafe_allow_html=True)

        try:
            dna, market, gen_df, dossier_path, dossier_md = run_intelligence_pipeline(
                company_url, api_key, progress_callback=on_progress
            )
            # Mark all done
            for i in range(1, 6):
                phases_status[i] = ("done", phases_status[i][1])
            progress_placeholder.markdown(render_progress(phases_status), unsafe_allow_html=True)

            # Store in session
            st.session_state["intel_dna"] = dna
            st.session_state["intel_market"] = market
            st.session_state["generated_clients"] = gen_df
            st.session_state["intel_dossier"] = dossier_md
            st.session_state["intel_dossier_path"] = dossier_path
            st.session_state["company_source"] = None

        except Exception as e:
            st.error(_t("pipeline_error", e=e))

# ── Show Results ──
if "intel_dna" in st.session_state:
    dna = st.session_state["intel_dna"]
    market = st.session_state["intel_market"]
    dossier_md = st.session_state.get("intel_dossier", "")
    dossier_path = st.session_state.get("intel_dossier_path", "")

    name = dna.get("company_name", "Empresa")
    initial = name[0].upper() if name else "?"

    # Source
    source_obj = st.session_state.get("company_source")
    if source_obj and source_obj.get("source"):
        source_text = source_obj["source"]
    else:
        source_text = _t("scrape_source")

    # Build tag helpers
    def tags(items, cls="cc-tag"):
        return "".join(f'<span class="{cls}">{i}</span>' for i in (items or []))

    def bullets(items):
        return "".join(f'<div class="cc-list-item"><div class="cc-bullet"></div>{i}</div>' for i in (items or []))

    # ── Company DNA Card (split into smaller chunks to avoid Streamlit HTML truncation) ──
    products_html = tags(dna.get('products', [])[:8])
    tech_html = tags(dna.get('technologies', [])[:6])
    segments_html = tags(dna.get('target_segments', [])[:6])
    social_html = bullets(dna.get('social_proof', [])[:5])
    partners_html = bullets(dna.get('partnerships', [])[:5])

    hq = dna.get('headquarters', '')
    size_signals = dna.get('company_size_signals', '')
    founded = dna.get('founded_year', '')

    # Build meta line: HQ · Founded · Size signals
    meta_parts = []
    if hq:
        meta_parts.append(f"📍 {_safe(hq)}")
    if founded and str(founded) != "unknown":
        meta_parts.append(f"{_t('founded')} {_safe(founded)}")
    meta_line = " · ".join(meta_parts)

    st.markdown(f"""
    <div class="company-card">
        <div class="cc-header">
            <div class="cc-icon">{initial}</div>
            <div style="flex:1;">
                <div class="cc-name">{name}</div>
                <div class="cc-industry">{dna.get('industry', '')} · {dna.get('business_model', '')}</div>
                <div style="font-size:0.75rem;color:#8892a4;margin-top:4px;">{meta_line}</div>
            </div>
        </div>
        <div style="padding:10px 16px;margin:12px 0;background:rgba(255,255,255,0.03);
            border:1px solid rgba(255,255,255,0.06);
            border-radius:12px;font-size:0.78rem;color:#cbd5e1;line-height:1.6;">
            <span style="font-weight:600;color:var(--primary);font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;">{_t('company_size')}</span><br>
            {_safe(size_signals)}
        </div>
        <div class="cc-desc">{dna.get('description', '')}</div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="cc-grid">
            <div>
                <div class="cc-section-title">{_t("products_services")}</div>
                {products_html}
            </div>
            <div>
                <div class="cc-section-title">{_t("technologies")}</div>
                {tech_html}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="margin-top: 1rem;">
            <div class="cc-section-title">{_t("target_segments")}</div>
            {segments_html}
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="cc-grid" style="margin-top: 1rem;">
            <div>
                <div class="cc-section-title">{_t("social_proof")}</div>
                {social_html}
            </div>
            <div>
                <div class="cc-section-title">{_t("partnerships")}</div>
                {partners_html}
            </div>
        </div>
        <div style="margin-top:1rem; padding-top:0.75rem; border-top:1px solid rgba(255,255,255,0.06);">
            <div style="font-size:0.7rem; color:#64748b;">Fonte: {source_text}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Market Intel Card ──
    st.markdown(f'<div class="s-header"><div class="s-icon"></div>{_t("market_intel_title")}</div>', unsafe_allow_html=True)

    col_market1, col_market2 = st.columns(2)

    with col_market1:
        st.markdown(f"""
        <div class="company-card">
            <div class="cc-section-title">{_t("competitors_mapped")}</div>
            {bullets(market.get('likely_competitors', [])[:6])}
            <div class="cc-section-title" style="margin-top:1rem;">{_t("buying_triggers")}</div>
            {bullets(market.get('buying_triggers', [])[:5])}
            <div class="cc-section-title" style="margin-top:1rem;">{_t("typical_decision_makers")}</div>
            {tags(market.get('decision_makers', [])[:6])}
        </div>
        """, unsafe_allow_html=True)

    with col_market2:
        st.markdown(f"""
        <div class="company-card">
            <div class="cc-section-title">{_t("ideal_customer_chars")}</div>
            {bullets(market.get('ideal_customer_characteristics', [])[:7])}
            <div class="cc-section-title" style="margin-top:1rem;">{_t("anti_icp_signals_title")}</div>
            {bullets(market.get('anti_icp_signals', [])[:5])}
        </div>
        """, unsafe_allow_html=True)

    # ── Dossier Download (only if available) ──
    if dossier_md:
        st.markdown(f"""
        <div class="dossier-card">
            <div class="dossier-icon">D</div>
            <div class="dossier-info">
                <div class="dossier-name">{_t("dossier_title", name=name)}</div>
                <div class="dossier-meta">{_t("dossier_available")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label=_t("download_dossier"),
            data=dossier_md,
            file_name=f"{name.replace(' ', '_')}_dossier.md",
            mime="text/markdown",
        )

# ── Load Data ──
df = None
if customers_file:
    df = pd.read_csv(customers_file)
    df["churned"] = df["churned"].apply(lambda x: str(x).lower() in ("true", "1", "yes", "sim"))
elif "generated_clients" in st.session_state:
    df = st.session_state["generated_clients"]
elif use_sample:
    df = pd.read_csv("data/sample.csv")
    df["churned"] = df["churned"].apply(lambda x: str(x).lower() in ("true", "1", "yes", "sim"))

if df is not None:
    # ── Detect optional columns ──
    has_nps = "nps_score" in df.columns and df["nps_score"].notna().any()

    # ── Metrics ──
    churn_rate = df["churned"].mean() * 100
    avg_ltv = df["ltv_usd"].mean()
    avg_nps = df["nps_score"].mean() if has_nps else None
    avg_cycle = df["sales_cycle_days"].mean()
    active = len(df[~df["churned"]])
    total_revenue = df["annual_revenue_usd"].sum()
    avg_deal = df["deal_size_usd"].mean()

    st.markdown(f"""
    <div class="metrics-grid">
        <div class="m-card">
            <div class="m-label">{_t("customers")}</div>
            <div class="m-value">{len(df)}</div>
        </div>
        <div class="m-card">
            <div class="m-label">{_t("active")}</div>
            <div class="m-value purple">{active}</div>
        </div>
        <div class="m-card">
            <div class="m-label">{_t("churn_rate")}</div>
            <div class="m-value">{churn_rate:.0f}%</div>
        </div>
        <div class="m-card">
            <div class="m-label">{_t("avg_ltv")}</div>
            <div class="m-value">${avg_ltv:,.0f}</div>
        </div>
        {f'<div class="m-card"><div class="m-label">NPS</div><div class="m-value purple">{avg_nps:.1f}</div></div>' if has_nps else ''}
        <div class="m-card">
            <div class="m-label">{_t("avg_cycle")}</div>
            <div class="m-value">{avg_cycle:.0f}d</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Shared chart layout ──
    neu_chart_layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#8892a4", size=11),
        title_font=dict(family="Inter", color="#e8edf8", size=13),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.08)",
            tickcolor="rgba(255,255,255,0.08)",
            zerolinecolor="rgba(255,255,255,0.05)",
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.08)",
            tickcolor="rgba(255,255,255,0.08)",
            zerolinecolor="rgba(255,255,255,0.05)",
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8892a4")),
        margin=dict(l=20, r=20, t=40, b=20),
        hoverlabel=dict(bgcolor="#0f1220", bordercolor="rgba(255,255,255,0.12)", font=dict(color="#e8edf8")),
    )
    colors_churn = {True: "#ef4444", False: "#3366ff"}

    # ══════════════════════════════════════════════════════
    # PRE-COMPUTE shared data for all tabs
    # ══════════════════════════════════════════════════════
    def classify_tech(tech_str):
        tech = str(tech_str).lower()
        if any(t in tech for t in ["cloud", "aws", "azure", "gcp", "saas", "kubernetes"]):
            return "Cloud/Moderno"
        elif any(t in tech for t in ["legacy", "on-premise", "excel", "planilha", "caderno", "nenhum", "whatsapp", "proprio"]):
            return "Legacy/Manual"
        return "Hibrido"

    df["tech_class"] = df["tech_stack"].apply(classify_tech)

    def revenue_band(rev):
        if rev < 5_000_000:
            return "< $5M"
        elif rev < 20_000_000:
            return "$5M-$20M"
        elif rev < 50_000_000:
            return "$20M-$50M"
        elif rev < 100_000_000:
            return "$50M-$100M"
        else:
            return "> $100M"

    band_order = ["< $5M", "$5M-$20M", "$20M-$50M", "$50M-$100M", "> $100M"]
    df["revenue_band"] = pd.Categorical(df["annual_revenue_usd"].apply(revenue_band), categories=band_order, ordered=True)
    df["company_age"] = 2025 - df["founding_year"]

    # ── ICP TIER SCORING ──
    # When NPS is available: NPS(30%) + Churn(25%) + Tech(15%) + Cycle(15%) + ROI(15%) = 100
    # Without NPS: Churn(36%) + Tech(21%) + Cycle(21%) + ROI(21%) = 100 (proportionally rescaled)
    # Based on Gartner/Inverta ICP Segmentation frameworks
    def compute_icp_score(row):
        nps_pts = 0
        if has_nps and pd.notna(row.get("nps_score")):
            nps_pts = min(row["nps_score"] / 10 * 30, 30)
        # Churn (0-25 pts)
        churn_pts = 0 if row["churned"] else 25
        # Tech maturity (0-15 pts)
        tc = row.get("tech_class", "Hibrido")
        tech_pts = 15 if tc == "Cloud/Moderno" else (7 if tc == "Hibrido" else 0)
        # Sales cycle efficiency (0-15 pts) — shorter = better
        cycle = row["sales_cycle_days"]
        cycle_pts = 15 if cycle <= 30 else (10 if cycle <= 50 else (5 if cycle <= 70 else 0))
        # ROI / LTV-to-deal ratio (0-15 pts)
        roi = row["ltv_usd"] / row["deal_size_usd"] if row["deal_size_usd"] > 0 else 0
        roi_pts = 15 if roi >= 5 else (10 if roi >= 3 else (5 if roi >= 1.5 else 0))

        if has_nps:
            return round(nps_pts + churn_pts + tech_pts + cycle_pts + roi_pts, 1)
        else:
            # Normalize to 100 without NPS (max possible = 70)
            raw = churn_pts + tech_pts + cycle_pts + roi_pts
            return round(raw / 70 * 100, 1)

    df["icp_score"] = df.apply(compute_icp_score, axis=1)

    # Assign tiers based on score distribution (Gartner/DataBees model)
    def assign_tier(score):
        if score >= 85:
            return "Tier 1"
        elif score >= 65:
            return "Tier 2"
        elif score >= 40:
            return "Tier 3"
        else:
            return "Tier 4"

    df["icp_tier"] = df["icp_score"].apply(assign_tier)

    TIER_COLORS = {
        "Tier 1": "#0000FF",
        "Tier 2": "#3b82f6",
        "Tier 3": "#f59e0b",
        "Tier 4": "#ef4444",
    }
    TIER_LABELS = {
        "Tier 1": _t("tier_ideal"),
        "Tier 2": _t("tier_good"),
        "Tier 3": _t("tier_risky"),
        "Tier 4": _t("tier_avoid"),
    }

    active_ltv = df[~df["churned"]]["ltv_usd"].mean()
    churned_ltv = df[df["churned"]]["ltv_usd"].mean()
    ltv_ratio = active_ltv / churned_ltv if churned_ltv > 0 else 0
    avg_roi_active = (df[~df["churned"]]["ltv_usd"] / df[~df["churned"]]["deal_size_usd"]).mean()
    avg_roi_churned = (df[df["churned"]]["ltv_usd"] / df[df["churned"]]["deal_size_usd"]).mean()
    cloud_churn = df[df["tech_class"] == "Cloud/Moderno"]["churned"].mean() * 100
    legacy_churn = df[df["tech_class"] == "Legacy/Manual"]["churned"].mean() * 100
    cloud_nps = df[df["tech_class"] == "Cloud/Moderno"]["nps_score"].mean() if has_nps else None
    legacy_nps = df[df["tech_class"] == "Legacy/Manual"]["nps_score"].mean() if has_nps else None
    active_age = df[~df["churned"]]["company_age"].mean()
    churned_age = df[df["churned"]]["company_age"].mean()
    active_size = df[~df["churned"]]["employee_count"].mean()
    churned_size = df[df["churned"]]["employee_count"].mean()
    best_industry = df[~df["churned"]].groupby("industry")["ltv_usd"].mean().idxmax()
    worst_churn_industry = df.groupby("industry")["churned"].mean().idxmax()
    promoters = len(df[df["nps_score"] >= 9]) if has_nps else 0
    detractors = len(df[df["nps_score"] <= 6]) if has_nps else 0
    nps_net = int(((promoters - detractors) / len(df)) * 100) if has_nps else None

    _cohort_agg = {"total": ("company_name", "count"), "churned_count": ("churned", "sum"),
                   "avg_ltv": ("ltv_usd", "mean"), "avg_deal": ("deal_size_usd", "mean")}
    if has_nps:
        _cohort_agg["avg_nps"] = ("nps_score", "mean")
    cohort = df.groupby("revenue_band", observed=True).agg(**_cohort_agg).reset_index()
    if not has_nps:
        cohort["avg_nps"] = None
    cohort["retention_rate"] = ((cohort["total"] - cohort["churned_count"]) / cohort["total"] * 100)
    best_cohort = cohort.loc[cohort["avg_ltv"].idxmax()]

    # ══════════════════════════════════════════════════════
    # TABBED CHART NAVIGATION
    # ══════════════════════════════════════════════════════
    st.markdown(f'<div class="s-header"><div class="s-icon"></div>{_t("visual_analysis")}</div>', unsafe_allow_html=True)

    tab_tiers, tab_health, tab_finance, tab_segment, tab_risk, tab_summary = st.tabs([
        _t("tab_tiers"),
        _t("tab_health"),
        _t("tab_finance"),
        _t("tab_segment"),
        _t("tab_risk"),
        _t("tab_summary"),
    ])

    # ── TAB 0: ICP TIERS ──
    with tab_tiers:
        # Tier summary metrics
        _tier_agg = {"count": ("company_name", "count"), "avg_ltv": ("ltv_usd", "mean"),
                     "avg_deal": ("deal_size_usd", "mean"), "avg_cycle": ("sales_cycle_days", "mean"),
                     "avg_score": ("icp_score", "mean"), "churn_rate": ("churned", "mean"),
                     "avg_revenue": ("annual_revenue_usd", "mean"), "avg_employees": ("employee_count", "mean")}
        if has_nps:
            _tier_agg["avg_nps"] = ("nps_score", "mean")
        tier_summary = df.groupby("icp_tier").agg(**_tier_agg).reset_index()
        if not has_nps:
            tier_summary["avg_nps"] = None
        tier_summary["churn_rate"] = tier_summary["churn_rate"] * 100
        tier_summary = tier_summary.sort_values("avg_score", ascending=False)

        # Tier cards row — one st.markdown per card to avoid truncation
        tier_cols = st.columns(len(tier_summary))
        for idx, (_, trow) in enumerate(tier_summary.iterrows()):
            tier = trow["icp_tier"]
            color = TIER_COLORS[tier]
            label = TIER_LABELS[tier]
            pct = trow["count"] / len(df) * 100
            with tier_cols[idx]:
                st.markdown(f"""
                <div class="m-card" style="border-left: 4px solid {color};">
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                        <div style="width:10px; height:10px; border-radius:50%; background:{color};"></div>
                        <span style="font-size:0.65rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:{color};">{tier} — {label}</span>
                    </div>
                    <div class="m-value" style="color:{color};">{int(trow['count'])}</div>
                    <div class="m-label">{pct:.0f}% {_t("of_base")}</div>
                    <div style="margin-top:8px; font-size:0.7rem; color:#8892a4; line-height:1.6;">
                        Score: {trow['avg_score']:.0f}/100<br>
                        LTV: ${trow['avg_ltv']:,.0f}<br>
                        {f"NPS: {trow['avg_nps']:.1f} · " if has_nps and trow['avg_nps'] is not None else ""}Churn: {trow['churn_rate']:.0f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

        tt_col1, tt_col2 = st.columns(2)

        with tt_col1:
            # Tier distribution donut
            tier_counts = df["icp_tier"].value_counts().reindex(["Tier 1", "Tier 2", "Tier 3", "Tier 4"]).fillna(0)
            fig_tier_donut = go.Figure(go.Pie(
                labels=[f"{t} — {TIER_LABELS[t]}" for t in tier_counts.index],
                values=tier_counts.values,
                hole=0.55,
                marker=dict(colors=[TIER_COLORS[t] for t in tier_counts.index]),
                textinfo="label+percent",
                textposition="outside",
                textfont=dict(size=11),
            ))
            fig_tier_donut.update_layout(
                title=_t("tier_distribution"),
                height=420,
                showlegend=False,
                **neu_chart_layout,
            )
            fig_tier_donut.add_annotation(
                text=f"<b>{len(df)}</b><br>{_t('customers').lower()}",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color="#e8edf8", family="Inter"),
            )
            st.plotly_chart(fig_tier_donut, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                {_t("tier_how_calculated")}
                <div class="insight"><div class="insight-dot"></div>{_t("tier_dim_nps")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("tier_dim_retention")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("tier_dim_tech")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("tier_dim_cycle")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("tier_dim_roi")}</div>
            </div>
            """, unsafe_allow_html=True)

        with tt_col2:
            # Tier comparison radar
            tier_radar_data = tier_summary.copy()
            # Normalize metrics to 0-10 for radar
            max_ltv = tier_radar_data["avg_ltv"].max() or 1
            max_deal = tier_radar_data["avg_deal"].max() or 1
            max_rev = tier_radar_data["avg_revenue"].max() or 1

            fig_radar = go.Figure()
            if has_nps:
                categories = ["NPS", _t("retention_pct"), _t("ltv_norm"), _t("deal_size_norm"), _t("cycle_speed")]
            else:
                categories = [_t("retention_pct"), _t("ltv_norm"), _t("deal_size_norm"), _t("cycle_speed")]

            for _, trow in tier_radar_data.iterrows():
                tier = trow["icp_tier"]
                retention = 100 - trow["churn_rate"]
                cycle_speed = max(0, 10 - (trow["avg_cycle"] / 10))  # invert: faster = higher
                if has_nps:
                    values = [trow["avg_nps"], retention / 10, trow["avg_ltv"] / max_ltv * 10,
                              trow["avg_deal"] / max_deal * 10, cycle_speed]
                else:
                    values = [retention / 10, trow["avg_ltv"] / max_ltv * 10,
                              trow["avg_deal"] / max_deal * 10, cycle_speed]
                fig_radar.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    name=f"{tier} — {TIER_LABELS[tier]}",
                    line=dict(color=TIER_COLORS[tier], width=2),
                    fillcolor={"Tier 1": "rgba(124,58,237,0.1)", "Tier 2": "rgba(59,130,246,0.1)", "Tier 3": "rgba(245,158,11,0.1)", "Tier 4": "rgba(239,68,68,0.1)"}[tier],
                ))

            fig_radar.update_layout(
                title=_t("tier_comparison_radar"),
                height=420,
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 10], gridcolor="rgba(255,255,255,0.05)"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#8892a4", size=11),
                title_font=dict(size=13, color="#e8edf8", family="Inter"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=10, color="#8892a4")),
                margin=dict(l=40, r=40, t=60, b=40),
                hoverlabel=dict(bgcolor="#0f1220", bordercolor="rgba(255,255,255,0.12)", font=dict(color="#e8edf8")),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                {_t("radar_explain")}
                <div class="insight"><div class="insight-dot"></div>{_t("radar_insight_1")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("radar_insight_2")}</div>
            </div>
            """, unsafe_allow_html=True)

        # Tier metrics comparison bar charts
        tt2_col1, tt2_col2 = st.columns(2)

        with tt2_col1:
            fig_tier_ltv = px.bar(
                tier_summary, x="icp_tier", y="avg_ltv",
                color="icp_tier", color_discrete_map=TIER_COLORS,
                title=_t("avg_ltv_per_tier"),
                labels={"icp_tier": _t("tier_label"), "avg_ltv": _t("avg_ltv_usd")},
                text=tier_summary["avg_ltv"].apply(lambda x: f"${x:,.0f}"),
            )
            fig_tier_ltv.update_layout(height=350, showlegend=False, **neu_chart_layout)
            fig_tier_ltv.update_traces(textposition="outside")
            st.plotly_chart(fig_tier_ltv, use_container_width=True)

        with tt2_col2:
            fig_tier_cycle = px.bar(
                tier_summary, x="icp_tier", y="avg_cycle",
                color="icp_tier", color_discrete_map=TIER_COLORS,
                title=_t("avg_cycle_per_tier"),
                labels={"icp_tier": _t("tier_label"), "avg_cycle": _t("cycle_days")},
                text=tier_summary["avg_cycle"].apply(lambda x: f"{x:.0f}d"),
            )
            fig_tier_cycle.update_layout(height=350, showlegend=False, **neu_chart_layout)
            fig_tier_cycle.update_traces(textposition="outside")
            st.plotly_chart(fig_tier_cycle, use_container_width=True)

        # Client list by tier
        st.markdown(f'<div class="s-header"><div class="s-icon"></div>{_t("clients_by_tier")}</div>', unsafe_allow_html=True)

        for tier in ["Tier 1", "Tier 2", "Tier 3", "Tier 4"]:
            tier_df = df[df["icp_tier"] == tier].sort_values("icp_score", ascending=False)
            if len(tier_df) == 0:
                continue
            color = TIER_COLORS[tier]
            label = TIER_LABELS[tier]

            with st.expander(f"{tier} — {label} ({len(tier_df)} {_t('customers').lower()})", expanded=(tier == "Tier 1")):
                for _, row in tier_df.iterrows():
                    roi = row["ltv_usd"] / row["deal_size_usd"] if row["deal_size_usd"] > 0 else 0
                    status_text = _t("CHURNED") if row["churned"] else _t("ATIVO")
                    status_color = "#ef4444" if row["churned"] else "#22c55e"
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:12px;padding:12px 16px;margin-bottom:6px;'
                        f'background:#0f1220;'
                        f'border:1px solid rgba(255,255,255,0.08);'
                        f'border-radius:14px;border-left:3px solid {color};">'
                        f'<div style="flex:1;"><div style="font-weight:600;color:#e8edf8;font-size:0.85rem;">{_safe(row["company_name"])}</div>'
                        f'<div style="font-size:0.7rem;color:#64748b;">{_safe(row["industry"])} · {row["employee_count"]:,} {_t("func")} · {_safe(row["tech_class"])}</div></div>'
                        f'<div style="text-align:right;font-size:0.75rem;color:#8892a4;line-height:1.5;">'
                        f'Score: <span style="font-weight:700;color:{color};">{row["icp_score"]:.0f}</span>'
                        + (f' · NPS {int(row["nps_score"])}' if has_nps and pd.notna(row.get("nps_score")) else "")
                        + f' · {row["sales_cycle_days"]}d<br>'
                        f'LTV ${row["ltv_usd"]:,.0f} · ROI {roi:.1f}x · <span style="color:{status_color};font-weight:600;">{status_text}</span>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )

        # Tier methodology note
        st.markdown(f"""
        <div class="chart-explain" style="margin-top:1rem;">
            {_t("tier_methodology_title")} — {_t("tier_methodology_intro")}
            <div class="insight"><div class="insight-dot"></div>{_t("tier_1_desc")}</div>
            <div class="insight"><div class="insight-dot"></div>{_t("tier_2_desc")}</div>
            <div class="insight"><div class="insight-dot"></div>{_t("tier_3_desc")}</div>
            <div class="insight"><div class="insight-dot"></div>{_t("tier_4_desc")}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── TAB 1: Client Health ──
    with tab_health:
        th_col1, th_col2 = st.columns(2)

        with th_col1:
            df_health = df.copy()
            ltv_min_display = df["ltv_usd"].max() * 0.06
            df_health["ltv_display"] = df_health["ltv_usd"].clip(lower=ltv_min_display)

            if has_nps:
                _y_col = "nps_score"
                _y_label = _t("nps_score_label")
            else:
                _y_col = "ltv_usd"
                _y_label = _t("ltv_usd")

            fig_health = px.scatter(
                df_health, x="sales_cycle_days", y=_y_col,
                size="ltv_display", color="churned",
                color_discrete_map=colors_churn,
                hover_name="company_name",
                hover_data={"ltv_usd": ":$,.0f", "ltv_display": False},
                title=_t("health_matrix"),
                labels={"sales_cycle_days": _t("sales_cycle_days"), _y_col: _y_label, "churned": _t("churned_label")},
                size_max=40,
            )
            fig_health.update_traces(marker=dict(sizemin=10))
            if has_nps:
                fig_health.add_hline(y=6.5, line_dash="dot", line_color="rgba(0,0,0,0.15)")
                fig_health.add_annotation(x=25, y=9.5, text=_t("ideal_quadrant"), showarrow=False,
                                          font=dict(size=10, color="#0000FF", family="Inter"), opacity=0.6)
                fig_health.add_annotation(x=80, y=9.5, text=_t("slow_loyal"), showarrow=False,
                                          font=dict(size=10, color="#f59e0b", family="Inter"), opacity=0.6)
                fig_health.add_annotation(x=25, y=2.5, text=_t("fast_unhappy"), showarrow=False,
                                          font=dict(size=10, color="#f59e0b", family="Inter"), opacity=0.6)
                fig_health.add_annotation(x=80, y=2.5, text=_t("danger_zone"), showarrow=False,
                                          font=dict(size=10, color="#ef4444", family="Inter"), opacity=0.6)
            fig_health.add_vline(x=50, line_dash="dot", line_color="rgba(0,0,0,0.15)")
            fig_health.update_layout(height=480, **neu_chart_layout)
            st.plotly_chart(fig_health, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                {_t("health_explain")}
                <div class="insight"><div class="insight-dot"></div>{_t("health_insight_1")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("health_insight_2")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("health_insight_3")}</div>
            </div>
            """, unsafe_allow_html=True)

        with th_col2:
            if has_nps:
                fig_nps = go.Figure()
                fig_nps.add_trace(go.Histogram(
                    x=df[~df["churned"]]["nps_score"], name=_t("active_label"), marker_color="#0000FF",
                    opacity=0.8, xbins=dict(start=0, end=11, size=1)
                ))
                fig_nps.add_trace(go.Histogram(
                    x=df[df["churned"]]["nps_score"], name=_t("churned_status"), marker_color="#ef4444",
                    opacity=0.8, xbins=dict(start=0, end=11, size=1)
                ))
                fig_nps.add_vrect(x0=0, x1=6.5, fillcolor="rgba(239,68,68,0.05)", line_width=0)
                fig_nps.add_vrect(x0=6.5, x1=8.5, fillcolor="rgba(245,158,11,0.05)", line_width=0)
                fig_nps.add_vrect(x0=8.5, x1=11, fillcolor="rgba(124,58,237,0.05)", line_width=0)
                fig_nps.add_annotation(x=3, y=1, yref="paper", yanchor="top", text=_t("detractors"),
                                       showarrow=False, font=dict(size=9, color="#ef4444"))
                fig_nps.add_annotation(x=7.5, y=1, yref="paper", yanchor="top", text=_t("neutrals"),
                                       showarrow=False, font=dict(size=9, color="#f59e0b"))
                fig_nps.add_annotation(x=9.5, y=1, yref="paper", yanchor="top", text=_t("promoters"),
                                       showarrow=False, font=dict(size=9, color="#0000FF"))
                fig_nps.update_layout(
                    title=_t("nps_distribution"), barmode="overlay", height=480,
                    xaxis_title=_t("nps_score_label"), yaxis_title=_t("quantity"), **neu_chart_layout,
                )
                st.plotly_chart(fig_nps, use_container_width=True)

                st.markdown(f"""
                <div class="chart-explain">
                    {_t("nps_explain")}
                    <div class="insight"><div class="insight-dot"></div>{_t("nps_insight_1", nps_net=nps_net)}</div>
                    <div class="insight"><div class="insight-dot"></div>{_t("nps_insight_2", promoters=promoters, detractors=detractors)}</div>
                    <div class="insight"><div class="insight-dot"></div>{_t("nps_insight_3")}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # No NPS data — show churn rate by sales cycle bucket instead
                df_churn_bucket = df.copy()
                df_churn_bucket["cycle_bucket"] = pd.cut(
                    df_churn_bucket["sales_cycle_days"],
                    bins=[0, 30, 60, 90, 180, 9999],
                    labels=["≤30d", "31–60d", "61–90d", "91–180d", "180d+"]
                )
                churn_by_bucket = df_churn_bucket.groupby("cycle_bucket", observed=True)["churned"].mean() * 100
                fig_churn_cycle = go.Figure(go.Bar(
                    x=churn_by_bucket.index.astype(str),
                    y=churn_by_bucket.values,
                    marker_color="#0000FF",
                    text=[f"{v:.0f}%" for v in churn_by_bucket.values],
                    textposition="outside",
                ))
                fig_churn_cycle.update_layout(
                    title=_t("churn_by_cycle"),
                    height=480,
                    yaxis_title="%",
                    xaxis_title=_t("sales_cycle_days"),
                    **neu_chart_layout,
                )
                st.plotly_chart(fig_churn_cycle, use_container_width=True)

    # ── TAB 2: Financial Analysis ──
    with tab_finance:
        tf_col1, tf_col2 = st.columns(2)

        with tf_col1:
            fig_ltv = px.bar(
                df.sort_values("ltv_usd", ascending=True),
                x="ltv_usd", y="company_name", orientation="h",
                color="churned", color_discrete_map=colors_churn,
                title=_t("ltv_per_customer"),
                labels={"ltv_usd": _t("ltv_usd"), "company_name": "", "churned": _t("churned_label")},
            )
            fig_ltv.update_layout(height=520, **neu_chart_layout)
            fig_ltv.update_traces(marker_line_width=0)
            st.plotly_chart(fig_ltv, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                {_t("ltv_explain")}
                <div class="insight"><div class="insight-dot"></div>{_t("ltv_insight_1", active_ltv=f"{active_ltv:,.0f}", churned_ltv=f"{churned_ltv:,.0f}", ratio=f"{ltv_ratio:.0f}")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("ltv_insight_2")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("ltv_insight_3")}</div>
            </div>
            """, unsafe_allow_html=True)

        with tf_col2:
            fig_roi = px.scatter(
                df, x="deal_size_usd", y="ltv_usd",
                color="churned", color_discrete_map=colors_churn,
                hover_name="company_name", size="employee_count",
                title=_t("deal_vs_ltv"),
                labels={"deal_size_usd": _t("deal_size_usd"), "ltv_usd": _t("ltv_usd"), "churned": _t("churned_label")},
            )
            max_deal = df["deal_size_usd"].max()
            for mult, label in [(1, "1x"), (3, "3x"), (5, "5x")]:
                fig_roi.add_trace(go.Scatter(
                    x=[0, max_deal], y=[0, max_deal * mult],
                    mode="lines", line=dict(dash="dot", color="rgba(0,0,0,0.1)", width=1),
                    showlegend=False, hoverinfo="skip"
                ))
                fig_roi.add_annotation(x=max_deal * 0.95, y=max_deal * mult * 0.95,
                                       text=f"{label} {_t('roi_label')}", showarrow=False,
                                       font=dict(size=9, color="#64748b"))
            fig_roi.update_layout(height=520, **neu_chart_layout)
            st.plotly_chart(fig_roi, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                {_t("roi_explain")}
                <div class="insight"><div class="insight-dot"></div>{_t("roi_insight_1", active_roi=f"{avg_roi_active:.1f}", churned_roi=f"{avg_roi_churned:.1f}")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("roi_insight_2")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("roi_insight_3")}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 3: Segmentation & Tech ──
    with tab_segment:
        ts_col1, ts_col2 = st.columns(2)

        with ts_col1:
            industry_data = df.groupby(["industry", "churned"]).size().reset_index(name="count")
            industry_data["status"] = industry_data["churned"].map({True: _t("churned_status"), False: _t("active_status")})

            fig_industry = px.sunburst(
                industry_data, path=["status", "industry"], values="count",
                color="status", color_discrete_map={_t("active_status"): "#0000FF", _t("churned_status"): "#ef4444"},
                title=_t("status_industry_dist"),
            )
            fig_industry.update_layout(height=480, **neu_chart_layout)
            fig_industry.update_traces(
                textinfo="label+percent parent",
                insidetextorientation="radial",
                marker=dict(line=dict(color="#0c0f1a", width=2)),
            )
            st.plotly_chart(fig_industry, use_container_width=True)

            top_industries = df[~df["churned"]].groupby("industry").agg(
                count=("company_name", "count"), avg_ltv=("ltv_usd", "mean")
            ).sort_values("avg_ltv", ascending=False)
            top3 = top_industries.head(3)
            top3_items = "".join([
                f'<div class="insight"><div class="insight-dot"></div>{ind} — LTV medio ${row["avg_ltv"]:,.0f}</div>'
                for ind, row in top3.iterrows()
            ])

            st.markdown(f"""
            <div class="chart-explain">
                {_t("sunburst_explain")}
                <div class="insight"><div class="insight-dot"></div>{_t("top3_industries")}</div>
                {top3_items}
                <div class="insight"><div class="insight-dot"></div>{_t("problematic_segments")}</div>
            </div>
            """, unsafe_allow_html=True)

        with ts_col2:
            tech_summary = df.groupby(["tech_class", "churned"]).agg(
                count=("company_name", "count"),
            ).reset_index()
            tech_summary["status"] = tech_summary["churned"].map({True: _t("churned_status"), False: _t("active_status")})

            fig_tech = px.bar(
                tech_summary, x="tech_class", y="count",
                color="status", barmode="group",
                color_discrete_map={_t("active_status"): "#0000FF", _t("churned_status"): "#ef4444"},
                title=_t("tech_maturity_title"),
                labels={"tech_class": _t("tech_stack"), "count": _t("customers"), "status": _t("status_label")},
            )
            fig_tech.update_layout(height=480, **neu_chart_layout)
            st.plotly_chart(fig_tech, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                {_t("tech_explain")}
                <div class="insight"><div class="insight-dot"></div>{_t("tech_insight_1", cloud=f"{cloud_churn:.0f}", legacy=f"{legacy_churn:.0f}")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("tech_insight_2", cloud_nps=f"{cloud_nps:.1f}", legacy_nps=f"{legacy_nps:.1f}")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("tech_insight_3")}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 4: Risk & Cohort ──
    with tab_risk:
        tr_col1, tr_col2 = st.columns(2)

        with tr_col1:
            fig_cohort = go.Figure()
            fig_cohort.add_trace(go.Bar(
                x=cohort["revenue_band"], y=cohort["avg_ltv"],
                name=_t("avg_ltv"), marker_color="#0000FF", yaxis="y",
            ))
            fig_cohort.add_trace(go.Scatter(
                x=cohort["revenue_band"], y=cohort["retention_rate"],
                name=_t("retention_pct"), mode="lines+markers",
                line=dict(color="#22c55e", width=3), marker=dict(size=8), yaxis="y2",
            ))
            fig_cohort.update_layout(
                title=_t("cohort_revenue"), height=480,
                yaxis=dict(title=_t("avg_ltv_chart"), gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)", tickcolor="rgba(255,255,255,0.08)"),
                yaxis2=dict(title=_t("retention_chart"), overlaying="y", side="right", range=[0, 110], gridcolor="rgba(0,0,0,0)"),
                xaxis=dict(title=_t("annual_revenue_band"), gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)", tickcolor="rgba(255,255,255,0.08)"),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#8892a4", size=11),
                title_font=dict(size=13, color="#e8edf8", family="Inter"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11, color="#8892a4")),
                margin=dict(l=0, r=40, t=40, b=0),
                hoverlabel=dict(bgcolor="#0f1220", bordercolor="rgba(255,255,255,0.12)", font=dict(color="#e8edf8")),
            )
            st.plotly_chart(fig_cohort, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                {_t("cohort_explain")}
                <div class="insight"><div class="insight-dot"></div>{_t("cohort_insight_1", band=best_cohort['revenue_band'], ltv=f"{best_cohort['avg_ltv']:,.0f}", retention=f"{best_cohort['retention_rate']:.0f}")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("cohort_insight_2")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("cohort_insight_3")}</div>
            </div>
            """, unsafe_allow_html=True)

        with tr_col2:
            fig_age = px.scatter(
                df, x="company_age", y="employee_count",
                color="churned", color_discrete_map=colors_churn,
                size="deal_size_usd", hover_name="company_name",
                title=_t("age_vs_size"),
                labels={"company_age": _t("age_years"), "employee_count": _t("employees"), "churned": _t("churned_label")},
            )
            fig_age.update_layout(height=480, **neu_chart_layout)
            st.plotly_chart(fig_age, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                {_t("age_explain")}
                <div class="insight"><div class="insight-dot"></div>{_t("age_insight_1", age=f"{active_age:.0f}", size=f"{active_size:.0f}")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("age_insight_2", age=f"{churned_age:.0f}", size=f"{churned_size:.0f}")}</div>
                <div class="insight"><div class="insight-dot"></div>{_t("age_insight_3")}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 5: Executive Summary ──
    with tab_summary:
        top_ltv_company = df.loc[df["ltv_usd"].idxmax(), "company_name"]
        top_ltv_val = df["ltv_usd"].max()

        _nps_line = ""
        if has_nps:
            best_nps_company = df.loc[df["nps_score"].idxmax(), "company_name"]
            _nps_line = f'<div class="cc-list-item"><div class="cc-bullet"></div>{_t("best_nps_customer", name=_safe(best_nps_company), nps=df["nps_score"].max())}</div>'

        st.markdown(f"""
        <div class="company-card">
            <div class="cc-section-title">{_t("key_findings")}</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>{_t("best_industry", industry=best_industry)}</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>{_t("worst_industry", industry=worst_churn_industry)}</div>
            {_nps_line}
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="cc-list-item"><div class="cc-bullet"></div>{_t("top_ltv_customer", name=_safe(top_ltv_company), ltv=f"{top_ltv_val:,.0f}")}</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>{_t("tech_predictor", diff=f"{legacy_churn - cloud_churn:.0f}")}</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>{_t("roi_comparison", active=f"{avg_roi_active:.1f}", churned=f"{avg_roi_churned:.1f}")}</div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="cc-section-title" style="margin-top:1.25rem;">{_t("recommendations")}</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>{_t("rec_1", industry=best_industry)}</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>{_t("rec_2", size=int(churned_size))}</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>{_t("rec_3", band=best_cohort['revenue_band'])}</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>{_t("rec_4")}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── ICP Button ──
    st.markdown(f'<div class="s-header"><div class="s-icon"></div>{_t("generate_icp")}</div>', unsafe_allow_html=True)

    if st.button(_t("generate_icp_btn"), type="primary", use_container_width=True):
        if not api_key:
            st.error(_t("configure_api"))
        else:
            with st.spinner(_t("analyzing_patterns")):
                icp = analyze_customers(df, api_key, lang=st.session_state.get("_lang", "en"))
                st.session_state["icp"] = icp

    if "icp" in st.session_state:
        icp = st.session_state["icp"]
        col_icp, col_anti = st.columns(2)

        with col_icp:
            st.markdown(f"""
            <div class="icp-card positive">
                <div class="card-badge">Ideal Customer Profile</div>
                <h2>{_t("ideal_customer")}</h2>
                <p>{icp.summary}</p>
            </div>
            """, unsafe_allow_html=True)

            # Industries
            st.markdown(f'<div class="detail-group"><div class="dg-title">{_t("ideal_industries")}</div>', unsafe_allow_html=True)
            for ind in icp.ideal_industries:
                st.markdown(f'<div class="detail-item"><div class="di-dot"></div>{ind}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Profile
            st.markdown(f"""
            <div class="detail-group">
                <div class="dg-title">{_t("profile")}</div>
                <div class="detail-item"><div class="di-dot"></div>{_t("employees")}: {icp.ideal_employee_range}</div>
                <div class="detail-item"><div class="di-dot"></div>{_t("revenue_label").title()}: {icp.ideal_revenue_range}</div>
                <div class="detail-item"><div class="di-dot"></div>{_t("age_years")}: {icp.ideal_company_age}</div>
            </div>
            """, unsafe_allow_html=True)

            # Tech
            st.markdown(f'<div class="detail-group"><div class="dg-title">{_t("tech_signals")}</div>', unsafe_allow_html=True)
            for sig in icp.ideal_tech_signals:
                st.markdown(f'<div class="detail-item"><div class="di-dot"></div>{sig}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Key patterns
            st.markdown(f'<div class="detail-group"><div class="dg-title">{_t("key_patterns")}</div>', unsafe_allow_html=True)
            pills = "".join(f'<span class="pattern-pill">{p}</span>' for p in icp.key_patterns)
            st.markdown(pills, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_anti:
            st.markdown(f"""
            <div class="icp-card negative">
                <div class="card-badge">Anti-ICP</div>
                <h2>{_t("profile_to_avoid")}</h2>
                <p>{icp.anti_icp_summary}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f'<div class="detail-group"><div class="dg-title" style="color:#ef4444;">{_t("warning_signals")}</div>', unsafe_allow_html=True)
            for sig in icp.anti_icp_signals:
                st.markdown(f'<div class="alert-item"><div class="alert-dot"></div>{sig}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Beta Disclaimer ──
        st.markdown(f"""
        <div style="
            margin: 1.5rem 0 1rem 0;
            padding: 1.25rem 1.5rem;
            background: #0f1220;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            border-left: 4px solid #0000FF;
            display: flex; align-items: flex-start; gap: 14px;
        ">
            <div style="font-size: 1.4rem; line-height: 1;">🧪</div>
            <div>
                <div style="font-weight: 700; font-size: 0.8rem; color: #0000FF; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">{_t("beta_badge")}</div>
                <div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.6;">{_t("beta_disclaimer")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Suggestions ──
        st.markdown(f'<div class="s-header"><div class="s-icon"></div>{_t("suggestions_title")}</div>', unsafe_allow_html=True)
        _suggestion = st.text_area(_t("suggestions_placeholder"), height=100, key="suggestion_text", label_visibility="collapsed", placeholder=_t("suggestions_placeholder"))
        if _suggestion and _suggestion.strip():
            _mailto = f"mailto:bruno@brunoseixas.com?subject={quote('ICP Tool — Suggestion')}&body={quote(_suggestion.strip())}"
            st.markdown(
                f'<a href="{_mailto}" target="_blank" style="'
                f'display:inline-flex;align-items:center;gap:8px;padding:10px 24px;'
                f'background:linear-gradient(135deg,#0000FF,#0033CC);color:white;'
                f'border-radius:50px;font-size:0.82rem;font-weight:600;text-decoration:none;'
                f'box-shadow:0 4px 14px rgba(0,0,255,0.25);'
                f'transition:all 0.2s ease;">'
                f'✉️ {_t("suggestions_send")}</a>',
                unsafe_allow_html=True,
            )
        else:
            st.caption(_t("suggestions_hint"))

        # ── Scoring ──
        st.markdown(f'<div class="s-header"><div class="s-icon"></div>{_t("prospect_scoring")}</div>', unsafe_allow_html=True)

        if prospects_file:
            prospects_df = pd.read_csv(prospects_file)
        else:
            st.info(_t("no_prospects"))
            prospects_df = df.copy()

        if st.button(_t("score_prospects_btn"), type="primary", use_container_width=True):
            with st.spinner(_t("scoring_prospects")):
                scored = score_prospects(icp, prospects_df, api_key, lang=st.session_state.get("_lang", "en"))
                st.session_state["scored"] = scored

        if "scored" in st.session_state:
            scored = st.session_state["scored"]
            scored_df = pd.DataFrame([s.model_dump() for s in scored])
            scored_df = scored_df.sort_values("score", ascending=False)

            # Chart
            colors_rec = {"hot": "#0000FF", "warm": "#f59e0b", "cold": "#9ca3af", "avoid": "#ef4444"}
            fig_scores = px.bar(
                scored_df, x="company_name", y="score",
                color="recommendation", color_discrete_map=colors_rec,
                title=_t("prospect_ranking"),
                labels={"company_name": "", "score": "Score", "recommendation": "Status"},
            )
            fig_scores.update_layout(height=400, xaxis_tickangle=-45, **neu_chart_layout)
            fig_scores.update_traces(marker_line_width=0)
            st.plotly_chart(fig_scores, use_container_width=True)

            # Score rows
            for _, row in scored_df.iterrows():
                rec = row["recommendation"]
                st.markdown(f"""
                <div class="score-row">
                    <div class="sr-name">{_safe(row['company_name'])}</div>
                    <div class="sr-score {_safe(rec)}">{row['score']}</div>
                    <div class="sr-badge {_safe(rec)}">{_safe(rec)}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            for _, row in scored_df.iterrows():
                with st.expander(f"{row['company_name']} — {_t('details')}"):
                    fit_col, risk_col = st.columns(2)
                    with fit_col:
                        st.markdown(f"**{_t('fit')}**")
                        for r in row["fit_reasons"]:
                            st.markdown(f"- {r}")
                    with risk_col:
                        if row["risk_flags"]:
                            st.markdown(f"**{_t('risks')}**")
                            for r in row["risk_flags"]:
                                st.markdown(f"- {r}")
else:
    st.markdown(f"""
    <div class="empty-state">
        <div style="color: #8892a4; font-size: 1rem; line-height: 1.7; max-width: 560px; margin: 0 auto;">
            {_t("empty_subtitle")}
        </div>
    </div>
    """, unsafe_allow_html=True)

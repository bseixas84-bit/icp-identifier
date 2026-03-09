import os
import json
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

from engine.analyzer import analyze_customers
from engine.scorer import score_prospects
from engine.intelligence import run_intelligence_pipeline

load_dotenv()

st.set_page_config(page_title="ICP Identifier", page_icon="target", layout="wide")

# ── Load cached companies ──
CACHE_DIR = Path("data/cache")
CACHED_COMPANIES = {}
if CACHE_DIR.exists():
    for f in sorted(CACHE_DIR.glob("*.json")):
        with open(f) as fh:
            data = json.load(fh)
        label = data.get("dna", {}).get("company_name", f.stem.title())
        CACHED_COMPANIES[label] = data

# ── Neuromorphic CSS ──
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    :root {
        --neu-bg: #e6e9ef;
        --neu-bg2: #d1d5db;
        --neu-dark: #b8bcc2;
        --neu-light: #ffffff;
        --primary: #7c3aed;
        --primary-dark: #6d28d9;
    }

    * { font-family: 'Inter', system-ui, sans-serif !important; }

    /* Global background */
    .stApp {
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2)) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2)) !important;
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
        background: rgba(230, 233, 239, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(0,0,0,0.06);
        transition: all 0.35s ease;
    }
    .bs-navbar .bs-logo {
        font-size: 1rem;
        font-weight: 700;
        color: #111827;
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
        color: #6b7280;
        text-decoration: none;
        transition: color 0.2s ease;
        letter-spacing: 0.01em;
    }
    .bs-navbar nav a:hover {
        color: #111827;
    }
    .bs-navbar .bs-cta {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 20px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white !important;
        background: linear-gradient(135deg, #7c3aed, #6d28d9);
        border-radius: 50px;
        text-decoration: none;
        box-shadow: 3px 3px 6px var(--neu-dark), -3px -3px 6px var(--neu-light);
        transition: all 0.2s ease;
    }
    .bs-navbar .bs-cta:hover {
        transform: translateY(-1px);
        box-shadow: 4px 4px 10px var(--neu-dark), -4px -4px 10px var(--neu-light);
    }
    .bs-navbar .bs-lang {
        font-size: 0.65rem;
        color: #9ca3af;
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

    /* ── Neuromorphic Surfaces ── */
    .neu-raised {
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        box-shadow: 8px 8px 16px var(--neu-dark), -8px -8px 16px var(--neu-light);
        border-radius: 24px;
    }
    .neu-raised-sm {
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        box-shadow: 4px 4px 8px var(--neu-dark), -4px -4px 8px var(--neu-light);
        border-radius: 16px;
    }
    .neu-inset {
        background: linear-gradient(145deg, var(--neu-bg2), var(--neu-bg));
        box-shadow: inset 4px 4px 8px var(--neu-dark), inset -4px -4px 8px var(--neu-light);
        border-radius: 12px;
    }

    /* ── Header ── */
    .header-container {
        text-align: center;
        padding: 1rem 0 1.5rem 0;
        margin-bottom: 1.5rem;
    }
    .header-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 50px;
        box-shadow: 4px 4px 8px var(--neu-dark), -4px -4px 8px var(--neu-light);
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        margin-bottom: 1.25rem;
        font-size: 0.7rem;
        font-weight: 500;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .header-badge .pulse-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #22c55e;
        animation: pulse-glow 2s ease-in-out infinite;
    }
    @keyframes pulse-glow {
        0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
        50% { opacity: 0.7; box-shadow: 0 0 0 6px rgba(34,197,94,0); }
    }
    .header-container h1 {
        font-size: 2.75rem;
        font-weight: 700;
        color: #1f2937;
        letter-spacing: -0.03em;
        margin: 0;
    }
    .header-container p {
        color: #6b7280;
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
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
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        box-shadow: 6px 6px 12px var(--neu-dark), -6px -6px 12px var(--neu-light);
        border-radius: 20px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .m-card:hover {
        transform: translateY(-2px);
        box-shadow: 10px 10px 20px var(--neu-dark), -10px -10px 20px var(--neu-light);
    }
    .m-card .m-label {
        color: #9ca3af;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.5rem;
    }
    .m-card .m-value {
        color: #1f2937;
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
        box-shadow: 4px 4px 8px var(--neu-dark), -4px -4px 8px var(--neu-light);
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        margin: 2rem 0 1.5rem 0;
        font-size: 0.7rem;
        font-weight: 600;
        color: #6b7280;
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
        background: linear-gradient(145deg, var(--neu-bg2), var(--neu-bg));
        box-shadow: inset 2px 2px 4px var(--neu-dark), inset -2px -2px 4px var(--neu-light);
        border-radius: 12px;
        font-size: 0.78rem;
        color: #4b5563;
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
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        box-shadow: 8px 8px 16px var(--neu-dark), -8px -8px 16px var(--neu-light);
        border-radius: 24px;
        margin-bottom: 1.5rem;
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
        background: linear-gradient(135deg, #7c3aed, #6d28d9);
        color: white;
    }
    .icp-card.negative .card-badge {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
    }
    .icp-card h2 {
        color: #1f2937;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0 0 0.75rem 0;
        letter-spacing: -0.02em;
    }
    .icp-card p {
        color: #6b7280;
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
        background: linear-gradient(145deg, var(--neu-bg2), var(--neu-bg));
        box-shadow: inset 2px 2px 4px var(--neu-dark), inset -2px -2px 4px var(--neu-light);
        border-radius: 12px;
        color: #374151;
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
        background: linear-gradient(135deg, #7c3aed, #6d28d9);
        color: white;
        font-size: 0.75rem;
        font-weight: 500;
        border-radius: 50px;
        box-shadow: 3px 3px 6px var(--neu-dark), -3px -3px 6px var(--neu-light);
    }

    /* ── Alert Items (Anti-ICP) ── */
    .alert-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 12px 14px;
        margin-bottom: 6px;
        background: linear-gradient(145deg, var(--neu-bg2), var(--neu-bg));
        box-shadow: inset 2px 2px 4px var(--neu-dark), inset -2px -2px 4px var(--neu-light);
        border-radius: 12px;
        color: #374151;
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
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        box-shadow: 4px 4px 8px var(--neu-dark), -4px -4px 8px var(--neu-light);
        border-radius: 16px;
        transition: transform 0.15s ease;
    }
    .score-row:hover { transform: translateY(-1px); }
    .score-row .sr-name {
        flex: 1;
        color: #1f2937;
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
    .sr-score.warm { color: #6b7280; }
    .sr-score.cold { color: #9ca3af; }
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
    .sr-badge.hot { background: linear-gradient(135deg, #7c3aed, #6d28d9); }
    .sr-badge.warm { background: linear-gradient(135deg, #f59e0b, #d97706); }
    .sr-badge.cold { background: linear-gradient(135deg, #9ca3af, #6b7280); }
    .sr-badge.avoid { background: linear-gradient(135deg, #ef4444, #dc2626); }

    /* ── Button Override ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 0.75rem 2rem !important;
        box-shadow: 4px 4px 8px var(--neu-dark), -4px -4px 8px var(--neu-light) !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 6px 6px 12px var(--neu-dark), -6px -6px 12px var(--neu-light) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(1px) !important;
        box-shadow: inset 2px 2px 4px var(--neu-dark), inset -2px -2px 4px var(--neu-light) !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        border-radius: 16px !important;
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
    }
    .empty-icon {
        width: 64px; height: 64px;
        margin: 0 auto 1.5rem auto;
        border-radius: 20px;
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        box-shadow: 6px 6px 12px var(--neu-dark), -6px -6px 12px var(--neu-light);
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
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        box-shadow: 8px 8px 16px var(--neu-dark), -8px -8px 16px var(--neu-light);
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
        background: linear-gradient(135deg, #7c3aed, #6d28d9);
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
        color: #1f2937;
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
        color: #6b7280;
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
        background: linear-gradient(145deg, var(--neu-bg2), var(--neu-bg));
        box-shadow: inset 2px 2px 4px var(--neu-dark), inset -2px -2px 4px var(--neu-light);
        border-radius: 50px;
        font-size: 0.75rem;
        color: #374151;
    }
    .cc-tag.purple {
        background: linear-gradient(135deg, #7c3aed, #6d28d9);
        box-shadow: 2px 2px 4px var(--neu-dark), -2px -2px 4px var(--neu-light);
        color: white;
    }
    .cc-list-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 6px 0;
        font-size: 0.8rem;
        color: #374151;
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
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        box-shadow: 8px 8px 16px var(--neu-dark), -8px -8px 16px var(--neu-light);
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
        border-bottom: 1px solid rgba(0,0,0,0.04);
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
        background: linear-gradient(135deg, #7c3aed, #6d28d9);
        color: white;
    }
    .phase-num.active {
        background: linear-gradient(145deg, var(--neu-bg2), var(--neu-bg));
        box-shadow: inset 2px 2px 4px var(--neu-dark), inset -2px -2px 4px var(--neu-light);
        color: var(--primary);
        animation: pulse-phase 1.5s ease-in-out infinite;
    }
    .phase-num.pending {
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        box-shadow: 2px 2px 4px var(--neu-dark), -2px -2px 4px var(--neu-light);
        color: #9ca3af;
    }
    @keyframes pulse-phase {
        0%, 100% { box-shadow: inset 2px 2px 4px var(--neu-dark), inset -2px -2px 4px var(--neu-light); }
        50% { box-shadow: inset 1px 1px 2px var(--neu-dark), inset -1px -1px 2px var(--neu-light), 0 0 12px rgba(124,58,237,0.3); }
    }
    .phase-info { flex: 1; }
    .phase-name {
        font-size: 0.8rem;
        font-weight: 600;
        color: #374151;
    }
    .phase-status {
        font-size: 0.7rem;
        color: #9ca3af;
        margin-top: 2px;
    }
    .phase-status.done { color: #22c55e; }

    /* ── Dossier Card ── */
    .dossier-card {
        padding: 1.25rem 1.5rem;
        background: linear-gradient(145deg, var(--neu-bg), var(--neu-bg2));
        box-shadow: 4px 4px 8px var(--neu-dark), -4px -4px 8px var(--neu-light);
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
        background: linear-gradient(135deg, #7c3aed, #6d28d9);
        display: flex; align-items: center; justify-content: center;
        color: white; font-size: 1.1rem; flex-shrink: 0;
    }
    .dossier-info .dossier-name {
        font-size: 0.85rem; font-weight: 600; color: #1f2937;
    }
    .dossier-info .dossier-meta {
        font-size: 0.7rem; color: #9ca3af; margin-top: 2px;
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
        box-shadow: 2px 2px 4px var(--neu-dark), -2px -2px 4px var(--neu-light);
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
        background: linear-gradient(135deg, rgba(124,58,237,0.15), rgba(124,58,237,0.05));
        color: var(--primary);
    }
    .health-bad {
        background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05));
        color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)

# ── Navbar (brunoseixas.com style) ──
st.markdown("""
<div class="bs-navbar">
    <a href="https://brunoseixas.com" class="bs-logo" target="_blank"><span class="plus">+</span>Bruno Seixas</a>
    <nav>
        <a href="https://brunoseixas.com/#about" target="_blank">About</a>
        <a href="https://brunoseixas.com/#services" target="_blank">Services</a>
        <a href="https://brunoseixas.com/#case-studies" target="_blank">Case Studies</a>
        <a href="https://brunoseixas.com/#contact" target="_blank">Contact</a>
        <a href="#" class="bs-cta">Get in Touch</a>
    </nav>
</div>
<div class="navbar-spacer"></div>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""
<div class="header-container">
    <div class="header-badge">
        <div class="pulse-dot"></div>
        Powered by AI
    </div>
    <h1>ICP Identifier</h1>
    <p>Descubra seu cliente ideal a partir dos seus dados</p>
</div>
""", unsafe_allow_html=True)

# ── Load B3 companies ──
with open("data/companies_b3.json", "r") as f:
    B3_COMPANIES = json.load(f)
B3_OPTIONS = {f"{c['name']} ({c['ticker']})": c for c in B3_COMPANIES}

# ── Sidebar ──
api_key = os.getenv("GROQ_API_KEY", "")

with st.sidebar:
    st.markdown("### Fonte de Dados")

    data_source = st.radio(
        "Escolha uma opcao",
        options=["Empresa pre-carregada", "Pesquisar nova empresa", "Upload CSV"],
        key="data_source",
        horizontal=False,
    )

    # ── Option 1: Pre-loaded cache ──
    selected_cached = "Selecionar..."
    selected_company = "Selecionar..."
    company_url = ""
    research_btn = False
    customers_file = None
    use_sample = False
    prospects_file = None

    if data_source == "Empresa pre-carregada":
        cached_labels = list(CACHED_COMPANIES.keys())
        selected_cached = st.selectbox(
            "Carregamento instantaneo",
            options=["Selecionar..."] + cached_labels,
            key="cached_select",
            help="Dados completos pre-analisados. Carregamento imediato."
        )

        if selected_cached != "Selecionar...":
            cache_data = CACHED_COMPANIES[selected_cached]
            if st.session_state.get("_loaded_cache") != selected_cached:
                for key in ["icp", "scored"]:
                    st.session_state.pop(key, None)
                st.session_state["intel_dna"] = cache_data["dna"]
                st.session_state["intel_market"] = cache_data["market"]
                clients_df = pd.DataFrame(cache_data["clients"])
                clients_df["churned"] = clients_df["churned"].apply(
                    lambda x: str(x).strip().lower() in ("true", "1", "yes")
                )
                st.session_state["generated_clients"] = clients_df
                st.session_state["intel_dossier"] = ""
                st.session_state["intel_dossier_path"] = ""
                st.session_state["company_source"] = None
                st.session_state["_loaded_cache"] = selected_cached

            st.markdown(f"""
            <div class="instant-badge">Dados pre-carregados</div>
            <div style="padding:10px 12px; border-radius:12px;
                background: linear-gradient(145deg, var(--neu-bg2), var(--neu-bg));
                box-shadow: inset 2px 2px 4px var(--neu-dark), inset -2px -2px 4px var(--neu-light);
                font-size:0.75rem; color:#374151; line-height:1.6;">
                <strong style="color:#7c3aed;">{selected_cached}</strong><br>
                DNA + Mercado + {len(cache_data['clients'])} clientes<br>
                <span style="color:#9ca3af; font-size:0.65rem;">Fonte: Cache local + IA (Llama 3.3 70B)</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Option 2: Research new company ──
    elif data_source == "Pesquisar nova empresa":
        selected_company = st.selectbox(
            "Empresas B3 (exemplos)",
            options=["Selecionar..."] + list(B3_OPTIONS.keys()),
            key="b3_select",
        )
        company_url = st.text_input("Ou digite uma URL", placeholder="exemplo.com.br")

        if selected_company != "Selecionar..." and not company_url:
            company_url = B3_OPTIONS[selected_company]["url"]

        research_btn = st.button("Pesquisar", type="primary", use_container_width=True, key="research")

        if selected_company != "Selecionar...":
            c = B3_OPTIONS[selected_company]
            rev_brl = c["annual_revenue_brl"] / 1e9
            st.markdown(f"""
            <div style="padding:10px 12px; margin-top:8px; border-radius:12px;
                background: linear-gradient(145deg, var(--neu-bg2), var(--neu-bg));
                box-shadow: inset 2px 2px 4px var(--neu-dark), inset -2px -2px 4px var(--neu-light);
                font-size:0.75rem; color:#374151; line-height:1.6;">
                <strong style="color:#7c3aed;">{c['name']}</strong> — {c['industry']}<br>
                {c['employee_count']:,} funcionarios · R$ {rev_brl:.1f}B receita<br>
                Fundada em {c['founding_year']} · {c['hq']}<br>
                <span style="color:#9ca3af; font-size:0.65rem;">Fonte: {c['source']}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Option 3: Upload CSV ──
    elif data_source == "Upload CSV":
        customers_file = st.file_uploader("Upload CSV de clientes", type=["csv"], key="customers")
        use_sample = st.checkbox("Usar dados de exemplo", value=False)

    st.markdown("---")
    st.markdown("### Prospects")
    prospects_file = st.file_uploader("Upload CSV de prospects", type=["csv"], key="prospects")

# ── Company Research ──
# ── Intelligence Pipeline ──
PHASE_NAMES = {
    1: "Discovery",
    2: "Company DNA",
    3: "Market Intel",
    4: "Client Generation",
    5: "Dossier",
}

if research_btn and company_url:
    if not api_key:
        st.error("Configure GROQ_API_KEY no arquivo .env")
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
            return f'<div class="pipeline-container"><div class="pipeline-title">Intelligence Pipeline</div>{rows}</div>'

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
            b3_match = next((c for c in B3_COMPANIES if c["url"] == company_url), None)
            st.session_state["company_source"] = b3_match

        except Exception as e:
            st.error(f"Erro no pipeline: {e}")

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
        source_text = "Scraping do site oficial + analise por IA (Llama 3.3 70B via Groq)"

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

    st.markdown(f"""
    <div class="company-card">
        <div class="cc-header">
            <div class="cc-icon">{initial}</div>
            <div>
                <div class="cc-name">{name}</div>
                <div class="cc-industry">{dna.get('industry', '')} · {dna.get('business_model', '')}</div>
            </div>
        </div>
        <div class="cc-desc">{dna.get('description', '')}</div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="cc-grid">
            <div>
                <div class="cc-section-title">Produtos & Servicos</div>
                {products_html}
            </div>
            <div>
                <div class="cc-section-title">Tecnologias</div>
                {tech_html}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="margin-top: 1rem;">
            <div class="cc-section-title">Segmentos-alvo</div>
            {segments_html}
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="cc-grid" style="margin-top: 1rem;">
            <div>
                <div class="cc-section-title">Prova Social</div>
                {social_html}
            </div>
            <div>
                <div class="cc-section-title">Parcerias</div>
                {partners_html}
            </div>
        </div>
        <div style="margin-top:1rem; padding-top:0.75rem; border-top:1px solid rgba(0,0,0,0.06);">
            <div style="font-size:0.7rem; color:#9ca3af;">Fonte: {source_text}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Market Intel Card ──
    st.markdown('<div class="s-header"><div class="s-icon"></div>Inteligencia de Mercado</div>', unsafe_allow_html=True)

    col_market1, col_market2 = st.columns(2)

    with col_market1:
        st.markdown(f"""
        <div class="company-card">
            <div class="cc-section-title">Competidores Mapeados</div>
            {bullets(market.get('likely_competitors', [])[:6])}
            <div class="cc-section-title" style="margin-top:1rem;">Gatilhos de Compra</div>
            {bullets(market.get('buying_triggers', [])[:5])}
            <div class="cc-section-title" style="margin-top:1rem;">Decisores Tipicos</div>
            {tags(market.get('decision_makers', [])[:6])}
        </div>
        """, unsafe_allow_html=True)

    with col_market2:
        st.markdown(f"""
        <div class="company-card">
            <div class="cc-section-title">Caracteristicas do Cliente Ideal</div>
            {bullets(market.get('ideal_customer_characteristics', [])[:7])}
            <div class="cc-section-title" style="margin-top:1rem;">Sinais de Anti-ICP</div>
            {bullets(market.get('anti_icp_signals', [])[:5])}
        </div>
        """, unsafe_allow_html=True)

    # ── Dossier Download (only if available) ──
    if dossier_md:
        st.markdown(f"""
        <div class="dossier-card">
            <div class="dossier-icon">D</div>
            <div class="dossier-info">
                <div class="dossier-name">{name} — Intelligence Dossier</div>
                <div class="dossier-meta">Relatorio completo salvo em {dossier_path}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="Baixar Dossier (.md)",
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
    # ── Metrics ──
    churn_rate = df["churned"].mean() * 100
    avg_ltv = df["ltv_usd"].mean()
    avg_nps = df["nps_score"].mean()
    avg_cycle = df["sales_cycle_days"].mean()
    active = len(df[~df["churned"]])
    total_revenue = df["annual_revenue_usd"].sum()
    avg_deal = df["deal_size_usd"].mean()

    st.markdown(f"""
    <div class="metrics-grid">
        <div class="m-card">
            <div class="m-label">Clientes</div>
            <div class="m-value">{len(df)}</div>
        </div>
        <div class="m-card">
            <div class="m-label">Ativos</div>
            <div class="m-value purple">{active}</div>
        </div>
        <div class="m-card">
            <div class="m-label">Churn Rate</div>
            <div class="m-value">{churn_rate:.0f}%</div>
        </div>
        <div class="m-card">
            <div class="m-label">LTV Medio</div>
            <div class="m-value">${avg_ltv:,.0f}</div>
        </div>
        <div class="m-card">
            <div class="m-label">NPS</div>
            <div class="m-value purple">{avg_nps:.1f}</div>
        </div>
        <div class="m-card">
            <div class="m-label">Ciclo Medio</div>
            <div class="m-value">{avg_cycle:.0f}d</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Shared chart layout ──
    neu_chart_layout = dict(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#6b7280", size=11),
        title_font=dict(size=13, color="#374151", family="Inter"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11)),
        margin=dict(l=0, r=10, t=40, b=0),
        yaxis=dict(gridcolor="rgba(0,0,0,0.05)"),
        xaxis=dict(gridcolor="rgba(0,0,0,0.05)"),
    )
    colors_churn = {True: "#ef4444", False: "#7c3aed"}

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
    # Multi-dimensional scoring: NPS (30%), Churn (25%), Tech (15%), Cycle (15%), ROI (15%)
    # Based on Gartner/Inverta ICP Segmentation frameworks
    def compute_icp_score(row):
        score = 0
        # NPS (0-30 pts)
        score += min(row["nps_score"] / 10 * 30, 30)
        # Churn (0-25 pts)
        score += 0 if row["churned"] else 25
        # Tech maturity (0-15 pts)
        tc = row.get("tech_class", "Hibrido")
        if tc == "Cloud/Moderno":
            score += 15
        elif tc == "Hibrido":
            score += 7
        # Sales cycle efficiency (0-15 pts) — shorter = better
        cycle = row["sales_cycle_days"]
        if cycle <= 30:
            score += 15
        elif cycle <= 50:
            score += 10
        elif cycle <= 70:
            score += 5
        # ROI / LTV-to-deal ratio (0-15 pts)
        roi = row["ltv_usd"] / row["deal_size_usd"] if row["deal_size_usd"] > 0 else 0
        if roi >= 5:
            score += 15
        elif roi >= 3:
            score += 10
        elif roi >= 1.5:
            score += 5
        return round(score, 1)

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
        "Tier 1": "#7c3aed",
        "Tier 2": "#3b82f6",
        "Tier 3": "#f59e0b",
        "Tier 4": "#ef4444",
    }
    TIER_LABELS = {
        "Tier 1": "Ideal",
        "Tier 2": "Bom",
        "Tier 3": "Arriscado",
        "Tier 4": "Evitar",
    }

    active_ltv = df[~df["churned"]]["ltv_usd"].mean()
    churned_ltv = df[df["churned"]]["ltv_usd"].mean()
    ltv_ratio = active_ltv / churned_ltv if churned_ltv > 0 else 0
    avg_roi_active = (df[~df["churned"]]["ltv_usd"] / df[~df["churned"]]["deal_size_usd"]).mean()
    avg_roi_churned = (df[df["churned"]]["ltv_usd"] / df[df["churned"]]["deal_size_usd"]).mean()
    cloud_churn = df[df["tech_class"] == "Cloud/Moderno"]["churned"].mean() * 100
    legacy_churn = df[df["tech_class"] == "Legacy/Manual"]["churned"].mean() * 100
    cloud_nps = df[df["tech_class"] == "Cloud/Moderno"]["nps_score"].mean()
    legacy_nps = df[df["tech_class"] == "Legacy/Manual"]["nps_score"].mean()
    active_age = df[~df["churned"]]["company_age"].mean()
    churned_age = df[df["churned"]]["company_age"].mean()
    active_size = df[~df["churned"]]["employee_count"].mean()
    churned_size = df[df["churned"]]["employee_count"].mean()
    best_industry = df[~df["churned"]].groupby("industry")["ltv_usd"].mean().idxmax()
    worst_churn_industry = df.groupby("industry")["churned"].mean().idxmax()
    promoters = len(df[df["nps_score"] >= 9])
    detractors = len(df[df["nps_score"] <= 6])
    nps_net = int(((promoters - detractors) / len(df)) * 100)

    cohort = df.groupby("revenue_band", observed=True).agg(
        total=("company_name", "count"),
        churned_count=("churned", "sum"),
        avg_ltv=("ltv_usd", "mean"),
        avg_nps=("nps_score", "mean"),
        avg_deal=("deal_size_usd", "mean"),
    ).reset_index()
    cohort["retention_rate"] = ((cohort["total"] - cohort["churned_count"]) / cohort["total"] * 100)
    best_cohort = cohort.loc[cohort["avg_ltv"].idxmax()]

    # ══════════════════════════════════════════════════════
    # TABBED CHART NAVIGATION
    # ══════════════════════════════════════════════════════
    st.markdown('<div class="s-header"><div class="s-icon"></div>Analise Visual</div>', unsafe_allow_html=True)

    tab_tiers, tab_health, tab_finance, tab_segment, tab_risk, tab_summary = st.tabs([
        "ICP Tiers",
        "Saude do Cliente",
        "Analise Financeira",
        "Segmentacao & Tech",
        "Risco & Cohort",
        "Resumo Executivo",
    ])

    # ── TAB 0: ICP TIERS ──
    with tab_tiers:
        # Tier summary metrics
        tier_summary = df.groupby("icp_tier").agg(
            count=("company_name", "count"),
            avg_ltv=("ltv_usd", "mean"),
            avg_nps=("nps_score", "mean"),
            avg_deal=("deal_size_usd", "mean"),
            avg_cycle=("sales_cycle_days", "mean"),
            avg_score=("icp_score", "mean"),
            churn_rate=("churned", "mean"),
            avg_revenue=("annual_revenue_usd", "mean"),
            avg_employees=("employee_count", "mean"),
        ).reset_index()
        tier_summary["churn_rate"] = tier_summary["churn_rate"] * 100
        tier_summary = tier_summary.sort_values("avg_score", ascending=False)

        # Tier cards row — one st.markdown per card to avoid truncation
        tier_cols = st.columns(len(tier_summary))
        for idx, (_, t) in enumerate(tier_summary.iterrows()):
            tier = t["icp_tier"]
            color = TIER_COLORS[tier]
            label = TIER_LABELS[tier]
            pct = t["count"] / len(df) * 100
            with tier_cols[idx]:
                st.markdown(f"""
                <div class="m-card" style="border-left: 4px solid {color};">
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                        <div style="width:10px; height:10px; border-radius:50%; background:{color};"></div>
                        <span style="font-size:0.65rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:{color};">{tier} — {label}</span>
                    </div>
                    <div class="m-value" style="color:{color};">{int(t['count'])}</div>
                    <div class="m-label">{pct:.0f}% da base</div>
                    <div style="margin-top:8px; font-size:0.7rem; color:#6b7280; line-height:1.6;">
                        Score: {t['avg_score']:.0f}/100<br>
                        LTV: ${t['avg_ltv']:,.0f}<br>
                        NPS: {t['avg_nps']:.1f} · Churn: {t['churn_rate']:.0f}%
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
                title="Distribuicao por Tier",
                height=420,
                showlegend=False,
                **neu_chart_layout,
            )
            fig_tier_donut.add_annotation(
                text=f"<b>{len(df)}</b><br>clientes",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color="#374151", family="Inter"),
            )
            st.plotly_chart(fig_tier_donut, use_container_width=True)

            st.markdown("""
            <div class="chart-explain">
                <strong>Como os Tiers sao calculados?</strong> Score composto de 0-100 baseado em 5 dimensoes:
                <div class="insight"><div class="insight-dot"></div>NPS (30%) — satisfacao do cliente</div>
                <div class="insight"><div class="insight-dot"></div>Retencao (25%) — se o cliente deu churn ou nao</div>
                <div class="insight"><div class="insight-dot"></div>Tech Stack (15%) — maturidade tecnologica (Cloud vs Legacy)</div>
                <div class="insight"><div class="insight-dot"></div>Ciclo de Vendas (15%) — eficiencia de aquisicao</div>
                <div class="insight"><div class="insight-dot"></div>ROI (15%) — LTV em relacao ao deal size</div>
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
            categories = ["NPS", "Retencao %", "LTV (norm)", "Deal Size (norm)", "Velocidade Ciclo"]

            for _, t in tier_radar_data.iterrows():
                tier = t["icp_tier"]
                retention = 100 - t["churn_rate"]
                cycle_speed = max(0, 10 - (t["avg_cycle"] / 10))  # invert: faster = higher
                values = [
                    t["avg_nps"],
                    retention / 10,
                    t["avg_ltv"] / max_ltv * 10,
                    t["avg_deal"] / max_deal * 10,
                    cycle_speed,
                ]
                fig_radar.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    name=f"{tier} — {TIER_LABELS[tier]}",
                    line=dict(color=TIER_COLORS[tier], width=2),
                    fillcolor={"Tier 1": "rgba(124,58,237,0.1)", "Tier 2": "rgba(59,130,246,0.1)", "Tier 3": "rgba(245,158,11,0.1)", "Tier 4": "rgba(239,68,68,0.1)"}[tier],
                ))

            fig_radar.update_layout(
                title="Comparacao entre Tiers (Radar)",
                height=420,
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 10], gridcolor="rgba(0,0,0,0.05)"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#6b7280", size=11),
                title_font=dict(size=13, color="#374151", family="Inter"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=10)),
                margin=dict(l=40, r=40, t=60, b=40),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

            st.markdown("""
            <div class="chart-explain">
                <strong>O que estou vendo?</strong> Comparacao multi-dimensional entre tiers. Quanto maior a area, melhor o perfil.
                <div class="insight"><div class="insight-dot"></div>Tier 1 deve dominar em todas as dimensoes — e o formato ideal de cliente.</div>
                <div class="insight"><div class="insight-dot"></div>Gaps entre tiers revelam onde clientes de menor tier falham (ex: tech legado, ciclo longo).</div>
            </div>
            """, unsafe_allow_html=True)

        # Tier metrics comparison bar charts
        tt2_col1, tt2_col2 = st.columns(2)

        with tt2_col1:
            fig_tier_ltv = px.bar(
                tier_summary, x="icp_tier", y="avg_ltv",
                color="icp_tier", color_discrete_map=TIER_COLORS,
                title="LTV Medio por Tier",
                labels={"icp_tier": "Tier", "avg_ltv": "LTV Medio (USD)"},
                text=tier_summary["avg_ltv"].apply(lambda x: f"${x:,.0f}"),
            )
            fig_tier_ltv.update_layout(height=350, showlegend=False, **neu_chart_layout)
            fig_tier_ltv.update_traces(textposition="outside")
            st.plotly_chart(fig_tier_ltv, use_container_width=True)

        with tt2_col2:
            fig_tier_cycle = px.bar(
                tier_summary, x="icp_tier", y="avg_cycle",
                color="icp_tier", color_discrete_map=TIER_COLORS,
                title="Ciclo Medio por Tier (dias)",
                labels={"icp_tier": "Tier", "avg_cycle": "Ciclo (dias)"},
                text=tier_summary["avg_cycle"].apply(lambda x: f"{x:.0f}d"),
            )
            fig_tier_cycle.update_layout(height=350, showlegend=False, **neu_chart_layout)
            fig_tier_cycle.update_traces(textposition="outside")
            st.plotly_chart(fig_tier_cycle, use_container_width=True)

        # Client list by tier
        st.markdown('<div class="s-header"><div class="s-icon"></div>Clientes por Tier</div>', unsafe_allow_html=True)

        for tier in ["Tier 1", "Tier 2", "Tier 3", "Tier 4"]:
            tier_df = df[df["icp_tier"] == tier].sort_values("icp_score", ascending=False)
            if len(tier_df) == 0:
                continue
            color = TIER_COLORS[tier]
            label = TIER_LABELS[tier]

            with st.expander(f"{tier} — {label} ({len(tier_df)} clientes)", expanded=(tier == "Tier 1")):
                for _, row in tier_df.iterrows():
                    roi = row["ltv_usd"] / row["deal_size_usd"] if row["deal_size_usd"] > 0 else 0
                    status_text = "CHURNED" if row["churned"] else "ATIVO"
                    status_color = "#ef4444" if row["churned"] else "#22c55e"
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:12px;padding:12px 16px;margin-bottom:6px;'
                        f'background:linear-gradient(145deg,var(--neu-bg),var(--neu-bg2));'
                        f'box-shadow:3px 3px 6px var(--neu-dark),-3px -3px 6px var(--neu-light);'
                        f'border-radius:14px;border-left:3px solid {color};">'
                        f'<div style="flex:1;"><div style="font-weight:600;color:#1f2937;font-size:0.85rem;">{row["company_name"]}</div>'
                        f'<div style="font-size:0.7rem;color:#9ca3af;">{row["industry"]} · {row["employee_count"]:,} func · {row["tech_class"]}</div></div>'
                        f'<div style="text-align:right;font-size:0.75rem;color:#6b7280;line-height:1.5;">'
                        f'Score: <span style="font-weight:700;color:{color};">{row["icp_score"]:.0f}</span> · NPS {row["nps_score"]} · {row["sales_cycle_days"]}d<br>'
                        f'LTV ${row["ltv_usd"]:,.0f} · ROI {roi:.1f}x · <span style="color:{status_color};font-weight:600;">{status_text}</span>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )

        # Tier methodology note
        st.markdown("""
        <div class="chart-explain" style="margin-top:1rem;">
            <strong>Metodologia de Tiering</strong> — Baseada nos frameworks de Gartner, Inverta (4 Levels of ICP Segmentation) e DataBees (Account Tiering).
            <div class="insight"><div class="insight-dot"></div>Tier 1 (85+): Top 10-15% — clientes ideais que merecem tratamento high-touch e ABM personalizado.</div>
            <div class="insight"><div class="insight-dot"></div>Tier 2 (65-84): Clientes bons com campanhas semi-personalizadas e processos padronizados.</div>
            <div class="insight"><div class="insight-dot"></div>Tier 3 (40-64): Sinais mistos — nurture ate amadurecerem ou descarte se nao evoluirem.</div>
            <div class="insight"><div class="insight-dot"></div>Tier 4 (&lt;40): Anti-ICP — evitar investimento, redirecionar recursos para tiers superiores.</div>
        </div>
        """, unsafe_allow_html=True)

    # ── TAB 1: Client Health ──
    with tab_health:
        th_col1, th_col2 = st.columns(2)

        with th_col1:
            df_health = df.copy()
            ltv_min_display = df["ltv_usd"].max() * 0.06
            df_health["ltv_display"] = df_health["ltv_usd"].clip(lower=ltv_min_display)

            fig_health = px.scatter(
                df_health, x="sales_cycle_days", y="nps_score",
                size="ltv_display", color="churned",
                color_discrete_map=colors_churn,
                hover_name="company_name",
                hover_data={"ltv_usd": ":$,.0f", "ltv_display": False},
                title="Matriz de Saude do Cliente",
                labels={"sales_cycle_days": "Ciclo de Vendas (dias)", "nps_score": "NPS Score", "churned": "Churned"},
                size_max=40,
            )
            fig_health.update_traces(marker=dict(sizemin=10))
            fig_health.add_hline(y=6.5, line_dash="dot", line_color="rgba(0,0,0,0.15)")
            fig_health.add_vline(x=50, line_dash="dot", line_color="rgba(0,0,0,0.15)")
            fig_health.add_annotation(x=25, y=9.5, text="Ideal", showarrow=False,
                                      font=dict(size=10, color="#7c3aed", family="Inter"), opacity=0.6)
            fig_health.add_annotation(x=80, y=9.5, text="Lento mas leal", showarrow=False,
                                      font=dict(size=10, color="#f59e0b", family="Inter"), opacity=0.6)
            fig_health.add_annotation(x=25, y=2.5, text="Rapido mas insatisfeito", showarrow=False,
                                      font=dict(size=10, color="#f59e0b", family="Inter"), opacity=0.6)
            fig_health.add_annotation(x=80, y=2.5, text="Zona de Perigo", showarrow=False,
                                      font=dict(size=10, color="#ef4444", family="Inter"), opacity=0.6)
            fig_health.update_layout(height=480, **neu_chart_layout)
            st.plotly_chart(fig_health, use_container_width=True)

            st.markdown("""
            <div class="chart-explain">
                <strong>O que estou vendo?</strong> Cada bolha e um cliente. Eixo X = ciclo de vendas, Y = NPS, tamanho = LTV.
                <div class="insight"><div class="insight-dot"></div>Quadrante superior esquerdo = perfil ideal (ciclo curto + NPS alto).</div>
                <div class="insight"><div class="insight-dot"></div>Quadrante inferior direito = zona de perigo (ciclo longo + NPS baixo).</div>
                <div class="insight"><div class="insight-dot"></div>Bolhas vermelhas sao churned — note a concentracao na zona de perigo.</div>
            </div>
            """, unsafe_allow_html=True)

        with th_col2:
            fig_nps = go.Figure()
            fig_nps.add_trace(go.Histogram(
                x=df[~df["churned"]]["nps_score"], name="Ativos", marker_color="#7c3aed",
                opacity=0.8, xbins=dict(start=0, end=11, size=1)
            ))
            fig_nps.add_trace(go.Histogram(
                x=df[df["churned"]]["nps_score"], name="Churned", marker_color="#ef4444",
                opacity=0.8, xbins=dict(start=0, end=11, size=1)
            ))
            fig_nps.add_vrect(x0=0, x1=6.5, fillcolor="rgba(239,68,68,0.05)", line_width=0)
            fig_nps.add_vrect(x0=6.5, x1=8.5, fillcolor="rgba(245,158,11,0.05)", line_width=0)
            fig_nps.add_vrect(x0=8.5, x1=11, fillcolor="rgba(124,58,237,0.05)", line_width=0)
            fig_nps.add_annotation(x=3, y=1, yref="paper", yanchor="top", text="Detratores",
                                   showarrow=False, font=dict(size=9, color="#ef4444"))
            fig_nps.add_annotation(x=7.5, y=1, yref="paper", yanchor="top", text="Neutros",
                                   showarrow=False, font=dict(size=9, color="#f59e0b"))
            fig_nps.add_annotation(x=9.5, y=1, yref="paper", yanchor="top", text="Promotores",
                                   showarrow=False, font=dict(size=9, color="#7c3aed"))
            fig_nps.update_layout(
                title="Distribuicao de NPS", barmode="overlay", height=480,
                xaxis_title="NPS Score", yaxis_title="Quantidade", **neu_chart_layout,
            )
            st.plotly_chart(fig_nps, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                <strong>O que estou vendo?</strong> Distribuicao NPS separada por status (ativo vs churned).
                <div class="insight"><div class="insight-dot"></div>NPS Net Score: {nps_net} — % Promotores (9-10) menos % Detratores (0-6).</div>
                <div class="insight"><div class="insight-dot"></div>{promoters} promotores e {detractors} detratores na base.</div>
                <div class="insight"><div class="insight-dot"></div>Clientes churned se concentram na faixa de detratores — NPS baixo e forte preditor de churn.</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 2: Financial Analysis ──
    with tab_finance:
        tf_col1, tf_col2 = st.columns(2)

        with tf_col1:
            fig_ltv = px.bar(
                df.sort_values("ltv_usd", ascending=True),
                x="ltv_usd", y="company_name", orientation="h",
                color="churned", color_discrete_map=colors_churn,
                title="LTV por Cliente",
                labels={"ltv_usd": "LTV (USD)", "company_name": "", "churned": "Churned"},
            )
            fig_ltv.update_layout(height=520, **neu_chart_layout)
            fig_ltv.update_traces(marker_line_width=0)
            st.plotly_chart(fig_ltv, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                <strong>O que estou vendo?</strong> LTV de cada cliente, ordenado de menor para maior.
                <div class="insight"><div class="insight-dot"></div>LTV medio ativos: ${active_ltv:,.0f} vs churned: ${churned_ltv:,.0f} — diferenca de {ltv_ratio:.0f}x.</div>
                <div class="insight"><div class="insight-dot"></div>Churned = LTV igual ao deal (1x). Ativos alcancam 3-6x o contrato.</div>
                <div class="insight"><div class="insight-dot"></div>Reter clientes bons gera muito mais valor que adquirir perfis errados.</div>
            </div>
            """, unsafe_allow_html=True)

        with tf_col2:
            fig_roi = px.scatter(
                df, x="deal_size_usd", y="ltv_usd",
                color="churned", color_discrete_map=colors_churn,
                hover_name="company_name", size="employee_count",
                title="Deal Size vs LTV (Retorno do Cliente)",
                labels={"deal_size_usd": "Deal Size (USD)", "ltv_usd": "LTV (USD)", "churned": "Churned"},
            )
            max_deal = df["deal_size_usd"].max()
            for mult, label in [(1, "1x"), (3, "3x"), (5, "5x")]:
                fig_roi.add_trace(go.Scatter(
                    x=[0, max_deal], y=[0, max_deal * mult],
                    mode="lines", line=dict(dash="dot", color="rgba(0,0,0,0.1)", width=1),
                    showlegend=False, hoverinfo="skip"
                ))
                fig_roi.add_annotation(x=max_deal * 0.95, y=max_deal * mult * 0.95,
                                       text=f"{label} ROI", showarrow=False,
                                       font=dict(size=9, color="#9ca3af"))
            fig_roi.update_layout(height=520, **neu_chart_layout)
            st.plotly_chart(fig_roi, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                <strong>O que estou vendo?</strong> Deal inicial vs LTV total. Linhas tracejadas = multiplos de ROI.
                <div class="insight"><div class="insight-dot"></div>Ativos geram {avg_roi_active:.1f}x o contrato. Churned ficam em {avg_roi_churned:.1f}x.</div>
                <div class="insight"><div class="insight-dot"></div>Acima da linha 1x = lucro. Clientes bons ficam entre 3x e 6x.</div>
                <div class="insight"><div class="insight-dot"></div>Tamanho das bolhas = porte (funcionarios).</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 3: Segmentation & Tech ──
    with tab_segment:
        ts_col1, ts_col2 = st.columns(2)

        with ts_col1:
            industry_data = df.groupby(["industry", "churned"]).size().reset_index(name="count")
            industry_data["status"] = industry_data["churned"].map({True: "Churned", False: "Ativo"})

            fig_industry = px.sunburst(
                industry_data, path=["status", "industry"], values="count",
                color="status", color_discrete_map={"Ativo": "#7c3aed", "Churned": "#ef4444"},
                title="Distribuicao por Status e Industria",
            )
            fig_industry.update_layout(height=480, **neu_chart_layout)
            fig_industry.update_traces(
                textinfo="label+percent parent",
                insidetextorientation="radial",
                marker=dict(line=dict(color="#e6e9ef", width=2)),
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
                <strong>O que estou vendo?</strong> Anel interno: Ativo/Churned. Anel externo: industrias. Clique para expandir.
                <div class="insight"><div class="insight-dot"></div>Top 3 industrias por LTV (ativos):</div>
                {top3_items}
                <div class="insight"><div class="insight-dot"></div>Industrias concentradas no vermelho sao segmentos problematicos.</div>
            </div>
            """, unsafe_allow_html=True)

        with ts_col2:
            tech_summary = df.groupby(["tech_class", "churned"]).agg(
                count=("company_name", "count"),
            ).reset_index()
            tech_summary["status"] = tech_summary["churned"].map({True: "Churned", False: "Ativo"})

            fig_tech = px.bar(
                tech_summary, x="tech_class", y="count",
                color="status", barmode="group",
                color_discrete_map={"Ativo": "#7c3aed", "Churned": "#ef4444"},
                title="Maturidade Tecnologica vs Retencao",
                labels={"tech_class": "Tech Stack", "count": "Clientes", "status": "Status"},
            )
            fig_tech.update_layout(height=480, **neu_chart_layout)
            st.plotly_chart(fig_tech, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                <strong>O que estou vendo?</strong> Clientes Cloud vs Legacy e impacto na retencao.
                <div class="insight"><div class="insight-dot"></div>Churn: Cloud {cloud_churn:.0f}% vs Legacy {legacy_churn:.0f}%.</div>
                <div class="insight"><div class="insight-dot"></div>NPS: Cloud {cloud_nps:.1f} vs Legacy {legacy_nps:.1f}.</div>
                <div class="insight"><div class="insight-dot"></div>Empresas com stack moderno sao muito melhores clientes — sinal forte de ICP.</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 4: Risk & Cohort ──
    with tab_risk:
        tr_col1, tr_col2 = st.columns(2)

        with tr_col1:
            fig_cohort = go.Figure()
            fig_cohort.add_trace(go.Bar(
                x=cohort["revenue_band"], y=cohort["avg_ltv"],
                name="LTV Medio", marker_color="#7c3aed", yaxis="y",
            ))
            fig_cohort.add_trace(go.Scatter(
                x=cohort["revenue_band"], y=cohort["retention_rate"],
                name="Retencao %", mode="lines+markers",
                line=dict(color="#22c55e", width=3), marker=dict(size=8), yaxis="y2",
            ))
            fig_cohort.update_layout(
                title="Cohort por Faixa de Receita", height=480,
                yaxis=dict(title="LTV Medio (USD)", gridcolor="rgba(0,0,0,0.05)"),
                yaxis2=dict(title="Retencao %", overlaying="y", side="right", range=[0, 110], gridcolor="rgba(0,0,0,0)"),
                xaxis=dict(title="Faixa de Receita Anual", gridcolor="rgba(0,0,0,0.05)"),
                template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#6b7280", size=11),
                title_font=dict(size=13, color="#374151", family="Inter"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
                margin=dict(l=0, r=40, t=40, b=0),
            )
            st.plotly_chart(fig_cohort, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                <strong>O que estou vendo?</strong> LTV medio (barras) e retencao (linha verde) por faixa de receita.
                <div class="insight"><div class="insight-dot"></div>Melhor faixa: {best_cohort['revenue_band']} — LTV ${best_cohort['avg_ltv']:,.0f}, retencao {best_cohort['retention_rate']:.0f}%.</div>
                <div class="insight"><div class="insight-dot"></div>Revela o "sweet spot" de porte do cliente ideal.</div>
                <div class="insight"><div class="insight-dot"></div>Retencao abaixo de 70% = sinal de anti-ICP naquela faixa.</div>
            </div>
            """, unsafe_allow_html=True)

        with tr_col2:
            fig_age = px.scatter(
                df, x="company_age", y="employee_count",
                color="churned", color_discrete_map=colors_churn,
                size="deal_size_usd", hover_name="company_name",
                title="Idade vs Porte da Empresa",
                labels={"company_age": "Idade (anos)", "employee_count": "Funcionarios", "churned": "Churned"},
            )
            fig_age.update_layout(height=480, **neu_chart_layout)
            st.plotly_chart(fig_age, use_container_width=True)

            st.markdown(f"""
            <div class="chart-explain">
                <strong>O que estou vendo?</strong> Idade e porte dos clientes. Tamanho = deal size.
                <div class="insight"><div class="insight-dot"></div>Ativos: media {active_age:.0f} anos, {active_size:.0f} funcionarios.</div>
                <div class="insight"><div class="insight-dot"></div>Churned: media {churned_age:.0f} anos, {churned_size:.0f} funcionarios.</div>
                <div class="insight"><div class="insight-dot"></div>Empresas muito jovens ou pequenas tendem a dar mais churn.</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 5: Executive Summary ──
    with tab_summary:
        best_nps_company = df.loc[df["nps_score"].idxmax(), "company_name"]
        top_ltv_company = df.loc[df["ltv_usd"].idxmax(), "company_name"]
        top_ltv_val = df["ltv_usd"].max()

        st.markdown(f"""
        <div class="company-card">
            <div class="cc-section-title">Descobertas Principais</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>Melhor industria: {best_industry} — maior LTV medio entre ativos</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>Industria de maior risco: {worst_churn_industry} — maior taxa de churn</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>Cliente mais satisfeito: {best_nps_company} (NPS {df['nps_score'].max()})</div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="cc-list-item"><div class="cc-bullet"></div>Maior LTV: {top_ltv_company} (${top_ltv_val:,.0f})</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>Tech stack e preditor: Cloud tem {legacy_churn - cloud_churn:.0f}pp menos churn que Legacy</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>ROI medio: Ativos geram {avg_roi_active:.1f}x o contrato vs {avg_roi_churned:.1f}x dos churned</div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="cc-section-title" style="margin-top:1.25rem;">Recomendacoes</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>Priorize prospects da industria {best_industry} com stack Cloud/Moderno</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>Evite empresas com menos de {int(churned_size)} funcionarios e stack legado</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>Foco na faixa de receita {best_cohort['revenue_band']} — melhor retencao e LTV</div>
            <div class="cc-list-item"><div class="cc-bullet"></div>Investir em onboarding rapido — ciclos acima de 50 dias correlacionam com churn</div>
        </div>
        """, unsafe_allow_html=True)

    # ── ICP Button ──
    st.markdown('<div class="s-header"><div class="s-icon"></div>Gerar Perfil de Cliente Ideal</div>', unsafe_allow_html=True)

    if st.button("Gerar ICP com IA", type="primary", use_container_width=True):
        if not api_key:
            st.error("Configure GROQ_API_KEY no arquivo .env")
        else:
            with st.spinner("Analisando padroes..."):
                icp = analyze_customers(df, api_key)
                st.session_state["icp"] = icp

    if "icp" in st.session_state:
        icp = st.session_state["icp"]
        col_icp, col_anti = st.columns(2)

        with col_icp:
            st.markdown(f"""
            <div class="icp-card positive">
                <div class="card-badge">Ideal Customer Profile</div>
                <h2>Cliente Ideal</h2>
                <p>{icp.summary}</p>
            </div>
            """, unsafe_allow_html=True)

            # Industries
            st.markdown('<div class="detail-group"><div class="dg-title">Industrias Ideais</div>', unsafe_allow_html=True)
            for ind in icp.ideal_industries:
                st.markdown(f'<div class="detail-item"><div class="di-dot"></div>{ind}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Profile
            st.markdown(f"""
            <div class="detail-group">
                <div class="dg-title">Perfil</div>
                <div class="detail-item"><div class="di-dot"></div>Funcionarios: {icp.ideal_employee_range}</div>
                <div class="detail-item"><div class="di-dot"></div>Receita: {icp.ideal_revenue_range}</div>
                <div class="detail-item"><div class="di-dot"></div>Idade: {icp.ideal_company_age}</div>
            </div>
            """, unsafe_allow_html=True)

            # Tech
            st.markdown('<div class="detail-group"><div class="dg-title">Sinais Tecnologicos</div>', unsafe_allow_html=True)
            for sig in icp.ideal_tech_signals:
                st.markdown(f'<div class="detail-item"><div class="di-dot"></div>{sig}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Key patterns
            st.markdown('<div class="detail-group"><div class="dg-title">Padroes-chave</div>', unsafe_allow_html=True)
            pills = "".join(f'<span class="pattern-pill">{p}</span>' for p in icp.key_patterns)
            st.markdown(pills, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_anti:
            st.markdown(f"""
            <div class="icp-card negative">
                <div class="card-badge">Anti-ICP</div>
                <h2>Perfil a Evitar</h2>
                <p>{icp.anti_icp_summary}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="detail-group"><div class="dg-title" style="color:#ef4444;">Sinais de Alerta</div>', unsafe_allow_html=True)
            for sig in icp.anti_icp_signals:
                st.markdown(f'<div class="alert-item"><div class="alert-dot"></div>{sig}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Scoring ──
        st.markdown('<div class="s-header"><div class="s-icon"></div>Scoring de Prospects</div>', unsafe_allow_html=True)

        if prospects_file:
            prospects_df = pd.read_csv(prospects_file)
        else:
            st.info("Nenhum CSV de prospects enviado. Usando clientes atuais para demonstracao.")
            prospects_df = df.copy()

        if st.button("Pontuar Prospects", type="primary", use_container_width=True):
            with st.spinner("Pontuando prospects..."):
                scored = score_prospects(icp, prospects_df, api_key)
                st.session_state["scored"] = scored

        if "scored" in st.session_state:
            scored = st.session_state["scored"]
            scored_df = pd.DataFrame([s.model_dump() for s in scored])
            scored_df = scored_df.sort_values("score", ascending=False)

            # Chart
            colors_rec = {"hot": "#7c3aed", "warm": "#f59e0b", "cold": "#9ca3af", "avoid": "#ef4444"}
            fig_scores = px.bar(
                scored_df, x="company_name", y="score",
                color="recommendation", color_discrete_map=colors_rec,
                title="Ranking de Prospects",
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
                    <div class="sr-name">{row['company_name']}</div>
                    <div class="sr-score {rec}">{row['score']}</div>
                    <div class="sr-badge {rec}">{rec}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            for _, row in scored_df.iterrows():
                with st.expander(f"{row['company_name']} — Detalhes"):
                    fit_col, risk_col = st.columns(2)
                    with fit_col:
                        st.markdown("**Fit**")
                        for r in row["fit_reasons"]:
                            st.markdown(f"- {r}")
                    with risk_col:
                        if row["risk_flags"]:
                            st.markdown("**Riscos**")
                            for r in row["risk_flags"]:
                                st.markdown(f"- {r}")
else:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">&#127919;</div>
        <div style="font-size: 1.15rem; color: #374151; font-weight: 600; margin-bottom: 0.5rem;">
            Selecione uma empresa pre-carregada ou faca upload de um CSV
        </div>
        <div style="color: #9ca3af; font-size: 0.9rem;">
            Use o menu lateral para escolher uma das 5 empresas com dados completos
        </div>
    </div>
    """, unsafe_allow_html=True)

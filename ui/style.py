"""Shared look: page CSS, header, cards and badges. Colors match .streamlit/config.toml."""

import html

import streamlit as st

ACCENT = "#2346F9"
INK = "#14161C"
MUTED = "#6E6E76"
LINE = "#E6E8EE"
SOFT = "#F5F7FA"
CATEGORY_COLORS = {"Financial Pressure": "#14161C", "Commercial Opportunity": "#2346F9",
                   "Growth Catalysts": "#0099FF"}
CONFIDENCE_TONE = {"High": "green", "Medium": "blue", "Low": "orange", "Insufficient data": "gray"}

CSS = f"""
<style>
.block-container {{padding-top: 2.2rem; max-width: 1400px;}}
h1, h2, h3 {{letter-spacing: -0.02em;}}
.hero {{border-bottom: 1px solid {LINE}; padding-bottom: 1.1rem; margin-bottom: 1.2rem;}}
.hero .eyebrow {{font-size: 0.78rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
                 color: {ACCENT}; margin-bottom: 0.35rem;}}
.hero h1 {{font-size: 2.1rem; line-height: 1.15; margin: 0; padding: 0;}}
.hero .sub {{color: {MUTED}; font-size: 1rem; margin-top: 0.45rem; max-width: 60rem;}}
.card {{border: 1px solid {LINE}; border-radius: 0.8rem; padding: 1rem 1.1rem; background: #fff; height: 100%;}}
.card .label {{font-size: 0.78rem; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.06em;
               font-weight: 600;}}
.card .value {{font-size: 1.7rem; font-weight: 650; color: {INK}; letter-spacing: -0.02em; margin-top: 0.15rem;}}
.card .note {{font-size: 0.85rem; color: {MUTED}; margin-top: 0.2rem;}}
.pick {{border: 1px solid {LINE}; border-radius: 0.8rem; padding: 1rem 1.1rem; background: #fff; height: 100%;}}
.pick .rank {{font-size: 0.8rem; font-weight: 600; color: {ACCENT};}}
.pick .name {{font-size: 1.15rem; font-weight: 650; color: {INK}; margin: 0.1rem 0 0.35rem;}}
.pick .tier {{font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
             color: {ACCENT}; margin-top: 0.35rem;}}
.pick .index {{font-size: 0.86rem; color: {MUTED}; font-weight: 500;}}
.pick .why {{font-size: 0.86rem; color: {MUTED}; margin-top: 0.5rem; line-height: 1.4;}}
.bar {{height: 6px; background: {SOFT}; border-radius: 3px; margin-top: 0.6rem; overflow: hidden;}}
.bar > div {{height: 100%; background: {ACCENT}; border-radius: 3px;}}
.badge {{display: inline-block; font-size: 0.72rem; font-weight: 600; padding: 0.15rem 0.5rem;
         border-radius: 999px; margin-right: 0.3rem; border: 1px solid {LINE}; color: {INK}; background: {SOFT};}}
.badge.accent {{background: {ACCENT}; color: #fff; border-color: {ACCENT};}}
.footer {{color: {MUTED}; font-size: 0.8rem; border-top: 1px solid {LINE}; margin-top: 2.5rem; padding-top: 0.8rem;}}
[data-testid="stSidebarNav"] a span {{font-weight: 500;}}
</style>
"""


def apply():
    st.html(CSS)


def esc(text):
    return html.escape(str(text))


def hero(eyebrow, title, subtitle=""):
    st.html(f'<div class="hero"><div class="eyebrow">{esc(eyebrow)}</div><h1>{esc(title)}</h1>'
            + (f'<div class="sub">{esc(subtitle)}</div>' if subtitle else "") + "</div>")


def card(label, value, note=""):
    return (f'<div class="card"><div class="label">{esc(label)}</div><div class="value">{esc(value)}</div>'
            + (f'<div class="note">{esc(note)}</div>' if note else "") + "</div>")


def cards(items):
    """Row of KPI cards from (label, value, note) tuples."""
    for col, item in zip(st.columns(len(items)), items):
        col.html(card(*item))


def badges(*items):
    """items: text or (text, 'accent')."""
    out = []
    for item in items:
        text, kind = item if isinstance(item, tuple) else (item, "")
        out.append(f'<span class="badge {kind}">{esc(text)}</span>')
    return "".join(out)


def footer():
    st.html('<div class="footer">FY2025 NCAA financial data (Knight–Newhouse College Athletics Database, credited; '
            "schools' own reports where published) · 2024–25 attendance · research verified by a person before "
            "it is scored · Independent analysis prepared by Tucker Harrell. Not affiliated with any school or "
            "company named.</div>")

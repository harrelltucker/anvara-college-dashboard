"""Shared look: page CSS, header, cards and badges. Colors match .streamlit/config.toml."""

import html

import streamlit as st

ACCENT = "#6A4BF0"
NAVY = "#141A3D"
TINT = "#F4F1FF"
# Opportunity tiers: one purple, dark (best) to light, so the order reads without a legend
TIER_COLORS = {"Top opportunity": "#3B1FA8", "Strong": "#6A4BF0", "Moderate": "#A592F7", "Lower": "#D6CCFC"}
TIER_NOTES = {"Top opportunity": "top 10%", "Strong": "next 20%", "Moderate": "middle 40%", "Lower": "bottom 30%"}
INK = "#14161C"
MUTED = "#6E6E76"
LINE = "#E6E8EE"
SOFT = "#F5F7FA"
CATEGORY_COLORS = {"Financial Pressure": "#14161C", "Commercial Opportunity": "#6A4BF0",
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
.section {{font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: {MUTED};
           margin: 1.6rem 0 0.7rem;}}
.opp {{border: 1px solid {LINE}; border-radius: 0.9rem; padding: 1.1rem 1.2rem 0.6rem; background: #fff;
       box-shadow: 0 1px 2px rgba(20, 22, 28, 0.04);}}
.opp-rank {{font-size: 0.8rem; font-weight: 700; color: {ACCENT};}}
.opp-name {{font-size: 1.3rem; font-weight: 700; color: {INK}; letter-spacing: -0.02em; margin-top: 0.1rem;}}
.opp-meta {{font-size: 0.84rem; color: {MUTED}; margin-bottom: 0.6rem;}}
.opp-why, .why-list {{margin: 0; padding-left: 1.1rem; color: {INK}; font-size: 0.9rem; line-height: 1.45;}}
.opp-why li, .why-list li {{margin-bottom: 0.35rem;}}
.why-list {{font-size: 1rem;}}
.meter {{margin-bottom: 0.85rem;}}
.meter .top {{display: flex; justify-content: space-between; font-size: 0.92rem; font-weight: 600; color: {INK};}}
.meter .top span:last-child {{font-variant-numeric: tabular-nums;}}
.meter .track {{height: 8px; background: {SOFT}; border-radius: 4px; margin: 0.3rem 0 0.2rem; overflow: hidden;}}
.meter .track > div {{height: 100%; background: {ACCENT}; border-radius: 4px;}}
.meter .what {{font-size: 0.8rem; color: {MUTED};}}
@media (max-width: 640px) {{.opp {{min-height: 0 !important;}}}}
.fine {{font-size: 0.78rem; color: {MUTED}; margin-top: 0.4rem;}}
</style>
"""

# Public copy: equal-height card grids, clickable school cards, stat strip, callouts
PUBLIC_CSS = f"""
<style>
.hero {{border-bottom: 0; padding: 1.8rem 2rem 1.6rem; margin-bottom: 1.4rem; border-radius: 1.1rem;
        background: linear-gradient(135deg, {TINT} 0%, #FFFFFF 70%); border: 1px solid {LINE};}}
.hero h1 {{font-size: 2.4rem;}}
.stats {{display: flex; flex-wrap: wrap; gap: 0.6rem 2.2rem; margin-top: 1.2rem;}}
.stats div {{font-size: 0.82rem; color: {MUTED};}}
.stats b {{display: block; font-size: 1.35rem; font-weight: 700; color: {INK}; letter-spacing: -0.02em;}}
.grid {{display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(min(var(--min, 300px), 100%), 1fr));}}
.grid > .card {{height: auto;}}
a.opp-card {{display: flex; flex-direction: column; text-decoration: none !important; color: {INK} !important;
            border: 1px solid {LINE}; border-radius: 1rem; padding: 1.15rem 1.25rem 1rem; background: #fff;
            box-shadow: 0 1px 2px rgba(20, 22, 28, 0.04); transition: border-color .15s, box-shadow .15s, transform .15s;}}
a.opp-card:hover {{border-color: {ACCENT}; box-shadow: 0 8px 24px rgba(106, 75, 240, 0.12); transform: translateY(-2px);}}
.opp-head {{display: flex; align-items: baseline; justify-content: space-between; gap: 0.5rem;}}
.opp-num {{font-size: 2rem; font-weight: 750; color: {ACCENT}; letter-spacing: -0.04em; line-height: 1;}}
.pill {{display: inline-block; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
        padding: 0.2rem 0.55rem; border-radius: 999px; background: #EFEBFF; color: {ACCENT}; white-space: nowrap;}}
.pill.strong {{background: {SOFT}; color: {INK};}}
.pill.quiet {{background: {SOFT}; color: {MUTED};}}
a.opp-card .opp-name {{margin-top: 0.7rem;}}
a.opp-card .opp-meta {{margin-bottom: 0.8rem; padding-bottom: 0.8rem; border-bottom: 1px solid {LINE};}}
.ticks {{list-style: none; margin: 0 !important; padding: 0 !important; font-size: 0.9rem; line-height: 1.45; flex: 1;}}
.ticks li {{position: relative; padding-left: 1.2rem; margin: 0 0 0.5rem !important;}}
.ticks li::before {{content: ""; position: absolute; left: 0.1rem; top: 0.5em; width: 0.42rem; height: 0.42rem;
                    border-radius: 50%; background: {ACCENT};}}
.ticks, .timeline {{padding-inline-start: 0 !important;}}
.ticks li, .timeline li {{margin-left: 0 !important;}}
.opp-go {{font-size: 0.86rem; font-weight: 600; color: {ACCENT}; margin-top: 0.4rem;}}
.callout {{border-radius: 1rem; background: {TINT}; padding: 1.1rem 1.3rem 0.7rem; border-left: 4px solid {ACCENT};}}
.callout .ticks {{font-size: 1rem;}}
.rank-tile {{text-align: right;}}
.rank-tile .big {{font-size: 3rem; font-weight: 750; color: {ACCENT}; letter-spacing: -0.05em; line-height: 1;}}
.rank-tile .of {{font-size: 0.85rem; color: {MUTED}; margin-top: 0.3rem;}}
.hero-row {{display: flex; justify-content: space-between; align-items: flex-end; gap: 1.5rem; flex-wrap: wrap;}}
.weight {{font-size: 2.2rem; font-weight: 750; color: {ACCENT}; letter-spacing: -0.04em; line-height: 1.1;
          margin: 0.2rem 0 0.4rem;}}
.timeline {{list-style: none; margin: 0 0 0 0.4rem !important; padding: 0 !important; border-left: 2px solid {LINE};}}
.timeline li {{position: relative; padding: 0 0 0.9rem 1.2rem; font-size: 0.95rem; line-height: 1.45;}}
.timeline li::before {{content: ""; position: absolute; left: -0.36rem; top: 0.4em; width: 0.6rem; height: 0.6rem;
                       border-radius: 50%; background: #fff; border: 2px solid {ACCENT};}}
.timeline .when {{display: block; font-size: 0.78rem; font-weight: 600; color: {MUTED}; letter-spacing: 0.03em;}}
.timeline a {{color: {ACCENT}; text-decoration: none; font-size: 0.85rem;}}
@media (max-width: 640px) {{
  .hero {{padding: 1.3rem 1.1rem 1.2rem;}}
  .hero h1 {{font-size: 1.9rem;}}
  .rank-tile {{text-align: left;}}
}}
/* Dashboard: navy header bar, white panels, KPI tiles, takeaways */
[data-testid="stMain"], [data-testid="stAppViewContainer"] {{overflow-x: hidden;}}
header[data-testid="stHeader"] {{background: {NAVY};}}
header[data-testid="stHeader"] a, header[data-testid="stHeader"] a * {{color: #DADCF0 !important;}}
header[data-testid="stHeader"] a[aria-current="page"], header[data-testid="stHeader"] a:hover {{background: rgba(255,255,255,0.10) !important;}}
header[data-testid="stHeader"] a[aria-current="page"] * {{color: #fff !important;}}
header[data-testid="stHeader"] button, header[data-testid="stHeader"] button * {{color: #fff !important;}}
.block-container {{padding-top: 3.75rem !important;}}
.st-key-topbar {{background: {NAVY}; width: 100vw !important; max-width: none !important; box-sizing: border-box;
                 margin: 0 0 0.6rem calc(50% - 50vw); padding: 0.3rem calc(50vw - 50%) 1.1rem;}}
.st-key-topbar label p {{color: #C9CCE6 !important; font-weight: 600;}}
.st-key-topbar [data-baseweb="select"] > div {{background: #222A5A; border-color: #39417A; border-radius: 0.55rem;}}
.st-key-topbar [data-baseweb="select"] * {{color: #fff !important;}}
.st-key-topbar [data-baseweb="select"] svg {{fill: #fff;}}
.brand {{display: flex; align-items: center; gap: 0.65rem; color: #fff;}}
.brand .mark {{width: 2.1rem; height: 2.1rem; border-radius: 0.6rem; flex: none;
               background: linear-gradient(140deg, #8C73FF, {ACCENT} 60%, #3B1FA8);}}
.brand .for {{font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase; color: #A9ADD3;}}
.brand .name {{font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1;}}
.bar-title {{color: #fff; font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.2;}}
.bar-sub {{color: #B9BCDD; font-size: 0.92rem; margin-top: 0.15rem;}}
.kpi {{border: 1px solid {LINE}; border-radius: 0.9rem; background: #fff; padding: 0.9rem 1.1rem;
       box-shadow: 0 1px 2px rgba(20, 22, 28, 0.04);}}
.kpi .v {{font-size: 1.9rem; font-weight: 750; letter-spacing: -0.03em; color: {INK}; line-height: 1.15;}}
.kpi .v svg {{width: 1.3rem; height: 1.3rem; margin-right: 0.35rem; vertical-align: -0.05em;}}
.kpi .k {{font-size: 0.95rem; color: {INK}; margin-top: 0.1rem;}}
.kpi .n {{font-size: 0.8rem; color: {MUTED}; margin-top: 0.2rem;}}
.panel-title {{font-size: 1.2rem; font-weight: 700; color: {INK}; letter-spacing: -0.02em;}}
.panel-sub {{font-size: 0.85rem; color: {MUTED}; margin-top: 0.1rem;}}
[class*="st-key-panel"] {{background: #fff; border: 1px solid {LINE} !important; border-radius: 0.9rem !important;
                         box-shadow: 0 1px 2px rgba(20, 22, 28, 0.04);}}
.takeaways {{border: 1px solid {LINE}; border-radius: 0.9rem; background: #fff; overflow: hidden; height: 100%;
             box-shadow: 0 1px 2px rgba(20, 22, 28, 0.04);}}
.takeaways .head {{background: {NAVY}; color: #fff; font-size: 1.2rem; font-weight: 700; padding: 0.85rem 1.1rem;}}
.takeaways .item {{display: flex; gap: 0.85rem; padding: 1rem 1.1rem; border-top: 1px solid {LINE};}}
.takeaways .item:first-of-type {{border-top: 0;}}
.takeaways svg {{flex: none; width: 2rem; height: 2rem; color: {ACCENT};}}
.takeaways b {{display: block; font-size: 1.02rem; color: {INK}; letter-spacing: -0.01em;}}
.takeaways span {{font-size: 0.86rem; color: {MUTED}; line-height: 1.4;}}
.legend {{margin: 0.2rem 0.3rem 0;}}
.legend div {{display: flex; align-items: center; gap: 0.55rem; font-size: 0.88rem; color: {INK}; padding: 0.22rem 0;}}
.legend i {{width: 0.95rem; height: 0.95rem; border-radius: 0.25rem; flex: none;}}
.legend em {{font-style: normal; color: {MUTED};}}
.legend b {{margin-left: auto; font-variant-numeric: tabular-nums;}}
@media (max-width: 640px) {{
  .bar-title {{font-size: 1.2rem;}}
}}
</style>
"""

TIER_PILL = {"Top opportunity": "", "Strong": "strong"}


def apply(public=False):
    st.html(CSS)
    if public:      # top navigation sits over the page; leave room so the eyebrow isn't hidden
        st.html(PUBLIC_CSS)


def esc(text):
    return html.escape(str(text))


def hero(eyebrow, title, subtitle="", extra="", side=""):
    """extra: HTML under the subtitle (e.g. stats()); side: HTML shown to the right of the title."""
    head = (f'<div><div class="eyebrow">{esc(eyebrow)}</div><h1>{esc(title)}</h1>'
            + (f'<div class="sub">{esc(subtitle)}</div>' if subtitle else "") + "</div>")
    if side:
        head = f'<div class="hero-row">{head}{side}</div>'
    st.html(f'<div class="hero">{head}{extra}</div>')


def topbar(subtitle, controls=0):
    """Navy header bar: brand, dashboard title and up to `controls` columns for filters (returned)."""
    with st.container(key="topbar"):
        cols = st.columns([1, 2.5] + [1] * controls if controls else [1, 4.5], vertical_alignment="bottom",
                          gap="medium")
        cols[0].html('<div class="brand"><div class="mark"></div><div><div class="for">Prepared for</div>'
                     '<div class="name">Anvara</div></div></div>')
        cols[1].html(f'<div class="bar-title">College Sponsorship Opportunity Dashboard</div>'
                     f'<div class="bar-sub">{esc(subtitle)}</div>')
    return cols[2:]


def kpi(value, label, note="", icon=""):
    return (f'<div class="kpi"><div class="v">{icon}{esc(value)}</div><div class="k">{esc(label)}</div>'
            + (f'<div class="n">{esc(note)}</div>' if note else "") + "</div>")


def stats(items):
    """Strip of (value, label) figures for the hero."""
    return '<div class="stats">' + "".join(f"<div><b>{esc(v)}</b>{esc(k)}</div>" for v, k in items) + "</div>"


def pill(tier):
    return f'<span class="pill {TIER_PILL.get(tier, "quiet")}">{esc(tier)}</span>'


def grid(items, min_width=300):
    """Equal-height, wrapping grid of HTML cards."""
    st.html(f'<div class="grid" style="--min:{min_width}px">{"".join(items)}</div>')


def card(label, value, note=""):
    return (f'<div class="card"><div class="label">{esc(label)}</div>'
            + (f'<div class="value">{esc(value)}</div>' if value != "" else "")
            + (f'<div class="note">{esc(note)}</div>' if note else "") + "</div>")


def meter(label, value, what=""):
    """Labeled 0-100 bar."""
    shown, width = ("—", 0) if value != value else (f"{value:.0f}", max(min(value, 100), 0))
    return (f'<div class="meter"><div class="top"><span>{esc(label)}</span><span>{shown}</span></div>'
            f'<div class="track"><div style="width:{width:.0f}%"></div></div>'
            + (f'<div class="what">{esc(what)}</div>' if what else "") + "</div>")


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
    st.html('<div class="footer">FY2025 NCAA financial data (Knight–Newhouse College Athletics Database, used with '
            "permission; schools' own reports where published) · 2024–25 attendance · research verified by a person before "
            "it is scored · Independent analysis prepared by Tucker Harrell. Not affiliated with any school or "
            "company named.</div>")

"""Shared dashboard state: which dataset is shown, the live weights, and the scores."""

import copy
import os

import pandas as pd
import streamlit as st

from engine.data import DEMO_DIR, RESEARCH_DIR, load_tables, load_weights
from engine.scoring import CATEGORY_LABELS, COMPONENT_LABELS, score_schools

DEFAULTS = load_weights()
# Public, shared copy (set READ_ONLY = "1" in the host's secrets): no review queue, no adding findings
READ_ONLY = os.environ.get("READ_ONLY", "") == "1"
SLIDERS = {   # weight group -> {key: label}
    "categories": CATEGORY_LABELS,
    "financial_pressure": {k: COMPONENT_LABELS[k] for k in DEFAULTS["financial_pressure"]},
    "commercial_opportunity": {k: COMPONENT_LABELS[k] for k in DEFAULTS["commercial_opportunity"]},
    "fan_reach": {"football": "Football", "mens_basketball": "Men's basketball",
                  "womens_basketball": "Women's basketball"},
}
GROUP_TITLES = {"categories": "Category weights", "financial_pressure": "Financial Pressure components",
                "commercial_opportunity": "Commercial Opportunity components",
                "fan_reach": "Fan reach: attendance mix"}


def _folder_signature(folder):
    return tuple(sorted((p.name, p.stat().st_mtime) for p in folder.glob("*.csv")))


@st.cache_data(show_spinner=False)
def _load(folder_str, _signature):
    return load_tables(folder_str)


def reset_weights():
    for group, items in SLIDERS.items():
        for key in items:
            st.session_state[f"w.{group}.{key}"] = DEFAULTS[group][key]


def sidebar():
    """Draw the shared sidebar. Returns (is_demo, weights)."""
    with st.sidebar:
        st.markdown("**College Sponsorship Opportunity**")
        st.caption("113 public FBS athletic departments · FY2025")
        st.markdown("### Compare schools")
        within = st.segmented_control(
            "Score each school against", ["Its segment", "All FBS"], default="Its segment", key="rank_within",
            help="Its segment: Power 4 schools are scored against Power 4, Group of 5 & other FBS against "
                 "each other. All FBS: one scale for all 113 (big programs dominate the top).")
        st.markdown("### Scoring weights")
        st.caption("Provisional hypotheses, not validated predictors. Weights in each group are "
                   "rescaled to 100%.")
        weights = copy.deepcopy(DEFAULTS)
        for group, items in SLIDERS.items():
            with st.expander(GROUP_TITLES[group], expanded=(group == "categories")):
                for key, label in items.items():
                    weights[group][key] = st.slider(label, 0, 100, DEFAULTS[group][key], step=5,
                                                    key=f"w.{group}.{key}")
                total = sum(weights[group].values())
                if total == 0:
                    st.warning("All weights are zero; using defaults.")
                    weights[group] = dict(DEFAULTS[group])
                else:
                    st.caption(" · ".join(f"{items[k].split(' (')[0]} {v / total:.0%}"
                                          for k, v in weights[group].items()))
        st.button("Reset to default weights", on_click=reset_weights, width="stretch")
        weights["rules"]["rank_within"] = "all" if within == "All FBS" else "segment"
        st.markdown("### Data")
        is_demo = st.toggle("Show demonstration data", key="demo",
                            help="Fictional schools and numbers for exploring the dashboard. "
                                 "Never mixed with research data.")
    return is_demo, weights


def context():
    """Everything a page needs. Call once at the top of each page."""
    is_demo = st.session_state.get("demo", False)
    weights = st.session_state.get("weights", DEFAULTS)
    folder = DEMO_DIR if is_demo else RESEARCH_DIR
    tables = _load(str(folder), _folder_signature(folder))
    scored = score_schools(tables, weights)
    if is_demo:
        st.error("**DEMONSTRATION DATA**: fictional schools and numbers for exploring the "
                 "dashboard. Not research. Turn off in the sidebar.", icon="⚠️")
    return {"tables": tables, "scored": scored, "weights": weights, "is_demo": is_demo}


def clear_cache():
    _load.clear()


def rights_summary(tables):
    """school_id -> 'Org A; Org B' (supports several rights holders per school)."""
    rel = tables["rights_relationships"]
    names = tables["rights_holders"].set_index("organization_id")["name"]
    if rel.empty:
        return pd.Series(dtype=str)
    rel = rel.assign(org=rel["organization_id"].map(names).fillna(rel["organization_id"]))
    return rel.groupby("school_id")["org"].agg(lambda s: "; ".join(sorted(set(s))))

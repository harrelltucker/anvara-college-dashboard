"""Display formatting and shared table configuration."""

import pandas as pd
import streamlit as st

CONFERENCE_COLORS = {"B1G": "#1f3b73", "BIG12": "#c8102e", "SEC": "#f2a900", "ACC": "#00857c"}


def money(v):
    return "—" if pd.isna(v) else f"${v / 1e6:,.1f}M"


def pct(v, digits=0):
    return "—" if pd.isna(v) else f"{v:.{digits}%}"


def score(v):
    return "—" if pd.isna(v) else f"{v:.0f}"


SCORE_COL = lambda label: st.column_config.ProgressColumn(label, min_value=0, max_value=100, format="%.0f")
MONEY_COL = lambda label: st.column_config.NumberColumn(label, format="$%.1fM")
PCT_COL = lambda label: st.column_config.NumberColumn(label, format="%.0f%%")

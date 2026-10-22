"""Display formatting and shared table configuration."""

import pandas as pd
import streamlit as st

CONFERENCE_COLORS = {"B1G": "#2346F9", "SEC": "#14161C", "BIG12": "#0099FF", "ACC": "#7C5CFF",
                     "AAC": "#1D9E75", "MWC": "#F2A900", "SBC": "#E5484D", "MAC": "#5B6475",
                     "CUSA": "#A1C5FF", "PAC12": "#1D322D", "IND": "#B4B4BA"}
CONFERENCE_NAMES = {"B1G": "Big Ten", "SEC": "SEC", "BIG12": "Big 12", "ACC": "ACC", "AAC": "American",
                    "MWC": "Mountain West", "SBC": "Sun Belt", "MAC": "MAC", "CUSA": "Conference USA",
                    "PAC12": "Pac-12", "IND": "Independent"}


def money(v):
    return "—" if pd.isna(v) else f"${v / 1e6:,.1f}M"


def pct(v, digits=0):
    return "—" if pd.isna(v) else f"{v:.{digits}%}"


def score(v):
    return "—" if pd.isna(v) else f"{v:.0f}"


SCORE_COL = lambda label: st.column_config.ProgressColumn(label, min_value=0, max_value=100, format="%.0f")
MONEY_COL = lambda label: st.column_config.NumberColumn(label, format="$%.1fM")
PCT_COL = lambda label: st.column_config.NumberColumn(label, format="%.0f%%")

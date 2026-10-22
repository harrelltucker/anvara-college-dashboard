import pandas as pd
import streamlit as st

from ui.fmt import MONEY_COL, PCT_COL, SCORE_COL
from ui.state import context, rights_summary

ctx = context()
scored, tables = ctx["scored"], ctx["tables"]

st.title("College athletics sponsorship opportunity")
st.caption("Which athletic departments could be the largest, most motivated sponsorship-marketplace "
           "partners for Anvara. Scores rank schools against each other (0–100); weights are adjustable "
           "in the sidebar. This ranks opportunity, not unsold inventory.")

confs = sorted(c for c in scored["conference_id"].unique() if c)
c1, c2 = st.columns([1, 2])
conf_filter = c1.multiselect("Conference", confs)
search = c2.text_input("Search school")

rights = rights_summary(tables)
table = pd.DataFrame({
    "Rank": scored["rank"],
    "University": scored["name"],
    "Conference": scored["conference_id"],
    "Overall": scored["overall"],
    "Financial Pressure": scored["financial_pressure"],
    "Commercial Opportunity": scored["commercial_opportunity"],
    "Growth Catalysts": scored["growth_catalysts"],
    "FY25 revenue": scored["total_operating_revenue"] / 1e6,
    "FY25 expenses": scored["total_operating_expenses"] / 1e6,
    "FY25 reported result": scored["reported_result"] / 1e6,
    "FY25 commercial revenue": scored["commercial_revenue"] / 1e6,
    "Commercial % of revenue": scored["commercial_share"] * 100,
    "Rights holder(s)": rights.reindex(scored.index).fillna("Not yet researched"),
    "Data completeness": scored["completeness"] * 100,
    "Confidence": scored["confidence"],
}, index=scored.index)
if conf_filter:
    table = table[table["Conference"].isin(conf_filter)]
if search:
    table = table[table["University"].str.contains(search, case=False, regex=False)]

if scored["overall"].isna().all():
    st.info("No school has enough verified data for an overall score yet. Scores appear as research "
            "is verified (see **Research & data quality**). Turn on demonstration data in the "
            "sidebar to explore how the dashboard works.")

st.caption(f"{len(table)} schools · click a row to open its profile · click a column header to sort")
event = st.dataframe(
    table, hide_index=True, width="stretch", height=min(38 * (len(table) + 1), 640),
    on_select="rerun", selection_mode="single-row",
    column_config={
        "Rank": st.column_config.NumberColumn(format="%d"),
        "Overall": SCORE_COL("Overall"), "Financial Pressure": SCORE_COL("Financial Pressure"),
        "Commercial Opportunity": SCORE_COL("Commercial Opportunity"),
        "Growth Catalysts": SCORE_COL("Growth Catalysts"),
        "FY25 revenue": MONEY_COL("FY25 revenue"), "FY25 expenses": MONEY_COL("FY25 expenses"),
        "FY25 reported result": MONEY_COL("FY25 reported result"),
        "FY25 commercial revenue": st.column_config.NumberColumn(
            "FY25 commercial revenue", format="$%.1fM",
            help="NCAA category combining sponsorship, advertising, licensing and related items. "
                 "Not pure sponsorship revenue."),
        "Commercial % of revenue": PCT_COL("Commercial % of revenue"),
        "Data completeness": PCT_COL("Data completeness"),
    },
)
if event.selection.rows:
    st.session_state["selected_school"] = table.index[event.selection.rows[0]]
    st.switch_page(st.session_state["pages"]["profile"])

if ctx["is_demo"]:
    st.caption("CSV export is disabled for demonstration data.")
else:
    restricted = set(tables["sources"].loc[tables["sources"]["export_allowed"] == "no", "source_id"])
    export = table.copy()
    blocked = scored.reindex(export.index)["financial_source_id"].isin(restricted)
    export.loc[blocked, ["FY25 revenue", "FY25 expenses", "FY25 reported result",
                         "FY25 commercial revenue", "Commercial % of revenue"]] = None
    st.download_button("Download ranked table (CSV)", export.to_csv(index=False).encode("utf-8"),
                       "college_sponsorship_rankings.csv", "text/csv",
                       help="Figures from sources not cleared for export are left blank.")

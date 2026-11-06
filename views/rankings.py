from datetime import date

import pandas as pd
import streamlit as st

from engine.scoring import catalyst_points
from ui import style
from ui.fmt import CONFERENCE_NAMES, MONEY_COL, SCORE_COL, money
from ui.state import context, rights_summary

ctx = context()
scored, tables, weights = ctx["scored"], ctx["tables"], ctx["weights"]

style.hero("Sponsorship opportunity · FY2025",
           "Where college sponsorship is most likely to grow",
           "Public FBS athletic departments ranked as sponsorship-marketplace partners: how much commercial "
           "business they have, how much pressure they're under to grow it, and what they're doing about it. "
           "Schools are ranked against comparable schools and grouped into tiers. This ranks opportunity, "
           "not unsold inventory.")

views = {"Power 4": "Power 4", "Group of 5 & other FBS": "Group of 5 & other FBS", "All FBS": None}
pick = st.segmented_control("Segment", list(views), default="Power 4", key="segment_view",
                            label_visibility="collapsed")
segment = views.get(pick or "Power 4")
view = scored if segment is None else scored[scored["segment"] == segment]
rank_col = "rank" if segment is None else "segment_rank"
view = view.sort_values(["overall", "name"], ascending=[False, True], na_position="last")

# biggest verified catalyst per school, for the one-line "why"
points = catalyst_points(tables["catalysts"], weights["catalysts"], date.today())
top_event = {}
if len(points):
    best = points.sort_values("points", ascending=False).drop_duplicates("school_id")
    titles = tables["catalysts"].drop_duplicates("event_id").set_index("event_id")["title"]
    top_event = {r.school_id: titles.get(r.event_id, "") for r in best.itertuples()}


def why(row):
    parts = []
    if pd.notna(row["commercial_opportunity"]) and row["commercial_opportunity"] >= 67:
        parts.append(f"{money(row['commercial_revenue'])} in sponsorship & licensing revenue")
    if pd.notna(row["financial_pressure"]) and row["financial_pressure"] >= 67:
        parts.append("under financial pressure to grow its own revenue")
    if row.name in top_event:
        parts.append(top_event[row.name].split(":")[0].split(" (")[0])
    return "; ".join(parts[:2]) or "Balanced profile across categories"


style.cards([
    ("Schools", f"{len(view)}", f"{int(view['featured'].sum())} with deep research"),
    ("Sponsorship & licensing revenue", money(view["commercial_revenue"].sum()), "FY2025, NCAA report category 15"),
    ("Growth catalysts tracked", f"{int(view['catalyst_events'].sum())}", "Verified events since 2024"),
    ("High or medium confidence", f"{int(view['confidence'].isin(['High', 'Medium']).sum())}",
     "Schools with all three categories scored"),
])

ranked = view.dropna(subset=["overall"])
if ranked.empty:
    st.info("No school has enough verified data for an overall score yet. Scores appear as research is "
            "verified (see **Research & data quality**).")
else:
    st.markdown("#### Top opportunities")
    for col, (sid, row) in zip(st.columns(3), ranked.head(3).iterrows()):
        conf = CONFERENCE_NAMES.get(row["conference_id"], row["conference_id"])
        of = len(ranked) if segment is None else int(row["segment_size"])
        col.html(f'<div class="pick"><div class="rank">#{int(row[rank_col])} of {of} · {style.esc(conf)}'
                 f'{" · Featured" if row["featured"] else ""}</div>'
                 f'<div class="tier">{style.esc(row["tier"])}</div>'
                 f'<div class="name">{style.esc(row["name"])}</div>'
                 f'<div class="index">Opportunity index {row["overall"]:.0f}</div>'
                 f'<div class="why">{style.esc(why(row))}</div></div>')

st.markdown("#### All schools")
f1, f2, f3 = st.columns([2, 2, 1])
confs = sorted({c for c in view["conference_id"] if c}, key=lambda c: CONFERENCE_NAMES.get(c, c))
conf_filter = f1.multiselect("Conference", confs, format_func=lambda c: CONFERENCE_NAMES.get(c, c),
                             placeholder="All conferences")
search = f2.text_input("Search school", placeholder="e.g. Rutgers")
featured_only = f3.toggle("Featured only", help="The 15 schools with deep research: every catalyst, "
                                                "rights holders, contacts and an opportunity brief.")

rights = rights_summary(tables)
table = pd.DataFrame({
    "#": view[rank_col],
    "School": view["name"],
    "Conference": view["conference_id"].map(lambda c: CONFERENCE_NAMES.get(c, c)),
    "Featured": view["featured"].map({True: "★", False: ""}),
    "Tier": view["tier"],
    "Index": view["overall"],
    "Financial Pressure": view["financial_pressure"],
    "Commercial Opportunity": view["commercial_opportunity"],
    "Growth Catalysts": view["growth_catalysts"],
    "Sponsorship rev.": view["commercial_revenue"] / 1e6,
    "Total revenue": view["total_operating_revenue"] / 1e6,
    "Football attendance": view["football"],
    "Rights holder": rights.reindex(view.index).fillna("—"),
    "Confidence": view["confidence"],
}, index=view.index)
if conf_filter:
    table = table[view["conference_id"].isin(conf_filter)]
if search:
    table = table[table["School"].str.contains(search, case=False, regex=False)]
if featured_only:
    table = table[table["Featured"] == "★"]

st.caption(f"{len(table)} schools · click a row to open its profile · click a column header to sort")
event = st.dataframe(
    table, hide_index=True, width="stretch", height=min(36 * (len(table) + 1) + 4, 720),
    on_select="rerun", selection_mode="single-row",
    column_config={
        "#": st.column_config.NumberColumn(format="%d", width="small"),
        "School": st.column_config.TextColumn(width="medium"),
        "Featured": st.column_config.TextColumn("", width="small", help="Featured: deep-research school"),
        "Tier": st.column_config.TextColumn(
            help="Rank within the segment: Top opportunity = top 10%, Strong = next 20%, "
                 "Moderate = middle 40%, Lower = bottom 30%"),
        "Index": st.column_config.NumberColumn(
            "Index", format="%.0f", help="Opportunity index: weighted average of the category scores. "
                                         "100 would mean ranking first on every measure."),
        "Financial Pressure": SCORE_COL("Financial Pressure"),
        "Commercial Opportunity": SCORE_COL("Commercial Opportunity"),
        "Growth Catalysts": SCORE_COL("Growth Catalysts"),
        "Sponsorship rev.": st.column_config.NumberColumn(
            "Sponsorship rev.", format="$%.1fM",
            help="FY2025 sponsorship, advertising & licensing revenue (NCAA report category 15). "
                 "Not pure sponsorship revenue."),
        "Total revenue": MONEY_COL("Total revenue"),
        "Football attendance": st.column_config.NumberColumn("Football att.", format="%,d",
                                                             help="2024 average home attendance (NCAA)"),
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
    export.loc[blocked, ["Sponsorship rev.", "Total revenue"]] = None
    st.download_button("Download this table (CSV)", export.to_csv(index=False).encode("utf-8"),
                       "college_sponsorship_rankings.csv", "text/csv", icon=":material/download:",
                       help="Figures from sources not cleared for export are left blank.")

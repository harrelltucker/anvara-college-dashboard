import pandas as pd
import plotly.express as px
import streamlit as st

from engine.metrics import school_metrics
from engine.research import checklist, opportunity_brief
from engine.scoring import CATEGORY_LABELS, COMPONENT_LABELS, missing_inputs
from ui import style
from ui.fmt import CONFERENCE_NAMES, money, pct, score
from ui.state import context

ctx = context()
scored, tables, weights = ctx["scored"], ctx["tables"], ctx["weights"]
sources = tables["sources"].set_index("source_id")

ids = list(scored.sort_values("name").index)
default = st.session_state.get("selected_school")
school_id = st.selectbox("School", ids, index=ids.index(default) if default in ids else 0,
                         format_func=lambda s: f"{scored.loc[s, 'name']}{'  ★' if scored.loc[s, 'featured'] else ''}",
                         label_visibility="collapsed")
st.session_state["selected_school"] = school_id
row = scored.loc[school_id]
missing = missing_inputs(row, tables)


def source_link(source_id):
    if source_id and source_id in sources.index:
        s = sources.loc[source_id]
        return f"[{s['title']}]({s['url']}) · retrieved {s['retrieved_date']}"
    return "No source recorded"


conf_name = CONFERENCE_NAMES.get(row["conference_id"], row["conference_id"] or "Conference unknown")
style.hero(f"{conf_name} · {row['segment']} · {row['state']}", row["name"], row["full_name"])
st.html(style.badges(*([("Featured: deep research", "accent")] if row["featured"] else ["Broad research"]),
                     f"Confidence: {row['confidence']}", f"Data completeness {row['completeness']:.0%}"))

seg_size = int(scored[scored["segment"] == row["segment"]]["overall"].notna().sum())
style.cards([
    ("Opportunity score", score(row["overall"]),
     f"#{int(row['segment_rank'])} of {seg_size} in {row['segment']}" if pd.notna(row["segment_rank"]) else ""),
    *[(CATEGORY_LABELS[cat], score(row[cat]), f"{row[f'{cat}_coverage']:.0%} of inputs available")
      for cat in CATEGORY_LABELS],
])
if not row["featured"]:
    st.caption("Broad research: scored on verified financials, attendance and a catalyst scan. Rights holders, "
               "contacts and a school-by-school catalyst review are done for Featured schools.")

tabs = st.tabs(["Brief", "Score breakdown", "Financials", "Commercial & audience",
                "Growth catalysts", "Rights holders & contacts", "Gaps & research checklist"])

with tabs[0]:
    st.markdown(opportunity_brief(school_id, scored, tables, missing))

with tabs[1]:
    rows = []
    for cat in ("financial_pressure", "commercial_opportunity"):
        total = sum(weights[cat].values())
        for comp, w in weights[cat].items():
            rows.append({"Category": CATEGORY_LABELS[cat], "Component": COMPONENT_LABELS[comp],
                         "Weight in category": w / total, "Score": row.get(f"{cat}.{comp}")})
    rows.append({"Category": "Growth Catalysts", "Component": f"Rubric ({int(row['catalyst_events'])} distinct events)",
                 "Weight in category": 1.0, "Score": row["growth_catalysts"]})
    breakdown = pd.DataFrame(rows)
    fig = px.bar(breakdown.dropna(subset=["Score"]), x="Score", y="Component", color="Category",
                 orientation="h", range_x=[0, 100], template="simple_white", height=340,
                 color_discrete_map=style.CATEGORY_COLORS)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend_title_text="", yaxis_title="")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(breakdown.assign(**{"Weight in category": breakdown["Weight in category"].map(pct),
                                     "Score": breakdown["Score"].map(score)}),
                 hide_index=True, width="stretch")
    st.caption("Component scores are ranks among the schools analyzed (0 = lowest, 100 = highest). "
               "'—' means missing data; missing data is never scored as 0.")

with tabs[2]:
    fin = pd.DataFrame([
        ("Total operating revenue (reported)", money(row["total_operating_revenue"]), "As reported to the NCAA"),
        ("Total operating expenses (reported)", money(row["total_operating_expenses"]), "As reported to the NCAA"),
        ("Reported surplus / (deficit)", money(row["reported_result"]), "Revenue minus expenses, after subsidies"),
        ("Reported result, % of expenses", pct(row["reported_margin"], 1), "Used in the score so schools of different sizes compare fairly"),
        ("Allocated revenue", money(row["allocated_revenue"]), "Institutional support (direct + indirect) + student fees + direct government support"),
        ("Athletics-generated revenue (NCAA definition)", money(row["generated_revenue"]),
         "Total revenue minus allocated revenue. Includes conference payouts and donations"),
        ("Self-sufficiency", pct(row["self_sufficiency"]), "Generated revenue ÷ expenses"),
        ("Conference/NCAA distributions, media rights, bowl revenue", money(row["conference_ncaa_media_revenue"]),
         "Largely negotiated and shared by the conference"),
        ("Donor contributions (incl. in-kind)", money(row["donor_contributions"]), "Shown for context"),
        ("Own-operations revenue", money(row["own_operations_revenue"]),
         "Generated revenue minus conference/NCAA distributions, media rights and bowl revenue"),
        ("Own-operations revenue vs. conference public-peer median", "—" if pd.isna(row["conf_relative_generated"])
         else f"{row['conf_relative_generated']:.2f}×", f"{int(row['peer_count'])} public peers with data; "
         f"coverage {pct(row['peer_coverage'])}"),
    ], columns=["Metric", "FY2025", "Definition"])
    st.dataframe(fin, hide_index=True, width="stretch")
    st.caption(f"Source: {source_link(row['financial_source_id'])}")
    if pd.notna(row["peer_coverage"]) and row["peer_coverage"] < weights["rules"]["min_peer_coverage"]:
        st.warning("Too few conference members have FY2025 data for a fair benchmark, so this "
                   "component is left out of the score rather than using a partial sample.")
    everyone = school_metrics(tables, weights["rules"])      # includes benchmark-only peers
    peers = everyone[everyone["conference_id"] == row["conference_id"]].dropna(subset=["own_operations_revenue"])
    if len(peers) > 1:
        peers = peers.sort_values("own_operations_revenue")
        fig = px.bar(peers, x=peers["own_operations_revenue"] / 1e6, y="name", orientation="h",
                     template="simple_white", labels={"x": "FY2025 own-operations revenue ($M)", "name": ""},
                     color=peers.index == school_id,
                     color_discrete_map={True: style.ACCENT, False: "#C9CDD6"}, height=60 + 24 * len(peers))
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0),
                          title=f"Own-operations revenue vs. {row['conference_id']} public schools")
        st.plotly_chart(fig, width="stretch")

with tabs[3]:
    c = st.columns(3)
    c[0].metric("Sponsorship, advertising & licensing (as reported to the NCAA, category 15)", money(row["commercial_revenue"]))
    c[1].metric("Share of total athletics revenue", pct(row["commercial_share"], 1))
    c[2].metric("Conference peer median share", pct(row["conf_peer_median_commercial_share"], 1),
                help="Shown for context; the share itself is not scored")
    st.caption("This category of the NCAA financial report (category 15) combines sponsorships, advertising, licensing and related items. "
               "It is never labeled as pure sponsorship revenue.")
    aud = tables["audience"][tables["audience"]["school_id"] == school_id]
    if aud.empty:
        st.info("No verified audience data yet.")
    else:
        st.dataframe(aud.assign(source=aud["source_id"].map(source_link))[["season", "metric", "value", "source", "notes"]],
                     hide_index=True, width="stretch")
    st.caption(f"Fan reach score: {score(row['fan_reach_score'])} (average home attendance, ranked and weighted by "
               "sport; football only by default until every school has basketball figures; stadium capacity "
               "is never used as a substitute).")

with tabs[4]:
    cats = tables["catalysts"][tables["catalysts"]["school_id"] == school_id]
    if cats.empty:
        researched = (tables["research_status"].query("school_id == @school_id and area == 'catalysts'")["status"] == "complete").any()
        st.info("Researched: no qualifying catalysts found." if researched else "Catalyst research not yet done.")
    else:
        st.dataframe(cats.sort_values("event_date", ascending=False).assign(
            source=cats["source_id"].map(source_link))[["event_date", "title", "category", "significance",
                                                        "commercial_relevance", "confidence", "event_id", "source"]],
                     hide_index=True, width="stretch")
        st.caption("Rows sharing an event_id are one underlying event and are counted once.")

with tabs[5]:
    rel = tables["rights_relationships"][tables["rights_relationships"]["school_id"] == school_id]
    orgs = tables["rights_holders"].set_index("organization_id")
    st.markdown("**Commercial rights** (context only, not scored)")
    if rel.empty:
        st.info("Rights-holder research not yet done. Unknown arrangements are shown as unknown, never assumed.")
    else:
        st.dataframe(rel.assign(organization=rel["organization_id"].map(orgs["name"]),
                                source=rel["source_id"].map(source_link))[
            ["organization", "management_model", "rights_scope", "agreement_details", "start_date",
             "expiration_date", "expiration_verified", "source"]], hide_index=True, width="stretch")
        st.caption("A Learfield or Playfly relationship is not a negative: rights holders could be "
                   "distribution partners for Anvara.")
    st.markdown("**Commercial contacts** (public professional information only)")
    con = tables["contacts"][tables["contacts"]["school_id"] == school_id]
    if con.empty:
        st.info("No contacts identified yet.")
    else:
        st.dataframe(con.assign(source=con["source_id"].map(source_link))[
            ["name", "title", "organization_id", "profile_url", "business_contact", "source"]],
            hide_index=True, width="stretch",
            column_config={"profile_url": st.column_config.LinkColumn("Profile")})

with tabs[6]:
    st.dataframe(checklist(school_id, row, tables, missing), hide_index=True, width="stretch")

if not ctx["is_demo"]:
    st.download_button("Download this profile's metrics (CSV)",
                       row.drop(labels=[c for c in row.index if "." in c]).to_frame("value").to_csv().encode("utf-8"),
                       f"{school_id.lower()}_profile.csv", "text/csv")

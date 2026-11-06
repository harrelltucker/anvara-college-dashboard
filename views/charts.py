import pandas as pd
import plotly.express as px
import streamlit as st

from engine.scoring import CATEGORY_LABELS
from ui import style
from ui.fmt import CONFERENCE_COLORS, CONFERENCE_NAMES
from ui.state import context

ctx = context()
scored, tables, weights = ctx["scored"], ctx["tables"], ctx["weights"]
FONT = dict(family="Inter, sans-serif", color=style.INK, size=12)


def tidy(fig, height=420):
    fig.update_layout(template="simple_white", height=height, margin=dict(l=0, r=0, t=30, b=0),
                      legend_title_text="", font=FONT, hoverlabel=dict(font_family="Inter"))
    fig.update_xaxes(gridcolor=style.LINE, linecolor=style.LINE)
    fig.update_yaxes(gridcolor=style.LINE, linecolor=style.LINE)
    return fig


style.hero("Market view", "How the market is shaped",
           "Where pressure and commercial scale meet, who sells the most sponsorship, how conferences "
           "compare, and which schools are actively building their commercial business.")

pick = st.segmented_control("Segment", ["Power 4", "Group of 5 & other FBS", "All FBS"], default="Power 4",
                            key="chart_segment", label_visibility="collapsed")
view = scored if pick == "All FBS" else scored[scored["segment"] == (pick or "Power 4")]
view = view.assign(conference=view["conference_id"].map(lambda c: CONFERENCE_NAMES.get(c, c)))
colors = {CONFERENCE_NAMES.get(k, k): v for k, v in CONFERENCE_COLORS.items()}

# 1. Pressure vs opportunity
st.markdown("#### Financial Pressure vs. Commercial Opportunity")
size_by = st.radio("Bubble size", ["Sponsorship revenue", "Football attendance"], horizontal=True)
size_col = "commercial_revenue" if size_by == "Sponsorship revenue" else "football"
plot = view.dropna(subset=["financial_pressure", "commercial_opportunity"]).copy()
if plot.empty:
    st.info("Needs schools with both Financial Pressure and Commercial Opportunity scores.")
else:
    plot["bubble"] = plot[size_col].fillna(plot[size_col].median()).fillna(1)
    labelled = set(plot.nlargest(12, "overall").index) | set(plot[plot["featured"]].index)
    plot["label"] = [n if i in labelled else "" for i, n in zip(plot.index, plot["name"])]
    fig = px.scatter(plot, x="financial_pressure", y="commercial_opportunity", size="bubble",
                     color="conference", text="label", size_max=40, range_x=[-5, 105], range_y=[-5, 108],
                     color_discrete_map=colors, hover_name="name",
                     labels={"financial_pressure": "Financial Pressure (higher = more incentive to grow)",
                             "commercial_opportunity": "Commercial Opportunity (higher = bigger dollars)"},
                     hover_data={"bubble": False, "label": False, "overall": ":.0f", "growth_catalysts": ":.0f"})
    fig.update_traces(textposition="top center", textfont_size=10, marker_line_width=0, opacity=0.85)
    fig.add_hline(y=50, line_dash="dot", line_color="#C9CDD6")
    fig.add_vline(x=50, line_dash="dot", line_color="#C9CDD6")
    for x, y, label in ((100, 106, "Motivated and large"), (0, 106, "Large, less pressure")):
        fig.add_annotation(x=x, y=y, text=label, showarrow=False, font_color=style.MUTED,
                           xanchor="right" if x > 50 else "left")
    st.plotly_chart(tidy(fig, 580), width="stretch")
    st.caption("Labels show the top 12 by score and Featured schools; hover for any school. Missing bubble "
               "sizes use the median, so size never implies a value that wasn't reported.")

left, right = st.columns(2)

# 2. Sponsorship revenue leaders
with left:
    st.markdown("#### Sponsorship & licensing revenue leaders")
    rev = view.dropna(subset=["commercial_revenue"]).nlargest(20, "commercial_revenue").sort_values("commercial_revenue")
    if rev.empty:
        st.info("No verified commercial revenue yet.")
    else:
        fig = px.bar(rev, x=rev["commercial_revenue"] / 1e6, y="name", orientation="h", color="conference",
                     color_discrete_map=colors, labels={"x": "FY2025, $M (NCAA report category 15)", "name": ""})
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(tidy(fig, 80 + 24 * len(rev)), width="stretch")
        st.caption("Top 20 in this segment. Category 15 combines sponsorship, advertising and licensing.")

# 3. Conference comparison
with right:
    st.markdown("#### Conference comparison")
    metric = st.selectbox("Metric", ["commercial_share", "commercial_revenue", "self_sufficiency", "overall",
                                     "financial_pressure", "commercial_opportunity"],
                          format_func=lambda m: {"commercial_share": "Sponsorship % of revenue",
                                                 "commercial_revenue": "Sponsorship revenue",
                                                 "self_sufficiency": "Self-sufficiency",
                                                 "overall": "Opportunity index", **CATEGORY_LABELS}.get(m, m))
    conf = view.dropna(subset=[metric])
    conf = conf[conf["conference_id"] != ""]
    if conf.empty:
        st.info("No data for this metric yet.")
    else:
        fig = px.strip(conf, x="conference", y=metric, color="conference", hover_name="name",
                       color_discrete_map=colors, labels={"conference": "", metric: ""})
        medians = conf.groupby("conference")[metric].median().reset_index()
        fig.add_scatter(x=medians["conference"], y=medians[metric], mode="markers", name="Median",
                        marker=dict(symbol="line-ew-open", size=36, color=style.INK, line_width=2))
        if metric in ("commercial_share", "self_sufficiency"):
            fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(tidy(fig, 80 + 24 * 20), width="stretch")
        st.caption("Public schools only; each dot is a school, the bar is the conference median.")

# 4. Score breakdown
st.markdown("#### What drives the top scores")
total_w = sum(weights["categories"].values())
contrib = view.dropna(subset=["overall"]).nlargest(20, "overall")
if contrib.empty:
    st.info("No overall scores yet.")
else:
    avail_w = sum(contrib[c].notna() * weights["categories"][c] for c in CATEGORY_LABELS)
    long = pd.concat([pd.DataFrame({"School": contrib["name"], "Category": label,
                                    "Points": contrib[c].fillna(0) * weights["categories"][c] / avail_w})
                      for c, label in CATEGORY_LABELS.items()])
    fig = px.bar(long, x="Points", y="School", color="Category", orientation="h",
                 category_orders={"School": list(contrib["name"])}, color_discrete_map=style.CATEGORY_COLORS)
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(tidy(fig, 100 + 26 * len(contrib)), width="stretch")
    st.caption("Top 20 in this segment. Bars sum to each school's score. Category weights: "
               + ", ".join(f"{CATEGORY_LABELS[c]} {w / total_w:.0%}" for c, w in weights["categories"].items()))

# 5. Growth catalyst timeline
st.markdown("#### Growth catalysts over time")
cats = tables["catalysts"].drop_duplicates("event_id", keep="first")
cats = cats[cats["school_id"].isin(view.index)]
if cats.empty:
    st.info("No verified growth catalysts yet.")
else:
    labels = {"in_house_rights_org": "New commercial company / in-house rights", "private_capital": "Private capital",
              "commercial_leadership": "Commercial leadership hire", "new_inventory": "New inventory (patches, field logos)",
              "major_partnership": "Naming rights / major partnership", "rights_restructuring": "Rights restructuring",
              "sponsorship_initiative": "Sponsorship initiative", "other": "Other"}
    cats = cats.assign(school=cats["school_id"].map(view["name"]), date=pd.to_datetime(cats["event_date"]),
                       type=cats["category"].map(labels).fillna(cats["category"]))
    fig = px.scatter(cats, x="date", y="school", color="type", hover_name="title",
                     size=cats["significance"].map({"high": 16, "medium": 10, "low": 6}),
                     labels={"date": "", "school": "", "type": ""})
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(tidy(fig, 120 + 22 * cats["school"].nunique()), width="stretch")
    st.caption("Bigger dots = more significant events. Several announcements of one event appear once.")

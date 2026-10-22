import pandas as pd
import plotly.express as px
import streamlit as st

from engine.scoring import CATEGORY_LABELS
from ui.fmt import CONFERENCE_COLORS
from ui.state import context

ctx = context()
scored, tables, weights = ctx["scored"], ctx["tables"], ctx["weights"]
TEMPLATE = "simple_white"


def tidy(fig, height=420):
    fig.update_layout(template=TEMPLATE, height=height, margin=dict(l=0, r=0, t=40, b=0),
                      legend_title_text="")
    return fig


st.title("Market view")

# 1. Pressure vs opportunity
st.subheader("Financial Pressure vs. Commercial Opportunity")
size_by = st.radio("Bubble size", ["Commercial revenue", "Football attendance"], horizontal=True)
size_col = "commercial_revenue" if size_by == "Commercial revenue" else "football"
plot = scored.dropna(subset=["financial_pressure", "commercial_opportunity"]).copy()
if plot.empty:
    st.info("Needs schools with both Financial Pressure and Commercial Opportunity scores.")
else:
    plot["bubble"] = plot[size_col].fillna(plot[size_col].median()).fillna(1)
    fig = px.scatter(plot, x="financial_pressure", y="commercial_opportunity", size="bubble",
                     color="conference_id", text="name", size_max=48, range_x=[-5, 105], range_y=[-5, 105],
                     color_discrete_map=CONFERENCE_COLORS,
                     labels={"financial_pressure": "Financial Pressure (higher = more incentive)",
                             "commercial_opportunity": "Commercial Opportunity (higher = bigger dollars)"},
                     hover_data={"bubble": False, "overall": ":.0f", "growth_catalysts": ":.0f"})
    fig.update_traces(textposition="top center", textfont_size=10)
    fig.add_hline(y=50, line_dash="dot", line_color="#bbb")
    fig.add_vline(x=50, line_dash="dot", line_color="#bbb")
    for x, y, label in ((97, 103, "Motivated + large"), (3, 103, "Large, less pressure")):
        fig.add_annotation(x=x, y=y, text=label, showarrow=False, font_color="#888",
                           xanchor="right" if x > 50 else "left")
    st.plotly_chart(tidy(fig, 560), width="stretch")
    st.caption("Schools missing either score are omitted. Missing bubble sizes use the median, so "
               "size never implies a value that wasn't reported.")

left, right = st.columns(2)

# 2. Commercial revenue ranking
with left:
    st.subheader("Commercial revenue ranking")
    rev = scored.dropna(subset=["commercial_revenue"]).sort_values("commercial_revenue")
    if rev.empty:
        st.info("No verified commercial revenue yet.")
    else:
        fig = px.bar(rev, x=rev["commercial_revenue"] / 1e6, y="name", orientation="h", color="conference_id",
                     color_discrete_map=CONFERENCE_COLORS,
                     labels={"x": "FY2025 sponsorship, advertising & licensing ($M, NCAA report category 15)", "name": ""})
        st.plotly_chart(tidy(fig, 60 + 26 * len(rev)), width="stretch")

# 3. Conference comparison
with right:
    st.subheader("Conference comparison")
    metric = st.selectbox("Metric", ["commercial_share", "self_sufficiency", "overall",
                                     "financial_pressure", "commercial_opportunity"],
                          format_func=lambda m: {"commercial_share": "Commercial % of revenue",
                                                 "self_sufficiency": "Self-sufficiency",
                                                 "overall": "Overall score",
                                                 **CATEGORY_LABELS}.get(m, m))
    conf = scored.dropna(subset=[metric])
    if conf.empty:
        st.info("No data for this metric yet.")
    else:
        fig = px.strip(conf, x="conference_id", y=metric, color="conference_id", hover_name="name",
                       color_discrete_map=CONFERENCE_COLORS, labels={"conference_id": "", metric: ""})
        medians = conf.groupby("conference_id")[metric].median().reset_index()
        fig.add_scatter(x=medians["conference_id"], y=medians[metric], mode="markers", name="Median",
                        marker=dict(symbol="line-ew-open", size=40, color="#333"))
        if metric in ("commercial_share", "self_sufficiency"):
            fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(tidy(fig), width="stretch")
        st.caption("Only schools in this dataset; partial conference samples are not full benchmarks.")

# 4. Score breakdown: weighted contribution of each category
st.subheader("Score breakdown")
total_w = sum(weights["categories"].values())
contrib = scored.dropna(subset=["overall"]).copy()
if contrib.empty:
    st.info("No overall scores yet.")
else:
    avail_w = sum(contrib[c].notna() * weights["categories"][c] for c in CATEGORY_LABELS)
    long = pd.concat([pd.DataFrame({"School": contrib["name"], "Category": label,
                                    "Points": contrib[c].fillna(0) * weights["categories"][c] / avail_w})
                      for c, label in CATEGORY_LABELS.items()])
    fig = px.bar(long, x="Points", y="School", color="Category", orientation="h",
                 category_orders={"School": list(contrib.sort_values("overall")["name"])[::-1]},
                 color_discrete_sequence=["#1f3b73", "#00857c", "#c8102e"])
    st.plotly_chart(tidy(fig, 80 + 28 * len(contrib)), width="stretch")
    st.caption(f"Bars sum to each school's overall score. Category weights: " +
               ", ".join(f"{CATEGORY_LABELS[c]} {w / total_w:.0%}" for c, w in weights["categories"].items()))

# 5. Growth catalyst timeline
st.subheader("Growth catalyst timeline")
cats = tables["catalysts"].drop_duplicates("event_id", keep="first")
if cats.empty:
    st.info("No verified growth catalysts yet.")
else:
    names = scored["name"].to_dict()
    cats = cats.assign(school=cats["school_id"].map(names).fillna(cats["school_id"]),
                       date=pd.to_datetime(cats["event_date"]))
    fig = px.scatter(cats, x="date", y="school", color="category", symbol="confidence", hover_name="title",
                     size=cats["significance"].map({"high": 18, "medium": 12, "low": 7}),
                     labels={"date": "", "school": ""})
    st.plotly_chart(tidy(fig, 120 + 30 * cats["school"].nunique()), width="stretch")

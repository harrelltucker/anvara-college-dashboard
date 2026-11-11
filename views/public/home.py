import plotly.graph_objects as go
import streamlit as st

from ui import style
from ui.fmt import CONFERENCE_NAMES, money
from ui.public import STATES, big_league_cities, reasons, top_events
from ui.state import context

ctx = context()
scored, tables, weights = ctx["scored"], ctx["tables"], ctx["weights"]
events, cities = top_events(tables, weights), big_league_cities(tables)
ranked = scored.dropna(subset=["overall"])
TIERS = list(style.TIER_COLORS)
ICONS = {   # simple line icons, drawn in the accent color
    "trophy": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
              'stroke-linejoin="round"><path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4z"/>'
              '<path d="M17 6h3v2a3 3 0 0 1-3 3M7 6H4v2a3 3 0 0 0 3 3"/></svg>',
    "trend": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
             'stroke-linejoin="round"><path d="M4 20V14M9 20V10M14 20v-4M19 20V7"/><path d="M4 9l5-4 5 4 6-5"/></svg>',
    "target": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" '
              'r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/></svg>',
    "star": '<svg viewBox="0 0 24 24" fill="#F2A900"><path d="M12 2.5l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.3l-5.9 '
            '3.3 1.3-6.6L2.5 9.4l6.6-.8z"/></svg>',
}

# ---- header bar with filters ----------------------------------------------------------------------------------
f_group, f_conf, f_state = style.topbar(
    "113 public FBS athletic departments, ranked within their group (Power 4, or Group of 5 & other FBS)", controls=3)
segment = f_group.selectbox("Group", ["Power 4", "Group of 5 & other FBS"], key="segment_view")
group = ranked[ranked["segment"] == segment]
confs = sorted(group["conference_id"].unique(), key=lambda c: CONFERENCE_NAMES.get(c, c))
conf = f_conf.selectbox("Conference", ["All conferences"] + confs,
                        format_func=lambda c: CONFERENCE_NAMES.get(c, c), key=f"conf_view.{segment}")
states = sorted(group["state"].unique(), key=lambda s: STATES.get(s, s))
state = f_state.selectbox("Location", ["All locations"] + states, format_func=lambda s: STATES.get(s, s),
                          key=f"state_view.{segment}")
view = group
if conf != "All conferences":
    view = view[view["conference_id"] == conf]
if state != "All locations":
    view = view[view["state"] == state]
view = view.sort_values(["segment_rank", "name"])
if view.empty:
    st.info("No schools match these filters.")
    st.stop()
filtered = len(view) < len(group)
scope = "these schools" if filtered else segment


def open_profile(school_id):
    st.session_state["selected_school"] = school_id
    st.switch_page(st.session_state["pages"]["profile"])


# ---- takeaways + KPI tiles + charts ---------------------------------------------------------------------------
left, right = st.columns([1, 3.1], gap="medium")

best = view.iloc[0]
top = view[view["tier"] == "Top opportunity"]
shown = top if len(top) else view
rank_note = f"#{int(best['segment_rank'])} in {segment}"
items = [
    ("trophy", f"{best['name']} ranks {rank_note}" if not filtered else f"{best['name']} leads here ({rank_note})",
     reasons(best, events, limit=1, cities=cities)[0]),
    ("trend", f"{len(top)} top {'opportunity' if len(top) == 1 else 'opportunities'}",
     f"The top 10% of {segment} by opportunity index" + (", among these filters" if filtered else "")),
    ("target", f"{int((shown['reported_result'] < 0).sum())} of {len(shown)} "
               f"{'top schools' if len(top) else 'schools'} ran a deficit",
     "Athletics spending exceeded revenue in FY2025, a reason to want new sponsorship money"),
]
left.html('<div class="takeaways"><div class="head">Top takeaways</div>' + "".join(
    f'<div class="item">{ICONS[icon]}<div><b>{style.esc(head)}</b><span>{style.esc(body)}</span></div></div>'
    for icon, head, body in items) + "</div>")

with right:
    style.grid([
        style.kpi(money(view["commercial_revenue"].sum()), "Sponsorship & licensing revenue",
                  f"Combined, {scope}, FY2025"),
        style.kpi(f"{len(view)}", "Schools analyzed",
                  f"of {len(group)} in {segment}" if filtered else "Public FBS athletic departments"),
        style.kpi(f"{len(top)}", "Top opportunities", f"Top 10% of {segment}", icon=ICONS["star"]),
        style.kpi(f"{int((view['reported_result'] < 0).sum())} of {len(view)}", "Ran an athletics deficit",
                  "Spending above revenue, FY2025"),
    ], min_width=190)

    chart, donut = st.columns([2.55, 1], gap="medium")
    with chart.container(border=True, key="panel_landscape"):
        st.html('<div class="panel-title">Opportunity landscape</div><div class="panel-sub">Commercial opportunity '
                f'vs. financial pressure, each scored 0–100 within {style.esc(segment)}. Click a school to open it.</div>')
        def label_positions(d):
            """First label spot (above, below, right, left) that no nearby label already uses."""
            placed, out = [], []
            for x, y in zip(d["commercial_opportunity"], d["financial_pressure"]):
                taken = {pos for px, py, pos in placed if abs(x - px) < 24 and abs(y - py) < 10}
                options = ["bottom center", "middle right", "middle left"] if y > 95 else                     ["top center", "bottom center", "middle right", "middle left"]
                pos = next((o for o in options if o not in taken), options[0])
                placed.append((x, y, pos))
                out.append(pos)
            return out

        fig = go.Figure()
        for tier in TIERS:
            d = view[view["tier"] == tier]
            if d.empty:
                continue
            labelled = tier == "Top opportunity"
            fig.add_trace(go.Scatter(
                x=d["commercial_opportunity"], y=d["financial_pressure"], name=tier,
                mode="markers+text" if labelled else "markers",
                text=d["name"] if labelled else None, textposition=label_positions(d) if labelled else None,
                textfont=dict(size=12, color=style.INK, family="Inter"),
                marker=dict(size=15 if labelled else 11, color=style.TIER_COLORS[tier],
                            line=dict(width=1.5, color="#FFFFFF" if tier != "Lower" else "#A592F7")),
                customdata=list(zip(d.index, d["name"], d["conference_id"].map(lambda c: CONFERENCE_NAMES.get(c, c)),
                                    d["segment_rank"].astype(int), d["overall"])),
                hovertemplate="<b>%{customdata[1]}</b> · %{customdata[2]}<br>"
                              f"#%{{customdata[3]}} in {segment} · {tier}<br>"
                              "Commercial opportunity %{x:.0f} · Financial pressure %{y:.0f}<br>"
                              "Opportunity index %{customdata[4]:.0f}<extra></extra>"))
        axis = dict(range=[-3, 105], showgrid=True, gridcolor="#EEF0F4", zeroline=False, fixedrange=True,
                    tickfont=dict(color=style.MUTED), title_font=dict(color=style.INK, size=13))
        fig.update_layout(
            height=360, margin=dict(l=55, r=10, t=36, b=50), plot_bgcolor="#fff", paper_bgcolor="#fff",
            font=dict(family="Inter", color=style.INK), hoverlabel=dict(bgcolor="#fff", font_size=13),
            xaxis=dict(axis, title="Commercial opportunity score"),
            yaxis=dict(axis, title="Financial pressure score"),
            legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom", font=dict(size=12), title=dict(text="")))
        picked = st.plotly_chart(fig, theme=None, width="stretch", on_select="rerun", selection_mode="points",
                                 config={"displayModeBar": False}, key=f"landscape.{segment}")
        if picked and picked.selection.points:
            open_profile(picked.selection.points[0]["customdata"][0])

    with donut.container(border=True, key="panel_tiers"):
        counts = view["tier"].value_counts().reindex(TIERS, fill_value=0)
        st.html('<div class="panel-title">Opportunity by tier</div>'
                f'<div class="panel-sub">Rank within {style.esc(segment)}</div>')
        pie = go.Figure(go.Pie(
            labels=TIERS, values=counts.values, hole=0.66, sort=False, direction="clockwise",
            marker=dict(colors=[style.TIER_COLORS[t] for t in TIERS], line=dict(color="#fff", width=2)),
            textinfo="none", hovertemplate="%{label}: %{value} schools<extra></extra>"))
        pie.update_layout(height=200, margin=dict(l=0, r=0, t=4, b=0), showlegend=False, paper_bgcolor="#fff",
                          font=dict(family="Inter"),
                          annotations=[dict(text=f"<b style='font-size:30px'>{len(view)}</b><br>schools",
                                            showarrow=False, font=dict(size=14, color=style.INK))])
        st.plotly_chart(pie, theme=None, width="stretch", config={"displayModeBar": False}, key="tiers")
        st.html('<div class="legend">' + "".join(
            f'<div><i style="background:{style.TIER_COLORS[t]}"></i>{style.esc(t)} '
            f'<em>({style.TIER_NOTES[t]})</em><b>{counts[t]}</b></div>' for t in TIERS) + "</div>")

# ---- full ranking table ---------------------------------------------------------------------------------------
rank_label = f"Rank in {'Power 4' if segment == 'Power 4' else 'Group of 5'}"
table = view.assign(
    Rank=view["segment_rank"].astype(int),
    School=view["name"],
    Conference=view["conference_id"].map(lambda c: CONFERENCE_NAMES.get(c, c)),
    Tier=view["tier"],
    FP=view["financial_pressure"].round(0),
    CO=view["commercial_opportunity"].round(0),
    Index=view["overall"].round(0),
)[["Rank", "School", "Conference", "Tier", "FP", "CO", "Index"]]
with st.container(border=True, key="panel_ranking"):
    head, export = st.columns([4, 1], vertical_alignment="center")
    head.html(f'<div class="panel-title">{style.esc(segment)} sponsorship opportunity ranking</div>'
              '<div class="panel-sub">Ranks compare schools within this group only. Click a row to open the school.</div>')
    export.download_button(
        "Export rankings", table.rename(columns={"Rank": rank_label, "FP": "Financial pressure",
                                                 "CO": "Commercial opportunity", "Index": "Opportunity index"})
        .to_csv(index=False).encode("utf-8"),
        file_name=f"sponsorship-opportunity-{'power-4' if segment == 'Power 4' else 'group-of-5'}.csv",
        mime="text/csv", icon=":material/download:", width="stretch")
    score = lambda label, help_: st.column_config.ProgressColumn(label, min_value=0, max_value=100, format="%d",
                                                                 help=help_, width="medium")
    event = st.dataframe(
        table, hide_index=True, width="stretch", height=min(36 * (len(table) + 1) + 4, 560),
        on_select="rerun", selection_mode="single-row", key=f"ranking.{segment}",
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="%d", width="small", help=f"{rank_label} (not national)"),
            "School": st.column_config.TextColumn(width="medium"),
            "Tier": st.column_config.TextColumn(width="medium"),
            "FP": score("Financial pressure", "How much the department needs new revenue (35% of the index)"),
            "CO": score("Commercial opportunity", "How much room there is to grow sponsorship (45% of the index)"),
            "Index": score("Opportunity index", "Financial pressure 35%, commercial opportunity 45%, momentum 20% "
                                                "(momentum is shown on each school's profile)"),
        })
    if event.selection.rows:
        open_profile(table.index[event.selection.rows[0]])
st.caption("Tiers: Top opportunity = top 10% of the group, Strong = next 20%, Moderate = middle 40%, "
           "Lower = bottom 30%. The index ranks opportunity, not unsold inventory.")

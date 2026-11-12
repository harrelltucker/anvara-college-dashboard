import copy

import plotly.graph_objects as go
import streamlit as st

from engine.scoring import score_schools
from ui import style
from ui.fmt import CONFERENCE_NAMES
from ui.public import STATES
from ui.state import DEFAULTS, context

ctx = context()
scored, tables, weights = ctx["scored"], ctx["tables"], ctx["weights"]
ranked = scored.dropna(subset=["overall"])
CATS = {   # weight key: (slider label, what it measures)
    "financial_pressure": ("Financial pressure", "How much the department needs new revenue: deficit, subsidy, "
                                                 "revenue vs. its conference"),
    "commercial_opportunity": ("Commercial opportunity", "How much room there is to grow sponsorship: revenue per "
                                                         "fan, audience size, local competition"),
    "growth_catalysts": ("Momentum", "Recent moves to build its commercial business, since 2024"),
}
TIERS = list(style.TIER_COLORS)
ALL_FBS = "All FBS"
GROUP_COLORS = {"Power 4": style.ACCENT, "Group of 5 & other FBS": "#E07B39"}
SHORT = {"Power 4": "Power 4", "Group of 5 & other FBS": "Group of 5"}
SLUG = {ALL_FBS: "all-fbs", "Power 4": "power-4", "Group of 5 & other FBS": "group-of-5"}

# ---- header bar with filters ----------------------------------------------------------------------------------
f_group, f_conf, f_state = style.topbar(
    "113 public FBS athletic departments, ranked within their group (Power 4, or Group of 5 & other FBS)", controls=3)
segment = f_group.selectbox("Group", [ALL_FBS, "Power 4", "Group of 5 & other FBS"], key="segment_view")
in_group = lambda d: d if segment == ALL_FBS else d[d["segment"] == segment]
confs_all = in_group(ranked)
confs = sorted(confs_all["conference_id"].unique(), key=lambda c: CONFERENCE_NAMES.get(c, c))
conf = f_conf.selectbox("Conference", ["All conferences"] + confs,
                        format_func=lambda c: CONFERENCE_NAMES.get(c, c), key=f"conf_view.{segment}")
states = sorted(confs_all["state"].unique(), key=lambda s: STATES.get(s, s))
state = f_state.selectbox("Location", ["All locations"] + states, format_func=lambda s: STATES.get(s, s),
                          key=f"state_view.{segment}")


def open_profile(school_id):
    st.session_state["selected_school"] = school_id
    st.switch_page(st.session_state["pages"]["profile"])


def reset_weights():
    for c in CATS:
        st.session_state[f"pw.{c}"] = DEFAULTS["categories"][c]


# ---- the exercise: what's being ranked, and the weights (re-ranks everything below) ---------------------------
left, right = st.columns([1, 3.1], gap="medium")
for c in CATS:       # sliders forget their value when you leave the page; restore from the last weights used
    st.session_state.setdefault(f"pw.{c}", weights["categories"][c])
with left.container(border=True, key="panel_weights"):
    st.html('<div class="panel-title">How this ranking works</div><div class="panel-sub" style="margin-top:0.4rem">'
            "Every school gets three scores from 0 to 100, each compared only with the schools in its group. "
            "The opportunity index blends them using these weights. Drag a slider to see how the ranking changes."
            "</div>")
    for c, (label, what) in CATS.items():
        st.slider(label, 0, 100, step=5, key=f"pw.{c}", help=what)
    picked_weights = {c: st.session_state[f"pw.{c}"] for c in CATS}
    total = sum(picked_weights.values())
    if total == 0:
        st.warning("All weights are zero, so the default weights are used.")
        picked_weights, total = dict(DEFAULTS["categories"]), sum(DEFAULTS["categories"].values())
    st.html('<div class="fine">Index = ' + " + ".join(
        f"{picked_weights[c] / total:.0%} {CATS[c][0].lower()}" for c in CATS) + ". Default weights are "
        + " / ".join(str(DEFAULTS["categories"][c]) for c in CATS)
        + ": starting assumptions, not proven predictors.</div>")
    st.button("Reset to default weights", on_click=reset_weights, type="tertiary", icon=":material/restart_alt:")

if picked_weights != weights["categories"]:
    weights = copy.deepcopy(weights)
    weights["categories"] = picked_weights
    scored = score_schools(tables, weights)
    ranked = scored.dropna(subset=["overall"])
st.session_state["weights"] = weights       # profiles show ranks under the same weights
view = in_group(ranked)
if conf != "All conferences":
    view = view[view["conference_id"] == conf]
if state != "All locations":
    view = view[view["state"] == state]
if segment == ALL_FBS:     # ranks only compare schools within a group, so mix the groups by tier, not by rank
    view = view.assign(_tier=view["tier"].map(TIERS.index)).sort_values(["_tier", "segment_rank", "name"])
else:
    view = view.sort_values(["segment_rank", "name"])
if view.empty:
    st.info("No schools match these filters.")
    st.stop()
# ---- charts ---------------------------------------------------------------------------------------------------
with right:
    chart, donut = st.columns([2.55, 1], gap="medium")
    with chart.container(border=True, key="panel_landscape"):
        st.html('<div class="panel-title">Two markets</div><div class="panel-sub">Football crowd vs. sponsorship '
                'revenue, in real numbers (log scale). Large outlined dots: the top opportunities in each group. '
                'Hover for names; click to open a school.</div>' if segment == ALL_FBS else
                '<div class="panel-title">Opportunity landscape</div><div class="panel-sub">Commercial opportunity '
                f'vs. financial pressure, each scored 0–100 within {style.esc(segment)}. Click a school to open it.</div>')
        def label_positions(xs, ys):
            """First label spot (above, below, right, left) that no nearby label already uses. xs, ys on 0-100."""
            placed, out = [], []
            for x, y in zip(xs, ys):
                taken = {pos for px, py, pos in placed if abs(x - px) < 24 and abs(y - py) < 10}
                options = (["bottom center", "middle right", "middle left"] if y > 95
                           else ["top center", "bottom center", "middle right", "middle left"])
                level = {pos for px, py, pos in placed if abs(x - px) < 24 and abs(y - py) < 5}
                if level & {"top center", "bottom center"}:    # a neighbour at the same height: go sideways
                    options = ["middle right", "middle left"] + options
                pos = next((o for o in options if o not in taken), options[0])
                placed.append((x, y, pos))
                out.append(pos)
            return out

        if segment == ALL_FBS:     # real fans and dollars: the one view where the two groups can share axes
            d = view[(view["commercial_revenue"] > 0) & view["football"].notna()]
            fig = go.Figure()
            for grp, color in GROUP_COLORS.items():
                for top in (False, True):
                    g = d[(d["segment"] == grp) & ((d["tier"] == "Top opportunity") == top)]
                    if g.empty:
                        continue
                    fig.add_trace(go.Scatter(
                        x=g["football"], y=g["commercial_revenue"] / 1e6, name=SHORT[grp], legendgroup=grp,
                        showlegend=not top, mode="markers",     # top schools cluster too tightly to label
                        marker=dict(size=16 if top else 9, color=color, opacity=1 if top else 0.6,
                                    line=dict(width=2 if top else 1, color=style.NAVY if top else "#FFFFFF")),
                        customdata=list(zip(g.index, g["name"],
                                            g["conference_id"].map(lambda c: CONFERENCE_NAMES.get(c, c)),
                                            g["segment_rank"].astype(int), g["tier"])),
                        hovertemplate="<b>%{customdata[1]}</b> · %{customdata[2]}<br>"
                                      f"#%{{customdata[3]}} in {SHORT[grp]} · %{{customdata[4]}}<br>"
                                      "Football crowd %{x:,.0f} · Sponsorship $%{y:.1f}M<extra></extra>"))
            axis = dict(type="log", showgrid=True, gridcolor="#EEF0F4", zeroline=False, fixedrange=True,
                        tickfont=dict(color=style.MUTED), title_font=dict(color=style.INK, size=13))
            fig.update_layout(
                height=360, margin=dict(l=55, r=10, t=36, b=50), plot_bgcolor="#fff", paper_bgcolor="#fff",
                font=dict(family="Inter", color=style.INK), hoverlabel=dict(bgcolor="#fff", font_size=13),
                xaxis=dict(axis, title="Average football crowd, 2024", tickvals=[10_000, 20_000, 50_000, 100_000],
                           ticktext=["10k", "20k", "50k", "100k"]),
                yaxis=dict(axis, title="Sponsorship & licensing, FY2025", tickvals=[0.3, 1, 3, 10, 30],
                           ticktext=["$0.3M", "$1M", "$3M", "$10M", "$30M"]),
                legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom", font=dict(size=12), title=dict(text="")))
        else:
            fig = go.Figure()
            for tier in TIERS:
                d = view[view["tier"] == tier]
                if d.empty:
                    continue
                labelled = tier == "Top opportunity"
                fig.add_trace(go.Scatter(
                    x=d["commercial_opportunity"], y=d["financial_pressure"], name=tier,
                    mode="markers+text" if labelled else "markers",
                    text=d["name"] if labelled else None, textposition=label_positions(d["commercial_opportunity"], d["financial_pressure"])
                    if labelled else None,
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
                + ('<div class="panel-sub">Tier within each school&#39;s own group</div>' if segment == ALL_FBS else
                  f'<div class="panel-sub">Rank within {style.esc(segment)}</div>'))
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
rank_label = "Rank in group" if segment == ALL_FBS else f"Rank in {SHORT[segment]}"
table = view.assign(
    Rank=view["segment_rank"].astype(int),
    School=view["name"],
    Conference=view["conference_id"].map(lambda c: CONFERENCE_NAMES.get(c, c)),
    Tier=view["tier"],
    FP=view["financial_pressure"].round(0),
    CO=view["commercial_opportunity"].round(0),
    Index=view["overall"].round(0),
)[["Rank", "School", "Conference", "Tier", "FP", "CO", "Index"]]
if segment == ALL_FBS:
    table = table.assign(Group=view["segment"].map(SHORT), Sponsorship=(view["commercial_revenue"] / 1e6).round(1))[
        ["Rank", "Group", "School", "Conference", "Tier", "Sponsorship", "FP", "CO", "Index"]]
with st.container(border=True, key="panel_ranking"):
    head, export = st.columns([4, 1], vertical_alignment="center")
    head.html(f'<div class="panel-title">{style.esc(segment)} sponsorship opportunity ranking</div>'
              + ('<div class="panel-sub">Both groups, sorted by tier. Ranks, tiers and scores compare each school '
                 'only with its own group, so a Power 4 rank and a Group of 5 rank are not comparable. '
                 'Click a row to open the school.</div>' if segment == ALL_FBS else
                 '<div class="panel-sub">Ranks compare schools within this group only. '
                 'Click a row to open the school.</div>'))
    export.download_button(
        "Export rankings", table.rename(columns={"Rank": rank_label, "Sponsorship": "Sponsorship ($M)", "FP": "Financial pressure",
                                                 "CO": "Commercial opportunity", "Index": "Opportunity index"})
        .to_csv(index=False).encode("utf-8"),
        file_name=f"sponsorship-opportunity-{SLUG[segment]}.csv",
        mime="text/csv", icon=":material/download:", width="stretch")
    score = lambda label, help_: st.column_config.ProgressColumn(label, min_value=0, max_value=100, format="%d",
                                                                 help=help_,
                                                                 width="small" if segment == ALL_FBS else "medium")
    if segment == ALL_FBS:     # two extra columns: shorter score headers so the table fits
        short = {"FP": "Pressure", "CO": "Commercial", "Index": "Index"}
    else:
        short = {"FP": "Financial pressure", "CO": "Commercial opportunity", "Index": "Opportunity index"}
    event = st.dataframe(
        table, hide_index=True, width="stretch", height=min(36 * (len(table) + 1) + 4, 560),
        on_select="rerun", selection_mode="single-row", key=f"ranking.{segment}",
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="%d", width="small", help=f"{rank_label} (not national)"),
            "Group": st.column_config.TextColumn(width="small"),
            "Sponsorship": st.column_config.NumberColumn(
                "Sponsorship", format="$%.1fM",
                help="Sponsorship & licensing revenue, FY2025, in real dollars (comparable across groups)"),
            "School": st.column_config.TextColumn(width="medium"),
            "Tier": st.column_config.TextColumn(width="medium"),
            "FP": score(short["FP"], "How much the department needs new revenue (35% of the index)"),
            "CO": score(short["CO"], "How much room there is to grow sponsorship (45% of the index)"),
            "Index": score(short["Index"], "Financial pressure 35%, commercial opportunity 45%, momentum 20% "
                                                "(momentum is shown on each school's profile)"),
        })
    if event.selection.rows:
        open_profile(table.index[event.selection.rows[0]])
st.caption("Tiers: Top opportunity = top 10% of the group, Strong = next 20%, Moderate = middle 40%, "
           "Lower = bottom 30%. The index ranks opportunity, not unsold inventory.")

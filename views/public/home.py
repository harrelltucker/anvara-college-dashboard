import streamlit as st

from ui import style
from ui.fmt import CONFERENCE_NAMES
from ui.public import STATES, reasons, top_events
from ui.state import context

ctx = context()
scored, tables, weights = ctx["scored"], ctx["tables"], ctx["weights"]
events = top_events(tables, weights)

ranked = scored.dropna(subset=["overall"])
style.hero("College sponsorship · FY2025", "Where college sponsorship is most likely to grow",
           "All 113 public FBS athletic departments, ranked on three questions: how much they need new revenue, "
           "how much room they have to grow sponsorship, and what they're already doing about it.",
           extra=style.stats([(f"{len(ranked)}", "schools ranked"),
                              (f"{(ranked['tier'] == 'Top opportunity').sum()}", "top opportunities"),
                              ("3", "questions per school"), (f"{len(tables['sources'])}", "public sources")]))

segment = st.segmented_control("Group", ["Power 4", "Group of 5 & other FBS"], default="Power 4",
                               key="segment_view", label_visibility="collapsed") or "Power 4"
view = scored[scored["segment"] == segment].dropna(subset=["overall"]).sort_values(["segment_rank", "name"])


def open_profile(school_id):
    st.session_state["selected_school"] = school_id
    st.switch_page(st.session_state["pages"]["profile"])


def opp_card(sid, row):
    conf = CONFERENCE_NAMES.get(row["conference_id"], row["conference_id"])
    items = "".join(f"<li>{style.esc(r)}</li>" for r in reasons(row, events))
    return (f'<a class="opp-card" href="profile?school={sid}">'
            f'<div class="opp-head"><span class="opp-num">#{int(row["segment_rank"])}</span>{style.pill(row["tier"])}</div>'
            f'<div class="opp-name">{style.esc(row["name"])}</div>'
            f'<div class="opp-meta">{style.esc(conf)} · {style.esc(STATES.get(row["state"], row["state"]))}</div>'
            f'<ul class="ticks">{items}</ul><div class="opp-go">View profile →</div></a>')


top = view[view["tier"] == "Top opportunity"]
st.html(f'<div class="section">Top {len(top)} opportunities in {style.esc(segment)}</div>')
style.grid([opp_card(sid, row) for sid, row in top.iterrows()], min_width=340)

st.html(f'<div class="section">All {len(view)} schools</div>')
table = view.assign(
    Rank=view["segment_rank"].astype(int),
    School=view["name"],
    Conference=view["conference_id"].map(lambda c: CONFERENCE_NAMES.get(c, c)),
    Tier=view["tier"],
    Why=[reasons(r, events, limit=1)[0] for _, r in view.iterrows()],
)[["Rank", "School", "Conference", "Tier", "Why"]]
event = st.dataframe(
    table, hide_index=True, width="stretch", height=min(36 * (len(table) + 1) + 4, 640),
    on_select="rerun", selection_mode="single-row",
    column_config={"Rank": st.column_config.NumberColumn("#", format="%d", width="small"),
                   "School": st.column_config.TextColumn(width="medium"),
                   "Tier": st.column_config.TextColumn(width="small"),
                   "Why": st.column_config.TextColumn("Main reason", width="large")})
st.caption("Click a school to open its profile. Tiers: Top opportunity = top 10% of the group, Strong = next 20%, "
           "Moderate = middle 40%, Lower = bottom 30%.")
if event.selection.rows:
    open_profile(table.index[event.selection.rows[0]])

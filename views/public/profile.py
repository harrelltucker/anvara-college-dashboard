import pandas as pd
import streamlit as st

from ui import style
from ui.fmt import CONFERENCE_NAMES, money
from ui.public import LABELS, MEANING, STATES, big_league_cities, reasons, short_title, top_events
from ui.state import context, rights_summary

ctx = context()
scored, tables, weights = ctx["scored"], ctx["tables"], ctx["weights"]
sources = tables["sources"].set_index("source_id")

ids = list(scored.sort_values("name").index)
linked = st.query_params.get("school")      # set by the cards on Top opportunities
default = linked if linked in ids else st.session_state.get("selected_school", scored.index[0])
_, pick = st.columns([3, 1])
school_id = pick.selectbox("Switch school", ids, index=ids.index(default) if default in ids else 0,
                           format_func=lambda s: scored.loc[s, "name"])
st.session_state["selected_school"] = school_id
st.query_params["school"] = school_id
row = scored.loc[school_id]
conf = CONFERENCE_NAMES.get(row["conference_id"], row["conference_id"])

ranked = pd.notna(row["segment_rank"])
side = (f'<div class="rank-tile"><div class="big">#{int(row["segment_rank"])}</div>'
        f'<div class="of">of {int(row["segment_size"])} in {style.esc(row["segment"])}</div></div>') if ranked else ""
style.hero(f"{conf} · {STATES.get(row['state'], row['state'])}", row["name"],
           extra=f'<div style="margin-top:0.7rem">{style.pill(row["tier"])}</div>' if ranked else
           '<div class="sub">Not enough data to rank</div>', side=side)

left, right = st.columns([3, 2], gap="large")
with left:
    st.html('<div class="section">Why it\'s an opportunity</div><div class="callout"><ul class="ticks">'
            + "".join(f"<li>{style.esc(r)}</li>" for r in reasons(row, top_events(tables, weights), limit=4,
                                                         cities=big_league_cities(tables)))
            + "</ul></div>")
with right:
    st.html('<div class="section">How it scores</div>' + "".join(
        style.meter(LABELS[c], row[c], MEANING[c]) for c in LABELS)
        + '<div class="fine">Each score compares the school with the others in its group: '
          '100 = highest in the group, 0 = lowest.</div>')

st.html('<div class="section">Key numbers · FY2025</div>')
deficit = row["reported_result"]
style.grid([style.card(*c) for c in [
    ("Athletics revenue", money(row["total_operating_revenue"]), f"Expenses {money(row['total_operating_expenses'])}"),
    ("Surplus / deficit", money(deficit), "Revenue minus expenses, as reported to the NCAA"),
    ("Sponsorship & licensing", money(row["commercial_revenue"]), "Includes advertising and licensing"),
    ("Football crowd", "—" if pd.isna(row["football"]) else f"{row['football']:,.0f}",
     "Average home attendance, 2024"
     + ("" if pd.isna(row["mens_basketball"]) else f" · basketball {row['mens_basketball']:,.0f}")),
]], min_width=220)

cats = tables["catalysts"][tables["catalysts"]["school_id"] == school_id]
if len(cats):
    cats = cats.sort_values("event_date", ascending=False).drop_duplicates("event_id")
    link = lambda sid: (f' · <a href="{style.esc(sources.loc[sid, "url"])}">source</a>' if sid in sources.index else "")
    st.html('<div class="section">Recent moves</div><ul class="timeline">'
            + "".join(f'<li><span class="when">{str(c["event_date"])[:7]}</span>'
                      f'{style.esc(short_title(c["title"]))}{link(c["source_id"])}</li>'
                      for _, c in cats.head(6).iterrows()) + "</ul>")

rights = rights_summary(tables).get(school_id)
contacts = tables["contacts"][tables["contacts"]["school_id"] == school_id]
if rights or len(contacts):
    st.html('<div class="section">Who sells its sponsorships</div>')
    if rights:
        st.markdown(f"**Rights holder:** {rights}")
    if len(contacts):
        st.dataframe(contacts[["name", "title", "profile_url"]], hide_index=True, width="stretch",
                     column_config={"name": "Name", "title": "Title",
                                    "profile_url": st.column_config.LinkColumn("Profile", display_text="Staff page")})

fin = row["financial_source_id"]
if fin in sources.index:
    st.caption(f"Financials: [{sources.loc[fin, 'title']}]({sources.loc[fin, 'url']}). Attendance: NCAA. "
               "All sources are listed on the Sources page.")

import pandas as pd
import streamlit as st

from ui import style
from ui.fmt import CONFERENCE_NAMES, money
from ui.public import LABELS, MEANING, STATES, reasons, short_title, top_events
from ui.state import context, rights_summary

ctx = context()
scored, tables, weights = ctx["scored"], ctx["tables"], ctx["weights"]
sources = tables["sources"].set_index("source_id")

ids = list(scored.sort_values("name").index)
default = st.session_state.get("selected_school", scored.index[0])
school_id = st.selectbox("School", ids, index=ids.index(default) if default in ids else 0,
                         format_func=lambda s: scored.loc[s, "name"], label_visibility="collapsed")
st.session_state["selected_school"] = school_id
row = scored.loc[school_id]
conf = CONFERENCE_NAMES.get(row["conference_id"], row["conference_id"])

ranked = pd.notna(row["segment_rank"])
style.hero(f"{conf} · {STATES.get(row['state'], row['state'])}", row["name"],
           f"{row['tier']} · #{int(row['segment_rank'])} of {int(row['segment_size'])} in {row['segment']}"
           if ranked else "Not enough data to rank")

left, right = st.columns([3, 2], gap="large")
with left:
    st.html('<div class="section">Why it\'s an opportunity</div>'
            + "<ul class='why-list'>" + "".join(f"<li>{style.esc(r)}</li>"
                                                for r in reasons(row, top_events(tables, weights), limit=4))
            + "</ul>")
with right:
    st.html('<div class="section">How it scores</div>' + "".join(
        style.meter(LABELS[c], row[c], MEANING[c]) for c in LABELS)
        + '<div class="fine">Each score compares the school with the others in its group: '
          '100 = highest in the group, 0 = lowest.</div>')

st.html('<div class="section">Key numbers · FY2025</div>')
deficit = row["reported_result"]
style.cards([
    ("Athletics revenue", money(row["total_operating_revenue"]), f"Expenses {money(row['total_operating_expenses'])}"),
    ("Surplus / deficit", money(deficit), "Revenue minus expenses, as reported to the NCAA"),
    ("Sponsorship & licensing", money(row["commercial_revenue"]), "Includes advertising and licensing"),
    ("Football crowd", "—" if pd.isna(row["football"]) else f"{row['football']:,.0f}",
     "Average home attendance, 2024"
     + ("" if pd.isna(row["mens_basketball"]) else f" · basketball {row['mens_basketball']:,.0f}")),
])

cats = tables["catalysts"][tables["catalysts"]["school_id"] == school_id]
if len(cats):
    cats = cats.sort_values("event_date", ascending=False).drop_duplicates("event_id")
    link = lambda sid: (f" · [source]({sources.loc[sid, 'url']})" if sid in sources.index else "")
    st.html('<div class="section">Recent moves</div>')
    st.markdown("\n".join(f"- **{str(c['event_date'])[:7]}** · {short_title(c['title'])}{link(c['source_id'])}"
                          for _, c in cats.head(6).iterrows()))

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

"""College Sponsorship Opportunity Dashboard.

Run:   streamlit run app.py
"""

import streamlit as st

from ui import style
from ui.state import PUBLIC, sidebar

st.set_page_config(page_title="College Sponsorship Opportunity", page_icon=":material/stadium:",
                   layout="wide")
style.apply(public=PUBLIC)

PAGES = {
    "rankings": st.Page("views/rankings.py", title="Rankings", icon=":material/leaderboard:", default=True),
    "profile": st.Page("views/profile.py", title="School profile", icon=":material/school:"),
    "charts": st.Page("views/charts.py", title="Market view", icon=":material/insights:"),
    "research": st.Page("views/research.py", title="Research & data quality", icon=":material/fact_check:"),
    "methodology": st.Page("views/methodology.py", title="Methodology", icon=":material/menu_book:"),
}
if PUBLIC:     # the shared copy: answers and sources only, default weights, top navigation, no sidebar
    PAGES = {
        "rankings": st.Page("views/public/home.py", title="Top opportunities", icon=":material/leaderboard:",
                            default=True),
        "profile": st.Page("views/public/profile.py", title="School profiles", icon=":material/school:"),
        "method": st.Page("views/public/method.py", title="How it works", icon=":material/menu_book:"),
        "sources": st.Page("views/public/sources.py", title="Sources", icon=":material/library_books:"),
    }
st.session_state["pages"] = PAGES

nav = st.navigation(list(PAGES.values()), position="top" if PUBLIC else "sidebar")
if not PUBLIC:
    _, st.session_state["weights"] = sidebar()
nav.run()
style.footer()

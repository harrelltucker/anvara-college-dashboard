"""College Sponsorship Opportunity Dashboard.

Run:   streamlit run app.py
"""

import streamlit as st

from ui import style
from ui.state import sidebar

st.set_page_config(page_title="College Sponsorship Opportunity", page_icon=":material/stadium:",
                   layout="wide")
style.apply()

PAGES = {
    "rankings": st.Page("views/rankings.py", title="Rankings", icon=":material/leaderboard:", default=True),
    "profile": st.Page("views/profile.py", title="School profile", icon=":material/school:"),
    "charts": st.Page("views/charts.py", title="Market view", icon=":material/insights:"),
    "research": st.Page("views/research.py", title="Research & data quality", icon=":material/fact_check:"),
    "methodology": st.Page("views/methodology.py", title="Methodology", icon=":material/menu_book:"),
}
st.session_state["pages"] = PAGES

nav = st.navigation(list(PAGES.values()))
_, st.session_state["weights"] = sidebar()
nav.run()
style.footer()

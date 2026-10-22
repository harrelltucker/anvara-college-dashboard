"""College Sponsorship Opportunity Dashboard.

Run:   streamlit run app.py
"""

import streamlit as st

from ui.state import sidebar

st.set_page_config(page_title="College Sponsorship Opportunity", page_icon="🏟️", layout="wide")

PAGES = {
    "rankings": st.Page("views/rankings.py", title="Rankings", icon="🏆", default=True),
    "profile": st.Page("views/profile.py", title="School profile", icon="🏫"),
    "charts": st.Page("views/charts.py", title="Market view", icon="📊"),
    "research": st.Page("views/research.py", title="Research & data quality", icon="🔎"),
    "methodology": st.Page("views/methodology.py", title="Methodology", icon="📐"),
}
st.session_state["pages"] = PAGES

nav = st.navigation(list(PAGES.values()))
_, st.session_state["weights"] = sidebar()
nav.run()

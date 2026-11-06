import streamlit as st

from ui import style
from ui.state import context

ctx = context()
src = ctx["tables"]["sources"]

style.hero("Sources", "Where the numbers come from",
           "Every figure links back to a public source. Primary documents are used wherever they exist.")

st.markdown("""
- **Finances (FY2025):** the [Knight–Newhouse College Athletics Database](https://knightnewhousedata.org/), compiled from the financial reports schools file with the NCAA, used with permission. Schools' own reports where published.
- **Attendance (2024–25):** NCAA football and basketball attendance records.
- **Markets:** U.S. Census Bureau population estimates and County Business Patterns; NCES college directory; league team lists.
- **Commercial moves, rights holders and contacts:** university and company announcements, rights-holder partner pages, staff directories and news coverage.
""")

TYPES = {"ncaa_financial_report": "School financial report", "university_disclosure": "University disclosure",
         "state_portal": "State portal", "eada": "EADA", "conference": "Conference", "university_release":
         "University announcement", "rights_holder": "Rights holder", "ncaa_statistics": "NCAA statistics",
         "government_statistics": "Government statistics", "news": "News", "other": "Other"}
shown = src[src["source_type"] != "demonstration"].assign(Type=lambda d: d["source_type"].map(TYPES).fillna("Other"))
shown.loc[shown["source_id"] == "KN-FY2025", "Type"] = "Database"
shown = shown.sort_values(["Type", "title"])[["title", "Type", "retrieved_date", "url"]]
st.html(f'<div class="section">All {len(shown)} sources</div>')
st.dataframe(shown, hide_index=True, width="stretch", height=min(36 * (len(shown) + 1) + 4, 640),
             column_config={"title": st.column_config.TextColumn("Source", width="large"),
                            "Type": st.column_config.TextColumn(width="medium"), "retrieved_date": "Retrieved",
                            "url": st.column_config.LinkColumn("Link", display_text="Open")})

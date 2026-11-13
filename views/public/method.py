import streamlit as st

from engine.data import ROOT
from ui import style
from ui.public import LABELS
from ui.state import context

ctx = context()
weights = ctx["weights"]

style.topbar("How the opportunity index is built")
style.hero("How it works", "Three questions, one ranking",
           "Each school is compared with the others in its group (Power 4, or Group of 5 & other FBS) "
           "on three questions, weighted into one opportunity index.")

WHAT = {
    "financial_pressure": "Deficit or surplus, how much of its spending the department earns itself, and how its "
                          "own revenue compares with its conference.",
    "commercial_opportunity": "Sponsorship revenue for its crowd size, total audience (football and basketball), "
                              "and local competition for sponsors.",
    "growth_catalysts": "New commercial companies, in-house sponsorship sales, private capital, jersey-patch and "
                        "naming-rights deals since 2024.",
}
total = sum(weights["categories"].values())
style.grid([f'<div class="card"><div class="label">{style.esc(LABELS[c])}</div>'
            f'<div class="weight">{weights["categories"][c] / total:.0%}</div>'
            f'<div class="note">{style.esc(WHAT[c])}</div></div>' for c in LABELS], min_width=260)

st.html('<div class="section">Reading the results</div>')
st.markdown("""
- **Tiers** are by rank within the group: *Top opportunity* = top 10%, *Strong* = next 20%, *Moderate* = middle 40%, *Lower* = bottom 30%.
- **The index** is the weighted average of the three scores. No school leads on everything, so the top schools land in the 60s and 70s.
- **It ranks opportunity, not unsold inventory.** A high rank means strong reasons to grow sponsorship, not that inventory is available.
- **Data periods:** finances are FY2025 (July 2024 – June 2025) and attendance is the 2024–25 season. Commercial moves run from March 2024 to August 2026. Population is 2025 and local business counts are 2023 (U.S. Census). Sources were checked in October–November 2026.
- **"Sponsorship & licensing"** is the NCAA's reporting line for sponsorship, advertising and licensing together. Schools that sell sponsorships in-house may record some of it elsewhere.
""")

INTERNAL = ("review queue", "Demonstration data", "**Confidence:**", "Data completeness", "Featured schools")
st.html('<div class="section">Full methodology</div>')
text = (ROOT / "docs" / "METHODOLOGY.md").read_text(encoding="utf-8")
st.markdown("\n".join(line for line in text.splitlines() if not any(k in line for k in INTERNAL)))

import streamlit as st

from engine.data import ROOT
from engine.scoring import CATEGORY_LABELS, COMPONENT_LABELS
from ui.state import context

ctx = context()
weights, tables = ctx["weights"], ctx["tables"]

st.title("Methodology")

st.subheader("Weights in effect")
cols = st.columns(3)
for col, group in zip(cols, ("categories", "financial_pressure", "commercial_opportunity")):
    total = sum(weights[group].values())
    col.markdown(f"**{'Categories' if group == 'categories' else CATEGORY_LABELS[group]}**")
    for k, v in weights[group].items():
        col.markdown(f"- {CATEGORY_LABELS.get(k) or COMPONENT_LABELS.get(k)}: {v / total:.0%}")

st.markdown((ROOT / "docs" / "METHODOLOGY.md").read_text(encoding="utf-8"))

st.subheader("Market context (shown, not scored)")
ctx_table = tables["market_context"]
if ctx_table.empty:
    st.info("No market context recorded yet. League-wide changes (e.g., NCAA rules) appear here rather "
            "than adding points to every school; proposed legislation is labeled as a scenario.")
else:
    st.dataframe(ctx_table.sort_values("date", ascending=False), hide_index=True, width="stretch")

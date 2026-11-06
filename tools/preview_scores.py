"""Preview rankings as if every pending finding were verified. Nothing is saved.

Compares the current scoring with the earlier version (raw sponsorship revenue 60 / fan reach 40)
and checks whether Financial Pressure and Commercial Opportunity still pull against each other.

Usage:  python tools/preview_scores.py [--top N]
"""

import copy
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.data import load_findings, load_tables, load_weights  # noqa: E402
from engine.scoring import score_schools  # noqa: E402

OLD_COMMERCIAL = {"commercial_revenue": 60, "fan_reach": 40, "untapped_value": 0, "regional_appeal": 0}


def with_pending(tables):
    """Copy of the tables with every pending finding added, marked as unverified."""
    out = {k: v.copy() for k, v in tables.items()}
    pending = load_findings().query("status == 'pending'")
    for table, group in pending.groupby("target_table"):
        rows = [dict(json.loads(r), source_id="PENDING", verified_by="(pending)", verified_date="")
                for r in group["record_json"]]
        out[table] = pd.concat([out[table], pd.DataFrame(rows)], ignore_index=True).fillna("")
    return out, len(pending)


def main():
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 10
    tables, n = with_pending(load_tables())
    weights = load_weights()
    old_weights = copy.deepcopy(weights)
    old_weights["commercial_opportunity"] = OLD_COMMERCIAL
    new, old = score_schools(tables, weights), score_schools(tables, old_weights)
    print(f"Preview with {n} pending findings treated as verified.\n")

    for seg, g in new.groupby("segment"):
        o = old[old["segment"] == seg]
        print(f"== {seg}: {g['overall'].notna().sum()} of {len(g)} schools scored")
        print("   corr(Financial Pressure, Commercial Opportunity): "
              f"before {o['financial_pressure'].corr(o['commercial_opportunity']):+.2f}, "
              f"now {g['financial_pressure'].corr(g['commercial_opportunity']):+.2f}")
        cols = ["name", "overall", "overall_raw", "financial_pressure", "commercial_opportunity", "growth_catalysts",
                "commercial_opportunity.untapped_value", "fan_reach_score", "regional_appeal_score", "market_scope"]
        view = g.sort_values("overall", ascending=False)[cols].head(top).copy()
        view.insert(1, "was #", view.index.map(o["segment_rank"]))
        view.columns = ["school", "was #", "score", "raw", "fin.press", "comm.opp", "catalysts", "untapped",
                        "fan reach", "regional", "market"]
        print(view.round(0).to_string(), "\n")


if __name__ == "__main__":
    main()

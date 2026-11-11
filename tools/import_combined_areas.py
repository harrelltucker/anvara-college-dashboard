"""Queue each market's Census Combined Statistical Area, so a metro next to a big-league city (Boulder, next to
Denver) competes with that city's teams.

Download (kept out of Git, in data/incoming/market/csa/):
  list1_2023.xlsx     Census metro and combined-area delineation, July 2023 (OMB Bulletin 23-01)

Covers every metro in school_markets and market_teams that belongs to a combined area. All rows share one
source, so the file is verified once in the review queue.

Usage:
  python tools/import_combined_areas.py            (preview)
  python tools/import_combined_areas.py --submit   (queue findings)
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.data import RESEARCH_DIR, ROOT, load_findings, load_tables  # noqa: E402
from engine.research import submit_finding  # noqa: E402

FILE = ROOT / "data" / "incoming" / "market" / "csa" / "list1_2023.xlsx"
BY = "tools/import_combined_areas.py"
SOURCE = ("Core Based Statistical Areas (CBSAs), Metropolitan Divisions, and Combined Statistical Areas (CSAs), "
          "July 2023 delineation file (U.S. Census Bureau)",
          "https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/"
          "list1_2023.xlsx")


def main():
    d = pd.read_excel(FILE, header=2, dtype=str).dropna(subset=["CBSA Code"])
    d = d.dropna(subset=["CSA Code"]).drop_duplicates("CBSA Code").set_index("CBSA Code")
    tables = load_tables(RESEARCH_DIR)
    needed = sorted(set(tables["school_markets"]["cbsa_code"]) | set(tables["market_teams"]["cbsa_code"]))
    rows = [{"cbsa_code": c, "cbsa_title": d.loc[c, "CBSA Title"], "csa_code": d.loc[c, "CSA Code"],
             "csa_title": d.loc[c, "CSA Title"]} for c in needed if c in d.index]
    print(f"{len(rows)} of {len(needed)} market metros belong to a combined area")
    for r in rows:
        print(f"  {r['cbsa_title'][:45]:<45} -> {r['csa_title']}")

    if "--submit" not in sys.argv:
        print("Preview only. Re-run with --submit to queue findings.")
        return
    queued = {(f["target_table"], f["record_json"]) for _, f in load_findings().iterrows()}
    n = 0
    for record in rows:
        if ("market_areas", json.dumps(record, ensure_ascii=False)) in queued:     # re-runs don't duplicate
            continue
        submit_finding("market_areas", record, *SOURCE, "government_statistics", BY)
        n += 1
    print(f"Queued {n} findings.")


if __name__ == "__main__":
    main()

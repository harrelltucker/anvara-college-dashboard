"""Create the research tables with the 15-school universe. Safe to re-run: never overwrites.

Usage:  python tools/init_research_data.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.data import RESEARCH_DIR, save_table  # noqa: E402
from engine.schema import TABLES  # noqa: E402

SCHOOLS = [  # school_id, name, state, FY2025 conference
    ("RUTGERS", "Rutgers University", "NJ", "B1G"),
    ("IOWA", "University of Iowa", "IA", "B1G"),
    ("CLEMSON", "Clemson University", "SC", "ACC"),
    ("UTAH", "University of Utah", "UT", "BIG12"),
    ("MARYLAND", "University of Maryland", "MD", "B1G"),
    ("UCLA", "UCLA", "CA", "B1G"),
    ("MINNESOTA", "University of Minnesota", "MN", "B1G"),
    ("PURDUE", "Purdue University", "IN", "B1G"),
    ("ILLINOIS", "University of Illinois Urbana-Champaign", "IL", "B1G"),
    ("MICHSTATE", "Michigan State University", "MI", "B1G"),
    ("WISCONSIN", "University of Wisconsin-Madison", "WI", "B1G"),
    ("ARIZONA", "University of Arizona", "AZ", "BIG12"),
    ("ARIZSTATE", "Arizona State University", "AZ", "BIG12"),
    ("TEXAS", "University of Texas at Austin", "TX", "SEC"),
    ("OHIOSTATE", "Ohio State University", "OH", "B1G"),
]
CONFERENCES = [("B1G", "Big Ten Conference"), ("BIG12", "Big 12 Conference"),
               ("SEC", "Southeastern Conference"), ("ACC", "Atlantic Coast Conference")]
AREAS = TABLES["research_status"]["enums"]["area"]

rows = {
    "schools": [{"school_id": s, "name": n, "state": st, "subdivision": "FBS", "control": "public",
                 "in_universe": "yes"} for s, n, st, _ in SCHOOLS],
    "conferences": [{"conference_id": c, "name": n, "fiscal_year": "2025"} for c, n in CONFERENCES],
    "memberships": [{"school_id": s, "conference_id": c, "fiscal_year": "2025"} for s, _, _, c in SCHOOLS],
    "research_status": [{"school_id": s, "area": a, "status": "not_started"} for s, *_ in SCHOOLS for a in AREAS],
}

for table, spec in TABLES.items():
    path = RESEARCH_DIR / f"{table}.csv"
    if path.exists():
        print(f"skip   {path.name} (already exists)")
        continue
    save_table(pd.DataFrame(rows.get(table, []), columns=spec["columns"]), path, spec["columns"])
    print(f"create {path.name} ({len(rows.get(table, []))} rows)")

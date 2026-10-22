"""Queue FY financials from a Knight-Newhouse College Athletics Database download.

Knight-Newhouse data: free for non-commercial use, must be credited, copyright protected,
no commercial use without permission (knightnewhousedata.org/privacy-policy-and-terms-of-use).
So: the source is credited, marked export_allowed = no, and the raw file stays out of Git.

Schools that already have figures from their own published NCAA report are skipped
(the original report is the source of record). Conference peers are added as
benchmark-only schools (in_universe = no) so conference comparisons have coverage.

Usage:
  python tools/import_knight_newhouse.py data/incoming/file.xlsx            (preview)
  python tools/import_knight_newhouse.py data/incoming/file.xlsx --submit   (queue findings)
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.data import RESEARCH_DIR, append_record, load_findings, load_tables, save_table  # noqa: E402
from engine.research import submit_finding  # noqa: E402
from engine.schema import TABLES  # noqa: E402

SOURCE = {"source_id": "KN-FY2025", "title": "Knight-Newhouse College Athletics Database, custom report (FY2025)",
          "publisher": "Knight Commission on Intercollegiate Athletics / S.I. Newhouse School, Syracuse University",
          "url": "https://knightnewhousedata.org/", "source_type": "other", "reporting_year": "2025",
          "retrieved_date": date.today().isoformat(), "export_allowed": "no",
          "license_note": "Non-commercial use with credit; copyright protected; no redistribution or commercial "
                          "use without permission. Data compiled from institutions' NCAA MFRS reports."}
CONFERENCES = {"Big Ten Conference": "B1G", "Big 12 Conference": "BIG12",
               "Southeastern Conference": "SEC", "Atlantic Coast Conference": "ACC"}
UNIVERSE = {  # Knight-Newhouse name -> our school_id
    "Rutgers, The State University of New Jersey-New Brunswick": "RUTGERS", "University of Iowa": "IOWA",
    "Clemson University": "CLEMSON", "University of Utah": "UTAH",
    "University of Maryland, College Park": "MARYLAND", "University of California, Los Angeles": "UCLA",
    "University of Minnesota, Twin Cities": "MINNESOTA", "Purdue University": "PURDUE",
    "University of Illinois Urbana-Champaign": "ILLINOIS", "Michigan State University": "MICHSTATE",
    "University of Wisconsin-Madison": "WISCONSIN", "University of Arizona": "ARIZONA",
    "Arizona State University": "ARIZSTATE", "University of Texas at Austin": "TEXAS",
    "The Ohio State University": "OHIOSTATE",
}
# Knight-Newhouse metric (lowercased, matched by keywords) -> our field
METRICS = [
    (("total revenues",), "total_operating_revenue"),
    (("total expenses",), "total_operating_expenses"),
    (("corporate sponsorship",), "commercial_revenue"),
    (("student fees",), "student_fees"),
    (("direct state", "government support"), "direct_government_support"),
    (("direct institutional support",), "direct_institutional_support"),
    (("transfers to the institution",), "transfers_to_institution"),
    (("indirect institutional support",), "indirect_institutional_support"),
]


def _match(column):
    c = column.lower()
    if "institutional/government" in c:
        return "combined_support"      # can't be split into our lines; noted only
    for keys, field in METRICS:
        if all(k in c for k in keys):
            return field
    return None


def _peer_id(name):
    return "PEER-" + re.sub(r"[^A-Z0-9]", "", name.upper().replace("UNIVERSITY", "U"))[:16]


def build(path):
    df = pd.read_excel(path, sheet_name="Data").rename(columns={"Data": "school"})
    fields = {col: _match(col) for col in df.columns}
    df = df[(df["Year"] == 2025) & df["FBS Conference"].isin(CONFERENCES)]
    rows = []
    for _, r in df.iterrows():
        rec = {}
        for col, field in fields.items():
            if field and pd.notna(r[col]):
                rec.setdefault(field, 0)
                rec[field] += int(r[col])
        rows.append({"name": r["school"], "conference": CONFERENCES[r["FBS Conference"]],
                     "school_id": UNIVERSE.get(r["school"], _peer_id(r["school"])),
                     "in_universe": r["school"] in UNIVERSE, **rec})
    return pd.DataFrame(rows), fields


def to_record(row, fields_present):
    have_lines = {"student_fees", "direct_government_support", "direct_institutional_support",
                  "indirect_institutional_support"} <= set(fields_present)
    rec = {"school_id": row["school_id"], "fiscal_year": "2025",
           "total_operating_revenue": str(row["total_operating_revenue"]),
           "total_operating_expenses": str(row["total_operating_expenses"]),
           "commercial_revenue": str(row["commercial_revenue"]),
           "commercial_revenue_label": "Knight-Newhouse: Corporate Sponsorship, Advertising, Licensing (NCAA MFRS line 15)"}
    note = "Knight-Newhouse College Athletics Database (credited; not for export). "
    if have_lines:
        direct = row.get("direct_institutional_support", 0) + row.get("transfers_to_institution", 0)
        rec.update({"student_fees": str(row["student_fees"]),
                    "direct_government_support": str(row["direct_government_support"]),
                    "direct_institutional_support": str(direct),
                    "indirect_institutional_support": str(row["indirect_institutional_support"])})
        note += "Direct institutional support is net of transfers to institution where provided."
    else:
        note += (f"Allocated revenue lines not in this download (combined institutional/government "
                 f"support, before transfers: {row.get('combined_support', 'n/a'):,}); generated revenue "
                 "not computed.")
    rec["notes"] = note
    return rec


def main():
    path = sys.argv[1]
    peers, fields = build(path)
    present = {f for f in fields.values() if f}
    print("Columns mapped:", {c: f for c, f in fields.items() if f})
    print(f"\n{len(peers)} schools in Big Ten/Big 12/SEC/ACC ({peers['in_universe'].sum()} in our universe):")
    print(peers.groupby("conference").size().to_string())

    tables = load_tables()
    queued = load_findings()
    has_primary = set()
    for _, f in queued.iterrows():
        if f["target_table"] == "financials":
            rec = json.loads(f["record_json"])
            if rec.get("fiscal_year") == "2025" and "knight" not in f["source_title"].lower():
                has_primary.add(rec["school_id"])
    has_primary |= set(tables["financials"].query("fiscal_year == '2025'")["school_id"])
    print("\nSkipped (original NCAA report already used):", sorted(has_primary & set(peers["school_id"])))

    if "--submit" not in sys.argv:
        print("\nPreview only. Re-run with --submit to queue findings.")
        return

    if "KN-FY2025" not in set(tables["sources"]["source_id"]):
        append_record("sources", SOURCE)
    new_schools = peers[~peers["school_id"].isin(tables["schools"]["school_id"])]
    for _, p in new_schools.iterrows():
        append_record("schools", {"school_id": p["school_id"], "name": p["name"], "state": "",
                                  "subdivision": "FBS", "control": "public", "in_universe": "no"})
        append_record("memberships", {"school_id": p["school_id"], "conference_id": p["conference"],
                                      "fiscal_year": "2025", "source_id": "KN-FY2025"})
    m = load_tables()["memberships"]
    m.loc[(m["fiscal_year"] == "2025") & (m["source_id"] == ""), "source_id"] = "KN-FY2025"
    save_table(m, RESEARCH_DIR / "memberships.csv", TABLES["memberships"]["columns"])

    n = 0
    for _, p in peers[~peers["school_id"].isin(has_primary)].iterrows():
        submit_finding("financials", to_record(p, present), SOURCE["title"], SOURCE["url"], "other",
                       "AI research assistant (Claude) via tools/import_knight_newhouse.py")
        n += 1
    print(f"\nAdded {len(new_schools)} benchmark-only peer schools; queued {n} financial findings.")


if __name__ == "__main__":
    main()

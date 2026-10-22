"""Queue FY financials from a Knight-Newhouse College Athletics Database download.

Knight-Newhouse data: free for non-commercial use, must be credited, copyright protected,
no commercial use without permission (knightnewhousedata.org/privacy-policy-and-terms-of-use).
So: the source is credited, marked export_allowed = no, and the raw file stays out of Git.

Schools that already have figures from their own published NCAA report are skipped
(the original report is the source of record). Conference peers are added as
benchmark-only schools (in_universe = no) so conference comparisons have coverage.

Uses two custom-report downloads joined on IPEDS ID:
  file 1: Total Revenues, Total Expenses, Corporate Sponsorship..., Institutional/Government Support
  file 2: revenue components incl. Conference/NCAA Distributions..., Donor Contributions, and
          Total Institutional/Government Support and Student Fees
Knight-Newhouse's subsidy total is BEFORE transfers back to the institution, while Total Revenues
is AFTER. The components of file 2 sum to Total Revenues except for those transfers, so
  allocated (net) = support and fees + (Total Revenues - sum of components), when that gap is negative.
Verified to the dollar against the original reports of Ohio State, Illinois and Wisconsin.

Usage:
  python tools/import_knight_newhouse.py FILE1.xlsx FILE2.xlsx            (preview)
  python tools/import_knight_newhouse.py FILE1.xlsx FILE2.xlsx --submit   (queue findings)
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
COMPONENTS = ["Other Revenue", "Corporate Sponsorship, Advertising, Licensing", "Donor Contributions",
              "Competition Guarantees - Revenues",
              "Conference/NCAA Distributions, Media Rights, and Post-Season Football", "Ticket Sales",
              "Total Institutional/Government Support and Student Fees"]


def _peer_id(name):
    return "PEER-" + re.sub(r"[^A-Z0-9]", "", name.upper().replace("UNIVERSITY", "U"))[:16]


def build(path1, path2):
    a = pd.read_excel(path1, sheet_name="Data").rename(columns={"Data": "school"})
    b = pd.read_excel(path2, sheet_name="Data")
    df = a.merge(b[["IPEDS ID", "Year", *[c for c in COMPONENTS if c not in a.columns]]],
                 on=["IPEDS ID", "Year"], how="left")
    df = df[(df["Year"] == 2025) & df["FBS Conference"].isin(CONFERENCES)].copy()
    df["gap"] = df["Total Revenues"] - df[COMPONENTS].sum(axis=1)
    support = df["Total Institutional/Government Support and Student Fees"]
    df["allocated_net"] = (support + df["gap"].clip(upper=0)).clip(lower=0)
    df["school_id"] = [UNIVERSE.get(s, _peer_id(s)) for s in df["school"]]
    df["in_universe"] = df["school"].isin(UNIVERSE)
    df["conference"] = df["FBS Conference"].map(CONFERENCES)
    return df


def to_record(r):
    as_int = lambda v: str(int(round(v)))
    note = ("Knight-Newhouse College Athletics Database (credited; not for export). Allocated revenue = "
            f"institutional/government support and student fees ({support_str(r)}) net of transfers to the "
            f"institution ({min(r['gap'], 0):,.0f}).")
    if r["gap"] > 0:
        note += (f" Components fall short of total revenue by {r['gap']:,.0f} (unexplained; not treated "
                 "as a transfer).")
    return {"school_id": r["school_id"], "fiscal_year": "2025",
            "total_operating_revenue": as_int(r["Total Revenues"]),
            "total_operating_expenses": as_int(r["Total Expenses"]),
            "allocated_revenue_total": as_int(r["allocated_net"]),
            "commercial_revenue": as_int(r["Corporate Sponsorship, Advertising, Licensing"]),
            "commercial_revenue_label": "Knight-Newhouse: Corporate Sponsorship, Advertising, Licensing (NCAA MFRS line 15)",
            "conference_ncaa_media_revenue": as_int(r["Conference/NCAA Distributions, Media Rights, and Post-Season Football"]),
            "donor_contributions": as_int(r["Donor Contributions"]),
            "notes": note}


def support_str(r):
    return f"{r['Total Institutional/Government Support and Student Fees']:,.0f}"


def main():
    peers = build(sys.argv[1], sys.argv[2])
    print(f"{len(peers)} schools in Big Ten/Big 12/SEC/ACC ({peers['in_universe'].sum()} in our universe):")
    print(peers.groupby("conference").size().to_string())
    odd = peers[peers["gap"] > 0]
    if len(odd):
        print("\nComponents short of total revenue (noted, not treated as transfers):")
        print(odd[["school", "gap"]].to_string(index=False))

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
        append_record("schools", {"school_id": p["school_id"], "name": p["school"], "state": "",
                                  "subdivision": "FBS", "control": "public", "in_universe": "no"})
        append_record("memberships", {"school_id": p["school_id"], "conference_id": p["conference"],
                                      "fiscal_year": "2025", "source_id": "KN-FY2025"})
    m = load_tables()["memberships"]
    m.loc[(m["fiscal_year"] == "2025") & (m["source_id"] == ""), "source_id"] = "KN-FY2025"
    save_table(m, RESEARCH_DIR / "memberships.csv", TABLES["memberships"]["columns"])

    n = 0
    for _, p in peers[~peers["school_id"].isin(has_primary)].iterrows():
        submit_finding("financials", to_record(p), SOURCE["title"], SOURCE["url"], "other",
                       "AI research assistant (Claude) via tools/import_knight_newhouse.py")
        n += 1
    print(f"\nAdded {len(new_schools)} benchmark-only peer schools; queued {n} financial findings.")


if __name__ == "__main__":
    main()

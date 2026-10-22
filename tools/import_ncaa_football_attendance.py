"""Queue 2024-season football home attendance from the NCAA's attendance records PDF.

The NCAA republishes one file (Attend.pdf) each year, so the live copy now shows 2025 only.
The 2024 edition is archived by the Wayback Machine (snapshot 2025-10-30); download it to
data/incoming/ncaa_football_attendance_2024_edition.pdf. Its 'All FBS Schools' table lists
home games, total and average for every FBS school.

Schools that already have a verified or queued 2024-25 football figure are skipped.

Usage:
  python tools/import_ncaa_football_attendance.py            (preview)
  python tools/import_ncaa_football_attendance.py --submit   (queue findings)
"""

import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.data import ROOT, load_findings, load_tables  # noqa: E402
from engine.research import submit_finding  # noqa: E402

PDF = ROOT / "data" / "incoming" / "ncaa_football_attendance_2024_edition.pdf"
URL = ("https://web.archive.org/web/20251030192151/"
       "https://s3.amazonaws.com/fs.ncaa.org/Docs/stats/football_records/Attend.pdf")
TITLE = "NCAA Football Attendance Records, 2024 season edition (Wayback Machine copy, 2025-10-30)"
POSTSEASON = {"OHIOSTATE": " Count includes College Football Playoff home game(s).",
              "TEXAS": " Count includes a College Football Playoff home game."}
METRIC, SEASON = "football_avg_home_attendance", "2024-25"


def parse(pdf=PDF):
    """NCAA name -> (home games, total, average) from the 2024 'All FBS Schools' table."""
    text = "\n".join(p.extract_text() for p in PdfReader(pdf).pages)
    section = text[text.index("2024 ATTENDANCE"):]
    section = section[section.index("All FBS Schools"):]
    section = section[:section.index("FCS")]
    rows = re.findall(r"^#?([A-Z][A-Za-z.&()' -]+?) (\d{1,2}) ([\d,]+) ([\d,]+)\s*$", section, re.M)
    out = {}
    for name, games, total, avg in rows:
        g, t, a = int(games), int(total.replace(",", "")), int(avg.replace(",", ""))
        if abs(t / g - a) < 1:                 # sanity check: average = total / games
            out[name] = (g, t, a)
    return out


def main():
    table = parse()
    tables = load_tables()
    schools = tables["schools"].query("in_universe == 'yes'")
    have = set(tables["audience"].query("metric == @METRIC and season == @SEASON")["school_id"])
    for _, f in load_findings().query("status == 'pending' and target_table == 'audience'").iterrows():
        rec = json.loads(f["record_json"])
        if rec.get("metric") == METRIC and rec.get("season") == SEASON:
            have.add(rec["school_id"])
    todo = schools[~schools["school_id"].isin(have)]
    missing = [n for n in todo["ncaa_name"] if n not in table]
    print(f"{len(table)} FBS rows parsed; {len(todo)} schools need a figure; not found in PDF: {missing or 'none'}")
    if "--submit" not in sys.argv:
        print("Preview only. Re-run with --submit to queue findings.")
        return
    n = 0
    for _, s in todo.iterrows():
        if s["ncaa_name"] not in table:
            continue
        g, t, a = table[s["ncaa_name"]]
        submit_finding("audience", {
            "school_id": s["school_id"], "season": SEASON, "metric": METRIC, "value": str(a),
            "notes": f"2024 football season (FY2025). NCAA 'All FBS Schools' table, row '{s['ncaa_name']}': "
                     f"{g} home games, {t:,} total.{POSTSEASON.get(s['school_id'], '')}"},
            TITLE, URL, "ncaa_statistics", "tools/import_ncaa_football_attendance.py")
        n += 1
    print(f"Queued {n} football attendance findings.")


if __name__ == "__main__":
    main()

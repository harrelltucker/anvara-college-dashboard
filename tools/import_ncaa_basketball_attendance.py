"""Queue 2024-25 men's and women's basketball home attendance from the NCAA's attendance records PDFs.

The NCAA republishes one file per sport (Attend.pdf) each year, so the live copies now show 2025-26.
The 2024-25 editions are archived by the Wayback Machine (snapshots 2026-04-16 and 2026-04-15); download
them to data/incoming/basketball/mbb_2025.pdf and wbb_2025.pdf. Each lists every Division I team's home
games, total and average attendance.

Only schools without a 2024-25 figure (verified or pending) are queued, so figures already taken from a
school's own statistics are kept.

Usage:
  python tools/import_ncaa_basketball_attendance.py            (preview)
  python tools/import_ncaa_basketball_attendance.py --submit   (queue findings)
"""

import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.data import ROOT, load_findings, load_tables  # noqa: E402
from engine.research import submit_finding  # noqa: E402

IN = ROOT / "data" / "incoming" / "basketball"
SEASON = "2024-25"
SPORTS = {
    "mbb": {"pdf": IN / "mbb_2025.pdf", "pages": (3, 7), "metric": "mbb_avg_home_attendance", "label": "men's basketball",
            "url": "https://web.archive.org/web/20260416051950/"
                   "https://s3.amazonaws.com/fs.ncaa.org/Docs/stats/m_basketball_RB/Attend.pdf",
            "title": "NCAA Men's Basketball Attendance Records through 2024-25 (Wayback Machine copy, 2026-04-16)"},
    "wbb": {"pdf": IN / "wbb_2025.pdf", "pages": (3, 8), "metric": "wbb_avg_home_attendance", "label": "women's basketball",
            "url": "https://web.archive.org/web/20260415175520/"
                   "https://s3.amazonaws.com/fs.ncaa.org/Docs/stats/w_basketball_RB/Attend.pdf",
            "title": "NCAA Women's Basketball Attendance Records through 2024-25 (Wayback Machine copy, 2026-04-15)"},
}
# NCAA basketball tables name a few schools differently from the football table (schools.ncaa_name)
ALIASES = {}


def parse(pdf, pages):
    """NCAA name -> (home games, total, average) from the Division I team tables (page index range)."""
    text = "\n".join(p.extract_text() for p in PdfReader(pdf).pages[slice(*pages)])
    rows = re.findall(r"^(?:\d+\.\s+)?([A-Z][A-Za-z.&()'\- ]+?)\s+(\d{1,2})\s+([\d,]+)\s+([\d,]+)\s*$", text, re.M)
    out = {}
    for name, games, total, avg in rows:
        g, t, a = int(games), int(total.replace(",", "")), int(avg.replace(",", ""))
        if g and abs(t / g - a) < 1:             # sanity check: average = total / games
            out.setdefault(name.strip(), (g, t, a))
    return out


def main():
    tables = load_tables()
    schools = tables["schools"].query("in_universe == 'yes'")
    pending = [json.loads(r) for r in load_findings().query(
        "status == 'pending' and target_table == 'audience'")["record_json"]]
    queued = 0
    for key, sport in SPORTS.items():
        table = parse(sport["pdf"], sport["pages"])
        have = set(tables["audience"].query("metric == @sport['metric'] and season == @SEASON")["school_id"])
        have |= {r["school_id"] for r in pending if r.get("metric") == sport["metric"] and r.get("season") == SEASON}
        todo = schools[~schools["school_id"].isin(have)]
        name = lambda s: ALIASES.get(s["school_id"], s["ncaa_name"])
        missing = [name(s) for _, s in todo.iterrows() if name(s) not in table]
        print(f"{key}: {len(table)} Division I rows parsed; {len(todo)} schools need a figure; "
              f"not found: {missing or 'none'}")
        if "--submit" not in sys.argv:
            continue
        for _, s in todo.iterrows():
            if name(s) not in table:
                continue
            g, t, a = table[name(s)]
            submit_finding("audience", {
                "school_id": s["school_id"], "season": SEASON, "metric": sport["metric"], "value": str(a),
                "notes": f"2024-25 {sport['label']} (FY2025). NCAA Division I attendance table, row "
                         f"'{name(s)}': {g} home games, {t:,} total."},
                sport["title"], sport["url"], "ncaa_statistics", "tools/import_ncaa_basketball_attendance.py")
            queued += 1
    print(f"Queued {queued} basketball attendance findings." if "--submit" in sys.argv
          else "Preview only. Re-run with --submit to queue findings.")


if __name__ == "__main__":
    main()

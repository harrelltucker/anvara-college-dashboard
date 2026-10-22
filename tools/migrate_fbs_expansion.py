"""One-time migration (2026-10-22): expand the universe from 15 schools to all public FBS schools.

- renames the benchmark-only 'PEER-...' IDs to the registry IDs (everywhere, incl. pending findings)
- adds short_name / ncaa_name / featured to schools; every public FBS school is now ranked
- adds the remaining FBS conferences and the new schools with their FY2025 memberships
Financial figures for the new schools are NOT added here: run tools/import_knight_newhouse.py
to queue them for verification.

Usage:  python tools/migrate_fbs_expansion.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.data import PENDING_FILE, RESEARCH_DIR, load_findings, load_tables, save_table  # noqa: E402
from engine.schema import FINDINGS_COLUMNS, TABLES  # noqa: E402
from tools.fbs_registry import CONFERENCES, FEATURED, SCHOOLS  # noqa: E402

FY = "2025"
SOURCE = "KN-FY2025"


def main():
    t = load_tables()
    schools = t["schools"]
    by_name = {kn: v for kn, v in SCHOOLS.items()}
    rename = {row.school_id: by_name[row.name][0] for row in schools.itertuples()
              if row.school_id.startswith("PEER-") and row.name in by_name}
    unmatched = [s for s in schools["school_id"] if s.startswith("PEER-") and s not in rename]
    if unmatched:
        sys.exit(f"Unmatched peer IDs: {unmatched}")

    for table in ("schools", "memberships", "financials", "audience", "catalysts", "rights_relationships",
                  "contacts", "research_status"):
        if "school_id" in t[table]:
            t[table]["school_id"] = t[table]["school_id"].replace(rename)

    # school attributes
    s = t["schools"]
    info = {v[0]: (kn, v[1], v[2], v[3]) for kn, v in SCHOOLS.items()}
    existing = set(s["school_id"])
    new_rows = [{"school_id": sid, "name": kn, "subdivision": "FBS", "control": "public"}
                for sid, (kn, *_rest) in info.items() if sid not in existing]
    s = pd.concat([s, pd.DataFrame(new_rows)], ignore_index=True).fillna("")
    s["short_name"] = s["school_id"].map(lambda x: info[x][1] if x in info else "")
    s["ncaa_name"] = s["school_id"].map(lambda x: info[x][2] if x in info else "")
    s["state"] = [st or (info[x][3] if x in info else "") for x, st in zip(s["school_id"], s["state"])]
    s["in_universe"] = s["school_id"].map(lambda x: "yes" if x in info else "no")
    s["featured"] = s["school_id"].map(lambda x: "yes" if x in FEATURED else "no")
    t["schools"] = s

    # conferences (FY2025)
    c = t["conferences"]
    rows = {cid: {"conference_id": cid, "name": name, "fiscal_year": FY, "member_count": str(n),
                  "public_member_count": str(pub), "source_id": SOURCE,
                  "notes": f"{n} football members in 2024-25. {note} Public members per Knight-Newhouse FY2025 list."}
            for cid, name, n, pub, note in CONFERENCES.values()}
    c = c[~c["conference_id"].isin(rows)]
    t["conferences"] = pd.concat([c, pd.DataFrame(rows.values())], ignore_index=True).fillna("")

    # memberships for new schools come from the Knight-Newhouse conference column
    kn = pd.read_excel(RESEARCH_DIR.parent / "incoming" / "knight_newhouse_custom_report.xlsx", sheet_name="Data")
    kn = kn[(kn["Year"] == 2025) & (kn["NCAA Subdivision"] == "Football Bowl Subdivision")]
    conf_id = {k: v[0] for k, v in CONFERENCES.items()}
    m = t["memberships"]
    have = set(m[m["fiscal_year"] == FY]["school_id"])
    add = [{"school_id": SCHOOLS[name][0], "conference_id": conf_id[conf], "fiscal_year": FY, "source_id": SOURCE}
           for name, conf in zip(kn["Data"], kn["FBS Conference"]) if SCHOOLS[name][0] not in have]
    t["memberships"] = pd.concat([m, pd.DataFrame(add)], ignore_index=True)

    # research status rows for every ranked school
    rs = t["research_status"]
    known = set(zip(rs["school_id"], rs["area"]))
    extra = [{"school_id": sid, "area": area, "status": "not_started"}
             for sid in info for area in TABLES["research_status"]["enums"]["area"] if (sid, area) not in known]
    t["research_status"] = pd.concat([rs, pd.DataFrame(extra)], ignore_index=True).fillna("")

    for table in ("schools", "conferences", "memberships", "financials", "research_status"):
        save_table(t[table], RESEARCH_DIR / f"{table}.csv", TABLES[table]["columns"])

    f = load_findings()
    for old, new in rename.items():
        f["record_json"] = f["record_json"].str.replace(json.dumps(old), json.dumps(new), regex=False)
    save_table(f, PENDING_FILE, FINDINGS_COLUMNS)
    print(f"Renamed {len(rename)} IDs; added {len(new_rows)} schools, {len(add)} memberships; "
          f"{len(t['schools'][t['schools']['in_universe'] == 'yes'])} schools now ranked.")


if __name__ == "__main__":
    main()

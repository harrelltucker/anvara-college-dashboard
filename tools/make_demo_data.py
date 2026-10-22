"""Generate the DEMONSTRATION dataset: fictional schools, fictional numbers.

It exists only to exercise the dashboard before research data is complete. Every name is
fictional on purpose, so a screenshot can never be mistaken for real research.

Usage:  python tools/make_demo_data.py
"""

import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.data import DEMO_DIR, save_table  # noqa: E402
from engine.schema import TABLES  # noqa: E402

random.seed(2025)
DEMO_SOURCE = {"source_id": "DEMO", "title": "DEMONSTRATION DATA - fictional, not research",
               "publisher": "Generated", "url": "https://example.com/demonstration-data",
               "source_type": "demonstration", "reporting_year": "2025", "retrieved_date": "2026-10-22",
               "export_allowed": "no", "license_note": "Fictional demonstration data"}
CONFS = {"DEMO-N": "Demo Conference North", "DEMO-S": "Demo Conference South", "DEMO-W": "Demo Conference West"}
NAMES = ["Alder", "Birch", "Cedar", "Dogwood", "Elm", "Fir", "Ginkgo", "Hazel", "Ironwood",
         "Juniper", "Kapok", "Larch", "Maple", "Nutmeg", "Oak"]
V = {"verified_by": "DEMO", "verified_date": "2026-10-22"}

schools, members, fin, aud, cats, rel, status = [], [], [], [], [], [], []
for i, name in enumerate(NAMES):
    sid, conf = f"DEMO{i + 1:02d}", list(CONFS)[i % 3]
    in_universe = "no" if i >= 12 else "yes"          # last three are benchmark-only peers
    schools.append({"school_id": sid, "name": f"{name} State University (DEMO)", "state": "XX",
                    "subdivision": "FBS", "control": "public", "in_universe": in_universe})
    members.append({"school_id": sid, "conference_id": conf, "fiscal_year": "2025", "source_id": "DEMO"})
    scale = random.uniform(0.6, 2.6) * (1.8 if i == 0 else 1)   # one outlier, like a Texas
    rev = scale * 120e6
    alloc = [rev * random.uniform(0, 0.08), rev * random.uniform(0, 0.03),
             rev * random.uniform(0, 0.06), rev * random.uniform(0, 0.01)]
    fin.append({"school_id": sid, "fiscal_year": "2025",
                "total_operating_revenue": round(rev), "total_operating_expenses": round(rev * random.uniform(0.94, 1.03)),
                "direct_institutional_support": round(alloc[0]), "indirect_institutional_support": round(alloc[1]),
                "student_fees": round(alloc[2]), "direct_government_support": round(alloc[3]),
                "commercial_revenue": round(rev * random.uniform(0.04, 0.14)),
                "commercial_revenue_label": "Corporate Sponsorship, Advertising, and Licensing",
                "source_id": "DEMO", **V, "notes": "DEMO"})
    if in_universe == "yes":
        for metric, base in (("football_avg_home_attendance", 60000), ("mbb_avg_home_attendance", 11000),
                             ("wbb_avg_home_attendance", 4500)):
            if not (metric.startswith("wbb") and i == 5):          # leave one gap to show missing data
                aud.append({"school_id": sid, "season": "2024-25", "metric": metric,
                            "value": round(base * random.uniform(0.5, 1.6) * min(scale, 1.6)),
                            "source_id": "DEMO", **V, "notes": "DEMO"})
        for area in TABLES["research_status"]["enums"]["area"]:
            status.append({"school_id": sid, "area": area,
                           "status": "not_started" if (area == "catalysts" and i == 7) else "complete"})
        rel.append({"relationship_id": f"DEMO-R{i + 1:02d}", "school_id": sid,
                    "organization_id": random.choice(["DEMO-RH1", "DEMO-RH2", "DEMO-INHOUSE"]),
                    "management_model": "outsourced", "rights_scope": "Multimedia rights (DEMO)",
                    "agreement_details": "DEMO", "expiration_verified": "no", "source_id": "DEMO", **V})

events = [("DEMO01", "private_capital", "high", "direct", "2026-06-01", "Private capital partner for commercial entity (DEMO)"),
          ("DEMO03", "in_house_rights_org", "high", "direct", "2025-11-15", "Launches in-house commercial rights unit (DEMO)"),
          ("DEMO03", "in_house_rights_org", "high", "direct", "2025-11-20", "Same event, second announcement (DEMO)"),
          ("DEMO04", "commercial_leadership", "medium", "direct", "2026-02-01", "Hires chief revenue officer (DEMO)"),
          ("DEMO06", "major_partnership", "medium", "indirect", "2024-08-01", "New stadium naming partner (DEMO)"),
          ("DEMO09", "sponsorship_initiative", "low", "direct", "2026-09-10", "Announces new sponsorship categories (DEMO)")]
for n, (sid, cat, sig, relv, when, title) in enumerate(events):
    event_id = "DEMO-E03" if sid == "DEMO03" else f"DEMO-E{n + 1:02d}"
    cats.append({"catalyst_id": f"DEMO-C{n + 1:02d}", "school_id": sid, "event_id": event_id, "event_date": when,
                 "category": cat, "title": title, "description": "Fictional demonstration event",
                 "significance": sig, "commercial_relevance": relv, "confidence": "confirmed",
                 "source_id": "DEMO", **V})

data = {
    "sources": [DEMO_SOURCE],
    "conferences": [{"conference_id": c, "name": n, "fiscal_year": "2025", "member_count": "5",
                     "source_id": "DEMO"} for c, n in CONFS.items()],
    "schools": schools, "memberships": members, "financials": fin, "audience": aud,
    "catalysts": cats, "rights_relationships": rel, "research_status": status,
    "rights_holders": [
        {"organization_id": "DEMO-RH1", "name": "Demo Rights Co. (DEMO)", "org_type": "multimedia_rights_company", "source_id": "DEMO"},
        {"organization_id": "DEMO-RH2", "name": "Sample Media Partners (DEMO)", "org_type": "multimedia_rights_company", "source_id": "DEMO"},
        {"organization_id": "DEMO-INHOUSE", "name": "In-house commercial unit (DEMO)", "org_type": "in_house_entity", "source_id": "DEMO"}],
    "market_context": [{"context_id": "DEMO-M1", "date": "2025-07-01", "title": "Example rule change (DEMO)",
                        "description": "Fictional market context entry", "context_type": "ncaa_rule",
                        "status": "in_effect", "source_id": "DEMO"}],
}
for table, spec in TABLES.items():
    save_table(pd.DataFrame(data.get(table, []), columns=spec["columns"]), DEMO_DIR / f"{table}.csv", spec["columns"])
print(f"Demo data written to {DEMO_DIR}")

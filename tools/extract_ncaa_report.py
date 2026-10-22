"""Read an NCAA Membership Financial Reporting System (MFRS) report PDF and pull the
FY figures this dashboard uses, from the report's "Revenue/Expense Summary" pages.

The result is queued as a PENDING finding; it affects scores only after a person verifies it.

Usage:
  python tools/extract_ncaa_report.py report.pdf                       (preview only)
  python tools/extract_ncaa_report.py report.pdf --submit SCHOOL_ID "Source title" https://source-url

Mapping to NCAA categories (FY2025 form):
  direct_government_support      = 2  Direct State or Other Government Support
  student_fees                   = 3  Student Fees
  direct_institutional_support   = 4  Direct Institutional Support + 5 Less - Transfers to Institution
                                       (category 5 is reported as a negative)
  indirect_institutional_support = 6  Indirect Institutional Support
                                    + 6A Indirect Institutional Support - Athletic Facilities Debt Service,
                                       Lease and Rental Fees
  commercial_revenue             = 15 Royalties, Licensing, Advertisement and Sponsorships
  conference_ncaa_media_revenue  = 11 Media Rights + 12 Total NCAA Distributions + 13 Conference
                                   Distributions + 13A Conference Distributions of Post-Season Revenue
                                   + 19 Post-Season Football (matches Knight-Newhouse's grouping)
  donor_contributions            = 8 Contributions + 9 In-Kind (matches Knight-Newhouse's grouping)
"""

import re
import sys
from pathlib import Path

import pypdf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.research import submit_finding  # noqa: E402

AMOUNT = re.compile(r"(-?)\$\s?(\(?)([\d,]+)\)?")
ITEM_START = re.compile(r"^(\d{1,2})([A-Z]?) ([A-Z].+)")   # e.g. "13A Conference ..."; label starts uppercase


def _amount(match):
    neg = match.group(1) == "-" or match.group(2) == "("
    return -int(match.group(3).replace(",", "")) if neg else int(match.group(3).replace(",", ""))


def summary_items(text):
    """{category id: (label, amount)} plus the two totals, from the summary section."""
    start = text.find("Revenue/Expense Summary")
    end = text.find("Total of Categories 20-44.")
    if start < 0 or end < 0:
        raise ValueError("Couldn't find the Revenue/Expense Summary section")
    lines = [l.strip() for l in text[start:end + 40].splitlines()]
    items, current, label, last = {}, None, [], (0, "")
    for line in lines:
        if line.startswith(("Reporting Institution", "NCAA Membership Financial")):
            continue
        m = ITEM_START.match(line)
        # Category IDs only ever increase (12, 12A, 12B, 13 ...). This stops numbers inside
        # definition text (e.g. "...Categories 23 and 25 combined.") being read as categories.
        if m and current is None and (int(m.group(1)), m.group(2)) > last:
            last = (int(m.group(1)), m.group(2))
            current, label = m.group(1) + m.group(2), []
            line = m.group(3)
        if current is not None or line.startswith("Total Operating"):
            if current is None:
                current, label = "TOTAL_" + str(len([k for k in items if k.startswith("TOTAL")])), []
            amt = AMOUNT.search(line)
            if amt:
                label.append(line[:amt.start()])
                items[current] = (" ".join(" ".join(label).split()), _amount(amt))
                current, label = None, []
            else:
                label.append(line)
    return items


def extract(pdf_path):
    reader = pypdf.PdfReader(pdf_path)
    text = "\n".join(p.extract_text() for p in reader.pages[:20])
    header = re.search(r"Reporting Institution:\s*(.+?)\s*Reporting Year \(FY\):\s*(\d{4})", text)
    items = summary_items(text)
    get = lambda k: items.get(k, (None, 0))[1]
    return {
        "institution": header.group(1) if header else "?",
        "fiscal_year": header.group(2) if header else "?",
        "items": items,
        "record": {
            "fiscal_year": header.group(2) if header else "",
            "total_operating_revenue": str(items["TOTAL_0"][1]),
            "total_operating_expenses": str(items["TOTAL_1"][1]),
            "direct_government_support": str(get("2")),
            "student_fees": str(get("3")),
            "direct_institutional_support": str(get("4") + get("5")),
            "indirect_institutional_support": str(get("6") + get("6A")),
            "commercial_revenue": str(get("15")),
            "conference_ncaa_media_revenue": str(get("11") + get("12") + get("13") + get("13A") + get("19")),
            "donor_contributions": str(get("8") + get("9")),
            "commercial_revenue_label": f"NCAA category 15: {items.get('15', ('?',))[0]}",
            "notes": (f"From the MFRS Revenue/Expense Summary. Direct institutional support is net of "
                      f"category 5 transfers to institution ({get('4'):,} + {get('5'):,}); indirect "
                      f"institutional support includes 6A facilities debt/lease ({get('6'):,} + {get('6A'):,})."),
        },
    }


def main():
    result = extract(sys.argv[1])
    print(f"Institution: {result['institution']} | FY{result['fiscal_year']}")
    for k, (label, amt) in result["items"].items():
        if k in {"2", "3", "4", "5", "6", "6A", "8", "9", "11", "12", "13", "13A", "15", "19", "TOTAL_0", "TOTAL_1"}:
            print(f"  {k:>8}  {label[:70]:<70} {amt:>15,}")
    if "--submit" in sys.argv:
        i = sys.argv.index("--submit")
        school_id, title, url = sys.argv[i + 1:i + 4]
        record = {"school_id": school_id, **result["record"]}
        fid = submit_finding("financials", record, title, url, "ncaa_financial_report",
                             "AI research assistant (Claude) via tools/extract_ncaa_report.py")
        print(f"Queued {fid} for verification")


if __name__ == "__main__":
    main()

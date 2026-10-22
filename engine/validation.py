"""Data quality checks.

error   = wrong or incomplete; must be fixed
warning = unusual or unverified; a human should look
"""

from dataclasses import dataclass
from datetime import date, datetime

import pandas as pd

from engine.schema import ALLOCATED_FIELDS, MONEY_FIELDS, TABLES

ERROR, WARNING = "error", "warning"


@dataclass
class Issue:
    severity: str
    table: str
    record: str
    message: str


def _is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def _is_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def check_record(table, record, tables, today=None):
    """Check one record (a dict) against the schema. Used for tables and new findings."""
    today = today or date.today()
    spec = TABLES[table]
    rid = record.get(spec["key"]) if spec["key"] else ", ".join(
        str(record.get(c, "")) for c in spec["required"][:2])
    problems = []
    for col in spec["required"]:
        if not str(record.get(col, "")).strip():
            problems.append((ERROR, f"Missing required field '{col}'"))
    for col, allowed in spec.get("enums", {}).items():
        v = record.get(col, "")
        if v and v not in allowed:
            problems.append((ERROR, f"'{col}' is '{v}'; must be one of: {', '.join(allowed)}"))
    for col in spec.get("numbers", []):
        v = record.get(col, "")
        if v and not _is_number(v):
            problems.append((ERROR, f"'{col}' must be a number (no $ or commas), got '{v}'"))
    for col in spec.get("dates", []):
        v = record.get(col, "")
        if v and not _is_date(v):
            problems.append((ERROR, f"'{col}' must be YYYY-MM-DD, got '{v}'"))
        elif v and col != "expiration_date" and datetime.strptime(v, "%Y-%m-%d").date() > today:
            problems.append((ERROR, f"'{col}' is in the future ({v})"))
    for col in spec.get("urls", []):
        v = record.get(col, "")
        if v and not v.startswith(("http://", "https://")):
            problems.append((ERROR, f"'{col}' is not a web link: '{v}'"))
    for col, other in spec.get("refs", {}).items():
        v = record.get(col, "")
        key = TABLES[other]["key"]
        if v and v not in set(tables[other][key]):
            problems.append((ERROR, f"'{col}' = '{v}' not found in {other}"))
    return [Issue(sev, table, rid or "(new)", msg) for sev, msg in problems]


def run_checks(tables, rules):
    issues = []
    for table, spec in TABLES.items():
        df = tables[table]
        if spec["key"]:
            for dup in df[spec["key"]][df[spec["key"]].duplicated() & (df[spec["key"]] != "")].unique():
                issues.append(Issue(ERROR, table, dup, f"Duplicate {spec['key']}"))
        for _, row in df.iterrows():
            issues += check_record(table, row.to_dict(), tables)
    issues += _financial_checks(tables["financials"])
    issues += _coverage_checks(tables, rules)
    return issues


def _financial_checks(fin):
    issues = []
    dupes = fin[fin.duplicated(["school_id", "fiscal_year"], keep=False)]
    for (school, fy), group in dupes.groupby(["school_id", "fiscal_year"]):
        conflicting = [c for c in MONEY_FIELDS if group[c].nunique() > 1]
        msg = (f"Conflicting values for {', '.join(conflicting)} across sources" if conflicting
               else "Duplicate record for the same year")
        issues.append(Issue(ERROR, "financials", f"{school} FY{fy}", msg))
    for _, r in fin.iterrows():
        rid = f"{r['school_id']} FY{r['fiscal_year']}"
        num = {c: float(r[c]) for c in MONEY_FIELDS if r[c] and _is_number(r[c])}
        rev = num.get("total_operating_revenue")
        if rev is not None:
            alloc = sum(num.get(c, 0) for c in ALLOCATED_FIELDS)
            if alloc > rev:
                issues.append(Issue(ERROR, "financials", rid, "Allocated revenue exceeds total revenue"))
            if num.get("commercial_revenue", 0) > rev:
                issues.append(Issue(ERROR, "financials", rid, "Commercial revenue exceeds total revenue"))
        if any(c in num for c in ALLOCATED_FIELDS) and not all(r[c] for c in ALLOCATED_FIELDS):
            issues.append(Issue(WARNING, "financials", rid,
                                "Some allocated revenue lines are blank; enter 0 if the report shows none, "
                                "otherwise generated revenue can't be calculated"))
        if r["commercial_revenue"] and not r["commercial_revenue_label"]:
            issues.append(Issue(WARNING, "financials", rid,
                                "Record the exact NCAA category label for commercial revenue"))
    return issues


def _coverage_checks(tables, rules):
    issues = []
    fy = str(rules["scoring_fiscal_year"])
    for _, c in tables["conferences"][tables["conferences"]["fiscal_year"] == fy].iterrows():
        if not c["member_count"]:
            issues.append(Issue(WARNING, "conferences", c["conference_id"],
                                "Member count unknown, so peer coverage can't be measured"))
        if not c["source_id"]:
            issues.append(Issue(WARNING, "conferences", c["conference_id"], "No source for membership"))
    for _, m in tables["memberships"].iterrows():
        if not m["source_id"]:
            issues.append(Issue(WARNING, "memberships", m["school_id"],
                                f"No source for FY{m['fiscal_year']} conference membership"))
    return issues


def issues_frame(issues):
    return pd.DataFrame([vars(i) for i in issues], columns=["severity", "table", "record", "message"])

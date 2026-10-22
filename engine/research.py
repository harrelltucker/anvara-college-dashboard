"""AI-assisted research workflow, without needing a paid AI service.

1. checklist()      - what's missing for a school, and where to look for it
2. submit_finding() - a new sourced finding (from a person or an AI assistant) goes to a
                      pending queue; it does NOT affect scores yet
3. verify_finding() - a human confirms the source supports it; it is validated and only
                      then becomes part of the scored research data
4. opportunity_brief() - a short brief built only from verified data, with every fact
                      cited and interpretation labeled separately
"""

import json
from datetime import date

import pandas as pd

from engine.data import PENDING_FILE, RESEARCH_DIR, append_record, load_findings, save_table
from engine.schema import FINDINGS_COLUMNS, TABLES
from engine.validation import ERROR, check_record

WHERE_TO_LOOK = {
    "financials": "University NCAA financial report (athletics or institutional-research site), "
                  "state transparency portal, or a public records request. EADA as a cross-check "
                  "only (different accounting).",
    "audience": "NCAA attendance statistics; school's official season stats.",
    "catalysts": "Official university/athletics press releases, board of trustees/regents minutes.",
    "rights": "Rights-holder announcements (Learfield, Playfly, etc.), university releases, "
              "board-approved contracts.",
    "contacts": "Athletics staff directory and the rights holder's local team page.",
}


def checklist(school_id, scored_row, tables, missing_items):
    """Structured to-do list for one school."""
    status = tables["research_status"]
    s = status[status["school_id"] == school_id].set_index("area")["status"]
    rows = []
    for item in missing_items:
        area = ("financials" if "FY2025" in item or "benchmark" in item
                else "audience" if "attendance" in item
                else item.split()[0].lower())
        rows.append({"area": area, "missing": item, "where_to_look": WHERE_TO_LOOK.get(area, ""),
                     "status": s.get(area, "not_started").replace("_", " ")})
    return pd.DataFrame(rows, columns=["area", "missing", "where_to_look", "status"])


def submit_finding(target_table, record, source_title, source_url, source_type, submitted_by):
    """Queue a finding for human verification. Returns the new finding id."""
    findings = load_findings()
    finding_id = f"F-{len(findings) + 1:04d}"
    row = {"finding_id": finding_id, "target_table": target_table,
           "record_json": json.dumps(record, ensure_ascii=False), "source_title": source_title,
           "source_url": source_url, "source_type": source_type, "submitted_by": submitted_by,
           "submitted_date": date.today().isoformat(), "status": "pending", "review_note": ""}
    save_table(pd.concat([findings, pd.DataFrame([row])], ignore_index=True), PENDING_FILE, FINDINGS_COLUMNS)
    return finding_id


def preview_finding(finding, tables, verifier):
    """The record exactly as it would be saved, plus any validation problems."""
    record = json.loads(finding["record_json"])
    sources = tables["sources"]
    existing = sources[sources["url"] == finding["source_url"]]
    source_id = existing["source_id"].iloc[0] if len(existing) else f"S-{len(sources) + 1:04d}"
    record["source_id"] = source_id
    if "verified_by" in TABLES[finding["target_table"]]["columns"]:
        record["verified_by"] = verifier
        record["verified_date"] = date.today().isoformat()
    new_source = None if len(existing) else {
        "source_id": source_id, "title": finding["source_title"], "publisher": "",
        "url": finding["source_url"], "source_type": finding["source_type"], "reporting_year": "",
        "retrieved_date": date.today().isoformat(), "export_allowed": "yes", "license_note": ""}
    check_tables = dict(tables)
    if new_source:
        check_tables["sources"] = pd.concat([sources, pd.DataFrame([new_source])], ignore_index=True)
    problems = check_record(finding["target_table"], record, check_tables)
    return record, new_source, problems


def verify_finding(finding_id, tables, verifier):
    """Promote a pending finding into the research data, if it passes validation."""
    findings = load_findings()
    finding = findings[findings["finding_id"] == finding_id].iloc[0]
    record, new_source, problems = preview_finding(finding, tables, verifier)
    errors = [p for p in problems if p.severity == ERROR]
    if errors:
        return errors
    if new_source:
        append_record("sources", new_source, RESEARCH_DIR)
    append_record(finding["target_table"], record, RESEARCH_DIR)
    _set_status(findings, finding_id, "verified", f"Verified by {verifier} on {date.today()}")
    return []


def reject_finding(finding_id, note):
    _set_status(load_findings(), finding_id, "rejected", note)


def _set_status(findings, finding_id, status, note):
    findings.loc[findings["finding_id"] == finding_id, ["status", "review_note"]] = [status, note]
    save_table(findings, PENDING_FILE, FINDINGS_COLUMNS)


def _money(v):
    return "n/a" if pd.isna(v) else f"${v / 1e6:,.1f}M"


def _pct(v):
    return "n/a" if pd.isna(v) else f"{v:.0%}"


def opportunity_brief(school_id, scored, tables, missing_items):
    """Evidence-grounded markdown brief: verified facts (cited) vs. interpretation."""
    row = scored.loc[school_id]
    sources = tables["sources"].set_index("source_id")
    cite = lambda sid: (f" ([{sources.loc[sid, 'title']}]({sources.loc[sid, 'url']}))"
                        if sid and sid in sources.index else "")
    facts, reads = [], []

    if pd.notna(row["total_operating_revenue"]):
        facts.append(f"FY2025 athletics operating revenue {_money(row['total_operating_revenue'])} vs. "
                     f"expenses {_money(row['total_operating_expenses'])}; reported result "
                     f"{_money(row['reported_result'])}.{cite(row['financial_source_id'])}")
    if pd.notna(row["generated_revenue"]):
        facts.append(f"Athletics-generated revenue (NCAA definition: excludes institutional support and "
                     f"student fees) {_money(row['generated_revenue'])}, covering "
                     f"{_pct(row['self_sufficiency'])} of expenses.")
    if pd.notna(row["own_operations_revenue"]):
        facts.append(f"Own-operations revenue (also excluding {_money(row['conference_ncaa_media_revenue'])} "
                     f"of conference/NCAA distributions, media rights and bowl revenue) "
                     f"{_money(row['own_operations_revenue'])}.")
    if pd.notna(row["commercial_revenue"]):
        facts.append(f"Sponsorship, advertising & licensing revenue (NCAA category, not pure sponsorship) "
                     f"{_money(row['commercial_revenue'])}, {_pct(row['commercial_share'])} of total revenue.")
    for key, label in (("football", "Football"), ("mens_basketball", "Men's basketball"),
                       ("womens_basketball", "Women's basketball")):
        if pd.notna(row[key]):
            facts.append(f"{label} average home attendance (2024-25): {row[key]:,.0f}.")
    cats = tables["catalysts"][tables["catalysts"]["school_id"] == school_id].sort_values("event_date")
    for _, c in cats.drop_duplicates("event_id", keep="last").iterrows():
        facts.append(f"{c['event_date']}: {c['title']} ({c['confidence']}).{cite(c['source_id'])}")
    rel = tables["rights_relationships"]
    orgs = tables["rights_holders"].set_index("organization_id")["name"]
    for _, r in rel[rel["school_id"] == school_id].iterrows():
        facts.append(f"Commercial rights: {orgs.get(r['organization_id'], r['organization_id'])} "
                     f"({r['management_model'].replace('_', ' ')}).{cite(r['source_id'])}")

    for cat, label in (("financial_pressure", "financial pressure"),
                       ("commercial_opportunity", "commercial opportunity"),
                       ("growth_catalysts", "growth catalysts")):
        v = row[cat]
        if pd.notna(v):
            level = "high" if v >= 67 else "moderate" if v >= 34 else "low"
            reads.append(f"{level.capitalize()} {label} relative to the schools analyzed (score {v:.0f}/100).")
    if pd.notna(row["commercial_opportunity"]) and row["commercial_opportunity"] >= 67:
        reads.append("A large existing commercial business suggests sizable sponsorship dollars in play.")
    if pd.notna(row["financial_pressure"]) and row["financial_pressure"] >= 67:
        reads.append("Weaker self-funding suggests an incentive to grow athletics-generated revenue.")
    if pd.notna(row["growth_catalysts"]) and row["growth_catalysts"] >= 40:
        reads.append("Recent commercial developments suggest active motivation to expand revenue.")

    overall = "n/a" if pd.isna(row["overall"]) else f"{row['overall']:.0f}/100"
    bullets = lambda items: "\n".join(f"- {i}" for i in items)
    sections = [
        f"### {row['name']}: opportunity brief",
        f"**Overall score:** {overall} · confidence: {row['confidence']} · "
        f"data completeness: {row['completeness']:.0%}",
        "**Verified evidence**\n\n" + bullets(facts or ["No verified data yet."]),
        "**Interpretation** *(analysis, not verified fact)*\n\n"
        + bullets(reads or ["Not enough verified data to interpret yet."]),
    ]
    if missing_items:
        sections.append("**Gaps and limitations**\n\n" + bullets(missing_items))
    sections.append("*This brief does not claim the school has unsold sponsorship inventory.*")
    return "\n\n".join(sections)

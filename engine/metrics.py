"""FY financial and audience metrics per school, before any scoring.

Definitions (NCAA Membership Financial Reporting System categories):
  allocated revenue  = direct institutional support + indirect institutional support
                       + student fees + direct government support
  generated revenue  = total operating revenue - allocated revenue
  reported result    = total operating revenue - total operating expenses (as reported,
                       i.e. after subsidies and student fees)
  self-sufficiency   = generated revenue / total operating expenses
  commercial revenue = the NCAA category combining sponsorship, advertising, licensing and
                       related items. It is NOT pure sponsorship revenue.
"""

import numpy as np
import pandas as pd

from engine.schema import ALLOCATED_FIELDS, MONEY_FIELDS

AUDIENCE_METRICS = {
    "football": "football_avg_home_attendance",
    "mens_basketball": "mbb_avg_home_attendance",
    "womens_basketball": "wbb_avg_home_attendance",
}


def _num(series):
    return pd.to_numeric(series.replace("", np.nan), errors="coerce")


def school_metrics(tables, rules):
    """One row per school (all schools, including benchmark-only peers)."""
    fy = str(rules["scoring_fiscal_year"])
    schools = tables["schools"].set_index("school_id")

    m = pd.DataFrame(index=schools.index)
    m["name"] = schools["name"]
    m["in_universe"] = schools["in_universe"] == "yes"
    members = tables["memberships"]
    members = members[members["fiscal_year"] == fy].set_index("school_id")
    m["conference_id"] = members["conference_id"].reindex(m.index).fillna("")

    fin = tables["financials"]
    fin = fin[fin["fiscal_year"] == fy].drop_duplicates("school_id", keep="last").set_index("school_id")
    for col in MONEY_FIELDS:
        m[col] = _num(fin[col]).reindex(m.index) if col in fin else np.nan
    m["financial_source_id"] = fin["source_id"].reindex(m.index).fillna("") if len(fin) else ""

    # allocated revenue needs every line present (0 is fine); otherwise it's unknown
    alloc = m[ALLOCATED_FIELDS]
    m["allocated_revenue"] = alloc.sum(axis=1).where(alloc.notna().all(axis=1))
    m["generated_revenue"] = m["total_operating_revenue"] - m["allocated_revenue"]
    m["reported_result"] = m["total_operating_revenue"] - m["total_operating_expenses"]
    m["reported_margin"] = m["reported_result"] / m["total_operating_expenses"]
    m["self_sufficiency"] = m["generated_revenue"] / m["total_operating_expenses"]
    m["commercial_share"] = m["commercial_revenue"] / m["total_operating_revenue"]

    _conference_benchmarks(m, tables["conferences"], fy, rules)

    aud = tables["audience"]
    aud = aud[aud["season"] == rules["audience_season"]]
    for key, metric in AUDIENCE_METRICS.items():
        rows = aud[aud["metric"] == metric].drop_duplicates("school_id", keep="last").set_index("school_id")
        m[key] = _num(rows["value"]).reindex(m.index)
    return m


def _conference_benchmarks(m, conferences, fy, rules):
    """Each school's generated revenue vs. the median of its conference peers.

    Peers = other members of the same FY conference with known generated revenue.
    If too few of the conference's members have data, the benchmark is left blank
    rather than treating a partial sample as the whole conference.
    """
    conf = conferences[conferences["fiscal_year"] == fy].set_index("conference_id")
    member_count = _num(conf["member_count"]) if len(conf) else pd.Series(dtype=float)
    if rules.get("peer_coverage_basis") == "public_members" and len(conf):
        # private members never publish NCAA reports, so measure coverage against public members
        member_count = _num(conf["public_member_count"]).fillna(member_count)

    m["peer_count"] = 0
    m["peer_coverage"] = np.nan
    m["conf_peer_median_generated"] = np.nan
    m["conf_relative_generated"] = np.nan
    m["conf_peer_median_commercial_share"] = np.nan
    for school_id, row in m.iterrows():
        cid = row["conference_id"]
        if not cid:
            continue
        peers = m[(m["conference_id"] == cid) & (m.index != school_id)]
        known = peers["generated_revenue"].dropna()
        total = member_count.get(cid, np.nan)
        coverage = len(known) / (total - 1) if total and total > 1 else np.nan
        m.loc[school_id, "peer_count"] = len(known)
        m.loc[school_id, "peer_coverage"] = coverage
        m.loc[school_id, "conf_peer_median_commercial_share"] = peers["commercial_share"].median()
        if len(known) and coverage >= rules["min_peer_coverage"]:
            median = known.median()
            m.loc[school_id, "conf_peer_median_generated"] = median
            m.loc[school_id, "conf_relative_generated"] = row["generated_revenue"] / median

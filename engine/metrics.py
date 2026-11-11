"""FY financial and audience metrics per school, before any scoring.

Definitions (NCAA Membership Financial Reporting System categories):
  allocated revenue  = direct institutional support + indirect institutional support
                       + student fees + direct government support
  generated revenue  = total operating revenue - allocated revenue
  reported result    = total operating revenue - total operating expenses (as reported,
                       i.e. after subsidies and student fees)
  self-sufficiency   = generated revenue / total operating expenses
  own-operations revenue = generated revenue - (media rights + NCAA & conference distributions
                       + post-season football). Conference payouts are similar for every member and
                       negotiated by the conference, so this isolates what the department's own
                       operations (tickets, sponsorship, fundraising, etc.) bring in.
  commercial revenue = the NCAA category combining sponsorship, advertising, licensing and
                       related items. It is NOT pure sponsorship revenue.
  commercial per fan = commercial revenue / football average home attendance (the one sport with
                       official attendance for every school)
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


def school_metrics(tables, rules, competition=None):
    """One row per school (all schools, including benchmark-only peers)."""
    fy = str(rules["scoring_fiscal_year"])
    schools = tables["schools"].set_index("school_id")

    m = pd.DataFrame(index=schools.index)
    short = schools["short_name"] if "short_name" in schools else pd.Series("", index=schools.index)
    m["name"] = short.where(short != "", schools["name"])
    m["full_name"] = schools["name"]
    m["state"] = schools["state"]
    m["in_universe"] = schools["in_universe"] == "yes"
    m["featured"] = (schools["featured"] == "yes") if "featured" in schools else False
    members = tables["memberships"]
    members = members[members["fiscal_year"] == fy].set_index("school_id")
    m["conference_id"] = members["conference_id"].reindex(m.index).fillna("")
    power4 = set(rules.get("power4_conferences", []))
    m["segment"] = np.where(m["conference_id"].isin(power4), "Power 4", "Group of 5 & other FBS")

    fin = tables["financials"]
    fin = fin[fin["fiscal_year"] == fy].drop_duplicates("school_id", keep="last").set_index("school_id")
    for col in MONEY_FIELDS:
        m[col] = _num(fin[col]).reindex(m.index) if col in fin else np.nan
    m["financial_source_id"] = fin["source_id"].reindex(m.index).fillna("") if len(fin) else ""

    # allocated revenue: every separate line present (0 is fine), else a reported total, else unknown
    alloc = m[ALLOCATED_FIELDS]
    m["allocated_revenue"] = alloc.sum(axis=1).where(alloc.notna().all(axis=1)).fillna(m["allocated_revenue_total"])
    m["generated_revenue"] = m["total_operating_revenue"] - m["allocated_revenue"]
    m["own_operations_revenue"] = m["generated_revenue"] - m["conference_ncaa_media_revenue"]
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
    m["commercial_per_fan"] = m["commercial_revenue"] / m["football"]

    _market_metrics(m, tables, rules, competition or {})
    return m


def _market_metrics(m, tables, rules, competition):
    """Regional Sponsorship Appeal inputs.

    Market = the school's metro area (Census CBSA), widened to its Combined Statistical Area when it has one, so
    Boulder competes with Denver's teams. A school in a smaller metro with no major-league team in its metro or
    combined area (rules) draws sponsors statewide instead: its state outside the metros that do host major-league teams
    (Iowa: all of Iowa; Penn State: Pennsylvania outside Philadelphia and Pittsburgh). Competing weight = sum
    of league weights of every other team and FBS program in that market; Power 4 schools ignore leagues below
    their level (rules["power4_ignores_rivals"]). Sponsor pool per property = sponsor-type businesses / (1 + competing weight).
    Fan intensity = football average home attendance / metro population (always the metro: local dominance).
    """
    for col in ("market_scope", "cbsa_name"):
        m[col] = ""
    for col in ("metro_population", "competing_weight", "sponsor_pool", "sponsor_pool_per_property",
                "fan_intensity"):
        m[col] = np.nan
    loc = tables["school_markets"].drop_duplicates("school_id", keep="last").set_index("school_id")
    loc = loc[loc.index.isin(m.index)]
    if loc.empty:
        return

    stats = tables["market_stats"]
    stat = lambda geo_type, metric: _num(stats[(stats["geo_type"] == geo_type) & (stats["metric"] == metric)]
                                         .drop_duplicates("geo_id", keep="last").set_index("geo_id")["value"])
    population, pool_cbsa, pool_state = stat("cbsa", "population"), stat("cbsa", "sponsor_businesses"), \
        stat("state", "sponsor_businesses_outside_major_metros")

    # every team that competes for sponsors: pro teams, other FBS programs, and our own schools
    ours = pd.DataFrame({"team_id": loc.index, "state": loc["state"], "cbsa_code": loc["cbsa_code"],
                         "league": np.where(m.loc[loc.index, "segment"] == "Power 4", "FBS_POWER4", "FBS_OTHER")})
    teams = pd.concat([tables["market_teams"][["team_id", "state", "cbsa_code", "league"]], ours],
                      ignore_index=True)
    teams["weight"] = teams["league"].map(competition).fillna(0.0)
    csa = _combined_areas(tables)
    teams["csa"] = teams["cbsa_code"].map(csa)
    major = teams["league"].isin(rules.get("statewide_market_leagues", []))
    major_metros, major_csas = set(teams.loc[major, "cbsa_code"]), set(teams.loc[major, "csa"].dropna())

    for sid, r in loc.iterrows():
        pop = population.get(r["cbsa_code"], np.nan)
        area = csa.get(r["cbsa_code"])
        statewide = (pd.notna(pop) and pop < rules.get("statewide_market_max_population", 0)
                     and r["cbsa_code"] not in major_metros and area not in major_csas)
        same = ((teams["state"] == r["state"]) & ~teams["cbsa_code"].isin(major_metros) if statewide
                else _same_market(teams, r["cbsa_code"], area))
        rivals = teams[same & (teams["team_id"] != sid)]
        if m.loc[sid, "segment"] == "Power 4":
            rivals = rivals[~rivals["league"].isin(rules.get("power4_ignores_rivals", []))]
        pool = pool_state.get(r["state"], np.nan) if statewide else pool_cbsa.get(r["cbsa_code"], np.nan)
        m.loc[sid, ["market_scope", "cbsa_name"]] = ["state" if statewide else "metro", r["cbsa_name"]]
        m.loc[sid, "metro_population"] = pop
        m.loc[sid, "competing_weight"] = rivals["weight"].sum()
        m.loc[sid, "sponsor_pool"] = pool
        m.loc[sid, "sponsor_pool_per_property"] = pool / (1 + rivals["weight"].sum())
    m["fan_intensity"] = m["football"] / m["metro_population"]


def market_rivals(school_id, tables, scored, rules, competition):
    """The teams counted against one school's market, for the profile page."""
    row = scored.loc[school_id]
    loc = tables["school_markets"].drop_duplicates("school_id", keep="last").set_index("school_id")
    if school_id not in loc.index or not row["market_scope"]:
        return pd.DataFrame(columns=["name", "league", "city", "weight"])
    pro = tables["market_teams"][["name", "league", "city", "state", "cbsa_code"]]
    ours = pd.DataFrame({"name": scored.loc[scored.index.isin(loc.index), "full_name"],
                         "league": np.where(scored.loc[scored.index.isin(loc.index), "segment"] == "Power 4",
                                            "FBS_POWER4", "FBS_OTHER")})
    ours = ours.join(loc[["city", "state", "cbsa_code"]])
    teams = pd.concat([pro, ours.drop(index=school_id)], ignore_index=True)
    csa = _combined_areas(tables)
    teams["csa"] = teams["cbsa_code"].map(csa)
    me = loc.loc[school_id]
    major_metros = set(pro.loc[pro["league"].isin(rules.get("statewide_market_leagues", [])), "cbsa_code"])
    same = ((teams["state"] == me["state"]) & ~teams["cbsa_code"].isin(major_metros)
            if row["market_scope"] == "state" else _same_market(teams, me["cbsa_code"], csa.get(me["cbsa_code"])))
    out = teams[same].assign(weight=lambda t: t["league"].map(competition).fillna(0.0))
    if row["segment"] == "Power 4":
        out = out[~out["league"].isin(rules.get("power4_ignores_rivals", []))]
    return out[["name", "league", "city", "weight"]].sort_values(["weight", "name"], ascending=[False, True])


def _combined_areas(tables):
    """metro (CBSA) code -> its Combined Statistical Area code, for metros that belong to one."""
    areas = tables.get("market_areas")
    if areas is None or areas.empty:
        return {}
    areas = areas[areas["csa_code"] != ""].drop_duplicates("cbsa_code", keep="last")
    return dict(zip(areas["cbsa_code"], areas["csa_code"]))


def _same_market(teams, cbsa_code, csa_code):
    """Teams in the same metro, or anywhere in the same combined area."""
    same = teams["cbsa_code"] == cbsa_code
    return same | (teams["csa"] == csa_code) if csa_code else same


def _conference_benchmarks(m, conferences, fy, rules):
    """Each school's revenue vs. the median of its conference peers.

    Which revenue is set by rules["conference_comparison_basis"]: "own_operations" (default)
    or "generated" (NCAA definition).

    Peers = other members of the same FY conference with known generated revenue.
    If too few of the conference's members have data, the benchmark is left blank
    rather than treating a partial sample as the whole conference.
    """
    conf = conferences[conferences["fiscal_year"] == fy].set_index("conference_id")
    member_count = _num(conf["member_count"]) if len(conf) else pd.Series(dtype=float)
    if rules.get("peer_coverage_basis") == "public_members" and len(conf):
        # private members never publish NCAA reports, so measure coverage against public members
        member_count = _num(conf["public_member_count"]).fillna(member_count)

    basis = "own_operations_revenue" if rules.get("conference_comparison_basis", "own_operations") == "own_operations" \
        else "generated_revenue"
    m["peer_count"] = 0
    m["peer_coverage"] = np.nan
    m["conf_peer_median_generated"] = np.nan
    m["conf_relative_generated"] = np.nan
    m["conf_peer_median_commercial_share"] = np.nan
    for school_id, row in m.iterrows():
        cid = row["conference_id"]
        if not cid or cid in rules.get("no_benchmark_conferences", []):
            continue
        peers = m[(m["conference_id"] == cid) & (m.index != school_id)]
        known = peers[basis].dropna()
        total = member_count.get(cid, np.nan)
        coverage = len(known) / (total - 1) if total and total > 1 else np.nan
        m.loc[school_id, "peer_count"] = len(known)
        m.loc[school_id, "peer_coverage"] = coverage
        m.loc[school_id, "conf_peer_median_commercial_share"] = peers["commercial_share"].median()
        if len(known) >= rules.get("min_peer_count", 1) and coverage >= rules["min_peer_coverage"]:
            median = known.median()
            m.loc[school_id, "conf_peer_median_generated"] = median
            m.loc[school_id, "conf_relative_generated"] = row[basis] / median

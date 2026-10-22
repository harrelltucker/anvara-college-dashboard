"""Turn metrics into 0-100 scores.

Normalization: percentile rank among the schools in the ranking universe, rescaled so the
lowest school scores 0 and the highest 100. Ranks can't be stretched by one outlier
(e.g., Texas's revenue), and they read simply: "ahead of X% of the group".
Raw values are always shown alongside so the size of gaps isn't hidden.

Missing data is never scored as 0. A category is scored from the components that have
data, re-weighted, provided they cover enough of the category's weight; otherwise the
category is "incomplete". The same rule applies to the overall score.
"""

from datetime import date

import numpy as np
import pandas as pd

from engine.metrics import school_metrics

CATEGORY_LABELS = {
    "financial_pressure": "Financial Pressure",
    "commercial_opportunity": "Commercial Opportunity",
    "growth_catalysts": "Growth Catalysts",
}
COMPONENT_LABELS = {
    "reported_result": "Reported surplus/deficit (% of expenses)",
    "conference_relative_generated": "Own-operations revenue vs. conference public peers",
    "self_sufficiency": "Financial self-sufficiency",
    "commercial_revenue": "Sponsorship, advertising & licensing revenue (as reported to the NCAA, category 15)",
    "fan_reach": "Fan reach (attendance)",
}


def percentile_score(values, higher_is_better=True):
    """0-100 rank score among non-missing values; missing stays missing."""
    s = pd.Series(values, dtype=float)
    known = s.dropna()
    out = pd.Series(np.nan, index=s.index)
    if len(known) == 1:
        out[known.index] = 50.0
    elif len(known) > 1:
        out[known.index] = (known.rank(method="average") - 1) / (len(known) - 1) * 100
    return out if higher_is_better else 100 - out


def weighted_score(components, weights, min_coverage):
    """Weighted average over components with data. Returns (score, coverage share)."""
    total = sum(weights.values())
    frame = pd.DataFrame(components)
    w = pd.Series(weights, dtype=float)
    present = frame.notna()
    covered = present.mul(w, axis=1).sum(axis=1)
    score = frame.fillna(0).mul(w, axis=1).sum(axis=1) / covered.replace(0, np.nan)
    coverage = covered / total if total else covered * 0
    return score.where(coverage >= min_coverage), coverage


def catalyst_points(catalysts, settings, as_of):
    """Points per distinct event (duplicates of one event count once, at their best)."""
    if catalysts.empty:
        return pd.DataFrame(columns=["school_id", "event_id", "points"])
    c = catalysts.copy()
    sig = c["significance"].map({k: settings[f"significance_{k}"] for k in ("high", "medium", "low")})
    rel = c["commercial_relevance"].map({"direct": settings["relevance_direct"],
                                         "indirect": settings["relevance_indirect"]})
    conf = c["confidence"].map({"confirmed": settings["confidence_confirmed"],
                                "reported": settings["confidence_reported"]})
    months = (pd.Timestamp(as_of) - pd.to_datetime(c["event_date"], errors="coerce")).dt.days / 30.44
    recency = np.select([months <= settings["recency_full_credit_months"],
                         months <= settings["recency_half_credit_months"]], [1.0, 0.5], 0.25)
    c["points"] = (sig * rel * conf * recency).fillna(0)
    return c.groupby(["school_id", "event_id"], as_index=False)["points"].max()


def score_schools(tables, weights, as_of=None):
    """Full scored table: metrics, component scores, category scores, overall score."""
    as_of = as_of or date.today()
    rules = weights["rules"]
    m = school_metrics(tables, rules)
    u = m[m["in_universe"]].copy()

    # Financial Pressure: weaker finances => higher score
    fp = {
        "reported_result": percentile_score(u["reported_margin"], higher_is_better=False),
        "conference_relative_generated": percentile_score(u["conf_relative_generated"], higher_is_better=False),
        "self_sufficiency": percentile_score(u["self_sufficiency"], higher_is_better=False),
    }
    # Commercial Opportunity: bigger commercial business and audience => higher score
    reach_parts = {k: percentile_score(u[k]) for k in weights["fan_reach"]}
    u["fan_reach_score"], u["fan_reach_coverage"] = weighted_score(
        reach_parts, weights["fan_reach"], rules["min_component_coverage"])
    co = {
        "commercial_revenue": percentile_score(u["commercial_revenue"]),
        "fan_reach": u["fan_reach_score"],
    }
    for name, comps in (("financial_pressure", fp), ("commercial_opportunity", co)):
        for comp, values in comps.items():
            u[f"{name}.{comp}"] = values
        u[name], u[f"{name}_coverage"] = weighted_score(comps, weights[name], rules["min_component_coverage"])

    u["growth_catalysts"], u["catalyst_events"] = _catalyst_scores(u.index, tables, weights["catalysts"], as_of)
    u["growth_catalysts_coverage"] = u["growth_catalysts"].notna().astype(float)

    u["overall"], u["overall_coverage"] = weighted_score(
        {k: u[k] for k in CATEGORY_LABELS}, weights["categories"], rules["min_overall_coverage"])
    u["confidence"] = _confidence(u)
    u["completeness"] = _completeness(u, tables)
    u["rank"] = u["overall"].rank(ascending=False, method="min")
    return u.sort_values(["overall", "name"], ascending=[False, True], na_position="last")


def _catalyst_scores(school_ids, tables, settings, as_of):
    """Rubric score (not a percentile): events are sparse, so absolute points are fairer.

    'Researched, none found' is a real 0. 'Not yet researched' (and no events) is missing.
    """
    points = catalyst_points(tables["catalysts"], settings, as_of)
    totals = points.groupby("school_id")["points"].sum().clip(upper=100)
    counts = points.groupby("school_id")["event_id"].nunique()
    status = tables["research_status"]
    researched = set(status[(status["area"] == "catalysts") & (status["status"] == "complete")]["school_id"])
    scores = pd.Series({s: totals.get(s, 0.0 if s in researched else np.nan) for s in school_ids})
    return scores, pd.Series({s: int(counts.get(s, 0)) for s in school_ids})


def _confidence(u):
    cats = list(CATEGORY_LABELS)
    full = ((u[[f"{c}_coverage" for c in cats]] >= 0.999).all(axis=1)
            & (u["fan_reach_coverage"] >= 0.999))      # a missing sport inside fan reach counts too
    n_cats = u[cats].notna().sum(axis=1)
    return np.select([u["overall"].isna(), full, n_cats == 3], ["Insufficient data", "High", "Medium"], "Low")


def _completeness(u, tables):
    """Share of the key research inputs that are present."""
    status = tables["research_status"]
    done = lambda area: set(status[(status["area"] == area) & (status["status"] == "complete")]["school_id"])
    checks = pd.DataFrame({
        "revenue & expenses": u["total_operating_revenue"].notna() & u["total_operating_expenses"].notna(),
        "allocated revenue lines": u["allocated_revenue"].notna(),
        "commercial revenue": u["commercial_revenue"].notna(),
        "conference benchmark": u["conf_relative_generated"].notna(),
        "football attendance": u["football"].notna(),
        "men's basketball attendance": u["mens_basketball"].notna(),
        "women's basketball attendance": u["womens_basketball"].notna(),
        "catalysts researched": u.index.isin(done("catalysts")),
        "rights holders researched": u.index.isin(done("rights")),
        "contacts researched": u.index.isin(done("contacts")),
    }, index=u.index)
    return checks.mean(axis=1)


def missing_inputs(row, tables):
    """Plain-language list of what's missing for one scored school row."""
    status = tables["research_status"]
    s = status[status["school_id"] == row.name].set_index("area")["status"]
    items = []
    if pd.isna(row["total_operating_revenue"]) or pd.isna(row["total_operating_expenses"]):
        items.append("FY2025 total operating revenue and expenses")
    if pd.isna(row["allocated_revenue"]):
        items.append("FY2025 allocated revenue lines (institutional support, student fees, government support)")
    if pd.isna(row["commercial_revenue"]):
        items.append("FY2025 sponsorship, advertising & licensing revenue (as reported to the NCAA, category 15)")
    if pd.isna(row["conf_relative_generated"]):
        items.append(f"Conference benchmark (have {int(row['peer_count'])} peers with data; "
                     "need more conference members' FY2025 financials)")
    for key, label in (("football", "football"), ("mens_basketball", "men's basketball"),
                       ("womens_basketball", "women's basketball")):
        if pd.isna(row[key]):
            items.append(f"2024-25 {label} average home attendance")
    for area in ("catalysts", "rights", "contacts"):
        if s.get(area) != "complete":
            items.append(f"{area.capitalize()} research ({s.get(area, 'not_started').replace('_', ' ')})")
    return items

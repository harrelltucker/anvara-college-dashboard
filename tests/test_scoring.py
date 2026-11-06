"""Scoring rules that must always hold. Run:  python -m pytest"""

import copy
from datetime import date

import numpy as np
import pandas as pd
import pytest

from engine.data import DEMO_DIR, load_tables, load_weights
from engine.scoring import catalyst_points, percentile_score, score_schools, weighted_score

AS_OF = date(2026, 10, 22)


@pytest.fixture
def demo():
    return load_tables(DEMO_DIR)


@pytest.fixture
def weights():
    return load_weights()


def test_missing_values_stay_missing_not_zero():
    s = percentile_score([10, np.nan, 30, 20])
    assert np.isnan(s[1])
    assert s.dropna().min() == 0 and s.dropna().max() == 100


def test_outlier_does_not_compress_everyone_else():
    normal = percentile_score([10, 20, 30, 40])
    with_outlier = percentile_score([10, 20, 30, 4000])
    assert list(normal) == list(with_outlier)


def test_incomplete_category_is_not_scored():
    comps = {"a": pd.Series([50.0]), "b": pd.Series([np.nan])}
    score, coverage = weighted_score(comps, {"a": 40, "b": 60}, min_coverage=0.6)
    assert np.isnan(score[0]) and coverage[0] == pytest.approx(0.4)
    score, _ = weighted_score(comps, {"a": 70, "b": 30}, min_coverage=0.6)
    assert score[0] == 50.0           # re-weighted over available data, not dragged to 0


def test_duplicate_announcements_count_once(weights):
    cats = pd.DataFrame([
        {"school_id": "X", "event_id": "E1", "event_date": "2026-09-01", "significance": "high",
         "commercial_relevance": "direct", "confidence": "confirmed"},
        {"school_id": "X", "event_id": "E1", "event_date": "2026-09-05", "significance": "high",
         "commercial_relevance": "direct", "confidence": "confirmed"},
    ])
    pts = catalyst_points(cats, weights["catalysts"], AS_OF)
    assert len(pts) == 1 and pts["points"].iloc[0] == 45


def test_unresearched_catalysts_are_missing_but_researched_none_is_zero(demo, weights):
    s = score_schools(demo, weights, as_of=AS_OF)
    assert np.isnan(s.loc["DEMO08", "growth_catalysts"])        # research not started
    assert s.loc["DEMO02", "growth_catalysts"] == 0             # researched, nothing found


def test_missing_sport_in_fan_reach_lowers_confidence(demo, weights):
    w = copy.deepcopy(weights)
    w["fan_reach"] = {"football": 60, "mens_basketball": 25, "womens_basketball": 15}
    s = score_schools(demo, w, as_of=AS_OF)
    assert s.loc["DEMO06", "fan_reach_coverage"] < 1             # no women's basketball figure
    assert s.loc["DEMO06", "confidence"] != "High"


def test_benchmark_only_peers_are_not_ranked(demo, weights):
    s = score_schools(demo, weights, as_of=AS_OF)
    assert not {"DEMO13", "DEMO14", "DEMO15"} & set(s.index)


def test_partial_conference_sample_is_not_a_benchmark(demo, weights):
    thin = copy.deepcopy(demo)
    thin["conferences"]["member_count"] = "30"                  # pretend most members lack data
    s = score_schools(thin, weights, as_of=AS_OF)
    assert s["conf_relative_generated"].isna().all()
    assert s["financial_pressure"].notna().all()               # other components still score


def test_weight_changes_move_rankings_in_expected_direction(demo, weights):
    commercial_heavy = copy.deepcopy(weights)
    commercial_heavy["categories"] = {"financial_pressure": 0, "commercial_opportunity": 100, "growth_catalysts": 0}
    s = score_schools(demo, commercial_heavy, as_of=AS_OF)
    top = s["overall"].idxmax()
    assert top == s["commercial_opportunity"].idxmax()


def test_low_commercial_revenue_is_not_rewarded(demo, weights):
    s = score_schools(demo, weights, as_of=AS_OF)
    lowest = s["commercial_revenue"].idxmin()
    assert s.loc[lowest, "commercial_opportunity.commercial_revenue"] == 0


def test_scores_are_ranked_within_segments(demo, weights):
    w = copy.deepcopy(weights)
    w["rules"]["power4_conferences"] = ["DEMO-N"]               # split the demo schools into two segments
    s = score_schools(demo, w, as_of=AS_OF)
    assert set(s["segment"]) == {"Power 4", "Group of 5 & other FBS"}
    for _, g in s.groupby("segment"):
        top = g["commercial_opportunity.commercial_revenue"].dropna()
        assert top.max() == 100 and top.min() == 0              # each segment has its own 0-100 scale


def test_unweighted_sport_is_not_required(demo, weights):
    w = copy.deepcopy(weights)
    w["fan_reach"] = {"football": 100, "mens_basketball": 0, "womens_basketball": 0}
    s = score_schools(demo, w, as_of=AS_OF)
    assert s.loc["DEMO06", "fan_reach_coverage"] >= 0.999        # missing women's basketball doesn't count

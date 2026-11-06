"""Plain-language summaries for the public copy: why each school is an opportunity, in one or two lines."""

from datetime import date

import pandas as pd

from engine.scoring import catalyst_points
from ui.fmt import money, pct

LABELS = {"financial_pressure": "Financial pressure", "commercial_opportunity": "Commercial opportunity",
          "growth_catalysts": "Momentum"}
STATES = {"AL": "Alabama", "AR": "Arkansas", "AZ": "Arizona", "CA": "California", "CO": "Colorado",
          "CT": "Connecticut", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "IA": "Iowa", "ID": "Idaho",
          "IL": "Illinois", "IN": "Indiana", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
          "MA": "Massachusetts", "MD": "Maryland", "MI": "Michigan", "MN": "Minnesota", "MO": "Missouri",
          "MS": "Mississippi", "NC": "North Carolina", "NE": "Nebraska", "NJ": "New Jersey", "NM": "New Mexico",
          "NV": "Nevada", "NY": "New York", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
          "SC": "South Carolina", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VA": "Virginia",
          "WA": "Washington", "WI": "Wisconsin", "WV": "West Virginia", "WY": "Wyoming"}
MEANING = {"financial_pressure": "How much the department needs new revenue",
           "commercial_opportunity": "How much room there is to grow sponsorship",
           "growth_catalysts": "Recent moves to build its commercial business"}


def top_events(tables, weights):
    """school_id -> (short title, date) of its highest-scoring recent catalyst."""
    points = catalyst_points(tables["catalysts"], weights["catalysts"], date.today())
    if points.empty:
        return {}
    best = points.sort_values("points", ascending=False).drop_duplicates("school_id")
    events = tables["catalysts"].drop_duplicates("event_id").set_index("event_id")
    return {r.school_id: (short_title(events.loc[r.event_id, "title"]), events.loc[r.event_id, "event_date"])
            for r in best.itertuples() if r.event_id in events.index}


def short_title(title):
    return title.split(";")[0].split(" (")[0].strip()


def reasons(row, events, limit=3):
    """Strongest reasons first, each with its number. Only reasons the scores actually support."""
    out = []                                        # (strength, text)
    fp = row["financial_pressure"]
    if pd.notna(fp) and fp >= 67:
        if pd.notna(row["reported_result"]) and row["reported_result"] < -1e6:
            text = f"Ran a {money(-row['reported_result'])} athletics deficit in FY2025"
        elif pd.notna(row["self_sufficiency"]) and row["self_sufficiency"] < 0.75:
            text = f"Earns only {pct(row['self_sufficiency'])} of what it spends; the rest is subsidy"
        else:
            text = f"Relies on {money(row['allocated_revenue'])} of school support and student fees"
        out.append((fp, text))
    untapped = row.get("commercial_opportunity.untapped_value")
    if pd.notna(untapped) and untapped >= 70 and pd.notna(row["football"]):
        out.append((untapped, f"Little sponsorship revenue for its crowds: {money(row['commercial_revenue'])} "
                              f"with {row['football']:,.0f} fans a game"))
    reach = row.get("commercial_opportunity.fan_reach")
    if pd.notna(reach) and reach >= 75 and pd.notna(row["football"]):
        out.append((reach, f"One of the biggest audiences in its group ({row['football']:,.0f} per football game)"))
    alone = row.get("regional_appeal.only_game_in_town")
    if pd.notna(alone) and alone >= 80 and row.get("competing_weight", 1) == 0:
        where = f"across {STATES.get(row['state'], row['state'])}" if row.get("market_scope") == "state" else "in its metro area"
        out.append((alone - 10, f"No major pro team competing for sponsors {where}"))
    gc = row["growth_catalysts"]
    if pd.notna(gc) and gc >= 40 and row.name in events:
        title, when = events[row.name]
        out.append((gc, f"{title} ({str(when)[:4]})"))
    out.sort(key=lambda r: -r[0])
    return [text for _, text in out[:limit]] or ["Solid across all three measures, with no single standout"]

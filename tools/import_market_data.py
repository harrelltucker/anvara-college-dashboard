"""Queue Regional Sponsorship Appeal inputs from official bulk files.

Downloads (kept out of Git, in data/incoming/market/):
  HD2023.csv          IPEDS 2023 directory (NCES): each school's city, county and metro area (CBSA)
  cbp23msa.txt        Census County Business Patterns 2023, by metro area
  cbp23co.txt         Census County Business Patterns 2023, by county
  cbsa-est2025.csv    Census population estimates, July 1 2025, by metro area
  wikipedia/*.html    League pages (team, city) for NFL, MLB, NBA, NHL, MLS, WNBA, NWSL, as of retrieval

Every value is queued as a finding, grouped by source, so each file is verified once in the review queue.

Usage:
  python tools/import_market_data.py            (preview)
  python tools/import_market_data.py --submit   (queue findings)
"""

import difflib
import io
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.data import ROOT, load_findings  # noqa: E402
from engine.research import submit_finding  # noqa: E402
from tools.fbs_registry import SCHOOLS  # noqa: E402

IN = ROOT / "data" / "incoming" / "market"
BY = "tools/import_market_data.py"
RETRIEVED = "2026-10-23"

IPEDS = ("IPEDS 2023-24 Institutional Characteristics: Directory information (HD2023), NCES",
         "https://nces.ed.gov/ipeds/datacenter/data/HD2023.zip")
CBP_MSA = ("County Business Patterns 2023, metropolitan and micropolitan areas (U.S. Census Bureau)",
           "https://www2.census.gov/programs-surveys/cbp/datasets/2023/cbp23msa.zip")
CBP_CO = ("County Business Patterns 2023, counties (U.S. Census Bureau)",
          "https://www2.census.gov/programs-surveys/cbp/datasets/2023/cbp23co.zip")
MAJOR_LEAGUES = ["NFL", "MLB", "NBA", "NHL"]       # keep in step with rules.statewide_market_leagues
PEP = ("Annual Estimates of the Resident Population for Metropolitan and Micropolitan Statistical Areas, "
       "July 1 2025 (U.S. Census Bureau, Vintage 2025)",
       "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/metro/totals/cbsa-est2025-alldata.csv")
LEAGUES = {   # league: (Wikipedia page, table number, team column, city column)
    "NFL": ("National_Football_League", 2, "Team[53]", "City"),
    "MLB": ("Major_League_Baseball", 1, "Team", "City"),
    "NBA": ("National_Basketball_Association", 1, "Team", "Location"),
    "NHL": ("National_Hockey_League", 2, "Team", "City"),
    "MLS": ("Major_League_Soccer", 1, "Club", "Location"),
    "WNBA": ("Women%27s_National_Basketball_Association", 2, "Team", "City"),
    "NWSL": ("National_Women%27s_Soccer_League", 1, "Team", "Location"),
}

# Sponsor-type industries (NAICS 2017, 4-digit), counted at establishments with 20+ employees.
# Restaurants (7225) are left out: they'd be two-thirds of the count and swamp every other industry.
SPONSOR_INDUSTRIES = {
    "5221": "banks & credit unions", "5242": "insurance agencies", "6221": "hospitals", "4411": "auto dealers",
    "5411": "law firms", "4451": "grocery stores", "2382": "building-equipment contractors (HVAC, plumbing, "
    "electrical)", "2211": "electric utilities", "3121": "beverage makers", "4248": "beer, wine & spirits distributors",
}
SIZE_CLASSES = ["n20_49", "n50_99", "n100_249", "n250_499", "n500_999", "n1000"]

# Knight-Newhouse names that don't match the IPEDS name exactly
IPEDS_NAMES = {
    "PURDUE": "Purdue University-Main Campus", "ARIZSTATE": "Arizona State University Campus Immersion",
    "LSU": "Louisiana State University and Agricultural & Mechanical College",
    "TEXASAM": "Texas A & M University-College Station", "BUFFALO": "University at Buffalo",
    "COLOSTATE": "Colorado State University-Fort Collins", "ARMY": "United States Military Academy",
    "AKRON": "University of Akron Main Campus", "OHIOSTATE": "Ohio State University-Main Campus",
    "ALABAMA": "The University of Alabama", "MICHIGAN": "University of Michigan-Ann Arbor",
    "SOUTHCAROLINA": "University of South Carolina-Columbia", "TENNESSEE": "The University of Tennessee-Knoxville",
    "OKSTATE": "Oklahoma State University-Main Campus", "WASHINGTON": "University of Washington-Seattle Campus",
    "PENNSTATE": "Pennsylvania State University-Main Campus",
    "BOWLINGGREEN": "Bowling Green State University-Main Campus", "KENTSTATE": "Kent State University at Kent",
    "MIAMIOH": "Miami University-Oxford", "CINCINNATI": "University of Cincinnati-Main Campus",
    "VIRGINIA": "University of Virginia-Main Campus", "NCSTATE": "North Carolina State University at Raleigh",
    "OKLAHOMA": "University of Oklahoma-Norman Campus",
}
# FBS programs (2024 season) outside the 113: private, or public but not in Knight-Newhouse.
# They compete for the same sponsors. Power 4 by 2024-25 conference (Notre Dame counted as Power 4).
OTHER_FBS = {
    "BYU": ("Brigham Young University", "FBS_POWER4"), "BAYLOR": ("Baylor University", "FBS_POWER4"),
    "BC": ("Boston College", "FBS_POWER4"), "DUKE": ("Duke University", "FBS_POWER4"),
    "KENNESAW": ("Kennesaw State University", "FBS_OTHER"), "LIBERTY": ("Liberty University", "FBS_OTHER"),
    "MIAMIFL": ("University of Miami", "FBS_POWER4"), "NORTHWESTERN": ("Northwestern University", "FBS_POWER4"),
    "NOTREDAME": ("University of Notre Dame", "FBS_POWER4"),
    "PITT": ("University of Pittsburgh-Pittsburgh Campus", "FBS_POWER4"), "RICE": ("Rice University", "FBS_OTHER"),
    "SMU": ("Southern Methodist University", "FBS_POWER4"), "USC": ("University of Southern California", "FBS_POWER4"),
    "STANFORD": ("Stanford University", "FBS_POWER4"), "SYRACUSE": ("Syracuse University", "FBS_POWER4"),
    "TCU": ("Texas Christian University", "FBS_POWER4"), "TEMPLE": ("Temple University", "FBS_OTHER"),
    "TULANE": ("Tulane University of Louisiana", "FBS_OTHER"), "TULSA": ("University of Tulsa", "FBS_OTHER"),
    "VANDERBILT": ("Vanderbilt University", "FBS_POWER4"), "WAKE": ("Wake Forest University", "FBS_POWER4"),
}
# Team venue city -> CBSA code (2023 delineation). Suburban venues belong to their metro area.
TEAM_CBSA = {
    "Anaheim": "31080", "Arlington, Texas": "19100", "Atlanta": "12060", "Austin": "12420", "Baltimore": "12580",
    "Boston": "14460", "Bronx": "35620", "Brooklyn": "35620", "Buffalo": "15380", "Carson": "31080", "Cary": "39580",
    "Centennial": "19740", "Charlotte": "16740", "Chester": "37980", "Chicago": "16980", "Cincinnati": "17140",
    "Cleveland": "17410", "College Park": "12060", "Columbus": "18140", "Commerce City": "19740",
    "Cumberland": "12060", "Dallas": "19100", "Denver": "19740", "Detroit": "19820", "East Rutherford": "35620",
    "Elmont": "35620", "Evanston": "16980", "Foxborough": "14460", "Frisco": "19100", "Glendale": "38060",
    "Green Bay": "24580", "Harrison": "35620", "Houston": "26420", "Indianapolis": "26900", "Inglewood": "31080",
    "Jacksonville": "27260", "Kansas City": "28140", "Landover": "47900", "Los Angeles": "31080",
    "Louisville": "31140", "Memphis": "32820", "Miami Gardens": "33100", "Miami": "33100", "Milwaukee": "33340",
    "Minneapolis": "33460", "Nashville": "34980", "New Orleans": "35380", "New York": "35620", "Newark": "35620",
    "Oklahoma City": "36420", "Orchard Park": "15380", "Orlando": "36740", "Paradise": "29820",
    "Philadelphia": "37980", "Phoenix": "38060", "Pittsburgh": "38300", "Portland": "38900", "Raleigh": "39580",
    "Sacramento": "40900", "Saint Paul": "33460", "Salt Lake City": "41620", "San Antonio": "41700",
    "San Diego": "41740", "San Francisco": "41860", "San Jose": "41940", "Sandy": "41620", "Santa Clara": "41940",
    "Seattle": "42660", "St. Louis": "41180", "St. Petersburg": "45300", "Sunrise": "33100", "Tampa": "45300",
    "Washington": "47900", "West Sacramento": "40900",
}
STATES = {"Alabama": "AL", "Arizona": "AZ", "California": "CA", "Colorado": "CO", "D.C.": "DC", "Florida": "FL",
          "Georgia": "GA", "Illinois": "IL", "Indiana": "IN", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
          "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Missouri": "MO",
          "Nevada": "NV", "New Jersey": "NJ", "New York": "NY", "North Carolina": "NC", "Ohio": "OH",
          "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
          "Washington": "WA", "Wisconsin": "WI"}
CANADA = ("Ontario", "Quebec", "Manitoba", "Alberta", "British Columbia")


def _ipeds():
    hd = pd.read_csv(IN / "HD2023.csv", encoding="latin1", dtype=str)
    hd.columns = ["UNITID"] + list(hd.columns[1:])     # first header carries a byte-order mark
    return hd


def school_markets(hd, cbsa_names):
    public = hd[(hd["ICLEVEL"] == "1") & (hd["CONTROL"] == "1")]
    rows = []
    for kn_name, (sid, _, _, state) in SCHOOLS.items():
        name = IPEDS_NAMES.get(sid) or (kn_name if kn_name in set(public["INSTNM"]) else difflib.get_close_matches(
            kn_name, list(public[public["STABBR"] == state]["INSTNM"]), n=1, cutoff=0.4)[0])
        r = hd[(hd["INSTNM"] == name) & (hd["STABBR"] == state)].iloc[0]
        rows.append({"school_id": sid, "ipeds_unitid": r["UNITID"], "city": r["CITY"].replace("  ", " "),
                     "state": r["STABBR"], "county_fips": r["COUNTYCD"], "cbsa_code": r["CBSA"],
                     "cbsa_name": cbsa_names.get(r["CBSA"], ""), "_ipeds_name": name})
    return rows


def other_fbs(hd):
    rows = []
    for tid, (name, league) in OTHER_FBS.items():
        r = hd[hd["INSTNM"] == name].iloc[0]
        rows.append({"team_id": f"FBS-{tid}", "name": name, "league": league, "city": r["CITY"],
                     "state": r["STABBR"], "cbsa_code": r["CBSA"], "season": "2024"})
    return rows


def pro_teams():
    rows = []
    for league, (page, table, team_col, city_col) in LEAGUES.items():
        html = (IN / "wikipedia" / f"{page}.html").read_text(encoding="utf-8")
        html = re.sub(r'(colspan|rowspan)="(\d+)[^"]*"', r'\1="\2"', html)   # malformed spans break the parser
        t = pd.read_html(io.StringIO(html))[table]
        t.columns = [str(c) for c in t.columns]
        for _, r in t.iterrows():
            team = re.sub(r"\[.*?\]|[*†]", "", str(r[team_col])).strip()
            city = re.sub(r"\[.*?\]", "", str(r[city_col])).strip()
            if team == city or city.endswith(CANADA):      # section-header rows; Canadian teams
                continue
            place, state = [s.strip() for s in city.rsplit(",", 1)] if "," in city else (city, "")
            cbsa = TEAM_CBSA.get(city) or TEAM_CBSA[place]
            rows.append({"team_id": f"{league}-{re.sub(r'[^A-Z0-9]', '', team.upper())}", "name": team,
                         "league": league, "city": city, "state": STATES[state], "cbsa_code": cbsa,
                         "season": "2026", "_source": (f"{page.replace('_', ' ').replace('%27', chr(39))} "
                                                       f"(Wikipedia, teams table, retrieved {RETRIEVED})",
                                                       f"https://en.wikipedia.org/wiki/{page}")})
    return rows


def sponsor_pool(path, geo_cols):
    d = pd.read_csv(path, dtype=str)
    d = d[d["naics"].str.replace("/", "").isin(SPONSOR_INDUSTRIES)]
    counts = d[SIZE_CLASSES].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
    return counts.groupby(d[geo_cols].agg("".join, axis=1)).sum().astype(int)


def main():
    hd = _ipeds()
    pep = pd.read_csv(IN / "cbsa-est2025.csv", encoding="latin1", dtype=str)
    areas = pep[pep["LSAD"].isin(["Metropolitan Statistical Area", "Micropolitan Statistical Area"])]
    cbsa_names = dict(zip(areas["CBSA"], areas["NAME"]))
    schools = school_markets(hd, cbsa_names)
    teams = other_fbs(hd) + pro_teams()

    # stats only for the areas that matter: every school's metro, every state with a school
    cbsas = sorted({s["cbsa_code"] for s in schools})
    states = sorted({s["state"] for s in schools})
    fips = hd.drop_duplicates("STABBR").set_index("STABBR")["FIPS"].str.zfill(2)
    pool_msa = sponsor_pool(IN / "cbp23msa.txt", ["msa"])
    pool_county = sponsor_pool(IN / "cbp23co.txt", ["fipstate", "fipscty"])
    pop = areas.set_index("CBSA")["POPESTIMATE2025"]

    # statewide draw for small-metro schools: the state's counties outside metros with a major-league team
    major = {t["cbsa_code"] for t in teams if t["league"] in MAJOR_LEAGUES}
    counties = pep[pep["LSAD"] == "County or equivalent"][["CBSA", "STCOU"]]
    outside = counties[~counties["CBSA"].isin(major)]
    by_state = {s: int(pool_county[[c for c in outside["STCOU"] if c[:2] == fips[s] and c in pool_county]].sum())
                for s in states}
    # counties outside any metro/micro area aren't listed in the population file: add them
    in_area = set(counties["STCOU"])
    for s in states:
        by_state[s] += int(pool_county[[c for c in pool_county.index if c[:2] == fips[s] and c not in in_area
                                        and not c.endswith("999")]].sum())
    excluded = lambda s: ", ".join(sorted(cbsa_names[c] for c in major
                                          if s in cbsa_names[c].split(", ")[-1].split("-")))

    industries = "; ".join(f"{k} {v}" for k, v in SPONSOR_INDUSTRIES.items())
    note = f"Establishments with 20+ employees in sponsor-type industries (NAICS {industries}). Restaurants excluded."
    stats = ([{"geo_type": "cbsa", "geo_id": c, "geo_name": cbsa_names[c], "year": "2025", "metric": "population",
               "value": pop[c], "notes": "July 1 2025 estimate", "_source": PEP} for c in cbsas]
             + [{"geo_type": "cbsa", "geo_id": c, "geo_name": cbsa_names[c], "year": "2023",
                 "metric": "sponsor_businesses", "value": str(pool_msa.get(c, 0)), "notes": note,
                 "_source": CBP_MSA} for c in cbsas]
             + [{"geo_type": "state", "geo_id": s, "geo_name": s, "year": "2023",
                 "metric": "sponsor_businesses_outside_major_metros", "value": str(by_state[s]),
                 "notes": f"{note} Counties outside metros with an NFL/MLB/NBA/NHL team"
                          f"{' (excluded: ' + excluded(s) + ')' if excluded(s) else ''}.",
                 "_source": CBP_CO} for s in states])

    print(f"{len(schools)} school locations ({sum(1 for s in schools if not s['cbsa_name'])} without a metro), "
          f"{len(teams)} competing teams/programs, {len(stats)} market statistics")
    for s in schools:
        print(f"  {s['school_id']:<14} {s['_ipeds_name'][:45]:<45} {s['city']}, {s['state']} -> {s['cbsa_name']}")

    queued = {(f["target_table"], f["record_json"]) for _, f in load_findings().iterrows()}
    if "--submit" not in sys.argv:
        print("Preview only. Re-run with --submit to queue findings.")
        return
    n = 0
    for table, rows, default_source in (("school_markets", schools, IPEDS), ("market_teams", teams, IPEDS),
                                        ("market_stats", stats, None)):
        for row in rows:
            title, url = row.get("_source") or default_source
            record = {k: str(v) for k, v in row.items() if not k.startswith("_")}
            if (table, json.dumps(record, ensure_ascii=False)) in queued:     # re-runs don't duplicate
                continue
            submit_finding(table, record, title, url, "government_statistics" if "wikipedia" not in url else "other",
                           BY)
            n += 1
    print(f"Queued {n} findings.")


if __name__ == "__main__":
    main()

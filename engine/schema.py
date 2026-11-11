"""Table definitions: the single place that says what every CSV contains.

Used by data loading, validation, and the findings intake form.
"""

# NCAA "allocated" revenue: subsidies and student fees (net of transfers back to the institution)
ALLOCATED_FIELDS = ["direct_institutional_support", "indirect_institutional_support",
                    "student_fees", "direct_government_support"]
MONEY_FIELDS = [
    "total_operating_revenue", "total_operating_expenses", *ALLOCATED_FIELDS,
    "allocated_revenue_total",          # used only when the separate lines aren't available
    "commercial_revenue",
    "conference_ncaa_media_revenue",    # media rights + NCAA & conference distributions + bowl revenue
    "donor_contributions",              # contributions + in-kind
]

VERIFIED = ["verified_by", "verified_date"]

TABLES = {
    "sources": {
        "key": "source_id",
        "columns": ["source_id", "title", "publisher", "url", "source_type", "reporting_year",
                    "retrieved_date", "export_allowed", "license_note"],
        "required": ["source_id", "title", "url", "source_type", "retrieved_date", "export_allowed"],
        "enums": {"source_type": ["ncaa_financial_report", "university_disclosure", "state_portal",
                                  "eada", "conference", "university_release", "rights_holder",
                                  "ncaa_statistics", "government_statistics", "news", "other",
                                  "demonstration"],
                  "export_allowed": ["yes", "no"]},
        "dates": ["retrieved_date"],
        "urls": ["url"],
    },
    "conferences": {
        "key": "conference_id",
        "columns": ["conference_id", "name", "fiscal_year", "member_count", "public_member_count",
                    "source_id", "notes"],
        "required": ["conference_id", "name", "fiscal_year"],
        "numbers": ["member_count", "public_member_count"],
        "refs": {"source_id": "sources"},
    },
    "schools": {
        "key": "school_id",
        "columns": ["school_id", "name", "short_name", "ncaa_name", "state", "subdivision", "control",
                    "in_universe", "featured"],
        "required": ["school_id", "name", "subdivision", "control", "in_universe"],
        "enums": {"subdivision": ["FBS", "FCS"], "control": ["public", "private"],
                  "in_universe": ["yes", "no"],    # "no" = conference peer used only for benchmarks
                  "featured": ["yes", "no"]},      # "yes" = deep-research school (catalysts, contacts, brief)
    },
    "memberships": {
        "key": None,
        "columns": ["school_id", "conference_id", "fiscal_year", "source_id"],
        "required": ["school_id", "conference_id", "fiscal_year"],
        "refs": {"school_id": "schools", "conference_id": "conferences", "source_id": "sources"},
    },
    "financials": {
        "key": None,
        "columns": ["school_id", "fiscal_year", *MONEY_FIELDS, "commercial_revenue_label",
                    "source_id", *VERIFIED, "notes"],
        "required": ["school_id", "fiscal_year", "source_id", *VERIFIED],
        "numbers": MONEY_FIELDS,
        "refs": {"school_id": "schools", "source_id": "sources"},
        "dates": ["verified_date"],
    },
    "audience": {
        "key": None,
        "columns": ["school_id", "season", "metric", "value", "source_id", *VERIFIED, "notes"],
        "required": ["school_id", "season", "metric", "value", "source_id", *VERIFIED],
        "enums": {"metric": ["football_avg_home_attendance", "mbb_avg_home_attendance",
                             "wbb_avg_home_attendance", "other_avg_home_attendance",
                             "social_followers_total", "other_digital"]},
        "numbers": ["value"],
        "refs": {"school_id": "schools", "source_id": "sources"},
        "dates": ["verified_date"],
    },
    "catalysts": {
        "key": "catalyst_id",
        "columns": ["catalyst_id", "school_id", "event_id", "event_date", "category", "title",
                    "description", "significance", "commercial_relevance", "confidence",
                    "source_id", *VERIFIED],
        "required": ["catalyst_id", "school_id", "event_id", "event_date", "category", "title",
                     "significance", "commercial_relevance", "confidence", "source_id", *VERIFIED],
        "enums": {"category": ["private_capital", "in_house_rights_org", "commercial_leadership",
                               "sponsorship_initiative", "rights_restructuring", "new_inventory",
                               "major_partnership", "other"],
                  "significance": ["high", "medium", "low"],
                  "commercial_relevance": ["direct", "indirect"],
                  "confidence": ["confirmed", "reported"]},
        "refs": {"school_id": "schools", "source_id": "sources"},
        "dates": ["event_date", "verified_date"],
    },
    "market_context": {
        "key": "context_id",
        "columns": ["context_id", "date", "title", "description", "context_type", "status", "source_id"],
        "required": ["context_id", "date", "title", "context_type", "status", "source_id"],
        "enums": {"context_type": ["ncaa_rule", "legal_settlement", "legislation", "market_trend"],
                  "status": ["in_effect", "approved", "proposed", "scenario"]},
        "refs": {"source_id": "sources"},
        "dates": ["date"],
    },
    "rights_holders": {
        "key": "organization_id",
        "columns": ["organization_id", "name", "org_type", "ownership_note", "website", "source_id"],
        "required": ["organization_id", "name", "org_type"],
        "enums": {"org_type": ["multimedia_rights_company", "in_house_entity", "joint_venture",
                               "agency", "other"]},
        "refs": {"source_id": "sources"},
        "urls": ["website"],
    },
    "rights_relationships": {
        "key": "relationship_id",
        "columns": ["relationship_id", "school_id", "organization_id", "management_model",
                    "rights_scope", "agreement_details", "start_date", "expiration_date",
                    "expiration_verified", "source_id", *VERIFIED],
        "required": ["relationship_id", "school_id", "organization_id", "management_model",
                     "source_id", *VERIFIED],
        "enums": {"management_model": ["in_house", "outsourced", "joint_venture", "unknown"],
                  "expiration_verified": ["yes", "no"]},
        "refs": {"school_id": "schools", "organization_id": "rights_holders", "source_id": "sources"},
        "dates": ["start_date", "expiration_date", "verified_date"],
    },
    "contacts": {
        "key": "contact_id",
        "columns": ["contact_id", "school_id", "organization_id", "name", "title", "profile_url",
                    "business_contact", "source_id", *VERIFIED],
        "required": ["contact_id", "school_id", "name", "title", "source_id", *VERIFIED],
        "refs": {"school_id": "schools", "source_id": "sources"},
        "urls": ["profile_url"],
        "dates": ["verified_date"],
    },
    # Regional Sponsorship Appeal inputs: where each school is, who else competes there, how big the market is
    "school_markets": {
        "key": "school_id",
        "columns": ["school_id", "ipeds_unitid", "city", "state", "county_fips", "cbsa_code", "cbsa_name",
                    "source_id", *VERIFIED],
        "required": ["school_id", "cbsa_code", "source_id", *VERIFIED],
        "refs": {"school_id": "schools", "source_id": "sources"},
        "dates": ["verified_date"],
    },
    "market_teams": {     # pro teams, plus FBS programs outside the 113 (our own schools come from school_markets)
        "key": "team_id",
        "columns": ["team_id", "name", "league", "city", "state", "cbsa_code", "season", "source_id", *VERIFIED],
        "required": ["team_id", "name", "league", "state", "cbsa_code", "source_id", *VERIFIED],
        "enums": {"league": ["NFL", "MLB", "NBA", "NHL", "MLS", "WNBA", "NWSL", "FBS_POWER4", "FBS_OTHER"]},
        "refs": {"source_id": "sources"},
        "dates": ["verified_date"],
    },
    # Census Combined Statistical Areas: metros that form one wider market (Boulder is part of greater Denver)
    "market_areas": {
        "key": "cbsa_code",
        "columns": ["cbsa_code", "cbsa_title", "csa_code", "csa_title", "source_id", *VERIFIED],
        "required": ["cbsa_code", "csa_code", "source_id", *VERIFIED],
        "refs": {"source_id": "sources"},
        "dates": ["verified_date"],
    },
    "market_stats": {
        "key": None,
        "columns": ["geo_type", "geo_id", "geo_name", "year", "metric", "value", "source_id", *VERIFIED, "notes"],
        "required": ["geo_type", "geo_id", "year", "metric", "value", "source_id", *VERIFIED],
        "enums": {"geo_type": ["cbsa", "state"],
                  "metric": ["population", "sponsor_businesses", "sponsor_businesses_outside_major_metros"]},
        "numbers": ["value"],
        "refs": {"source_id": "sources"},
        "dates": ["verified_date"],
    },
    # Headline sponsor deals (jersey patch, naming rights, field logo...). Context only, never scored:
    # full sponsor rosters aren't published consistently, so counts would measure publicity, not demand.
    "partners": {
        "key": "partner_id",
        "columns": ["partner_id", "school_id", "partner_name", "deal_type", "partner_scope",
                    "announced_date", "description", "source_id", *VERIFIED],
        "required": ["partner_id", "school_id", "partner_name", "deal_type", "partner_scope",
                     "source_id", *VERIFIED],
        "enums": {"deal_type": ["jersey_patch", "field_or_court_logo", "naming_rights",
                                "presenting_sponsor", "broadcast_title", "official_partner", "other"],
                  "partner_scope": ["local", "regional", "national"]},
        "refs": {"school_id": "schools", "source_id": "sources"},
        "dates": ["announced_date", "verified_date"],
    },
    "research_status": {
        "key": None,
        "columns": ["school_id", "area", "status", "last_reviewed", "notes"],
        "required": ["school_id", "area", "status"],
        "enums": {"area": ["financials", "audience", "catalysts", "rights", "contacts", "partners"],
                  "status": ["not_started", "in_progress", "complete"]},
        "refs": {"school_id": "schools"},
        "dates": ["last_reviewed"],
    },
}

# Unverified findings waiting for human review (lives in data/pending/).
FINDINGS_COLUMNS = ["finding_id", "target_table", "record_json", "source_title", "source_url",
                    "source_type", "submitted_by", "submitted_date", "status", "review_note"]

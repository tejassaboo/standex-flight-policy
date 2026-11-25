"""The handbook-specific settings the template's acceptance tests read. Every other file in tests/ is the
template's and stays identical across plugins (see TEMPLATE_GUIDE.md)."""

from pathlib import Path

import contract

ROOT = Path(__file__).resolve().parents[1]

# Ids that are published or taken: a new plugin never reuses one (MASTER_PLAN section 4, "id check").
PUBLISHED_IDS = {
    "aiib-delegation-entitlement", "ec-mission-cabin-allowance", "ftr-city-pair-fare-selection",
    "gates-vendor-flight-ranking", "njc-cabin-meal-allowance", "sfc-travel-preapproval", "uc-g28-expense-audit",
    "un-staff-air-travel-audit", "vt-airfare-policy-booking", "wa-saam-travel-versioned-audit",
    "energy-corporate-flight-booking", "pharma-distributor-flight-booking", "shipping-company-flight-booking",
    "telecommunications-flight-booking", "preference-aware-flight-booking", "llm-context-compress",
    "weather-alert", "word-check", "arxiv-source",
}

# The frozen original's SHA256SUMS, when this checkout sits beside pilot_work/ (skipped elsewhere).
FROZEN_SHA256SUMS = ROOT.parents[1] / "pilot_work" / "originals" / "standex" / "frozen" / "SHA256SUMS"

# Scenario mix by primary category (EDGE_CASES.md section 5.2; the 24-scenario row).
MIX = {"easy": 5, "boundary_twin": 6, "multi_rule": 4, "hidden_clause": 2, "distractor": 2, "refusal": 2, "flag": 3}

# Overlay minimums (EDGE_CASES.md section 5.3) for the rules this handbook has. It has no rule on several
# employees on one flight and none on overnight stops, so neither overlay is required.
OVERLAY_MINIMUMS = {
    "multi_leg": 3, "date_arithmetic": 2, "month_end": 1, "personal_travel": 1,
    "dearer_option": 2, "upgrade_not_taken": 2, "outside_air_section": 2,
}

# Words a scenario id may not contain beyond the template's universal list: this handbook's rule and role
# terms.
ID_FORBIDDEN_TERMS = {
    "spouse", "companion", "wife", "husband", "family", "holiday", "personal", "medical", "doctor", "supervisor",
    "manager", "president", "finance", "cfo", "nonstop", "direct", "connection", "connecting", "segment", "routing",
    "refundable", "flexible", "loyalty", "miles", "airline", "incentive", "reward", "savings", "premium", "coach",
    "advance", "notice", "rental", "train", "audit", "atlas", "agency", "logical", "lowest", "ticket", "total",
}

# The handbook-specific enums whose member words a scenario id may not contain either.
ID_CATEGORY_ENUMS = [contract.Passenger, contract.Purpose, contract.SignOffSubject]

# How many scenarios a degenerate agent may pass: one that always holds the right offer for approval, and
# one that always books the cheapest seat (with the right section).
MAX_PASS_ALWAYS_FLAG = 2
MAX_PASS_ALWAYS_LOWEST = 10

# Hand-built duration cases beyond the automatic both-sides tests: (rule, outbound scheduled minutes per
# flight, layovers, expected True / False / None for unclear).
DURATION_CASES = [
    ("premium-economy", [180], [], True),  # inclusive: "3 hours or more"
    ("premium-economy", [179], [], False),
    ("premium-economy", [200, 200], [60], True),  # every segment reaches the limit
    ("premium-economy", [150, 150], [60], False),  # flights add to 300 but each is under 3 hours
    ("premium-economy", [140, 245], [70], None),  # one short, one long segment: unclear
    ("business", [600], [], True),  # inclusive: "10 hours or more"
    ("business", [599], [], False),
    ("business", [590, 590], [60], False),  # never added together
    ("business", [960, 235], [90], None),
    ("business", [640, 610], [80], True),
]

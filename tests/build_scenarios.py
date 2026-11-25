"""Writes the Standex scenario JSON files (an authoring aid, not a test; the JSON files are the truth).

    uv run python tests/build_scenarios.py

Expected answers are hand-written here; tests/test_scenarios.py checks them against rules.solve.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

POLICY = (ROOT / "src/plugin/data/policy.txt").read_text(encoding="utf-8").split("\n")
OUT = ROOT / "src/plugin/data/scenarios"


def norm(text):
    return " ".join(text.split())


def keep(a, b, quote, why):
    text = norm(" ".join(POLICY[a - 1:b]))
    quote = text if quote is None else quote
    assert norm(quote) in text, (a, b, quote, text)
    return {"lines": [a, b], "sha256": hashlib.sha256(text.encode()).hexdigest(), "quote": quote, "why": why}


def aside(a, b, quote, why):
    text = norm(" ".join(POLICY[a - 1:b]))
    assert norm(quote) in text, (a, b, quote, text)
    return {"lines": [a, b], "quote": quote, "why": why}


# ----- clauses the answers rest on -----
LOWEST = keep(118, 118, "Travelers are required to accept the lowest logical airfare available.",
              "the default: the lowest logical airfare")
AGENCY = keep(111, 112, "The Company's travel agency is guided by this travel policy and will confirm the lowest "
              "airfare available on the requested itinerary based on the traveler's need.",
              "the agency confirms the lowest airfare on the requested itinerary")
OPTION = keep(112, 115, "When a significant savings can be made, alternatives for consideration will be offered. The "
              "traveler will have the option of deciding whether the alternative is acceptable or unacceptable. If the "
              "traveler declines the lowest airfare, the lost savings will be reflected on the travelers' itinerary by "
              "the travel agency.", "the traveller may decline a cheaper alternative; the lost savings are recorded")
TICKET = keep(125, 128, None, "a ticket of $7,500 or more needs a supervisor's approval before purchase")
NONREF = keep(130, 131, None, "the lower non-refundable fare, unless the plans are subject to known possible changes")
COACH = keep(136, 136, None, "coach on flights with each segment under 3 hours")
PREMIUM = keep(137, 138, None, "premium economy may be selected for a segment of 3 hours or more")
BUSINESS = keep(139, 140, None, "business class may be selected for a segment of 10 hours or more")
ROUTING = keep(141, 146, None, "the cheaper connecting routing should be selected if the listed tests are met")
DOCTOR = keep(148, 149, None, "special accommodations are documented by a doctor in writing")
CHOICE = keep(154, 155, None, "an employee's airline selection only at or below the lowest fare offered")
UPGRADES = keep(225, 226, None, "upgrades are not reimbursable")
LOYALTY = keep(240, 240, "Employees may not select an airline /rental car/hotel at a higher price",
               "no airline at a higher price (for personal points)")
INCENTIVE = keep(179, 180, None, "the incentive is for economy instead of business on a 10-hour segment")
PERSONAL = keep(47, 48, None, "no personal travel reservations on the company's accounts")
CARD = keep(737, 737, None, "the corporate card is for business expenses only")
EXCEPTION = keep(37, 40, "Exceptions to this policy can only be granted in special situations with the approval of the "
                 "appropriate Group VP of Finance or the Corporate CFO.",
                 "an exception only with the Group VP of Finance or the Corporate CFO")
COMPANION = keep(697, 703, None, "companion travel is not reimbursable, except with a business purpose and advance "
                 "approval by the group president or CFO")
FAMILY = keep(874, 874, "Family expenses on business trips", "family expenses are not reimbursable")
CONCERNS = keep(935, 937, None, "concerns about the policy as written go to the immediate supervisor/manager")

# ----- nearby clauses that must not change the answer -----
RENTAL = aside(301, 305, "Rental cars must not be rented for more than 30 calendar days.",
               "a 30-day limit and its approvers for rental cars, not for the flight")
NOTICE = aside(186, 189, "If an employee becomes aware of travel with less than 14 days ' notification, supervisor "
               "approval will be required.", "the short-notice approval of the savings incentive concerns the reward")
ADVANCE = aside(118, 119, "flights should be booked 14-21 days in advance when possible",
                "booking 14-21 days ahead is 'when possible', not a ban")
TRAIN = aside(574, 575, "First class train travel is only permissible if the cost is less than the cost of a standard "
              "coach flight fare.", "a rail rule that names a coach fare; it does not set the flight cabin")
EARLY = aside(151, 152, "Early boarding fees are strongly discouraged", "a fee rule, not a fare rule")
INTERNET = aside(230, 231, "Inflight internet fees are strongly discouraged",
                 "a fee rule for flights, not for the cabin")
LUGGAGE = aside(219, 222, "The Company will reimburse employees for one checked piece of luggage.",
                "a baggage rule, not a fare rule")
INTERNATIONAL = aside(160, 161, "It is extremely important for employees who are traveling internationally to notify "
                      "Atlas in advance", "an international notice, not a cabin rule")
ARRIVE = aside(903, 904, "Plan to arrive at the airport at least one (1) hour before scheduled flight for domestic "
               "travel and two (2) hours for international flights.", "a safety tip with hours, not a routing test")
REWARD = aside(191, 193, "This incentive is equal to 50% of the difference between the roundtrip economy or premium "
               "economy fare and lowest roundtrip business class fare.", "how the reward is paid, not what is bought")

# ----- builders -----


def trip(**fields):
    base = {
        "traveller_name": "", "traveller_title": "", "passenger": "EMPLOYEE", "accompanies": "", "origin": "",
        "destination": "", "travel_date": "", "booking_date": "", "requested_departure": "", "purpose": "",
        "purpose_kind": "CUSTOMER_VISIT", "requested_cabin": "ECONOMY", "wants_nonstop": False, "chosen_airline": "",
        "wants_refundable": False, "dates_may_move": False, "doctor_note_on_file": False, "sign_offs": [],
        "car_rental_days": 0,
    }
    unknown = set(fields) - set(base)
    assert not unknown, unknown
    base.update(fields)
    return base


def sign(role, name, subject):
    return {"role": role, "name": name, "subject": subject}


def offer(slot, flight, cabin, cents, seats=True, refundable=False):
    data = {"slot": slot, "flight": flight, "cabin": cabin, "fare_cents": cents}
    if not seats:
        data["seats"] = False
    if refundable:
        data["refundable"] = True
    return data


def expected(decision, slots, cabins, reasons, approvers, clauses, phrase=""):
    return {"decision": decision, "offer_slots": slots, "cabins": cabins, "reason_codes": reasons,
            "approvers": approvers, "clauses": clauses, "unclear_phrase": phrase}


def search(origin, destination, date, flights, offers, background=0):
    # Background offers only on the scenario's own search, and only where no background routing could change the
    # answer (handbook.json background_offers is 0, so a search the scenario does not pin lists nothing).
    return {"name": "main", "origin": origin, "destination": destination, "date": date, "return_date": "",
            "background": background, "flights": flights, "offers": offers}


S = []


def scenario(id, category, overlays, request, trip_, search_spec, exp, must_keep, notes, twin_of="", twin_fact="",
             flag_twins=(), ambiguity="none", distractors=()):
    S.append({
        "id": id, "category": category, "overlays": list(overlays), "twin_of": twin_of, "twin_fact": twin_fact,
        "flag_twins": list(flag_twins), "ambiguity_note": ambiguity, "request": request, "trip": trip_,
        "world": {"searches": [search_spec]}, "expected": exp, "must_keep": list(must_keep),
        "distractors": list(distractors), "design_notes": notes,
    })


LOW_CLAUSES = ["AIRLINE_TRAVEL", "TRAVEL_MANAGEMENT"]
NOT_ELIGIBLE = ["LOWEST_FARE", "UPGRADE_NOT_ELIGIBLE"]
BUSINESS_NOT_MET = ["LONG_FLIGHT_CONDITION_NOT_MET", "LOWEST_FARE", "UPGRADE_NOT_ELIGIBLE"]
LONG_OK = ["INTERNATIONAL_LONG_FLIGHT", "LONG_FLIGHT_APPROVED"]
UNCLEAR_ROLES = ["CHIEF_FINANCIAL_OFFICER", "GROUP_VP_FINANCE", "MANAGER", "NOT_NAMED", "SUPERVISOR"]

# ===== easy (5) =====

scenario(
    "alder-quince", "easy", [],
    "I need to get from Boston to Chicago on December 15th for the dealer meeting. Economy, whatever is cheapest.",
    trip(traveller_name="Dana Whitcomb", traveller_title="Regional Sales Manager", origin="BOS", destination="ORD",
         travel_date="2026-12-15", booking_date="2026-11-30", purpose="Dealer meeting in Chicago"),
    search("BOS", "ORD", "2026-12-15", {
        "early": {"carrier": "AA", "depart": "07:00"},
        "mid": {"carrier": "UA", "depart": "09:30"},
        "noon": {"carrier": "AA", "depart": "13:15"},
        "late": {"carrier": "DL", "depart": "17:00"},
    }, [
        offer("early-economy", "early", "ECONOMY", 21400, seats=False),
        offer("mid-economy", "mid", "ECONOMY", 23800),
        offer("noon-economy", "noon", "ECONOMY", 25900),
        offer("late-economy", "late", "ECONOMY", 31500, refundable=True),
    ], background=3),
    expected("BOOK", ["mid-economy"], ["ECONOMY"], ["LOWEST_FARE"], ["NONE"], LOW_CLAUSES),
    [LOWEST, AGENCY, COACH],
    "A 130-minute domestic flight in economy at the lowest logical airfare (line 118). The cheaper 07:00 fare is sold "
    "out; the refundable fare is dearer anyway.")

scenario(
    "birch-tallow", "easy", ["multi_leg", "dearer_option"],
    "Boston to Honolulu on January 19th for the foodservice equipment expo. It's a long day of flying, so I'd like "
    "premium economy, connections are fine.",
    trip(traveller_name="Priya Raman", traveller_title="Product Line Manager", origin="BOS", destination="HNL",
         travel_date="2027-01-19", booking_date="2026-12-29", purpose="Foodservice equipment expo in Honolulu",
         purpose_kind="CONFERENCE", requested_cabin="PREMIUM_ECONOMY"),
    search("BOS", "HNL", "2027-01-19", {
        "losangeles": {"carrier": "DL", "via": ["LAX"], "depart": "07:30", "minutes": [365, 340], "layovers": [75]},
        "seattle": {"carrier": "AS", "via": ["SEA"], "depart": "08:45", "minutes": [380, 365], "layovers": [65]},
    }, [
        offer("losangeles-economy", "losangeles", "ECONOMY", 48900),
        offer("losangeles-premium", "losangeles", "PREMIUM_ECONOMY", 79800),
        offer("seattle-economy", "seattle", "ECONOMY", 45600),
        offer("seattle-premium", "seattle", "PREMIUM_ECONOMY", 83500),
    ]),
    expected("BOOK", ["losangeles-premium"], ["PREMIUM_ECONOMY"], ["PREMIUM_ECONOMY_ALLOWED"], ["NONE"],
             ["AIRLINE_TRAVEL"]),
    [PREMIUM, COACH, LOWEST],
    "Both itineraries connect, and every flight of each is 3 hours or more (365 and 340, 380 and 365 minutes), so "
    "premium economy may be selected on every reading of lines 137-138: the cheapest premium economy fare. The "
    "Seattle economy fare is cheaper but the traveller asked for premium economy, which is permitted.")

scenario(
    "cinder-moth", "easy", ["dearer_option"],
    "Please book me business class from New York JFK to Hong Kong on February 8th for the plant audit in Shenzhen.",
    trip(traveller_name="Marcus Feld", traveller_title="Director of Operations Engineering", origin="JFK",
         destination="HKG", travel_date="2027-02-08", booking_date="2027-01-11",
         purpose="Supplier plant audit in Shenzhen", purpose_kind="PROJECT_WORK", requested_cabin="BUSINESS"),
    search("JFK", "HKG", "2027-02-08", {
        "cathay": {"carrier": "CX", "depart": "01:15", "minutes": [955]},
        "american": {"carrier": "AA", "depart": "11:20", "minutes": [965]},
    }, [
        offer("cathay-economy", "cathay", "ECONOMY", 118000),
        offer("cathay-business", "cathay", "BUSINESS", 624000),
        offer("american-economy", "american", "ECONOMY", 121500),
        offer("american-business", "american", "BUSINESS", 655000),
    ]),
    expected("BOOK", ["cathay-business"], ["BUSINESS"], LONG_OK, ["NONE"], ["AIRLINE_TRAVEL"]),
    [BUSINESS, LOWEST, TICKET],
    "A 955-minute nonstop: a segment of 10 hours or more, so business class may be selected (lines 139-140). The "
    "cheapest business fare is $6,240, under $7,500, so no supervisor approval is needed (lines 125-128).")

scenario(
    "dahlia-quarry", "easy", ["upgrade_not_taken"],
    "Boston to London Heathrow on the 3rd of February for the distributor review. Economy is fine, cheapest one "
    "please.",
    trip(traveller_name="Owen Castellano", traveller_title="International Sales Engineer", origin="BOS",
         destination="LHR", travel_date="2027-02-03", booking_date="2027-01-12", purpose="Distributor review in London"),
    search("BOS", "LHR", "2027-02-03", {
        "british": {"carrier": "BA", "depart": "18:30", "minutes": [410]},
        "virgin": {"carrier": "VS", "depart": "19:45", "minutes": [405]},
    }, [
        offer("british-economy", "british", "ECONOMY", 61200),
        offer("british-premium", "british", "PREMIUM_ECONOMY", 118400),
        offer("virgin-economy", "virgin", "ECONOMY", 64800),
        offer("virgin-premium", "virgin", "PREMIUM_ECONOMY", 121000),
    ], background=2),
    expected("BOOK", ["british-economy"], ["ECONOMY"], ["LOWEST_FARE"], ["NONE"], LOW_CLAUSES),
    [LOWEST, AGENCY, PREMIUM],
    "A 410-minute flight would allow premium economy (lines 137-138), but the employee 'may' select it and asks for "
    "the cheapest economy: the lowest logical airfare (line 118).",
    distractors=[INTERNATIONAL])

scenario(
    "elm-vesper", "easy", ["multi_leg"],
    "Boston to Austin on December 9th for the customer install. Any time of day, and I'm happy to connect if it's "
    "cheaper.",
    trip(traveller_name="Leah Brandt", traveller_title="Field Service Technician", origin="BOS", destination="AUS",
         travel_date="2026-12-09", booking_date="2026-11-23", purpose="Customer installation in Austin",
         purpose_kind="PROJECT_WORK"),
    search("BOS", "AUS", "2026-12-09", {
        "dallas": {"carrier": "AA", "via": ["DFW"], "depart": "06:30", "layovers": [70]},
        "atlanta": {"carrier": "DL", "via": ["ATL"], "depart": "08:10", "layovers": [85]},
        "nonstop": {"carrier": "B6", "depart": "10:00"},
    }, [
        offer("dallas-economy", "dallas", "ECONOMY", 27900),
        offer("atlanta-economy", "atlanta", "ECONOMY", 30400),
        offer("nonstop-economy", "nonstop", "ECONOMY", 33800),
    ], background=2),
    expected("BOOK", ["dallas-economy"], ["ECONOMY"], ["LOWEST_FARE"], ["NONE"], LOW_CLAUSES),
    [LOWEST, AGENCY, COACH],
    "No requested time and no wish for a nonstop: the lowest logical airfare is the Dallas connection (line 118); "
    "the traveller asks for nothing above economy, so the 210-minute first flight changes nothing (premium economy is "
    "a choice the employee 'may' make, lines 137-138). Under every reading of the routing tests (lines 141-146) a "
    "traveller who wants the cheaper connection may take it.")

# ===== boundary twins (6) =====

MIAMI = {
    "american": {"carrier": "AA", "depart": "08:20"},
    "delta": {"carrier": "DL", "depart": "11:05"},
}
MIAMI_OFFERS = [
    offer("american-economy", "american", "ECONOMY", 24600),
    offer("american-premium", "american", "PREMIUM_ECONOMY", 39800),
    offer("delta-economy", "delta", "ECONOMY", 25900),
    offer("delta-premium", "delta", "PREMIUM_ECONOMY", 41200),
]
MIAMI_REQUEST = ("Boston to Miami on January 26th for the regional distributor meeting. I'd like premium economy "
                 "if I'm allowed it on this flight; otherwise regular economy.")


def miami(minutes):
    return {name: {**spec, "minutes": [minutes]} for name, spec in MIAMI.items()}


scenario(
    "fern-cobble", "boundary_twin", ["dearer_option"], MIAMI_REQUEST,
    trip(traveller_name="Hannah Okafor", traveller_title="Channel Marketing Manager", origin="BOS", destination="MIA",
         travel_date="2027-01-26", booking_date="2027-01-04", purpose="Regional distributor meeting in Miami",
         requested_cabin="PREMIUM_ECONOMY"),
    search("BOS", "MIA", "2027-01-26", miami(180), MIAMI_OFFERS),
    expected("BOOK", ["american-premium"], ["PREMIUM_ECONOMY"], ["PREMIUM_ECONOMY_ALLOWED"], ["NONE"],
             ["AIRLINE_TRAVEL"]),
    [PREMIUM, COACH],
    "Both nonstops are scheduled at exactly 180 minutes: '3 hours or more' is inclusive, so premium economy may be "
    "selected (lines 137-138): the cheapest premium economy fare.",
    twin_of="gorse-lumen", twin_fact="nonstops scheduled at 180 or 179 minutes")

scenario(
    "gorse-lumen", "boundary_twin", [], MIAMI_REQUEST,
    trip(traveller_name="Hannah Okafor", traveller_title="Channel Marketing Manager", origin="BOS", destination="MIA",
         travel_date="2027-01-26", booking_date="2027-01-04", purpose="Regional distributor meeting in Miami",
         requested_cabin="PREMIUM_ECONOMY"),
    search("BOS", "MIA", "2027-01-26", miami(179), MIAMI_OFFERS),
    expected("BOOK", ["american-economy"], ["ECONOMY"], NOT_ELIGIBLE, ["NONE"], ["AIR_UPGRADES", "AIRLINE_TRAVEL"]),
    [COACH, PREMIUM, LOWEST],
    "Both nonstops are scheduled at 179 minutes, under 3 hours: coach (line 136), so premium economy is not "
    "available and the traveller falls back to economy as asked: the lowest logical airfare (line 118).",
    twin_of="fern-cobble", twin_fact="nonstops scheduled at 179 or 180 minutes")

SEOUL = {
    "united": {"carrier": "UA", "depart": "11:10"},
    "korean": {"carrier": "KE", "depart": "13:40"},
}
SEOUL_OFFERS = [
    offer("united-economy", "united", "ECONOMY", 98500),
    offer("united-premium", "united", "PREMIUM_ECONOMY", 172000),
    offer("united-business", "united", "BUSINESS", 512000),
    offer("korean-economy", "korean", "ECONOMY", 94200),
    offer("korean-premium", "korean", "PREMIUM_ECONOMY", 168000),
    offer("korean-business", "korean", "BUSINESS", 488000),
]
SEOUL_REQUEST = ("Please book business class from San Francisco to Seoul on March 2nd for the customer summit. If "
                 "the policy doesn't allow business on this flight, just put me in plain economy, nothing in between.")


def seoul(minutes):
    return {name: {**spec, "minutes": [minutes]} for name, spec in SEOUL.items()}


SEOUL_TRIP = {"traveller_name": "Kenji Morales", "traveller_title": "Key Account Director", "origin": "SFO",
                  "destination": "ICN", "travel_date": "2027-03-02", "booking_date": "2027-02-08",
                  "purpose": "Customer summit in Seoul", "purpose_kind": "CONFERENCE", "requested_cabin": "BUSINESS"}

scenario(
    "hemlock-tide", "boundary_twin", ["dearer_option"], SEOUL_REQUEST, trip(**SEOUL_TRIP),
    search("SFO", "ICN", "2027-03-02", seoul(600), SEOUL_OFFERS),
    expected("BOOK", ["korean-business"], ["BUSINESS"], LONG_OK, ["NONE"], ["AIRLINE_TRAVEL"]),
    [BUSINESS, LOWEST],
    "Both nonstops are scheduled at exactly 600 minutes: '10 hours or more' is inclusive, so business class may be "
    "selected (lines 139-140): the cheapest business fare, $4,880, under the $7,500 approval line.",
    twin_of="ivy-sorrel", twin_fact="nonstops scheduled at 600 or 599 minutes")

scenario(
    "ivy-sorrel", "boundary_twin", ["upgrade_not_taken"], SEOUL_REQUEST, trip(**SEOUL_TRIP),
    search("SFO", "ICN", "2027-03-02", seoul(599), SEOUL_OFFERS),
    expected("BOOK", ["korean-economy"], ["ECONOMY"], BUSINESS_NOT_MET, ["NONE"], ["AIR_UPGRADES", "AIRLINE_TRAVEL"]),
    [BUSINESS, PREMIUM, LOWEST, UPGRADES],
    "Both nonstops are scheduled at 599 minutes, under 10 hours, so business class is not available (lines 139-140). "
    "Premium economy would be allowed (lines 137-138), but the traveller asked for plain economy otherwise: the lowest "
    "logical airfare (line 118).",
    twin_of="hemlock-tide", twin_fact="nonstops scheduled at 599 or 600 minutes")

ATLANTA_REQUEST = ("Boston to Atlanta on January 14th for the supplier visit. Please put me on Delta, I collect their "
                   "miles.")
ATLANTA_TRIP = {"traveller_name": "Rita Szabo", "traveller_title": "Purchasing Manager", "origin": "BOS", "destination": "ATL",
                    "travel_date": "2027-01-14", "booking_date": "2026-12-21", "purpose": "Supplier visit in Atlanta",
                    "chosen_airline": "Delta Air Lines"}


def atlanta(delta_cents):
    return search("BOS", "ATL", "2027-01-14", {
        "jetblue": {"carrier": "B6", "depart": "07:15"},
        "delta": {"carrier": "DL", "depart": "08:00"},
        "later": {"carrier": "DL", "depart": "12:30"},
    }, [
        offer("jetblue-economy", "jetblue", "ECONOMY", 22800),
        offer("delta-economy", "delta", "ECONOMY", delta_cents),
        offer("later-economy", "later", "ECONOMY", 26400),
    ])


scenario(
    "juniper-flint", "boundary_twin", [], ATLANTA_REQUEST, trip(**ATLANTA_TRIP), atlanta(22800),
    expected("BOOK", ["delta-economy"], ["ECONOMY"],
             ["CHOSEN_AIRLINE_AT_LOWEST_FARE", "LOWEST_FARE", "LOYALTY_PROGRAM_PREFERENCE"], ["NONE"],
             ["AIRLINE_TRAVEL", "LOYALTY_PROGRAMS"]),
    [CHOICE, LOYALTY, LOWEST],
    "Delta's 08:00 fare equals the lowest fare offered ($228.00, tied with JetBlue): selection is permitted when the "
    "cost is 'at or below' the lowest fare (lines 154-155), so book the airline the traveller chose. The JetBlue fare "
    "is not accepted: it is no cheaper and is not the traveller's permitted choice.",
    twin_of="kiln-meadow", twin_fact="Delta's fare equal to or $1 above the lowest")

scenario(
    "kiln-meadow", "boundary_twin", [], ATLANTA_REQUEST, trip(**ATLANTA_TRIP), atlanta(22900),
    expected("BOOK", ["jetblue-economy"], ["ECONOMY"], ["LOWEST_FARE", "LOYALTY_PROGRAM_PREFERENCE"], ["NONE"],
             ["AIRLINE_TRAVEL", "LOYALTY_PROGRAMS", "TRAVEL_MANAGEMENT"]),
    [CHOICE, LOYALTY, LOWEST],
    "Delta's cheapest fare is $229.00, $1 above JetBlue's $228.00: airline selection is not permitted unless the cost "
    "is at or below the lowest fare offered (lines 154-155), and no airline at a higher price for points (line 240). "
    "A $1 difference is no 'significant savings' alternative (lines 112-115). Book JetBlue.",
    twin_of="juniper-flint", twin_fact="Delta's fare $1 above or equal to the lowest")

# ===== multi-rule (4) =====

scenario(
    "larch-pewter", "multi_rule", ["dearer_option", "approval_required"],
    "New York JFK to Singapore on March 15th for the Asia-Pacific engineering review, business class please. My "
    "supervisor already signed the printed itinerary for the business fare.",
    trip(traveller_name="Elena Voss", traveller_title="Vice President, Engineered Products", origin="JFK",
         destination="SIN", travel_date="2027-03-15", booking_date="2027-02-17",
         purpose="Asia-Pacific engineering review in Singapore", purpose_kind="INTERNAL_MEETING",
         requested_cabin="BUSINESS", sign_offs=[sign("SUPERVISOR", "Tom Reilly", "TICKET_PURCHASE")]),
    search("JFK", "SIN", "2027-03-15", {
        "singapore": {"carrier": "SQ", "depart": "10:30", "minutes": [1110]},
    }, [
        offer("singapore-economy", "singapore", "ECONOMY", 142000),
        offer("singapore-premium", "singapore", "PREMIUM_ECONOMY", 248000),
        offer("singapore-business", "singapore", "BUSINESS", 812000),
    ]),
    expected("BOOK", ["singapore-business"], ["BUSINESS"], [*LONG_OK, "TICKET_TOTAL_APPROVED"], ["NONE", "SUPERVISOR"],
             ["AIRLINE_TRAVEL"]),
    [BUSINESS, TICKET, LOWEST],
    "A 1,110-minute nonstop allows business (lines 139-140). The business ticket is $8,120, $7,500 or greater, so it "
    "needs a supervisor approval before purchase (lines 125-128); the supervisor's sign-off on the printed itinerary "
    "is on file, so book it. The approver is the supervisor whose sign-off is on file, or NONE (SYNC_NOTES 4': a sign-off already on file reads both ways).")

SFO_FLIGHTS = {
    "nonstop": {"carrier": "UA", "depart": "08:00", "minutes": [395]},
    "detroit": {"carrier": "DL", "via": ["DTW"], "depart": "07:15", "minutes": [130, 290], "layovers": [60]},
    "chicago": {"carrier": "AA", "via": ["ORD"], "depart": "11:00", "minutes": [165, 275], "layovers": [95]},
}
SFO_OFFERS = [
    offer("nonstop-economy", "nonstop", "ECONOMY", 61800),
    offer("detroit-economy", "detroit", "ECONOMY", 36900),
    offer("chicago-economy", "chicago", "ECONOMY", 52800),
]
SFO_TRIP = {"traveller_name": "Graham Pike", "traveller_title": "Applications Engineer", "origin": "BOS",
                "destination": "SFO", "travel_date": "2027-02-09", "booking_date": "2027-01-19", "requested_departure": "08:00",
                "purpose": "Customer design review in San Francisco"}

scenario(
    "maple-onyx", "multi_rule", ["multi_leg"],
    "Boston to San Francisco on February 9th for the design review. I'd like to leave around 8 in the morning; "
    "nonstop or a connection, whatever the policy calls for.",
    trip(**SFO_TRIP),
    search("BOS", "SFO", "2027-02-09", SFO_FLIGHTS, SFO_OFFERS),
    expected("BOOK", ["detroit-economy"], ["ECONOMY"], ["ALTERNATE_ROUTE_TOO_EXPENSIVE", "COST_SAVINGS", "LOWEST_FARE"],
             ["NONE"], LOW_CLAUSES),
    [ROUTING, LOWEST, AGENCY],
    "The 08:00 nonstop is $618.00 (395 minutes). The Detroit connection leaves at 07:15 and lands 40 minutes after "
    "the nonstop, takes 480 minutes (85 more) and saves $249.00: it passes all three tests of lines 141-146, so on "
    "every reading of the list's '; or' the less expensive routing is selected, and it is the lowest logical airfare "
    "(line 118). The Chicago connection fails all three tests and is dearer. The traveller does not decline the "
    "alternative, so lines 113-115 change nothing.")

scenario(
    "nettle-brine", "multi_rule", ["multi_leg", "dearer_option"],
    "Boston to Seattle on December 10th for the customer training. I want the 9 a.m. nonstop; please don't put me on "
    "a connection.",
    trip(traveller_name="Joyce Amari", traveller_title="Technical Trainer", origin="BOS", destination="SEA",
         travel_date="2026-12-10", booking_date="2026-11-23", requested_departure="09:00",
         purpose="Customer operator training in Seattle", purpose_kind="TRAINING", wants_nonstop=True),
    search("BOS", "SEA", "2026-12-10", {
        "alaska": {"carrier": "AS", "depart": "09:00", "minutes": [385]},
        "minneapolis": {"carrier": "DL", "via": ["MSP"], "depart": "13:10", "minutes": [165, 225], "layovers": [130]},
        "delta": {"carrier": "DL", "depart": "11:30", "minutes": [390]},
    }, [
        offer("alaska-economy", "alaska", "ECONOMY", 48200),
        offer("minneapolis-economy", "minneapolis", "ECONOMY", 42200),
        offer("delta-economy", "delta", "ECONOMY", 51400),
    ]),
    expected("BOOK", ["alaska-economy"], ["ECONOMY"],
             ["ALTERNATE_ROUTE_WITHIN_MARGIN", "CONNECTION_TOO_LONG", "LOWEST_FARE"], ["NONE"], LOW_CLAUSES),
    [ROUTING, LOWEST, OPTION],
    "The Minneapolis connection saves only $60.00 (under $200 even doubled for a round trip), takes 520 minutes "
    "against 385 (135 more) and leaves 4 h 10 min after the requested 09:00 and lands 6 h 25 min after the nonstop: "
    "it fails all three tests of lines 141-146, so on every reading it is not the lowest logical airfare, and the "
    "traveller declines it anyway (lines 113-115). Book the cheapest nonstop, Alaska at 09:00; Delta's nonstop is "
    "dearer.")

scenario(
    "ochre-pinion", "multi_rule", ["dearer_option"],
    "Boston to Washington National on January 21st for the customer audit. The customer still hasn't confirmed the "
    "audit date and may push it a few days, so please book a fare I can change without a penalty.",
    trip(traveller_name="Victor Nwosu", traveller_title="Quality Assurance Manager", origin="BOS", destination="DCA",
         travel_date="2027-01-21", booking_date="2026-12-30", purpose="Customer quality audit in Washington",
         wants_refundable=True, dates_may_move=True),
    search("BOS", "DCA", "2027-01-21", {
        "american": {"carrier": "AA", "depart": "07:00"},
        "delta": {"carrier": "DL", "depart": "09:30"},
    }, [
        offer("american-saver", "american", "ECONOMY", 18900),
        offer("american-flex", "american", "ECONOMY", 32400, refundable=True),
        offer("delta-saver", "delta", "ECONOMY", 19800),
        offer("delta-flex", "delta", "ECONOMY", 34800, refundable=True),
    ]),
    expected("BOOK", ["american-flex"], ["ECONOMY"], ["FLEXIBLE_FARE_JUSTIFIED", "LOWEST_FARE"], ["NONE"],
             ["AIRLINE_TRAVEL"]),
    [NONREF, LOWEST, COACH],
    "Lines 130-131: the lower non-refundable fare is used 'unless their travel plans are subject to known possible "
    "changes'. The audit date is unconfirmed and may move, so the refundable fare the traveller asks for is "
    "permitted: the cheapest refundable economy fare (line 118 for the cheapest of that kind).")

# ===== hidden clause (2) =====

scenario(
    "oak-saffron", "hidden_clause", ["outside_air_section"],
    "Please book my wife, Claire, from Boston to Orlando on February 24th. She's co-hosting the customers' spouses "
    "program at our dealer awards dinner, and Ruth Calder approved it last month.",
    trip(traveller_name="Claire Dumont", traveller_title="Spouse of Paul Dumont, Group Sales Director",
         passenger="SPOUSE_OR_COMPANION", accompanies="Paul Dumont", origin="BOS", destination="MCO",
         travel_date="2027-02-24", booking_date="2027-01-27",
         purpose="Co-hosting the customers' spouses program at the dealer awards dinner", purpose_kind="CLIENT_EVENT",
         sign_offs=[sign("GROUP_PRESIDENT", "Ruth Calder", "COMPANION_TRAVEL")]),
    search("BOS", "MCO", "2027-02-24", {
        "jetblue": {"carrier": "B6", "depart": "07:40"},
        "delta": {"carrier": "DL", "depart": "10:15"},
        "southwest": {"carrier": "WN", "depart": "12:30"},
    }, [
        offer("jetblue-economy", "jetblue", "ECONOMY", 19800),
        offer("delta-economy", "delta", "ECONOMY", 21600),
        offer("southwest-economy", "southwest", "ECONOMY", 18900, seats=False),
    ]),
    expected("BOOK", ["jetblue-economy"], ["ECONOMY"], ["COMPANION_TRAVEL_AUTHORIZED", "LOWEST_FARE"],
             ["GROUP_PRESIDENT", "NONE"], ["AIRLINE_TRAVEL", "SPOUSE_COMPANION"]),
    [COMPANION, LOWEST],
    "Lines 697-703 (Spouse/Companion Travel, far from the air section): a spouse's transportation is reimbursed when "
    "there is a specific business purpose and the trip is approved in advance by the appropriate group president. "
    "Both hold, so book the lowest logical airfare (line 118); the cheaper Southwest fare is sold out.")

scenario(
    "poplar-wick", "hidden_clause", ["outside_air_section", "dearer_option"],
    "Boston to Paris on March 4th for the Lyon plant startup. My doctor's note about my back surgery is on file, and "
    "Martin Ruiz, our Group VP of Finance, approved business class as an exception. Please book business.",
    trip(traveller_name="Sofia Lindqvist", traveller_title="Senior Process Engineer", origin="BOS", destination="CDG",
         travel_date="2027-03-04", booking_date="2027-02-10", purpose="Plant startup support near Lyon",
         purpose_kind="PROJECT_WORK", requested_cabin="BUSINESS", doctor_note_on_file=True,
         sign_offs=[sign("GROUP_VP_FINANCE", "Martin Ruiz", "POLICY_EXCEPTION")]),
    search("BOS", "CDG", "2027-03-04", {
        "airfrance": {"carrier": "AF", "depart": "18:10", "minutes": [415]},
        "delta": {"carrier": "DL", "depart": "19:25", "minutes": [420]},
    }, [
        offer("airfrance-economy", "airfrance", "ECONOMY", 68400),
        offer("airfrance-premium", "airfrance", "PREMIUM_ECONOMY", 122000),
        offer("airfrance-business", "airfrance", "BUSINESS", 398000),
        offer("delta-economy", "delta", "ECONOMY", 70100),
        offer("delta-business", "delta", "BUSINESS", 415000),
    ]),
    expected("BOOK", ["airfrance-business"], ["BUSINESS"], ["MEDICAL_NEED", "POLICY_EXCEPTION_APPROVED"],
             ["GROUP_VP_FINANCE", "NONE"], ["AIRLINE_TRAVEL", "EXCEPTIONS", "POLICY_PRINCIPLES"]),
    [EXCEPTION, DOCTOR, BUSINESS, PREMIUM],
    "A 415-minute flight allows premium economy, not business (lines 137-140). Lines 37-40 (Policy Principles): "
    "exceptions can only be granted in special situations with the approval of the Group VP of Finance or the "
    "Corporate CFO; the Group VP of Finance granted one, and the doctor's written documentation is on file (lines "
    "148-149). Book the cheapest business fare; approver the Group VP of Finance (on file) or NONE (SYNC_NOTES 4').",
    distractors=[CONCERNS])

# ===== distractor (2) =====

scenario(
    "sage-tundra", "distractor", ["date_arithmetic", "upgrade_not_taken"],
    "Boston to Tokyo Haneda on January 14th, the customer moved the kickoff up so it's short notice. I could fly "
    "business on this one, but put me in economy instead; I'd like the savings reward. My supervisor already "
    "confirmed the short notice.",
    trip(traveller_name="Daniel Ochoa", traveller_title="Business Development Manager", origin="BOS",
         destination="HND", travel_date="2027-01-14", booking_date="2027-01-05", purpose="Customer project kickoff in Tokyo",
         sign_offs=[sign("SUPERVISOR", "Alicia Grant", "SHORT_NOTICE")]),
    search("BOS", "HND", "2027-01-14", {
        "japan": {"carrier": "JL", "depart": "11:45", "minutes": [810]},
        "ana": {"carrier": "NH", "depart": "13:20", "minutes": [815]},
    }, [
        offer("japan-economy", "japan", "ECONOMY", 112000),
        offer("japan-business", "japan", "BUSINESS", 648000),
        offer("ana-economy", "ana", "ECONOMY", 108500),
        offer("ana-business", "ana", "BUSINESS", 671000),
    ]),
    expected("BOOK", ["ana-economy"], ["ECONOMY"], ["COST_SAVINGS", "LOWEST_FARE"], ["NONE", "SUPERVISOR"],
             ["AIRLINE_TRAVEL", "TRAVEL_MANAGEMENT", "TRAVEL_SAVINGS_INCENTIVE"]),
    [LOWEST, BUSINESS, INCENTIVE],
    "An 815-minute flight allows business (lines 139-140), but the employee 'may' select it and chooses economy: the "
    "lowest logical airfare (line 118), which is what the savings incentive rewards (lines 179-180). Booked 9 days "
    "ahead: the 14-day and supervisor conditions of lines 186-189 decide whether the reward is paid, not whether the "
    "ticket is bought, and line 119's 14-21 days applies 'when possible'. The supervisor's short-notice note is on file "
    "but the booking does not rely on it: NONE or SUPERVISOR.",
    distractors=[NOTICE, ADVANCE, REWARD])

scenario(
    "thistle-amber", "distractor", ["date_arithmetic", "month_end", "upgrade_not_taken"],
    "I start a five-week commissioning job in Denver; I need to fly out of Boston on December 3rd and I'll rent a car "
    "there for the whole 35 days. Cheapest economy seat is fine.",
    trip(traveller_name="Brian Kowalski", traveller_title="Commissioning Engineer", origin="BOS", destination="DEN",
         travel_date="2026-12-03", booking_date="2026-11-24", purpose="Five-week equipment commissioning in Denver",
         purpose_kind="PROJECT_WORK", car_rental_days=35),
    search("BOS", "DEN", "2026-12-03", {
        "united": {"carrier": "UA", "depart": "07:10", "minutes": [235]},
        "southwest": {"carrier": "WN", "depart": "09:20", "minutes": [240]},
        "delta": {"carrier": "DL", "depart": "12:00", "minutes": [235]},
    }, [
        offer("united-economy", "united", "ECONOMY", 28700),
        offer("united-premium", "united", "PREMIUM_ECONOMY", 51800),
        offer("southwest-economy", "southwest", "ECONOMY", 26900),
        offer("delta-economy", "delta", "ECONOMY", 30200),
    ], background=2),
    expected("BOOK", ["southwest-economy"], ["ECONOMY"], ["LOWEST_FARE"], ["NONE"], LOW_CLAUSES),
    [LOWEST, AGENCY, PREMIUM],
    "The 35-day rental needs prior approval under the rental-car rule (lines 301-305), but that is about the car, not "
    "the flight. Booked 9 days ahead across the month end (November 24 to December 3): line 119's 14-21 days applies "
    "'when possible'. Premium economy would be allowed on these 235-240-minute flights, but the traveller asks for "
    "the cheapest economy: the lowest logical airfare (line 118).",
    distractors=[RENTAL, ADVANCE, TRAIN])

# ===== refusal (2) =====

scenario(
    "quince-ember", "refusal", ["personal_travel", "outside_air_section"],
    "Could you book me Boston to Orlando on December 19th? It's our family holiday trip to the parks. Put it on the "
    "company account and I'll pay it back from my next paycheck.",
    trip(traveller_name="Megan Holt", traveller_title="Payroll Specialist", origin="BOS", destination="MCO",
         travel_date="2026-12-19", booking_date="2026-11-25", purpose="Family holiday at the theme parks",
         purpose_kind="PERSONAL"),
    search("BOS", "MCO", "2026-12-19", {
        "jetblue": {"carrier": "B6", "depart": "08:05"},
        "delta": {"carrier": "DL", "depart": "10:40"},
    }, [
        offer("jetblue-economy", "jetblue", "ECONOMY", 21200),
        offer("delta-economy", "delta", "ECONOMY", 23400),
    ], background=2),
    expected("REFUSE", [], ["NONE"], ["OUTSIDE_POLICY_SCOPE", "PERSONAL_TRAVEL_NOT_COVERED"], ["NONE"],
             ["AUTHORIZED_USAGE", "CORPORATE_CREDIT_CARD", "POLICY_PRINCIPLES"]),
    [PERSONAL, CARD],
    "Lines 47-48 (Policy Principles): employees are not permitted to use the company's credit card accounts to make "
    "personal travel reservations; line 737: the corporate card is for business expenses only. Repaying later does not "
    "change that. Flights exist, so the refusal is not 'no compliant offer'.")

scenario(
    "rowan-slate", "refusal", ["outside_air_section"],
    "My husband Ben would like to come with me to the trade show in Las Vegas on March 9th and see the sights while "
    "I'm working the booth. Can you book his flight from Boston too?",
    trip(traveller_name="Ben Alvarez", traveller_title="Spouse of Nora Alvarez, Marketing Communications Manager",
         passenger="SPOUSE_OR_COMPANION", accompanies="Nora Alvarez", origin="BOS", destination="LAS",
         travel_date="2027-03-09", booking_date="2027-02-09", purpose="Sightseeing while his wife works the trade show",
         purpose_kind="PERSONAL"),
    search("BOS", "LAS", "2027-03-09", {
        "jetblue": {"carrier": "B6", "depart": "08:30"},
        "southwest": {"carrier": "WN", "depart": "10:50", "via": ["DEN"], "layovers": [70]},
    }, [
        offer("jetblue-economy", "jetblue", "ECONOMY", 32600),
        offer("southwest-economy", "southwest", "ECONOMY", 29800),
    ], background=2),
    expected("REFUSE", [], ["NONE"], ["COMPANION_NOT_COVERED"], ["NONE"], ["NON_REIMBURSABLE", "SPOUSE_COMPANION"]),
    [COMPANION, FAMILY],
    "Lines 697-700: spouse or companion travel expenses, air included, are not reimbursable. The exception (lines "
    "700-703) needs a specific business purpose and advance approval; sightseeing is no business purpose, so the "
    "company buys no ticket (line 874: family expenses on business trips are not reimbursable).")

# ===== flag (3) =====

scenario(
    "umber-wisp", "flag", ["multi_leg", "unclear_phrase"],
    "Boston to San Francisco on February 9th for the design review. I want the 8 a.m. nonstop. I know there's a "
    "cheaper connection, but I'd rather not take it.",
    trip(**{**SFO_TRIP, "traveller_name": "Irene Castell", "traveller_title": "Senior Applications Engineer",
            "wants_nonstop": True}),
    search("BOS", "SFO", "2027-02-09", SFO_FLIGHTS, SFO_OFFERS),
    expected("FLAG_FOR_APPROVAL", ["detroit-economy", "nonstop-economy"], ["ECONOMY"], ["UNCLEAR_POLICY_TEXT"],
             UNCLEAR_ROLES, LOW_CLAUSES, phrase="The traveler will have the option of deciding whether the alternative "
             "is acceptable or unacceptable"),
    [OPTION, LOWEST, ROUTING, CONCERNS],
    "The Detroit connection passes all three tests of lines 141-146 (saves $249.00, 85 more minutes, leaves 45 "
    "minutes before the requested time), so on every reading of the list it is the lowest logical airfare, which line "
    "118 says travelers 'are required to accept'. Lines 113-115 say the traveler 'will have the option of deciding "
    "whether the alternative is acceptable or unacceptable' and, on declining, the lost savings go on the itinerary. "
    "The traveller declines; the handbook gives no order between the two: hold the nonstop or the connection.",
    flag_twins=["maple-onyx", "nettle-brine"],
    ambiguity={"phrase": "The traveler will have the option of deciding whether the alternative is acceptable or "
               "unacceptable",
               "readings": [("line 118 requires the lowest logical airfare and the connection passes every routing "
                            "test: book the Detroit connection"),
                            ("lines 113-115 let the traveller decline the cheaper alternative, with the lost savings "
                            "noted on the itinerary: book the nonstop")]})

scenario(
    "vetch-harbor", "flag", ["multi_leg", "unclear_phrase"],
    "Boston to Portland, Oregon on January 28th for the customer line trial. I'd like premium economy for the trip, "
    "please.",
    trip(traveller_name="Tessa Moreau", traveller_title="Process Development Engineer", origin="BOS",
         destination="PDX", travel_date="2027-01-28", booking_date="2027-01-07", purpose="Customer production-line trial",
         purpose_kind="PROJECT_WORK", requested_cabin="PREMIUM_ECONOMY"),
    search("BOS", "PDX", "2027-01-28", {
        "united": {"carrier": "UA", "via": ["ORD"], "depart": "07:05", "minutes": [140, 245], "layovers": [70]},
        "american": {"carrier": "AA", "via": ["ORD"], "depart": "09:40", "minutes": [145, 250], "layovers": [65]},
    }, [
        offer("united-economy", "united", "ECONOMY", 41800),
        offer("united-premium", "united", "PREMIUM_ECONOMY", 69500),
        offer("american-economy", "american", "ECONOMY", 43600),
        offer("american-premium", "american", "PREMIUM_ECONOMY", 72800),
    ]),
    expected("FLAG_FOR_APPROVAL", ["united-premium"], ["PREMIUM_ECONOMY"], ["UNCLEAR_POLICY_TEXT"], UNCLEAR_ROLES,
             ["AIRLINE_TRAVEL"], phrase="For flights with a segment of 3 hours or more in duration, an employee may "
             "select"),
    [PREMIUM, COACH, CONCERNS],
    "Each itinerary has one flight under 3 hours (140 or 145 minutes to Chicago) and one of 3 hours or more (245 or "
    "250 minutes to Portland). Premium economy may be selected 'for flights with a segment of 3 hours or more' (lines "
    "137-138), but coach is used on 'all flights with each segment under 3 hours' (line 136), and the offer sells "
    "premium economy on both flights. The text does not say whether one long segment qualifies the whole ticket: hold "
    "the cheapest premium economy fare.",
    flag_twins=["birch-tallow", "gorse-lumen"],
    ambiguity={"phrase": "For flights with a segment of 3 hours or more in duration, an employee may select",
               "readings": [("the itinerary has a segment of 3 hours or more, so premium economy may be selected for "
                            "the ticket: book the United premium economy fare"),
                            ("only the long segment qualifies and the short one stays in coach; no offer sells that, so "
                            "book the lowest economy fare")]})

scenario(
    "willow-gale", "flag", ["approval_required", "dearer_option"],
    "Chicago to Hong Kong on February 22nd for the supplier development program. Business class please, it's a very "
    "long flight.",
    trip(traveller_name="Arjun Mehta", traveller_title="Supplier Development Manager", origin="ORD", destination="HKG",
         travel_date="2027-02-22", booking_date="2027-01-25", purpose="Supplier development program in Hong Kong",
         purpose_kind="PROJECT_WORK", requested_cabin="BUSINESS"),
    search("ORD", "HKG", "2027-02-22", {
        "cathay": {"carrier": "CX", "depart": "12:40", "minutes": [930]},
        "american": {"carrier": "AA", "depart": "14:15", "minutes": [940]},
    }, [
        offer("cathay-economy", "cathay", "ECONOMY", 121000),
        offer("cathay-business", "cathay", "BUSINESS", 750000),
        offer("american-economy", "american", "ECONOMY", 126500),
        offer("american-business", "american", "BUSINESS", 784000),
    ]),
    expected("FLAG_FOR_APPROVAL", ["cathay-business"], ["BUSINESS"], ["APPROVAL_REQUIRED"], ["SUPERVISOR"],
             ["AIRLINE_TRAVEL"]),
    [TICKET, BUSINESS],
    "A 930-minute nonstop allows business (lines 139-140). The cheapest business ticket is exactly $7,500.00: 'totaling "
    "$7,500 USD or greater' is inclusive, so it needs a supervisor approval before it is purchased (lines 125-128), "
    "and none is on file. Hold the business fare for the supervisor; approval required, not 'no compliant offer'.",
    flag_twins=["cinder-moth", "larch-pewter"],
    ambiguity="none: an approval is required and missing; the text is clear")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    for data in S:
        (OUT / f"{data['id']}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(S)} scenarios to {OUT}")


if __name__ == "__main__":
    main()

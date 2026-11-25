"""The answer key's rules for the Standex International Corporation TVL 1-1 Travel Policies and Guidelines
(February 2018), as exact integer code. Byte-identical in src/plugin/rules.py and verifier/rules.py; it imports
only modules a verifier may use.

Every rule cites the frozen handbook text (src/plugin/data/policy.txt) by line. Where the text leaves an
answer open, the rule returns FLAG_FOR_APPROVAL with the unclear words, and a scenario may depend on each
unclear phrase at most once (tests/test_scenarios.py). Combinations no scenario needs raise ValueError, so a
new scenario cannot fall silently into untested logic.

The duration hook. Lines 136-140 set the cabin by segment: "Coach or economy class will be used on all flights
with each segment under 3 hours", "For flights with a segment of 3 hours or more in duration, an employee may
select a premium economy seating", "For flights with a segment of 10 hours or more in duration, an employee may
select business class." Both thresholds are inclusive ("or more") and measured on one segment's scheduled
minutes, never on segments added together. An itinerary whose every segment reaches the limit is over it on
every reading, and one whose every segment is under it is not. When one segment reaches the limit and another
does not, the text does not say whether the cabin chosen for "flights with a segment" of that length covers the
short segment too (the world sells one cabin on every flight of an offer): unclear (None).
"""

from contract import Approver, Cabin, Clause, Decision, Passenger, Purpose, ReasonCode, SignOffSubject

from .world import clock_minutes, days_between, utc_minute

HANDBOOK = "Standex International Corporation, TVL 1-1 Travel Policies and Guidelines, February 2018"

# Each closed-list section and the heading it names in the frozen text (tests check every heading is there).
CLAUSE_HEADINGS = {
    Clause.PURPOSE: "PURPOSE",
    Clause.SCOPE_OF_POLICY: "SCOPE OF POLICY",
    Clause.POLICY_PRINCIPLES: "POLICY PRINCIPLES",
    Clause.RESPONSIBILITIES: "RESPONSIBILITES",
    Clause.ENFORCEMENT: "ENFORCEMENT",
    Clause.TRANSPORTATION_EXPENSES: "TRANSPORTATION EXPENSES",
    Clause.TRAVEL_MANAGEMENT: "TRAVEL MANAGEMENT",
    Clause.AIRLINE_TRAVEL: "AIRLINE TRAVEL",
    Clause.INTERNATIONAL_TRAVEL: "INTERNATIONAL TRAVEL",
    Clause.TRAVEL_SAVINGS_INCENTIVE: "TRAVEL SAVINGS INCENTIVE PROGRAM",
    Clause.ONLINE_BOOKING: "ONLINE BOOKING",
    Clause.EXCESS_LUGGAGE: "EXCESS LUGGAGE",
    Clause.AIR_UPGRADES: "UPGRADES FOR AIR TRAVEL",
    Clause.INFLIGHT_INTERNET: "INFLIGHT INTERNET",
    Clause.UNUSED_TICKETS: "UNUSED AIRLINE TICKETS",
    Clause.LOYALTY_PROGRAMS: "LOYALTY PROGRAMS",
    Clause.RENTAL_CARS: "RENTAL CARS",
    Clause.TRAIN: "Train",
    Clause.SPOUSE_COMPANION: "SPOUSE/ COMPANION TRAVEL",
    Clause.CORPORATE_CREDIT_CARD: "CORPORATE CREDIT CARD",
    Clause.AUTHORIZED_USAGE: "AUTHORIZED USAGE",
    Clause.CASH_ADVANCE: "TRAVEL (CASH) ADVANCE",
    Clause.NON_REIMBURSABLE: "NON-REIMBURSABLE EXPENSES",
    Clause.SAFETY_TIPS: "GENERAL TRAVEL SAFETY TIPS",
    Clause.EXCEPTIONS: "EXCEPTIONS TO THIS POLICY",
}

# The handbook's duration thresholds (the per-handbook duration hook; tests/test_duration.py tests both
# sides of each). ">=" is inclusive ("3 hours or more", "10 hours or more").
DURATION_RULES = (
    {"name": "premium-economy", "minutes": 180, "operator": ">=", "lines": [137, 138],
     "quote": "For flights with a segment of 3 hours or more in duration, an employee may select a premium economy "
              "seating if available by the carrier."},
    {"name": "business", "minutes": 600, "operator": ">=", "lines": [139, 140],
     "quote": "For flights with a segment of 10 hours or more in duration, an employee may select business class."},
)
LIMITS = {rule["name"]: rule["minutes"] for rule in DURATION_RULES}

# Handbook-specific conventions shown by booking_requirements, beyond the template's (none here).
CONVENTIONS = ()

# Lines 125-128: "Airline tickets totaling $7,500 USD or greater will need a supervisor approval prior to the
# ticket being purchased" (inclusive, in cents of USD).
SUPERVISOR_TICKET_CENTS = 750_000
# Lines 141-146, the connecting-routing tests, in integer minutes and cents. "Fare savings is $200 USD ... or
# more roundtrip" (inclusive); "One-way elapsed trip time is not increased by more than 2 hours" (inclusive);
# "Departure/arrival time is within 2 hours (before/after) of the requested time" (inclusive).
ROUTE_SAVINGS_CENTS = 20_000
ROUTE_EXTRA_MINUTES = 120
ROUTE_WINDOW_MINUTES = 120
# Every case buys a one-way fare, and the savings test is worded "roundtrip". A one-way saving of $200 or more
# passes on every reading and one under $100 fails on every reading (even doubled it stays under $200); a saving
# between the two is left open, and no scenario uses one.
ROUTE_SAVINGS_FLOOR_CENTS = 10_000
# Lines 118-119: "flights should be booked 14-21 days in advance when possible": a soft rule that never changes
# the decision; a trip booked later is still booked.
ADVANCE_DAYS = 14

TRAVELLER_OPTION_PHRASE = "The traveler will have the option of deciding whether the alternative is acceptable or unacceptable"
SEGMENT_PHRASE = "For flights with a segment of 3 hours or more in duration, an employee may select"

# Who a hold over unclear words may name: nobody is named to settle the text; lines 935-937 send concerns about
# the policy as written to the immediate supervisor/manager, and lines 37-40 let exceptions be granted only by
# the Group VP of Finance or the Corporate CFO.
UNCLEAR_ROLES = [Approver.NOT_NAMED, Approver.SUPERVISOR, Approver.MANAGER, Approver.GROUP_VP_FINANCE,
                 Approver.CHIEF_FINANCIAL_OFFICER]
# Such a hold also waits on that sign-off, so APPROVAL_REQUIRED may stand beside UNCLEAR_POLICY_TEXT (the reason
# of a hold that awaits someone; NJC iron-plover), and the section may be EXCEPTIONS TO THIS POLICY (lines 935-937).
UNCLEAR_REASONS = [ReasonCode.UNCLEAR_POLICY_TEXT, ReasonCode.APPROVAL_REQUIRED]


def over(rule, offer):
    """True, False or None (unclear): whether ``offer``'s outbound flights reach the handbook's ``rule``
    (premium-economy: a segment of 180 minutes or more; business: a segment of 600 minutes or more)."""
    if rule not in LIMITS:
        raise ValueError(f"unknown duration rule {rule!r}")
    reached = [segment.scheduled_minutes >= LIMITS[rule] for segment in offer.segments]
    if all(reached):
        return True
    if not any(reached):
        return False
    return None


def by_value(items):
    return sorted(set(items), key=lambda item: item.value)


def answer(decision, offers, reasons, approvers, clauses, why, phrase=""):
    return {
        "decision": decision,
        "offer_ids": sorted(offer.offer_id for offer in offers),
        "cabins": by_value(offer.cabin for offer in offers) or [Cabin.NONE],
        "reason_codes": by_value(reasons),
        "approvers": by_value(approvers),
        "clauses": by_value(clauses),
        "unclear_phrase": phrase,
        "explanation": why,
    }


def refuse(reasons, clauses, why):
    return answer(Decision.REFUSE, [], reasons, [Approver.NONE], clauses, why)


def cheapest(offers):
    if not offers:
        return []
    low = min(offer.fare_cents for offer in offers)
    return [offer for offer in offers if offer.fare_cents == low]


def signed(trip, subject, roles):
    return sorted({record.role for record in trip.sign_offs if record.subject == subject and record.role in roles},
                  key=lambda role: role.value)


def unused_sign_offs(trip):
    """Approvers a decision that relies on nobody accepts: NONE, and the role of any sign-off on file that the
    decision does not use. The approver field names the sign-off a decision relies on; a reader may also name
    one that is on file and was weighed, so both are accepted."""
    return [Approver.NONE, *(record.role for record in trip.sign_offs)]


# SYNC_NOTES 4': a BOOK or REFUSE whose needed sign-off is already on file accepts that role and NONE (readers
# split on whether a sign-off already given is still "relied on"); a hold awaiting a sign-off accepts only the
# awaited role.


def in_cabin(offers, cabin):
    return [offer for offer in offers if offer.cabin == cabin]


def ticket_check(trip, wanted, reasons, approvers, clauses, why):
    """Lines 125-128: a ticket of $7,500 or more needs a supervisor's approval before it is bought. With it on
    file the booking relies on it; without it the ticket is held for it."""
    high = [offer.fare_cents >= SUPERVISOR_TICKET_CENTS for offer in wanted]
    if not any(high):
        return answer(Decision.BOOK, wanted, reasons, approvers, clauses, why)
    if not all(high):
        raise ValueError("accepted offers on both sides of the $7,500 approval line are not modelled")
    if signed(trip, SignOffSubject.TICKET_PURCHASE, [Approver.SUPERVISOR]):
        return answer(Decision.BOOK, wanted, [*reasons, ReasonCode.TICKET_TOTAL_APPROVED], [Approver.SUPERVISOR, Approver.NONE],
                      clauses, why + " Lines 125-128: the ticket totals $7,500 or more, and the supervisor's approval "
                      "is on file before purchase.")
    return answer(Decision.FLAG_FOR_APPROVAL, wanted, [ReasonCode.APPROVAL_REQUIRED], [Approver.SUPERVISOR], clauses,
                  why + " Lines 125-128: but the ticket totals $7,500 or more and needs a supervisor approval before "
                  "it is bought, which is not on file: hold it.")


def solve(trip, offers, hidden):
    """The answer key for one trip and the offers on its route and date: the decision, and every accepted
    offer id, cabin, reason, approver and section. ``hidden`` (the scenario's answer_key_inputs) is unused
    by this handbook."""
    if hidden:
        raise ValueError("this handbook's scenarios carry no answer_key_inputs")
    if any(offer.return_segments for offer in offers):
        raise ValueError("round-trip fares are not modelled: every case buys a one-way ticket")
    seated = [offer for offer in offers if offer.seats_available]
    if trip.passenger == Passenger.SPOUSE_OR_COMPANION:
        return companion(trip, seated)
    if trip.passenger != Passenger.EMPLOYEE:
        raise ValueError(f"a {trip.passenger.value} passenger is not modelled")
    if trip.purpose_kind == Purpose.PERSONAL:
        return refuse([ReasonCode.PERSONAL_TRAVEL_NOT_COVERED, ReasonCode.OUTSIDE_POLICY_SCOPE],
                      [Clause.POLICY_PRINCIPLES, Clause.CORPORATE_CREDIT_CARD, Clause.AUTHORIZED_USAGE],
                      "Lines 47-48: employees are not permitted to use the company's credit card accounts to make "
                      "personal travel reservations; line 737: the corporate card is for business expenses only. The "
                      "company buys no ticket for a personal trip.")
    if trip.requested_cabin == Cabin.BUSINESS:
        return business(trip, seated)
    if trip.requested_cabin == Cabin.PREMIUM_ECONOMY:
        return premium(trip, seated)
    if trip.requested_cabin != Cabin.ECONOMY:
        raise ValueError(f"a {trip.requested_cabin.value} request is not modelled")
    return economy(trip, seated)


def lowest_economy(seated):
    lowest = cheapest(in_cabin(seated, Cabin.ECONOMY))
    if not lowest:
        raise ValueError("no economy offer can be bought")
    if any(offer.refundable for offer in lowest):
        raise ValueError("a refundable fare that is the lowest is not modelled")
    return lowest


def economy_clauses():
    # Line 118 (Airline Travel) and lines 111-112 (Travel Management): the lowest airfare.
    return [Clause.AIRLINE_TRAVEL, Clause.TRAVEL_MANAGEMENT]


def companion(trip, seated):
    """Lines 697-703: a spouse or companion's travel is not reimbursable, except transportation when there is a
    specific business purpose and the trip is approved in advance by the appropriate group president or chief
    financial officer."""
    if not trip.accompanies or trip.requested_cabin != Cabin.ECONOMY:
        raise ValueError("a companion with nobody accompanied, or outside economy, is not modelled")
    if trip.purpose_kind in (Purpose.PERSONAL, Purpose.INTERNAL_MEETING, Purpose.TRAINING):
        # The trip record calls this a personal trip, so PERSONAL_TRAVEL_NOT_COVERED names the same refusal.
        return refuse([ReasonCode.COMPANION_NOT_COVERED, ReasonCode.PERSONAL_TRAVEL_NOT_COVERED],
                      [Clause.SPOUSE_COMPANION, Clause.NON_REIMBURSABLE],
                      "Lines 697-700: spouse or companion travel expenses, air included, are not reimbursable; the "
                      "exception of lines 700-703 needs a specific business purpose, and this trip has none (line 874: "
                      "family expenses on business trips are not reimbursable). The company buys no ticket.")
    if trip.purpose_kind != Purpose.CLIENT_EVENT:
        raise ValueError("a companion trip of another kind is not modelled")
    roles = signed(trip, SignOffSubject.COMPANION_TRAVEL, [Approver.GROUP_PRESIDENT, Approver.CHIEF_FINANCIAL_OFFICER])
    if not roles:
        raise ValueError("a companion trip with a business purpose but no advance approval is not modelled")
    lowest = lowest_economy(seated)
    return answer(Decision.BOOK, lowest, [ReasonCode.COMPANION_TRAVEL_AUTHORIZED, ReasonCode.LOWEST_FARE],
                  [*roles, Approver.NONE],
                  [Clause.SPOUSE_COMPANION, Clause.AIRLINE_TRAVEL],
                  "Lines 700-703: the companion's trip has a specific business purpose and was approved in advance by "
                  "the group president, so the transportation is paid; line 118: at the lowest logical airfare.")


def business(trip, seated):
    """A business request. Lines 139-140: business class may be selected on flights with a segment of 10 hours or
    more; lines 37-40: an exception may be granted only by the Group VP of Finance or the Corporate CFO."""
    offered = in_cabin(seated, Cabin.BUSINESS)
    granted = signed(trip, SignOffSubject.POLICY_EXCEPTION, [Approver.GROUP_VP_FINANCE, Approver.CHIEF_FINANCIAL_OFFICER])
    if granted:
        if not trip.doctor_note_on_file:
            raise ValueError("an exception without a documented special situation is not modelled")
        if any(over("business", offer) is not False for offer in offered):
            raise ValueError("an exception on a flight that already allows business is not modelled")
        wanted = cheapest(offered)
        if not wanted:
            raise ValueError("an exception with no business offer is not modelled")
        return ticket_check(trip, wanted, [ReasonCode.POLICY_EXCEPTION_APPROVED, ReasonCode.MEDICAL_NEED],
                            [*granted, Approver.NONE],
                            [Clause.POLICY_PRINCIPLES, Clause.EXCEPTIONS, Clause.AIRLINE_TRAVEL],
                            "Lines 37-40: an exception granted in a special situation by the Group VP of Finance; lines "
                            "148-149: the doctor's written documentation of the accommodation is on file. The segment is "
                            "under 10 hours (lines 139-140), so only the exception allows business: the cheapest "
                            "business fare.")
    if trip.doctor_note_on_file:
        raise ValueError("a documented need without an exception granted is not modelled")
    qualifying = [offer for offer in offered if over("business", offer) is True]
    wanted = cheapest(qualifying)
    if any(over("business", offer) is None and (not wanted or offer.fare_cents < wanted[0].fare_cents)
           for offer in offered):
        raise ValueError("a business fare on a mixed-length itinerary cheaper than the qualifying one is not modelled")
    if not wanted:
        lowest = lowest_economy(seated)
        return answer(Decision.BOOK, lowest,
                      [ReasonCode.UPGRADE_NOT_ELIGIBLE, ReasonCode.LONG_FLIGHT_CONDITION_NOT_MET, ReasonCode.LOWEST_FARE],
                      unused_sign_offs(trip), [Clause.AIRLINE_TRAVEL, Clause.AIR_UPGRADES],
                      "Lines 139-140: business class needs a segment of 10 hours or more, and no segment reaches 600 "
                      "minutes; the traveller asked for plain economy otherwise, so the lowest logical airfare (line "
                      "118). Line 225: upgrades are not reimbursable.")
    return ticket_check(trip, wanted, [ReasonCode.INTERNATIONAL_LONG_FLIGHT, ReasonCode.LONG_FLIGHT_APPROVED],
                        unused_sign_offs(trip), [Clause.AIRLINE_TRAVEL],
                        "Lines 139-140: the flight has a segment of 10 hours or more (600 minutes or more), so the "
                        "employee may select business class: the cheapest business fare (line 118).")


def premium(trip, seated):
    """A premium economy request. Lines 136-138: coach on all flights with each segment under 3 hours; premium
    economy may be selected for flights with a segment of 3 hours or more."""
    offered = in_cabin(seated, Cabin.PREMIUM_ECONOMY)
    if not offered:
        raise ValueError("a premium economy request with no premium economy offer is not modelled")
    qualifying = [offer for offer in offered if over("premium-economy", offer) is True]
    unclear = [offer for offer in offered if over("premium-economy", offer) is None]
    if qualifying and unclear:
        raise ValueError("premium economy offers both qualifying and unclear are not modelled")
    if unclear:
        # Hold either reading's offer (the premium fare, or the lowest economy fare of the per-segment reading);
        # the hold waits on a supervisor/manager (lines 935-937), so APPROVAL_REQUIRED and EXCEPTIONS also stand.
        return answer(Decision.FLAG_FOR_APPROVAL, [*cheapest(unclear), *lowest_economy(seated)],
                      UNCLEAR_REASONS, UNCLEAR_ROLES, [Clause.AIRLINE_TRAVEL, Clause.EXCEPTIONS],
                      "Lines 136-138: one flight of the itinerary is 3 hours or more and the other is under 3 hours. "
                      "Premium economy may be selected 'for flights with a segment of 3 hours or more', but coach is used "
                      "on segments under 3 hours, and the offer sells premium economy on both flights; the text does not "
                      "say whether the ticket qualifies. Hold the premium economy fare.", phrase=SEGMENT_PHRASE)
    if qualifying:
        return answer(Decision.BOOK, cheapest(qualifying), [ReasonCode.PREMIUM_ECONOMY_ALLOWED],
                      unused_sign_offs(trip), [Clause.AIRLINE_TRAVEL],
                      "Lines 137-138: every flight of the itinerary is 3 hours or more (180 minutes or more), so the "
                      "employee may select premium economy: the cheapest premium economy fare.")
    return answer(Decision.BOOK, lowest_economy(seated), [ReasonCode.UPGRADE_NOT_ELIGIBLE, ReasonCode.LOWEST_FARE],
                  unused_sign_offs(trip), [Clause.AIRLINE_TRAVEL, Clause.AIR_UPGRADES],
                  "Line 136: coach or economy is used on flights with each segment under 3 hours (under 180 minutes), "
                  "so premium economy is not available; the lowest logical airfare (line 118). Line 225: upgrades are "
                  "not reimbursable.")


def economy(trip, seated):
    """An economy request: the lowest logical airfare (line 118), with the airline, routing and fare-type wishes
    the handbook speaks to."""
    if trip.wants_refundable:
        return refundable(trip, seated)
    if trip.chosen_airline:
        return airline_choice(trip, seated)
    if trip.requested_departure:
        return routing(trip, seated)
    if trip.wants_nonstop:
        raise ValueError("a nonstop wish without a requested time is not modelled")
    lowest = lowest_economy(seated)
    reasons, clauses = [ReasonCode.LOWEST_FARE], economy_clauses()
    notes = ["Line 118: travelers are required to accept the lowest logical airfare available"]
    if any(over("business", offer) is True for offer in lowest):
        reasons.append(ReasonCode.COST_SAVINGS)
        clauses.append(Clause.TRAVEL_SAVINGS_INCENTIVE)
        notes.append("lines 179-180: economy instead of an allowed business fare on a 10-hour segment is what the "
                     "savings incentive rewards; its 14-day and supervisor conditions (lines 186-189) concern the "
                     "reward, not the ticket")
    if days_between(trip.booking_date, trip.travel_date) < ADVANCE_DAYS:
        notes.append("line 119: booking 14-21 days ahead applies 'when possible', so a later booking is still made")
    return answer(Decision.BOOK, lowest, reasons, unused_sign_offs(trip), clauses, "; ".join(notes) + ".")


def refundable(trip, seated):
    """Lines 130-131: the lower non-refundable fare, unless the travel plans are subject to known possible
    changes."""
    if not trip.dates_may_move:
        raise ValueError("a refundable wish without plans that may change is not modelled")
    wanted = cheapest([offer for offer in in_cabin(seated, Cabin.ECONOMY) if offer.refundable])
    if not wanted:
        raise ValueError("a refundable wish with no refundable offer is not modelled")
    return answer(Decision.BOOK, wanted, [ReasonCode.FLEXIBLE_FARE_JUSTIFIED, ReasonCode.LOWEST_FARE],
                  unused_sign_offs(trip), [Clause.AIRLINE_TRAVEL],
                  "Lines 130-131: the lower non-refundable fare is used unless the travel plans are subject to known "
                  "possible changes; the meeting date may still move, so the cheapest refundable economy fare.")


def airline_choice(trip, seated):
    """Lines 154-155: airline selection by an employee is not permitted unless the cost is at or below the lowest
    fare offered; lines 240-246: no airline at a higher price for personal points."""
    lowest = lowest_economy(seated)
    chosen = [offer for offer in lowest if offer.carrier == trip.chosen_airline]
    clauses = [Clause.AIRLINE_TRAVEL, Clause.LOYALTY_PROGRAMS]
    if chosen:
        return answer(Decision.BOOK, chosen,
                      [ReasonCode.CHOSEN_AIRLINE_AT_LOWEST_FARE, ReasonCode.LOWEST_FARE,
                       ReasonCode.LOYALTY_PROGRAM_PREFERENCE],
                      unused_sign_offs(trip), clauses,
                      "Lines 154-155: the traveller's airline costs no more than the lowest fare offered ('at or "
                      "below'), so the selection is permitted: book the chosen airline's lowest fare.")
    if not any(offer.carrier == trip.chosen_airline for offer in in_cabin(seated, Cabin.ECONOMY)):
        raise ValueError("a chosen airline with no offer on the route is not modelled")
    return answer(Decision.BOOK, lowest, [ReasonCode.LOWEST_FARE, ReasonCode.LOYALTY_PROGRAM_PREFERENCE],
                  unused_sign_offs(trip), [*clauses, Clause.TRAVEL_MANAGEMENT],
                  "Lines 154-155: the chosen airline costs more than the lowest fare offered, so the selection is not "
                  "permitted; lines 240-246: no airline at a higher price for personal points. The lowest fare.")


def departure_gap(offer, requested):
    return abs(clock_minutes(offer.segments[0].depart_local[11:]) - clock_minutes(requested))


def arrival_gap(offer, nonstop):
    return abs(utc_minute(offer.segments[-1].arrive_utc) - utc_minute(nonstop.segments[-1].arrive_utc))


def route_tests(offer, nonstop, requested):
    """Lines 141-146 for one cheaper connection against the nonstop: (savings, elapsed, time) each True or False.
    Raises where a reading would differ: a one-way saving between $100 and $200 (the test says 'roundtrip'), or a
    departure and an arrival on different sides of the 2-hour window ('Departure/arrival')."""
    saving = nonstop.fare_cents - offer.fare_cents
    if ROUTE_SAVINGS_FLOOR_CENTS <= saving < ROUTE_SAVINGS_CENTS:
        raise ValueError("a one-way saving between $100 and $200 is not modelled (the test is worded roundtrip)")
    leaves = departure_gap(offer, requested) <= ROUTE_WINDOW_MINUTES
    lands = arrival_gap(offer, nonstop) <= ROUTE_WINDOW_MINUTES
    if leaves != lands:
        raise ValueError("a departure and arrival on different sides of the window are not modelled")
    return (saving >= ROUTE_SAVINGS_CENTS, offer.elapsed_minutes - nonstop.elapsed_minutes <= ROUTE_EXTRA_MINUTES,
            leaves)


def routing(trip, seated):
    """A request with a departure time, nonstop or not. Lines 141-146: the less expensive connecting routing
    should be selected if the fare saving is $200 or more, the elapsed time grows by no more than 2 hours, or the
    times are within 2 hours of the requested time. The list's '; or' leaves open whether one test or all three
    are needed, so a connection is only modelled when its three tests agree. Lines 113-115 give the traveller the
    option of declining a cheaper alternative, while line 118 requires the lowest logical airfare."""
    economy_offers = in_cabin(seated, Cabin.ECONOMY)
    if any(offer.refundable for offer in economy_offers):
        raise ValueError("refundable fares on a routing case are not modelled")
    nonstops = cheapest([offer for offer in economy_offers if offer.stops == 0])
    if len(nonstops) != 1:
        raise ValueError("a routing case needs one cheapest nonstop")
    nonstop = nonstops[0]
    if departure_gap(nonstop, trip.requested_departure) > ROUTE_WINDOW_MINUTES:
        raise ValueError("a nonstop away from the requested time is not modelled")
    cheaper = [offer for offer in economy_offers if offer.stops > 0 and offer.fare_cents < nonstop.fare_cents]
    logical, other = [], []
    for offer in cheaper:
        tests = route_tests(offer, nonstop, trip.requested_departure)
        if all(tests):
            logical.append(offer)
        elif not any(tests):
            other.append(offer)
        else:
            raise ValueError("a connection passing some routing tests and failing others is not modelled ('; or')")
    best = cheapest(logical)
    if best and any(offer.fare_cents < best[0].fare_cents for offer in other):
        raise ValueError("a cheaper connection failing every test below a logical one is not modelled")
    clauses = [Clause.AIRLINE_TRAVEL, Clause.TRAVEL_MANAGEMENT]
    if not best:
        if not trip.wants_nonstop:
            raise ValueError("a routing case with no logical connection and no nonstop wish is not modelled")
        return answer(Decision.BOOK, [nonstop],
                      [ReasonCode.CONNECTION_TOO_LONG, ReasonCode.ALTERNATE_ROUTE_WITHIN_MARGIN, ReasonCode.LOWEST_FARE],
                      unused_sign_offs(trip), clauses,
                      "Lines 141-146: the cheaper connection saves under $100, adds more than 2 hours and leaves and lands "
                      "more than 2 hours from the requested time, so it fails every test and is not the lowest logical "
                      "airfare (line 118): book the nonstop the traveller asked for, the cheapest nonstop.")
    if not trip.wants_nonstop:
        return answer(Decision.BOOK, best,
                      # The connection is "within" every margin of lines 145-146, so WITHIN_MARGIN also names it.
                      [ReasonCode.COST_SAVINGS, ReasonCode.LOWEST_FARE, ReasonCode.ALTERNATE_ROUTE_TOO_EXPENSIVE,
                       ReasonCode.ALTERNATE_ROUTE_WITHIN_MARGIN],
                      unused_sign_offs(trip), clauses,
                      "Lines 141-146: the connection saves $200 or more, adds no more than 2 hours and leaves within 2 "
                      "hours of the requested time, so the less expensive routing is selected; line 118: the lowest "
                      "logical airfare. The traveller did not ask for the nonstop.")
    return answer(Decision.FLAG_FOR_APPROVAL, [nonstop, *best], UNCLEAR_REASONS, UNCLEAR_ROLES,
                  [*clauses, Clause.EXCEPTIONS],
                  "Lines 141-146: the connection passes every routing test, so it is the lowest logical airfare, which "
                  "line 118 requires travelers to accept; but lines 113-115 say the traveler has the option of deciding "
                  "whether the alternative is acceptable and, on declining the lowest airfare, the lost savings go on "
                  "the itinerary. The traveller declines it and the handbook gives no order between the two: hold.",
                  phrase=TRAVELLER_OPTION_PHRASE)

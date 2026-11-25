# Standex Travel Policy Flight Booking

**Source of the handbook:** http://web.archive.org/web/20231025075509id_/https://standex.com/wp-content/uploads/2020/06/TVL-1-1-Travel-Policies-and-Guidelines-2-2018.pdf. The agent reads it verbatim (bundled at `src/plugin/data/policy.txt`); flights, fares and trips are synthetic.

**No affiliation with Standex International Corporation.** The handbook is the company's *TVL 1-1 Travel Policies
and Guidelines* (February 2018), a PDF the company once hosted publicly (Wayback Machine copy), bundled verbatim for
research. Do not publish this plugin before the course staff confirm that a verbatim corporate handbook may be
redistributed (MASTER_PLAN section 4: corporate plugins wait for the instructor's answer).

A `nanoagent.plugin/v0001` plugin. An agent handles one traveller's flight request under the company's real travel
policy: it reads the trip record, searches a simulated flight world and submits **BOOK**, **REFUSE** or
**FLAG_FOR_APPROVAL** with the offer, cabin, reason, approver and policy section. A deterministic Python verifier,
with no LLM, rebuilds the offers and the policy's answer itself and checks every field. Built from the
original-handbook template (`handbook_plugins/_template`); `tests/build_scenarios.py` writes the scenario files.

## The handbook and the harness flag

The frozen text (`src/plugin/data/policy.txt`, 6,972 words, 973 lines, 46,942 bytes, sha256 `005f2a55...fcd2d486`,
equal to `pilot_work/originals/standex/frozen/SHA256SUMS`) is never paraphrased, and the task text restates no rule.
Under stock NanoAgent the agent does not see it: the plugin then runs as the `off` baseline. The `harness.policy`
switch of the NanoAgent fork (github.com/tejassaboo/nanoagent, branch `policy-switch`) adds it to the system prompt:
`harness.policy: full` adds all of it, and the selection methods add parts of it. These plugins are meant to run
with `query: instructions+input`, so a selector sees the traveller's request.

**Size.** At 1.33 tokens a word the policy alone is about 9,300 tokens; calibrated on the paid Thornton and NJC runs
(about 0.2 tokens a character plus 1,800) the first `full` call is about 11,200 input tokens. A run makes 3 calls
(`get_trip`, `search_flights`, `submit`) of about 11,200, 11,500 and 12,000 to 12,800 (3 to 8 offers): about 35,000
to 36,000 input tokens per run, plus about 12,500 for the final message after `submit`. That is well under the hosted
cap of 65,536, and a run with one repeated search (about 48,000 before `submit`) still fits.

## Task

- **Input:** `TaskInput`: `scenario` (one of 24 case ids) and `request`, the traveller's own words.
- **Steps:** `get_trip`, then `search_flights` on the trip's route and date (every case buys one one-way ticket),
  then `submit`.
- **Output:** `BookingOutput`: `decision`, `offer_id` (empty when refusing), `cabin` (`NONE` when refusing),
  `reason_code`, `approver` and `clause`, each from a closed list. The reason list is the template's shared list plus
  five codes of this policy (`COMPANION_TRAVEL_AUTHORIZED`, `POLICY_EXCEPTION_APPROVED`, `TICKET_TOTAL_APPROVED`,
  `FLEXIBLE_FARE_JUSTIFIED`, `CHOSEN_AIRLINE_AT_LOWEST_FARE`) and twelve decoy codes from other handbooks' rules.
  Fares are in cents of US dollars (`currency: USD`).
- **Success:** every field is one the answer key accepts; the cabin is graded as the chosen offer's own. Score =
  fields right / 6.
- **Reasons on a declined request.** The task instructions say that when the booking is not what the traveller asked
  for, the reason code gives why the request is declined. Such a booking accepts only the codes that name the
  handbook's ground, not `LOWEST_FARE`: `gorse-lumen` (premium economy under 3 hours) and `ivy-sorrel` (business
  under 10 hours) accept `UPGRADE_NOT_ELIGIBLE` or `LONG_FLIGHT_CONDITION_NOT_MET`. `kiln-meadow` keeps
  `LOWEST_FARE` beside `LOYALTY_PROGRAM_PREFERENCE`, because lines 154-155 decline the chosen airline on the
  lowest-fare test itself ("at or below the lowest fare offered").
- **No hidden facts:** no scenario has `answer_key_inputs`.

| Scenario | Category | Expected decision (offer; cabin) | Frozen lines |
|---|---|---|---|
| `alder-quince` | easy | BOOK (mid-economy; ECONOMY) | 111-112, 118, 136 |
| `birch-tallow` | easy | BOOK (losangeles-premium; PREMIUM_ECONOMY) | 118, 136, 137-138 |
| `cinder-moth` | easy | BOOK (cathay-business; BUSINESS) | 118, 125-128, 139-140 |
| `dahlia-quarry` | easy | BOOK (british-economy; ECONOMY) | 111-112, 118, 137-138 |
| `elm-vesper` | easy | BOOK (dallas-economy; ECONOMY) | 111-112, 118, 136 |
| `fern-cobble` | boundary_twin | BOOK (american-premium; PREMIUM_ECONOMY), 180 minutes | 136, 137-138 |
| `gorse-lumen` | boundary_twin | BOOK (american-economy; ECONOMY), 179 minutes | 118, 136, 137-138 |
| `hemlock-tide` | boundary_twin | BOOK (korean-business; BUSINESS), 600 minutes | 118, 139-140 |
| `ivy-sorrel` | boundary_twin | BOOK (korean-economy; ECONOMY), 599 minutes | 118, 137-140, 225-226 |
| `juniper-flint` | boundary_twin | BOOK (delta-economy; ECONOMY), chosen airline ties the lowest | 118, 154-155, 240 |
| `kiln-meadow` | boundary_twin | BOOK (jetblue-economy; ECONOMY), chosen airline $1 above | 118, 154-155, 240 |
| `larch-pewter` | multi_rule | BOOK (singapore-business; BUSINESS), $8,120 with the supervisor's sign-off | 118, 125-128, 139-140 |
| `maple-onyx` | multi_rule | BOOK (detroit-economy; ECONOMY): connection passes every routing test | 111-112, 118, 141-146 |
| `nettle-brine` | multi_rule | BOOK (alaska-economy; ECONOMY): connection fails every test, nonstop wanted | 112-115, 118, 141-146 |
| `ochre-pinion` | multi_rule | BOOK (american-flex; ECONOMY): refundable, plans may move | 118, 130-131, 136 |
| `oak-saffron` | hidden_clause | BOOK (jetblue-economy; ECONOMY): companion approved by the group president | 118, 697-703 |
| `poplar-wick` | hidden_clause | BOOK (airfrance-business; BUSINESS): exception by the Group VP of Finance | 37-40, 137-140, 148-149 |
| `sage-tundra` | distractor | BOOK (ana-economy; ECONOMY): savings-incentive notice rule | 118, 139-140, 179-180 |
| `thistle-amber` | distractor | BOOK (southwest-economy; ECONOMY): 35-day car rental | 111-112, 118, 137-138 |
| `quince-ember` | refusal | REFUSE: personal trip | 47-48, 737 |
| `rowan-slate` | refusal | REFUSE: companion without a business purpose | 697-703, 874 |
| `umber-wisp` | flag | FLAG_FOR_APPROVAL (nonstop or connection; ECONOMY), UNCLEAR_POLICY_TEXT (or APPROVAL_REQUIRED) | 112-118, 141-146, 935-937 |
| `vetch-harbor` | flag | FLAG_FOR_APPROVAL (united-premium or united-economy), UNCLEAR_POLICY_TEXT (or APPROVAL_REQUIRED) | 136-138, 935-937 |
| `willow-gale` | flag | FLAG_FOR_APPROVAL (cathay-business; BUSINESS), APPROVAL_REQUIRED, SUPERVISOR | 125-128, 139-140 |

Every accepted reason, approver and section per case is in the scenario files, `tests/BUILD_NOTES.md` and `tests/AUDIT_NOTES.md`.

**Duration (`rules.over`).** Lines 136-140 set the cabin per segment, inclusive: premium economy may be selected for
"a segment of 3 hours or more" (180 minutes), business class for "a segment of 10 hours or more" (600 minutes);
segments are never added together. An itinerary whose every segment reaches the limit is over it; one whose every
segment is under it is not; a mix of the two is unclear (`None`), which only `vetch-harbor` uses.

**Approvers.** A booking that uses a sign-off on file accepts that role and `NONE` (SYNC_NOTES 4'); an unused
sign-off on file is accepted beside `NONE`; a hold awaiting a sign-off accepts only the awaited role (`willow-gale`:
`SUPERVISOR`). A hold over unclear words accepts `NOT_NAMED`, `SUPERVISOR` or `MANAGER` (lines 935-937 send concerns
about the policy to the immediate supervisor/manager) and `GROUP_VP_FINANCE` or `CHIEF_FINANCIAL_OFFICER` (lines
37-40 grant exceptions).

Degenerate agents (`tests/test_verifier.py`): always holding the right offer as unclear passes 2 cases (the two
unclear flags); always booking the cheapest seat with `LOWEST_FARE`, `NONE` and the right section passes 8.

## Tools

| Tool | Does | Code |
|---|---|---|
| `booking_requirements` | The trip record's fields, the world's conventions (local times, dates, fares, sold-out seats) and its airports | `src/plugin/guide.py` |
| `get_trip` | A case's request and trip record: traveller, route, date, requested time, purpose, requested cabin, airline and fare type, sign-offs, car rental days | `src/plugin/tools.py` |
| `search_flights` | Every offer on a route and local date: the pinned scenario offers plus seeded background offers on those searches only; a search the case does not pin lists nothing and says so | `src/plugin/world.py` |
| `solve_booking` | The answer key (`rules.solve`), the agent task's `reference`, never shown to the agent | `src/plugin/rules.py` |

| Task | Does | Runner |
|---|---|---|
| `book-standex-flight` | Handles one booking request | `agent`, with `get_trip` and `search_flights`; reference `solve_booking` |
| `booking-requirements` | Shows `booking_requirements` | `tool` |
| `search-flights` | Shows `search_flights` | `tool` |

## Layout

- `contract.py`: the template's shared contract plus this policy's scenario ids, approvers, sections, reason codes
  and trip record.
- `src/plugin/`: `world.py`, `scenarios.py`, `guide.py`, `answer.py`, `tools.py` (shared), `rules.py` (this
  policy's rules, citing frozen lines), `__main__.py`.
- `src/plugin/data/`: `policy.txt` (frozen), `handbook.json`, `scenarios/*.json`.
- `verifier/`: byte-identical copies of the shared modules and `rules.py`, plus `booking.py` and `tools.py`.
- `tests/`: the template's acceptance suite; `tests/plugin_spec.py` holds this policy's settings.
- `tests/build_scenarios.py`: writes the scenario files (an authoring aid, not a test).
- `tests/BUILD_NOTES.md`: design choices, the blind read and the acceptance outputs.
- `tests/AUDIT_NOTES.md`: the independent audit and its fixes.

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv lock --check
python3 ../_template/check_shared.py .
# from a NanoAgent checkout (read-only use):
nanoagent plugin inspect <this folder>
nanoagent plugin pack <this folder> /tmp/standex-flight-policy.tar.gz
# from this folder, with that checkout's Python:
/path/to/nanoagent/nanoagent/.venv/bin/python ../_template/tools/stock_verify.py .
```

Offline: `hosts: []`, an empty `.env`, `write: []`, no clock (each case fixes its `booking_date`).

# Build notes: standex-flight-policy (wave 2, 2026-11-24)

Built from `_template` with `instantiate.py` (slug `standex`, `--task-id book-standex-flight`, `--currency USD`,
`--background 0`, `--scenarios 24`). Frozen handbook: `pilot_work/originals/standex/frozen/standex_policy.txt`,
6,972 words (under 10,000, so 24 scenarios), sha256 `005f2a55...fcd2d486`. Decisions were taken without asking (the
lead was away); each is recorded here.

## 1. What the handbook supports

Mandatory or checkable flight clauses (frozen line numbers):

| Lines | Clause | Operator / force | Used by |
|---|---|---|---|
| 118 | "required to accept the lowest logical airfare available" | mandatory | every booking |
| 111-115 | agency confirms the lowest fare; when significant savings exist, alternatives are offered and the traveller "will have the option of deciding whether the alternative is acceptable"; lost savings noted | permissive, conflicts with 118 | maple-onyx, nettle-brine, umber-wisp |
| 119 | book 14-21 days ahead "when possible" | soft (never a refusal) | sage-tundra, thistle-amber |
| 125-128 | tickets "totaling $7,500 USD or greater" need supervisor approval before purchase | inclusive | cinder-moth, larch-pewter, willow-gale |
| 130-131 | lower non-refundable fare unless plans "subject to known possible changes" | should/unless | ochre-pinion |
| 136-138 | coach when each segment under 3 hours; premium economy for a segment of "3 hours or more" | inclusive, per segment | birch-tallow, fern-cobble, gorse-lumen, vetch-harbor |
| 139-140 | business for a segment of "10 hours or more" | inclusive, per segment | cinder-moth, hemlock-tide, ivy-sorrel, larch-pewter, sage-tundra, willow-gale |
| 141-146 | cheaper connection "should be selected if" savings $200+ roundtrip; elapsed +2 h at most; "or" times within 2 h | three tests joined by "; or" | maple-onyx, nettle-brine, umber-wisp |
| 154-155 | airline selection only "at or below the lowest fare offered" | inclusive, mandatory | juniper-flint, kiln-meadow |
| 225-226, 240 | upgrades not reimbursable; no airline at a higher price for points | mandatory | ivy-sorrel, gorse-lumen, kiln-meadow |
| 37-40 | exceptions only with the Group VP of Finance or Corporate CFO | mandatory ("only") | poplar-wick |
| 47-48, 737 | no personal travel on company card accounts | mandatory | quince-ember |
| 697-703, 874 | companion travel not reimbursable, except business purpose + advance approval by group president or CFO | mandatory | oak-saffron, rowan-slate |

No rule on several employees on one flight and none on overnight stops: the `multi_traveller` and overnight overlays
are not required (plugin_spec `OVERLAY_MINIMUMS`). No round-trip case: every case buys one one-way ticket, and the
trip record has no `return_date` field.

## 2. Unclear points and how they are handled

- **"; or" in lines 141-146** (one test enough, or all three needed?). Not flagged: it is avoided. Every connection
  in a routing case passes all three tests or fails all three (rules.route_tests raises otherwise), so both readings
  agree. Also avoided: the "$200 ... roundtrip" wording on one-way fares (savings are either $200+ one-way or under
  $100 one-way; rules raise between) and "Departure/arrival" (departure and arrival gaps on the same side).
- **Lines 113-115 against line 118** (may the traveller decline a cheaper logical alternative?). Flag `umber-wisp`:
  the connection passes every test and the traveller declines it. Twins: `maple-onyx` (passes every test, traveller
  indifferent: book the connection) and `nettle-brine` (fails every test, traveller wants the nonstop: book the
  nonstop). `kiln-meadow` is not touched by it: a $1 difference is no "significant savings" alternative, and lines
  154-155 speak to airline choice directly.
- **"For flights with a segment of 3 hours or more"** on a connection with one long and one short segment (the
  world sells one cabin per offer). Flag `vetch-harbor`; twins `birch-tallow` (both segments 3 h+: premium economy)
  and `gorse-lumen` (179-minute nonstop: economy).
- **Approval required** (`willow-gale`): a $7,500.00 business ticket, no supervisor sign-off: hold for SUPERVISOR.
  Twins `cinder-moth` ($6,240: book, NONE) and `larch-pewter` ($8,120 with the sign-off: book). Together with
  willow-gale these are the $7,500 boundary (750000 cents, inclusive). Not a `boundary_twin` pair because the flag
  side must be category `flag`.
- **Savings incentive's supervisor approval** (lines 186-189) reads as a condition of the reward, not the ticket;
  `sage-tundra` puts the supervisor's short-notice note on file so the booking is the same on either reading
  (approver NONE or SUPERVISOR).

Numeric twin pairs: 180/179 minutes (premium economy), 600/599 minutes (business), airline fare equal/$1 above
(lines 154-155). The routing tests get no twin (the "; or" makes any one-test boundary a split).

## 3. Choices made without asking

1. `juniper-flint` accepts only the chosen Delta offer, not the tied JetBlue fare: the traveller's choice is
   permitted ("at or below"), so booking another airline at the same price ignores a permitted request.
2. `nettle-brine` accepts only the nonstop (not the cheaper but illogical connection the traveller declined).
3. `ivy-sorrel`: the request says "plain economy, nothing in between", so premium economy (permitted at 599
   minutes) is not accepted.
4. `ochre-pinion` accepts only the refundable fare the traveller asked for (permission is not obligation; the
   request decides).
5. Hold approvers over unclear words: NOT_NAMED, SUPERVISOR, MANAGER (lines 935-937), GROUP_VP_FINANCE,
   CHIEF_FINANCIAL_OFFICER (lines 37-40).
6. Approver rule SYNC_NOTES 4' (lead's message tonight): larch-pewter, oak-saffron and poplar-wick accept the
   on-file role and NONE; willow-gale (awaiting) accepts SUPERVISOR only.
7. Reason accept sets include LOWEST_FARE beside each specific code (validation lesson from kestrel-loom).
8. Background offers: 0 except alder-quince (3) and dahlia-quarry, elm-vesper, thistle-amber, quince-ember,
   rowan-slate (2), where no background routing can change the answer (economy-cheapest or refusal cases).
9. Decoy reason codes (grepped, none has a subject in the text): WEEKEND_TRAVEL_HOME, WEEKEND_TRIP_NOT_EARNED,
   NEXT_OF_KIN_TRAVEL, FLY_AMERICA_US_CARRIER_REQUIRED, OPEN_SKIES_AGREEMENT, CHANCELLOR_WRITTEN_AUTHORIZATION,
   CREATIVE_TICKETING, PRIVATE_AIRCRAFT_NOT_APPROVED, DOUBLE_BOOKING_PROHIBITED, DENIED_BOARDING_NOT_ALLOWED,
   CANDIDATE_TRIP_NOT_COVERED, SAME_CLASS_AS_CUSTOMER. EXTENDED_TRAVEL_SAVINGS was left out (this handbook has a
   travel savings incentive). Approver decoys: VICE_PRESIDENT, CHIEF_EXECUTIVE, HUMAN_RESOURCES.

## 4. Mix and overlays

5 easy, 6 boundary_twin, 4 multi_rule, 2 hidden_clause, 2 distractor, 2 refusal, 3 flag (12.5%). Decisions: 19 BOOK
(4 business, 3 premium economy, 12 economy), 2 REFUSE, 3 FLAG. Overlays: multi_leg 6, date_arithmetic 2 (month_end 1),
personal_travel 1, dearer_option 9, upgrade_not_taken 4, outside_air_section 4. Degenerate agents: always-flag
passes 2, always-cheapest passes 10 (MAX_PASS_ALWAYS_LOWEST = 10, its real count).

## 5. Independent blind read (non-flag scenarios)

Re-derived from the frozen text and the tool outputs only (trip record plus `search_flights` listing, dumped per
scenario), not from rules.py, then compared with `expected`.

| Scenario | My reading from text + offers | Agrees |
|---|---|---|
| alder-quince | 130-min flights, coach; 07:00 $214 sold out; cheapest seated UA $238 | yes |
| birch-tallow | both itineraries have every segment >= 180 (365/340, 380/365); PE allowed; cheapest PE DL $798 | yes |
| cinder-moth | 955-min segment >= 600, business allowed; CX $6,240 < $7,500, no approval needed | yes |
| dahlia-quarry | 410 min, PE permitted but traveller wants cheapest economy: BA $612 | yes |
| elm-vesper | no requested time, connection welcome: AA via DFW $279 cheapest | yes |
| fern-cobble | 180 min = "3 hours or more": PE; AA PE $398 | yes |
| gorse-lumen | 179 min under 3 h: coach; AA economy $246 | yes |
| hemlock-tide | 600 min = "10 hours or more": business; KE $4,880 | yes |
| ivy-sorrel | 599 min: no business; traveller wants plain economy: KE $942 | yes |
| juniper-flint | Delta $228 equals lowest: selection at or below permitted: DL 08:00 | yes |
| kiln-meadow | Delta $229 > $228 lowest: selection not permitted: JetBlue $228 | yes |
| larch-pewter | 1,110 min business; $8,120 >= $7,500, supervisor signed itinerary on file: book SQ business | yes |
| maple-onyx | DL via DTW: saves $249, +85 min, departs 07:15 (45 min off), lands 40 min after nonstop: all tests pass; traveller indifferent: book it | yes |
| nettle-brine | DL via MSP: saves $60, +135 min, departs 13:10, lands 18:50: all fail; traveller wants nonstop: AS 09:00 $482 | yes |
| ochre-pinion | meeting date unconfirmed: refundable allowed; cheapest refundable AA $324 | yes |
| oak-saffron | spouse, specific business purpose, group president approved in advance: cheapest seated B6 $198 (WN sold out) | yes |
| poplar-wick | 415 min: no business by duration; exception by Group VP of Finance with doctor's note: AF business $3,980 | yes |
| sage-tundra | 815 min allows business; traveller chooses economy: NH $1,085; incentive conditions concern the reward | yes |
| thistle-amber | 35-day rental is a car rule; 9 days' notice is soft; cheapest economy WN $269 | yes |
| quince-ember | family holiday on the company account: refuse (lines 47-48) | yes |
| rowan-slate | spouse sightseeing, no business purpose: refuse (lines 697-700) | yes |

21 of 21 non-flag scenarios agree. The read caught one wrong design note (elm-vesper said every flight is under 3
hours; the DFW leg is 210 minutes): fixed; the answer was unaffected because the traveller asks for economy.

## 6. Hosted-cap estimate

Full-handbook prompt: 46,942 bytes; about 9,300 tokens at 1.33 a word, about 11,200 on the Thornton/NJC calibration
(0.2 a character plus 1,800). A 3-call run is about 35,000 to 36,000 input tokens before the final message (about
48,000 with it): under the 65,536 cap, with room for one repeated search.

## 7. Template change requests

None needed. Observation: the skeleton's `search-flights` task text says "one-way" (Thornton); kept, since every
Standex case is one-way.

## 8. Acceptance outputs

```
$ uv run pytest -q
210 passed in 1.78s
$ uv run ruff check .
All checks passed!
$ uv lock --check
Resolved 42 packages in 4ms
$ python3 ../_template/check_shared.py .
: ok
$ nanoagent plugin inspect .
ok (exit 0)
$ nanoagent plugin pack . /tmp/standex-flight-policy.tar.gz
packed . into /tmp/standex-flight-policy.tar.gz (167272 bytes)
$ python ../_template/tools/stock_verify.py .
alder-quince         right=True score=1.00 identical=True wrong-decision-rejected=True
birch-tallow         right=True score=1.00 identical=True wrong-decision-rejected=True
cinder-moth          right=True score=1.00 identical=True wrong-decision-rejected=True
dahlia-quarry        right=True score=1.00 identical=True wrong-decision-rejected=True
elm-vesper           right=True score=1.00 identical=True wrong-decision-rejected=True
fern-cobble          right=True score=1.00 identical=True wrong-decision-rejected=True
gorse-lumen          right=True score=1.00 identical=True wrong-decision-rejected=True
hemlock-tide         right=True score=1.00 identical=True wrong-decision-rejected=True
ivy-sorrel           right=True score=1.00 identical=True wrong-decision-rejected=True
juniper-flint        right=True score=1.00 identical=True wrong-decision-rejected=True
kiln-meadow          right=True score=1.00 identical=True wrong-decision-rejected=True
larch-pewter         right=True score=1.00 identical=True wrong-decision-rejected=True
maple-onyx           right=True score=1.00 identical=True wrong-decision-rejected=True
nettle-brine         right=True score=1.00 identical=True wrong-decision-rejected=True
oak-saffron          right=True score=1.00 identical=True wrong-decision-rejected=True
ochre-pinion         right=True score=1.00 identical=True wrong-decision-rejected=True
poplar-wick          right=True score=1.00 identical=True wrong-decision-rejected=True
quince-ember         right=True score=1.00 identical=True wrong-decision-rejected=True
rowan-slate          right=True score=1.00 identical=True wrong-decision-rejected=True
sage-tundra          right=True score=1.00 identical=True wrong-decision-rejected=True
thistle-amber        right=True score=1.00 identical=True wrong-decision-rejected=True
umber-wisp           right=True score=1.00 identical=True wrong-decision-rejected=True
vetch-harbor         right=True score=1.00 identical=True wrong-decision-rejected=True
willow-gale          right=True score=1.00 identical=True wrong-decision-rejected=True
24 scenarios, 0 failures
```

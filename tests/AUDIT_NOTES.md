# Audit notes: standex-flight-policy (2026-11-24)

This is an independent audit of the build at 0543d99. I read the frozen handbook
(`pilot_work/originals/standex/frozen/standex_policy.txt`, lines 1-260 in full, then the companion, card,
non-reimbursable and exceptions sections). I then re-derived every scenario from the handbook text plus what the
agent sees (the `get_trip` record and the `search_flights` listing for the trip's route and date). I did not use
`rules.py` for that. The standards were MASTER_PLAN section 4, EDGE_CASES sections 1-3 and 5, SYNC_NOTES (4'
included), and the defect classes from the paid runs (Thornton/NJC VALIDATION.md, LSU and NJC REVALIDATION_NOTES).

## Verdict

The plugin passes after four accept-set fixes. Every decision and every primary accepted offer in the key matches
my own reading, on all 24 scenarios. No world, request or trip record changed. The fixes widen the reason, clause
and offer sets where a correct answer could fairly use a value that the key did not accept.

## Defects found and fixed

| Scenario | Problem | Fix |
|---|---|---|
| maple-onyx | The agent sees reason codes by name only. The connection passes the "within 2 hours" margins of lines 145-146, so a correct booking of it can fairly give `ALTERNATE_ROUTE_WITHIN_MARGIN`. That code was not accepted, which is the kestrel-loom class of defect. | `ALTERNATE_ROUTE_WITHIN_MARGIN` was added to the connection-booking branch of `rules.routing`. |
| rowan-slate | The trip record shows `purpose_kind: PERSONAL` (sightseeing), so a correct refusal can fairly give `PERSONAL_TRAVEL_NOT_COVERED`. Only `COMPANION_NOT_COVERED` was accepted. | `PERSONAL_TRAVEL_NOT_COVERED` was added to the companion refusal in `rules.companion`. |
| umber-wisp | The key's own approver set (SUPERVISOR or MANAGER, from lines 935-937) means this hold also waits on a sign-off. It is the "hold that also awaits a sign-off" class (NJC iron-plover), but `APPROVAL_REQUIRED` was not accepted. Nor was the section that names those approvers (EXCEPTIONS TO THIS POLICY, already in `must_keep`). | Reasons are now `UNCLEAR_POLICY_TEXT` or `APPROVAL_REQUIRED` (`rules.UNCLEAR_REASONS`). `EXCEPTIONS` was added to the clauses. |
| vetch-harbor | Same as umber-wisp. In addition, only the premium economy fare could be held, while umber-wisp (and LSU cattail-ember) hold the offer of either reading. The per-segment reading's answer is the lowest economy fare. | The hold now accepts united-premium or united-economy (cabins PREMIUM_ECONOMY or ECONOMY), `UNCLEAR_REASONS`, and clauses AIRLINE_TRAVEL or EXCEPTIONS. |

I made the changes in `src/plugin/rules.py` and `verifier/rules.py`, which are still byte-identical, and in
`tests/build_scenarios.py`. I then regenerated the scenario JSON. The two degenerate baselines are unchanged:
always-flag passes 2 and always-cheapest passes 10. Always-flag uses `NOT_NAMED` and the first clause, and both of
those were already accepted.

## The builder's "unsure" list, checked

- **juniper-flint** (accepts only Delta at the tied $228): kept. Lines 154-155 permit the choice ("at or below"),
  and the request decides (EDGE_CASES 3.17). JetBlue at the same price ignores a permitted request.
- **nettle-brine** (accepts only the 09:00 Alaska nonstop): kept. The MSP connection fails all three tests of
  lines 141-146: it saves $60, takes 135 more minutes, and leaves and lands more than 4 hours away. The traveller
  also declines it (lines 113-115). So both readings give the nonstop. The DL nonstop is dearer and leaves at
  11:30, not at the requested time.
- **ivy-sorrel** (plain economy only): kept. The request says "plain economy, nothing in between". At 599 minutes
  business is not allowed, and premium economy, though permitted, was refused by the traveller.
- **ochre-pinion** (accepts only the refundable fare): kept. Lines 130-131's "unless ... subject to known possible
  changes" applies, because the record shows the date may move and the traveller asks for a changeable fare. The
  cheapest refundable fare is AA at $324.
- **Broad approver sets on the unclear flags** (NOT_NAMED, SUPERVISOR, MANAGER, GROUP_VP_FINANCE, CFO): kept.
  Lines 935-937 send "concerns regarding the policy as it is written" to the immediate supervisor or manager, and
  lines 37-40 name who may grant exceptions. `NOT_NAMED` is lenient, since a role is named, but it fails no correct
  answer. `NONE` is still excluded, as 4' requires.
- **sage-tundra**: kept. The business fare is permitted (815 minutes) and the traveller chooses economy.
  Lines 186-189 (14 days, supervisor) condition the reward. Even read as conditions on the ticket, the
  supervisor's short-notice sign-off is on file, so the answer is BOOK on every reading. NH at $1,085 is the
  cheapest. Approver NONE or SUPERVISOR follows 4'.

## Other checks (no change needed)

- **Flags are genuinely unclear.**
  - umber-wisp: line 118 says "required to accept", while lines 113-115 say the traveller "will have the option of
    deciding" and lost savings are noted.
  - vetch-harbor: "flights with a segment of 3 hours or more" reads as the whole itinerary, but the tool output
    calls each segment a "flight", so a per-segment reading is natural too. The two readings give different
    bookings.
  - willow-gale: exactly $7,500.00 against "totaling $7,500 USD or greater" is clear. It is an approval hold, kept
    separate from "no compliant offer".
- **Twins.** fern-cobble/gorse-lumen and hemlock-tide/ivy-sorrel each differ only in scheduled minutes.
  juniper-flint/kiln-meadow differ in one fare. umber-wisp/maple-onyx differ only in the traveller's preference
  (the name and title also change). The other flag twins (nettle-brine, cinder-moth, larch-pewter, birch-tallow,
  gorse-lumen) are clear cases on the other side, but on different routes. That matches the template's
  `flag_twins` rule and the audited plugins (LSU, Blackbaud).
  - Observation: no one-fact pair sits on the $7,500 line ($7,499.99 against $7,500.00). Adding one would change
    the 24-scenario mix, so it is left as a coverage note, not a fairness defect.
  - Observation: umber-wisp cannot get a one-fact twin on the nonstop side, because changing one routing fact
    lands in the "; or" split.
- **Same-day arrival with no deadline** (the LSU tupelo-wren class): no key turns on it. In every case the keyed
  offer is either the earliest bookable seat or arrives at a time no stated event contradicts. Long-haul cases
  land the next day whichever offer is taken.
- **Lint.** The template lint passes. I also linted each request against its `must_keep` text. The only overlaps
  are the date "3rd" (dahlia-quarry, thistle-amber) and the role title "Group VP of Finance" (poplar-wick, which
  EDGE_CASES 3.6 expects to be stated exactly). The conventions are in the task instructions and tool descriptions.
- **Same-LLM fairness test (EDGE_CASES section 2):** 21 of 21 non-flag answers agree with my reading. Soft rules
  never produce a REFUSE: line 119 (14-21 days "when possible") never blocks a booking (thistle-amber,
  sage-tundra).

## Layout change (lead's request)

Stock `nanoagent plugin inspect` rejects extra root files, so `BUILD_NOTES.md` moved to `tests/` and these notes
are in `tests/` too. The two README references were updated.

## Acceptance outputs after the fixes

```
uv run pytest -q                                  210 passed
uv run ruff check .                               All checks passed!
uv lock --check                                   Resolved 42 packages
python3 ../_template/check_shared.py .            : ok
nanoagent plugin inspect .                        exit 0
stock_verify.py . (nanoagent venv python)         24 scenarios, 0 failures
```

# Validation notes: standex-flight-policy (wave 2 paid validation, 2026-11-25)

Run: `efficient_corporate_travel_agent/pilot/ladder/runs/validation_w2_2026-11-25/` (arm `full`, DeepSeek V4 Flash,
temperature 0, max_steps 6), plugin head 50ba3f2. Line numbers are lines of `src/plugin/data/policy.txt`.

## Results

| | standex |
|---|---|
| valid | **21/24 = 87.5%** |
| easy valid | 5/5 |
| by category | boundary 6/6, distractor 2/2, easy 5/5, flag 1/3, hidden 2/2, multi 4/4, refusal 1/2 |
| always-cheapest agent | 8/24 (33%), unchanged (`MAX_PASS_ALWAYS_LOWEST = 8`) |

## Every failure, classified

| scenario | category | submitted vs key | class | evidence |
|---|---|---|---|---|
| quince-ember | refusal | REFUSE, PERSONAL_TRAVEL_NOT_COVERED (right), clause NON_REIMBURSABLE; key AUTHORIZED_USAGE, CORPORATE_CREDIT_CARD or POLICY_PRINCIPLES | model slip | The reasoning names the right ground and its sections: "employees are not permitted to use company credit card for personal travel reservations ... clause could be AUTHORIZED_USAGE or NON_REIMBURSABLE. Let me pick NON_REIMBURSABLE since it's a personal expense." The NON-REIMBURSABLE section (lines 865-868) covers "personal expenses while traveling" on company business and says nothing about booking a personal trip on the company account with repayment, which is what the request tests ("I'll pay it back"); lines 47-48 and 737 state that ground. Accepting NON_REIMBURSABLE would let the refusal pass without the card rule. |
| umber-wisp | flag | BOOK Detroit connection (S5Y6-SZXA, a held offer), LOWEST_FARE, NONE; key FLAG either offer, UNCLEAR_POLICY_TEXT or APPROVAL_REQUIRED | model slip | It saw the second reading and settled it: "The traveler will have the option of deciding whether the alternative is acceptable ... This suggests the traveler can decline and pay the difference. But is that our decision? ... Given the policy strongly requires lowest logical airfare ... book the connection." Lines 113-115 (the traveller may decline, lost savings noted) against line 118 ("required to accept") is a real conflict, and the traveller declines. The twins agree with the key: maple-onyx (traveller indifferent, book the connection) and nettle-brine (connection fails every test, book the nonstop) both passed. |
| vetch-harbor | flag | BOOK United premium economy (H8PL-FXAS, a held offer), PREMIUM_ECONOMY_ALLOWED, NONE; key FLAG either United offer, UNCLEAR_POLICY_TEXT or APPROVAL_REQUIRED | model slip (borderline: a weak flag) | It weighed line 136 and set it aside: "should we consider whether economy should be chosen because policy says economy on under 3-hour segments? ... Since there's a segment of 3+ hours, premium economy allowed." The offer and cabin are one of the two held readings. Note for the lead: the handbook's own words ("flights with each segment under 3 hours", "flights with a segment of 3 hours or more", lines 136-138) treat a flight as having segments, which favours the model's whole-itinerary reading; the per-segment reading leans on the tool calling each leg a flight (AUDIT_NOTES "Other checks"). The audit judged it genuinely unclear and I leave the key. If the re-run books premium economy again, convert it to a BOOK (new id) rather than count a second slip. |

No scenario or grader defect. Nothing was changed; no accept set was widened.

## Re-run

None required. Optional: vetch-harbor once, to see whether the premium-economy booking is systematic.

## Checks at this commit

`uv run pytest -q` (210 passed), `uv run ruff check .`, `uv lock --check`, `check_shared.py`, `stock_verify.py`
(24 scenarios, 0 failures), stock `nanoagent plugin inspect .` (exit 0).



### 11.30 — September 19: prior IV rules on the full 2024–2026 population, +5/−10

This completes the earlier IV-rule comparison, separately from MAD magnitude.
All 172 selected 2024 dates were checked across all eleven ETFs: 1,816 captured
sector-days, 76 with no allowed expiry bracket (XLRE43/XLB33), none pending.
Across 421 dates there are 4,488 captured sector-days and 143 expiry gaps. The
primary analysis uses 411 research dates; ten development dates stay separate.
All new native/derived data reside in
`/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_iv_full_2024_2026_2026-09-19-v1/`.
There were 5,293 new successful ThetaData SDK data calls; original exact-parameter
caches were reused and existing raw files preserved. Captured does not mean all
minute measurements pass quote quality.

**Learning 1 — the old B06 advantage did not generalize.** Under +5 before−10
within sixty native minutes, plain B06 is 1,208/2,382 (50.7%). Falling IV in six
sectors is 729/1,454 (50.1%); falling plus downward acceleration is 315/632 (49.8%).
Allowing midpoint recovery when bid IV fails gives 341/678 (50.3%). Balanced nearby
recovery gives 328/655 (50.1%). These reject many winners without supplying a
meaningful broad B06 advantage. Capitalization weighting and confirmation during
the breakout do not repair it. Post-target givebacks never affect this score.

The original IV measurements reproduce exactly across 45,760 sector/policy events,
with zero numerical differences. The expanded evidence, not a silently changed
version of those measurements, is driving the changed assessment. Even excluding
2024, original acceleration on the expanded 2025–2026 data is 187/349 (53.6%) versus
plain B06's 685/1,302 (52.6%). The early attractive percentages are not durable
estimates for the expanded population. A 2026 H1 benefit does not appear uniformly
in other halves. Different score barriers, cohorts and VT gates remain distinct.

**Learning 2 — B07 is the simpler transfer lead.** Failed breakdown/range reclaim
with original six-sector acceleration is 96/157 (61.1%), versus 393/769 (51.1%)
unfiltered,254/539 (47.1%) definite nonqualifiers and 350/696 (50.3%) measurable.
The qualifier has 121 distinct dates and a higher observed percentage in all six
halves. First/day is 72/121 (59.5%) versus 141/283 (49.8%); spaced 60 is 82/137 (59.9%)
versus 239/470 (50.9%). Its unadjusted whole-date difference interval versus all B07
is+3.4 to+16.7 percentage points. Midpoint recovery is 100/163 (61.3%).
Guarded 50 with majority prior-session IVV weight is 68/104 (65.4%), but has 363
unknowns and the additional historical-weight proxy limitation. No thrust+B07
union was predeclared, so none was constructed retrospectively for this report.

**Learning 3 — guarded eight-sector B09 is the strongest predeclared N lead.**
The one-minute staircase's guarded 100 acceleration-in-eight rule gives 69/105
(65.7%,69 dates); guarded 50 gives 44/66 (66.7%,39 dates). Adding these executions
to thrust gives 128/197 (65.0%) and 103/158 (65.2%), versus thrust 59/92 (64.1%).
The additions do not share thrust's date/minute identities: N rises 114.1% or 71.7%.
Simple midpoint recovery without these guards adds more B09 entries but dilutes
the combined percentage to 200/332 (60.2%). The quote policy is part of the observed
candidate, not a negligible data-cleaning implementation choice.

Guarded 50's first/day union is 68/97 (70.1%) versus thrust 48/68 (70.6%); its spaced
union is 87/124 (70.2%) versus 55/81 (67.9%). Guarded 100 supplies more N but has lower
first/spaced percentages than thrust. Neither tiny pooled-rate difference proves
an accuracy gain. Union 95% rate intervals are 57.7–71.8% and 57.2–72.5%; these are
not superiority/noninferiority tests versus thrust. Both settings were already
in the frozen registry; choosing between them now still incurs selection risk.
Half-year samples are uneven: guarded 50 adds 21/30 winners in 2024 H1 but 0/1 in 2026 H2.

**Learning 4 — opening-range confirmation is a secondary, smaller N lead.**
Thrust plus midpoint-recovered six-sector-acceleration B10 is 77/120 (64.2%), adding
18 winners/28 entries. Guarded 100 is 69/106 (65.1%), adding 10/14. The spectacular-looking
standalone B10 guarded 100 rate 13/17 (76.5%) is a seventeen-entry cell, not a reliable
champion. Original eight-sector or shape diagnostics do not rescue B06. All four
conservative bid/ask-envelope rules yield zero qualifiers; their NaN rate meansN=0
after evaluating a condition, not an unfinished download.

**Learning 5 — comparable-price matching leaves a narrow falling-IV hint.**
Within-half original falling-IV matches give 223/421 (53.0%) versus 194/421 (46.1%);
global matches give 208/432 (48.1%) versus 201/432 (46.5%). Acceleration within-half
is 252/497 (50.7%) versus 247/497 (49.7%). Matching fixes rising-sector count and
uses a 10 bps median-return caliper without replacement, before outcomes are joined.
The effect's dependence on the matched subset matters; it has not yielded a broad
operational B06 improvement. The same-sector price/IV rule is 409/801 (51.1%) in
the full B06 pool. T+15 confirmation is a genuinely new entry with fresh VT and
sixty-minute scoring:83/156 (53.2%) versus all delayed B06 1,201/2,381 (50.4%).

**Learning 6 — unknown is informative and has multiple causes.** There are 741
primary recipe entries before 10:05 whose reference starts before 09:30. This is a
structural window issue, distinct from quotes or expiry brackets. The additive
coverage audit separates it from remaining unresolved quote/expiry conditions and
rejected issuer snapshots. Unknown groups retain their own outcomes. B09 guarded 50
has 1,479/2,736 (54.1%) unknown winners; B06 original acceleration unknowns are
203/365 (55.6%). Missing values are not failures or free opportunities to discard.
All eleven sectors remain in the voting denominator. Fifty reused validated issuer
bodies lack recorded HTTP status and are labeled that way, rather than claiming
historical HTTP200 evidence that was never captured.

**Verification and interpretation.** The score, native price inputs, entry recipes
and strict through-entry VT gate are unchanged. No future session-low gate is used.
There are 105 registry rules (104 at original entry and one delayed),13 families,
six halves, all/first/spaced modes, and 88 predeclared opportunity unions. All 97,656
comparison rows,1,848 union rows,312 original baseline rows and 4,056 additional
unknown-state disclosure rows reconcile. Independent feature checks cover five
policies/four descriptors and 68,000 scalar comparisons, maxerror 5.44 e−15.
Whole-date bootstrap uses 5,000 draws/seed 20260919, retains zero-event dates and
does not adjust for the many hypotheses. This is expanded descriptive research,
not an untouched holdout. Higher observed rates remain research leads.

Requested Claude Opus 5/xhigh review: **CONDITIONAL PASS** over 16 implementation
files. Medium concerns about structural/informative missingness and zero-qualifier
cells are disclosed; the metadata registration writer was replaced with a tested
durable roll-forward writer that writes its completion inventory last. Canonical
pair IDs, issuer HTTP provenance and actual prior-date checks are recorded. No
numeric result or signal threshold changed after that review. Local validation:
23 tests and Ruff; the verdict remains conditional rather than being relabeledPASS.

- [Extensive findings, all important tradeoffs and evidence links](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/FINDINGS.md).
- [Complete result tables and missingness disclosures](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/RESULT_TABLES.md).
- [Inventory of tested and explicitly untested ideas](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/IDEA_INVENTORY.md).
- [Independent review and dispositions](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/REVIEW_RESOLUTION.md).

MAD magnitude, short-tenor/term-structure, monthly-only expiry and individual
constituent surface strategies were not tested in this comparison. The older
datasets and interactive dashboard remain untouched by this isolated run.

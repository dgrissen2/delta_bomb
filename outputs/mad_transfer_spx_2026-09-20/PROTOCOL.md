# Reviewed MAD transfer and SPX study — execution contract

Authorized September 20, 2026. Implements CHARLIE_PROPOSAL.md as amended by
REVIEW_RESPONSE.md and the conditional recheck in b09_mad_followup_plan_2026-09-20.
Those documents and input hashes are preserved in the outcome-free freeze.

## Scope and search disclosure

Use January 2025–September 18, 2026, the 239 existing non-development research
dates, and unchanged B09/B07/B05 entries. SPX measurements extend to 2024 but the
matched sector experiment does not. Previous work inspected 105 IV rule labels
and 48 MAD cells. The reviewer already saw B09 sign controls (2544 and 1933
qualifiers); reconcile them, never describe this as untouched holdout evidence.

Four primary transfer cells: B07/S4, B07/F4, B05/S4, B05/F4. Six diagnostic
controls: sign4 and sign_falling4 on B09, B07 and B05. Existing B09 S4/F4 are
references. One separately declared SPX_F rule on B09 and its OR with F4.
No other parent, threshold, tenor, delta, sector subset, or retention optimization.

## Fixed measurement, entry and outcome rules

S4: at least four of eleven ETFs have M>1. F4: at least four of the same eleven
each have M>1 and b2<−1e−12. sign4 uses a<0; sign_falling4 adds b2<−1e−12.
Use the identical source eligibility for sign and magnitude (finite scored M),
so this is a fixed-rule/selectivity comparison, not isolated normalization value.
Known-false conjunctions are false even if the other field is unknown. Basket
yes requires four observed positive votes; definite no requires positive+unknown
votes<4; everything else is unknown. No imputation/reweighting.

SPX_F: native SPXW 30-calendar-day ATM IV, M>1 and b2<−1e−12. OR uses three-valued
logic: either yes => yes; both no => no; otherwise unknown. No ETF proxy.
All scores use exact T−1 for entry T. Every source lies in T−30…T−1. Endpoint
blocks follow the source calibration: (end_min−570)//60, i.e. blocks anchored
at 09:30, not integer clock hours. Calibration dates are strictly prior.

Require native prior RTH lows and entry open strictly above same-date VT. Audit
the flag against native prices before attaching outcomes, including excluded
candidates. Never require future prices to remain above VT. Deduplicate each
parent by date and entry minute, preserving its original causal trigger.

Only target_first wins: +5 before −10 within the existing 60 native minute bars
including entry. Adverse_first, neither and ambiguous remain in N. Reuse unchanged
outcomes and verify native first-touch labels. Ignore post-target givebacks.

## Frozen diagnostics

- All entries, first qualifying per day, greedy 60-minute spacing; filter before
  thinning, chronological with a daily reset. Corresponding baseline policy.
- Pooled and completed-half pooled estimates, all four halves separately. Partial
  2026 H2 stays visible. Target/adverse/neither/ambiguous, N/dates, retained/excluded
  winners, coverage and unknown groups. No composite optimizer or new N floor.
- One all-eleven-observed sensitivity: finite M, a and b2 for all eleven; use the
  same rules and its restricted parent. No optimized ETF subset.
- Same-selected-date parent for every rule. Within-date/endpoint-block yes-versus-
  definite-no differences, only two-sided strata; average blocks equally within
  date and dates equally. Report removed strata/events and remaining N/dates.
- B07/B05 S4/F4 split by whether a B09 qualifier under the corresponding rule
  exists in that date/block, and exact-timestamp overlap. Block absence is not
  out-of-sample evidence. No combined parent portfolio or summed opportunity N.
- SPX pre-outcome entry participation and coverage by half/block. Definite 2x2
  groups on the jointly measurable parent; all five unknown combinations also
  published. F4/SPX/OR accuracy comparisons on the same measurable parent.
  OR additions split into sector-definite-no and sector-unknown. Compare the
  SPX-positive/sector-negative subset to SPX-negative/sector-negative and the
  whole jointly measurable sector-negative group; never claim selectivity-matched
  information-source attribution. Also report full-parent and all-eleven results.
- Every ETF entry gap gets a reason from unchanged daily/window source receipts:
  no permitted expiry bracket, recorded provider issue, or rejected current
  window. Unknown is not a negative vote. Do not assume refetch resolves gaps.

Uncertainty: 5000 shared whole-date resamples of all 239 research dates, seed
20260920. Reapply no outcome-dependent rules; existing deterministic spacing is
within each original date. Report rate and uplift intervals versus full/restricted
parent, definite no, measurable parent, and sign control as applicable. For the
within-block diagnostic resample date contributions, retaining equal date weight.
No interval for fewer than two contributing dates or a constant binary outcome.
Disclose finite bootstrap draws. Intervals are descriptive, unadjusted for prior
selection and cross-day dependence. Half-year signs do not confer validation;
sparse/wide-interval and zero cells may be underpowered/uninformative.

## Data and reproducibility

New derived data only in
/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1.
Code, protocol and findings live in this project slug. Preserve originals and
unrelated changes. No new market-data request or measurement-policy changes.
Freeze source/code/protocol hashes and outcome-free classifications, coverage,
and native VT checks before joining outcomes. Fail on source changes.
Local independent-formula/scalar checks are verification, not a new Claude review.
Document results and central dictionary/changelog. No deployment or dashboard edit.

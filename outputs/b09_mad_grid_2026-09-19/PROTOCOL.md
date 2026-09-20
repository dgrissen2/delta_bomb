# B09 sector IV MAD grid — frozen exploratory protocol

User authorized both definitions and the fixed grid before outcomes were calculated.
This is a descriptive optimization on previously examined dates, not an untouched
holdout or a claim of future accuracy. No collection, recalibration, price-entry
change, option-return model, post-target reversal test, or dashboard change.

## Inputs and population

- Read the eleven exact-calibration sources in the all-sector source registry from
  sector_iv_mad_remaining_2025_2026_2026-09-19. Verify all registered file hashes.
- Scope January 2, 2025–September 18, 2026. Full 2024 MAD scores are unavailable;
  late-2024 observations supply the existing sixty-session warmup only.
- Use unchanged B09 native-minute staircase events and +5-before-minus-10 outcomes
  from branch_b_stop10_2026-09-19-v1, deduplicated by variant/date/known_min.
- Require the existing strict causal always_above flag: all prior RTH lows and
  the entry open strictly above that day's VT. Never condition on the future day.
- Exclude development_10. Primary parent has 3,141 entries across 178 active dates.
  Retain the full selected research-date population, including zero-entry dates,
  for whole-date uncertainty calculations.

## Two families, exactly 48 cells

For entry at minute T use the stored endpoint T−1: the existing thirty-minute
window T−30…T−1. This is an explicit change from old B06 context ending T−6.
No nearest endpoint substitution. All quote sources must lie inside the window;
none may exceed T−1. The baseline ends before the current session.

M = −acceleration / (1.4826 × historical MAD). It is signed, zero-centered,
scaled-MAD magnitude, not a median-centered z-score, percentile, probability or
bid/ask-resolved estimate. Positive M is downward acceleration. All existing
measurement policies, history weighting, minimum support and quote guards stay fixed.

- signed: a sector qualifies when finite M > k.
- falling: a sector qualifies when finite M > k AND b2 < −1e−12.
- k in {1,2,3,4}; required sector count b in {4,5,6,7,8,9}.
- Count all eleven fixed sectors, equally. Equality to k is NOT an exceedance.
- A known-false conjunct is false even if the other conjunct is unknown.
- Yes if observed qualifying sectors >= b; no if qualifiers + unknowns < b;
  otherwise unknown. Do not reweight, reduce the denominator, or fill gaps.

## Outcomes and comparisons

Only target_first is a win. adverse_first, neither and ambiguous remain in N.
Keep the original 60 native-minute horizon, entry included. First +5 ends the
success question. Reuse and verify the existing outcome hash rather than rescore.

Report each cell against plain B09, definite no and the rule's measurable parent
(yes plus no). Unknowns are separate. Report retained/discarded winners and events,
active dates, signal/day concentration, plus the additional signed-only entries
excluded by the falling condition. Filter before chronological thinning.
Sensitivity policies: all entries, first qualifying entry per date, and greedy
60-minute spacing within date. Spacing uses timestamps only, not earlier outcomes.

## Stability and high N, specified before grid outcomes

Publish every cell for 2025 H1, 2025 H2, 2026 H1, partial 2026 H2 and pooled.
Use ONLY the three completed halves for stability selection. Partial 2026 H2
is a separate descriptive check, not a pristine holdout.

For each rule record worst completed-half hit rate, worst uplift versus the
same-half plain B09 policy, unweighted half-rate standard deviation, smallest
half-year N and active-date count. Flag whether every completed half has entries
and strictly positive observed uplift. Rank those candidates by completed-half N
descending, then worst-half accuracy descending, then rule identifier. No minimum
sample or accuracy floor is chosen after seeing results. Sparse cells stay visible.
Also publish the nondominated tradeoff set in completed-half N, worst-half accuracy
and worst-half uplift. Do not force one weighted composite or silently relax the
positive-uplift criterion if no candidate meets it. Inspect neighboring cells.

Whole-date bootstrap: 5,000 draws, seed 20260919, shared draws for all rules and
parent comparisons, all selected eligible dates including zero-event dates. Report
95% descriptive intervals for pooled rates and uplift; these are not adjusted for
searching 48 cells, prior research, or cross-date dependence. Sparse/no-variation
groups receive no misleading precision claims. Stability selection is exploratory.

## Artifacts and review

New derived data only under central_trade_data/thetadata/b09_mad_grid_2026-09-19-v1.
Code, protocol and findings in this separate project slug. Original data, registries,
dashboard and unrelated uncommitted work remain untouched. No commit requested.
Freeze input/code hashes and outcome-free memberships before attaching outcomes.
Verify boundary/missingness/timing rules with tests and replay all memberships with
an independently written scalar implementation. Reconcile all summary partitions,
nesting, inherited parent counts and source hashes.

Claude review was requested. This side conversation prohibits separate sub-agents,
including launching an independent Claude reviewer process. Review status must remain
NOT RUN / AWAITING INDEPENDENT REVIEW, never PASS or a fabricated tooling failure.
The canonical Charlie persona was applied in-thread at the planning stage; this was
not a fresh independent reviewer run. The user explicitly approved testing both gates.

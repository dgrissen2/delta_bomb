# Combine the three existing opportunity expansions

Authorized September 20, 2026, after the three separate expansion results were
known. This is one fixed additional exploratory comparison, not a holdout test.

At each native SPX entry timestamp accept any of:
1. Existing B09 sector F4 OR SPX baseline.
2. Existing B05 F4.
3. Existing B09 five-endpoint persistence (same qualifying sectors still falling,
   or the equivalent SPX route; endpoints T-5 through T-1).
4. Original B07 six-sector acceleration, retaining its original measurement clock.

OR these frozen admission flags; deduplicate by Eastern date and minute. Preserve
all matching rule identities. No threshold changes, additional gates, application
of persistence to B05/B07, new outcomes, or new volume/skew condition. Reuse the
239 selected research dates in 2025 through September 18, 2026, unchanged strict
causal above-VT admission and +5 before -10 within 60 native bars including entry.
Only target_first wins. Adverse, neither and ambiguous remain in the denominator.

Freeze source hashes and the deduplicated, outcome-free membership before joining
outcomes for this combined rule. Known component results are already available;
this freeze does not undo that selection. Check original counts reconcile.

Primary comparison: no-spacing combined union versus original B09 OR; also show
all genuinely added entries and mutually exclusive combinations of source rules
among those additions. Do not credit a shared timestamp to multiple routes or
infer causal contributions from the overlap groups. Retain every half-year,
including sparse partial 2026 H2. Show active/new dates and median daily counts.

Sensitivity: first/day and greedy 60-minute spacing, resetting each day. Apply
policy to the complete union, not each component separately. Report newly kept
and displaced baseline executions and winners. The raw added set under no spacing
is different from these policy changes. No optimization of policy or rule subset.

Uncertainty: 5,000 paired whole-date resamples within each period, seed 20260920,
including all research dates with zero signals. Reuse the existing interval
implementation to maintain comparability. Show accuracy and combined-minus-base
intervals. These do not adjust for prior search or between-date dependence and
cannot establish equal accuracy by containing zero. Also show leave-one-date-out
sensitivity and added-entry outcomes on new versus already baseline-active dates;
the latter is retrospective and never an entry-time gate.

Verification: test duplicate route retention and conflicting outcomes, independently
reconstruct membership and policies, reconcile summary/overlap/policy arithmetic,
and replay the combined union against original native SPX/VT source records.
All new tables go to central_trade_data/thetadata/b09_combined_expansion_2026-09-20-v1;
code and findings remain in this project. Original data and unrelated concurrent
work are unchanged. No new collection or independent reviewer launch.

# Existing-cache relative volume across the current working set

Authorized September 20, 2026, after consolidation commit e5259b4 and its push.
This is a descriptive extension of an already examined feature, not an untouched
holdout. No new download, IV calculation, parent-signal search, threshold sweep,
or selection of a winning threshold is part of this study.

## Fixed cohorts and outcome

Reuse the immutable combined study's 685 unique date/minute entries and 239
research dates in 2025–September 18, 2026. Report the four original flags separately
(baseline B09 sector F4 OR SPX; B05 F4; B09 five-minute persistence; original B07
six-sector acceleration), and their deduplicated union. Preserve causal above-VT
admission and native high/low +5 before entry−10 within 60 minute bars including
entry. Neither and ambiguous outcomes remain in N. Primary analysis has no spacing.
No outcome is changed by a reversal after reaching +5.

## One existing feature

At entry T, sum cached SPY volume at T−5 through T−1. Divide by the median of the
same five clock minutes across exactly 60 strictly preceding source-calendar
sessions. Require five actual finite nonnegative observations in the current
window and in every reference window, with positive reference median.

- High activity: RVOL > 1, the previous experiment's fixed threshold.
- Ordinary activity: finite RVOL <= 1, including exactly 1.
- Unknown: current date/window unavailable, incomplete reference history, or
  nonpositive reference. Never impute missing bars or classify unknown as ordinary.

The existing Databento XNAS.ITCH cache is Nasdaq-venue SPY share volume, not
consolidated SPY volume, SPX volume, or signed buying pressure. It ends June 11,
2026. It cannot answer the 2026 H2 question. Some earlier windows also lack complete
60-session reference histories; report their separate causes and date/time ledger.
Reuse the previous feature-builder and reconcile every overlapping B09 timestamp.
Verify all new feature values independently against direct raw five-bar sums.

## Comparisons specified before new outcome tables

For each cohort and each half-year plus pooled, report full cohort, observed
volume, high, ordinary and unknown counts, wins, stop/timeout counts and accuracy.
Compare high versus ordinary within the same observed population. Also show high
versus all observed entries, fraction of observed signals and winners retained,
and successful opportunities excluded. Unknowns do not count as volume rejects.

Use 5,000 paired whole-date multinomial bootstrap draws (seed 20260920), retaining
zero-entry dates in each of the original research calendars, for rates and their
differences. Omit denominator-zero draws and report finite draw counts. These CIs
address dependence within a day, not earlier rule searches or between-day regimes.
Empty or single-active-day estimates do not get an informative CI.

As an existing confounding diagnostic, compare high versus ordinary inside the
same date and 09:30-anchored one-hour block of the last completed minute T−1.
Keep only blocks containing both states. Average block differences within date,
then equally across dates; bootstrap dates and report surviving entries/dates.
Also show pre-entry 30-minute SPX return and realized movement by state. This is
a different, limited-support estimand, not a causal effect or full price match.
Inspect half-year direction and pooled leave-one-date-out high-minus-ordinary
differences without retuning anything. Five cohorts overlap and are not independent
replications. No inverted low-volume rule will be promoted from this experiment.

## Reproducibility

Freeze source, reused implementation, protocol and outcome-free feature hashes
before joining known outcomes. Verify the previous feature and outcome receipts.
Save all tabular artifacts under central_trade_data/thetadata/
b09_working_set_volume_2026-09-20-v1; code and interpretation live in this folder.
Update the central changelog/dictionary and project memory/learning notebook.

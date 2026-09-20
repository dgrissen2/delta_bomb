# Current Branch B working set: consolidated findings

September 20, 2026. Explicitly designated by the user as the current working set.
The following consolidates the completed union, endpoint-distribution, confidence-
interval and day-influence work. It supersedes earlier working-set choices, while
preserving earlier research as historical evidence. More opportunities at a similar
observed hit rate is encouraging; forward accuracy equivalence is not established.

The unchanged objective is native SPX +5 before entry−10 within 60 minute bars,
using highs/lows rather than closes for touches. Post-target declines do not undo
wins. The primary policy has no spacing; 239 selected research dates span January
2025–September 18, 2026, under strict causal above-VT admission.


## Five current cohorts

| Current cohort | Winners/signals | Accuracy | Source flag in combined ledger |
|---|---:|---:|---|
| B09 + sector F4 OR SPX | 198/318 | 62.3% | baseline |
| B05 + F4 alone | 70/112 | 62.5% | b05_candidate |
| B09 five-minute IV persistence | 308/492 | 62.6% | persistence_candidate |
| B07 original six-sector acceleration | 57/91 | 62.6% | b07_candidate |
| All combined, duplicates removed | 427/685 | 62.3% | Entire deduplicated ledger |

B09 is the existing one-minute staircase in bullish five-minute context. B05
is the existing stall/reclaim. F4 means at least four sectors pass the fixed MAD>1
cooling rule while IV is already falling. Baseline B09 accepts that sector rule OR
the existing SPX falling-IV MAD confirmation. Persistence permits one common
qualifying endpoint T−5…T−1, requiring the same sectors still to have valid falling
IV at T−1; SPX is its equivalent alternative. This includes all baseline entries.
Missing current measurements remain unknown. Do not pool sector votes from different
earlier minutes or extend this persistence rule to B05/B07 without a new request.

B07 is the original failed-breakdown/reclaim plus six-sector falling/downward IV
acceleration, preserving its older quote policy and T−35…T−6 reference. It is not
B07 MAD-F4. Standalone counts differ from additions to baseline: B05 adds105/64wins,
B07 adds90/56wins, persistence adds174/110wins. Two overlapping addition timestamps
leave367distinct additions with229wins; combined is685, not687.

## Requested neither-barrier distribution snapshot

This table is CONDITIONAL on neither +5 nor −10 being touched during the hour.
Finished-positive percentages are not the original strategy accuracy.

| Cohort | Neither cases | Finished positive | Median move | Mean move | 10th–90th percentiles |
|---|---:|---:|---:|---:|---:|
| B09 + F4 OR SPX | 43 | 51.2% | +0.07 | −0.50 | −5.04 to +2.43 |
| B05 + F4 alone | 5 | 40.0% | −2.14 | −0.73 | −3.43 to +2.84 |
| B09 five-minute IV persistence | 73 | 46.6% | −0.26 | −0.68 | −5.25 to +2.96 |
| B07 six-sector acceleration | 15 | 46.7% | −0.77 | −0.83 | −4.48 to +2.74 |
| All combined | 92 | 46.7% | −0.33 | −0.70 | −5.17 to +3.64 |

All moves are SPX points. These cohorts overlap. Combined neither cases are92
unique entries;43positive,48negative,1flat. B05's five cases are especially thin.



## Combined entry set, overlap, half-years and spacing

Source: [FINDINGS.md](/Users/dgrissen/Dev/delta_bomb/outputs/b09_combined_expansion_2026-09-20/FINDINGS.md).

September 20, 2026. **Combining all three expansions gives 427 winners / 685
distinct signals = 62.3%, versus 198/318 = 62.3% for the original B09 OR rule.**
That adds 367 entries and 229 winners, with 62.4% accuracy among the additions.
The no-spacing historical result supports substantially more opportunities at a
similar observed rate; it does not prove future accuracy is preserved.

### Exactly what was combined

At each entry minute accept B09 with sector F4 OR SPX confirmation, OR existing
B05 with F4, OR B09 with the fixed five-endpoint IV persistence rule, OR original
B07 with six-sector acceleration. The persistence route already includes baseline
B09 OR. Deduplicate by Eastern date/minute while retaining every qualifying route.

This combines accepted entry sets. It does not require B05, B09 and B07 to agree;
it does not apply the relaxed IV timing to B05/B07; it does not add volume or skew.
Each constituent keeps its existing definition, including B07's older measurement
clock. There is no new threshold sweep or selection of an optimal subset.

Same 239 selected research dates, January 2025–September 18, 2026; strict causal
above-VT at entry, +5 before -10 within 60 native minute bars including entry.
This is not the full exchange calendar. All non-target outcomes remain in N.
Above-VT uses all observed session lows before entry and entry open, not future
session prices. Later post-target reversals do not change a winner.

### Primary result: no spacing

| Cohort | Winners / signals | Accuracy | 95% whole-date interval | Active dates |
|---|---:|---:|---:|---:|
| Original B09 F4 OR SPX | 198/318 | 62.3% | 55.6–68.4% | 121 |
| All three expansions combined | 427/685 | 62.3% | 57.5–66.8% | 163 |
| Genuinely added entries only | 229/367 | 62.4% | 56.8–67.9% | 153 |

The combined count rises 115.4%, with 42 additional active dates. Median signals
per research date rise from 1 to 2; per active date, from 2 to 3. Added-only active
dates include 111 dates already active under baseline and 42 entirely new dates.

Combined-minus-baseline accuracy is +0.07 percentage points, with a paired 95%
whole-date interval of -3.82 to +4.04 points. This does not establish noninferiority.
The pooled union's narrower interval reflects these historical observations under
the resampling assumptions, not independent new data or a correction for selection.

Outcome mix: baseline 198 target / 77 adverse / 43 neither; combined 427 target /
166 adverse / 92 neither; additions 229 target / 89 adverse / 49 neither. None of
these selected executions is ambiguous. We retain the user's +5-first objective.

### Where the duplicates were

Separate experiments supplied 105 B05 additions, 174 persistence additions and
90 B07 additions: 369 memberships, but **367 distinct new timestamps**.

| Mutually exclusive source among additions | Winners / signals | Accuracy |
|---|---:|---:|
| B05 only | 63/104 | 60.6% |
| B09 persistence only | 110/173 | 63.6% |
| B07 only | 55/88 | 62.5% |
| B05 and B07 together | 1/1 | 100% |
| B09 persistence and B07 together | 0/1 | 0% |
| Total distinct additions | 229/367 | 62.4% |

One shared addition was a winner; the other reached neither barrier. Thus sum of
separate added winners 64+110+56=230 loses one duplicate winner, leaving 229.
Baseline plus additions is 318+367=685 and 198+229=427. The single-observation
overlap cells are accounting details, not evidence for an agreement filter.

### Every half-year

| Half-year | Baseline winners/N | Baseline rate | Combined winners/N | Combined rate | Combined 95% interval | Added winners/N |
|---|---:|---:|---:|---:|---:|---:|
| 2025 H1 | 58/96 | 60.4% | 127/205 | 62.0% | 53.7–69.5% | 69/109 |
| 2025 H2 | 78/130 | 60.0% | 159/268 | 59.3% | 51.3–66.9% | 81/138 |
| 2026 H1 | 50/74 | 67.6% | 115/173 | 66.5% | 57.7–74.1% | 65/99 |
| 2026 H2 through September 18 | 12/18 | 66.7% | 26/39 | 66.7% | 41.9–85.4% | 14/21 |

No-spacing combined rates stay near the baseline in each half, with more signals.
The partial final half still has only 12 active dates and should not establish
stability. Complete per-half intervals, differences, outcomes, medians and research
date denominators are in ALL_RESULTS.md and the central summary.csv.

### Chronological spacing changes the tradeoff

| Policy | Baseline winners/N | Baseline accuracy | Combined winners/N | Combined accuracy |
|---|---:|---:|---:|---:|
| All entries | 198/318 | 62.3% | 427/685 | 62.3% |
| First qualifying entry each day | 70/121 | 57.9% | 95/163 | 58.3% |
| At least 60 minutes since last accepted entry | 107/175 | 61.1% | 191/327 | 58.4% |

The full union is thinned chronologically with a daily reset. Under 60-minute
spacing, 184 executions/108 winners are newly selected relative to the spaced
baseline, while 32 baseline executions/24 winners are displaced: net +152 entries
and +84 winners. Newly selected executions can include baseline-qualified entries
that the old spacing policy skipped, so these are policy changes, not the raw
367 additions. First/day similarly adds 76/45 and displaces 34/20, net +42/+25.

The spaced accuracy difference is -2.73 points, with paired date interval -8.48
to +3.23 points. Combined spaced rates by half are 60.9%, 52.5%, 65.6%, and 50.0%.
2025 H2 is the weakest completed half; do not hide it behind the pooled count.
No spacing remains the declared primary comparison; neither policy was optimized.

### Are these new market conditions or more entries on similar days?

Of the 367 additions, 279 occur on dates with a baseline entry and hit 189/279 =
67.7%. The other 88 occur on 42 entirely new dates and hit 40/88 = 45.5%.
The new dates' half-year results are 12/23, 10/30, 11/24 and 7/11.

This means the strong pooled expansion is concentrated on already-active dates.
It does not mean a live rule can simply discard the weaker group: a baseline
signal may occur later that day. This is a retrospective diagnostic, never a
causal admission gate, and these subgroup rates remain uncertain.

Removing each research date separately leaves the combined pooled rate at
61.8–62.8%; the top five winning dates contribute 49/427 = 11.5% of winners,
and the largest contributes 13. The baseline deletion range is 61.3–63.1%.
These are sensitivity ranges, not confidence intervals or independent trials.

### Confidence and verification

Five thousand paired whole-date bootstrap draws per period, seed 20260920, include
research dates with zero entries and preserve within-date clustering. They do not
adjust for earlier 105-rule/48-cell searches, selection of these components after
seeing their outcomes, or dependence across dates. This additional union test is
exploratory. No new IV-versus-price matching, volume test or skew measurement ran.

Four boundary tests pass, covering cross-parent duplicates, retention of baseline
membership, conflicting outcomes and missing outcomes. Ruff passes. A separate
local verification implementation reconstructs all 685 memberships, replays all
685 native SPX entry/VT/first-touch paths with complete minutes, verifies all 239
native source hashes, checks 35 summary rows, 15 policy changes, 19 route-pattern
rows, 10 date-novelty rows and 956 day deletions, and independently reproduces the
pooled paired bootstrap. All 60 prior component summary cells reconcile exactly.

The prior Claude review concerned the proposal; this new union has local checks,
not a new independent reviewer approval. Original research and concurrent files
are unchanged. No market-data calls, option-profitability claims or dashboard edits.

Data and exact per-entry route labels:
`/Users/dgrissen/Dev/central_trade_data/thetadata/b09_combined_expansion_2026-09-20-v1`.


## Unresolved entries: signed sixty-minute endpoint distributions

Source: [FINDINGS.md](/Users/dgrissen/Dev/delta_bomb/outputs/b09_timeout_endpoints_2026-09-20/FINDINGS.md).

September20,2026. The requested subset touches **neither entry+5 nor entry-10**
anywhere in the original hour, measured using native minute highs/lows. It excludes
both target-first and adverse-first entries. The final result is the close of
the last minute in that hour minus entry open, in signed SPX points.

**For all rules combined, 92/685 entries (13.4%) reached neither barrier.** They
finished at a median of **-0.33 points**, mean **-0.70**, and a 10th–90th percentile
range of **-5.17 to +3.64**. Of those92 entries,43 ended positive,48 negative,
and1 flat. These are the unresolved entries' endpoints, not a revised hit rate.

### Each requested rule

No spacing, unchanged239 selected research dates in2025–September18,2026 and
strict causal above-VT admission. The combined set counts each date/minute once.

| Rule | Neither / all signals | Finished positive | Mean points | Median points | 10th percentile | 90th percentile | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B09 + sector F4 OR SPX | 43/318 | 22/43 (51.2%) | -0.50 | +0.07 | -5.04 | +2.43 | -6.75 | +4.23 |
| B05 + F4 alone | 5/112 | 2/5 (40.0%) | -0.73 | -2.14 | -3.43 | +2.84 | -3.75 | +3.82 |
| B09 with five-minute IV persistence | 73/492 | 34/73 (46.6%) | -0.68 | -0.26 | -5.25 | +2.96 | -7.48 | +4.82 |
| B07 + original six-sector acceleration | 15/91 | 7/15 (46.7%) | -0.83 | -0.77 | -4.48 | +2.74 | -6.12 | +4.09 |
| All combined, duplicates removed | 92/685 | 43/92 (46.7%) | -0.70 | -0.33 | -5.17 | +3.64 | -7.48 | +4.82 |

The median is near entry for baseline, persistence and combined. Every cohort's
sample mean is modestly negative. B05 has only five observations; its median and
percentiles should not establish a different behavior. The five standalone B05
endpoints are -3.75,+1.36,-2.14,+3.82,-2.94 points in date order.

Negative/flat/positive counts are respectively21/0/22 for baseline,3/0/2 forB05,
38/1/34 for persistence,8/0/7 forB07,48/1/43 combined. These cohorts overlap and
cannot be summed. The92 combined neither entries span57 active dates. The baseline
43 span34 dates, B05five span5, persistence73 span47, and B07fifteen span12.

### Combined distribution in fixed buckets

| Final SPX move | Count | Percent |
|---|---:|---:|
| -10 to below -7.5 | 0 | 0.0% |
| -7.5 to below -5 | 13 | 14.1% |
| -5 to below -2.5 | 13 | 14.1% |
| -2.5 to below 0 | 22 | 23.9% |
| 0 to below +2.5 | 30 | 32.6% |
| +2.5 to +5 | 14 | 15.2% |

The0-to+2.5 bucket includes the one exactly-flat endpoint. By construction no
selected entry may finish at or outside the original barriers; observed endpoints
range from-7.48 to+4.82. A positive endpoint below+5 remains an original non-win.

![Distributions for all five requested cohorts](/Users/dgrissen/Dev/delta_bomb/outputs/b09_timeout_endpoints_2026-09-20/endpoint_distributions.png)

### Half-year sensitivity of the combined unresolved subset

| Period | Neither N | Active dates | Mean | Median | Negative / flat / positive |
|---|---:|---:|---:|---:|---:|
| 2025 H1 | 21 | 12 | -2.65 | -2.55 | 17/0/4 |
| 2025 H2 | 53 | 31 | -0.22 | +0.26 | 23/1/29 |
| 2026 H1 | 16 | 12 | +0.25 | +0.37 | 7/0/9 |
| 2026 H2 through September18 | 2 | 2 | -0.89 | -0.89 | 1/0/1 |

The pooled mild loss is not a stable half-year estimate. The partial last half
has only two unresolved cases. All five cohorts' per-half distributions and
histogram counts are preserved in ALL_RESULTS.md and the central summary tables.

### Exact clock and verification

Entry is open(T); the hour comprises native interval-start labels T…T+59.
The endpoint is close(T+59), the boundary T+60 under the original convention,
not close of the bar labeledT+60. Every selected path has60consecutive distinct
finite, positive, correctly ordered native OHLC bars. No data filling or inference.

Reused the existing validated path and linear-quantile routines. Independently
checked all92paths directly for high<entry+5 and low>entry-10, their exact endpoint
differences, complete session-prefix minutes and causal above-VT eligibility.
Native source hashes match on57used dates; frozen combined event/calendar hashes
match. All43baseline endpoints match the prior B09 path-distribution output exactly.

Independent scalar checks reconcile positive/negative/flat counts, means and
linear p10/p25/median/p75/p90 values in all25summary groups, and all150fixed-bin
counts. All source hashes were rechecked after execution; Ruff passes. The chart
was visually inspected. This is local descriptive verification, not a new
independent review or independent market sample. Percentiles describe the sample;
they are not confidence intervals. Unspaced signals can share the same price path.

Data: `/Users/dgrissen/Dev/central_trade_data/thetadata/b09_timeout_endpoints_2026-09-20-v1`.
`events.csv` gives every date, entry time, horizon-end timestamp, final move and
rule flags. `minute_paths.parquet` preserves the5520native supporting rows.
No provider calls, signal changes, threshold changes, or option-payoff estimates.


## Complete outcome mix with winner-rate confidence intervals

Source: [TABLES_WITH_CI.md](/Users/dgrissen/Dev/delta_bomb/outputs/b09_outcome_stability_2026-09-20/TABLES_WITH_CI.md).

All percentages use all signals in the row. Endpoint buckets include only neither-barrier cases. No spacing. Confidence intervals use whole-date resampling, not independent-signal trials.

### Baseline

| Half | Winners/signals | Win % | 95% CI | Stop % | −7.5 to <−5 | −5 to <−2.5 | −2.5 to <0 | Flat | >0 to <+2.5 | +2.5 to <+5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025_H1 | 58/96 | 60.4% | 48.0–70.9% | 27.1% | 2.1% | 2.1% | 5.2% | 0.0% | 3.1% | 0.0% |
| 2025_H2 | 78/130 | 60.0% | 49.7–69.8% | 22.3% | 1.5% | 1.5% | 3.1% | 0.0% | 10.0% | 1.5% |
| 2026_H1 | 50/74 | 67.6% | 55.1–78.5% | 23.0% | 1.4% | 1.4% | 2.7% | 0.0% | 1.4% | 2.7% |
| 2026_H2 | 12/18 | 66.7% | 0.0–88.9% | 27.8% | 0.0% | 0.0% | 0.0% | 0.0% | 5.6% | 0.0% |
| pooled | 198/318 | 62.3% | 55.6–68.4% | 24.2% | 1.6% | 1.6% | 3.5% | 0.0% | 5.7% | 1.3% |

### Combined

| Half | Winners/signals | Win % | 95% CI | Stop % | −7.5 to <−5 | −5 to <−2.5 | −2.5 to <0 | Flat | >0 to <+2.5 | +2.5 to <+5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025_H1 | 127/205 | 62.0% | 53.7–69.5% | 27.8% | 2.4% | 2.9% | 2.9% | 0.0% | 2.0% | 0.0% |
| 2025_H2 | 159/268 | 59.3% | 51.3–66.9% | 20.9% | 2.6% | 1.5% | 4.5% | 0.4% | 7.1% | 3.7% |
| 2026_H1 | 115/173 | 66.5% | 57.7–74.1% | 24.3% | 0.6% | 1.2% | 2.3% | 0.0% | 2.9% | 2.3% |
| 2026_H2 | 26/39 | 66.7% | 41.9–85.4% | 28.2% | 0.0% | 2.6% | 0.0% | 0.0% | 2.6% | 0.0% |
| pooled | 427/685 | 62.3% | 57.5–66.8% | 24.2% | 1.9% | 1.9% | 3.2% | 0.1% | 4.2% | 2.0% |

No unresolved entry ends between −10 and −7.5, so that zero column is omitted. 2026_H2 is partial through September18; pooled is the total. Percentages may not sum exactly to100 after rounding.

Intervals use5000whole-date resamples,seed20260920. Baseline2026H2 has4999finite replicates and one zero-signal replicate, omitted; every other row has5000. These intervals do not adjust for earlier searches or between-date dependence.


## Charlie interpretation, confidence and whole-day influence

Source: [FINDINGS.md](/Users/dgrissen/Dev/delta_bomb/outputs/b09_outcome_stability_2026-09-20/FINDINGS.md).

September20,2026. Completed in the requested order: confidence intervals added
to the full original outcome tables, local canonical Charlie interpretation,
then a whole-day removal recount of the full outcome mix.

**The combined rule preserves the observed pooled outcome mix and survives losing
any individual day. The partial2026H2 result is fragile.** This does not establish
that future accuracy is unchanged or that685signals are independent observations.

### Full-sample confidence intervals, before removing days

The [updated tables](/Users/dgrissen/Dev/delta_bomb/outputs/b09_outcome_stability_2026-09-20/TABLES_WITH_CI.md) retain the prior winner/stop/negative/flat/
positive columns and add95%winner-rate intervals. All percentages use all signals
in each row, with neither-only final-price buckets, no spacing and causal above-VT.

| Half | Baseline winners/N | Baseline rate | Baseline95%CI | Combined winners/N | Combined rate | Combined95%CI |
|---|---:|---:|---:|---:|---:|---:|
| 2025H1 | 58/96 | 60.4% | 48.0–70.9% | 127/205 | 62.0% | 53.7–69.5% |
| 2025H2 | 78/130 | 60.0% | 49.7–69.8% | 159/268 | 59.3% | 51.3–66.9% |
| 2026H1 | 50/74 | 67.6% | 55.1–78.5% | 115/173 | 66.5% | 57.7–74.1% |
| 2026H2partial | 12/18 | 66.7% | 0.0–88.9% | 26/39 | 66.7% | 41.9–85.4% |
| Total | 198/318 | 62.3% | 55.6–68.4% | 427/685 | 62.3% | 57.5–66.8% |

Five thousand paired whole-date bootstrap draws per period,seed20260920, include
zero-entry research dates. Each sampled date brings all its signals, preserving
within-day dependence. This does not account for prior searches or dependence
between days. All ten intervals independently reproduce prior combined-study
intervals; these are not new independent evidence.

The0%lower endpoint in baseline2026H2 is not a typo. There are seven active dates,
only three containing winners, and August4alone supplies8of12winners. Some
resamples contain signals but no winning dates. One of5000draws contains no
signals and is omitted, leaving4999finite rates. All other rows have5000finite
draws. Such a small number of dates makes bootstrap inference fragile; neither
the exact bounds nor the66.7%point estimate should establish stability.

Pooled combined-minus-baseline accuracy is+0.07percentage points with a paired
95%interval-3.82to+4.04points. A difference interval containing zero does not
prove equivalent accuracy or noninferiority. The component selection and this
combination were explored on reused observations.

### Charlie's local interpretation

The canonical registry resolves Charlie to
`/Users/dgrissen/.config/persona-review-kit/personas/market/charlie-mcelligott.md`.
The persona is applied here as a positioning/market-structure lens, not the real
person or an independent agent. The side conversation prohibits reviewer agents.
The [interpretation](/Users/dgrissen/Dev/delta_bomb/outputs/b09_outcome_stability_2026-09-20/CHARLIE_INTERPRETATION.md) was written after the CI table and
before this deletion phase; its hash is recorded in the deletion receipt.

The central interpretation is an expansion of opportunities with a similar
historical payoff-relevant outcome mix. It is not a demonstrated reduction in
adverse outcomes: pooled stop-out rates remain24.2%, and absolute stops rise77to166
with the larger opportunity count. Several triggers may reflect the same
supportive market conditions; more entries do not establish additional independent
sources of buying. No measured dealer gamma,vanna,CTA or forced-flow mechanism is
established by these tables. The follow-up therefore examines whole sessions.

### Remove each date and recompute

Each deletion removes every qualifying signal on that date and recalculates the
denominator and every outcome cell. It does not refit indicators or choose new
thresholds. The ranges below are **sensitivity ranges, not confidence intervals**.

| Half | Baseline original | Baseline after deleting one day | Combined original | Combined after deleting one day |
|---|---:|---:|---:|---:|
| 2025H1 | 60.4% | 58.7–63.0% | 62.0% | 60.8–63.6% |
| 2025H2 | 60.0% | 58.4–61.6% | 59.3% | 57.9–60.2% |
| 2026H1 | 67.6% | 65.2–69.4% | 66.5% | 65.2–67.9% |
| 2026H2partial | 66.7% | 40.0–70.6% | 66.7% | 55.2–71.4% |
| Total | 62.3% | 61.3–63.1% | 62.3% | 61.8–62.8% |

The three completed halves move modestly after a single-day deletion. The pooled
combined estimate moves less than one percentage point in either direction. These
facts reject the narrow explanation that one exceptional date creates the pooled
hit rate. Because each deletion retains almost all the original sample, they do
not establish generalization to a different multi-day regime or narrow the CI.

### Dates causing the largest downward change in accuracy

| Cohort/half | Most damaging removed date | Removed winners/N | Remaining winners/N | Remaining rate |
|---|---|---:|---:|---:|
| Baseline2025H1 | 2025-01-21 | 4/4 | 54/92 | 58.7% |
| Combined2025H1 | 2025-04-29 | 6/6 | 121/199 | 60.8% |
| Baseline2025H2 | 2025-08-12 | 5/5 | 73/125 | 58.4% |
| Combined2025H2 | 2025-08-12 | 9/9 | 150/259 | 57.9% |
| Baseline2026H1 | 2026-04-30 | 5/5 | 45/69 | 65.2% |
| Combined2026H1 | 2026-04-30 | 8/9 | 107/164 | 65.2% |
| Baseline2026H2 | 2026-08-04 | 8/8 | 4/10 | 40.0% |
| Combined2026H2 | 2026-08-04 | 10/10 | 16/29 | 55.2% |
| Baseline pooled | 2026-08-04 | 8/8 | 190/310 | 61.3% |
| Combined pooled | 2026-08-04 | 10/10 | 417/675 | 61.8% |

Most damaging means lowest remaining hit rate; it need not be the date with the
largest number of winners. Combined's largest winner-count date is April25,2025
(13winners/18signals), while its most damaging deletion is August4,2026(10/10).
The stored ledger retains every date, including ties and zero-entry dates.

### Stop-rate and concentration checks

Pooled stop-out rates after deleting a date are baseline23.3–24.9% and combined
23.7–24.6%. Thus the roughly24%adverse-first frequency also survives individual
day removal. In partial2026H2 those ranges widen to23.5–50.0% and24.3–37.9%.
All endpoint-bucket sensitivity ranges are in the central stability summary.
Each column's extrema can occur on different deletions and must not be assembled
into a synthetic row that purports to sum to100%.

Top-five winning-date concentration is34/198=17.2%baseline and49/427=11.5%combined
pooled. Per half it is39.7%,32.1%,44.0%,100%baseline and32.3%,23.9%,31.3%,76.9%
combined. The last half is supported by very few dates, even after expansion.

Removing the same date from both strategies leaves pooled combined-minus-baseline
accuracy between-0.35and+0.49percentage points. Neither rule establishes a stable
pooled accuracy advantage from this exercise. The practical historical gain remains
more opportunities at a similar pooled rate, with unchanged adverse-outcome share.

### Verification and reproduction

Four boundary tests cover outcome priority, all endpoint bucket boundaries and
zero, full-day denominator changes, and empty remainders. Ruff passes. Source
hashes, all685event classifications, ten CI rows and five paired-CI rows reconcile.
All956date/period/cohort deletions are independently filtered and recounted across
nine categories(8604category checks); winner counts/rates exactly match the prior
winner-only day-deletion ledger. Paired same-date comparisons add478rows. No market
data, outcomes or rules changed, and no provider or reviewer process was launched.

Data:
`/Users/dgrissen/Dev/central_trade_data/thetadata/b09_outcome_stability_2026-09-20-v1`.
`table_with_ci.csv` is the full original-sample table; `leave_one_day_out.csv` is
every recomputed row; `stability_summary.csv` contains ranges/concentration;
`paired_day_deletions.csv` compares both on each same removed date. Reproduction
commands and exact phase ordering are in REPRODUCTION.md.


## Canonical Charlie interpretation as recorded before day deletion

Source: [CHARLIE_INTERPRETATION.md](/Users/dgrissen/Dev/delta_bomb/outputs/b09_outcome_stability_2026-09-20/CHARLIE_INTERPRETATION.md).

Canonical source: `/Users/dgrissen/.config/persona-review-kit/personas/market/charlie-mcelligott.md`.
Applied locally by the current assistant; not the real person or an independent
reviewer. Input: fixed outcome tables and whole-date confidence intervals.

**Decision: promising expansion of opportunities; greater safety is unproven.**

- **What works:**685signals retain essentially the318signal baseline's62.3%hit
  rate. The complete outcome mix also stays similar, rather than concealing a
  higher stop rate behind the winner percentage.
- **What remains costly:**roughly24.2%still touch-10first. The extra entries add
  absolute stop-outs as well as winners. The unresolved cases finish near entry
  on average; the full stop-outs remain the material adverse outcome.
- **The positioning read:**several triggers may be expressing the same supportive
  market environment. Repeated signals within a session are not separate evidence
  that another source of buying appeared. IV cooling does not establish dealer
  gamma, vanna or forced flows; those mechanisms are not measured in this table.
- **What to challenge next:**remove entire days, especially strong winner days,
  and inspect each half separately. Similar pooled rates and more signals do not
  establish equal forward accuracy. Partial2026H2's uncertainty is especially large.

**Confidence:**moderate in the historical accounting; low in claims of a stable
future advantage or an identified market-structure mechanism.


## Next bounded experiment

The next authorized step reuses the existing cached SPY relative-volume feature
across all five current cohorts. Keep five completed pre-entry minutes divided by
the same-clock median across 60 strictly prior source sessions, with RVOL>1 as the
single high-volume threshold. Preserve unknowns, observed-calendar comparisons,
retained/rejected winners, stop rates, and half-years. Do not fetch more data yet.
The cache ends June 11, 2026 and measures Nasdaq-venue SPY shares; neither2026H2
coverage nor consolidated/signed volume can be inferred. The prior B09-only test
was weak. Extension to B05/B07/persistence/combined is still pending at this commit.

Project memory is persisted in `/Users/dgrissen/Dev/delta_bomb/MEMORY.md` and linked
from README. All underlying data remain under `/Users/dgrissen/Dev/central_trade_data/`.

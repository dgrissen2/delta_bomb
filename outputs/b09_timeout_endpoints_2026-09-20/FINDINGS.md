# Where neither-barrier entries finish after sixty minutes

September20,2026. The requested subset touches **neither entry+5 nor entry-10**
anywhere in the original hour, measured using native minute highs/lows. It excludes
both target-first and adverse-first entries. The final result is the close of
the last minute in that hour minus entry open, in signed SPX points.

**For all rules combined, 92/685 entries (13.4%) reached neither barrier.** They
finished at a median of **-0.33 points**, mean **-0.70**, and a 10th–90th percentile
range of **-5.17 to +3.64**. Of those92 entries,43 ended positive,48 negative,
and1 flat. These are the unresolved entries' endpoints, not a revised hit rate.

## Each requested rule

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

## Combined distribution in fixed buckets

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

## Half-year sensitivity of the combined unresolved subset

| Period | Neither N | Active dates | Mean | Median | Negative / flat / positive |
|---|---:|---:|---:|---:|---:|
| 2025 H1 | 21 | 12 | -2.65 | -2.55 | 17/0/4 |
| 2025 H2 | 53 | 31 | -0.22 | +0.26 | 23/1/29 |
| 2026 H1 | 16 | 12 | +0.25 | +0.37 | 7/0/9 |
| 2026 H2 through September18 | 2 | 2 | -0.89 | -0.89 | 1/0/1 |

The pooled mild loss is not a stable half-year estimate. The partial last half
has only two unresolved cases. All five cohorts' per-half distributions and
histogram counts are preserved in ALL_RESULTS.md and the central summary tables.

## Exact clock and verification

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

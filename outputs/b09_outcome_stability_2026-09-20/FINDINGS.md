# Outcome-table intervals and individual-day stability

September20,2026. Completed in the requested order: confidence intervals added
to the full original outcome tables, local canonical Charlie interpretation,
then a whole-day removal recount of the full outcome mix.

**The combined rule preserves the observed pooled outcome mix and survives losing
any individual day. The partial2026H2 result is fragile.** This does not establish
that future accuracy is unchanged or that685signals are independent observations.

## Full-sample confidence intervals, before removing days

The [updated tables](TABLES_WITH_CI.md) retain the prior winner/stop/negative/flat/
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

## Charlie's local interpretation

The canonical registry resolves Charlie to
`/Users/dgrissen/.config/persona-review-kit/personas/market/charlie-mcelligott.md`.
The persona is applied here as a positioning/market-structure lens, not the real
person or an independent agent. The side conversation prohibits reviewer agents.
The [interpretation](CHARLIE_INTERPRETATION.md) was written after the CI table and
before this deletion phase; its hash is recorded in the deletion receipt.

The central interpretation is an expansion of opportunities with a similar
historical payoff-relevant outcome mix. It is not a demonstrated reduction in
adverse outcomes: pooled stop-out rates remain24.2%, and absolute stops rise77to166
with the larger opportunity count. Several triggers may reflect the same
supportive market conditions; more entries do not establish additional independent
sources of buying. No measured dealer gamma,vanna,CTA or forced-flow mechanism is
established by these tables. The follow-up therefore examines whole sessions.

## Remove each date and recompute

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

## Dates causing the largest downward change in accuracy

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

## Stop-rate and concentration checks

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

## Verification and reproduction

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

# How much do individual days drive B09 + (sector F4 OR SPX)?

September 20, 2026. No spacing. Same above-VT entries and same +5 before −10
within 60 native minute bars. A later reversal after +5 is irrelevant here.

**The pooled result survives losing any one session.** The original 198/318
(62.3%) becomes 190/310 (61.3%) when its most influential favorable day is removed.
Across every individual-day removal, accuracy stays between 61.3% and 63.1%.
The completed halves are also relatively insensitive to any one day. Partial
2026 H2 has too little evidence to support a reliable performance conclusion.

## Removing each day in turn

Each row below summarizes separate leave-one-day-out recalculations within that
period. Research dates with no qualifying signal are retained in the ledgers;
removing them leaves the filtered hit rate unchanged. The ranges are sensitivity
ranges, **not confidence intervals**. Entries remain signal-weighted throughout.

| Period | Active / research days | Original wins / N | Original hit rate | Lowest after one day removed | Highest after one day removed |
|---|---:|---:|---:|---:|---:|
| Pooled | 121 / 239 | 198 / 318 | 62.3% | 61.3% | 63.1% |
| 2025 H1 | 32 / 62 | 58 / 96 | 60.4% | 58.7% | 63.0% |
| 2025 H2 | 47 / 92 | 78 / 130 | 60.0% | 58.4% | 61.6% |
| 2026 H1 | 35 / 67 | 50 / 74 | 67.6% | 65.2% | 69.4% |
| 2026 H2 through September 18 | 7 / 18 | 12 / 18 | 66.7% | 40.0% | 70.6% |

## Which session matters most?

The day producing the most winners is not necessarily the day whose removal
hurts the rate most: a large day can contribute several losses as well as wins.
Both definitions were specified and are reported, rather than choosing whichever
looks most dramatic after seeing outcomes.

| Period | Day with most winners | Day wins / N | Remaining wins / N | Remaining hit rate |
|---|---|---:|---:|---:|
| Pooled | 2026-08-04 | 8 / 8 | 190 / 310 | 61.3% |
| 2025 H1 | 2025-04-25 | 7 / 10 | 51 / 86 | 59.3% |
| 2025 H2 | 2025-10-23 | 7 / 9 | 71 / 121 | 58.7% |
| 2026 H1 | 2026-01-09 | 6 / 8 | 44 / 66 | 66.7% |
| 2026 H2 partial | 2026-08-04 | 8 / 8 | 4 / 10 | 40.0% |

The most damaging deletions by rate are:

- Pooled: August 4, 2026; decrease of 0.97 percentage points.
- 2025 H1: January 21 or February 13, 2025, tied at 4/4; remaining 54/92,
  58.7%, a decrease of 1.72 points.
- 2025 H2: August 12, 2025, 5/5; remaining 73/125, 58.4%, a decrease of 1.60 points.
- 2026 H1: April 30 or June 1, 2026, tied at 5/5; remaining 45/69,
  65.2%, a decrease of 2.35 points.
- Partial 2026 H2: August 4, 2026; remaining 4/10. Its large percentage change
  is a thin-sample warning, not evidence that the strategy stopped working.

## Concentration of winners

Rank days by their number of target-first outcomes. These are cumulative shares
of winners, not simulations of deleting three or five sessions. Ties use earliest
date for deterministic display; tied win counts do not change these shares.

| Period | Days with at least one win | Largest day's share of wins | Top 3 days | Top 5 days |
|---|---:|---:|---:|---:|
| Pooled | 87 | 4.0% (8/198) | 11.1% (22/198) | 17.2% (34/198) |
| 2025 H1 | 22 | 12.1% (7/58) | 25.9% (15/58) | 39.7% (23/58) |
| 2025 H2 | 36 | 9.0% (7/78) | 23.1% (18/78) | 32.1% (25/78) |
| 2026 H1 | 26 | 12.0% (6/50) | 32.0% (16/50) | 44.0% (22/50) |
| 2026 H2 partial | 3 | 66.7% (8/12) | 100% (12/12) | 100% (12/12) |

Pooled, 164 of the 198 winners occur outside the five biggest winning dates.
That is reassuring against the specific concern that one spectacular session
created the whole result. At the half-year level, a handful of sessions still
accounts for a meaningful share of winners; this test does not establish regime
independence or make the half-year estimates precise.

## Does the descriptive advantage over plain B09 survive?

Removing the same date from both filtered and plain B09 preserves a positive
pooled rate gap in every case: **+7.51 to +8.73 percentage points**, compared
with the original +8.01 (62.26% versus 54.25%). For the three completed halves,
the same-date-removal gaps remain positive: +3.60 to +7.25, +10.74 to +13.62,
and +5.57 to +9.88 points respectively.

These compare selected signals with their full parent, including different date
and time mixes. They are descriptive checks, not proof that IV independently
causes or predicts the improvement. They do not replace the earlier within-date
and time-block comparisons, which showed substantially more uncertainty.

## What this adds to confidence

The narrow pooled deletion range answers a limited, useful question: **no single
research day is propping up the observed 62.3% rate.** It is not a new 61.3–63.1%
confidence interval. Each deletion still uses almost the entire original sample,
so this check alone cannot supply much new statistical information.

The 318 signals occurred on 121 active days. Neither number is an established
effective sample size: nearby entries can share a price move, and different days
can share a regime. No independence assumption is needed for the arithmetic here.
The results do not fix prior rule selection or constitute fresh validation.

The small partial half should carry little weight in judging stability: 18 signals
on seven active dates do not let us reliably distinguish a 40% strategy from a
67% strategy. The observed change reflects sensitivity, not an estimated future
rate. More distinct days under the unchanged rule would provide more information.

For the general problem of overstated precision when observations are clustered,
see [Cameron and Miller's practitioner guide](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015.pdf).
Their regression-inference discussion is motivation; this diagnostic does not
implement a regression estimator or claim calibrated clustered inference.

## Reproduction and verification

- Producer: `analyze.py`; fixed scope: `PROTOCOL.md`; boundary checks: `test_analysis.py`.
- Original memberships, events and calendar passed their frozen SHA-256 checks.
- Four hand-calculated tests passed, including zero-entry dates, retaining all
  non-target outcomes, rejecting unlisted dates/outcomes, and undefined empty samples.
- Independently filtered original event records for all 478 period/date removals,
  both selected and parent cohorts: **956 recounts**, every outcome and rate matched.
- Ruff passed. No entry, measurement, rule, outcome or source data was modified.
- Derived tables and receipt are under
  `/Users/dgrissen/Dev/central_trade_data/thetadata/b09_or_day_influence_2026-09-20-v1`.
  `daily_counts.csv` contains every research day; `leave_one_day_out.csv` every
  removal; `selected_entries.csv` the 318 entry records with Eastern entry times;
  `summary.csv` the five period summaries; `receipt.json` the source/code/output hashes.

Run from the project root:

```sh
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B -m unittest discover -s outputs/b09_or_day_influence_2026-09-20 -p test_analysis.py
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B outputs/b09_or_day_influence_2026-09-20/analyze.py
```

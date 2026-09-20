# Cached SPY relative volume across the five current Branch B cohorts

September 20, 2026. The earlier findings and current-set memory were committed
and pushed first (project consolidation e5259b4). This is the subsequent bounded
volume experiment using existing data only.

## Decision in plain terms

**This particular volume rule has not earned a filter.** The combined signals
already hit +5 first on 371/592 measurable entries (62.7%). Keeping only high
volume leaves 173/274 (63.1%): about half a percentage point more accuracy while
discarding 198 observed winners. Comparing high with ordinary volume directly
gives only +0.87 percentage points, with a 95% interval from −8.08 to +9.52 points.
That is not persuasive evidence of useful additional information.

B09 persistence offers the strongest small positive pooled hint: 63.0% versus
61.4%, but its difference interval is −9.03 to +12.47 points. The other three
individual cohorts have lower pooled accuracy with high volume. None establishes
a reliable benefit. The five overlapping cohorts are not five independent trials.
The current working set stays unchanged; no high-volume gate is adopted.

This is a result about one existing measure of trading activity. It does not
reject signed buying pressure, consolidated volume, or every possible volume
hypothesis. Those were not tested. It also provides no strong reason by itself
to buy or collect more data for this exact threshold.

## Exactly what was measured

At entry minute T, use actual cached SPY share volume from T−5 through T−1,
divided by the median volume for those same five clock minutes across exactly
60 strictly preceding source-calendar sessions. For a 10:15 entry, that means
the completed 10:10–10:14 bars, compared with 10:10–10:14 on each reference date.
The entry minute's volume is never included. RVOL > 1 is high; finite RVOL <= 1
is ordinary. This is the previously fixed threshold, not a newly optimized one.

All five bars must exist and be finite/nonnegative in the current window and
every one of the 60 history windows. The reference median must be positive.
Missing volume never becomes zero, ordinary volume, or a failed trading signal.
There is no stale forward-fill. Reference sessions can precede the 2025 research
sample and need not be above VT: they estimate normal SPY activity, not outcomes.

Source is the existing Databento XNAS.ITCH SPY cache, **Nasdaq-venue volume**.
It is not consolidated SPY trading, SPX index volume, or buyer-initiated pressure.
Cache availability ends June 11, 2026. No provider calls or data downloads occurred.

The four standalone cohorts and their union retain their original definitions,
239 research dates, exact-minute deduplication and no-spacing policy. Win means
native SPX high reaches entry+5 before native low reaches entry−10 within the
60 bars T…T+59. The low need not close there. A reversal after +5 cannot undo a
win. Causal above-VT admission and the fixed entry-based adverse barrier are
unchanged. All 685 price paths and their entry/VT checks were replayed successfully.

## Main comparison on observed volume

Ordinary volume is the comparison group, not a newly proposed inverted rule.
Unknown entries remain a separate coverage group. Full-cohort accuracy and
observed-cohort accuracy can differ because their dates and entries differ.

| Cohort | Observed, unfiltered | High volume | Ordinary volume | High − ordinary (pp) | 95% CI of difference (pp) | Unknown N |
|---|---|---|---|---|---|---|
| B09 + F4 OR SPX | 176/284 = 62.0% | 84/136 = 61.8% | 92/148 = 62.2% | -0.40 | -12.4 to 12.3 | 34 |
| B05 + F4 | 59/88 = 67.0% | 29/44 = 65.9% | 30/44 = 68.2% | -2.27 | -21.7 to 16.9 | 24 |
| B09 five-minute persistence | 271/436 = 62.2% | 126/200 = 63.0% | 145/236 = 61.4% | +1.56 | -9.0 to 12.5 | 56 |
| B07 original six-sector acceleration | 49/77 = 63.6% | 20/33 = 60.6% | 29/44 = 65.9% | -5.30 | -27.0 to 17.3 | 14 |
| All combined, deduplicated | 371/592 = 62.7% | 173/274 = 63.1% | 198/318 = 62.3% | +0.87 | -8.1 to 9.5 | 93 |

## Cost in opportunities

The correct unfiltered reference here is the **observed subset of each cohort**,
not its entire historical sample. For example, B05's full-sample 62.5% must not
be compared with high-volume 65.9% as though volume improved it: the same volume-
observable B05 population already achieved 67.0% without the volume gate.

| Cohort | Observed N retained | Observed winners retained | Winners excluded by gate | Accuracy change vs all observed (pp) | 95% CI (pp) |
|---|---|---|---|---|---|
| B09 + F4 OR SPX | 136/284 (47.9%) | 84/176 (47.7%) | 92 | -0.21 | -6.8 to 6.2 |
| B05 + F4 | 44/88 (50.0%) | 29/59 (49.2%) | 30 | -1.14 | -11.1 to 8.7 |
| B09 five-minute persistence | 200/436 (45.9%) | 126/271 (46.5%) | 145 | +0.84 | -5.0 to 6.6 |
| B07 original six-sector acceleration | 33/77 (42.9%) | 20/49 (40.8%) | 29 | -3.03 | -15.4 to 10.2 |
| All combined, deduplicated | 274/592 (46.3%) | 173/371 (46.6%) | 198 | +0.47 | -4.6 to 5.0 |

Combined high volume retains 46.3% of measurable entries and 46.6% of measurable
winners. The rejected ordinary-volume group itself contains 198 winners at a
62.3% hit rate. This fails the intended balance of accuracy and opportunity count.
The 93 unknown entries are not included in those rejected-by-volume counts.

## Half-year behavior

| Cohort | Half-year | High volume | Ordinary volume | High − ordinary (pp) | Unknown N |
|---|---|---|---|---|---|
| B09 + F4 OR SPX | 2025_H1 | 26/39 = 66.7% | 27/50 = 54.0% | +12.67 | 7 |
| B09 + F4 OR SPX | 2025_H2 | 48/83 = 57.8% | 28/44 = 63.6% | -5.81 | 3 |
| B09 + F4 OR SPX | 2026_H1 | 10/14 = 71.4% | 37/54 = 68.5% | +2.91 | 6 |
| B09 + F4 OR SPX | 2026_H2 | No coverage | No coverage | Not measured | 18 |
| B05 + F4 | 2025_H1 | 10/17 = 58.8% | 10/14 = 71.4% | -12.61 | 5 |
| B05 + F4 | 2025_H2 | 15/23 = 65.2% | 4/8 = 50.0% | +15.22 | 2 |
| B05 + F4 | 2026_H1 | 4/4 = 100.0% | 16/22 = 72.7% | +27.27 | 6 |
| B05 + F4 | 2026_H2 | No coverage | No coverage | Not measured | 11 |
| B09 five-minute persistence | 2025_H1 | 39/56 = 69.6% | 45/80 = 56.2% | +13.39 | 15 |
| B09 five-minute persistence | 2025_H2 | 74/125 = 59.2% | 41/66 = 62.1% | -2.92 | 5 |
| B09 five-minute persistence | 2026_H1 | 13/19 = 68.4% | 59/90 = 65.6% | +2.87 | 13 |
| B09 five-minute persistence | 2026_H2 | No coverage | No coverage | Not measured | 23 |
| B07 original six-sector acceleration | 2025_H1 | 7/11 = 63.6% | 7/10 = 70.0% | -6.36 | 1 |
| B07 original six-sector acceleration | 2025_H2 | 13/21 = 61.9% | 7/15 = 46.7% | +15.24 | 5 |
| B07 original six-sector acceleration | 2026_H1 | 0/1 = 0.0% | 15/19 = 78.9% | -78.95 | 3 |
| B07 original six-sector acceleration | 2026_H2 | No coverage | No coverage | Not measured | 5 |
| All combined, deduplicated | 2025_H1 | 54/82 = 65.9% | 60/102 = 58.8% | +7.03 | 21 |
| All combined, deduplicated | 2025_H2 | 102/168 = 60.7% | 52/89 = 58.4% | +2.29 | 11 |
| All combined, deduplicated | 2026_H1 | 17/24 = 70.8% | 86/127 = 67.7% | +3.12 | 22 |
| All combined, deduplicated | 2026_H2 | No coverage | No coverage | Not measured | 39 |

Combined high-volume accuracy is modestly higher in each of the three measurable
halves. That is a descriptive positive hint, but its weights vary sharply: there
are 82, 168 and only 24 high-volume combined entries in those halves. B09's
individual comparisons reverse direction in 2025 H2. B05/B07 cells are thin;
4/4 or 0/1 is not a dependable accuracy estimate. There is no volume test at all
for 2026 H2. These half-years do not establish stability of a volume advantage.

## Outcome mix and uncertainty

| Cohort | Volume | Win rate | 95% win-rate CI | Stopped first | Neither |
|---|---|---|---|---|---|
| B09 + F4 OR SPX | High | 61.8% | 52.3 to 70.8 | 38/136 (27.9%) | 14/136 (10.3%) |
| B09 + F4 OR SPX | Ordinary | 62.2% | 53.1 to 70.3 | 31/148 (20.9%) | 25/148 (16.9%) |
| B05 + F4 | High | 65.9% | 51.9 to 80.6 | 14/44 (31.8%) | 1/44 (2.3%) |
| B05 + F4 | Ordinary | 68.2% | 53.5 to 82.9 | 13/44 (29.5%) | 1/44 (2.3%) |
| B09 five-minute persistence | High | 63.0% | 54.5 to 70.8 | 52/200 (26.0%) | 22/200 (11.0%) |
| B09 five-minute persistence | Ordinary | 61.4% | 53.7 to 69.1 | 50/236 (21.2%) | 41/236 (17.4%) |
| B07 original six-sector acceleration | High | 60.6% | 43.6 to 77.8 | 10/33 (30.3%) | 3/33 (9.1%) |
| B07 original six-sector acceleration | Ordinary | 65.9% | 51.1 to 80.6 | 6/44 (13.6%) | 9/44 (20.5%) |
| All combined, deduplicated | High | 63.1% | 56.0 to 69.8 | 75/274 (27.4%) | 26/274 (9.5%) |
| All combined, deduplicated | Ordinary | 62.3% | 55.7 to 68.6 | 69/318 (21.7%) | 51/318 (16.0%) |

For the combined set, high volume has 75/274 stops first (27.4%), versus 69/318
(21.7%) for ordinary volume. Its slightly higher target frequency accompanies
fewer timeouts and more stops, not an obvious reduction in failed entries. This
does not change the objective: reaching +5 first remains the win definition.

Intervals use 5,000 paired whole-date bootstrap resamples, seed 20260920, within
each original half-year/pooled research calendar, including zero-entry dates.
All events on a sampled day move together. Differences use the same draws for
both groups. These are percentile intervals; they address intraday clustering,
not the history of rule selection, multi-day dependence or future regime changes.
Zero-denominator draws are excluded and their counts are recorded. Rate CIs are
suppressed for fewer than two active dates or constant binary outcomes. Sparse
or constant-outcome contrast bootstraps can also be degenerate and must not be
read as evidence of precision. There is no multiplicity correction or untouched
holdout here. The five cohorts are strongly overlapping.

## Does the pooled hint survive comparing similar dates and times?

Use the prior diagnostic: retain only date/hour blocks that contain both high
and ordinary entries. Blocks are anchored at 09:30, using the final completed
minute T−1. Calculate the hit-rate difference in each block, average blocks within
a date, then give each retained date equal weight. This changes both the sample
and weighting; it is not a causal volume estimate or a full price-strength match.

| Cohort | Comparable dates / blocks | High / ordinary entries | Equal-date difference (pp) | 95% date-bootstrap CI (pp) |
|---|---|---|---|---|
| B09 + F4 OR SPX | 18 / 19 | 23 / 26 | -17.59 | -42.6 to 7.4 |
| B05 + F4 | 3 / 3 | 5 / 3 | +16.67 | 0.0 to 50.0 |
| B09 five-minute persistence | 27 / 32 | 49 / 47 | -4.32 | -20.1 to 12.7 |
| B07 original six-sector acceleration | 2 / 2 | 2 / 2 | -50.00 | -100.0 to 0.0 |
| All combined, deduplicated | 38 / 44 | 73 / 63 | +0.44 | -12.7 to 14.5 |

Combined remains near zero (+0.44 pp), with a wide −12.72 to +14.47 pp interval
and only 136 entries across 38 dates. Persistence becomes −4.32 pp on its matched
blocks, also uncertain. B05's positive block number comes from only three dates
and eight entries; B07's negative number from two dates and four entries.
Those tiny subsets do not justify a conclusion in either direction.

Price context also differs. Combined high-volume entries had mean pre-entry
30-minute SPX return +7.68 basis points versus +3.16 with ordinary volume, and
mean realized 30-minute movement 10.57 versus 9.17 SPX points. The latter is
sqrt(sum of squared changes from the first open through successive minute
closes), not a directional return. Volume can accompany stronger or noisier
movement already present in prices. We have not isolated an independent mechanism.
The full cohort/half-year balance table is preserved centrally.

## Individual-day sensitivity

Remove every research date in turn, without retuning the threshold or memberships.
The following are sensitivity extrema, **not confidence intervals**:

| Cohort | High − ordinary after dropping one date (pp) |
|---|---|
| B09 + F4 OR SPX | -2.2 to 1.3 |
| B05 + F4 | -5.5 to 0.9 |
| B09 five-minute persistence | 0.1 to 2.8 |
| B07 original six-sector acceleration | -8.4 to -1.4 |
| All combined, deduplicated | -0.2 to 1.9 |

Combined's tiny pooled difference can cross zero after dropping one date. The
small persistence advantage remains positive under single-date deletion, but
its broad cluster interval and negative within-date/hour diagnostic remain.
Surviving a single-date deletion is not proof of useful predictive improvement.

## Coverage and exact missing-entry ledger

| Period | Usable | Current date unavailable | Incomplete 60-session history |
|---|---|---|---|
| 2025_H1 | 184 | 0 | 21 |
| 2025_H2 | 257 | 0 | 11 |
| 2026_H1 | 151 | 13 | 9 |
| 2026_H2 | 0 | 39 | 0 |
| pooled | 592 | 52 | 41 |

592/685 unique entries (86.4%) have usable relative volume, on 145 active dates.
The 52 missing current observations occur after the cache end: 13 in late 2026 H1
and all 39 entries in partial 2026 H2. Another 41 earlier entries fail the exact
60-session history requirement. All 93 unknown rows retain date, entry minute,
original cohort flags and specific status in [unknown_entries.csv](/Users/dgrissen/Dev/central_trade_data/thetadata/b09_working_set_volume_2026-09-20-v1/unknown_entries.csv).
Cohort-specific unknown counts overlap; do not add them as independent cases.

Unknown combined entries hit 56/93 (60.2%). That describes unavailable coverage;
it is not an estimate of their high/ordinary volume behavior. We neither replace
their volume nor extrapolate their missing measurements from outcomes.

## Reproduction and verification

- `run.py prepare` reuses the earlier causal volume builder and freezes 685
  outcome-free measurements, memberships, calendar, protocol/code and sources.
  It exactly reconciles all 501 overlapping timestamps against earlier features.
- `run.py analyze` independently checks all 685 measurements using direct raw
  five-column sums, joins hash-verified existing outcomes, and publishes 125
  summary rows, coverage, block comparisons, balances and 1,195 date deletions.
- `verify.py` independently replays all 685 native SPX entry paths (41,100 bar
  observations across 163 dates), confirms above-VT admission, recounts all 125
  summary rows and all 1,195 date deletions. Baseline volume counts exactly match
  the earlier 84/136 high, 92/148 ordinary and 22/34 unknown results.
- The existing boundary test confirms RVOL uses strictly prior dates and requires
  all 60 reference windows; Ruff passes. Source hashes and output receipts are
  stored alongside the data. No independent reviewer agent was run in this side chat.

Data: [/Users/dgrissen/Dev/central_trade_data/thetadata/b09_working_set_volume_2026-09-20-v1](/Users/dgrissen/Dev/central_trade_data/thetadata/b09_working_set_volume_2026-09-20-v1). Code/protocol: [/Users/dgrissen/Dev/delta_bomb/outputs/b09_working_set_volume_2026-09-20](/Users/dgrissen/Dev/delta_bomb/outputs/b09_working_set_volume_2026-09-20). CSV/Parquet bulk artifacts
remain in the central cache under its existing ignore policy; central dictionaries
and hash receipts are committed. Findings and extensive commit notes preserve the
reviewable results in the project repository. Original inputs remain unchanged.

**Research disposition:** keep all five existing cohorts as the working set. Keep
this fixed volume observation as a documented weak result; do not adopt a volume
gate, reverse the threshold, or run a threshold sweep on these same results.

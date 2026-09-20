# Project memory: current Branch B research working set

Updated September 20, 2026, by explicit user instruction. This is the current
working set for the above-Vol-Trigger OHLCV/IV research. Earlier B0x studies remain
historical evidence; do not silently substitute their populations or IV rules.

## Frozen objective and population

- January 2025–September 18, 2026: 239 selected research dates. This working set
  is not the earlier full 2024–2026 B0x population or a fresh holdout sample.
- Strict causal above-VT admission: all observed current-session RTH lows before entry and the entry open above the
  day's VT, using the existing verified provenance. Do not require future prices
  to remain above VT or admit below-VT entries.
- Win = native SPX high touches entry+5 before a native low touches entry−10,
  within sixty one-minute bars T through T+59, including the entry bar.
- −10 is relative to entry, not a trailing peak and not a candle-close condition.
  Same-minute first double touches are ambiguous; no inferred intraminute ordering.
  Neither/ambiguous remain in the denominator. A decline after +5 does not undo a win.
- Primary policy: no spacing. Keep separate first/day and 60-minute sensitivities;
  deduplicate identical date/minute entries before applying a policy.
- Endpoint of the hour = close(T+59), the T+60 boundary under the native convention.

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

## Current conclusions and limitations

- Encouraging expansion of historical opportunities, not proven preservation of
  future accuracy. Both pooled win rates are62.3%; both stop-out rates are24.2%.
- Full-sample whole-date95%CI: baseline55.6–68.4%, combined57.5–66.8%. Paired
  difference+0.07pp with interval−3.82to+4.04pp; no noninferiority claim.
- Leaving out each whole date gives pooled61.3–63.1%baseline/61.8–62.8%combined.
  These sensitivity ranges are not CIs. Prior searches and between-day regimes remain.
- Partial2026H2 is fragile. Removing August4 leaves baseline4/10 and combined16/29.
  Seven baseline/twelve combined active dates do not establish stable66.7%accuracy.
- With60-minute spacing combined191/327=58.4% versus baseline107/175=61.1%.
  New-date additions hit40/88=45.5% versus189/279=67.7%on already-active dates.
  Date labels may use later signals and cannot become an entry-time filter.
- Canonical Charlie lens was applied locally. No independent reviewer approved
  these new results; the separate Claude proposal review had no clean panel approval.

## Authoritative artifacts and next work

- Consolidated learning notebook: `outputs/ohlcv_branch_design_2026-09-12/OHLCV_BRANCH_COMBINATIONS.md`, section11.35.
- Current-set consolidation: `outputs/b09_current_working_set_2026-09-20/`.
- Combined counts: `outputs/b09_combined_expansion_2026-09-20/FINDINGS.md`.
- Neither endpoints: `outputs/b09_timeout_endpoints_2026-09-20/FINDINGS.md`.
- CIs/full outcome tables/day deletion: `outputs/b09_outcome_stability_2026-09-20/`.
- Frozen combined ledger: `/Users/dgrissen/Dev/central_trade_data/thetadata/b09_combined_expansion_2026-09-20-v1/events.parquet`.
- All new raw/derived data belong under `/Users/dgrissen/Dev/central_trade_data/`;
  maintain its changelog and data dictionary. Never infer missing minute prices.

## Completed volume extension: no new filter adopted

The fixed cached SPY RVOL test is complete across all five cohorts. Use five
completed minutes T−5…T−1 / same-clock median of 60 strictly prior source sessions,
with RVOL>1 fixed in advance. This is Nasdaq-venue volume, not consolidated volume
or signed buying pressure. No new data was fetched and no threshold was swept.

| Cohort | High-volume winners/N | Ordinary-volume winners/N | Unknown N |
|---|---:|---:|---:|
| B09 + F4 OR SPX | 84/136 (61.8%) | 92/148 (62.2%) | 34 |
| B05 + F4 | 29/44 (65.9%) | 30/44 (68.2%) | 24 |
| B09 persistence | 126/200 (63.0%) | 145/236 (61.4%) | 56 |
| Original B07 six-sector | 20/33 (60.6%) | 29/44 (65.9%) | 14 |
| All combined | 173/274 (63.1%) | 198/318 (62.3%) | 93 |

Combined high−ordinary difference +0.87 pp, paired date-cluster 95% CI −8.08 to
+9.52 pp. The common observed population already hits 371/592 (62.7%); high volume
adds only +0.47 pp relative to that while excluding 198 observed winners. Do not
claim B05 improves from full-sample 62.5% to high-volume 65.9%: its volume-observed
unfiltered population already hits 67.0%. Compare the same measurement coverage.

Only 592/685 combined entries have usable RVOL: 52 lack current data and 41 lack
complete reference history. The cache ends June 11, 2026, so 2026 H2 is entirely
unmeasured. Keep unknowns separate; never classify missing volume as ordinary.
Half-year counts and within-date/hour controls do not establish a useful advantage.
No high-volume gate or opposite low-volume gate is part of the current working set.

Full report: `outputs/b09_working_set_volume_2026-09-20/FINDINGS.md`; canonical
learning notebook section 11.36. Data and exact missing-entry ledger:
`/Users/dgrissen/Dev/central_trade_data/thetadata/b09_working_set_volume_2026-09-20-v1/`.
All 685 native price/VT paths, 125 summary rows, 1,195 day deletions and causal
feature measurements were checked. The small persistence hint remains exploratory.

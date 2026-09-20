
## B09-WORKING-SET-VOLUME-2026-09-20 — fixed cached SPY activity diagnostic

Namespace: `/Users/dgrissen/Dev/central_trade_data/thetadata/b09_working_set_volume_2026-09-20-v1`.
Producer/full findings: `/Users/dgrissen/Dev/delta_bomb/outputs/b09_working_set_volume_2026-09-20`.
Five fixed overlapping cohorts: B09 sector F4 OR SPX, B05 F4, B09 five-minute
persistence, original B07 six-sector acceleration, and exact-minute union.
239 selected research dates in 2025–September 18, 2026; 685 unique entries; no
spacing; causal above VT; high touch +5 before low touch entry−10 within 60 bars.

RVOL uses SPY Nasdaq-venue share volume from completed T−5…T−1 divided by the
same-clock median of exactly 60 strictly earlier source-calendar sessions.
Require all five actual bars per window and positive reference. High is >1,
ordinary finite <=1, missing/invalid remains unknown. No entry-bar volume,
forward-fill, new provider data, threshold search or inverted-rule adoption.

685 causal features and outcomes; 125 cohort/period/state summaries with 5,000
paired whole-date bootstrap CIs; coverage and pre-entry price-balance tables;
same-date/hour comparison with explicit surviving support; 1,195 pooled date
deletions. All rates are percent, differences percentage points. CIs do not correct
prior searches or between-day regimes; deletion extrema are not confidence intervals.

592 unique entries have usable RVOL. Exact unknown ledger has 52 current-data
gaps after June 11, 2026 and 41 incomplete historical references. 2026 H2 is
entirely unmeasured. Unknowns never count as volume-gate rejections. Combined high
173/274 (63.1%) versus ordinary 198/318 (62.3%); +0.87 pp, CI −8.08 to +9.52.
Common observed unfiltered rate 371/592 (62.7%); gate excludes 198 observed winners.
Weak result; current working set remains unchanged.

Namespace dictionary defines all fields, state partitions, clocks and dependencies.
Source/code/feature/output hash receipts record 501 prior feature reconciliations,
685 direct feature checks and native price/VT replays, 125 summary checks and
1,195 deletion checks. No raw data changed or downloaded. Bulk CSV/Parquet remain
local under existing ignore policy; documentation and receipts are versioned.

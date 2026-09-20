# IV idea inventory and exact treatment in this rerun

This inventory separates previously executed signal rules from measurement changes,
new transfers of those rules to other entries, and ideas that never became executable
rules. No row is promoted because it performed well in this expanded sample.

| Idea | Treatment here | Earlier implementation |
|---|---|---|
| ATM IV falling in six sectors | Exact second-half OLS direction on complete prior reference; eight-sector sensitivity | b06_sector_surface_50d_2026-09-13/breadth.py and analyze.py |
| Falling ATM IV with downward acceleration | Same-sector conjunction; thresholds six/eight; compare within broad falling | Same; b06_iv_acceleration_increment_2026-09-17 |
| Surface shape changes | ATM, 25-delta put richness, call richness and risk reversal; latest-half direction and acceleration. Full-window direction and slowing phases remain separately labeled diagnostics | Original surface.py/breadth.py; related coordinates are not independent votes |
| Bid/ask-resolved decline or acceleration | Conservative propagated quote-envelope sign, separate from calculated midpoint sign | Original breadth.py; no claim these ranges are confidence intervals |
| Bid-IV failure recovery | Original validity, midpoint recovery, guarded100 and guarded50 as separate policies; positive dollar bid still required | b06_iv_recovery_findings_2026-09-19 and b06_iv_expansion_150d_2026-09-19/iv_rules.py |
| Nearby strict quote before recovery | Balanced ±2 minute, same block/window, strict-first then guarded100 fallback, unique actual timestamps | xlre_balanced_baseline_2026-09-19/balanced.py; transfer as measurement sensitivity, no historical MAD needed |
| Same ETF price rising and IV falling | Endpoint changes over the identical thirty-point reference; six/eight ETFs must each satisfy both | b06_paired_price_iv_2026-09-17 |
| Prices versus IV disagreements | Broad price/IV cross-classification; unknown separate | b06_iv_price_disagreement_2026-09-14 |
| Comparable price setups | Exact rising count and ≤10 bps median-return gap; maximum one-to-one matches; global and within-half replication | b06_iv_matched_price_2026-09-17/matching.py |
| More sectors joining/dropping out | First/second fifteen-point price returns, identical sector support and missing-vote bounds; contextual tables | b06_participation_change_2026-09-17 |
| Capitalization weighting | Prior-session IVV equity weights, strict >50% full weight, missing mass unreallocated. Apply same rule to measurement policies explicitly | b06_sector_weighted_iv_2026-09-19 |
| IV confirmation during breakout | Separate five-point IV slope available at original T; paired with reference falling. New filter interpretation of an already measured feature | Original breadth.py breakout_slope |
| Confirmation after entry | At T+15, paired sector return/IV change measured T…T+14; new entry/VT gate and fresh sixty-minute price score | Earlier paired-price study used remaining45; current sixty-minute request changes that horizon explicitly |
| Filtering other price entry families | Same frozen context transferred to all B01–B10 variants; entries before10:05 cannot have the full reference | New transfer experiment using unchanged existing price recipes |
| Increase opportunities beyond selective thrust | Prespecified unions with qualified B06, B09, B10 or all three; duplicate executions counted once; report extra entries and their targets | New combination experiment, not a filter claiming to enlarge its own base |
| Acceleration strength compared with history | Not part of this prior-version rerun, per scope clarification. Existing balanced/MAD measurement work and new outcome cutoffs remain untested here | sector_iv_mad_2025_2026_2026-09-19 and remaining-sector study |
| Monthly-only expiry comparison | Not tested: existing near30DTE rule unchanged; a separate monthly-only definition/contract set is needed | Pilot measurement-validation proposal |
| Short-tenor/30-day term structure | Not tested: current expiry bracket supports the declared30-day coordinates, not a separately captured7-day surface | Earlier surface brainstorm |
| Leading constituents within sectors | Not tested: this is ETF data, not individual constituent option surfaces; no frozen leadership/universe rule | Sector/constituent brainstorm |
| Full continuous IV surface | Not claimed: measured ATM-spot and ±25delta coordinates at constant30calendarDTE | Original sparse-surface definition |
| Post-target givebacks | Excluded from success definition at user's direction | Earlier post-target audit is not used to reject a +5-first winner |

All source directories above are under `/Users/dgrissen/Dev/delta_bomb/outputs/`.
Results never convert a missing expiry bracket, missing native observation, or failed
weight snapshot into a negative IV reading. A rising/stress cell is a diagnostic
comparison, not an assumed bullish signal. The expanded registry and reused dates
make ranking exploratory; half-year tables and whole-date uncertainty are required.

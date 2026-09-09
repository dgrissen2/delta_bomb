# Broad call-wing normalization without HIRO

E-PNDR-012. This is a fixed daily-surface experiment, not an executable option-trade backtest. No HIRO observation, feature, filter, or timing rule is used. The existing membership file supplies stock names only. No provider calls were made.

Raw background: **921 distinct market sessions**, 2023-01-03 through 2026-09-03. Evaluation ledger: **671 distinct signal dates**, **216,733 stock-date slots**, **323 stock names**. Background dates are not additional trade dates.

| Sample | Stock-dates | Stocks | Distinct signal dates | First signal | Last signal |
|---|---:|---:|---:|---|---|
| quality_valid | 175,006 | 312 | 671 | 2024-01-02 | 2026-09-03 |
| quality_earnings_valid | 104,328 | 308 | 649 | 2024-01-02 | 2026-08-04 |
| rich_eligible | 17,458 | 304 | 643 | 2024-01-02 | 2026-08-04 |
| nonoverlap_admitted | 6,364 | 304 | 633 | 2024-01-02 | 2026-08-04 |

Rich observations span 32 reference months and 7,939 ticker-episode identifiers; episodes and stocks are not independent trials. Unknown episode starts stay labeled. The 30-calendar-day actual-earnings purge is retrospective; it is not proof that the calendar was known at entry.

The signal uses positive 5-delta/10-calendar-day call IV minus same-tenor ATM IV in the top 15% of its own strictly prior history. This surface coordinate measures a phenomenon; it does not prescribe a five-delta trade. The reference is the next market session close. Primary horizon is two sessions after that reference.

| Two-session rich group | Valid observations | Wing compresses | Compression with ATM flat/up | Total call IV falls | All three jointly | Mean wing change (vol points) | Mean stock return | Mean max upside excursion |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| slowing_rolling | 6,798 | 59.18% | 26.14% | 59.46% | 13.27% | -0.968 | 0.214% | 3.454% |
| continued_accelerating | 10,658 | 58.81% | 28.08% | 56.33% | 13.32% | -0.880 | 0.226% | 3.336% |

The 26%–28% figures above are joint frequencies across **all** valid observations, not probabilities conditional on ATM IV holding up. The following decomposition was requested after reviewing the primary result and is explicitly descriptive. It conditions on a future outcome that cannot be known at entry.

| Two-session group | All valid cases | ATM flat/up cases | ATM flat/up frequency | Wing compresses within ATM-flat/up cases | Wing and total call IV fall within those cases |
|---|---:|---:|---:|---:|---:|
| slowing_rolling | 6,798 | 3,056 | 44.95% | 1,777/3,056 = 58.15% | 902/3,056 = 29.52% |
| continued_accelerating | 10,658 | 5,028 | 47.18% | 2,993/5,028 = 59.53% | 1,420/5,028 = 28.24% |

All differences below are slowing/rolling minus continued/accelerating. Month blocks resample the entire stock cross-section together, 2,000 times.

| Sample / period | Joint difference (percentage points) | 95% month-block interval | Mean wing-change difference (vol points) | 95% month-block interval |
|---|---:|---|---:|---|
| rich_all_signals / all | -1.942 | [-3.282, -0.565] | -0.088 | [-0.320, 0.132] |
| rich_all_signals / 2024-2025 | -2.188 | [-3.592, -0.571] | -0.132 | [-0.439, 0.150] |
| rich_all_signals / 2026 | -1.018 | [-4.443, 1.516] | 0.075 | [-0.093, 0.275] |
| rich_nonoverlap / all | -3.544 | [-5.642, -1.358] | -0.332 | [-0.881, 0.156] |
| rich_nonoverlap / 2024-2025 | -2.794 | [-5.168, -0.362] | -0.340 | [-1.041, 0.312] |
| rich_nonoverlap / 2026 | -5.865 | [-10.784, -2.461] | -0.275 | [-0.629, 0.246] |

| Adjusted model | Joint difference (percentage points) | Month-clustered 95% interval |
|---|---:|---|
| rich_all_signals | -0.909 | [-2.219, 0.400] |
| rich_nonoverlap | -2.773 | [-5.326, -0.220] |

The adjusted model includes signal wing, signal ATM IV, ticker effects and reference calendar-month effects. It is an observational comparison, not causal proof. Full 1/2/4-session results, positive-but-slowing versus nonpositive slopes, chronology, signal-to-reference moves and censor counts are in raw_group_summary.csv.

Limitations: fixed-delta surfaces roll through different contracts each day and can change when spot changes. Modeled IV changes are not executable P&L. No option bid/ask, kink execution, fees, Greek repricing, or spread-leg benefit is established here. Current membership is applied backward; historical listings and symbol reuse are not reconstructed. The historical panel was examined in earlier work; neither chronological slice is an unseen holdout. No new thresholds were selected from these outcomes.

Price handling: ORATS defines both hiPx and clsPx as adjusted for splits and dividends ([official definitions](https://orats.com/docs/definitions)). They are used directly together. An initial implementation assumed raw highs and was corrected after checking these definitions; no second adjustment is applied. Missing prices/IV at any intervening session censor the outcome. Adjusted highs below adjusted closes cannot produce an excursion. Known splits and price-basis discrepancies are retained as flags: `{"adjusted_high_below_adjusted_close": 11, "adjusted_unadjusted_basis_differs": 8653, "adjustment_factor_jump": 2, "known_split_on_signal": 0, "known_split_through_exit": 0, "summary_raw_price_discrepancy": 10}`.

Reproduction: `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python scripts/pandar_no_hiro_surface.py`. Protocol/input hashes precede signal computation; the candidate ledger hash precedes outcome computation. All failed selections remain in candidate_reason_ledger.csv and candidate_reason_ledger.parquet.

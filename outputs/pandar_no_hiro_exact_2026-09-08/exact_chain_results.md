# Preliminary exact-call economics without HIRO

**The proposed selector did not establish a profitable or broader call-sale method.** Across all 1,163 eligible stock-dates it admitted 33 entries on 28 signal dates, all in five previously studied names: CRM, MRVL, ORCL, PLTR and QCOM. It admitted no new-name trade. Its eight common nonoverlap entries lost a combined $3,211.40 per one-contract case; three were profitable. The broader date/name counts below describe the search population, not 1,163 economic-rule trades.

The apparent positive mean policy difference includes many dates when the economic rule did nothing. The both-entered comparison has only eight cases and a negative median difference. Control exit coverage is also incomplete: 131 of its 260 nonoverlap entries lack a priced four-session outcome. None is assigned zero profit.

The cache supplies **1,163 eligible stock-dates**, across **203 signal dates** and **71 stocks**, from 2024-01-10 through 2026-06-15. The common nonoverlap sample has **273 cases** across 119 dates and 71 stocks.

Signals use existing stock names and daily quality with the authorized 30-day actual-earnings exclusion. No HIRO observations, features or coverage gates are used. Dates are selected by signal and next-session input availability, never by later outcome availability.

The economic selector compares the net modeled benefit of removing 25% of the current call-minus-spot-ATM IV with local dollar loss from a 1% rally. Gross recovery is capped at the entire ask value so the projected buyback ask cannot become negative; uncapped values and violations are retained. This is a testable scenario ranking, not an expected-return forecast. The control chooses nearest ten-day expiry and nearest ten-delta call. Exact strikes remain fixed at entry, with no replacement after failure.

## Common nonoverlap results

| Policy | Sessions after entry | Admitted | Priced | Known no-entry | Entry censored | Mean priced trade | Median priced trade | Win rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| economic | 2 | 8 | 8 | 265 | 0 | $-189.55 | $6.20 | 50.0% |
| economic | 4 | 8 | 8 | 265 | 0 | $-401.43 | $-62.30 | 37.5% |
| mechanical | 2 | 260 | 167 | 13 | 0 | $-32.18 | $-2.30 | 44.9% |
| mechanical | 4 | 260 | 129 | 13 | 0 | $-67.52 | $4.70 | 61.2% |

Per assumed standard 100-share contract, using actual entry bid minus one cent and exit ask plus one cent, with $0.65 per action. These are daily vendor snapshots (actual timestamps retained), not closing-auction fills.

## Paired policy comparison

| Sample / period | Horizon | Paired cases | Month blocks | Economic minus control, mean per case | 95% month-block interval |
| --- | ---: | ---: | ---: | ---: | --- |
| all_signals / all | 4 | 610 | 15 | $37.28 | $-5.44 to $92.46 |
| all_signals / 2024-2025 | 4 | 169 | 10 | $-2.47 | $-10.22 to $15.09 |
| all_signals / 2026 | 4 | 441 | 6 | $52.51 | $-5.74 to $121.01 |
| common_nonoverlap / all | 4 | 142 | 14 | $38.72 | $-7.94 to $118.78 |
| common_nonoverlap / 2024-2025 | 4 | 63 | 9 | $-5.92 | $-12.53 to $3.22 |
| common_nonoverlap / 2026 | 4 | 79 | 6 | $74.32 | $-8.60 to $190.06 |
| common_nonoverlap_excluding_prior_six / all | 4 | 58 | 10 | $13.70 | $-6.52 to $60.97 |
| common_nonoverlap_excluding_prior_six / 2024-2025 | 4 | 45 | 7 | $-2.68 | $-8.65 to $12.61 |
| common_nonoverlap_excluding_prior_six / 2026 | 4 | 13 | 3 | $70.39 | $-8.35 to $93.18 |
| common_nonoverlap_both_entered_priced / all | 4 | 8 | 3 | $488.50 | $-32.00 to $660.33 |
| common_nonoverlap_both_entered_priced / 2024-2025 | 4 | 1 | 1 | $-22.00 | Unavailable |
| common_nonoverlap_both_entered_priced / 2026 | 4 | 7 | 2 | $561.43 | $-32.00 to $660.33 |

Known no-entry decisions count as zero policy P&L. Unknown entries and exits remain censored. Paired comparisons require both policy outcomes; trade-only averages answer a different question. Common reservations persist even when either policy fails.

## Interpretation and limitations

This does not certify Pandar-approved trades or demonstrate an optimal delta/expiry. The candidate search has no narrow delta or percentage-OTM band. Many cached daily chains truncate contracts below five DTE; a selected contract disappearing before expiry is censored, never replaced or marked at zero.

Call-wing depth, local strike residuals, required IV contraction, actual entry delta/distance/DTE, runner-up candidates, and quote timestamps are retained. No long call is automatically purchased. Greek sensitivity is local and cannot bound naked-call upside loss. Historical deliverables and full comparable-surface richness remain unverified.

Worst EOD ask-to-cover loss is complete only when every intervening exact quote exists. A separate observed partial worst mark is not represented as complete risk. Underlying highs use the provider’s already-adjusted daily high and the entry snapshot converted to the same price basis; entry-day pre-trade highs are excluded.

Artifacts: `population_ledger.csv`, `candidates.parquet`, `frozen_selections.csv`, `policy_trades.csv`, `paired_policy_results.csv`, `failure_ledger.csv`, `source_conflicts.csv`, `summary.json`, `bootstrap.json`, and the input/selection hash manifests. Reproduce with the project Python runtime running `scripts/pandar_no_hiro_exact.py`. Zero provider calls.

## Why wing compression was insufficient

All five losing economic nonoverlap trades with supported entry/exit IV measurements showed fixed-strike wing compression. That does not make them successful trades:

| Case | Fixed-strike wing change | Same-expiry spot-ATM change | Stock at entry / exit snapshot | Net one-contract P&L |
| --- | ---: | ---: | ---: | ---: |
| MRVL, May 28 signal | −16.96 points | +30.88 points | $205.47 / $316.56 | −$2,731.30 |
| ORCL, May 1 signal | −3.38 points | −2.07 points | $180.95 / $196.03 | −$105.30 |

The MRVL call was sold for $0.77 and covered for $28.05. Its wing flattened, while general IV and the stock rose enough to overwhelm that improvement. ORCL lost even while both wing and ATM IV declined. These are fixed-contract measurements as remaining maturity changes, not constant-delta surface outcomes or a full attribution of option P&L.

Charlie's practical interpretation: a removable-premium scenario divided by a small local rally sensitivity does not express Pandar's stated requirement to withstand a much larger move toward the strike. The local ratio cannot establish the probability or cost of the joint stock/volatility path. No threshold, strike or expiration was retuned after these results.

## Participation, approximation and provenance

Of 107 economic signal selections, 74 no longer had positive modeled net economics at the fixed next-session entry snapshot. The frozen rule preserved those failed entries rather than substituting another strike. This timing issue is separate from whether a different causal entry time would work; that alternative was not tested.

Among 33 admitted economic cases, the assumed wing-IV contraction ranged from 1.43 to 9.44 points (median 3.73). The 1% rally denominator ranged from $1.28 to $49.58 per contract (median $8.74). No selected signal or admitted entry breached the uncapped ask-value recovery bound. The cap prevents impossible negative buyback asks, but does not turn a local Greek approximation into full repricing.

All eight economic nonoverlap entries came from the prior `pandar_richness_hist_strikes` source family. The source explicitly named `deustrader_wins_recreate_20260823` contributes 30 all-signal cases and eight common nonoverlap cases, with no economic entries. Excluding that explicitly winner-selected family leaves a four-session paired policy mean difference of $39.81 over 136 common cases; its 95% month-block interval is −$9.88 to +$123.44. This is a descriptive provenance sensitivity, not a new selection rule. The remaining cache is not thereby an unbiased sample or an unseen test.

The [source-family ledger](source_family_counts.csv) reports entry and paired-outcome counts for every source. The [provenance sensitivity](exclude_explicit_winner_source_sensitivity.json) preserves both horizons. Reproduce that addition with [provenance_sensitivity.py](provenance_sensitivity.py), after the main replay.

Input, source and frozen-selection hashes, exact contract preservation and quote-side arithmetic were independently rechecked in [validation.json](validation.json). Fourteen meaningful tests and Ruff passed; no provider calls were made.

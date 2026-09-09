# Frozen population descriptive features

All 50 frozen rows are retained, including 1 unselected contracts. This enrichment changes no population gate, contract, hypothesis, or protocol. No provider requests or option outcome inputs are used.

## IV Rank and Risk Reversal Rank

The authoritative local SpotGamma learnings reference supersedes the older Compass skill's 90-day-input reconstruction. These columns are **SpotGamma-compatible ORATS reconstructions**, not exact official product values or calibrated live hover cards.

- IV input: raw 30-calendar-day ATM IV `iv30d` in decimal volatility.
- Risk reversal: `dlt25Iv30d - dlt75Iv30d`, 30-day 25-delta call minus 25-delta put IV. Negative RR is valid. High RR rank describes calls richer relative to puts in their own history; it does not establish an absolute expensive call.
- Decomposition: call25-minus-ATM and put25-minus-ATM are shown separately in volatility points. Their difference equals RR. Neither leg uses ex-earnings IV.
- Rank: share of valid values strictly below current in the preceding 252 SPY exchange sessions, excluding current. Minimum 100 valid dates. Missing sessions occupy window slots; no backward extension to accumulate 252 valid values. Ties count as not below. Missing/insufficient values remain unavailable, never zero.
- `_rank_01` is a fraction; `_rank_pct` is exactly 100 times that fraction. This is a percentile, not the min-max statistic sometimes also called IV Rank.
- Each rank exposes valid count, missing count, actual window size, start/end dates, lookback, minimum and status. 252 sessions and minimum 100 are project conventions, not publicly documented SpotGamma edge-case rules.

Definition evidence was consulted locally: [SpotGamma learnings reference](/Users/dgrissen/.codex/skills/spotgamma-learnings/REFERENCE.md). It records the [official Guided View description](https://support.spotgamma.com/hc/en-us/articles/39936624524691-What-is-Guided-View-in-Compass) and first-party one-month webinar captures; no network fetch was performed for this enrichment.

## Existing call-wing and call-skew proxies

The frozen population used 5-call-delta/10-day IV minus ATM IV10, positive in absolute terms and at least the 85th prior percentile. Its saved rank uses 252 prior sessions and minimum 126. It is not IV30 Rank, RR30 Rank, an exact option bid-IV history or a claim that delta estimates touch probability.

The separate saved call-skew measure is ex-earnings 30-day 25-delta call IV minus ex-earnings ATM IV. It is neither call-minus-put RR nor an official Compass fixed-moneyness skew value. The source proxy values are retained unchanged.

Journey fields retain observed episode age and its left-censor flag, current percentile depth above 85, cumulative sum of `(rank-85)/15`, decline from the peak known at signal, two completed sessions of rollover/expansion, slopes and second differences. These describe different aspects of the journey; none was fitted to later option profits.

## Realized volatility and price-quality flags

For 30 and 60 **calendar days**, use all adjusted-close log returns ending in `(signal-days, signal]`, including the signal close. RV is `sqrt(252 * mean(log_return^2))`, a zero-drift historical estimate. It is not the Compass 20-trading-day realized-volatility display. Every expected return and its preceding price must exist; missing data prevents the RV estimate. The input is ORATS's reported adjusted `clsPx`; corporate-action correctness is not independently certified by the column name.

A daily adjusted simple return of absolute magnitude at least 25% is flagged. A gap greater than five percentage points between adjusted and unadjusted daily simple returns is flagged separately. Missing unadjusted comparisons are explicit. These fixed audit thresholds are not trading filters or proof of an error: legitimate splits, dividends and market jumps require context. **No extreme return is deleted or winsorized.** RV values, valid/expected return counts, flag dates and largest daily moves remain available for review. `no_threshold_flag` means only that these checks did not fire, not verified data quality.

Implied-minus-realized variance is `iv30d^2 - RV30^2` and `iv60d^2 - RV60^2`, in annualized decimal variance. Raw implied variance is compared with raw realized variance, not an asserted event-free diffusion premium or a forecast. Frozen RV values and recomputation differences are shown for reconciliation.

IV inputs are decimals; display volatility percentages and volatility-point differences multiply by 100 once. Current IV values at least 5.0 (500%) receive an extreme-input/unit-review flag but are not silently rescaled or deleted. Nonpositive or nonfinite individual IV inputs cannot form a valid IV/RR measure.

Signal summary spot, reported adjusted/unadjusted closes and their price gap are shown separately. Different snapshot times can explain a gap; prices are not silently spliced. Contract delta and OTM come from the frozen signal-date chain: delta fraction, delta points = 100*delta, OTM percent = 100*(K/S-1). Missing expiry or contract data remains missing. These are signal coordinates, not actual-entry Greeks.

## Observed coverage

- IV30 rank available: 50/50; RR30 rank available: 50/50.
- RV30 available: 50/50; rows with extreme adjusted jumps: 3; rows with adjusted/unadjusted divergence: 0.
- RV60 available: 50/50; rows with extreme adjusted jumps: 4; rows with adjusted/unadjusted divergence: 0.

## Reproduction and source hashes

`/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python scripts/pandar_hypothesis_features.py`

The parquet reader projects only summary/price fields and filters dates through the latest frozen signal. Each case then uses its own causal cutoff. No derived-outcome panel is opened.

- [selected_population.csv](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/selected_population.csv): `c4ef0d114dad6ed078d66406d079997a696ddcc6b796afa172d9bfe9bdc7e79a`
- [frozen_contract_selections.csv](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/frozen_contract_selections.csv): `ce22494b0da826cc86034c5a0cfe5b57ad76bcf41731a85652919dd0211a5304`
- [summaries.parquet](/Users/dgrissen/Dev/delta_bomb/docs/replay/pandar_skew_journey_2026-09-06/summaries.parquet): `6b7a07a0c3deb374abe78547fd71d6d3f4a6b846256432ad23393c19b0fdccc1`
- [dailies.parquet](/Users/dgrissen/Dev/delta_bomb/docs/replay/pandar_skew_journey_2026-09-06/dailies.parquet): `cbd574c5af47631a21c1ff46d1bc391e951910e3f9cd5c971856388a3a6c81f8`
- [pandar_hypothesis_features.py](/Users/dgrissen/Dev/delta_bomb/scripts/pandar_hypothesis_features.py): `1ceb9af3520af719325af004361bc23631b162c46267b45c65b1570665d34b96`

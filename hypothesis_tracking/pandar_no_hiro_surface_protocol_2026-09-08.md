# E-PNDR-012: broad call-wing normalization without HIRO

Frozen before this experiment's outcome computation on September 8, 2026. The underlying historical daily panel has been examined in earlier research; this is a new exploratory specification, not an unseen holdout. Current user instruction removes HIRO from every feature, filter, timing rule and outcome. The existing 323-stock membership snapshot supplies names only.

## Target / Outcome Definition

Primary question: among rich positive call-wing observations, does slowing/rolling wing expansion predict more subsequent wing compression with ATM IV flat or higher than continued/accelerating expansion?

W = 100 × (ORATS 10-calendar-day 5-call-delta IV − ATM IV10). This fixed surface coordinate is a broad diagnostic, not a selected contract or mandated trade delta. EOD signal t; reference next SPY trading session EOD t+1. Outcomes at 1, 2 (primary), and 4 sessions after reference. Joint primary indicator = ΔW<0 AND ΔATM>=0. Also report wing compression overall, fraction with ΔcallIV<0, wing compression/ATM-flat-up/total-call-IV-down jointly, ΔW, ΔATM, ΔcallIV=ΔW+ΔATM, stock return, and maximum intervening high relative to reference close. Preserve signal-to-reference changes separately.

## Sample Integrity

Use cached daily summaries and prices from January 2023 to September 3, 2026. Signal evaluation begins January 2, 2024. Prior history supplies warmup. Retain the existing signal quality rules: valid positive IV inputs, provider confidence >=50%, complete 20-session dollar-turnover proxy >=$20m. No contemporary option OI/volume filters. Require positive W and its strictly prior 252-session percentile >=85 with >=126 valid prior values. All other stock-dates stay in a reason ledger, not silently dropped. Report the full quality-valid sample and the rich subset separately.

Use the previously authorized actual-event earnings purge: no known historical earnings inclusively from signal through signal+30 calendar days, and reference through reference+30. Require explicit coverage of both windows in the cached metadata, capped at September 4, 2026. This is retrospective event exclusion, not a historically announced calendar. Unknown earnings coverage is not clear. No split-coverage requirement for this normalized daily-surface study; flag known splits and adjusted/unadjusted price-basis anomalies, and discuss symbol reuse as a limitation. Exact-contract studies need their own identity checks.

Reindex each stock onto the actual SPY calendar. Missing intervening prices or required IV values censor the corresponding outcome. Never jump over missing sessions. Missing outcome rows remain recorded and are not zero P&L. No HIRO imports, joins or files apart from the ticker-name CSV.

## Method

Recent slope = (W[t]−W[t−3])/3. Preceding slope = (W[t−3]−W[t−6])/3. Require all seven daily W values present. Continued/accelerating expansion means recent slope>0 and recent slope>=preceding slope. Slowing/rolling means all other valid rich observations. Separately describe positive-but-slowing and nonpositive recent slopes. Age, depth and time near extremes remain descriptive; do not add pass/fail gates. Preserve baseline rank and age metrics rather than choosing thresholds after outcomes.

Compute all-signal comparisons and a sensitivity retaining the earliest eligible rich signal per ticker, then no further signal until its reference+4-session exit is past. Use the same admitted nonoverlap sample for both groups; group membership does not choose a different overlap policy. A failure of an outcome does not release the holding reservation early. Report independent episode counts from the existing causal high-rank episode definition; unknown-start ages remain labeled.

Report raw group means/medians/rates. Adjust the primary binary outcome and ΔW with one additive linear regression: group + signal W + signal ATM IV + ticker fixed effects + reference-calendar-month fixed effects, clustered by month. No interactions or feature search. This is an observational adjustment, not causal identification. For raw primary differences and mean ΔW differences, resample whole reference calendar months across the cross-section with 2,000 draws, seed 20260908. A one-month sample cannot get a valid interval. Report monthly counts and chronological slices 2024–2025 versus 2026; neither is claimed to be unseen.

Primary support requires a positive slowing-minus-expanding difference in joint compression-with-ATM-flat/up with 95% month-block interval above zero, directionally consistent chronological slices, and the adjusted effect in the same direction. Missing common support or materially reversing nonoverlap/adjusted results weakens the verdict. ΔcallIV and adverse stock outcomes must be reported even when the primary result looks favorable. This can support a surface phenomenon, not profitability.

## Reproduction and next stage

Implementation: `scripts/pandar_no_hiro_surface.py`; outputs: `outputs/pandar_no_hiro_2026-09-08/`. Freeze this protocol and input hashes before executing outcomes. Tests cover earnings inclusivity, next-session causality, missing-session censoring, state calculation, and overlap exclusion. Native Codex Charlie/Brent reviews follow the analysis. No new provider calls are needed for this stage; the prior shared API budget remains 1,363/2,000 used.

E-PNDR-013 will evaluate richer strike/expiry selection and kink economics on exact historical chains, separately from this surface study. The available six-stock 126-date chain panel is selection-biased from the prior pilot; additional cached chains will be inventoried before choosing a broader deterministic sample. No exact-trade profitability claim follows from E-PNDR-012.

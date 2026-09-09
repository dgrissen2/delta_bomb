---
id: H-PNDR-003
round: 2
hypothesis_status: active
phase: recorded
---

# H-PNDR-003: Two-session contraction in a rich call wing improves short-call profit relative to continued expansion.

## Claim and decision summary

Two-session contraction in a rich call wing improves short-call profit relative to continued expansion. No new option outcome histories have been evaluated in round 1. This is a descriptive historical pilot until the predeclared sample and execution requirements are met.

## Target / Outcome Definition

D4 short-only net P&L and prior-comparable bid-IV-minus-ATM normalization, rollover minus expansion at comparable starting state. USD per one-contract episode after $0.65 per action and one-cent per-share adverse slippage. Two-cent cost stress holds trade timestamps fixed. A known no-entry has zero trading P&L in the policy denominator; missing evidence is censored, not zero. Primary horizon is holding session four at 15:50 ET, sale day counted as session one; session five is secondary.

## Data, inputs and supporting documents

[Seed and frozen protocol](pandar_seed_and_frozen_protocol.md), [hypothesis index](RESEARCH_HYPOTHESIS_INDEX.md), [memo](memo-pndr_pandar_call_research.md), [raw persona seeds](../outputs/seed_expansion.json), [data readiness](../outputs/pandar_hypothesis_2026-09-07/data_readiness.md).

[All population rows](../outputs/pandar_hypothesis_2026-09-07/population_ledger.csv), [selected population](../outputs/pandar_hypothesis_2026-09-07/selected_population.csv), [population hashes](../outputs/pandar_hypothesis_2026-09-07/population_manifest.json), [earnings](../data/pandar_hypothesis_2026-09-07/earnings.parquet), [split metadata](../data/pandar_hypothesis_2026-09-07/splits.parquet), [HIRO causal windows](../outputs/pandar_hypothesis_2026-09-07/hiro_pre_august_decisions.parquet), [budget](../outputs/pandar_hypothesis_2026-09-07/api_budget.json).

## Sample Integrity and alignment

The 323-stock current HIRO membership is applied backward; it is not historical membership. All 41,864 supplied ledger rows remain, including failure reasons. Fifty nonoverlapping ticker episodes pass the population gate across five entry dates, June 12–18, 2026. Seventeen otherwise eligible rows are blocked by an earlier five-session holding window. The population is a pre-outcome freeze, not fifty entered trades.

Refreshed actual earnings exclude signal and entry dates through +30 calendar days, inclusive. The user authorized this retrospective event purge. It does not prove an earnings schedule was available at entry. Eight stocks lack dated earnings history; no successor ticker is substituted. Nine invalid date placeholders are quarantined. Existing 2024–2026 surface results and ten earlier hand-reviewed option examples are exploratory.

## Method

| Test | Fixed rule | Pass criterion |
|---|---|---|
| Primary economic contrast | D4 short-only net P&L and prior-comparable bid-IV-minus-ATM normalization, rollover minus expansion at comparable starting state. | Positive paired mean and median, at least 20 distinct entry dates and date/episode-blocked 97.5% interval above zero |
| Execution validity | Fixed identities, actual-entry Greeks, quote spread/size/condition, event age, deliverables | Every required input verified for an executable-trade claim |
| Data repair | Actual-event exclusion, unchanged HIRO membership, no aliases | Every failure retained; no missing result converted to a winner |

All expiry, delta, OTM, ATM-distance, richness and timing details are frozen in the linked protocol. The 2–10 delta band is a project test assumption; it is not attributed to Pandar. Comparable richness uses at least 60 valid strictly prior dates independently in delta/DTE and forward-moneyness/DTE. IV and ATM total variance are interpolated separately before computing their IV difference.

## Results

| Round | Evidence | Result |
|---|---|---|
| 1 | ORATS earnings refresh | 26,510 valid event records; 315 of 323 stock names; nine invalid dates quarantined |
| 1 | Frozen eligible population | 50 stocks on five entry dates; 41,864 rows retained; 17 overlap exclusions |
| 1 | Preliminary HIRO audit before earnings | 72 candidates; 122 triggers across 57; eight first observed triggers have earlier missing decisions |
| 1 | Economic outcome | Not yet collected or tested; no profit claim |

## What worked and what did not

Actual earnings history repairs the otherwise empty next-earnings fields for retrospective filtering. June archives expand the stock sample. They provide only five independent entry dates, which cannot meet the predeclared twenty-date statistical threshold regardless of the number of stocks.

## Threats To Validity

Current-universe selection, retrospective earnings knowledge, previously seen surface results, five-date cross-sectional concentration, quote sampling and corporate-action identity remain material limitations. Raw quote history cannot establish execution if contract deliverables or quote age remain unknown. HIRO describes observed classified options flow; it is not direct proof of dealer hedges.

## Final Verdict

inconclusive

The population and causal signal data are ready for exact-contract testing. There is no new outcome evidence yet, and this five-date archive cannot establish statistical replication.

## Decision Impact

Proceed to frozen signal chains and entry snapshots, then exact leg histories. Preserve descriptive economics even when the statistical conclusion remains inconclusive. Do not promote a live trading rule from this round.

## Other Experiments To Run

Round 1 Charlie/Quant proposals will be indexed and backlinked by the native research adapter before closure. No follow-up is treated as completed until its evidence exists.

## Independent Persona Commentary

[Actual round 1 commentary](../outputs/commentary/round1/H-PNDR-003.json)

### charlie-mcelligott

The earlier surface work suggested modest volatility cooling after wing rollover; it did not establish rich exact-strike short-call profit. A persistent upside chase can keep expanding the wing, and a stock decline with rising volatility can damage the intended normalization mechanism. The June population repair does not resolve either issue, and five shared dates are insufficient for the frozen statistical claim.

Keep two-session contraction versus expansion as the single primary journey contrast. Build separate strictly prior sixty-date comparable delta/DTE and forward-moneyness/DTE histories, then retain observed starting richness and entry Greeks alongside short-only P&L. Do not substitute the fixed-five-delta summary for executable bid-IV excess, and do not add age, acceleration or variance-gap combinations to rescue a weak contrast.

### quant

The frozen metadata sample does not test whether rollover predicts short-call profit or exact-call bid-wing normalization. Prior surface findings are already seen exploratory evidence and cannot substitute for a new exact-contract result. The two historical richness coordinates measure different reference distributions: delta/DTE and forward-moneyness/DTE must retain separate valid-date counts and support failures. At least 60 valid prior dates establish minimum reference-history coverage; they do not create 60 independent strategy outcomes. Rollover-versus-expansion comparisons across different stocks remain observational even when starting-state bins match.

Audit the two 126-session prior windows for each frozen selected contract before claiming history-based richness. Use executable bid-IV minus matched call-mid ATM IV at K=F, verified forwards, adjacent supported smiles and total-variance tenor interpolation. Keep insufficient history, zero dispersion, missing forwards and unsupported brackets visible beside baseline replay results; do not turn richness availability into an unannounced trade filter. Report rollover and expansion sample counts and common support in the frozen starting-state bins before comparing simple means and medians. An empty or thin comparison remains inconclusive without new thresholds, fitted weights or favorable subgroup selection.

## Reproduction

`/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python scripts/pandar_hypothesis_population.py`

[Population implementation](../scripts/pandar_hypothesis_population.py), [batched acquisition](../scripts/pandar_hypothesis_api.py), [HIRO implementation](../scripts/pandar_hypothesis_hiro.py), [richness implementation](../scripts/pandar_hypothesis_richness.py), [contract selection](../scripts/pandar_hypothesis_contracts.py), [round verifier](../scripts/_research_loop/verify_round.py).

## Feynman Explanation

An expensive-looking call may keep getting more expensive. We want to learn whether prices starting to ease adds useful information beyond simply being high. The reference is comparable calls from earlier dates, not the short life of one weekly option.

We now have a list fixed before looking at new option profits, with earnings conflicts and missing data shown explicitly. The next step is to follow the same two contracts from the first sale through the planned exit, charging the prices and costs a trader would face.

## Round 2 appended evidence — entries and identities

The original expiry/delta rules selected 49 pairs; Z had no eligible expiry. Theta supplied 83 clock/causal-HIRO selected-expiry entry chains, plus six batches of signal-date quoted-contract listings. The original pairs failed the observed bid/delta/distance/spread gates in all 83 snapshots. ASML's far call was $0.50/$4.70; QCOM's clock quote was $1.00/$1.60, both wider than the frozen 30%-of-midpoint limit. This is a failure to enter under project quote rules, not evidence that Pandar has no call opportunities.

Both legs' minute quote and Greek histories were acquired for all 49 original pairs (196 files). Serial retries recovered the initially failed histories. No new P&L was used to choose the variant below. ORATS intraday returned 403; the first implementation issued 83 denied requests before a persistent denial circuit breaker was added. These attempts remain charged in the shared budget. Theta entry chains provide the fallback source with explicit provenance.

The contract audit preserves 98 original selected legs plus the no-expiry row. It found SERV history belonging to a former issuer, same-root strike adjustments, and distinct adjusted option roots including DVN1's 70-share deliverable. Exact historical deliverable verification remains missing; all eventual P&L is a quoted-price diagnostic until that requirement is satisfied.

[The one higher-delta follow-up](pandar_round2_delta_variant.md) is now frozen: signal delta 5–15, target 10, at least 5% OTM, identical expiry/nearer selection and quote/cost rules. It selects 47 pairs, has two no-call failures and the original no-expiry failure. Eleven legs overlap previously acquired original raw histories; the arm is an exploratory follow-up, not pristine validation. Six stocks pass the variant's preliminary entry-chain checks (seven policy entries): PLTR, DIS, MRVL, ORCL, QCOM and CRM. Displayed size, quote conditions, staleness and exact deliverables are still separate checks.

Evidence: [original entry gates](../outputs/pandar_hypothesis_2026-09-07/entry_chain_preliminary_gates.csv), [contract freeze](../outputs/pandar_hypothesis_2026-09-07/contract_freeze.json), [Theta entry manifest](../outputs/pandar_hypothesis_2026-09-07/theta_entry_manifest.json), [minute histories](../outputs/pandar_hypothesis_2026-09-07/minute_history_manifest.json), [identity audit](../outputs/pandar_hypothesis_2026-09-07/contract_reference_audit.md), [variant freeze](../outputs/pandar_hypothesis_2026-09-07/variant_freeze.json), [variant entry gates](../outputs/pandar_hypothesis_2026-09-07/variant_entry_chain_preliminary_gates.csv), [50-row IV/RR/journey table](../outputs/pandar_hypothesis_2026-09-07/eligibility_features.csv), [metric definitions](../outputs/pandar_hypothesis_2026-09-07/feature_definitions.md).

Round 2 verdict: inconclusive. Preserve the original no-entry outcomes, test the single higher-delta arm without further tuning, and allocate prior-smile requests using causal entry feasibility, never profit. No trade is yet claimed to have passed every execution requirement.

## Round 2 independent persona commentary

[Actual round 2 commentary](../outputs/commentary/round2/H-PNDR-003.json)

### charlie-mcelligott

The contract-level work has not established that wing contraction improves short-call profit. Zero preliminary entries in the original arm means there is no original admitted trade sample on which to resolve that claim. The higher-delta arm changes the contract exposure, so any later rollover contrast belongs to that separately labeled arm. Acquiring more files and finding six preliminary stocks cannot convert the earlier modest surface-normalization association into a demonstrated option edge.

Retain the two-session contraction-versus-expansion contrast and its starting-state controls. Allocate comparable prior-smile work using frozen entry feasibility, never subsequent profit, and require independent sixty-date support for delta/DTE and forward-moneyness/DTE. Report missing richness beside the baseline replay; do not add age, acceleration or variance-gap combinations to manufacture a favorable subset. Continue to mark statistical support inconclusive with only five entry dates.

### quant

The new descriptive IV30 and RR30 ranks have 252 prior valid dates for all fifty cases and are correctly separated from the existing call-wing and call-skew proxies. That does not establish sixty-date exact-call comparable richness or a rollover profit edge. Recomputed RV matches the frozen values, while extreme pre-signal jumps remain visible rather than being deleted; a variance premium influenced by those jumps is not evidence of diffusion-only carry. Identity findings also mean a matching ticker alone cannot justify borrowing predecessor-issuer history. No new economic rollover-versus-expansion result has been presented.

Complete only the already materialized richness-support audit using the variant's frozen coordinates and a date ledger for both delta/DTE and forward-moneyness/DTE. Allocate acquisition by causal entry feasibility within the shared budget, disclose that coverage restriction, and keep unsupported measurements beside the full population rather than filtering it. Require verified same-issuer history, at least sixty distinct prior dates, matched ATM and explicit forward support. Preserve the simple rollover/expansion contrast, jump flags and minimum-date limitation; do not add feature combinations to rescue the primary result.

---
id: H-PNDR-001
round: 1
hypothesis_status: active
phase: recorded
---

# H-PNDR-001: HIRO call-flow reversal improves the initial short-call entry.

## Claim and decision summary

HIRO call-flow reversal improves the initial short-call entry. No new option outcome histories have been evaluated in round 1. This is a descriptive historical pilot until the predeclared sample and execution requirements are met.

## Target / Outcome Definition

Net policy P&L per eligible episode: first HIRO reversal entry minus 10:01 clock entry, fixed contracts and D4 exit. USD per one-contract episode after $0.65 per action and one-cent per-share adverse slippage. Two-cent cost stress holds trade timestamps fixed. A known no-entry has zero trading P&L in the policy denominator; missing evidence is censored, not zero. Primary horizon is holding session four at 15:50 ET, sale day counted as session one; session five is secondary.

## Data, inputs and supporting documents

[Seed and frozen protocol](pandar_seed_and_frozen_protocol.md), [hypothesis index](RESEARCH_HYPOTHESIS_INDEX.md), [memo](memo-pndr_pandar_call_research.md), [raw persona seeds](../outputs/seed_expansion.json), [data readiness](../outputs/pandar_hypothesis_2026-09-07/data_readiness.md).

[All population rows](../outputs/pandar_hypothesis_2026-09-07/population_ledger.csv), [selected population](../outputs/pandar_hypothesis_2026-09-07/selected_population.csv), [population hashes](../outputs/pandar_hypothesis_2026-09-07/population_manifest.json), [earnings](../data/pandar_hypothesis_2026-09-07/earnings.parquet), [split metadata](../data/pandar_hypothesis_2026-09-07/splits.parquet), [HIRO causal windows](../outputs/pandar_hypothesis_2026-09-07/hiro_pre_august_decisions.parquet), [budget](../outputs/pandar_hypothesis_2026-09-07/api_budget.json).

## Sample Integrity and alignment

The 323-stock current HIRO membership is applied backward; it is not historical membership. All 41,864 supplied ledger rows remain, including failure reasons. Fifty nonoverlapping ticker episodes pass the population gate across five entry dates, June 12–18, 2026. Seventeen otherwise eligible rows are blocked by an earlier five-session holding window. The population is a pre-outcome freeze, not fifty entered trades.

Refreshed actual earnings exclude signal and entry dates through +30 calendar days, inclusive. The user authorized this retrospective event purge. It does not prove an earnings schedule was available at entry. Eight stocks lack dated earnings history; no successor ticker is substituted. Nine invalid date placeholders are quarantined. Existing 2024–2026 surface results and ten earlier hand-reviewed option examples are exploratory.

## Method

| Test | Fixed rule | Pass criterion |
|---|---|---|
| Primary economic contrast | Net policy P&L per eligible episode: first HIRO reversal entry minus 10:01 clock entry, fixed contracts and D4 exit. | Positive paired mean and median, at least 20 distinct entry dates and date/episode-blocked 97.5% interval above zero |
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

[Actual round 1 commentary](../outputs/commentary/round1/H-PNDR-001.json)

### charlie-mcelligott

Round 1 establishes a usable historical decision population, not an entry advantage. Fifty frozen episodes share only five June entry dates, so the cross-section cannot satisfy the twenty-date replication requirement. The preliminary 72-candidate HIRO audit found 122 flow triggers, but eight first observed triggers had earlier missing decisions. A fading call-flow line with a price break is evidence of estimated downward hedging pressure; it does not prove a profitable short sale or observed dealer execution.

Proceed with the first frozen HIRO action and 10:01 clock on the same contracts. Treat an earlier missing HIRO window as censored first-trigger selection. Preserve known no-trigger and known quote-gate failures as zero-trading policy outcomes, while missing evidence remains unavailable. Measure the short-phase exposure before comparing profit. Keep the verdict inconclusive irrespective of attractive individual June cases.

### quant

The population manifest establishes 50 frozen, nonoverlapping episodes from 41,864 retained rows, with 17 overlap exclusions. It explicitly records outcomes_read=false and only entry-session HIRO archive presence. This is a valid sample-construction result, not evidence that HIRO improves entry or that any of the 50 episodes became executable trades. Five June entry dates fail the predeclared minimum of 20 dates; adding cross-sectional stocks or bootstrap draws cannot repair that limitation. The preliminary 72-candidate HIRO audit is not the final earnings-filtered cohort. Its eight first observed triggers preceded by missing decisions show why first observed and first causally valid trigger cannot be conflated. The authorized actual-earnings purge is retrospective; no as-known schedule claim follows.

Keep the verdict inconclusive. Audit the causal HIRO decision history and fixed contract identities for every frozen episode. A complete observed no-trigger path may receive zero policy trading profit; a missing earlier decision must remain unavailable when it could change the first entry. Then compare the HIRO and clock policies by eligible episode, preserving entry failures and the shared dated sample. Report descriptive paired means and medians only for this five-date pilot; do not interpret its interval as satisfying the frozen statistical criterion.

## Reproduction

`/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python scripts/pandar_hypothesis_population.py`

[Population implementation](../scripts/pandar_hypothesis_population.py), [batched acquisition](../scripts/pandar_hypothesis_api.py), [HIRO implementation](../scripts/pandar_hypothesis_hiro.py), [richness implementation](../scripts/pandar_hypothesis_richness.py), [contract selection](../scripts/pandar_hypothesis_contracts.py), [round verifier](../scripts/_research_loop/verify_round.py).

## Feynman Explanation

The clock gives a fixed starting point. HIRO can improve it only if waiting for call demand to reverse produces better profit after costs, including times when it never signals.

We now have a list fixed before looking at new option profits, with earnings conflicts and missing data shown explicitly. The next step is to follow the same two contracts from the first sale through the planned exit, charging the prices and costs a trader would face.

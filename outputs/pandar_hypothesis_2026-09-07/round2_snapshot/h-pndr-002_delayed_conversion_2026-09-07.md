---
id: H-PNDR-002
round: 2
hypothesis_status: active
phase: recorded
---

# H-PNDR-002: A next-session nearer-call purchase adds value beyond an immediate spread and covering the short at conversion.

## Claim and decision summary

A next-session nearer-call purchase adds value beyond an immediate spread and covering the short at conversion. No new option outcome histories have been evaluated in round 1. This is a descriptive historical pilot until the predeclared sample and execution requirements are met.

## Target / Outcome Definition

D4 net P&L differences: next-session financed conversion minus immediate spread and minus covering the original short at the same conversion timestamp. USD per one-contract episode after $0.65 per action and one-cent per-share adverse slippage. Two-cent cost stress holds trade timestamps fixed. A known no-entry has zero trading P&L in the policy denominator; missing evidence is censored, not zero. Primary horizon is holding session four at 15:50 ET, sale day counted as session one; session five is secondary.

## Data, inputs and supporting documents

[Seed and frozen protocol](pandar_seed_and_frozen_protocol.md), [hypothesis index](RESEARCH_HYPOTHESIS_INDEX.md), [memo](memo-pndr_pandar_call_research.md), [raw persona seeds](../outputs/seed_expansion.json), [data readiness](../outputs/pandar_hypothesis_2026-09-07/data_readiness.md).

[All population rows](../outputs/pandar_hypothesis_2026-09-07/population_ledger.csv), [selected population](../outputs/pandar_hypothesis_2026-09-07/selected_population.csv), [population hashes](../outputs/pandar_hypothesis_2026-09-07/population_manifest.json), [earnings](../data/pandar_hypothesis_2026-09-07/earnings.parquet), [split metadata](../data/pandar_hypothesis_2026-09-07/splits.parquet), [HIRO causal windows](../outputs/pandar_hypothesis_2026-09-07/hiro_pre_august_decisions.parquet), [budget](../outputs/pandar_hypothesis_2026-09-07/api_budget.json).

## Sample Integrity and alignment

The 323-stock current HIRO membership is applied backward; it is not historical membership. All 41,864 supplied ledger rows remain, including failure reasons. Fifty nonoverlapping ticker episodes pass the population gate across five entry dates, June 12–18, 2026. Seventeen otherwise eligible rows are blocked by an earlier five-session holding window. The population is a pre-outcome freeze, not fifty entered trades.

Refreshed actual earnings exclude signal and entry dates through +30 calendar days, inclusive. The user authorized this retrospective event purge. It does not prove an earnings schedule was available at entry. Eight stocks lack dated earnings history; no successor ticker is substituted. Nine invalid date placeholders are quarantined. Existing 2024–2026 surface results and ten earlier hand-reviewed option examples are exploratory.

## Method

| Test | Fixed rule | Pass criterion |
|---|---|---|
| Primary economic contrast | D4 net P&L differences: next-session financed conversion minus immediate spread and minus covering the original short at the same conversion timestamp. | Positive paired mean and median, at least 20 distinct entry dates and date/episode-blocked 97.5% interval above zero |
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

[Actual round 1 commentary](../outputs/commentary/round1/H-PNDR-002.json)

### charlie-mcelligott

The later call purchase remains the economic question. Financing a nearer call merely changes the position: it spends premium to acquire upside and remove the unbounded short-call phase. Round 1 contains no new option profit evidence showing that this purchase adds more value than simply covering the short. Fifty population selections are not fifty entered or completed spreads.

Hold the original short sale fixed across immediate, day-zero, next-session and second-session purchase arms, with identical D4 and D5 deadlines. For each valid conversion compare final net wealth with covering the short at that exact minute and holding cash. Preserve the short when the purchase never qualifies, censor missing paths, and separate zero-bid residual marks from actual quoted closes. Apply the two-cent cost stress at the primary one-cent policy's fixed timestamps.

### quant

Round 1 supplies no option-price paths, purchase timestamps, profits, or loss measurements. The 50-episode population therefore neither supports nor rejects conversion economics. The useful methodological advance is the explicit conversion-time short-cover control: a financed nearer-call purchase can appear attractive while adding less value than closing the original short at that same time. The immediate-spread and final-deadline short-only controls answer additional, different comparisons. Fixed contracts and common deadlines are necessary for their paired arithmetic; selection counts alone cannot establish that these controls are observable or executable.

Execute the frozen paired-control replay after the contract and quote audit. Hold the initial short sale, nearer contract and D4 deadline fixed across acquisition arms; retain D5 as secondary. Include immediate, same-day, next-session and second-session purchases, conversion-time short cover and deadline short cover. Predeclare that a conversion-time-cover policy which never reaches a valid conversion timestamp falls back to deadline cover, matching the delayed policy's continuing short exposure. Report net differences, all failures/censoring, naked-short duration and observed adverse cover loss. Apply the two-cent cost stress at unchanged trade timestamps. Five dates permit a descriptive economic check, not statistical promotion.

## Reproduction

`/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python scripts/pandar_hypothesis_population.py`

[Population implementation](../scripts/pandar_hypothesis_population.py), [batched acquisition](../scripts/pandar_hypothesis_api.py), [HIRO implementation](../scripts/pandar_hypothesis_hiro.py), [richness implementation](../scripts/pandar_hypothesis_richness.py), [contract selection](../scripts/pandar_hypothesis_contracts.py), [round verifier](../scripts/_research_loop/verify_round.py).

## Feynman Explanation

Selling the far call brings in money; buying the nearer call spends some of it. Ending with a profitable spread does not tell us whether that purchase helped. We compare the same original sale with leaving the short alone, closing it, and buying both legs immediately.

We now have a list fixed before looking at new option profits, with earnings conflicts and missing data shown explicitly. The next step is to follow the same two contracts from the first sale through the planned exit, charging the prices and costs a trader would face.

## Round 2 appended evidence — entries and identities

The original expiry/delta rules selected 49 pairs; Z had no eligible expiry. Theta supplied 83 clock/causal-HIRO selected-expiry entry chains, plus six batches of signal-date quoted-contract listings. The original pairs failed the observed bid/delta/distance/spread gates in all 83 snapshots. ASML's far call was $0.50/$4.70; QCOM's clock quote was $1.00/$1.60, both wider than the frozen 30%-of-midpoint limit. This is a failure to enter under project quote rules, not evidence that Pandar has no call opportunities.

Both legs' minute quote and Greek histories were acquired for all 49 original pairs (196 files). Serial retries recovered the initially failed histories. No new P&L was used to choose the variant below. ORATS intraday returned 403; the first implementation issued 83 denied requests before a persistent denial circuit breaker was added. These attempts remain charged in the shared budget. Theta entry chains provide the fallback source with explicit provenance.

The contract audit preserves 98 original selected legs plus the no-expiry row. It found SERV history belonging to a former issuer, same-root strike adjustments, and distinct adjusted option roots including DVN1's 70-share deliverable. Exact historical deliverable verification remains missing; all eventual P&L is a quoted-price diagnostic until that requirement is satisfied.

[The one higher-delta follow-up](pandar_round2_delta_variant.md) is now frozen: signal delta 5–15, target 10, at least 5% OTM, identical expiry/nearer selection and quote/cost rules. It selects 47 pairs, has two no-call failures and the original no-expiry failure. Eleven legs overlap previously acquired original raw histories; the arm is an exploratory follow-up, not pristine validation. Six stocks pass the variant's preliminary entry-chain checks (seven policy entries): PLTR, DIS, MRVL, ORCL, QCOM and CRM. Displayed size, quote conditions, staleness and exact deliverables are still separate checks.

Evidence: [original entry gates](../outputs/pandar_hypothesis_2026-09-07/entry_chain_preliminary_gates.csv), [contract freeze](../outputs/pandar_hypothesis_2026-09-07/contract_freeze.json), [Theta entry manifest](../outputs/pandar_hypothesis_2026-09-07/theta_entry_manifest.json), [minute histories](../outputs/pandar_hypothesis_2026-09-07/minute_history_manifest.json), [identity audit](../outputs/pandar_hypothesis_2026-09-07/contract_reference_audit.md), [variant freeze](../outputs/pandar_hypothesis_2026-09-07/variant_freeze.json), [variant entry gates](../outputs/pandar_hypothesis_2026-09-07/variant_entry_chain_preliminary_gates.csv), [50-row IV/RR/journey table](../outputs/pandar_hypothesis_2026-09-07/eligibility_features.csv), [metric definitions](../outputs/pandar_hypothesis_2026-09-07/feature_definitions.md).

Round 2 verdict: inconclusive. Preserve the original no-entry outcomes, test the single higher-delta arm without further tuning, and allocate prior-smile requests using causal entry feasibility, never profit. No trade is yet claimed to have passed every execution requirement.

## Round 2 independent persona commentary

[Actual round 2 commentary](../outputs/commentary/round2/H-PNDR-002.json)

### charlie-mcelligott

The original arm supplies no admitted initial sale under its preliminary quote rules, so it cannot yet establish the value of buying the nearer call later. The frozen 5–15 delta, target-10, minimum-5%-OTM arm is a reasonable bounded feasibility experiment: a nearer far call may carry more saleable premium, but it also carries more upside exposure before protection. Its 47 pairs and seven preliminary entries are not profitable trades. Eleven legs overlap previously acquired histories, so the follow-up is explicitly exploratory even though new P&L did not select its rule.

Execute this one frozen variant with unchanged strikes, expiry, costs and liquidity gates; attribute the band to the project, not Pandar. Keep original results alongside it. For any admitted sale, compare next-session conversion with immediate spread purchase and covering the same short at the conversion minute, using common D4/D5 deadlines and fixed-time cost stress. If it cannot enter, cannot finance or lacks a quoted close, preserve that result without another parameter adjustment.

### quant

The original far calls' tiny bids and wide spreads explain why the fixed rules do not enter, without testing whether a later nearer-call purchase adds value. The one separately frozen 5–15-delta, target-10, minimum-5%-OTM variant addresses entry feasibility with a simple delta-plus-distance choice. Its 47 selected pairs and seven preliminary entries are still selections and checks, not completed trades or profits. Eleven legs overlap previously acquired histories, so the arm remains exploratory even though no P&L was used to choose it. A positive variant result cannot retroactively validate the original failed entry specification.

Execute only the already frozen delta10/OTM5 variant, preserving all 50 episode records, its two no-call failures, the no-expiry case, and the original arm. Freeze the rule and exact identities without another delta or spread search. For each shared initial sale compare next-session conversion with immediate spread, cover at the conversion minute, and final-deadline cover; report other timing arms as secondary. Use the same D4 deadline, retain D5 separately, stress costs at unchanged timestamps, and show observed adverse short exposure. Until exact deliverables and quote age are verified, label any resulting prices and P&L as diagnostics.

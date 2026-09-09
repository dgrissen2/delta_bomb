---
id: H-PNDR-003
round: 3
hypothesis_status: active
phase: recorded
---

# H-PNDR-003: Two-session contraction in a rich call wing improves short-call profit relative to continued expansion.

## Claim and decision summary

**Verdict: inconclusive.** Three rounds produced a frozen population, an audited higher-delta variant and exact-contract quote diagnostics. There are profitable examples, but the sample cannot establish a repeatable edge.

## Target / Outcome Definition

Compare frozen two-session rollover with expansion using D4 short-only P&L and separately supported prior delta/DTE and forward-moneyness/DTE strike richness. Describe episode age/depth and IV/RV30/60 without fitting another filter.

## Data and supporting documents

[Full trade report](../outputs/pandar_hypothesis_2026-09-07/pandar_trade_results.md), [all 50 eligibility/strike rows](../outputs/pandar_hypothesis_2026-09-07/eligibility_and_richness_tables.md), [frozen protocol](pandar_seed_and_frozen_protocol.md), [variant freeze](pandar_round2_delta_variant.md), [accounting interpretation](pandar_replay_interpretation.md), [index](RESEARCH_HYPOTHESIS_INDEX.md), [memo](memo-pndr_pandar_call_research.md).

## Sample Integrity and alignment

All 41,864 population rows are retained, including failed selections. Fifty nonoverlapping episodes on five June entry dates remain in both arms. The original selects 49 pairs; the variant selects 47, with two no-call failures and one no-expiry failure. Current HIRO membership is applied backward, not historical membership. Earnings exclude actual events in the inclusive next 30 calendar days, as authorized; this is not an as-known schedule claim.

The original and variant rules were frozen before their respective profit evaluation. Eleven variant legs overlap previously acquired original raw histories. The variant is explicitly an exploratory follow-up to original entry failures, not an untouched holdout. Every policy retains zero for a known skipped sale and unavailable for evidence that could change the first order. No contract substitution, post-path strike selection, deep-wing extrapolation or missing-result-to-zero replacement is permitted.

## Method

The clock and causal HIRO policies share fixed contracts with each purchase comparator. D0, D1 and D2 purchases scan their frozen windows, rechecking financing, quote quality, delta, OTM and earnings. HIRO governs the first sale only. Event replay uses the latest actual NBBO event at or before each order and a five-second age limit; Greek/underlying observations are exact-minute and cannot be future information.

Fees are $0.65 per action plus $0.01 per share adverse slippage. The $0.02 stress retains primary timestamps. D4/D5 deadlines are 15:50 ET, entry session counted as one and expiry capping the deadline. Bid/ask, displayed size, conditions, source/event timestamps, failed purchase attempts and short-phase exposure are saved. Exact dated deliverables remain unverified; P&L assumes a 100-share contract and remains a quoted-price diagnostic.

The frozen statistical threshold requires at least 20 distinct entry dates, positive paired mean/median and date/episode-blocked interval support. This sample has five dates and one five-session block. The 2,000 actual block resamples are degenerate; there is no confidence interval or statistical pass.

## Results

The fifty-signal population contains 35 episodes aged one or two, nine aged three to five and six aged at least six. Thirteen wings are expanding; only CPNG has the two-session rollover pattern. None of the six admitted-stock names is rollover, and all six are age one or two. The entered sample cannot estimate rollover-versus-expansion performance.

Six exact variant calls have at least 60 supported strictly prior delta/DTE observations. Four also meet that minimum at comparable forward-moneyness/DTE. MRVL has only 30 dates and QCOM 38 in the latter coordinate, so their z-scores/percentiles there remain unavailable. MRVL is at the 99.1st delta-coordinate percentile; CRM is around the 96th percentile in both supported coordinates. DIS has −0.26 vol points of absolute bid-IV excess despite an elevated relative percentile.

The six calls span about 7.21–36.56% OTM at the signal yet roughly 1.43–1.62 ATM-move units. Delta, raw distance and volatility-scaled distance supply different information. Only DIS has both 30/60-day implied variance above trailing realized variance among the six. MRVL’s large prior adjusted return affects RV; it was flagged, not deleted. No additional filter was selected from profit outcomes.

The ATM reference uses a carry-model forward internally checked against ORATS model call/put values. It is not independently observed. Prior comparable histories include earnings periods; they are coordinate/DTE matched, not earnings matched.

## What worked and what did not

The earnings refresh supplies 26,510 valid actual events for 315 of 323 names; eight names remain without dated coverage and nine invalid dates are quarantined. The one wider-delta variant creates a useful economic comparison. Minute-only data missed stale quote exposure at the ORCL D5 long exit. Exact event history repairs that interpretation without selecting another exit. IV/RR ranks and journey features are reported, but not silently promoted into new profitable-entry filters.

## Threats To Validity

Five-date concentration, current-universe survivorship, retrospective earnings knowledge, prior exploratory history, incomplete later HIRO archives, unverified dated deliverables/forward, and no early-assignment model prevent a validated execution or trading-edge claim. Extreme opening ask marks are displayed quote exposure, not proof of traded losses or maximum loss. Nonoverlap and date resampling preserve the observed dependence; they cannot create new independent episodes.

## Final Verdict

inconclusive

The declared statistical requirement is unmet and exact deliverables remain unavailable. The diagnostic economic findings above are retained; no live rule is promoted.

## Decision Impact

Keep delta, raw OTM, normalized distance and both supported richness coordinates separate. Do not claim a mature-skew exhaustion edge from young admitted episodes. Preserve missing deep-wing history instead of extrapolating.

## Other Experiments To Run

See the indexed experiments and actual round 3 Charlie/Quant proposals. Completed audits, partial deliverable verification and data-dependent follow-ups are distinguished in the index. No additional band is selected from the observed profit paths.

## Independent Persona Commentary

[Actual round 3 commentary](../outputs/commentary/round3/H-PNDR-003.json)

### charlie-mcelligott

The measured calls do not test mature skew rollover: all six names are in episode age one or two, and none has the frozen two-session contraction pattern. Only CPNG is a rollover case in the full fifty-episode feature table. Delta and OTM distance remain distinct coordinates: MRVL's admitted clock sale is 8.73 delta yet 36.31% OTM, versus DIS at 13.94 delta and 5.05% OTM. MRVL and QCOM lack sixty valid prior forward-moneyness/DTE observations, with only thirty and thirty-eight respectively. Only DIS has implied variance above trailing realized variance at both thirty and sixty days. Sources: eligibility_features.csv, strike_richness.csv and charlie_round3_feature_read.md.

Keep episode age, accumulated richness, distance from the known peak and contraction separate; no fitted mixture or favorable subgroup is justified. Maintain both prior-history coordinates independently and retain missing richness beside the baseline replay. Do not turn a high historical wing percentile or profitable short into proof that broad implied volatility was expensive. H-PNDR-003 remains untested in the admitted rollover contrast. All three claims remain statistically inconclusive: five entry dates occupy one five-session block, below the frozen twenty-date minimum. Preserve the original and exploratory variant labels without another delta/OTM adjustment.

### quant

There is no admitted rollover sample on which to test the frozen mechanism. All six measured/admitted stocks are only one or two sessions into their high-wing episode and none satisfies two-session rollover; the full population has one rollover case, CPNG, which did not enter. Thus the available short-call profits cannot establish that mature contracting skew beats expansion. The prior measurement audit is informative but separate: all six measured calls have at least 60 valid delta/DTE dates, while MRVL has only 30 and QCOM 38 forward-moneyness/DTE dates and remain unavailable in that coordinate. The other four have support in both coordinates. DIS has a negative exact bid-IV-minus-ATM spread despite a high relative historical score. IV30 and RR30 ranks and the older call-wing proxy do not substitute for those exact-call measurements. The 44 unrequested histories remain visible, and none of these prior observations increases the five-date strategy sample.

Label H-PNDR-003 untested economically in the admitted sample and inconclusive overall. Keep separate support counts, the ORATS carry-model forward limitation, negative absolute richness and RV jump flags. Do not relabel young high-wing episodes as rollover, change the two-session rule, or construct a fitted combination of age, acceleration and variance premium from these profits. In a separately frozen later sample, report rollover/expansion counts and common starting-state support first; only then show simple fixed-control means and medians. If there are no admitted comparable rollover cases or no supported bid-wing path, report that absence rather than replacing the comparison.
 The earlier notes and commentaries remain in the immutable [round 1 snapshot](../outputs/pandar_hypothesis_2026-09-07/round1_snapshot/h-pndr-003_skew_rollover_2026-09-07.md) and [round 2 snapshot](../outputs/pandar_hypothesis_2026-09-07/round2_snapshot/h-pndr-003_skew_rollover_2026-09-07.md).

## Reproduction

Use `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python`. Run `-m scripts.pandar_hypothesis_run`, `-m scripts.pandar_hypothesis_event_replay`, `-m scripts.pandar_hypothesis_event_exposure`, and `-m scripts.pandar_hypothesis_report`. The [resampling artifact](../outputs/pandar_hypothesis_2026-09-07/block_resampling.json) records its input hash and specification. The [event summary](../outputs/pandar_hypothesis_2026-09-07/event_replay_summary.json) records source hashes; the [call budget](../outputs/pandar_hypothesis_2026-09-07/api_budget.json) records all 1,363 provider attempts within the 2,000 authorization. Round closure requires `scripts/_research_loop/verify_round.py --round 3` to return zero.

## Feynman Explanation

A 10-delta call can be seven percent above one stock and thirty-seven percent above another. The second stock moves much more, so the raw distance alone is misleading. We compare the call’s bid volatility with ATM volatility and ask how unusual that difference was for similar prior calls. If only thirty comparable days exist, we cannot manufacture the required sixty. And because none of these entered names was actually rolling over, their profits cannot tell us whether rollover is the useful signal.

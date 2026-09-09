---
id: H-PNDR-002
round: 3
hypothesis_status: active
phase: recorded
---

# H-PNDR-002: A next-session nearer-call purchase adds value beyond an immediate spread and covering the short at conversion.

## Claim and decision summary

**Verdict: inconclusive.** Three rounds produced a frozen population, an audited higher-delta variant and exact-contract quote diagnostics. There are profitable examples, but the sample cannot establish a repeatable edge.

## Target / Outcome Definition

For the same initial sale and D4 deadline, compare next-session financed conversion with immediate spread, final short-only cover and covering the short at the exact purchase minute. Preserve D0/D2 as separately frozen alternatives.

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

At D4, all seven immediate spreads lose. Fourteen of 21 deferred stock/policy/window arms acquire the fixed nearer call; seven never purchase and remain short-only. All fourteen completed conversions beat immediate purchase, but only three beat covering the original short at the purchase minute: ORCL D1 (+$4.70), ORCL D2 (+$68.70), and QCOM D1 (+$20.70). These are correlated alternatives, not fourteen independent trades.

MRVL clock + D1 conversion earns $46.40 by D4, while same-minute cover earns $72.70 and final short-only cover $168.70. CRM D1 earns $18.40, versus $19.70 for same-minute cover. A profitable spread can therefore be a worse second decision.

QCOM D1 earns $9.40 at D4 and −$29.60 at D5. ORCL D2 earns $55.40 at D4 versus −$13.30 for same-minute cover, partly because the far call is quoted $0.03/$0.94 while the nearer ask is $0.18. This is relative closing liquidity, not evidence of a bullish forecast. ORCL D5 spread results remain unavailable because the long quote is stale; its short-only result is $72.70.

D1 clock conversion minus same-minute cover averages −$0.604 across all 50 eligible episodes; HIRO D1 averages −$0.110 across 42 priced episodes. Medians are zero. Dollar figures assume 100 shares and include primary fees/slippage.

## What worked and what did not

The earnings refresh supplies 26,510 valid actual events for 315 of 323 names; eight names remain without dated coverage and nine invalid dates are quarantined. The one wider-delta variant creates a useful economic comparison. Minute-only data missed stale quote exposure at the ORCL D5 long exit. Exact event history repairs that interpretation without selecting another exit. IV/RR ranks and journey features are reported, but not silently promoted into new profitable-entry filters.

## Threats To Validity

Five-date concentration, current-universe survivorship, retrospective earnings knowledge, prior exploratory history, incomplete later HIRO archives, unverified dated deliverables/forward, and no early-assignment model prevent a validated execution or trading-edge claim. Extreme opening ask marks are displayed quote exposure, not proof of traded losses or maximum loss. Nonoverlap and date resampling preserve the observed dependence; they cannot create new independent episodes.

## Final Verdict

inconclusive

The declared statistical requirement is unmet and exact deliverables remain unavailable. The diagnostic economic findings above are retained; no live rule is promoted.

## Decision Impact

Do not buy the nearer call merely because the first premium finances it. Preserve the second-decision comparison with same-minute cover, especially when the far call has a very wide ask. Later HIRO confirmation would require a new, simple frozen experiment and more later-session flow data.

## Other Experiments To Run

See the indexed experiments and actual round 3 Charlie/Quant proposals. Completed audits, partial deliverable verification and data-dependent follow-ups are distinguished in the index. No additional band is selected from the observed profit paths.

## Independent Persona Commentary

[Actual round 3 commentary](../outputs/commentary/round3/H-PNDR-002.json)

### charlie-mcelligott

The later call purchase must justify itself independently of the first short sale. At the primary D4 horizon, next-session conversion beats same-minute cover only for ORCL and QCOM among six completed purchases; DIS never purchases. CRM D1 makes $18.40, but covering instead makes $19.70. Across all three timing windows, fourteen completed purchases beat immediate spread entry, while only three beat conversion-time cover; seven other arms remain short-only. ORCL D2 adds $68.70 versus cover partly because the far ask is $0.94 while the nearer ask is $0.18. QCOM D1 changes from +$9.40 at D4 to -$29.60 at D5. Source: event_admitted_case_comparisons.csv.

Retain next-session purchase as primary and D0/D2 as secondary; do not select the most profitable window. The fixed nearer strike is bought at its first valid financing minute without a later HIRO confirmation. A fresh bullish confirmation therefore requires a separate prospective experiment. Keep no-purchase paths visibly labeled as uncovered shorts. At D5, all eleven priced completed deferred conversions lose to same-minute cover, while ORCL's three deferred results are unavailable because its long exit quote is stale. Preserve that censoring and the fixed-timestamp two-cent cost stress. Financing a long call is not evidence that buying it creates value.

### quant

The strongest supported economic observation is narrower than a profitable conversion rule: waiting often improves the immediate-spread comparison, but the added nearer-call purchase does not improve the primary cover-at-conversion control on average. For the variant clock policy at D4 and one-cent slippage, next-session conversion minus immediate spread is +$5.226 per eligible episode, while minus cover at conversion is -$0.604 and minus final-deadline short cover is -$4.024; all 50 episodes are priced and all three medians are zero. The HIRO policy has 42 of 50 priced pairs: +$3.429 versus immediate spread, -$0.110 versus conversion-time cover and -$1.538 versus final short cover, again with zero medians. This fails the required positive mean-and-median pattern against the substantive controls in this pilot. Known no-purchase paths correctly use final short cover in both policies. ORCL D5 spread outcomes remain unavailable because the nearer closing quote is stale; the independently priced short-only outcome remains $72.70. These are quoted-price diagnostics, not realized fills.

Do not promote the next-session purchase rule or tune its financing, delta, OTM, spread or deadline thresholds. Preserve D4 as primary, D5 as secondary, both fixed-time cost assumptions, every rejected purchase and all missing exits. A financed construction or an improvement over an immediately purchased losing spread is insufficient evidence of added value. Continue the existing deliverable verification work without duplicating it as a new strategy, and use one unchanged chronological replication to test the two primary control differences. Treat adverse cover quotes as observed exposure diagnostics; a wide quote or a favorable isolated ORCL result is not an independently demonstrated trading edge.
 The earlier notes and commentaries remain in the immutable [round 1 snapshot](../outputs/pandar_hypothesis_2026-09-07/round1_snapshot/h-pndr-002_delayed_conversion_2026-09-07.md) and [round 2 snapshot](../outputs/pandar_hypothesis_2026-09-07/round2_snapshot/h-pndr-002_delayed_conversion_2026-09-07.md).

## Reproduction

Use `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python`. Run `-m scripts.pandar_hypothesis_run`, `-m scripts.pandar_hypothesis_event_replay`, `-m scripts.pandar_hypothesis_event_exposure`, and `-m scripts.pandar_hypothesis_report`. The [resampling artifact](../outputs/pandar_hypothesis_2026-09-07/block_resampling.json) records its input hash and specification. The [event summary](../outputs/pandar_hypothesis_2026-09-07/event_replay_summary.json) records source hashes; the [call budget](../outputs/pandar_hypothesis_2026-09-07/api_budget.json) records all 1,363 provider attempts within the 2,000 authorization. Round closure requires `scripts/_research_loop/verify_round.py --round 3` to return zero.

## Feynman Explanation

Selling MRVL’s 425 call collected $224 before costs. Buying the 420 call the next morning left a spread that eventually earned $46.40. But we could instead have closed the first short then and kept $72.70. The trade made money; the second purchase cost us money relative to that choice. ORCL shows another reason to convert: sometimes buying a better-protecting nearer call costs less than crossing a very wide ask to close the far short.

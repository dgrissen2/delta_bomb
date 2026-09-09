# Pandar call research decision memo

**Status:** final
**Date:** 2026-09-07
**Verdict:** inconclusive
**Decision:** Retain the documented profitable examples and failed comparisons. Do not promote a timing rule from this five-date pilot.

## 1. Executive Summary

The broader delta experiment found six call-sale names: **PLTR, DIS, MRVL, ORCL, QCOM and CRM**, with seven admitted clock/HIRO sales. Some made money, including MRVL’s clock short ($168.70 at D4), ORCL’s short ($72.70) and CRM’s short ($32.70). Buying the nearer call frequently consumed the first leg’s profit. Only three of fourteen completed deferred purchases beat covering the short at the purchase minute at D4; none of eleven priced purchases did at D5, with three ORCL results unavailable because the long quote was stale.

The verdict remains inconclusive. Both original and higher-delta populations retain all fifty episodes and every failed/missing case. The five entry dates cannot satisfy the frozen twenty-date criterion, and exact dated deliverables remain unverified. Values are historical quoted-price diagnostics assuming a 100-share contract, after fees/slippage, not actual fills.

Read the [complete trade report](../outputs/pandar_hypothesis_2026-09-07/pandar_trade_results.md) for every D4/D5 result, actual leg times/prices/deltas/distances, same-minute cover comparisons and exposure. The [eligibility and richness tables](../outputs/pandar_hypothesis_2026-09-07/eligibility_and_richness_tables.md) explain every qualifying date/ticker and both fixed contract selections.

## 2. What We Tested And Why It Mattered

[H-PNDR-001](h-pndr-001_hiro_entry_2026-09-07.md) compares HIRO flow-reversal entry with a 10:01 clock sale. [H-PNDR-002](h-pndr-002_delayed_conversion_2026-09-07.md) tests whether a later nearer-call purchase adds value versus immediate spread, covering then, and keeping the short. [H-PNDR-003](h-pndr-003_skew_rollover_2026-09-07.md) tests call-wing rollover with prior strike richness, episode age/depth and IV versus realized volatility.

The [initial protocol](pandar_seed_and_frozen_protocol.md) and [one higher-delta follow-up](pandar_round2_delta_variant.md) freeze selection and timings. The 2–6 band used earlier, the original 2–10 band here and the 5–15 variant are project choices. **They are not Pandar requirements.** The variant was chosen from entry-feasibility failures; it is exploratory, with eleven legs overlapping already acquired original raw histories.

## 3. What We Found

The original approximately five-delta selections failed the entry gates; that did not mean only MSTR could supply a Pandar-style sale. The target-ten-delta variant produced six names in the earlier June HIRO archive. Every original and variant pair’s entry session was checked against actual NBBO quote events; the same seven sale-policy cases survived. All corresponding fixed holding histories were acquired.

The stronger comparison is the second decision. D1 clock conversion averaged +$5.226 per eligible episode versus immediate spread, but −$0.604 versus covering at purchase and −$4.024 versus final short-only cover, with fifty episodes and zero medians. HIRO D1 also had negative average increments versus both cover controls across 42 of 50 priced episodes. HIRO-minus-clock D4 short-only P&L averaged −$3.19 across those 42 paired episodes, median zero. These descriptive means preserve skipped trades; they are not seven-trade win rates.

MRVL D1 conversion earned $46.40, but covering at that moment earned $72.70 and retaining the short earned $168.70. ORCL D2 conversion earned $55.40 versus −$13.30 for covering then, partly because buying the nearer call at $0.18 avoided the far call’s wide $0.94 ask. QCOM D1 earned $9.40 at D4 and lost $29.60 at D5. The liquidity comparison and common deadline materially affect the answer.

For richness, CRM is near the 96th percentile in both supported coordinates. MRVL reaches the 99.1st delta/DTE percentile but has only thirty supported prior forward-moneyness/DTE dates; QCOM has thirty-eight. Their second-coordinate scores stay unavailable. The six admitted names are all age one or two and none has two-session rollover. There is no entered rollover sample with which to test the exhaustion claim. The carry-model forward is not independently observed and prior reference histories include earnings periods.

ORATS earnings refresh recovered 26,510 valid actual events for 315 of 323 current-HIRO stocks; eight lack dated coverage and nine invalid dates were quarantined. Inclusive next-thirty-day actual-event exclusions are applied at signal and order, as authorized. This is not a historical as-known schedule claim. The [budget](../outputs/pandar_hypothesis_2026-09-07/api_budget.json) records 1,363 of 2,000 authorized provider attempts, including failed calls and authentication. Supported endpoints were batched, and exact-contract tick requests reused cached overlaps.

## 4. Timeline — What Actually Happened

| Round | Date | Step | What happened | Artifact |
|---|---|---|---|---|
| 1 | 2026-09-07 | Earnings and population freeze | 26,510 valid earnings events; fifty episodes on five June entry dates; every failed row retained. No new option outcome histories evaluated. | [Population manifest](../outputs/pandar_hypothesis_2026-09-07/population_manifest.json) |
| 2 | 2026-09-07 | Exact entry feasibility and one frozen variant | The original 49 pairs produced zero preliminary eligible entries. The 5–15 delta variant, targeting 10 delta and at least 5% OTM, freezes 47 pairs and identifies six preliminary stocks. Exact deliverables remain unverified. | [Variant freeze](../outputs/pandar_hypothesis_2026-09-07/variant_freeze.json) |
| 3 | 2026-09-07 | Event replay, prior richness and controls | Seven admitted sales across six names; every policy/failure retained. Most completed conversions fail the same-minute-cover comparison. One five-session block cannot support an interval. | [Trade results](../outputs/pandar_hypothesis_2026-09-07/pandar_trade_results.md) |

## 5. The Decision And Its Consequences

Keep delta and percentage OTM together, and report volatility-scaled distance and independently supported richness coordinates. Do not widen another band or add a winning filter after inspecting these paths. Do not buy a nearer call just because the first premium finances it; compare its cost and later cash flows with covering the original short at the same moment. A quote-liquidity reason can be distinct from a rebound forecast.

The calculation work and three persona rounds are complete for this available pilot. Execution validation remains incomplete: exact dated deliverables/multipliers were not obtained. The [contract audit](../outputs/pandar_hypothesis_2026-09-07/contract_reference_audit.md) documents issuer reuse and real adjustments rather than silently substituting contracts. Short-phase risk ledgers include fresh but very wide opening asks; these are observed cover costs, not traded losses or maximum-risk limits. Early assignment and overnight execution are not modeled.

## 6. Open Questions / Next Step

The [indexed follow-ups](RESEARCH_HYPOTHESIS_INDEX.md) identify the next useful evidence: dated exact deliverables and a new chronological block with complete HIRO and matured earnings windows. A simple later bullish HIRO confirmation could test the second purchase separately; it is absent from the current financing-only purchase rule and must be frozen before new outcomes. More resampling of these same five dates will not supply that missing evidence. No additional paid data entitlement has been purchased.

The [second-leg archive audit](../outputs/pandar_hypothesis_2026-09-07/second_leg_hiro_coverage.md) finds D1 coverage for only PLTR and ORCL among the six admitted stocks, with an opening gap for ORCL; only PLTR has D2 coverage. A complete-cohort later-flow test cannot be run from those files. All 192 selected original/variant legs match [dated quote-list tuples](../outputs/pandar_hypothesis_2026-09-07/signal_listing_reconciliation.csv), but those listings do not supply exact deliverables.

## 7. Feynman Explanation

Start with the money already made on the short call. In MRVL, we could have closed the first short the next morning and kept $72.70. Instead, buying the nearer call left a spread that eventually earned $46.40. The final profit is real arithmetic, but the second decision cost $26.30 relative to closing then.

ORCL shows why conversion can sometimes make sense for another reason. The short far call’s ask was $0.94, while a nearer call cost $0.18. Buying the nearer call supplied protection more cheaply than crossing that wide ask to close the short. We should identify that specific condition, not turn one attractive example into a claim that buying the second leg generally works.

The purpose of the two legs is therefore not just to show a positive final number. The second leg must improve the choice available at the time, after costs and with its risk stated. This sample supplies useful examples and a reason to test a more selective second purchase; it does not yet establish a dependable rule.

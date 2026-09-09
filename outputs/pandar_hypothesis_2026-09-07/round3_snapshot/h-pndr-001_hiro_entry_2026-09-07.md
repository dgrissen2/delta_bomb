---
id: H-PNDR-001
round: 3
hypothesis_status: active
phase: recorded
---

# H-PNDR-001: HIRO call-flow reversal improves the initial short-call entry.

## Claim and decision summary

**Verdict: inconclusive.** Three rounds produced a frozen population, an audited higher-delta variant and exact-contract quote diagnostics. There are profitable examples, but the sample cannot establish a repeatable edge.

## Target / Outcome Definition

Compare HIRO versus the 10:01 clock on the same frozen episode and contracts, retaining skipped and unavailable entries. D4 is primary; D5 is secondary.

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

The original rule admits no sales: 92 known no-entry stock/policy cases and eight unavailable HIRO cases out of 100 slots. The 5–15 delta variant admits seven sales across six stocks, with 85 known no-entries and eight unavailable entries. Actual event quotes confirm the same admitted set as the minute view.

For D4 short-only P&L, HIRO minus clock averages −$3.19 per paired eligible episode across 42 of 50 episodes; the median is $0. With next-session conversion, the corresponding difference is −$1.38, also median $0. These denominators include known skipped sales as zero and exclude the eight unavailable paths explicitly. They are not a conditional win rate among seven entered trades.

MRVL provides a direct example: the 10:01 June 16 sale receives $2.24, while the 14:16 HIRO sale receives $1.25. With the same D4 cover, short-only P&L is $168.70 versus $69.70. Waiting for that flow reversal gave up $99 of premium in this episode. QCOM has a qualifying HIRO entry while its clock attempt fails the gates; neither anecdote establishes a general timing rule.

## What worked and what did not

The earnings refresh supplies 26,510 valid actual events for 315 of 323 names; eight names remain without dated coverage and nine invalid dates are quarantined. The one wider-delta variant creates a useful economic comparison. Minute-only data missed stale quote exposure at the ORCL D5 long exit. Exact event history repairs that interpretation without selecting another exit. IV/RR ranks and journey features are reported, but not silently promoted into new profitable-entry filters.

## Threats To Validity

Five-date concentration, current-universe survivorship, retrospective earnings knowledge, prior exploratory history, incomplete later HIRO archives, unverified dated deliverables/forward, and no early-assignment model prevent a validated execution or trading-edge claim. Extreme opening ask marks are displayed quote exposure, not proof of traded losses or maximum loss. Nonoverlap and date resampling preserve the observed dependence; they cannot create new independent episodes.

## Final Verdict

inconclusive

The declared statistical requirement is unmet and exact deliverables remain unavailable. The diagnostic economic findings above are retained; no live rule is promoted.

## Decision Impact

Keep the observed clock/HIRO comparison. This sample does not support promoting the tested HIRO reversal rule. More independent dated stock HIRO archives and exact contract metadata are required.

## Other Experiments To Run

See the indexed experiments and actual round 3 Charlie/Quant proposals. Completed audits, partial deliverable verification and data-dependent follow-ups are distinguished in the index. No additional band is selected from the observed profit paths.

## Independent Persona Commentary

[Actual round 3 commentary](../outputs/commentary/round3/H-PNDR-001.json)

### charlie-mcelligott

The event-required replay preserves zero admitted original sales and seven exploratory variant sale-policy cases across six stocks. Eight HIRO entries per variant remain unavailable, not known no-trades. MRVL is the sole admitted clock/HIRO pair: its D4 short-only result is $168.70 at 10:01 versus $69.70 at 14:16, with collected bid falling from $2.24 to $1.25, delta from 8.73 to 5.47 points, and OTM distance rising from 36.31% to 45.47%. This demonstrates changed entry exposure, not a general benefit or failure of HIRO. Actual-event age checks support the quoted timestamps; exact deliverables and the assumed 100-share multiplier remain unverified. Sources: event_admitted_case_comparisons.csv and event_replay_summary.json.

Keep all 100 stock/policy slots per variant, including known skips and unavailable flow histories. Do not condition the initial-timing comparison on successful sales or read classified HIRO flow as direct dealer-hedging evidence. Audit dated contract deliverables before upgrading these cash-flow diagnostics. Retain event-level short-phase exposure: next-session clock paths show adverse displayed cover losses of $279.30 for MRVL, $220.30 for CRM and $919.30 for ORCL. The ORCL observation is a fresh one-sided opening ask, not a traded loss or a maximum-risk bound. Source: tick_short_phase_exposure.csv.

### quant

Round 3 preserves all 50 episodes in each arm and all 4,000 policy rows. Actual event quotes leave the original arm with zero admitted sales, 92 known skipped stock/policy slots and eight unavailable HIRO entries. The variant has five clock and two HIRO sales across six stocks, with MRVL appearing in both policies. For next-session conversion at D4 and one-cent slippage, HIRO minus clock averages -$1.381 over 42 fully priced episode pairs out of 50; its median is zero. The short-only comparison is also negative (-$3.190 per priced pair). Other timing arms have different signs, which does not justify selecting a favorable method after inspection. Five shared entry dates are one frozen five-session block: all 2,000 block draws repeat the same sample, so there is no confidence interval or statistical pass.

Close this pilot as inconclusive for a HIRO entry advantage. Retain the eight missing HIRO paths as unavailable and the observed no-entry policies as zero; do not compare only the two successful HIRO entries with the five successful clock entries. Keep the original zero-entry finding separate from the exploratory delta10/OTM5 result. Event age is now checked, but assumed 100-share deliverables, retrospective earnings exclusions and current-universe membership still limit execution and historical inference. Any replication should use one later chronological block and the unchanged rules, with no choice among timing results based on this sample.
 The earlier notes and commentaries remain in the immutable [round 1 snapshot](../outputs/pandar_hypothesis_2026-09-07/round1_snapshot/h-pndr-001_hiro_entry_2026-09-07.md) and [round 2 snapshot](../outputs/pandar_hypothesis_2026-09-07/round2_snapshot/h-pndr-001_hiro_entry_2026-09-07.md).

## Reproduction

Use `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python`. Run `-m scripts.pandar_hypothesis_run`, `-m scripts.pandar_hypothesis_event_replay`, `-m scripts.pandar_hypothesis_event_exposure`, and `-m scripts.pandar_hypothesis_report`. The [resampling artifact](../outputs/pandar_hypothesis_2026-09-07/block_resampling.json) records its input hash and specification. The [event summary](../outputs/pandar_hypothesis_2026-09-07/event_replay_summary.json) records source hashes; the [call budget](../outputs/pandar_hypothesis_2026-09-07/api_budget.json) records all 1,363 provider attempts within the 2,000 authorization. Round closure requires `scripts/_research_loop/verify_round.py --round 3` to return zero.

## Feynman Explanation

HIRO has to earn its waiting time. In MRVL, the call sold for $224 at the clock time and only $125 when HIRO later triggered. Both positions could then be covered at the same deadline, so waiting cost $99. That is one episode, not a law. We also count stocks where no sale happened, and leave missing signal histories unknown.

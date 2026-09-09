# Pandar call research decision memo

**Status:** living
**Date:** 2026-09-07
**Verdict:** inconclusive
**Decision:** Continue exact-contract research; no live-rule promotion.

## 1. Executive Summary

Continue the fixed-contract replay. The current verdict is inconclusive: the original near-five-delta pairs fail the entry price/liquidity gates. One separately frozen higher-delta variant has six stocks passing preliminary entry checks; its profit paths have not selected the rule. Their five entry dates are enough to examine individual trades and data failures, but too few to establish a repeatable advantage under the frozen statistical criterion.

## 2. What We Tested And Why It Mattered

[Three claims](RESEARCH_HYPOTHESIS_INDEX.md): whether HIRO improves the initial sale, whether a later nearer-call purchase adds value, and whether a rich call wing starting to contract helps identify better short sales. [Frozen protocol](pandar_seed_and_frozen_protocol.md).

## 3. What We Found

The earnings API recovered dated history that the empty next-earnings fields did not provide. Fifty nonoverlapping episodes remain after the user-authorized actual-event exclusions and preliminary HIRO coverage checks. The original calls fail the project entry quote limits; a separately frozen 5–15 delta variant identifies six preliminary stocks. Exact deliverables and event quote age remain unverified.

## 4. Timeline — What Actually Happened

| Round | Date | Step | What happened | Artifact |
|---|---|---|---|---|
| 1 | 2026-09-07 | Earnings and population freeze | 26,510 valid earnings events; fifty episodes on five June entry dates; every failed row retained. No new option outcome histories evaluated. | [Population manifest](../outputs/pandar_hypothesis_2026-09-07/population_manifest.json) |
| 2 | 2026-09-07 | Exact entry feasibility and one frozen variant | The original 49 pairs produced zero preliminary eligible entries. The 5–15 delta variant, targeting 10 delta and at least 5% OTM, freezes 47 pairs and identifies six preliminary stocks. Exact deliverables remain unverified. | [Variant freeze](../outputs/pandar_hypothesis_2026-09-07/variant_freeze.json) |

## 5. The Decision And Its Consequences

Collect the fixed calls' signal chains, entry snapshots and complete holding-window quotes. Keep profit comparisons separate from evidence that a trade met every execution requirement. The historical earnings purge is authorized research; it does not establish historical calendar availability.

## 6. Open Questions / Next Step

Can the preselected calls be verified and quoted well enough to compare buying the nearer call with closing the original short?

## 7. Feynman Explanation

A profitable spread can still be a poor second decision. We will start each comparison with the same short-call sale and ask what happened to the money if we bought the nearer call later, bought it immediately, or simply closed the short.

The list of candidates is fixed before the new profit paths are examined. A failed entry stays in the results, and a missing price stays missing. That keeps a handful of attractive examples from masquerading as a rule that usually works.

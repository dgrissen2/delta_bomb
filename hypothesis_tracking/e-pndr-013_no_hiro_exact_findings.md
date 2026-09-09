# E-PNDR-013 findings: exact-call selection without HIRO

Parent: [H-PNDR-003](h-pndr-003_skew_rollover_2026-09-07.md). [Index](RESEARCH_HYPOTHESIS_INDEX.md). Separately frozen follow-up experiment; this does not replace or reopen the original three-round pilot.

**Verdict: inconclusive for relative selection advantage; no demonstrated profitable strategy or new-name discovery.** The economic selector loses money on its priced trades. Its positive point estimate against the mechanical policy has an interval crossing zero, substantial differential missing exits, and a large participation difference.

## Target and frozen method

[Protocol](pandar_no_hiro_exact_protocol_2026-09-08.md) · [Detailed results](../outputs/pandar_no_hiro_exact_2026-09-08/exact_chain_results.md) · [Combined plain-language report](../outputs/pandar_no_hiro_2026-09-08/pandar_no_hiro_research.md).

At the signal snapshot, enumerate listed OTM calls with 1–35 calendar days remaining and expiry extending through the common closing deadline. Compare the estimated benefit of removing one quarter of the call-bid-IV excess over same-expiry spot-ATM IV, after quote width and costs, with the local dollar loss from a 1% stock rally. Gross estimated recovery cannot exceed the current ask value. There is no additional delta or percentage-OTM band. The control chooses the expiry nearest ten days and the call nearest ten delta. These are research proposals, not Pandar's stated rules.

Keep the selected contract at next-session entry; recheck its actual quote and economics without replacing a failed selection. Close four sessions after entry, with two sessions as a secondary horizon. All policies share input availability, earnings exclusions and nonoverlap reservations. Known no-entry has zero policy P&L; unavailable entry or exit evidence stays censored. No HIRO data, coverage or timing is used. The original 323-name membership supplies stock names only.

## Actual sample

- Full-chain signal/entry inputs and quality/earnings gates admit **1,163 stock-dates, 71 stocks, 203 signal dates**, January 10, 2024–June 15, 2026.
- The common nonoverlap population contains **273 cases across 119 dates and 71 stocks**.
- Across all signals, 552 cases across 139 signal dates and 42 stocks have a priced four-session exit for at least one policy. Input availability is not equivalent to completed-trade coverage.
- The economic selector chooses **107 signal contracts; 74 fail its positive-net-scenario recheck at next-session entry; 33 enter**. Those entries span five of the previous six studied names; 32 have priced exits. No economic entry is in a newly added name.
- Only **eight economic entries** remain in the common nonoverlap sample, across four stocks and eight entry dates. All eight have priced exits. The control enters 260 times; 129 exits are priced and 131 are censored.

## Results

Dollar amounts are per assumed standard 100-share contract. Sales use entry bid minus $0.01/share; covers use exit ask plus $0.01/share; each action costs $0.65. These are hypothetical daily-quote executions.

| Common nonoverlap, four sessions after entry | Economic selector | Mechanical control |
|---|---:|---:|
| Priced trades | 8 | 129 |
| Mean net priced-trade P&L | −$401.43 | −$67.52 |
| Median net priced-trade P&L | −$62.30 | +$4.70 |
| Positive priced trades | 3/8 | 79/129 |

Those trade-conditioned columns have different participation and missingness; they are not a controlled head-to-head comparison.

The primary paired policy difference is **+$38.72 per observed case**, 95% whole-month bootstrap interval **[−$7.94, +$118.78]**, across 142 common cases and 14 month blocks. Known skips contribute zero; unknown exits do not. The 2024–2025 point estimate is −$5.92 and the 2026 estimate +$74.32; both intervals include zero.

On the same eight cases where both policies enter and both exits are priced, the economic calls total **−$3,211.40**, against **−$7,119.40** for the mechanical calls. The difference is smaller losses, not a profitable strategy. The mean difference is +$488.50, but its median is −$15.50 and its interval crosses zero. The other 134 paired cases contribute a combined +$1,590.30 because the economic policy stays flat. Excluding the prior six names leaves no economic entries; its positive policy-difference point estimate therefore supplies no evidence of new-name strike selection.

## What the failures teach

MRVL's May 29 entry sold the June 18 $320 call at a $0.77 bid. It was 4.20 delta and 55.74% OTM. Its wing subsequently narrowed 16.96 IV points, while ATM IV rose 30.88 points and the stock snapshot rose from $205.47 to $316.56. Covering at the June 4 $28.05 ask produced **−$2,731.30** after specified costs. Wing narrowing alone did not protect this short call.

ORCL's May 4 $210 call lost **$105.30** even though its fixed-strike mid IV fell 5.46 points: the stock rose from $180.95 to $196.03. The local 1%-rally denominator is inadequate as a stress-risk measure. These examples were selected for explanation after evaluation, not used to tune the frozen rule.

The method does adapt its chosen strikes: all 33 economic entries range from 0.83 to 19.42 delta, 12.23% to 70.92% OTM and 4 to 31 calendar DTE. That flexibility alone does not establish good selection. Keep quote-cost and wing-sensitivity diagnostics; do not promote the wing/1%-rally ratio or loosen another threshold to manufacture more winners.

## Validity limits and review

The chain cache was assembled for earlier research, including an explicitly winner-recreation-named source. Freezing source precedence now cannot undo prior sample selection. Broad current membership applied backward also has survivorship limitations. Earnings exclusion uses actual retrospectively recorded events, not proof of schedules known then. Daily chains often drop contracts below five DTE, producing extensive and unequal outcome censoring. Historical deliverables, American assignment and quote-event freshness are not fully verified. This preliminary spot-ATM sensitivity screen does not meet the separate 60-prior-observation, comparable-delta/DTE and comparable-forward-moneyness/DTE richness requirements.

Charlie implemented the frozen selector and identified the next-session participation collapse. Brent independently checked the distinction between profitable calls, smaller losses and gains from staying flat. Both are canonical persona simulations in native Codex agents. The root independently reconciled unique records, selection/entry counts, every priced final-trade cash flow and the primary paired mean. No new provider calls were made; shared acquisition usage remains 1,363/2,000.

## Reproduction

From the repository root, run `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python scripts/pandar_no_hiro_exact.py`. Input and selection hash manifests, the complete candidate/failure ledgers, source conflicts and exact quote observations are retained under `outputs/pandar_no_hiro_exact_2026-09-08/`. Fourteen causal, quote-validity, accounting and end-to-end tests and Ruff passed. [Final validation](../outputs/pandar_no_hiro_exact_2026-09-08/validation.json) confirms 3,072 input/source hashes remained unchanged, the selection/candidate freeze remained unchanged, and quote-side fee arithmetic reconciles. [Brent's independent review](../outputs/pandar_no_hiro_exact_2026-09-08/brent_exact_review.json) records interpretation limitations.

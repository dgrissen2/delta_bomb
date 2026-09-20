# B09 MAD follow-up: two transfers and one index hypothesis

September 20, 2026. **Proposal only. No new B0x overlay outcomes or SPX MAD outcomes have been calculated.**

This applies the canonical global Charlie McElligott positioning framework within the current conversation. It is a simulated analytical lens, not the real person and not an independent reviewer. The requested independent Claude strategy review is **NOT RUN / PENDING** because this side conversation prohibits separate reviewer agents. Nothing here is a Charlie or Claude sign-off.

## Recommendation in plain terms

Test the two fixed four-sector rules on **B07 first and B05 second**, publishing both regardless of how the first performs. That is four transfer cells, not another parameter sweep. B07 tests a failed selloff; B05 offers a larger pool of stalled-selloff entries. Keep B03 and thrust as existing references rather than adding more candidates to this round.

An **SPX-options IV MAD** test is also worth investigating. Start by measuring the same 30-day ATM IV quantity on the index itself, then ask whether it identifies successful B09 entries that sector confirmation misses. This is a separate hypothesis with a data-readiness step; the existing SPX caches inspected here do not establish readiness for that calculation.

The objective remains **SPX +5 before −10 within 60 minutes**. A reversal after the first +5 does not turn a winner into a loser. We are looking for a useful balance of hit rate, retained opportunities, and half-year consistency. No claim about a sustained rally is needed.

## What is already committed

- Project results, implementation, verification, all 48 cells, and extensive learning notes: `19485384ecbaf57af456bd4c4bc16464900291c6`.
- Central dataset provenance, dictionary, and changelog: `8bcb0701674caf39fae531f4d8a47b3e92473c41`.
- Canonical research notebook: [section 11.31](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/OHLCV_BRANCH_COMBINATIONS.md:1646).
- [Completed findings](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_grid_2026-09-19/FINDINGS.md), [all 48 results](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_grid_2026-09-19/ALL_48_RESULTS.md), and [extensive commit notes](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_grid_2026-09-19/COMMIT_NOTES.md).

Those experiment documents were written before this documentation/commit request; their original statements that no commit was requested or made describe that earlier execution stage.

## The fixed rules to carry forward

“Same winners” means the **same indicator definitions**, applied to every eligible entry of the new parent. It never means selecting historical winning trades and searching their characteristics.

| Fixed rule | Exact sector condition | Existing B09 result | B09 with 60-minute spacing |
| --- | --- | --- | --- |
| S4: downward acceleration | At least 4 of the fixed 11 ETFs have M > 1 | 139/235 = 59.1% | 84/142 = 59.2% |
| F4: downward acceleration with IV falling | At least 4 of the same 11 ETFs each have M > 1 AND b2 < −1e−12 | 115/188 = 61.2% | 76/121 = 62.8% |
| Plain B09 reference | No IV filter | 1704/3141 = 54.3% | 285/554 = 51.4% |

For each ETF, b1 and b2 are the actual-time IV slopes in the first and second 15-minute halves of the 30-minute window. Acceleration a = (b2 − b1)/15; M = −a / (1.4826 × historical MAD). The same ETF must satisfy both conditions in F4. “IV falling” means a negative slope in the most recent 15-minute half; it does not require every minute to decline. S4 can admit positive IV slopes that are slowing sufficiently.

Keep the existing 30-calendar-day ATM midpoint-IV construction, quote guards, recovery rules, support requirements, and baseline weighting. MAD uses 60 strictly prior sessions, the same ETF/hour, all regimes and both signs, with equal total weight per date. M is a signed scaled magnitude; it is not a percentile, probability, or median-centered z-score.

The two five-sector counterparts remain documented accuracy references: 53/80 = 66.3% for acceleration alone and 43/64 = 67.2% with IV falling. Do not transfer them in this first round: the goal is to improve N, and their existing samples are much smaller. Thresholds 2–4 and breadth 6–9 remain published findings, not invitations to choose different cutoffs on each price setup.

## Charlie-framework interpretation, with limits

The useful hypothesis is that a local price recovery works more often when option-implied uncertainty is relaxing unusually quickly across several sectors. That makes a failed downside break and a stalled pullback sensible transfer candidates. This is a hypothesis about contemporaneous information, not evidence that a particular dealer, CTA, or volatility-control fund bought. We have not measured their inventories or flows, and a 30-minute IV change cannot establish a multi-day mechanical allocation story.

S4 and F4 address different stages of that relaxation. S4 can catch a market where IV is still rising but the rise is slowing; F4 waits until the recent IV slope is negative. Keeping both fixed lets the price setup determine whether that earlier admission adds useful +5-first opportunities. Do not assume slowing IV is always bullish, or that rising IV automatically rules out an upward move.

The key weakness is selection: four cells emerged from 48 correlated candidates on already examined dates. Their favorable completed-half pattern is interesting, but this transfer study would still reuse those market periods. It is a portability check, not a fresh out-of-sample proof. Both four-sector rules underperformed plain B09 in partial 2026 H2, on only ten and seven qualifying signals. Preserve that fact.

## Transfer 1: B07, failed breakdown and reclaim

B07 freezes an earlier range before the probe. Price trades below its low, reclaims the range, then a later one-minute close breaks above the frozen reclaim candle's high. This is not necessarily a break above the entire range high. Keep the existing range construction, assessment bars, cancellation, expiry, entry timing, and overlapping-episode policy unchanged.

The proposed question is: **after sellers fail to keep price below an established floor, does broad IV relaxation improve the chance of +5 before −10?** F4 may distinguish a recovery accompanied by declining implied uncertainty from a temporary rebound while uncertainty continues to rise. S4 tests whether requiring IV already to be falling waits too long. Neither claim has been established for these new rules on B07.

Run only B07 + S4 and B07 + F4, versus unfiltered B07 and the corresponding definite nonqualifiers. A higher pooled percentage alone is insufficient if one half accounts for the difference, the spacing check removes it, or almost all parent winners are excluded.

## Transfer 2: B05, stall and reclaim

B05 uses the existing eight-point pullback, five one-minute bars without a new running low, and a close above the running mean typical price since that low. The average is not VWAP. Preserve the implemented state initialization, 15-bar refire restriction, and all entry rules; do not silently replace its above-mean condition with a newly optimized crossing rule.

The proposed question is: **when price stops making new lows, does broad IV relaxation help distinguish a usable recovery from a pause before another decline?** This has a direct mechanism to test and a larger eligible price-signal pool than B07 or the five-minute staircase. More parent events create room for N; they do not guarantee more independent opportunities after filtering.

Run only B05 + S4 and B05 + F4. This is the high-N challenger. B05's weak partial-2026-H2 baseline is a counterexample to take seriously, not a period to discard.

## Why these parents, rather than a new B01–B10 sweep

The table below is read from the existing price/IV comparison artifact, restricted to 2025–2026. These are **unfiltered parent results**, not new MAD-overlay findings. H2 2026 ends September 18.

| Parent | 2025 H1 | 2025 H2 | 2026 H1 | 2026 H2, partial | Combined |
| --- | --- | --- | --- | --- | --- |
| B07 | 69/121 = 57.0% | 75/155 = 48.4% | 66/105 = 62.9% | 23/34 = 67.6% | 233/415 = 56.1% |
| B05 | 246/420 = 58.6% | 297/565 = 52.6% | 265/447 = 59.3% | 46/105 = 43.8% | 854/1537 = 55.6% |
| B03, five-minute staircase reference | 33/61 = 54.1% | 31/63 = 49.2% | 32/52 = 61.5% | 10/13 = 76.9% | 106/189 = 56.1% |

B03 is a sensible structural comparison to B09, but its 189 parent events offer less room for this specific high-N objective than B05's 1,537. An earlier persona-panel proposal nominated B03 as a challenger; this recommendation explicitly changes that choice because the current objective emphasizes N. It does not claim that a B05 MAD overlay has already beaten a B03 overlay.

Do not add B06, B08, opening-range variants, new cooldowns, alternate sector baskets, or new price thresholds to this round. A failed transfer should not trigger a search for a different parent until one happens to work.

## Common evaluation contract for the four transfer cells

1. Use the existing research population for January 2025–September 18, 2026; exclude development dates. No full-2024 MAD claim. Reconcile each parent against the stored baseline before attaching IV classifications. Record why any events cannot be reproduced.
2. Require the same causal above-VT rule: every previous RTH minute low and the entry open strictly above that day's VT. Never select entries using whether the market stays above VT later that day.
3. Use only the exact window ending T−1 at entry T. Every actual quote timestamp must be inside T−30 through T−1. No nearest-endpoint substitution or future observations. Historical calibration must end before the current session.
4. Freeze the four memberships, input hashes, and code before reading outcomes. Keep yes, definite no, and unknown separate using the existing bounded count logic. No renormalization to the ETFs that happen to be available.
5. Reuse the unchanged +5-before−10, 60-native-minute-bar outcomes, including entry. Only target_first wins; neither, adverse_first, and ambiguous remain in N. No post-+5 persistence requirement.
6. Report all entries, first qualifying entry per day, and greedy 60-minute spacing. Filter before spacing, reset by day, and compare with the corresponding unfiltered parent policy. No outcome-based reopening.
7. Publish N, wins, hit rate, active dates, winners retained/excluded, worst completed-half uplift, and each half separately. Compare both to the full parent and to its measurable yes-plus-no population. Report unknown outcomes explicitly.
8. Reuse whole-date uncertainty with shared parent/filter date draws. Label it descriptive and unadjusted for the prior search; many signals from one day do not constitute many independent tests.
9. Keep the previous stability criterion: positive observed uplift in each completed half, then compare retained N and worst-half accuracy. Publish failure or insufficient evidence as such. Do not change an accuracy floor, N floor, or half-year set after seeing results.
10. Report timestamp overlap with accepted B09 entries as a descriptive measure of possible new opportunities. Do not add overlapping counts together and call the sum new trades. A combined execution portfolio would require its own fixed overlap/spacing policy before testing.

A useful attribution control, specified before outcome access, is the same four-sector count with the same measurement and timing but **a < 0 alone**, or **a < 0 AND b2 < −1e−12** for the falling family. These two simpler controls per parent test whether the MAD magnitude requirement contributes beyond the sign conditions. They add four declared control cells to the four primary cells; report all eight, and do not promote whichever control happens to win as a new optimized strategy. This comparison matters because the older IV recipes also differed in clock, quality policy, and sector count.

## SPX-style MAD: one different source of information

Here “SPX-style” means applying the existing IV-acceleration normalization to **SPX options themselves**. It does not mean a MAD of SPX price returns, a VIX substitution, or an option-expiry sweep.

The sector measure asks how broadly implied uncertainty is relaxing. The index measure asks whether the market's price of index-option uncertainty is relaxing. They may disagree. A useful SPX result would be successful additional B09 entries when the sector rule definitely does not qualify. Agreement alone may improve accuracy while reducing N; it does not answer the high-N question.

Start with one defined measurement and one rule:

- Use a verified PM-settled SPXW contract universe. Keep AM- and PM-settled contracts distinct. Cboe specifies different expiration trading cutoffs for standard SPX and SPXW, so root/settlement and actual time-to-expiry must be recorded. [Cboe specifications](https://www.cboe.com/tradable-products/sp-500/spx-options/spx-specifications).
- Target the same 30-calendar-day, spot-ATM midpoint-IV quantity. Use the existing variance/total-variance interpolation and allowed 8–65-day expiry range, with an exact tenor or a genuine bracket and no extrapolation. Preserve the sector methodology's call/put construction. Do not select deltas or expiries using outcomes.
- Fetch missing observations, if execution is later requested, through the ThetaData Python SDK IV-history endpoint at `interval="1m"`, preserving bid/mid/ask IV, quote prices, actual quote and underlying timestamps, request parameters, and provenance. The endpoint supports one-minute requests. Its overview describes bid/mid/ask IV, while one response-field description uses trade wording; verify field behavior in the returned data rather than silently substituting a trade-IV endpoint. [ThetaData Python documentation](https://docs.thetadata.us/operations_python/option_history_greeks_implied_volatility.html).
- Verify index model inputs, contract identity, IV units, source ages, tenor roll continuity, and quote guards before using outcomes. A more liquid underlying does not automatically eliminate stale quotes or numerical artifacts. Do not assume index IV changes prove fresh option demand.
- Use the same T−1 endpoint, two 15-minute slopes, acceleration formula, and same-hour 60-prior-session MAD baseline. Include all regimes and both signs in calibration, not only above-VT or winning dates. Do not pool the SPX baseline with ETF baselines.
- Freeze one rule: **M_SPX > 1 AND b2_SPX < −1e−12**. This is the index counterpart to F4; there is no sector count for one index. M > 1 need not have the same empirical frequency in SPX as in an ETF.
- Apply it to B09 first, on the same 2025–2026 population. Do not cross every SPX threshold with every B0x parent. Do not introduce 0DTE, 7DTE, skew, delta variants, or strike-level surfaces into this initial test.

Cross-classify it against fixed sector F4:

| Sector F4 | SPX rule | Question |
| --- | --- | --- |
| Yes | Yes | Does index agreement change the hit rate of entries already accepted? |
| Yes | Definite no | Would requiring index confirmation discard useful existing winners? |
| Definite no | Yes | The key incremental-N group: does SPX identify useful opportunities sector F4 excludes? |
| Definite no | Definite no | What does the jointly measurable remainder do? |

Keep every combination containing an unknown as separate coverage groups. In particular, SPX-positive/sector-unknown events are possible coverage recovery, not evidence that SPX outsmarted a definitively negative sector signal.

Freeze one descriptive OR comparison in advance: sector F4 yes **or** SPX yes, with membership determined before outcomes and deduplication by parent entry. Separately attribute additions to sector-definite-no and sector-unknown. Publish the incremental group's rate by half, as well as the combined rate and N, using the same spacing rules. If added entries dilute accuracy or their advantage is isolated to one period, increasing N alone is not success. The common-population comparison must also show whether any apparent gain is simply different data availability.

Do not infer that an SPX signal measures dealer gamma, vanna flow, or implied correlation. Those would require additional measurements. This proposal tests an IV feature's incremental association with +5-first outcomes.

## SPX data readiness: what was actually inspected

The following is a bounded local inventory, not a claim that every possible cache has been audited:

| Existing cache under central_trade_data/thetadata | Observed inventory | Why it does not establish readiness |
| --- | --- | --- |
| `spxw_gamma_term_1m/first_order` | 1,065 Parquets: 355 each named 0dte, next_daily, and 3to5dte; sampled schema includes implied_vol and quotes | Short-tenor gamma research data, not a complete 30-day expiry bracket or bid/mid/ask-IV history for all calibration sessions |
| `spxw_bomb_chains` | 22 Parquets, August–September 2026; sampled schema min/strike/bid/ask/delta/underlying_price | Recent put-chain marks; no native IV fields or complete historical bracket/calibration coverage established |
| `spxw_marks` | 31 Parquets, September 2026; same sampled quote/delta schema | Short recent marks cache, not a ready 2025–2026 SPX MAD baseline |

No completed SPX MAD/calibration dataset was identified by the targeted filename search. Before collection, build an expiry/date/source coverage inventory, verify actual SDK contract symbology, and identify reusable data. The required scope is the same 2025–2026 evaluation dates plus every session needed for their 60-session calibration histories. A few IV observations at B09 entries are not sufficient to build that baseline.

Any future raw data, derived surfaces, calibration files, and result tables belong under `/Users/dgrissen/Dev/central_trade_data/` in a separate versioned namespace, with its changelog and data dictionary updated. This proposal fetched no market data.

## What would change the recommendation

- If F4's improvement disappears under the same-time, same-quality raw-sign control, do not credit MAD magnitude for an advantage it has not shown.
- If B07 or B05 gains only on one half or overlapping clusters of signals, record a failed/fragile transfer rather than adding exceptions.
- If the SPX-positive/sector-negative group fails to improve on its corresponding excluded-entry benchmark, a favorable agreement group does not establish incremental opportunity value.
- If SPX quote/expiry coverage is poor or the signal comes mainly from surface construction discontinuities, resolve measurement first; no rule should compensate for untrustworthy observations.
- If the evidence remains thin, freeze the definitions for later genuinely new sessions. Adding previously examined dates or more rule variations is not equivalent to independent confirmation.

## Source trail and review handoff

- Canonical persona applied: [Charlie framework](/Users/dgrissen/.config/persona-review-kit/personas/market/charlie-mcelligott.md).
- Parent counts: [existing comparison.csv](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_iv_full_2024_2026_2026-09-19-v1/comparison.csv), baseline/all/all rows for 2025_H1, 2025_H2, 2026_H1, 2026_H2.
- Exact parent rules: [B07 protocol](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/B07_B08_PROTOCOL.md), [B05 implementation](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/b05_signals.py).
- MAD contract: [completed protocol](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_grid_2026-09-19/PROTOCOL.md).
- [Independent strategy-review request and pending status](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_followup_plan_2026-09-20/STRATEGY_REVIEW_STATUS.md).

Recommended sequence: finish the independent logic review in a context that permits it; run the four fixed transfer cells plus the explicitly declared attribution controls; assess SPX data readiness and measurement before its single-rule B09 comparison. These are proposals, not executed or approved new strategies.

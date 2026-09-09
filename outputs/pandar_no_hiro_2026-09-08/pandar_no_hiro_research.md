# Pandar research on a larger sample, without HIRO

**HIRO is excluded from these tests.** There are no flow features, HIRO entry signals or HIRO coverage gates. The previous 323-stock list supplies the names, so the study can reach older dates where no HIRO observations exist. The authorized exclusion for actual earnings on the decision date or in the next 30 calendar days remains in force at signal and entry.

The larger sample does not support the two new rules tested here. Slowing skew expansion did not improve the specified wing-normalization outcome. A selector based on net wing-collapse sensitivity admitted few next-day trades and lost money on average. These results reject easy shortcuts; they do not establish that every form of skew mean reversion is useless.

## Exactly how much data

| Layer | Distinct signal dates | Stocks | Stock-date cases | What it establishes |
|---|---:|---:|---:|---|
| Broad eligible, high-wing surface study | **643** | **304** | **17,458** | Changes in standardized IV coordinates; not option P&L |
| Exact-chain signal/entry study | **203** | **71** | **1,163** | Both input snapshots exist and quality/earnings gates pass |
| Exact-chain cases with a priced four-session exit for at least one policy | **139** | **42** | **552** | Hypothetical exact-call P&L at quoted sides |

Surface signals run January 2, 2024–August 4, 2026. The underlying panel has 921 sessions starting in January 2023, but history used for warmup is **not counted as a traded or evaluated day**. There are 671 possible evaluation dates; coverage and admission reduce the analyzed set to 643. The actual-event 30-day gate prevents the most recent dates from being treated as cleared before their full earnings horizon is covered.

Exact-chain input cases run January 10, 2024–June 15, 2026, with gaps. They are drawn from existing research caches, not an evenly sampled market-wide tape. Later missing exits remain missing; they did not determine which signal cases were admitted.

## Test 1: does waiting for skew expansion to slow help?

Before measuring outcomes, freeze a prior-only rich-wing condition and a simple state: compare the latest three-session wing slope with the previous three-session slope. The wing here is ten-calendar-day five-call-delta IV minus matched ATM IV. Five delta identifies a measurement coordinate; it is **not a rule requiring us to sell five-delta calls**.

Reference the next daily snapshot and then measure two sessions forward:

| Outcome | Slowing/rolling | Continuing/accelerating |
|---|---:|---:|
| Wing narrows | 59.18% | 58.81% |
| Wing narrows **and** ATM stays flat/rises | 26.14% | 28.08% |
| Wing narrows, ATM stays flat/rises, **and total call IV falls** | 13.27% | 13.32% |

The proposed slowdown advantage is not supported. The primary difference is −1.94 percentage points. After controlling for starting wing/ATM, stock and month, the difference is −0.91 points with an interval spanning zero. The common nonoverlap and chronological checks do not rescue the rule.

These are joint outcomes. They are not conditional probabilities given a future ATM rise, and none is a short-call win rate. A narrower wing can coexist with a much higher total call IV. The moving five-delta coordinate also represents different actual contracts over time.

There is a useful timing clue: much narrowing already occurs between the signal and the next daily reference. That observation motivates checking when an executable opportunity exists; it does not prove we could sell at an earlier price using information available only later.

[Full surface results](no_hiro_surface_results.md) · [Frozen protocol](../../hypothesis_tracking/pandar_no_hiro_surface_protocol_2026-09-08.md) · [Findings](../../hypothesis_tracking/e-pndr-012_no_hiro_surface_findings.md).

## Test 2: can actual dollar economics select better strikes?

This search compares every supported listed OTM call in a 1–35-calendar-day expiry envelope, provided it lasts through the common exit. There is no narrow delta band or minimum percentage OTM. The exact selected contract stays fixed at next-day entry; a failed contract is not replaced by another one.

For each contract:

1. Measure call **bid IV minus same-expiry spot-ATM mid IV**, in IV points.
2. Estimate the dollar gain from removing one quarter of that positive wing while holding spot, time and ATM IV constant. This is a scenario, not a forecast. Cap the estimate at the current ask value to avoid an impossible negative buyback price.
3. Subtract the displayed bid/ask width, fees and specified slippage.
4. Divide the remaining scenario dollars by the local delta/gamma loss from a 1% stock rally. Select the highest positive ratio. Save local-strike kink measures separately.

The control uses the expiry nearest ten days and the call nearest ten delta. Neither rule is attributed to Pandar.

The economic rule finds **107 signal-day selections**. By the actual next-session snapshot, **74 no longer clear its positive-net-scenario condition**, leaving **33 entries on 28 dates**. Thirty-two have priced four-session exits; their mean is **−$77.27 per contract**. All 33 entries are in five of the six previously studied stocks. The larger search found no additional-name entries under this specification.

Common nonoverlap reservations reduce these to **eight entries across four stocks and eight dates**. Those eight lose a combined **$3,211.40** after costs, with three positive results. The mechanical control enters 260 times in that same 273-case population; only 129 exits are priced and 131 remain censored.

The paired policy comparison has a positive point estimate, **+$38.72 per observed case**, but its 95% month-block interval is **−$7.94 to +$118.78**. Staying flat contributes to the comparison. On the same eight cases where both policies trade, the economic calls lose $3,211.40 and the control loses $7,119.40. That is smaller loss in a tiny selected sample, not a profitable strike-selection result.

## Three actual quote replays

All entries below passed the frozen economic rule, use the original selected strike, and close four sessions after entry. Selection for this explanatory table occurred after the test; it is not a success-rate sample. Dollar P&L assumes one standard 100-share contract, bid-side sale, ask-side cover, $0.01/share slippage per side and $0.65 per transaction.

| Entry / exit | Contract sold | Entry delta | Entry % OTM | Entry bid → exit ask | Net P&L |
|---|---|---:|---:|---:|---:|
| Dec 22 → Dec 29, 2025 | ORCL Jan 16, 2026 $250 call | 5.20Δ | 26.15% | $0.54 → $0.16 | **+$34.70** |
| May 11 → May 15, 2026 | QCOM May 15 $300 call | 5.53Δ | 27.60% | $0.80 → $0.01 | **+$75.70** |
| May 29 → Jun 4, 2026 | MRVL Jun 18 $320 call | 4.20Δ | 55.74% | $0.77 → $28.05 | **−$2,731.30** |

MRVL shows precisely why skewness and total IV must be separated. Its fixed-strike mid-IV wing **fell 16.96 points**, but matched ATM IV **rose 30.88 points**. Total call mid IV therefore rose 13.93 points. The stock snapshot also rose from $205.47 to $316.56. Even a call initially 55.74% OTM suffered a large loss.

At entry, the MRVL estimate was only **$18.09 gross gain** from a 4.14-point wing decline, less **$12.30 in modeled quote costs and fees**, leaving **$5.79**. Its modeled loss from a 1% rally was $9.01. That ratio compares small local changes; it cannot describe the exposure during a much larger rally.

ORCL supplies a different failure: the May 4 $210 call's IV fell 5.46 points, yet the call sale lost $105.30 as the stock rose from $180.95 to $196.03. Even actual IV contraction does not by itself establish profitable selling.

## Charlie and Brent's practical conclusion

**Keep the economic questions; do not promote this particular score.** Compare the premium available after quote costs with what plausible changes in spot, ATM IV and wing shape do to the entire position. Delta and percentage OTM describe exposure and distance. Neither establishes that the price compensates for the risk.

The broad study gives no reason to require the tested slowdown state. The exact study gives no reason to declare the highest wing/1%-rally ratio a good trade. The 33 entries span **0.83–19.42 delta, 12.23–70.92% OTM and 4–31 calendar DTE**: the selector already flexes across strikes, yet the priced results remain poor.

The next distinct hypothesis should value the **whole candidate position under larger joint spot/ATM/wing scenarios**, including any hedge cost, before comparing it with available premium. A higher-strike protective call and a later purchase of a lower-strike call have different objectives and payoffs. They must be priced as separate policies. No long call was silently added to this test. A local kink is useful only with supported neighboring quotes; a positive residual by itself is not evidence of executable mean reversion. This follow-up is a research direction, not a validated replacement rule.

Canonical Charlie and Brent personas reviewed the work through Codex agents. These are persona simulations, not statements from the actual individuals. [Selection reasoning and calculations](../pandar_strike_selection_explainer_2026-09-08/charlie_brent_good_trade_method.md) · [Exact-chain findings](../../hypothesis_tracking/e-pndr-013_no_hiro_exact_findings.md) · [Exact-chain report](../pandar_no_hiro_exact_2026-09-08/exact_chain_results.md).

## Evidence limits and audit trail

The exact-chain sample comes from earlier research caches, including an explicitly winner-recreation-named source. It cannot be treated as an unbiased or unseen validation sample. Excluding the previous six stocks leaves no economic entries; that sensitivity tests the benefit of skipping, not successful new-name selection. Unequal missing exits further limit comparisons. The larger surface panel has 32 month blocks, not 17,458 independent trials.

Historical deliverables and quote-event freshness remain unverified; the calculations assume standard 100-share contracts. The preliminary exact-chain score uses spot-ATM and does not claim the separately required 60-observation comparable-delta/DTE and comparable-forward-moneyness/DTE historical richness clearance. All missing observations and failed selections are retained. Daily option snapshots are quoted observations, not proof of fills or complete intraday risk.

Input/selection freezes, candidates, failure ledgers, quoted cash flows and month-block comparisons accompany both reports. The root independently checked final-trade arithmetic and sample counts. This work used **zero new provider calls**; shared authorized usage remains **1,363 of 2,000**.

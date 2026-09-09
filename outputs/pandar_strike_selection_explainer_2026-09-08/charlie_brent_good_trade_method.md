# Finding a good call-tail sale: Charlie and Brent review

September 8, 2026. Research proposal, with a new sensitivity calculation from cached June 15 quotes. No new outcome backtest or provider calls in this note. The frozen June protocols and reported results are unchanged. **User update: exclude HIRO entirely from the current research; use the existing ticker names but do not require historical HIRO data or use flow in selection, timing or outcomes.**

**The proposed objective is to find removable option premium that is large enough to pay for execution and justify the exposure taken while waiting.** A richness percentile describes unusual pricing. It does not measure recoverable dollars, explain why pricing should normalize, or determine a strike.

## What Pandar documented, and what we infer

The original transcript says he liked NVDA's liquidity and repeated option expansion/collapse; selected February 7 calls because that expiry looked most overpriced; sold strikes at 190 and above; expected substantial compression after the weekend; and sized to withstand the stock reaching 190. He explicitly kept those calls naked because he did not want bullish call spreads. His statement about not particularly using delta answered a question about puts.

Our interpretation: compare specific option prices and plausible repricing paths, then choose exposure that fits the opportunity and portfolio. The transcript does not supply a z-score threshold, fixed call delta, universal strike distance, or automatic call-spread conversion. It also does not reveal his exact valuation model. [Original transcript, lines 245–303](/Users/dgrissen/Dev/delta_bomb-nvda_call_strat/docs/sources/discord_transcript_clean.txt:245).

Charlie and Brent are simulated analytical lenses using the canonical global personas, not statements obtained from those people. Their independent outputs are saved in [Charlie's review](charlie_good_trade.json) and [Brent's review](brent_good_trade.json).

- Charlie emphasizes whether the demand that inflated the call wing is still accelerating, stalling, or reversing. Prior richness alone cannot establish exhaustion.
- Brent emphasizes the dollars at risk if the stock rallies, the wing expands further, or price gaps while the trade waits for normalization.
- Both favor comparing partial-normalization proceeds after costs with adverse-path losses, and retaining choices with distinct economic advantages rather than selecting the largest z-score.
- Brent's canonical opposition to naked short convexity is his risk preference. Pandar documented naked calls. We preserve that difference and compare structures explicitly rather than letting a persona restriction rewrite the source strategy.

## Audit of the MRVL calculation

The [original calculation](how_the_comparison_works.md) showed that the June 26 $425 call's bid IV exceeded its matched ATM IV by 14.95 points, versus a prior comparable delta/DTE mean of 1.92. That established broad call-wing richness for this coordinate. It did not establish a local kink or a trading edge.

### A small wing contraction can disappear into costs

The June 15 15:46 ET snapshot has stock $311.22, call bid/ask $2.74/$3.00, model vega $0.089347 per share per IV point, delta 0.09770 and gamma 0.002518. Assume a standard 100-share contract. Hold stock, ATM IV, clock and displayed quote width unchanged. Lower only the sold call's wing IV.

| Wing IV decline | Approximate short-call mark gain | Estimated net after crossing quotes, fees and slippage |
|---|---:|---:|
| 0 points | $0.00 | −$29.30 |
| 1 point | $8.93 | −$20.37 |
| 2 points | $17.87 | −$11.43 |
| 3 points | $26.80 | −$2.50 |
| 5 points | $44.67 | +$15.37 |

The quote crossing cost is $26; modeled fees are $0.65 per action, plus $0.01 per share adverse slippage on each action, consistent with the prior research convention. With that convention, the local break-even contraction is about **3.28 IV points**. Without fees and slippage, the displayed width alone needs 2.91 points.

Separately, a 1% stock rally with strike IV unchanged produces approximately **$31.63 of short-call mark loss**, using delta plus half gamma times the squared price move. This is not a maximum loss or a probability estimate. It shows how a small rally can outweigh a small skew improvement.

These are local Greek approximations, not full revaluations, forecasts or fills. Vega changes with IV, spot and time; five points is less locally accurate than one. The future quote width is unknown. Theta and other surface changes are deliberately excluded to identify the mechanism. Real trade comparison needs full repricing, including all those components. [OIC's vega definition](https://www.optionseducation.org/advancedconcepts/vega).

### The $425 call does not show an isolated upward kink

| Strike | Bid IV | Mid IV | Ask IV |
|---|---:|---:|---:|
| $420 | 124.19% | 125.81% | 127.43% |
| $425 | 125.19% | 126.65% | 128.11% |
| $430 | 125.04% | 127.77% | 130.49% |

Interpolation between the $420 and $430 midpoint IVs at log-strike $425 gives 126.79%. The $425 midpoint is about **0.15 points below** that line. A bid-to-bid interpolation suggests a positive bump of 0.57 points, but the target bid lies 3.78 points below the interpolated neighboring asks. The quote envelopes do not establish an isolated sellable bump. This comparison is a diagnostic, not a proof of fair value or executable arbitrage.

There was also a terminology problem: the earlier project field `call_kink` measured **10-day five-delta call IV minus 30-day five-delta call IV**. It was a term comparison, not local strike curvature. Preserve the source field for reproducibility, but label it that way in future reports. [Earlier metric definition](/Users/dgrissen/Dev/delta_bomb/docs/replay/pandar_leg_timing_2026-09-05/eligibility_explanation.template.md:96).

## The measurements that would identify the opportunity

Treat these as separate explanations of price, not five additional pass/fail gates.

| Measurement | What it answers | Practical calculation |
|---|---|---|
| ATM level | Is general volatility expensive? | Same-tenor ATM IV and its prior history; compare 30/60-calendar-day implied variance with realized variance as context. |
| Call-wing shape | Is upside insurance expensive relative to ATM? | Show call-minus-ATM across several supported deltas and forward distances, including the sold strike. Keep put-minus-ATM separate. |
| Local strike bump | Is this strike unusually expensive even relative to the surrounding call wing? | Leave the candidate or small candidate band out; use liquid quotes on both sides to estimate a smooth surrounding smile, and show the residual plus bid/ask uncertainty. |
| Expiry bump | Is this expiration unusually expensive relative to nearby expirations? | Compare matched-coordinate call-minus-ATM against adjacent supported tenors, with consistent variance interpolation and event treatment. Do not compare unlike deltas or merely the raw IV levels. |
| Journey | Is the dislocation building, persisting or beginning to unwind? | Depth above its prior baseline, time spent elevated, excess accumulated through the episode, distance from its observed peak, and smoothed recent change. |

Risk reversal is a balance between puts and calls: it can change because put prices change while the call being sold stays expensive. Do not let that stand in for call-wing compression. Cross-strike curvature, time-series acceleration and option gamma are also different quantities. ORATS distinguishes strike slope from its curvature, and notes that wing modeling requires additional work beyond those summary parameters. [ORATS surface methodology](https://orats.com/blog/modeling-the-implied-volatility-surface-skewness-and-kurtosis).

For a simple second-derivative idea, compare the recent smoothed change in wing richness with the preceding change: is expansion slowing? Keep the raw level and first change visible. A noisy one-day second difference should not independently decide the trade.

The RV comparison helps explain whether a general ATM collapse is plausible; it is not a prerequisite for a wing-only trade. A single stock jump aging out of a rolling RV window can create apparent improvement without calmer recent trading. Keep that explanation visible instead of treating falling RV as an automatic short signal.

## Turn those measurements into dollars

For every candidate, retain its exact contract and reprice the surface under separate coherent scenarios:

1. **Wing-only softening:** stock, ATM and time fixed; reduce call-wing excess partially. Compare a common small absolute change with the change supported by prior episodes.
2. **Local bump removal:** surrounding smile fixed; remove only part of the candidate's local residual. If there is no credible residual, this scenario supplies no special kink edge.
3. **Expiry normalization:** reduce the anomalous term component without assuming the entire ATM curve collapses.
4. **Carry without normalization:** advance the clock with a declared surface assumption; test whether time alone offers acceptable net economics.
5. **Continued chase:** stock rises and call-wing demand stays firm or strengthens. Include adverse spot/vol co-movement, a gap, and wider exit quotes.

First isolate the components for explanation. Then use joint stock/ATM/wing changes from comparable prior episodes for realistic total P&L. Do not add separately calculated nonlinear scenario gains as though they were independent. Fully reprice the same strikes under each scenario; do not silently switch to whichever contracts have the original deltas after a move. Surface shocks need positivity and option-price/calendar consistency checks. For moved-spot scenarios, report assumptions about how the smile moves with stock and test a reasonable alternative.

Show normalization dollars per contract, net of execution, beside stressed dollar loss, quote quality and time exposed. Scale alternative positions to a common declared loss budget where feasible, with a separate notional/concentration cap. A finite stress is not a true bound on naked-call risk. Remove an option only if another is no worse across the relevant comparisons and better on at least one, accounting for estimation uncertainty. Retain a small set with different advantages; do not bury the trade-offs in an invented weighted score.

Delta and % OTM remain visible: they describe sensitivity and distance. Also show distance in ATM-implied move units and plausible gap scenarios; these are scaling tools, not actual tail probabilities. Two tickers at 10% OTM can have very different risk. A wider delta search is useful only if the resulting trade has better net economics for the exposure taken.

## When is normalization actually expected?

The 111 prior levels used for MRVL's z-score are not 111 independent episodes showing what happened after an entry. The forward-distance comparison also has only 30 supported dates, below the specified 60. Neither gap is solved by describing the z-score more persuasively.

The simplest proposed predictive study is an episode table, not a complex model:

- At each evaluation date, use only earlier episodes whose relevant outcome window has already completed. Include episodes that stayed rich or became richer.
- Separate broadly expanding versus stalled/rolling-over states. Keep age and depth visible; do not subdivide into dozens of tiny buckets or assume an old episode must end.
- Record the one-, two- and four-session call-wing change, ATM change, stock path, maximum adverse excursion, and whether exit liquidity remained available. Require a prior-only rule for what counts as a distinct episode.
- Report the fraction that compressed, median contraction, dispersion, and a continuation/tail-loss case. Preserve the joint changes rather than combining unrelated favorable medians.
- If same-ticker samples are thin, label a broader HIRO-ticker comparison separately and partially pool rather than present a noisy ticker-specific mean as reliable. If even the broader evidence is thin, show sensitivity scenarios without assigning expected return.

Compare the contraction needed to cover costs with contraction and timing actually observed in those earlier episodes. A trade needing 8 points of wing softening is unappealing under a thesis supported only by typical 2-point changes. It might still have another thesis, but that thesis must be priced explicitly. Do not assume a full return to the historical mean.

## How the choice flexes with the situation

| Observed situation | Interpretation to test | Appropriate comparison |
|---|---|---|
| Rich wing, still widening; stock and call-wing IV advancing together | Demand may keep inflating the premium | Waiting versus smaller exposure versus protected structures; include expansion loss rather than forcing a fade. |
| Rich wing, slowing or beginning to soften; stock price no longer extending | Partial normalization is a hypothesis to test | Net proceeds from modest wing compression versus stock-rally stress; compare expiries and liquid strikes. |
| One credible local bump; surrounding calls fairly priced | A relative-price opportunity may exist | Sell the bump and evaluate a less expensive hedge, repricing both legs. |
| Entire wing rich; no isolated bump | Broad upside-option demand | Avoid calling this a kink trade; assess broad-wing normalization and how much a hedge gives back. |
| Richness already mostly removed | The original sale opportunity may be over | Cover versus keep the short; a long-leg purchase needs its own value/inventory rationale. |
| General IV remains supported by realized moves | An ATM crush may be a poor assumption | Keep ATM unchanged or higher while testing wing softening; avoid counting broad vol gains automatically. |

The current implementation uses daily option-surface and stock observations only, with a next-session EOD reference. HIRO timing and historical gamma maps are deferred. Their absence does not remove a stock-date from this experiment.

## Choose the second leg for its purpose

Buying a **higher-strike call** against the short call caps expiry upside risk. Buying a **lower-strike call** creates a bullish call vertical after conversion. A nearer call is not automatically the right purchase simply because the original sale can pay for it.

Reprice both legs jointly for broad-wing flattening, isolated-bump removal, ATM changes and stock moves. In the MRVL snapshot, the $420 long minus $425 short has approximately **+$1.27 per IV point** of parallel-wing vega per standard pair: equal IV declines in both calls hurt that component. The $425 short/$430 long has approximately **+$0.06 per point**, almost canceling parallel-wing exposure at that snapshot. Those figures say nothing by themselves about the total spread P&L or a shape change that affects the two strikes differently.

A useful relative-vol structure needs the short to lose more value from the targeted normalization than the hedge loses, after execution. A later bullish conversion instead needs a reason to own bullish exposure at the then-current price. Compare it with covering the short at that same moment. The original premium is cash received against an outstanding short liability, not necessarily earned profit. The original credit does not make a new purchase economically free.

## Three proposed research comparisons

Execution update: [the broad no-HIRO surface test](/Users/dgrissen/Dev/delta_bomb/hypothesis_tracking/e-pndr-012_no_hiro_surface_findings.md) has now run across 643 qualifying signal dates. Its particular slowing/rolling rule did **not** improve the specified outcome. [The separately frozen exact-chain test](/Users/dgrissen/Dev/delta_bomb/hypothesis_tracking/e-pndr-013_no_hiro_exact_findings.md) has also completed across 1,163 input cases and 203 signal dates. Its simplified partial-wing/1%-rally ratio produced 33 entries, all in prior names, and negative average priced-trade P&L. No robust relative advantage was established. The scenario-dependent rows above remain hypotheses, not established entry guidance. [The combined report](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_no_hiro_2026-09-08/pandar_no_hiro_research.md) explains the actual losses and the remaining larger-move valuation question.

1. Does net value from **plausible partial wing normalization**, relative to stressed upside exposure, select better call sales than raw richness or nearest-target-delta selection?
2. Does **slowing/rolling-over demand** improve timing compared with equally rich but still-expanding episodes, after accounting for lost premium and missed trades while waiting?
3. Do **verified local strike or expiry bumps** normalize differently from a broadly elevated wing, and can any hedge preserve the difference after costs?

Retain the existing ticker names and authorized 30-day earnings exclusion, with no HIRO features or availability requirements. Before reading new outcome quotes, freeze the candidate search envelope, definitions, scenario estimation, ranking/tie handling, execution and exits for a new research version. Lead the shortlist with three numbers: net gain from plausible normalization, contraction needed to cover costs, and stressed loss. Compare expiries over the same holding horizon. Adaptation means the same declared process chooses different strikes and structures as prices and conditions change; it does not mean changing rules after seeing winners. Keep every rejection and missing-data case. Preserve chronological evaluation and date/episode resampling. The five-entry-date June pilot cannot validate this method.

## Reproduction and evidence

- [Exact sensitivity inputs](mrvl_sensitivity_inputs.csv), [scenario arithmetic](mrvl_skew_scenarios.csv), [calculation metadata](mrvl_skew_sensitivity.json).
- [Reproduction script](skew_sensitivity_example.py): local Greek arithmetic, no provider calls or outcome reads. Run from the repository root using the project Python runtime.
- A full surface scenario engine, verified kink-history study, and conditional episode forecast are **proposed, not implemented or validated by this note**.

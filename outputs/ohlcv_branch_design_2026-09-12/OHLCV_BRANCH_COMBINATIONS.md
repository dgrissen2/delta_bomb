# Traditional price/volume combinations for SPX Delta Bomb Branch A and Branch B

**Brent + Quant research synthesis · 12 September 2026**  
Status: independent brainstorming, historical evidence audit and reconciled research nominations. Existing local data only. These are not newly backtested winners or changes to the running strategy.

## The recommendation

**The most promising family is a completed five-minute trend context, a countertrend pullback, and a completed one-minute break back in the trend direction.** Brent and Quant reached that family independently. After cross-examination, both selected the same starting recipe: **five-minute EMA9/20 + a 0.5-ATR14 counter-move + a one-minute three-bar break**, retaining the EMA20-side requirement. Use ordinary moving averages to describe the slower context, price structure to identify the local turn, and ATR to describe distance. Do not turn several correlated indicators into a confidence vote.

| Branch | Leading combination | What must happen after entry |
|---|---|---|
| **A — buy put first** | Bearish five-minute EMA context → a one-minute bounce → downside break that shows the bounce failing | Enough downside put repricing remains to sell the lower put at the required price before the failure controls intervene |
| **B — sell put first** | Bullish five-minute EMA context → a one-minute pullback → upside break that shows the pullback holding | The rebound cheapens the upper put enough to complete the spread before the unpaired short put fails |

**Second choice:** a five-minute break out of a previously defined Donchian channel, followed by a later one-minute retest and rejection/hold of that same frozen level. It offers a more explicit price reference, but may give up too many entries or too much of the move while waiting.

For **accuracy first**, the trend-compatible pullback family and the break/retest family deserve the first comparison. A stricter structural-preservation condition is a nominated challenger, not something we know improves accuracy. For **accuracy adjusted for N**, start with the simpler trend/pullback family and require extra filters to justify the episodes and days they remove. No available result establishes which precise recipe has the highest construction accuracy.

The most directly measured existing SPX trigger remains **five-bar stall AND running typical-price-mean reclaim after a pullback**. It has a small upward-touch advantage and no demonstrated tail protection. Keep it as a baseline, not as proof that B is solved. The separate **low-ER × middle-range rebound** clue is more relevant to B than A. The strongest encouraging legacy five-minute shape result is **staircase admission**, which belongs on the breadth watchlist rather than inside the initial stack.

## 1. Scope, sources and what was actually done

The canonical global [Brent persona](/Users/dgrissen/.config/skillshare/personas/strategy/brent-kochuba.md) and [Quant persona](/Users/dgrissen/.config/skillshare/personas/strategy/quant.md) independently reviewed the material before reading each other's new conclusions. A separate lineage review traced relevant markdown, code, stored tables and commits across `spy_chaser` and its hidden worktrees. Their independent reports remain preserved; subsequent corrections belong to the cross-reviews and this synthesis.

This work covered the June opening/rollover toolkit, one-minute alligator/ride/confirmation research, the five-minute BVT expansion/staircase/chop/shape/exit families, parity-SPX corrections and real-bar revalidation boundaries, and the Delta Bomb's earlier traditional-indicator stack and real-SPX stall/range/ER tests. It also checked adjacent ideas such as the daily residual-pop note and alligator-alternative lists; they are not silently treated as tested intraday strategies.

New computation was limited to **reproducing saved SPX tables, aggregating legacy SPY result ledgers and inventorying existing bar coverage**. We did not run a new indicator parameter sweep, download market data, fabricate missing history, or modify production code. The proposed combinations below have not yet received a fresh chronological price replay or option replay.

The supporting documents are:

- [Brent's independent assessment](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/brent_independent.md) and [Quant's independent assessment](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/quant_independent.md).
- [Historical evidence and commit lineage](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/lineage_evidence.md).
- [The detailed one-minute/five-minute contract and source audit](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/timeframe_contract.md).
- [Brent's cross-examination](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/brent_crossreview.md) and [Quant's cross-examination](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/quant_crossreview.md).

## 2. What survived the historical audit

The right conclusion is more specific than either “we already solved this” or “all the indicators failed.” Different studies predicted different things, used different prices and charged different execution costs.

| Research family | What the existing evidence supports | What it does not establish |
|---|---|---|
| Opening range, VWAP persistence and early timing | A completed opening range is a usable causal reference. The particular 0DTE short-call timing overlay lost about **$281/year** against its fixed 09:35 baseline. | That every intraday price signal is useless, or that a month-out put construction shares the same theta/entry-delay economics |
| Call-price-as-spot / parity SPX | The call-price proxy was rejected; the companion investigation reported only **52% agreement with its then-used parity benchmark**, plus substantial up-day misclassification against that benchmark. A later commit explicitly flagged parity-derived SPX minute work for revalidation. | That parity produces genuine index OHLC, or that the parity flag invalidates the separate real-SPY candle studies |
| One-minute alligator/EMA/VWAP riding | Mature clean entries can be late; rearm/cooldown variants showed major era reversal. A spectacular managed return was corrected for lookahead. | That a failed continuation entry is a successful fade entry, or that visual cleanliness predicts remaining option repricing |
| Five-minute staircase admission | A preserved comparison reports **+242 underlying bp** versus thrust-only, with **+17/+185/+39 bp** across three eras and a reasonably broad slope neighborhood. | A validated SPX put-construction edge. The SG-conditioned SPY universe, mined family and current-close execution assumptions remain material. |
| Classic Williams Alligator / Awesome Oscillator / fractals | A separate displaced-SMMA, oscillator and confirmed-fractal SPY prototype was inspected on four example days (`2640d7f`). | An isolated AO effect, broad accuracy validation, or equivalence to the custom undisplaced EMA alligator |
| Five-minute ER and color-flip chop screens | Simple blanket chop avoidance did not consistently separate good expansions from false ones. | A reliable universal “avoid low ER” gate, or any tested VWAP-crossing rule from the candle-color-flip table |
| RSI/large-bar override and candle-shape exceptions | The 36-configuration override had **0/36** positive in all eras and **0/3** positive nested folds. A selected shape bypass weakened in 2026. | That another RSI setting should be added to rescue the stack, or that a shape name proves its actual coded definition |
| Smackdown/range-ceiling exception | The attractive older headline was superseded after the pattern definition was corrected; the useful-looking carve collapsed. | A reason to resurrect the favorable older commit while ignoring the correction |
| Geometry and protective exit overlays | Results were concentrated in few days; some choices became discretionary despite statistical reports leaving them unresolved. | An entry signal. An exit from a SPY long is a different decision from initiating A or B. |
| Direct SPX stall/reclaim | Reproduced small upward-touch lift on real index OHLC. | Faster completion, improved adverse tail, or construction accuracy at executable option quotes |
| Direct SPX range/ER interaction | Middle-range low ER had a larger upward-touch fraction than high ER; the downward contrast was tiny. | Symmetric A/B mean reversion, an economic “oscillation edge,” or calibrated live ER/range cutoffs |

Important history anchors include `eb67ddc` for the parity-data warning, `92bd00f` and `6720530` for real-bars follow-up, `9655818` for the staircase report, `7b2b261` / `893b1b2` for the corrected smackdown closure, and `cb50b6e` for discretionary geometry adoption. The [lineage appendix](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/lineage_evidence.md) gives the source-specific qualifications. Revalidation of L1/L2 does not automatically rehabilitate every alligator claim built on the earlier series.

The Delta Bomb's own [13-finding stack review](/Users/dgrissen/Dev/delta_bomb/docs/specs/spx_signal_stack_codex_strategy_review_2026-08-18.md) had already identified incompatible transfers, repeated information presented as independent confirmation, undefined pivots and unsupported fade logic. Its later [SPX evidence review](/Users/dgrissen/Dev/delta_bomb/docs/specs/spx_2c2d_codex_strategy_review_2026-08-18.md) and [chart-state review](/Users/dgrissen/Dev/delta_bomb/docs/specs/spx_chart_analyst_codex_review_2026-08-18.md) also rejected the leap from high spot-touch rates to reliable option economics. The new document retains those corrections while reopening specific hypotheses they did not actually test.

### The direct SPX numbers, without changing their meaning

Quant reproduced the saved stall tables: **7,337 starts, 824 active days, 845 available study sessions**. An upward four-basis-point touch within an hour occurred on **81.72%** of trigger starts versus **80.55%** of uniform minute starts and **80.27%** of clock-reweighted baseline starts. Those are lifts of **1.17** and **1.45 percentage points**. The equal-day average difference is **2.57 points**, a different weighting scheme. Adverse excursion above 20 bp was **15.16% versus 15.22%**. None of these are completed-bomb percentages. [Reproduced summary](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/quant_existing_stall_summary.json).

Within the previously selected middle prior-hour range band, **23.98–39.01 bp**, low versus high ER produced:

| Outcome | Low ER | High ER | Interpretation |
|---|---:|---:|---|
| Upward 4-bp touch | 82.47% | 76.88% | An exploratory rebound lead |
| Downward 4-bp touch | 77.73% | 77.25% | Little corresponding downside evidence for A |
| Round trip | 58.98% | 51.28% | More oscillation under this particular definition |
| Adverse >20 bp on the upward path | 16.02% | 15.62% | No demonstrated tail improvement |

The upward difference is **5.59 points**, with a descriptive day-resampled interval of approximately **2.23–8.97 points**. That interval does not correct historical cell selection, time-of-day and arm-state confounding, or repeated overlapping starts. The band boundaries were estimated from the same historical table; they are labels for the evidence, **not recommended live thresholds**. [Cells](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/quant_existing_ER_range.csv) and [contrast calculations](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/quant_existing_ER_range_contrasts.csv).

The old 4-bp target also changes in SPX points with the index level. A larger prior range mechanically makes a small fixed barrier easier to reach while raising adverse excursions. It does not hold the option's required repricing fixed.

## 3. How the one-minute and five-minute charts should interact

The five-minute chart should answer **“Which direction or previously defined boundary is this local move compatible with?”** The one-minute chart should answer **“Has the counter-move actually resolved at a usable entry location?”** Both consume the same underlying prices. The proposed benefit is a slower context with faster entry timing, not independent corroboration.

```mermaid
flowchart LR
    C[Last completed 5-minute context] --> S[New pullback or frozen-level setup]
    S --> T[Completed 1-minute resolution]
    T --> Q[First eligible later option quote]
    Q --> O[Completion or failure under declared management]
```

For start-labelled intervals, the five-minute candle beginning **10:00** is not known until **10:05**. A trigger completed at **10:03** can use context ending at **10:00**, not the eventual 10:00–10:05 high/low/close. Once a fresh five-minute bar completes, update the state; cancel an incompatible pending setup. A fresh price failure must not be ignored merely because the slower state has not flipped.

Do not demand an additional completed five-minute confirmation after every one-minute turn. That can donate several minutes of the move. Conversely, do not treat the developing five-minute candle as completed. Record the cost of each delay, including the changed first-leg price and second-leg hurdle.

The source audit found four issues that matter particularly here:

1. **Some “five-minute” charts only display one-minute strategy entries rounded onto five-minute candles.** They do not establish an executable combination of both timeframes.
2. **Some actual five-minute tests enter at the close that generated the signal.** The current expansion simulator also seeds peak from the entry candle's pre-entry high and contains high/low ordering ambiguity when arming trails.
3. **Indicator names hide different calculations.** One-minute EMA5/9/20, five-minute EMA5/9/20, cold-start EMAs and displaced SMMAs are different. One-minute ER60 and five-minute ER12 cover similar time but have different travelled-distance denominators.
4. **The original ER bridge was mislabeled.** The source used ten five-minute bars and candle-color flips; some later prose treated it as one-minute ER and VWAP flips. Those are separate hypotheses.

The [timeframe contract](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/timeframe_contract.md) specifies completed groups, missing minutes, initialization, raw timestamp uncertainty, causal pivots, distinct episodes and post-signal fills. These details can change which recipe appears to win. They are part of the hypothesis rather than implementation housekeeping.

## 4. The concrete shortlist

These are research seeds, with familiar settings chosen to make the ideas reviewable. Their exact numbers have not earned privileged status. The independent reports preserve two original implementations; cross-examination selected Quant's ATR-based version rather than joining their conditions. Section 8 records the final seed and the remaining ranking disagreement.

### Family T: trend-compatible pullback resolution

**Shared concept:** a modest five-minute trend, a genuine countertrend excursion, and a one-minute break back in the trend direction. Do not require a fully fanned alligator first.

| Component | A | B |
|---|---|---|
| Slow state | Completed five-minute EMA9 below EMA20; EMA20 declining over a declared short lookback | EMA9 above EMA20; EMA20 rising |
| Setup | A rebound from a causally observed low, after bearish context exists | A pullback from a causally observed high, after bullish context exists |
| Fast resolution | Completed one-minute close breaks the prior short micro-range low | Completed one-minute close breaks the prior short micro-range high |
| Local thesis failure | Price breaks the setup's rebound high, or the completed slow state becomes incompatible | Price breaks the setup's pullback low, or the slow state becomes incompatible |

Brent's original seed uses a touch of the **five-minute EMA9** followed by a **two-bar** one-minute break. Quant's adopted seed uses a retracement of **0.5 × five-minute ATR14**, remains on the trend-compatible side of EMA20, and triggers on a **three-bar** one-minute break. These are alternatives. Combining EMA9 touch, ATR floor, EMA20 position, multiple slope checks and both breaks would rebuild the very stack the review rejects. Brent accepted the ATR version because requiring a visit to a relatively slow EMA9 may exclude orderly shallow pullbacks or force a deeper, later entry.

For either version, freeze the setup reference at the declared arm, use only completed bars, and permit one attempt per fresh countertrend episode. Persistent context alone cannot rearm an old setup. A price failure before entry cancels the pending setup. During an entry-only comparison, a new price-failure event after entry is logged; do not quietly add an optimized exit and credit the entire gain to entry timing.

**Why it is the leading hypothesis:** it seeks a short favorable move from a better location rather than predicting the whole day or entering after a mature move. For A, a failing bounce within bearish context is more specific than buying puts because the tape has risen. For B, a holding pullback within bullish context is more specific than selling puts because the tape is oversold. These are price-side analogues, not equal economic risks.

**What would disprove its useful combination:** the one-minute trigger alone performs as well; the five-minute state mostly delays correct turns; matched immediate-at-arm entries do just as well; a later fill consumes the apparent gain; or the apparent precision comes from one unusual day. A high directional hit rate after a large trigger candle is particularly suspect unless enough movement remains after the actual quote.

**Precision challenger:** Brent proposes requiring the pullback to preserve a prior completed five-minute structural extreme. It might remove genuine reversals, but it could remove the best-priced entries and reduce N. Record it as one nested restriction, not an assumed upgrade. The simpler parent must remain visible.

### Family D: five-minute channel escape, then one-minute retest

Freeze the high/low of the **six five-minute bars preceding the breakout bar**. The breakout bar cannot belong to its own reference channel.

- **A:** a completed five-minute close breaks the frozen low; a subsequent one-minute bounce retests that broken level and closes back below it; downside price resolution confirms rejection.
- **B:** a completed five-minute close breaks the frozen high; a subsequent one-minute pullback retests it and closes back above it; upside resolution confirms the hold.

Brent's independent recipe waits for the following one-minute close to break the retest bar's extreme. Quant permits the completed retest bar itself to close beyond the previous one-minute extreme. The second is earlier; the first is stricter and later. Neither may claim fills inside the already completed retest candle. For the first comparison, this synthesis nominates Quant's earlier completed-retest version; Brent's extra-bar confirmation remains a declared latency sensitivity, not a trade-by-trade substitution.

The retest must occur after the breakout has become known. Keep the boundary fixed through the episode. Cancel if a newly completed five-minute close invalidates the breakout; do not move the boundary to preserve the story. If a break runs without a retest, this family misses it. That is an explicit N cost.

**Why it is second:** the boundary gives a clear test of acceptance or rejection, with fewer smoothing choices than a full trend stack. The main concern is latency and sparsity: two stages of confirmation can spend the small repricing the bomb needs. Compare breakout-only with breakout-plus-retest on the same armed episodes.

### Secondary families: keep them visible, do not mix them into the leaders

| Family | Concrete idea | Place in this document |
|---|---|---|
| Exact legacy stall/TPM | Existing eight-point pullback, five completed bars without a new running low, then close above running mean typical price since that low | Known B-like baseline. Its mirror for A is untested. TPM is unweighted and must not be renamed VWAP. |
| Range-edge failure | Freeze a prior five-minute channel, then assess later bars; A probes/re-enters the upper edge and turns down, B undercuts/reclaims the lower edge and turns up | Lower-priority new hypothesis. Avoid the tautology of building a range from the same closes you then “test” for remaining inside it. |
| Low ER × moderate range rebound | Keep the actual one-minute ER60 definition and investigate the previously observed upward asymmetry on independently armed pullbacks | B-oriented exploratory lead. No universal chop gate, no automatic mirror to A, no adoption of the historical tercile edges as optimized thresholds. |
| Staircase | Gradual progress inside a compatible five-minute state, admitted before a large thrust | Best legacy breadth idea. A new one-minute staircase is a transfer from the five-minute study, and must be tracked separately from pullback entries. |
| Bollinger/RSI re-entry | Flat-mean range hypothesis, band excursion, then an actual re-entry; compare price re-entry alone before requiring RSI | Quant's lower-priority alternative to structural range edges. It introduces more settings and does not earn a place in the initial comparison. |

Family T and Family D are the first two nominations. The secondary list is not an invitation to test every entry, indicator and threshold combination until one becomes perfect.

## 5. Which traditional indicators earn a role

| Indicator | Recommended role | Decision |
|---|---|---|
| EMA9/20 on completed five-minute closes | One slow directional state | **Core candidate** |
| Short one-minute high/low channel | Observe local resolution after a setup | **Core candidate** |
| Five-minute Donchian channel | Frozen boundary for break/retest | **Alternative core family** |
| ATR14 / prior-hour realized range | Distance ruler, chase/volatility diagnostics | **Keep**, but do not call high ATR directional confirmation |
| Running typical-price mean | Exact legacy stall/reclaim definition | **Keep as baseline** |
| Opening range | A completed early-session boundary | **Optional alternative reference**, not a forecast of all-day direction |
| SPY session VWAP | Price relative to that proxy instrument's own traded-volume benchmark | **One optional ablation**, subject to existing coverage |
| SPY relative volume | Unusual activity for the same session minute | **Separate optional ablation**; activity is not signed flow |
| RSI / stochastic / MACD / ROC | Alternative representations of momentum | **Do not stack onto the EMA state**; no tested MACD success was located in this intraday lineage |
| ADX/DMI | Describe strength/persistence | **Diagnostic first**; high ADX and a mature fan can describe a late move |
| ER / CHOP / flip counts | Describe path efficiency or congestion | **Conditional research**, not a blanket pass/fail gate |
| Bollinger/Keltner bands | Alternative range location | **Secondary family**, not extra votes on a Donchian/EMA stack |
| Wick/body scores | Explain a specific rejection | **Avoid optimized exceptions**; old shape definitions and overrides were unstable |
| OBV / volume profile / Supertrend | Different activity/location/management representations | **Low priority or separate management test**; suggestions in a brief are not successful tests |

Five-minute BVT “VWAP” also used cumulative five-minute close × volume, rather than exact transaction VWAP. A new SPY VWAP calculation must have a named price basis, regular-session reset and feed. Compare SPY with its own VWAP; never subtract a SPY price-level benchmark directly from SPX.

## 6. What the existing data can answer

The [local inventory](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/bar_coverage_summary.json) found **897 real-SPX OHLC dates through 11 September 2026** and **2,040 SPY OHLCV dates through 11 June 2026**. There are **841 shared dates** before checking interval-level alignment. SPX has no genuine traded volume. The cached SPY series includes extended hours and must be restricted consistently for regular-session features.

This is substantially more price history than the 22-session HIRO book. Use it. It can falsify direction, delay, regime and price-path claims without demanding more HIRO. It cannot supply the missing historical option quotes needed to turn a spot move into an observed construction result.

There are **zero SPY-volume dates overlapping the August–September option/HIRO book** in that cache. The price core can be studied on those recent dates; a volume-enhanced challenger can be compared on the older supported intersection. Carrying June volume forward, inventing index volume or treating absent VWAP as a passing signal would change the question.

The bar checks found no duplicate regular-session minute labels or invalid OHLC rows under the stated checks. They also found partial five-minute groups. The inventory does not certify a complete exchange calendar or raw timestamp interval semantics. Exclusions must be recorded rather than making the available folder synonymous with an unbiased market sample.

### Price-only policy versus HIRO overlay

The nominated indicators require **OHLC**, with an explicitly optional SPY-volume extension. They do not require HIRO, SG volatility trigger, gamma levels, implied move or option-derived IV to generate a signal.

Two applications must be distinguished:

1. **Standalone OHLC policy:** replace signal admission and any source-dependent state/veto behavior with the declared OHLC contract. Retain explicitly chosen execution mechanics such as strike geometry, quote eligibility, cap, deadline and portfolio limits. Its management must be named; it cannot quietly keep a HIRO flow exit and still be called independent of HIRO.
2. **OHLC overlay on the existing HIRO policy:** restrict or time existing HIRO episodes with the price rules. This answers whether price adds value conditional on HIRO. It does not answer whether OHLC can stand alone.

The current B safeguards include HIRO-flow and SG-level inputs, and some exits are source-dependent. Copying the old eligibility helper wholesale would contaminate a supposedly price-only test. Conversely, removing those rules creates a distinct B policy, whose risk and denominator cannot inherit the old results. A proposed protective option hedge would also be a new position, not a free accuracy improvement.

## 7. A finite comparison that respects accuracy, N and overfitting

We can make a reasoned decision using the archive without pretending there is a large untouched holdout. The proposed next comparison should be small enough that its failures can be understood.

**Freeze one representative version of Family T and one of Family D.** Keep A and B separate. Preserve the exact legacy B trigger and simple controls. Put staircase, range and volume alternatives in a dormant registry. Avoid combining whichever subrule happens to win on each day.

For price diagnostics, use all existing usable real-SPX history, an explicit post-signal delay and complete elapsed-time windows. Prespecify one main fixed-point target, with 3/5/7-point and normalized views as sensitivity rather than winner selection. Report time to touch, adverse-before-favorable ordering and ambiguity. A touch after a failure boundary is not a successful entry simply because the chart eventually rebounds.

For actual construction, use only existing eligible option quotes and a separately declared standalone or hybrid management policy. Keep the nominated geometry around **30 DTE, −0.20 delta, five-point width and $0.10 construction credit** fixed while comparing entries. Retain the declared cap, clock, fees, quote delay and capacity. Larger credit, different strike selection or a new exit are separate hypotheses.

The critical controls are:

- **Immediate at the same arm versus waiting for resolution.** This separates locating a setup from timing it. Record the changed first-leg price, elapsed delay and completion hurdle.
- **One-minute trigger alone versus the five-minute-plus-one-minute combination.** The slower chart must earn its role; visual plausibility is not enough.
- **Breakout alone versus breakout plus retest.** Count missed opportunities and remaining movement after confirmation.
- **Whole chronological policy versus isolated admitted trades.** One occupied slot can displace a later good entry. The old clean-leg overlay had attractive additions that displaced better baseline trades; added-trade averages concealed the loss.
- **Standalone A, standalone B and the capacity-limited combined policy.** Do not mask a weak short-put branch with a stronger A result.

For **priority 1**, construction accuracy is completed pairs divided by **all first-leg attempts**, before the declared failure or deadline. Show failures, cash losses, quote coverage and uncertainty beside it. Count an eventual rebound after the short-put cap as a failure. Directional hit rate and completed inventory value are separate quantities.

For **priority 2**, show accuracy against attempts, distinct episodes, active days, days on which the candidate actually differs from its parent, and worst-day concentration. `accuracy × N` merely counts wins and does not express the user's preference. A 100% rule on two selected days need not outrank a slightly less perfect rule with wider support. Conversely, broadening B just to create trades does not satisfy accuracy first.

Use day or contiguous-day blocks for descriptive uncertainty. Show pooled-opportunity and equal-day summaries separately. Delete the most influential day and inspect era/year stability. A chronological later-period comparison can be useful on the larger price history, but already inspected 2025–2026 remains reused evidence. Deletion and walk-forward analysis do not retroactively make it untouched.

Do not bootstrap six successes into a claim of certainty. Do not count overlapping minute starts as independent bets. Do not turn every nearby EMA/ATR/lookback setting into another selection opportunity. A small declared sensitivity—such as a one-minute extra execution delay or one nearby period—should test brittleness while keeping the original seed's result primary.

Demote a family if correct execution removes its lift, immediate-at-arm explains it, an extra filter merely selects one winning day, or improved completion comes with much worse failed-leg losses. If the long price history is encouraging but the option sample cannot distinguish candidates, the conclusion is **promising placement hypothesis; option accuracy unresolved**. That is a usable research ranking under the available evidence, not a request for more data.

## 8. Reconciliation and final research choice

The independently reached agreement was at the family level. Cross-examination then made the following concrete choices **without looking at new candidate returns**:

| Decision | Final nomination |
|---|---|
| Default A/B family | Quant's complete trend/pullback recipe; no added EMA9-touch requirement |
| Five-minute state | EMA9/20 and EMA20 change over three completed five-minute bars |
| Retracement scale | 0.5 × the latest available five-minute ATR14 at arm; anchor and ATR then frozen |
| One-minute trigger | Close beyond the prior three completed bars' low/high, excluding the trigger bar; below EMA20 for A, above it for B |
| Arm versus trigger | Trigger must occur on a later completed minute than arm |
| Episode lifetime | Thirty elapsed minutes after arm, or the declared last-entry cutoff, whichever is earlier |
| Cancellation | Process a failed completed five-minute state, new favorable anchor extreme or expiry before any coincident trigger |
| Rearm | One attempt per anchor; a genuinely new favorable extreme or off→on context transition is required. Timeout alone does not refresh an old setup. |
| Extra historical structural gate | Optional nested ablation; removed from the proposed default |
| Distinct challenger | Six-bar five-minute Donchian break, later one-minute retest/close beyond the prior minute's extreme |
| Lower-priority range idea | Frozen price-edge re-entry before adding Bollinger/RSI complexity |

Initialize the trend anchor from the **prior thirty completed one-minute bars**: low for A, high for B. Update it causally before arming. Arm on a completed close at least the declared ATR distance away in the countertrend direction, then freeze it. A new A low or B high before entry ends that armed pullback; it is not permission to enter the replacement episode on the same bar. This deliberately excludes a trigger that has already run through its original favorable anchor, and its lost opportunities must be visible in the comparison.

Use at least **100 preceding complete regular-session five-minute bars** as common prehistory for EMA/ATR calculation. For this new seed, use undisplaced close EMAs and a named Wilder ATR14 with SMA initialization followed by the recursive update; include the opening true range against the previous session's close. This is a declared new definition, not a claim of byte-for-byte equivalence to the legacy first-observation-seeded smoother. Require the same available prehistory for competing candidates and record the opening-gap effect. No same-day final daily ATR is allowed.

For the channel challenger, the retest must be later than the completed breakout. Apply the same thirty-minute finite setup lifetime, one attempt per frozen boundary, and last-entry cutoff as design conventions. A closes back below the broken low and below the previous one-minute low; B closes back above the broken high and above the previous one-minute high. Freeze all references before the decision. A newer completed five-minute close back inside the old boundary cancels a pending setup before a coincident trigger. These conventions finish the nominated comparison; they are not historically optimized settings.

The entry window should remain common across candidate families in the first option comparison: current baseline observation through 10:00, A no earlier than 10:35, no new leg after 14:30, sixty-minute construction clock, and 15:30 resolution. These are inherited comparison controls, **not OHLC-derived optimal times**. The [current configuration](/Users/dgrissen/Dev/delta_bomb/scripts/hiro_engine_v2/config.yaml:41) records their origin. A later clock experiment must not be folded into the indicator result. Any event-calendar exclusions must likewise be named and frozen separately from the price signal.

The remaining judgment difference is worth keeping:

- **Quant:** trend/pullback first under both accuracy and accuracy-adjusted support; channel/retest second because extra confirmation can spend the needed move.
- **Brent:** use the agreed trend/pullback seed as the default and N-adjusted choice, while giving channel/retest a distinct precision-challenger role because it tests acceptance at a fixed boundary.
- **Shared conclusion:** neither recipe has measured construction accuracy yet, and the stricter-looking one cannot be declared more accurate from its appearance or lower N.

Both also agree that the low-ER/middle-range observation remains a selected **B rebound clue**, not a reason to add ER to every entry or mirror it into A. Agreement between two personas is design scrutiny, not two independent market samples. The independent reports, [Brent's revisions](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/brent_crossreview.md) and [Quant's revisions](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/quant_crossreview.md) retain that distinction.

This document deliberately does not restore the old mature-alligator fade claim, the correlated two-of-three vote, a universal chop veto, or the idea that a high unconditional touch rate itself is the bomb's economic edge. It also does not treat the failed 0DTE timing program as proof that all traditional indicators are exhausted. The strongest remaining question is narrower: **can slow context and fast local resolution improve the entry price and remaining repricing enough to justify the opportunities and time they consume?**

The deliverable is this shortlist and its auditable reasoning. No recipe was deployed and no new performance estimate is implied. [Artifact and source provenance](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/DOCUMENT_MANIFEST.json) records the local inputs and completed package.

---

## 9. Revised test thesis after the adjacent trend-catching review

**Appendix added 12 September 2026. This section supersedes the research priority in “The recommendation” and §8; the earlier text is preserved as the original thesis.** It does not change production rules or report a newly validated combination.

Brent and Quant independently reconsidered [SpyChaser's trend-catching research review](/Users/dgrissen/Dev/spy_chaser/outputs/trend_catching_research_review_2026-09-12.md), checked relevant primary sources, and then cross-examined their revised conclusions. The source audit also reproduced the original one-minute impulse observations without changing their event definition. No new market data or indicator grid was used.

### 9.1 The substantive change

**Test the observed structure before preferring our invented combination, and let the branch evidence determine the research order.** Our earlier EMA9/20 + 0.5-ATR pullback + one-minute three-bar break is still a plausible placement hypothesis. Its precise recipe has no measured advantage. Agreement between two personas gave it a coherent mechanism, not enough evidence to put it ahead of the archive's strongest measured comparator.

| Question | Revised priority | Change from the original document |
|---|---|---|
| **B: what deserves the first empirical comparison?** | Five-minute staircase enabled versus identical thrust-only admission, followed by comparison with the frozen T pullback recipe under a common construction contract | Promote staircase from a dormant breadth idea to a primary empirical comparator. It is a research priority, not a B accuracy winner. |
| **A: what deserves the first inexpensive evidence check?** | The original downside range/volume-expansion events, with forward outcomes recalculated from existing real price bars on the same events | The newly audited volume lead is chiefly bearish. Verify that observation before inventing another A filter. |
| **A: what remains immediately testable on the recent price/option book?** | Frozen bearish T versus immediate entry at its same armed rebound | Retain T as a theory challenger. A volume-dependent policy cannot be scored on recent dates lacking SPY volume. |
| **What should one-minute bars do initially for staircase?** | Execute after the completed five-minute signal and monitor the declared path; any additional one-minute confirmation gets a separate immediate-versus-waiting comparison | Do not automatically attach T's pullback or micro-break to the staircase. Fast timing must justify its latency and lost opportunities. |
| **What leaves the first round?** | Channel/retest, extra structural gates, RSI/band combinations, daily/theme/surface gates and unions of the leading rules | Keep them documented but dormant. The revision substitutes priorities rather than expanding the search indefinitely. |

The evidence does **not** establish that five-minute bars are intrinsically better, that one-minute detection is useless, or that T is disproved. The historical five-minute and one-minute systems differ in features, source, instrument, exits and transaction costs. The revision changes which comparison is most informative; it does not pretend to isolate timeframe superiority from those studies.

### 9.2 What the adjacent review strengthens—and where it overreaches

The staircase result deserves its elevated role. The stored comparison reruns the whole entry/rearm book, reports **+242 underlying bp** versus thrust-only, and remains positive across the named eras and a broad slope neighborhood. That is stronger evidence than the exact T constants we nominated without testing. It is also preferable to judging only added trades, which the failed clean-leg overlay showed can conceal displacement of better entries.

But **185 of the 242 bp came from 2023**. The 2022 added cohort had only four trades; the 2024–2026 added cohort's win rate was approximately **54%**, versus the reported **65%** for all 49 added trades. These are managed underlying-profit rates, not construction accuracy. Positive era signs and leave-one-era-out results are useful stability evidence inside a mined family; some folds use later eras to select a setting for an earlier era. They are not three independent deployment replications. [Staircase source report](/Users/dgrissen/Dev/spy_chaser/.claude/worktrees/below_vol_trigger/outputs/staircase_cv_conclusions.md).

More precisely, those 49 “added” trades are **entry timestamps present only in the staircase-enabled full rerun**. Because earlier entries and exits change rearming, they need not all be direct staircase-trigger admissions. The 65% is neither the enabled full-book win rate nor an isolated causal staircase win rate. Also, the current CV script inherits geometry from the imported module unless explicitly overridden; invoking its filename alone does not reconstruct the old pre-geometry book.

The **+604-bp pre-geometry book** and the approximately **+678-bp current book** also remain distinct. Discretionary geometry-B is excluded from the nominated replication. Current-close entry, a pre-entry candle high in the initial peak, same-bar high/low trail ordering and exact-EMA fills must be accounted for consistently in both arms. A source hash alone does not make those mechanics executable. [Simulator](/Users/dgrissen/Dev/spy_chaser/.claude/worktrees/below_vol_trigger/eda/bvt_5m_expand_probe.py:192).

The adjacent review's proposed forward bridge makes another change that must be named: it replaces an **intrabar low crossing the prior EMA5** with a **completed five-minute close below it**. That changes when the exit triggers, not merely its fill price. Its 0DTE call vertical, 09:35 control and net-P&L objective answer the trend-catching question. They do not replace our roughly thirty-DTE put construction or accuracy-first objective. Poor results from its tested trend stops also do not authorize removing the current bomb's monetary cap.

Its daily/theme-first architecture is a proposal, not an established prerequisite for intraday SPX accuracy. The theme-label scores, eight-pair stock-ranking results, current-membership histories and daily surface studies do not justify adding breadth, RS, SG, IV or leader gates to our OHLC signal. The failed intraday surface grids discourage a rescue overlay, but do not invalidate every use of quotes to measure the actual construction hurdle.

Finally, the adjacent document's fifty new qualified days, twelve months and second untouched period belong to **its proposed deployment policy**. We do not adopt them as prerequisites for this task. The revised work is finite and uses existing data. It may reject a candidate, establish a useful partial ranking, or leave construction accuracy unresolved without asking for unavailable HIRO history.

### 9.3 The one-minute impulse: reproduced, but materially different by direction

The original result reproduces: **283 events on 103 active days out of 107 eligible days**, 26 May 2022–2 April 2026. However, the source is mixed. The signal uses real SPY bars; its forward returns use **anchored parity-SPX `U`**, not actual SPX OHLC. Anchoring removes a daily level offset, not time-varying reconstruction error. The new adjacent review must not be read as an independent real-SPX confirmation of this lead.

The exact original definition also differs from its prose:

- Range is **high minus low**, at least twice the previous twenty rows' mean high-low range. It is not true range incorporating previous close.
- Volume is at least the previous twenty rows' mean volume. It is not twice normal volume or same-minute historical RVOL.
- The opening range includes **09:30 through 09:45 labels inclusive**—sixteen observed bars here. The twenty-row history makes the first observed event label 09:50.
- A close need only be outside that range; a fresh crossing is not required. Only **58 of 283** events were fresh prior-close crossings.
- The implementation takes up to three events per day. **Eighty-six days reach that cap**, and the 45-minute returns include **112 overlapping event pairs on 74 days**.

These are findings from [the actual event function](/Users/dgrissen/Dev/spy_chaser/.claude/worktrees/below_vol_trigger/eda/bvt_r2_event_study.py:42), its [parity helper](/Users/dgrissen/Dev/spy_chaser/.claude/worktrees/below_vol_trigger/eda/bvt_common.py:25), and the new [frozen-recipe reproduction](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_1/adjacent_reproduce_impulse.py).

The directional split is more relevant than the pooled headline:

| Original event direction | Events / active days | Mean signed bp, 15 / 30 / 45 minutes | Positive endpoint fraction, 15 / 30 / 45 minutes | Implication |
|---|---:|---|---|---|
| Down | 119 / 51 | **+4.28 / +6.57 / +8.58** | **59.7% / 63.0% / 64.7%** | A-directed downside continuation lead to verify on real prices |
| Up | 164 / 68 | **+0.66 / +0.19 / +0.45** | **53.0% / 53.0% / 55.5%** | Does not support promoting a B upside-volume gate |
| Pooled signed directions | 283 / 103 | +2.18 / +2.87 / +3.87 | 55.8% / 57.2% / 59.4% | Conceals the branch asymmetry |

Direction-specific active-day counts overlap; they are not additive. Up-event means become **−1.00 / −1.80 / −2.33 bp** when days receive equal weight. Those means answer a different weighting question, not a contradiction. They show why the pooled result should not be applied to both branches. [Reproduced summary](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_1/adjacent_impulse_summary.csv) and [event ledger](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_1/adjacent_impulse_events.csv).

Neither the means nor the positive-endpoint fractions are target-before-stop probabilities or bomb-completion accuracy. A path can be positive at minute 45 after failing a cap at minute five. The ordinary unclustered p-values remain descriptive, and choosing the downside slice after seeing the split adds selection. The correct promotion is **to a source-repair test**, not to a proven bearish rule.

A “fresh opening-range cross,” real true range, time-of-day RVOL or first-event-only admission would each alter the signal population. They may be reasonable later variants, but must not silently replace the original event and inherit its favorable numbers. Deleting early events to impose A's 10:35 clock also does not reconstruct a policy that searched for its first three events only after 10:35.

The frozen-ledger clock check leaves **80 downside events on 42 days** at 10:35–14:30; their original parity-based 30-minute signed mean is **+5.84 bp**, with **65.0% positive endpoints**. The corresponding B clock, from 10:00, leaves **162 upside events on 68 days**, with **+0.03 bp** and **52.5% positive endpoints**. Four days had already exhausted the original three-event cap before A's start. These are filtered historical observations, not rerun branch policies. All 103 original event dates have existing real-SPX files, and 102 have all 390 regular-session minute labels, so the proposed outcome-source check can proceed with available data. [Clock-slice results](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_1/adjacent_impulse_branch_clock_summary.csv) and [coverage/clock metadata](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_1/adjacent_impulse_branch_clock_metadata.json).

### 9.4 Revised mechanism: remaining repricing matters more than visible strength

The common hypothesis becomes: **identify a causal opportunity, then determine whether enough favorable option repricing remains after the first executable leg to complete the structure at acceptable failure cost.** A convincing trend can help direction while hurting entry price.

A relevant archived [confirm-bar financing study](/Users/dgrissen/Dev/spy_chaser/.claude/worktrees/below_vol_trigger/outputs/confirm_bar_features_finding.md) reported roughly 49% financing success for a different call-leg hedge. ADX and SPY VWAP distance had reported fill AUCs of 0.407 and 0.318; some apparently stronger trend readings accompanied worse financing. Its selected gates, parity-based features and different option contract prevent transferring either those percentages or an inverse VWAP rule. It nevertheless challenges the assumption that textbook long confirmation must improve a financing trade. Its own explanation that the move is necessarily “spent” is a hypothesis, not a demonstrated cause.

For B, a staircase may confirm upside only after the first short put has cheapened. For A, a downside impulse may confirm the move only after the first purchased put has become expensive. Record the actual first-leg debit/credit, required second-leg limit, waiting time, favorable movement remaining and failure path. These are outcome diagnostics. Do not create another retrospectively optimized “headroom” gate from them.

### 9.5 What to test, in a bounded sequence

**The following experiments are proposed, not completed by this appendix.** The completed new computation is the original impulse reproduction, its direction/dependence summaries and source/coverage checks.

#### Test 1B — establish the staircase's empirical reference

Use the pinned five-minute source at commit `6c15500a4776a4b1f48c62d8cc7c7dcecf7fd52a`, keeping **staircase enabled versus thrust-only** as the single admission difference. Keep geometry, override and clean-leg additions off, and preserve the exact source definitions, historical population and clock for replication. Include the defining thrust, fan, steepness and extension settings from the source rather than replacing them with T's simpler EMA pair. Do not call a minimal three-green-bar rule a reproduction of the full staircase package.

First reconcile the original saved result. Then apply the same completed-bar availability, later-entry and post-entry-peak corrections to both arms, with explicit treatment of ambiguous intrabar ordering. Record how much the incremental result changes because of timing/fills versus a deliberately changed exit trigger. Use the existing one-minute bars to resolve what they can; do not invent a tick path where they cannot. Report full-book outcomes, changed days and displacement as well as admitted-event price paths.

**Decision:** keep the staircase as a serious B comparator if its incremental usefulness survives those corrections on more than an isolated influential day. If it disappears, demote it without searching another body/slope/exit grid. This establishes the quality of the upstream lead; it does not yet establish put-construction accuracy.

#### Test 1A — repair the original downside impulse's outcome source

Keep the original event timestamps, directions and parameters. Replace only the forward parity endpoint with existing real-SPX observations on matching available times; also report the same SPY-instrument path as a source diagnostic. Keep the original parity result beside the corrected result on identical support. Missing values are missing, not zero returns or nearest favorable timestamps.

Report up/down directions and era/day weighting separately. Preserve all three original horizons as descriptive replication outputs, with **30 minutes nominated as the single primary endpoint for this source check**, not selected later for significance. Add favorable-before-adverse path diagnostics using the already declared bomb-screen horizon and barriers, with ambiguous bars visible. This is not an option fill model.

Only after the source result is understood, compare the range/location condition with and without its volume requirement as one declared ablation. Recalculate the actual chronological admission/cap policy rather than appending all favorable no-volume observations. First-event/de-overlap reporting can show dependence sensitivity; changing the rule to require a fresh cross remains a separate, dormant idea.

**Decision:** reject or demote the lead if the downside advantage vanishes on real paths, matched days, the required branch clock or an extra execution delay. If it persists, compare immediate downside-impulse entry with the existing rebound-waiting hypothesis on declared populations. Do not add a new A oscillator. The present weak upside result supplies no reason to add volume to B.

#### Test 2 — translate the evidence to the actual available price and option contract

The original staircase needs SPY VWAP and was studied on an SG-conditioned universe. The original impulse needs SPY volume. Our cache ends on 11 June, so neither volume-dependent original policy can be scored on the August–September put book. Do not solve that by inventing volume or silently treating missing confirmation as satisfied.

For staircase, inspect the translation in identifiable steps on older supported data: **remove only VWAP on SPY; move that price-only rule to real SPX on matching dates; then distinguish the original conditioned population from the wider available SPX population.** Record differences rather than attributing a simultaneous instrument, volume and regime change to staircase alone. This is a short attribution ladder, not a parameter search. An unweighted typical-price mean is not a substitute VWAP.

The resulting **SPX price-only staircase-on and staircase-off transfers** are new hypotheses with zero inherited success count. Compare them with the already frozen bullish T recipe on common eligible dates under the actual put construction. Keep bearish T versus its same-arm immediate-entry control for A; a mirrored staircase stays inactive. The A volume policy remains limited to existing supported dates unless an explicitly different price-only transfer is later nominated. It is not required to finish the recent-book comparison.

Retain the previously declared put geometry, $0.10 credit, first eligible later quote, cap, timeout, entry window and capacity as comparison controls. Keep signal admission/management independent of HIRO for a standalone OHLC policy, and separately label any HIRO overlay. Do not import the adjacent study's 0DTE call expression, implied-move strikes or trend-riding exit.

**Decision:** the relevant B comparison is staircase-on versus staircase-off versus T for completed pairs over all first-leg attempts, with failure cash and changed-day support. The small quote sample may show grossly bad policies without identifying a unique best one. A price-only directional success on an older day never becomes a synthetic option completion.

#### Test 3 — make one-minute waiting earn a place

For the staircase reference, begin with the first eligible quote after the completed five-minute signal. If timing is then tested, use the **same five-minute setup IDs** to compare immediate entry with one declared one-minute resolution rule. Keep the earlier three-bar break as the available nominated alternative; do not attach T's ATR pullback and every context gate as well. Keep the finite cancellation and capacity accounting explicit.

Report entries delayed, entries missed, waiting time, premium/hurdle changes and whole-policy results, not just the percentage of surviving triggers that win. If the added waiting does not improve actual construction sufficiently to justify lost support or risk, keep the simpler five-minute signal plus one-minute execution. This is an empirical role assignment for one-minute data, not a universal prohibition on using it for detection.

### 9.6 How the revised thesis respects both accuracy priorities

**Accuracy first:** construction completion before the declared failure/deadline divided by all first-leg attempts. Failed first legs remain failures even when the path later moves favorably. Show cash loss and adverse tails alongside that fraction; a small rise in completion with much worse failed-leg losses is not an unqualified improvement.

**Accuracy adjusted for N second:** report distinct setups, active days, changed days versus the parent, concentration, missing-quote opportunities and coverage of the full eligible calendar. A no-entry day is retained in whole-policy accounting, but is neither a win nor a failed first-leg attempt. Pooled event accuracy and equal-day summaries remain distinct. More overlapping starts do not supply independent support.

Use reused-history stability and largest-day/era deletion as stress tests, with day-based uncertainty where meaningful. Do not rename inspected years as untouched validation. There is no new tiny holdout requirement, no post-hoc choice of the best horizon, and no fresh grid to rescue a losing seed. If the archive cannot distinguish two construction rates, keep the ordering unresolved and prefer the simpler policy for the next comparison rather than claiming precision it does not contain.

**Final revised thesis:** B's strongest observed upstream candidate is the five-minute staircase increment; A's most interesting newly audited upstream lead is downside range/volume expansion, pending real-price verification. T remains the frozen placement challenger for both branches. The question is which candidate leaves usable repricing after entry, not which produces the most convincing trend chart. Channel/retest and extra indicators wait until these comparisons close.

The independent analyses and their revisions are preserved in [Brent's assessment](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_1/brent_adjacent_independent.md), [Quant's assessment](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_1/quant_adjacent_independent.md), [Brent's cross-review](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_1/brent_adjacent_crossreview.md), [Quant's cross-review](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_1/quant_adjacent_crossreview.md), and the [source audit](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_1/adjacent_source_audit.md). The [revision manifest](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_1/REVISION_MANIFEST.json) records the source hashes, original document hash and append-only verification.

---

## 10. Idea log: sector participation, market drivers and surface acceleration

**Captured from Darrell, 12 September 2026. Status: proposed, untested hypotheses.** The originating idea is to examine the broad sector ETF basket—XLK and its sector peers—for simultaneous turns and strong trends, compare equal-weight and capitalization-weighted participation, identify which sectors and constituents are powering the index, standardize unusual activity with z-scores, and examine whether their implied-volatility repricing is speeding up or slowing down.

The definitions below make that idea retrievable and testable; they are suggested research interpretations, not settings Darrell specified or findings already established. Exact ETF membership, windows and thresholds remain unselected. These ideas extend the registry without replacing §9's current first tests. [Structured idea log](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/revision_2/sector_leadership_ideas.json).

### SECTOR-01 — simultaneous sector turns and trend breadth

**Question:** does a broadening share of sectors turning in the same direction improve the remaining repricing opportunity for A or B?

Use one frozen sector ETF universe and the same causal trend definition for each. Separately record:

- The percentage **newly turning up/down** within a declared recent window.
- The percentage **already in a strong up/down trend** at that moment.
- Both percentages using **equal sector weights** and **lagged index-sector capitalization weights**.

For fully observed sectors, equal-weight upward breadth is `count(up-state sectors) / sector count`; weighted upward breadth is `sum(index sector weight × up-state indicator)`. Keep downward readings separate, with neutral/unclassified states visible. Turning and established strength answer different questions: expanding participation may be early, while a mature strong-trend reading may already be late.

Use completed, synchronized five-minute bars for the initial context interpretation; one-minute data can establish the time when a turn became observable. Do not let an unfinished candle or a later sector quote enter an earlier cross-sector snapshot. Fix the meaning of “simultaneous” before testing. If observations are missing, report sector-count and weight coverage rather than calling the missing sectors neutral or presenting partial coverage as the whole market.

**First comparison:** the frozen branch parent with versus without one breadth descriptor, controlling for the contemporaneous SPX direction/range. No separate EMA/ADX/RSI votes for each sector. Test A and B independently; broader agreement could improve direction while worsening the first option price.

### SECTOR-02 — identify the drivers, concentration and absence of leadership

**Question:** is the index moving because many sectors agree, a few heavily weighted sectors dominate, or strong opposing sectors cancel each other?

Alongside participation percentages, record estimated signed contribution over one common return window: `sector index weight at window start × sector return`. Weight refers to the sector's share of the relevant index's constituent capitalization, **not ETF AUM or ETF share price**. ETF-return attribution is a proxy; exact index attribution requires the relevant constituent weights and returns. Label the approximation and any differences between ETF holdings and the index universe.

Keep positive contribution, negative contribution, net contribution and concentration separately. This preserves the distinctions Darrell wants:

| Observed configuration | Hypothesis to examine |
|---|---|
| High equal-weight and weighted directional participation | Broadly shared advance or decline |
| Strong weighted participation but weak equal-weight breadth | A few large sectors dominate the move |
| Large positive and negative contributions with a small net | Active rotation/cancellation, despite a quiet index |
| Small contributions and little strong participation on either side | Little clear directional leadership |

Do not infer that concentrated leadership must reverse, or that cancellation and quiet activity imply the same chop regime. Record the leading sectors, their contribution shares, whether additional sectors join, and whether the leaders strengthen or weaken. “Powering” means measured contribution here, not proof of a causal flow mechanism. Historical attribution must use weights and membership available then, not today's leaders projected backward.

### SECTOR-03 — z-scores for unusual strength and participation

**Question:** are the leaders or breadth changes unusually strong relative to their own normal behavior, rather than merely the strongest members of a weak market?

Candidate measurements are a sector's return/trend strength or its signed contribution, standardized against **strictly preceding observations**: `z = (current measurement − prior mean) / prior standard deviation`. For intraday measurements, account for the clock-time pattern using available historical observations at comparable times. A robust median/dispersion formulation is an alternative to declare, not another setting to select after seeing the winners.

Keep two uses distinct:

- **Historical z-score:** unusual for that sector and time of day.
- **Cross-sectional z-score:** strong relative to the other sectors right now.

A cross-sectional ranking always creates relative leaders, even when nothing is historically strong. It cannot by itself establish a powerful market driver. Preserve raw returns and capitalization contributions beside standardized readings; an extreme z-score in a small sector need not explain much of the SPX move. Zero/insufficient historical dispersion is unavailable, not an infinite-strength signal.

Start with one measurement and one window, then ask whether unusual sector participation adds information beyond the index's own return and volatility. Do not sweep combinations of breadth thresholds, return windows, slope windows and z-score cutoffs together.

### SECTOR-04 — temporal IV-surface acceleration among the driving constituents

**Question:** when a small group is measurably driving a sector or the index, do changes in its option surface—and changes in the speed of that repricing—add information about continuation, exhaustion or failure of the move?

Identify the leading sectors and influential constituents using only contributions known by the decision time. Freeze that leader set for the evaluation window. Do not choose the stocks that subsequently explained the day's move, and allow a legitimate “no clear leaders” state. Compare selected leaders with the broader sector and contemporaneous nonleaders; otherwise this may merely rediscover broad market stress.

Track separately defined surface coordinates, such as constant-tenor ATM IV, a fixed-delta risk reversal or put-skew measure. Retain the metric's sign convention. For a causally smoothed coordinate `f(t)` at equal time intervals `h`, distinguish:

- Level: `f(t)`.
- Repricing velocity: `[f(t) − f(t−h)] / h`.
- Repricing acceleration: `[f(t) − 2f(t−h) + f(t−2h)] / h²`.

This captures **the second derivative over time**, rather than smile curvature across strikes. Positive acceleration can mean IV is rising faster **or falling more slowly**; negative acceleration can mean IV is falling faster **or rising more slowly**. Interpret level, velocity and acceleration jointly. The surface's directional implication also depends on the coordinate—ATM IV and call-minus-put risk reversal cannot share an unexplained bullish/bearish sign rule.

Hold tenor and delta/moneyness conventions stable. Moving strikes, expiry rolls, stale/asynchronous quotes and numerical second differences can create artificial acceleration. Use causal smoothing and a declared sampling interval; daily snapshots support daily changes, not reconstructed minute-by-minute acceleration. First distinguish incremental information from a surface response to contemporaneous spot movement. A price rally plus falling IV is not automatically an independent second confirmation.

This is an explicitly separate **options-data extension** to the OHLCV research, authorized by this new idea. Use only the relevant data already available; missing constituent surfaces or historical weights do not block the simpler breadth study. Existing negative surface-acceleration and leader-specific results in §9 are relevant counterevidence, not grounds to label this narrower conditional idea either proven or impossible.

### Logged sequence and evaluation boundary

Capture price participation and contribution first (**SECTOR-01/02**), evaluate one useful normalization (**SECTOR-03**), then consider conditional constituent surface dynamics (**SECTOR-04**) where existing coverage supports them. These are related hypotheses, not four independent votes to stack into an entry gate. Their place after the current §9 tests is unchanged by logging them.

The eventual outcome remains branch-specific: completion before the fixed failure/deadline, failed-leg cash, distinct episodes/days and incremental value against the frozen parent. Sector agreement, dominant leaders and unusual surface acceleration are explanatory observations until that comparison earns them an operational role. No tests or performance claims accompany this capture.

---

## 11. B06 false-start follow-up: context must earn its place

**Added 13 September 2026 at Darrell's request to investigate B06 after reviewing the integrated ten-day dashboard.** This focused follow-up revisits channel-breakout context; it does not turn the earlier staircase evidence into a B06 result or change any dashboard entry rule.

Brent and Quant initially ranked the existing frozen-level retest, then the existing five-minute EMA context, as the most coherent false-start experiments. A protocol was written before comparing those already-defined candidates on the same 69 B06 immediate parents. The fixed inherited screen was +5 SPX points before −15 within sixty minutes from the actual next observed one-minute open.

| Candidate | +5 first / entries | −15 first | Neither | Active days |
|---|---:|---:|---:|---:|
| Existing B06 immediate | 34 / 69 | 6 | 29 | 10 |
| Immediate with existing EMA9/20 + three-bar EMA20 rise | 24 / 48 | 6 | 18 | 7 |
| Existing B06 retest | 9 / 22 | 2 | 11 | 9 |
| Those same 22 parents entered immediately | 8 / 22 | 1 | 13 | 9 |

There were no unresolved same-minute first-touch ties. This is a spot-path screen, not option construction accuracy or persistent-trend accuracy. The EMA condition removed ten target-first parents and none of six adverse-first parents. Waiting for retest added one target on matched parents but also one adverse outcome, while the 47 no-retest parents contained 26 target-first references. Both personas revised: **neither tested addition earns promotion here.**

**The next nominated investigation is previously known price structure/headroom.** Record whether a B06 breakout clears the earlier session high or only a local rolling thirty-minute high while older resistance remains overhead. Use one fixed causal reference and distances before selecting a cutoff. Study breakout-episode age, ATR extension and repeats separately for late entries. Preserve structural-pullback and micro-staircase alternatives as distinct deferred hypotheses; no first-N cap, optimized hold length or additional indicator vote is nominated.

The known SPY and eleven sector ETF intraday caches end 11 June and do not cover these ten August–September sessions. Sector participation/contribution remains an interesting existing-history extension; IV-surface acceleration remains lower priority. No market data was acquired.

The [full B06 layer review](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/b06_layer_review_2026-09-13/B06_LAYER_REVIEW.md) preserves the entire idea ranking, proposed next annotations, fixed protocol, paired/daily counts, input hashes, code and seven path-accounting tests. The [persona decision log](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/b06_layer_review_2026-09-13/PERSONA_DECISIONS.md) preserves their original and revised views plus the bounded arbitration.

### 11.1 Requested B06 + B09 combination check

**Added 13 September 2026 after Darrell specifically requested combining the one-minute staircase with B06.** The protocol was written before computing this additional comparison. Same 69 parents, ten dates, native minute opens and inherited +5-before−15-in-sixty-minutes price screen; no new data or dashboard gates.

| Comparison | +5 first / references | −15 first | Neither |
|---|---:|---:|---:|
| B06 immediate | 34 / 69 | 6 | 29 |
| B09 two-bar-slope EMA context only at B06 | 24 / 48 | 6 | 18 |
| B09 minute shape only at B06 | 11 / 26 | 2 | 13 |
| Full B09 qualification at B06 | 9 / 19 | 2 | 8 |
| First later B09 qualification above frozen B06 level | 21 / 45 | 8 | 16 |
| Same 45 parents entered immediately | 28 / 45 | 5 | 12 |

The same-time combination uses qualification state, not literal triangle coincidence: B09 triangles only mark run starts. There are nine triangle coincidences but nineteen qualifying states at B06 decisions. The delayed version requires no retest touch and inherits B06's thirty-minute, failed-five-minute-close and 14:30 cancellation rules. Its triggering minute is later, while its two preceding staircase bars may precede B06.

Median delay was two minutes and the entry reference rose by a median 1.58 SPX points. Five parent targets occurred before confirmation. The common original-parent deadline produces the same delayed counts. Forty-five delayed parent references occupy forty-one unique day/minute coordinates. The attractive 28/45 immediate rate is retrospectively selected using future B09 and cannot be used as a causal entry filter.

**Disposition: these exact B06+B09 combinations do not earn promotion on this screen.** Preserve location and maturity as separate questions; do not rescue B09 by searching coincidence windows or thresholds. These are price-path outcomes, not sustained-trend or option accuracy. [Full definitions, findings and reproducible artifacts](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/b06_b09_combo_2026-09-13/FINDINGS.md).


### 11.2 New information: sector ETF IV and temporal acceleration

**Added 13 September 2026 at Darrell's request.** New sector ETF minute data is now authorized through the ThetaData SDK, stored under central_trade_data. IV-first supersedes the earlier price-breadth-first research order; the other sector ideas in §10 remain preserved.

**Revised thesis:** B06 supplies the price trigger. Sector option repricing may describe broad stress or easing uncertainty, but must add beyond the price movement already observed. An ETF option surface measures its basket, not the surfaces of its individual constituents. A positive time acceleration can mean IV is rising faster or falling more slowly; it is not inherently bearish or bullish.

A protocol fixed before retrieval used the earliest original cohort date, 2026-08-12, and all eleven sector ETFs. The SDK returned 93,840 minute-IV rows in twelve files. The first measurement is one 30-calendar-day ATM-spot provider-model proxy with no tenor/strike extrapolation, separate calls/puts and bid/ask uncertainty. It is not a complete dividend-aware American surface. Ten ETFs supply 390 valid minutes each; XLRE supplies 208.

The fixed five-minute backward differences yielded **0/4,032 velocity envelopes and 0/3,969 acceleration envelopes excluding zero**. These conservative bid/ask-derived ranges are not confidence intervals and do not prove absence of predictive information. They show poor sign resolution for this measurement. A separate 132-observation actual-tick audit matched every sampled bid/ask pair. XLK demonstrated fresh quote events with unchanged prices; other sampled sector quotes were minutes old. Changing underlying prices can change calculated IV while the option quote prices remain fixed. Fresh timestamps alone therefore do not establish independent information.

**Disposition:** no IV-velocity or acceleration B06 gate, no outcome join and no automatic ten-day expansion. Brent and Quant retain the sector-IV hypothesis but put measurement first. A separately specified monthly-expiry comparator, using the same pilot date and all eleven ETFs without looking at B06 outcomes, is the next nominated quote-quality experiment. Preserve the original nearest-expiry pilot; do not declare a replacement winner. Then assess one broad sector stress/velocity descriptor beyond contemporaneous returns and common IV movement. Acceleration follows only if the series supports meaningful change measurement. Monthly comparison and predictive tests are not yet run.

The current-day/lagged cap-weighted participation, contribution, concentration, historical z-score, risk-reversal, term-structure and constituent-surface ideas remain separate backlog items. No cap weights, historical normalization or missing observations were invented. The adjacent negative intraday-surface and leader-acceleration studies remain counterevidence, not an exact test of this B06-conditioned sector hypothesis.

[Full findings and preserved protocol](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/sector_iv_pilot_2026-09-13/FINDINGS.md). [Independent Brent/Quant decision record](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/sector_iv_pilot_2026-09-13/PERSONA_DECISIONS.md). Raw data: `/Users/dgrissen/Dev/central_trade_data/thetadata/sector_iv_b06_1m_2026-09-13-v1/`.


### 11.3 Clarification: surface shape, sector participation and B06-matched acceleration

**User clarification, 13 September 2026:** the intended hypothesis concerns WHICH sector surfaces are changing, whether participation is narrow or broad (one sector, more than half, at least 70%), and whether those changes accelerate across the SAME lookback used by B06.

The first pilot did not test that hypothesis. It reduced each ETF to one constant-30-calendar-day ATM-SPOT IV point (strike/spot=1, not fixed50delta), and used five-minute differences at t,t−5,t−10. It had no wing/skew/term-shape measurement, no sector participation calculation and no thirty-minute B06 alignment. Its quote-uncertainty result therefore must not be presented as a negative result for the clarified hypothesis. The original pilot remains a measurement audit only.

**Corrected small prototype scope, proposed before further retrieval/outcomes:** use the same eleven ETFs and a constant30-calendar-day smile slice with three coordinates: put delta−0.25, ATM-spot, call delta+0.25. ATM-spot is not exactly50delta and must remain labeled. This is a sparse slice of the surface; a complete surface also varies over expiration. Keep7-day coordinates and7-vs30-day term structure as a separate extension, not required for this first breadth test. No claim these DTE/delta choices are optimal.

Capture each coordinate every minute. The primary descriptors are ATM IV level/change and put richness (25delta put IV minus ATM IV). Also retain call richness (25delta call IV minus ATM IV) and call-minus-put risk reversal; they are related descriptions of the same three inputs, not independent indicator votes. Use IV percentage points and fixed-coordinate interpolation with raw contract provenance. Existing IV-only downloads lack delta and do not guarantee coverage of the25delta wings; those coordinates must be obtained from real SDK Greeks/quotes, never inferred from ATM proximity. Fixed-delta coordinates still move across strikes as spot changes; retain that source of mechanical variation.

**B06 clock:** at decision time T, the completed breakout candle is [T−5,T), and the six previous five-minute reference bars are [T−35,T−5). Match the thirty-minute surface reference to those six bars, not accidentally to the last thirty minutes ending at T. Use the native samples at T−35 through T−6 inclusive. At10:05, that is9:30–9:59; the10:00–10:04 breakout-bar update is displayed separately. Missing opening observations remain missing, not backfilled.

For each sector and descriptor, fit a straight-line change rate to each fifteen-minute half using all fifteen native samples: first half T−35..T−21; second half T−20..T−6. Require all required source coordinates for the initial descriptive calculation, otherwise mark that sector/descriptor unavailable. The halves' time centers are fifteen minutes apart. Define acceleration estimate=(second-half slope−first-half slope)/15, in IVpoints/minute². Keep both slopes and the full-window change. This is a two-half acceleration estimate, not an instantaneous derivative. Show the breakout-bar update separately; do not silently include it in the channel-reference window or use observations at/afterT to qualify the original entry.

**Participation:** show sector identities, first-half/second-half rates, and separate counts for each descriptor: rising, falling, unchanged, and unavailable. Report raw midpoint direction alongside whether that direction survives the propagated quote envelope; do not call every tiny nonzero change meaningful. Preserve counts out of the fixed eleven and show valid coverage separately. One sector=1/11; more than half=at least6/11; at least70%=at least8/11 (72.7%). These are display buckets requested by the user, not tuned entry gates. Track whether participation broadens from the first half to the second. Separately count rising-and-speeding-up, rising-and-slowing, falling-and-speeding-down, and falling-and-slowing; do not mix positive acceleration with bullish direction.

Equal-weight counts are sufficient initially. Keep verified lagged-cap weighting as a separate existing backlog item. Do not combine rising ATM IV with falling put richness into a generic same-direction 'surface changed' vote. Example question: at B06, are8/11 sectors showing rising put richness, versus just one; and is the rate increasing in six of those eight? This is a hypothetical display example, not an observed result.

**Disposition:** this clarification changes the proposed scope and supersedes treating a standalone five-minute ATM-acceleration resolution check or monthly-only comparator as the test of the user's hypothesis. Quote-quality diagnostics remain visible, but the relevant descriptive test is surface-component participation and acceleration over the B06 reference window. No new surface retrieval, breadth computation or B06 outcome test has run for this clarified design.


### 11.4 Completed sector-surface breadth exploration over the B06 reference

**Added 13 September 2026 after Darrell authorized the clarified exploration.** This supersedes §11.3's not-yet-run status while preserving the original pilot and hypotheses. New native minute IV and Greek data was obtained through the ThetaData SDK for the original ten dates and eleven sector ETFs. Raw data is stored at `/Users/dgrissen/Dev/central_trade_data/thetadata/sector_surface_b06_1m_2026-09-13-v1/`. The collection contains 108/110 sector-days and 10,378,800 combined source rows from 422 successful explicit data requests; source-row volume does not increase the ten-date research sample.

**Fixed scope:** constant 30-calendar-DTE ATM-spot, −0.25-delta put and +0.25-delta call. Primary descriptors are ATM IV and put richness (put25 minus ATM), with call richness and call-minus-put risk reversal retained as related secondary descriptions. At B06 decision T, the reference is T−35 through T−6, split into fifteen native samples per half. Latest-half slopes describe direction; acceleration is the change between half-window slopes divided by fifteen. The breakout candle is separate. No inferred delta, minute fill, tenor extrapolation or optimized cutoff.

| Observation at original B06 decision | Entries / days | +5 first | −15 first | Neither | Target fraction |
|---|---:|---:|---:|---:|---:|
| All B06 immediate | 69 / 10 | 34 | 6 | 29 | 49.3% |
| ATM falling in ≥6/11 sectors | 38 / 9 | 20 | 3 | 15 | 52.6% |
| ATM falling in ≥8/11 sectors | 13 / 6 | 7 | 1 | 5 | 53.8% |
| ATM falling with slopes becoming more negative in ≥6/11 | 15 / 6 | 10 | 1 | 4 | 66.7% |
| ATM falling with slopes becoming more negative in ≥8/11 | 2 / 2 | 1 | 0 | 1 | 50.0% |
| Put richness falling in ≥6/11 | 6 / 5 | 5 | 1 | 0 | 83.3% |
| Put richness falling in ≥8/11 | 2 / 2 | 2 | 0 | 0 | 100.0% |

The inherited screen remains +5 SPX points before −15 within sixty minutes, not option completion or sustained-trend accuracy. “Falling with slopes becoming more negative” includes a transition from rising to falling; it does not require both halves to decline. Rows overlap. The tiny 100% group earns no superiority claim.

**Revised thesis:** shared sector ATM easing, especially a broad move toward more-negative IV slopes, is the leading surface observation to inspect alongside B06. Ordinary decline breadth offers little separation. Greater participation is not consistently better, and put-richness direction does not supply a simple stress veto: broadly rising put richness also contains 16 targets among 29 entries, with one adverse outcome.

For the leading six-sector ATM observation, removing each date leaves 63.6–72.7% target-first, above the correspondingly reduced baseline. However, three dates provide 12/15 entries and eight of ten targets. A keep-only rule would discard **24 of the baseline's 34 targets**, retaining just 10. Within the broader 38-entry ATM-decline cohort, the other 23 entries contain ten targets, two adverse and eleven neither outcomes; some have unknown acceleration membership. This is a descriptive decomposition after viewing results, not an independent test.

**Breadth and speed are distinct.** On September 3 at 11:10, ATM-decline participation grows from one to six of ten available sectors, with all six showing more-negative slopes, followed by +5 first. On August 27 at 13:10, participation grows from five to eight, seven show more-negative slopes, yet −15 occurs first. On August 28 at 13:50, participation contracts from nine to eight while eight have more-negative slopes; neither price boundary wins. Sector identities and all original events remain in the report and figures.

**Coverage and interpretation:** ATM has all eleven complete sectors at only seven events; wings have none. Before the outcome join, missing-sector bounds were specified with denominator eleven: observed count ≥ threshold means known membership, count + missing < threshold means known nonmembership, otherwise unknown. This retains useful observations without inventing sectors. For the leading ATM condition there are 15 known-meeting, 42 known-below and twelve unknown; those unknowns include six targets. Count certainty is not quote precision: every valid primary full-window slope and acceleration still has a conservative bid/ask envelope spanning zero. These ranges are not confidence intervals or proof of no information.

Put-richness full-window slopes correlate positively with their sector's simultaneous spot return across all ten measurable sectors. The options descriptors have not established information beyond price movement, and the provider's European/default-dividend calculation and moving fixed-delta coordinates remain explicit limitations. No fitted residual, weighted composite, sector ranking, tenor search or new dashboard gate was introduced.

**Brent and Quant disposition:** retain broad ATM easing/turning-down as the leading surface follow-up, preserve the put-richness result as a small secondary observation, and promote neither. Precision with opportunity count considered remains unproven. Inspect surface/price disagreements on these existing events alongside the already nominated price location, advance maturity and frozen-level behavior; do not rescue the result by fitting another threshold or combining votes. Cap-weighted breadth, term structure and constituent surfaces remain separate backlog ideas.

[Full findings, figures and every fixed comparison](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/sector_surface_breadth_2026-09-13/FINDINGS.md). [Independent persona decision record](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/sector_surface_breadth_2026-09-13/PERSONA_DECISIONS.md). The isolated slug preserves frozen protocol/features, source hashes, sector/day/event tables, day-deletion sensitivity and 52 passing computation tests. This exploration is on reused dates and does not provide out-of-sample validation.


### 11.5 Random 50-day replication of sector-surface breadth

**Completed 13 September 2026 after Darrell requested 50 random 2026 above-VT dates.** One frozen uniform draw selected 50 of 85 eligible additional sessions, excluding the original ten. Eligibility means observed 09:30 SPX open strictly above same-date VT, supported by an available pre-open note, with complete native minute data. Missing SPX coverage was completed through the ThetaData SDK before drawing. No dates were rerolled or replaced for their signals, option coverage or outcomes. The sample spans January 2–August 10 and includes July 13 with zero B06 entries; the other 49 dates supply 374 parents.

**The exact leading hypothesis was frozen:** at least six of the same eleven sectors have negative latest-half ATM IV slopes and slopes becoming more negative across the two fifteen-minute halves of B06's preceding thirty-minute reference. Constant 30-calendar-DTE ATM-spot and native ±0.25-delta wings, interpolation, quote gates, missing-sector arithmetic and +5-before−15-in-sixty-minutes outcome scoring were unchanged. Surface, breadth, B06 and scoring modules remain byte-identical to their recorded originals. Features and analysis code were frozen before new outcomes.

| New 50-day comparison | Entries / active dates | +5 first | −15 first | Neither | Target fraction |
|---|---:|---:|---:|---:|---:|
| All B06 immediate | 374 / 49 | 239 | 51 | 84 | 63.9% |
| ATM falling in ≥6/11 | 217 / 48 | 144 | 36 | 37 | 66.4% |
| ATM falling in ≥8/11 | 76 / 35 | 57 | 8 | 11 | 75.0% |
| ATM falling with more-negative slopes in ≥6/11 — frozen primary | 93 / 35 | 67 | 13 | 13 | 72.0% |
| ATM falling with more-negative slopes in ≥8/11 | 22 / 14 | 17 | 1 | 4 | 77.3% |
| Put richness falling in ≥6/11 | 72 / 34 | 47 | 7 | 18 | 65.3% |
| Put richness falling in ≥8/11 | 9 / 8 | 8 | 0 | 1 | 88.9% |

**The higher target fraction repeated; reduced adverse-first risk did not.** The primary advantage over its own baseline shrank from 17.4 percentage points in the old study to 8.1 points here. Its adverse-first rate is 14.0%, versus baseline 13.6%; the difference mainly reflects fewer neither outcomes (14.0% versus 22.5%). A keep-only rule retains just 24.9% of entries and 28.0% of targets, excluding 172 successful baseline triggers. These are spot-path counts, not persistent-trend accuracy or option P&L; neither does not automatically mean false start.

The observation now spans 35 dates, with at most six selected entries on one date and 16/93 on the busiest three. Removing any one date leaves a positive 6.7–10.1-point advantage over its reduced baseline. However, the predeclared paired whole-date bootstrap's 95% percentile interval is **−0.9 to +17.9 points**, including zero. The 10,000 draws retain all 50 sampled dates, including the zero-entry day. This is descriptive date-resampling uncertainty, not finite-population-corrected inference or removal of dependence between regimes and nearby dates.

There are 93 known primary members, 216 known below and 65 unknown. Unknowns contain 40 targets and remain in baseline. All eleven ATM sectors are complete at 114 events; a strict full-coverage subset is a different cohort. All 3,778 complete ATM sector/event windows still have full-slope and acceleration bid/ask envelopes spanning zero. This is unresolved measurement sign, not proof of no predictive information. Put-richness full-window slopes correlate positively with simultaneous sector spot returns across all eleven ETFs (Spearman approximately +0.24 to +0.53), leaving incremental information beyond price unproven.

**Revised thesis, agreed independently by Brent and Quant:** broad ATM easing/turning down may identify B06 attempts more likely to achieve the specified upward move instead of remaining unresolved. It has not demonstrated fewer damaging false starts or enough benefit after the lost opportunities to earn a hard entry gate. The next nominated existing-data comparison is the frozen surface descriptor versus sector-price participation over the identical reference window, especially their disagreements. Define that comparison before opening its outcome groups; preserve day dependence, unknowns and opportunity counts. Do not replace the primary with an attractive eight-sector or nine-entry put-richness result after seeing this table.

The six-sector put-richness result weakened from 83.3% on six old entries to 65.3% on 72 new entries, close to baseline. Eight-sector ordinary ATM decline remains a separate secondary observation. Location/headroom, advance maturity, level holding, cap weighting, term structure and constituent surfaces remain preserved independent hypotheses. No new dashboard admission rule follows from this replication.

Raw SDK responses are stored at `/Users/dgrissen/Dev/central_trade_data/thetadata/sector_surface_b06_50d_2026-09-13-v1/`: 2,016 successful explicit option requests, 46,740,000 combined IV/Greek rows and 537/550 sector-days with permitted tenor brackets; the thirteen missing brackets are XLRE. The study still has 50 sampled dates, not millions of independent observations. Pre-open archived labels do not establish unrevised notes or contemporaneous local capture. Additional historical dates from an already researched year are not automatically forward or untouched validation.

[Full findings and three figures](/Users/dgrissen/Dev/delta_bomb/outputs/b06_sector_surface_50d_2026-09-13/FINDINGS.md). [Independent persona decisions](/Users/dgrissen/Dev/delta_bomb/outputs/b06_sector_surface_50d_2026-09-13/PERSONA_DECISIONS.md). [Sampling account and saved draw](/Users/dgrissen/Dev/delta_bomb/outputs/b06_sector_surface_50d_2026-09-13/SAMPLING.md). The isolated slug contains every event, sector, day and fixed comparison; frozen hashes; 115 passing tests plus eight subtests; and independent numerical replay. The original ten-day study remains separate.


### 11.6 Completed IV-versus-price participation comparisons

**Completed 14 September 2026 after Darrell explicitly requested A versus C, B versus D and B versus C.** Same 374 B06 parents and 50 sampled dates; no new data, threshold or dashboard gate. The exact six-sector ATM IV condition from §11.5 is retained. The price comparison counts at least six of eleven sectors with positive endpoint returns over the same T−35 through T−6 reference. This is positive participation, not a strong-trend definition.

Membership is independently yes/no/unknown for IV and price. Six observed positives establish yes; observed positives plus missing sectors below six establish no; otherwise unknown. The four fully known cells contain 295 parents. Another 79, including 49 targets, remain in five explicit unknown cells. Unknown does not mean negative. All 50 dates remain in daily tables and whole-date resampling.

| Cell | IV / price participation | Entries / dates | +5 first | −15 first | Neither | Target fraction |
|---|---|---:|---:|---:|---:|---:|
| A | Yes / yes | 62 / 30 | 45 | 9 | 8 | 72.6% |
| B | Yes / no | 26 / 20 | 17 | 4 | 5 | 65.4% |
| C | No / yes | 153 / 44 | 88 | 21 | 44 | 57.5% |
| D | No / no | 54 / 30 | 40 | 6 | 8 | 74.1% |

**A versus C:** IV confirmation inside broad price participation accompanies a +15.1-point target advantage, with 95% paired whole-date resampling interval −0.9 to +30.2. Adverse-first frequency is 14.5% versus 13.7%, so it does not show fewer damaging false starts. The difference mainly concerns neither outcomes (12.9% versus 28.8%). An IV veto would reject all 153 C entries, removing 21 adverse outcomes but also 88 targets. Keeping A retains only 45/133 targets from the fully known price-supported group.

**B versus D:** IV confirmation without broad price participation does worse here: target frequency 65.4% versus 74.1%, difference −8.7 points with interval −31.3 to +10.8. Adverse-first frequency is also higher, 15.4% versus 11.1%. This does not support IV as independent permission for price-breadth-negative entries. Do not promote D after observing its attractive fraction.

**B versus C:** the IV-only disagreement group has a +7.9-point target advantage over the price-only group, with interval −15.6 to +27.5. Its adverse frequency is also higher. Both classifications change in this comparison, so it does not isolate an incremental IV effect. On the same fully known cohort, replacing price selection A+C with IV selection A+B removes C (153 entries; 88 targets, 21 adverse, 44 neither) and adds B (26 entries; 17 targets, four adverse, five neither). The net change is 127 fewer entries, 71 fewer targets, 17 fewer adverse and 39 fewer neither. The selected adverse fraction rises from 14.0% to 14.8%; fewer total adverse outcomes primarily reflect fewer attempts.

No single-date deletion reverses any observed target-difference direction, but all three target intervals include zero. The fixed 10,000 date draws, seed 20260914, use every sampled date including the zero-entry day, with no undefined comparison draws. These are per-comparison descriptive intervals, not simultaneous guarantees or finite-population-corrected inference. Repeated signals and related dates remain dependent.

The fully known all-parent baseline is 190/295 targets. IV selection A+B retains 62 targets on 88 entries; price selection A+C retains 133 on 215; both A retains 45 on 62. The original IV rule remains 67/93: five IV-positive entries have unknown price membership and all five reached target, so they are omitted only from the shared-known-cohort comparison. The full unchanged baseline remains 239/374.

**Revised thesis:** IV remains descriptive context for target-versus-unresolved behavior in some price-supported breakouts. It has not earned a damaging-false-start veto or independent admission when price participation is weak. The coarse price comparison does not control actual participation count, return magnitude, recent price shape, time of day or advance maturity. Midpoint IV signs remain unresolved by the prior conservative quote envelopes. This is an exploratory follow-up on already inspected historical events, not new validation or option accuracy. Existing structural, age, cap-weight, term-structure and constituent-surface ideas remain preserved.

[Full answers, figure and all nine joint cells](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_price_disagreement_2026-09-14/FINDINGS.md). [Independent Brent/Quant decisions](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_price_disagreement_2026-09-14/PERSONA_DECISIONS.md). The isolated slug preserves the pre-tabulation protocol and source/code hashes, all parent/date classifications, all requested contrasts, opportunity accounting, eight passing tests and independent numerical verification. No previous study or hypothesis was replaced.


### 11.7 Test 1 completed: first B06 versus repeats in a frozen-boundary episode

**Completed 17 September 2026 after Darrell authorized only test 1 from the six-test shortlist.** Same 374 B06 parents and all 50 sampled dates; no new data or entry rule. An episode begins with the first eligible B06, freezes that first channel boundary, and resets only when a later completed five-minute close returns at/below it. Every completed bar is checked, including bars without signals. Wicks do not reset; later channel boundaries do not update the original level; there is no thirty-minute timeout. Old-episode reset precedes any coincident existing eligible parent. All singleton firsts remain included.

| Reference group | Entries / active dates | +5 first | −15 first | Neither | Target fraction |
|---|---:|---:|---:|---:|---:|
| All B06 | 374 / 49 | 239 | 51 | 84 | 63.9% |
| First in episode | 113 / 49 | 74 | 17 | 22 | 65.5% |
| Subsequent in same episode | 261 / 46 | 165 | 34 | 62 | 63.2% |

The inherited +5-before−15-within-sixty-minutes price screen remains unchanged. There are no ambiguous first touches. The episodes total 113: 52 singletons and 61 with repeats. The largest contains 22 parents. This operational first signal is not necessarily the true start of a market advance.

**The first-only filter does not earn promotion.** Its +2.3-point target advantage over repeats has a paired whole-date 95% percentile interval of −9.9 to +15.7 points. Adverse frequency is slightly higher, 15.0% versus 13.0%, with a +2.0-point difference and interval −6.8 to +10.7. Compared with all B06, first-only improves the target fraction by only 1.6 points, interval −7.0 to +10.9. It retains 30.2% of entries and 31.0% of targets, excluding 165 successful repeats along with 34 adverse and 62 neither outcomes.

**Preserve the day-weighting distinction:** equal-active-day target averages are 72.4% for firsts on 49 days and 47.3% for repeats on 46 days, materially different from the pooled fractions. Repeat successes are more concentrated in high-entry-count dates; the busiest three repeat dates supply 48 targets among 54 repeats. These averages use different weights and day sets and are not a matched-day causal estimate or an executable portfolio result. They must not replace the predeclared entry-pooled primary result, but should not be hidden.

Repeats have median age 40 minutes, four preceding signals and a 13.65-point entry-price increase from the first signal. Median extension is 1.26 times the first signal's frozen per-day RMA14 ATR diagnostic. That ATR is initialized from the 09:30 bar, without fabricated prehistory, and does not gate signals. Median clock times also differ: 11:45 first versus 12:25 repeat. This comparison does not isolate age from timing, price development or survival of the original boundary.

The fixed 10,000 paired whole-date draws use seed 20260917 and all 50 dates, including July 13 with zero signals; no estimates are undefined. Single-day deletion gives first-minus-repeat target differences −0.1 to +4.8 points. No first-two/three cap, alternate reset, IV overlay or other shortlist test was searched. The result does not invalidate every maturity hypothesis; it fails to support this particular first-only admission rule.

[Full findings and figure](/Users/dgrissen/Dev/delta_bomb/outputs/b06_episode_age_2026-09-17/FINDINGS.md). [Independent persona decisions](/Users/dgrissen/Dev/delta_bomb/outputs/b06_episode_age_2026-09-17/PERSONA_DECISIONS.md). The isolated slug preserves the protocol/source/code freeze, all causal annotations and episode records, unchanged source outcomes, all daily rows, uncertainty calculations and ten passing timing/accounting tests. Tests 2–6 remain proposed, and prior documents/results remain preserved.


### 11.8 User-proposed B06 one-hour cooldown

**Completed 17 September 2026 as a separately authorized follow-up.** Admit the day's first
existing B06, then block parents for sixty elapsed minutes after each admitted parent.
Equality at sixty minutes is eligible. Blocked parents never restart the clock; a new
episode, level failure or completed outcome does not release it early. Admit only an
existing eligible signal, and reset daily. This differs from the first-per-episode test.
The sixty-minute duration was proposed after inspecting prior observations; this is
exploratory reuse, not a holdout. No alternate duration or exception was searched.

Same fifty dates and 374 original parents; unchanged +5-before−15 over sixty native minute
intervals from the original entry-open reference. Zero ambiguous outcomes; July 13 has no
B06 and remains in all daily accounting and date resampling.

| Reference group | Entries / active dates | +5 first | −15 first | Neither | Target fraction |
|---|---:|---:|---:|---:|---:|
| All original B06 | 374 / 49 | 239 | 51 | 84 | 63.9% |
| Admitted by one-hour cooldown | 124 / 49 | 78 | 21 | 25 | 62.9% |
| Blocked by cooldown | 250 / 46 | 161 | 30 | 59 | 64.4% |

**The cooldown does not earn adoption as a per-entry accuracy filter.** Admitted-minus-all
target difference is −1.0 percentage point, with paired whole-date 95% interval −7.0 to
+5.8 points. Adverse-first frequency increases from 13.6% to 16.9%: +3.3 points, interval
−1.7 to +8.1. The secondary admitted-minus-blocked target difference is −1.5 points,
interval −10.7 to +8.7. Retention is 33.2% of entries and 32.6% of targets; the rule blocks
161 targets, 30 adverse and 59 neither outcomes. Reduced total adverse observations must
not be mistaken for improved adverse frequency per admitted entry.

The paired equal-active-day result is more favorable: 63.6% cooldown versus 58.5% all B06,
both on the same 49 active dates. The average daily target-fraction difference is +5.1
points; 21 days improve, 18 worsen and ten are unchanged. This answers a different question
from the pooled entry rate and does not supersede the primary comparison. The cooldown
limits admitted entries to at most four per date here, versus twenty-two in the baseline.

The fixed 10,000 paired date draws use seed 20260917 and all fifty dates, with zero undefined
draws. Deleting any date leaves target differences between −2.3 and −0.3 points and adverse
differences between +2.4 and +4.0. Those checks do not establish a harmful causal effect;
they show that the pooled disappointment does not hinge on one date. Admitted sixty-minute
diagnostic windows do not overlap within a session. Neither this spacing nor its spot
outcomes establish option economics, execution quality or actual trend exhaustion.

[Full findings and figure](/Users/dgrissen/Dev/delta_bomb/outputs/b06_cooldown_60m_2026-09-17/FINDINGS.md).
[Independent Brent/Quant decisions](/Users/dgrissen/Dev/delta_bomb/outputs/b06_cooldown_60m_2026-09-17/PERSONA_DECISIONS.md).
The isolated slug preserves the fixed protocol, source/code and selection freezes, all
admitted/blocked events, paired daily accounting and uncertainty. Eleven rule tests and
Ruff passed. No data downloads, dashboard modifications or other shortlist tests.


### 11.9 Test 2 completed: B06 and the earlier session high

**Completed 17 September 2026 after explicit authorization of shortlist test 2.** Same
374 parents and fifty sampled dates, without first-only, cooldown or IV intersections.
The ceiling is the maximum RTH five-minute high strictly before the breakout candle.
Classify the breakout close as cleared, below or numerically equal (tolerance 1e−8).
Exclude the breakout candle's wick, all future data, overnight and prior sessions.
Signed entry room is ceiling minus the saved next-minute open; keep it separate from
the close-based classification. Current known per-day RMA14 ATR scales room descriptively.

| Reference group | Entries / active dates | +5 first | −15 first | Neither | Target fraction |
|---|---:|---:|---:|---:|---:|
| All B06 | 374 / 49 | 239 | 51 | 84 | 63.9% |
| Close clears earlier session high | 201 / 31 | 130 | 24 | 47 | 64.7% |
| Close still below earlier high | 173 / 46 | 109 | 27 | 37 | 63.0% |

No equal or ambiguous cases occurred. The inherited +5-before−15-in-sixty-native-minutes
outcome remains unchanged. Cleared-minus-below target difference is +1.7 percentage points,
with paired whole-date 95% interval −12.7 to +14.6; adverse-first difference is −3.7 points,
interval −11.3 to +4.4. Cleared-only keeps 53.7% of entries and 54.4% of targets, excluding
109 targets, 27 adverse and 37 neither outcomes. Its advantage over all B06 is only +0.8
target point, interval −6.6 to +6.4. The session-high requirement does not earn adoption.

**Measured room matters to interpretation:** all 173 below-high entries have a ceiling
older than the six-bar channel. Their median room is 13.57 SPX points / 2.05 ATR; the
middle half spans 4.98–36.06 points / 0.88–3.65 ATR. Being below an older high often
leaves more than the five-point target distance. This broad split does not test a
specific nearby-ceiling veto. No point/ATR cutoff or room/outcome bins were searched.
Among cleared closes, five entry opens are 0.03–0.26 point below the old high and one is
at it; these differences remain recorded without reclassification. ATR initialization
and its lack of prior-session warmup remain explicit.

**Day weighting reverses the small pooled advantage:** active-day target means are 46.7%
cleared (31 days) versus 60.6% below (46 days). On 28 common dates, they are 42.9% versus
60.8%, mean paired difference −17.9 points: six cleared-better dates, nineteen below-better
and three ties. The busiest three cleared dates supply 45 targets on 54 entries. Report
this openly while retaining the planned per-entry primary. Common days still differ in
clock time and price development; median signal times are 11:40 versus 12:40 ET.

All fifty dates, including the zero-event date, enter 10,000 shared date draws with seed
20260917; zero undefined draws. Delete-date cleared-minus-below target differences range
from −2.1 to +3.8 points, adverse differences −5.3 to −2.4. This is exploratory reused
history and a possible reference level, not proof of resistance supply or option profit.
Preserve the signed room annotations without deploying a high-clearance rule or tuning
a proximity cutoff after these results. Other shortlist tests remain untouched.

[Full findings and figure](/Users/dgrissen/Dev/delta_bomb/outputs/b06_older_ceiling_2026-09-17/FINDINGS.md).
[Independent persona decisions](/Users/dgrissen/Dev/delta_bomb/outputs/b06_older_ceiling_2026-09-17/PERSONA_DECISIONS.md).
The isolated slug preserves the protocol/source/code freeze, all causal features, original
outcomes, daily/room ledgers, uncertainty and fifteen passing reference/timing tests.


### 11.10 Test 6 completed: later closes after the original +5 target

**Completed 17 September 2026 after authorization of the post-target path check.** All
374 original B06 scores on fifty dates remain unchanged. For target-first entries only,
inspect subsequent completed minute closes below the saved entry open, after the
target-touch minute and through the final original outcome bar. Include that final bar's
close at the deadline; exclude the bar starting at the deadline. Equality and wicks do
not qualify. The target-touch minute itself is deliberately omitted, so this does not
capture every intraminute or same-minute giveback.

Baseline: 239 targets, 51 adverse-first, 84 neither, no ambiguous cases. Of 239 targets,
**87 later close below entry, 150 have no observed later below-entry close, and two have
no subsequent close to assess**. Reversal fraction is **87/237 = 36.7%** among assessable
targets. Among reversers, median first-below lag is ten minute bars after target, with
middle half six to 24.5. No observed reversal is not proof of a sustained advance.

To account for unequal follow-up, a fixed fifteen-subsequent-close diagnostic was specified
before inspection. Only targets with all fifteen closes available qualify; later targets
are excluded consistently even if they reversed within their shorter window. Baseline
has **49/222 = 22.1%** reversals in that common window and seventeen late targets excluded.
Median target-minute offset is twelve minutes and median subsequent support is 47 closes.
All individual clocks and fixed target-offset-band tables are preserved.

| Existing context | Original target fraction | Later reversal / assessable targets | Fifteen-close reversal / eligible targets |
|---|---:|---:|---:|
| All B06 | 239/374 = 63.9% | 87/237 = 36.7% | 49/222 = 22.1% |
| IV yes | 67/93 = 72.0% | 26/66 = 39.4% | 18/64 = 28.1% |
| A: IV yes / price yes | 45/62 = 72.6% | 18/45 = 40.0% | 11/44 = 25.0% |
| C: IV no / price yes | 88/153 = 57.5% | 33/88 = 37.5% | 18/84 = 21.4% |
| B: IV yes / price no | 17/26 = 65.4% | 8/16 = 50.0% | 7/15 = 46.7% |
| D: IV no / price no | 40/54 = 74.1% | 13/39 = 33.3% | 6/32 = 18.8% |

The IV condition's higher initial hit rate **does not demonstrate improved follow-through**.
Its winner-reversal difference versus all B06 is +2.7 percentage points, paired whole-date
95% interval −6.6 to +11.0; common-window reversal difference is +6.1, interval −3.2 to
+14.7. Target-and-no-observed-reversal as a fraction of original entries is 40/93 = 43.0%
for IV yes versus 150/374 = 40.1% overall: +2.9 points, interval −5.3 to +12.0. This joint
path descriptor excludes zero-follow-up targets from its numerator and is not a new win rate.

A−C also fails to demonstrate fewer givebacks: full-window difference +2.5 points,
interval −15.2 to +18.8; fifteen-close +3.6, interval −11.1 to +18.1. B−D and B−C common-
window point estimates are worse for B, but their small target samples and wide intervals
do not establish an inverse rule. All original IV/price unknowns and all nine joint cells
remain in the full sixteen-context tables. Winner conditioning and unequal context
composition limit causal interpretation; equal duration does not eliminate those effects.

All fifty dates, including the zero-B06 date, enter shared 10,000 paired date draws with
seed 20260917. All sixteen pre-specified contrast/metric intervals include zero and have
no undefined draws. Delete-date IV-minus-baseline reversal differences remain positive,
but A−C can change sign. Intervals are descriptive and unadjusted for prior exploration.

**CIO interpretation:** the original score captures an initial favorable movement, not
assurance it sticks. A substantial minority later give it back; the IV context has not
shown protection from that. A later below-entry close is not necessarily an economic
failure if the option construction completed first. Keep all original winners, preserve
the new retrospective path record and add no future-dependent entry filter or exit rule.

[Full findings and figure](/Users/dgrissen/Dev/delta_bomb/outputs/b06_post_target_2026-09-17/FINDINGS.md).
[Independent persona decisions](/Users/dgrissen/Dev/delta_bomb/outputs/b06_post_target_2026-09-17/PERSONA_DECISIONS.md).
The isolated slug contains native-data replay, thirteen passing boundary/eligibility tests,
all event/daily/timing records, uncertainty and the documented correction of insignificant
unused display-metadata parsing differences. All path and result bytes stayed unchanged
through that correction. No new data, dashboard changes or other shortlist tests.


### 11.11 Same-sector price-up / IV-down and a causal later checkpoint

**Completed 17 September 2026 after direct authorization.** Pair every sector ETF's own
price change with its own ATM IV change over identical observations. Use the existing
374 B06 parents / fifty dates and cached constant thirty-day, spot-relative ATM surfaces.
The entry window is T−35…T−6; qualify when at least six of the fixed eleven ETFs each
have rising price and falling IV. This uses net endpoint changes without acceleration.
It is a different hypothesis from the older latest-half slope/acceleration condition.

**Entry accuracy did not improve:** paired yes produces **62/97 = 63.9%** targets versus
**239/374 = 63.9%** overall. It retains 25.9% of entries and 25.9% of targets, excluding
177 targets. Target difference is +0.01 percentage points, paired whole-date 95% interval
−10.0 to +8.9. Among broad-price entries, definite paired no gives 73/119 = 61.3%; the
paired-yes advantage is only +2.6 points, interval −12.6 to +18.2. Unknown pairing remains
separate: 42 overall, including 36 with known broad price participation.

Winner follow-through offers only a modest hint: full-follow-up below-entry closes are
23/62 = 37.1% for paired yes versus 87/237 = 36.7% overall. In the fixed fifteen later
closes, they are 11/59 = 18.6% versus 49/222 = 22.1%, difference −3.4 points with interval
−11.7 to +5.6. Against broad-price / paired-no winners the corresponding fixed-window
rate is 20/72 = 27.8%, difference −9.1 points with interval −23.9 to +6.0. This does not
establish a more durable advance; all original winners remain winners.

At a fixed **T+15** decision, use only sector samples T…T+14. Within the 97 initial
qualifiers, majority pairing continues for 13, is lost for 72, and is unknown for 12.
The new movement score starts from the observed T+15 SPX open and runs only the remaining
forty-five minutes. It cannot be used at the original entry or repair an earlier outcome.

| Later context within initial paired yes | Parents / dates | New checkpoint targets | New checkpoint adverse | Neither |
|---|---:|---:|---:|---:|
| All initial qualifiers, same later benchmark | 97 / 37 | 54 = 55.7% | 13 = 13.4% | 30 |
| Confirmation continues | 13 / 9 | 9 = 69.2% | 3 = 23.1% | 1 |
| Confirmation lost | 72 / 35 | 39 = 54.2% | 8 = 11.1% | 25 |
| Lost pairing but later price breadth remains ≥6 | 24 / 15 | 13 = 54.2% | 2 = 8.3% | 9 |
| Later pairing unknown | 12 / 9 | 6 = 50.0% | 2 = 16.7% | 4 |

Continuation has more targets **and** adverse moves. Its +15.1-point target difference
versus lost confirmation has interval −16.7 to +38.4; within broad later price breadth,
−19.8 to +41.8. Fewer neither outcomes is the clearer descriptive separation. Requiring
continuation retains only 13.4% of initial qualifiers and 16.7% of their targets measured
from the common checkpoint, not original-entry targets. Ten of the thirteen already hit
the original target before confirmation; their median price was already +5.21 points.

Among parents above original entry at the checkpoint, future below-entry closes occur
in **5/12 = 41.7%** continuation survivors versus **22/40 = 55.0%** lost-confirmation
survivors. Difference −13.3 points, interval −44.7 to +22.7. The broad-later-price
comparator gives 9/15 = 60.0%, also inconclusive. This is a causal survivor subset; past
drawdowns and earlier target/adverse events remain separately recorded. Giveback is not
automatically failure of a previously completed option construction.

Support is thin and concentrated: seven of thirteen continuation signals occur on three
dates, and all nine continuation targets occur in January/February. Majority pairing can
rotate leaders: median intersection is four ETFs; only two continuation observations have
the same six or more qualifying in both windows. Saved surfaces stop at 14:29; eleven
of the twelve later-unknown cases within initial qualifiers have windows beyond that
coverage. No filling or new download. None of the 2,660 paired sector/window midpoint
declines excludes zero under its conservative bid/ask-derived change envelope; these are
measurement ranges, not confidence intervals or proof of no predictive information.

All fifty dates remain in 10,000 shared date draws, seed 20260917. Entry comparisons have
no undefined draws; later rate comparisons have two and survivor-giveback comparisons
four. No target/adverse/giveback interval excludes zero. Root, Brent and Quant preserve
this as an exploratory descriptor, without an entry veto, hold instruction, threshold
tuning or dashboard filter. Tests 3–5 in the six-test shortlist remain proposed.

[Full findings and figure](/Users/dgrissen/Dev/delta_bomb/outputs/b06_paired_price_iv_2026-09-17/FINDINGS.md).
[Independent persona decisions](/Users/dgrissen/Dev/delta_bomb/outputs/b06_paired_price_iv_2026-09-17/PERSONA_DECISIONS.md).
The isolated slug preserves protocol/code/input freezes, all sector and event measurements,
original and later outcomes, date/transition ledgers and independent numerical verification.


### 11.12 Recruitment versus loss of sector participation — completed

17 September 2026, first of three sequential follow-ups (older shortlist test 3).
Measure sector price-return signs in the two fifteen-sample halves of T−35…T−6, using
identical complete thirty-sample support and fixed denominator eleven. Bound net count
change by observed change ± missing sectors; keep improving/deteriorating/unchanged/unknown
separate. Save joining/leaving identities. Original 374 scores / fifty dates unchanged.

Improving: **118/190 = 62.1%** targets, **32/190 = 16.8%** adverse. Deteriorating:
**80/123 = 65.0%** targets, **14/123 = 11.4%** adverse. Primary target difference −2.9
points, paired-date 95% interval −14.8 to +10.3; adverse difference +5.5, interval −2.3
to +12.7. Improving-only retains 50.8% of signals and 49.4% of targets, excluding 121
targets without improving precision. There are 29 unchanged cases and 32 unknowns;
26 unchanged cases include offsetting joins/leaves. No inverse rule is established.

Within original static price breadth ≥6, targets are 84/132 = 63.6% improving versus
52/83 = 62.7% deteriorating; adverse remains higher for improving. Exact ending-count
standardization with complete eleven-sector coverage retains 132 improving and 89
deteriorating parents, excluding 27 other complete-coverage changing parents without
opposite-arm support. Weighted target rates are 62.6% versus 70.6%, but several strata
have only one to three observations on one side: **5,314/10,000 bootstrap draws are
undefined**, as is one date deletion. Conditional intervals cannot rescue sparse support.

Fixed fifteen-close winner giveback is 25/112 = 22.3% improving versus 18/72 = 25.0%
deteriorating and 49/222 = 22.1% overall. All ordinary contrast intervals include zero.
Brent and Quant advise no recruitment filter, inverted rule, regrouping or threshold
search. Participation signs do not establish option flow, gamma positioning or strong trends.

[Full findings, formulas, figure and ledgers](/Users/dgrissen/Dev/delta_bomb/outputs/b06_participation_change_2026-09-17/FINDINGS.md).


### 11.13 Original IV confirmation among matched price setups — completed

17 September 2026, second sequential follow-up (older shortlist test 4), begun only after
test 1 completed. Use the original ≥6-sector falling-and-accelerating ATM IV condition;
unknown remains separate. Require all eleven sector price series complete, exact same
full-window rising-sector count and signed median returns within a fixed ten-bps gap.
One-to-one matching maximizes count then minimizes distance, without reuse or outcomes.

**73 pairs / 146 parents remain.** Matched IV yes has **51/73 = 69.9%** targets versus
**42/73 = 57.5%** for definite IV no. Both have **12/73 = 16.4% adverse**; neither is
10 versus 19. Target difference **+12.3 points**, fixed-cohort paired-date 95% interval
**−3.5 to +27.4**. The association survives the two price controls, but adverse protection
does not appear. Fifteen-close winner giveback is 16/48 = 33.3% versus 12/38 = 31.6%,
also inconclusive. Original scores and labels are unchanged.

Matching is close: median return gap **0.58 bps**, maximum **3.92 bps**; count distributions
exactly equal. Return standardized imbalance improves from −0.302 to −0.011 using the
same prematch pooled SD. Of 374 parents, 97 lack complete price coverage; of the remaining
277, 41 have unknown IV. There are 236 eligible parents (76 yes, 160 no), 146 matched and
90 unmatched. The matched yes arm retains 73/93 original IV-yes parents and 51/67 of their
targets. Twenty unmatched IV-yes parents contain sixteen targets: exclusion here does not
justify avoiding them. Matching membership is a research sample, not an entry rule.

Only three pairs share a date; median entry clocks differ by thirty minutes. Time,
leadership, dispersion, SPX path, advance age and regime remain uncontrolled. All fifty
dates enter 10,000 shared draws, seed20260917, with fixed membership and arm-specific
denominators; no undefined draws. Intervals are conditional on the chosen matched cohort
and do not include matching-design uncertainty. Delete-date target differences stay
+10.1 to +16.1 points, but this is still
reused exploratory history. No independent dealer-flow or option-profit claim.

Brent and Quant retain a plausible progress-versus-stalling association, with no IV veto,
false-start guarantee or caliper retuning. [Full findings, pair ledger and figure](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_matched_price_2026-09-17/FINDINGS.md).


### 11.14 Acceleration beyond broadly falling IV — completed

17 September 2026, third sequential follow-up (older shortlist test 5), begun after test 2
completed. Preserve original sector validity, fixed eleven-sector denominator, half-window
OLS slopes and acceleration=(b2−b1)/15. Latest falling requires b2<−1e−12; original
confirmation adds acceleration<−1e−12 in at least six ETFs. It can include rising-to-falling
IV transitions. No new complete-eleven-sector restriction or quote-quality gate.

Within **217 broadly falling-IV parents**, the old 124 mixed nonselected observations
split into **86 definite acceleration nonqualifiers and 38 unknowns**. Acceleration yes:
**67/93 = 72.0%** targets, 13/93 = 14.0% adverse. Definite no: **53/86 = 61.6%** targets,
13/86 = 15.1% adverse. Unknown: 24/38 = 63.2% targets, 10/38 = 26.3% adverse. Unknowns stay separate.
Primary target difference +10.4 points, paired-date 95% interval −4.2 to +24.2; adverse
difference −1.1, interval −12.0 to +10.1. Versus all falling-only parents, target gain is
+5.7 points (−2.5 to +14.2), from 66.4% to 72.0%.

The requirement retains **93/217 = 42.9% of entries and 67/144 = 46.5% of targets**,
excluding 77 targets, 23 adverse and 24 neither. Median falling-sector count is eight for
acceleration yes versus six for no: this compares the added admission requirement but
does not isolate acceleration from the breadth or magnitude of IV decline.

Fifteen-close winner giveback is **18/64 = 28.1%** yes versus **7/45 = 15.6%** no;
difference +12.6 points, interval −0.9 to +25.6. Neither better persistence nor reliable
false-start protection is demonstrated. All eight planned intervals include zero; no
undefined draws among 10,000 shared draws of all fifty dates. Primary target difference
stays +8.1 to +12.5 under date deletion, but this remains reused exploratory history.

None of 1,604 qualifying sector/event acceleration signs clears its conservative quote
envelope. These are measurement ranges, not statistical confidence intervals. Preserve
the initial-progress hint; no hard gate, inverse rule, derivative tuning or option-profit
claim. Tests 2 and 3 use the same original IV rule and overlapping observations and are
not independent replications. [Full findings and figure](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_acceleration_increment_2026-09-17/FINDINGS.md).

### 11.15 — September 19: Brent side-agent framing of weighted constituent IV

Darrell revisited the top-five-holdings-per-sector idea. The requested canonical
Brent persona favors testing economic weighting at sector level first, then
considering constituent options. Keep price contribution, weighted participation
and opposing IV changes separate; a net weighted IV average can hide disagreement.
Use point-in-time SPX weights once, preserve uncovered index mass, and treat five
holdings per sector as exploratory coverage. The success criterion remains the
first +5 before −15 within one hour. This is an untested proposal refining
SECTOR-01/02/04, not a new filter or established improvement.

[Brent's reasoning and concrete readouts](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/BRENT_CONSTITUENT_IV_DIRECTION_2026-09-19.md).


### 11.16 — September 19: prior-day weighted sector IV — completed

Retrieved all fifty previous-session IVV holdings snapshots for free; normalized
its complete equity sleeve as an SPX sector-weight proxy. Compared the fixed
>50% weighted-majority rule with the existing six-of-eleven rule on the same
374 parents and unchanged +5-before−15 first-move score. No threshold search.
Missing IV remains unknown weight; historical source repairs are documented.

**Weighting did not improve accuracy.** Falling IV: equal 144/217 = 66.4%, weighted
155/239 = 64.9%. Acceleration: equal 67/93 = 72.0%, weighted 103/162 = 63.6%.
Plain B06 remains 239/374 = 63.9%. The weighted acceleration rule added 83 entries
with 47 targets (56.6%) while removing 14 with 11 targets (78.6%). It recovered
more opportunities but erased the original accuracy advantage.

Weighted-minus-equal differences: falling −1.5 points (shared-date descriptive
95% interval −5.2 to +2.2); acceleration −8.5 points (−16.9 to −0.1). Both remain
negative after deletion of any one date. This is reused exploratory history, not
an out-of-sample confirmation; weighting also changes selectivity. Prioritize the
equal-sector breadth hypothesis, with no weighted dashboard promotion.

[Full findings and reproducible ledgers](/Users/dgrissen/Dev/delta_bomb/outputs/b06_sector_weighted_iv_2026-09-19/FINDINGS.md).


### 11.17 — September 19: Brent / Charlie on IV acceleration magnitude — proposed

Both canonical personas independently favor per-ETF normalized magnitude before
combining sectors: M=−a/(1.4826×historical MAD), preserving actual falling-IV and
negative-acceleration signs. This zero-anchored score measures strength in units
of the ETF's own historical variability; it is not a centered z-score or a
statistical-significance measure. Keep six-of-eleven breadth and summarize median
M among qualifying sectors. Prior-date clock-hour baselines, minimum ten prior
dates; unknown scale/coverage stays unknown. Do not pool raw ETF scales, subtract
contemporaneous cross-sector common moves, or add cap weights.

Brent proposed a fixed M>=1 split; Charlie proposed a prior eligible-event median
split. CIO arbitration selected only the latter, frozen before each day without
outcomes, with the fixed-1 idea deferred. Compare first-move accuracy and retained
successful N on the identical warmup-eligible cohort. This remains a proposal:
no new performance result, acquisition or dashboard change. Standardization does
not resolve the existing quote-uncertainty and spot-repricing issues.

[Panel opinions, formula and next-test design](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/IV_ACCELERATION_MAGNITUDE_PANEL_2026-09-19.md).


### 11.18 — September 19: XLRE five-session magnitude circuit pilot — completed

Implemented the prior-session historical ruler for XLRE only on Aug4,5,6,7,10.
Each pilot uses60priorNYSEsessions, with one-hour bins anchored09:30 by the final
IV minute; thirty-minute acceleration and original surface construction unchanged.
65calendar sessions in union (May7–Aug10),162newSDKcalls,23legacylistings and
15legacysurfaces reused.19dates lack eligible tenor brackets; no fill or replacement.

560/1,355pilotwindows produced signed normalized scores;216also had IV falling
and accelerating downward. Per-block baseline coverage is9–31historicaldays; all
first-hour baselines have9 and stay unavailable under the fixed10dayfloor.
Zero qualifying negative accelerations clear the conservative quote envelope.
25baselines replayed with exact equal-day weights;183legacyXLREevents match;
560independentOLSchecks and13unit tests pass. These are overlapping measurement
windows, not B06 trade results. No broader sector run, outcome test, intensity
cutoff calibration or dashboard change.

[Results, five-session figure and ledgers](/Users/dgrissen/Dev/delta_bomb/outputs/xlre_iv_magnitude_5d_2026-09-19/FINDINGS.md).


### 11.19 — September 19: XLRE coverage diagnosis — completed

“Expiry and quote gaps” concealed two construction constraints. Of 19 excluded
dates, 14 had a 1–7 DTE front rejected by our eight-day floor; two had only a
0-DTE front and three had all future expiries beyond 30 days. All 162 SDK requests
succeeded. On 46 eligible days, zero provider bid IV alone blocked 5,533 of 6,085
rejected minutes (90.9%). The ATM definition requires both rights, bracketing
strikes, selected expiries and complete bid/mid/ask IV envelopes.

A diagnostic separating midpoint support from envelope validity supports
1,330 of 1,355 pilot thirty-minute windows versus 560 originally, with no fills or
shortened windows. This is potential support, not validated new scores. Original
first-block baselines had nine dates; all five current pilot mornings also lacked
a complete thirty-minute window, so lowering the ten-date history floor alone does not
fix them. Preserve the frozen pilot; next validate a separate midpoint/uncertainty
definition using cached data before expanding history or changing tenor policy.

[Detailed diagnosis and reproducible ledgers](/Users/dgrissen/Dev/delta_bomb/outputs/xlre_iv_magnitude_5d_2026-09-19/coverage_diagnosis/DIAGNOSIS.md).


### 11.20 — September 19: positive-midpoint recovery and nearby times

Darrell favors accepting positive midpoint IV when only bid IV is zero, keeping
positive and ordered dollar quotes and the other checks. This supports 1,330 of
1,355 pilot windows and 35–43 historical dates per block. Remaining pilot holes
are five opening snapshots and August 6, 09:37–09:50, where midpoint IV itself
fails at required strikes. A same-block ±2-minute lookup finds nearby support
for nine of those nineteen missing minute slots. The baseline already pools
all valid endpoints in each hour; nearby reuse must not duplicate observations
or add future data to an entry-time measurement. Expiry exclusions remain the
main whole-day gap. No new scores or dashboard rules were substituted.

[Recovery coverage and nearby-time evidence](/Users/dgrissen/Dev/delta_bomb/outputs/xlre_iv_magnitude_5d_2026-09-19/midpoint_recovery_followup/FINDINGS.md).


### 11.21 — September 19: prefer strict nearby observations before recovery

Darrell prefers strict same-minute IV, then a strict observation within ±2 minutes,
then original-minute midpoint recovery. Within the same session/hour block, this
supports 1,208 of 1,500 pilot minute slots before recovery (80.5%) and 1,482 after
(98.8%). Recovery use drops from 431 to 274 slots. Thirty-minute windows with every
slot supported rise from 560 strict exact to 700 with nearby strict observations,
then 1,331 with recovery. Sources after each window endpoint remain excluded.
First-block historical input support rises from nine dates to 13–14 before recovery
and 35–38 after it. Sources can be reused: supported pilot windows have median 28
distinct source minutes, so this is coverage only, not a recalculated acceleration
or historical scale. No fixed-grid filling, new scores or dashboard change.

[Nearby-first order, coverage and timestamp ledgers](/Users/dgrissen/Dev/delta_bomb/outputs/xlre_iv_magnitude_5d_2026-09-19/nearby_first_coverage/FINDINGS.md).


### 11.22 — September 19: nearby-first with three recovery guard buckets

Clarified that the previous 98.8% minute coverage excluded extra quote guards.
Replayed the committed guards at the final recovery step, preserving strict exact
then strict ±2-minute sources. Pilot minute/window coverage: base fallback
98.8%/98.2%; 100% guarded fallback 90.4%/73.0%; 50% guarded fallback 80.5%/51.7%.
Recovery adds 274, 148 and zero minute slots, respectively, beyond 1,208 strict
exact/nearby slots. First-hour historical input coverage is 35–38, 13–15 and
13–14 days. These guards apply only to fallback; this is distinct from the old
full guarded policies that guard every selected observation. No old hit rate
is assigned to these new combinations, and no acceleration score is recomputed.

[Three-bucket coverage, exact guards and policy-scope distinction](/Users/dgrissen/Dev/delta_bomb/outputs/xlre_iv_magnitude_5d_2026-09-19/nearby_first_guarded_coverage/FINDINGS.md).


### 11.23 — September 19: full nearby-first waterfall, ±2 versus ±3

Actually replayed ±3 with unchanged source masks, fallback guards, hourly boundaries
and per-window observation cutoffs. Strict pilot slot coverage rises 1,208→1,248;
base recovery stays 1,482/1,500. The 100% guarded-fallback total rises 1,356→1,379
(90.4%→91.9%); 50% rises 1,208→1,248 (80.5%→83.2%) and still accepts zero recovery
fallbacks. Supported thirty-minute windows: base unchanged at 1,331; 100% rises
989→1,008 (73.0%→74.4%); 50% rises 700→750 (51.7%→55.4%). First-block historical
support rises 13–15→15–17 dates for 100%, 13–14→15–16 for 50%. Source reuse is
explicit; base median distinct source minutes drops 28→27. No score or outcome
recalculation. All ±2 choices replay, and six radius tests pass.

[Full minute/window waterfalls and historical block coverage](/Users/dgrissen/Dev/delta_bomb/outputs/xlre_iv_magnitude_5d_2026-09-19/neighbor_radius_waterfall/FINDINGS.md).


### 11.24 — September 19: quant baseline trade-off recommendation

The canonical quant persona independently recommends strict exact → strict ±2
neighbor → 100% guarded recovery as the primary exploratory baseline policy.
The ±3 version adds only nineteen pilot windows; retain it as one calibration
sensitivity. The 50% version recovers no additional fallback observations, while
base recovery lacks the extra quote guards. Before any new normalization,
deduplicate source timestamps, assign observations to halves by actual time and
fit slopes against elapsed minutes; use the same estimator for current/history.
Recompute equal-date-weighted MAD on exactly sixty prior sessions. First-hour
13–15-date coverage remains sparse, and the ten-date floor is not a precision
guarantee. This is a recommendation, not an implemented or validated new baseline.

[Quant decision and necessary calculation changes](/Users/dgrissen/Dev/delta_bomb/outputs/xlre_iv_magnitude_5d_2026-09-19/neighbor_radius_waterfall/QUANT_BASELINE_RECOMMENDATION.md).


### 11.25 — September 19: balanced XLRE baseline implemented; full-date inventory

Darrell approved the quant's strict exact → strict ±2-minute neighbor → original-minute
100% guarded recovery policy. Implemented in a separate slug using cached native
quotes, deduplicating source timestamps and fitting slopes against actual elapsed
time in the original fifteen-minute halves. Recomputed equal-date-weighted MAD
from exactly sixty prior sessions. All 25 pilot date/hour baselines pass the
existing availability floor; 987/1,355 current windows score (72.8%), versus 560
originally. First-hour history now contributes 13–15 dates, but only 21/155 current
pilot first-block windows are measurable. Keeping sources inside the actual
thirty-minute window removes two windows from the earlier 989 coverage-only count.

The one ±3 sensitivity scores 1,005 windows; acceleration signs agree on 99.4% of
987 common scored endpoints. Keep ±2 as primary. This is implemented measurement
coverage, not evidence of improved B06 hit rate or validated magnitude thresholds.

Inventory through September 18: 429 completed 2025–2026 sessions plus sixty 2024
warmup sessions starting October 7, 2024. Of 489 dates, 145 have complete compatible
raw inputs, 39 have known missing expiry brackets, and 305 require collection.
At most 1,525 additional SDK calls before retries, roughly 30–48 minutes of serial
API time at observed recent speeds, plus setup/rebuilding/checks. A full-date
collection does not eliminate expiry/quote gaps. Scope remains 09:30–14:29 ET;
full RTH is extra, and 72 remaining 2026 sessions have not occurred yet. Broad
backfill has not been launched. All seventeen frozen original artifacts unchanged;
27 tests, ten guard checks, independent OLS replay and 650 prefix checks pass.

[Implemented baseline, five-session results and backfill estimate](/Users/dgrissen/Dev/delta_bomb/outputs/xlre_balanced_baseline_2026-09-19/FINDINGS.md).

### 11.26 — September 19: XLRE, XLF and XLU historical MAD calculations completed

Completed the same fixed measurement rules for all 429 sessions January 2, 2025–
September 18, 2026, with sixty preceding sessions starting October 7, 2024. These
are all-regime historical baselines, not an above-VT outcome sample. Native data
remain in central_trade_data. Scope is 09:30–14:29 ET, truncated to 12:59 on early
closes; future sessions and full-afternoon extension are outside this run.

Strict exact → strict ±2-minute neighbor → original-minute recovery with the
100% spread ceiling and quote guards remains unchanged. Every ETF has all 2,145
date/hour MAD baselines available under the existing ten-contributing-date floor.
Current thirty-minute windows additionally need usable current quotes: XLRE
70,498/115,989 (60.8%), XLF 115,535/115,989 (99.6%), XLU 112,462/115,989 (97.0%).
XLRE has 94 target dates without the permitted expiry bracket; XLF and XLU have
none. Current quote gaps remain explicit even when a historical baseline exists.

Saved weighted historical median, MAD, 1.4826×MAD scale, historical date/count
ledgers, first/second-half slopes, acceleration, signed magnitude −a/scale and
downward-only magnitude. Each ruler uses exactly sixty strictly prior calendar
sessions, equal total date weights and the same ETF/hour. The signed magnitude
is zero-centered acceleration scaling, not a conventional centered z-score or
a probability; downward-only also requires falling IV.

Independent verification caught cumulative floating-weight rounding at the exact
median boundary. All three ETFs were recalculated with exact integer date weights,
and an independent rational-CDF check verified every median and MAD. Largest scale
adjustments were 0.496% (XLRE), 0.627% (XLF), 0.472% (XLU). Authoritative outputs
are under calibration_exact/{ETF}; first-pass outputs are preserved. No source IV,
acceleration, coverage, policy or original five-day XLRE pilot score changed.
All 6,435 baselines, score arithmetic, independent OLS calculations and 46 tests
pass. This builds the measurement baseline; it does not test a magnitude threshold
or establish any improvement in B06 hit rate.

[Three-ETF results, coverage and calculation files](/Users/dgrissen/Dev/delta_bomb/outputs/sector_iv_mad_2025_2026_2026-09-19/FINDINGS.md).


### 11.27 — September 19: remaining-sector MAD continuation; provider outage checkpoint

Started the identical 429-target-session plus sixty-prior-session calculation for
XLC, XLY, XLP, XLE, XLV, XLI, XLB and XLK. XLC/XLY/XLP/XLE are complete and
independently verified, each with all 2,145 historical date/hour baselines.
Current-window score coverage is 112,407/115,989 (96.9%) for XLC,
115,759/115,989 (99.8%) for XLY, 114,729/115,989 (98.9%) for XLP, and
115,987/115,989 (>99.99%) for XLE. The previous XLRE/XLF/XLU remain unchanged.
Seven of eleven sectors therefore have full completed historical calculations.

Repeated native ThetaData HTTP 502 errors stopped the remaining downloads.
XLV has 345/489 dates assembled and processed from cache; XLI 160/489, XLB
184/489 and XLK 160/489. These four full historical calibrations are not complete.
The service-incident failures remain pending, not assumed absent historical data.
One earlier exhausted XLC September 18 request has an explicit unavailable ledger;
that last target date does not enter the earlier targets' historical baselines.

The ±2-minute/guarded-recovery and exact integer date-weighted MAD rules are unchanged.
All 8,580 completed baselines and 463,956 expected endpoint rows were independently
verified. Sixteen tests and 400 prior ETF-day strict-surface comparisons pass.
All native and derived data are retained centrally; the registry is reconciled
and checkpoint committed as `1a7271b`. No collector remains running. No B06 outcome
or magnitude-threshold test was performed.

[Results, checkpoint and resume procedure](/Users/dgrissen/Dev/delta_bomb/outputs/sector_iv_mad_remaining_2025_2026_2026-09-19/FINDINGS.md).


### 11.28 — September 19: full 2024–2026 price replay and the +5 / −10 barrier comparison

**Completed learning, rather than a new proposal.** The user requested the full
2024 extension, followed by rescoring the exact same entries for **+5 before −10
within 60 minutes**, instead of +5 before −15. These are price-only B01–B10
experiments. The sector-IV measurement work in the preceding sections supplies
no filter to these results. Earlier research nominations in this document remain
historical hypotheses; the completed observations below update their ranking.

#### What was held fixed, and what actually changed

The calendar audit covers all **681 completed NYSE sessions from January 2, 2024
through September 18, 2026**, including every 252-session 2024 date. There are
421 verifiable qualifying dates: 172 new 2024 dates plus 249 earlier dates.
The original ten dashboard-development dates remain separate, leaving **411
primary research dates**. Half-year research counts are **87 / 85 / 62 / 92 /
67 / 18**. The final half is partial; ten development dates are excluded from it.
Sixty-one research dates have no qualifying entry across the compared variants
and still remain in the date-resampling population.

“Above VT” means **every earlier observed RTH minute low from 09:30 and the entry
open are strictly above the same-date Vol Trigger**. A prior touch or breach
blocks subsequent entries. We do not use future entry-bar lows or future full-day
status to approve an entry. Date admission requires complete valid native prices
and same-date positive VT supported by matching preopen note labels. Missing,
conflicting or late evidence and early closes remain excluded; their exclusion
does not imply that every such date was below VT. Publication labels are evidence
of stated timing, not proof that the archived article was never revised.

The 2024 extension used 34 native one-minute ThetaData SDK requests. Thirty-three
responses normalized to complete sessions. May 30, 2024 contained 77 invalid OHLC
observations and was rejected; its old 313-minute source remains incomplete and
its observed open is below VT. No synthetic or repaired minute was admitted.
The requests restored chronological indicator history but added no evaluation
dates beyond the initial 172 qualifying 2024 dates. All **12,534 prior raw signal
records and 585 comparable earlier summary rows reproduced exactly**. The lower
pooled −15 percentages came from including 2024, not from changing old results.

For the −10 sensitivity, only the adverse barrier changes. Keep the exact entry
identities, dates, clocks, native observations, warmup and above-VT gates. Count
unique variant/date/entry-minute opportunities, preserving overlapping raw setup
records separately. The horizon includes the entry minute and ends with minute
+59. The original 1e-8 comparison tolerance remains. A first double touch in one
minute is ambiguous; no intraminute ordering is invented. Neither and ambiguous
remain in the denominator. **Anything after reaching +5 is irrelevant to a win.**

#### All thirteen results: the fixed population makes this a paired comparison

Cells are successful +5-first entries / all entries, with the corresponding rate.
Lost wins include any previous winner that becomes adverse-first or ambiguous.

| Variant | N | +5 before −15 | +5 before −10 | Lost wins |
| --- | --- | --- | --- | --- |
| B01 Fixed time | 1,569 | 844/1,569 · 53.8% | 813/1,569 · 51.8% | 31 |
| B02 Five-minute thrust | 92 | 61/92 · 66.3% | 59/92 · 64.1% | 2 |
| B03 Thrust + staircase | 317 | 184/317 · 58.0% | 180/317 · 56.8% | 4 |
| B04 T pullback/break | 1,330 | 688/1,330 · 51.7% | 664/1,330 · 49.9% | 24 |
| B05 Stall/reclaim | 2,790 | 1,527/2,790 · 54.7% | 1,477/2,790 · 52.9% | 50 |
| B06 Immediate breakout | 2,382 | 1,241/2,382 · 52.1% | 1,208/2,382 · 50.7% | 33 |
| B06 Breakout/retest | 563 | 302/563 · 53.6% | 292/563 · 51.9% | 10 |
| B07 Failed breakdown/reclaim | 769 | 403/769 · 52.4% | 393/769 · 51.1% | 10 |
| B08 Band rebound, price | 287 | 148/287 · 51.6% | 142/287 · 49.5% | 6 |
| B08 Band + RSI | 36 | 20/36 · 55.6% | 19/36 · 52.8% | 1 |
| B09 One-minute staircase | 5,560 | 2,973/5,560 · 53.5% | 2,890/5,560 · 52.0% | 83 |
| B10 Opening-range immediate | 260 | 153/260 · 58.8% | 145/260 · 55.8% | 8 |
| B10 Opening-range retest | 61 | 38/61 · 62.3% | 37/61 · 60.7% | 1 |

**Learning 1 — the extra five points of adverse room rescued relatively few
counted winners.** Hit rates fall by approximately 1.3–3.1 percentage points
across these variants. B06 loses 33 of its 1,241 previous winners, about 2.7%.
This answers the requested price question directly: most previous +5-first
winners did not need to survive a ten-point decline to succeed. It does not say
that allowing −15 was economically optimal, or that the tighter barrier increases
accuracy. On identical entries, tightening the adverse barrier cannot create wins.

**Learning 2 — a modest hit-rate decline can coexist with many more adverse-first
outcomes.** B06's complete transition accounting is:

| Original −15 outcome | New −10 outcome | Entries |
| --- | --- | --- |
| Target first | Target first | 1,208 |
| Target first | Adverse first | 33 |
| Adverse first | Adverse first | 242 |
| Neither | Adverse first | 209 |
| Neither | Neither | 689 |
| Ambiguous | Adverse first | 1 |

The new B06 distribution is **1,208 targets / 485 adverse / 689 neither / zero
ambiguous**, compared with **1,241 / 242 / 898 / one** before. All 33 lost B06
winners are definite −10-first observations. The additional 209 previous timeouts
were already nonwins under the user's objective, but now reach a defined adverse
barrier. Do not confuse “only 33 wins lost” with “only 33 additional stop outcomes.”
An adverse price touch here is an observed event, not a simulated option fill.

#### Which candidates retain support, and which interpretations weaken

**Learning 3 — thrust remains the strongest observed accuracy candidate, with
sparse evidence.** It gives 59/92 (64.1%) across 68 active dates. Its whole-date
95% rate interval is **54.7–73.2%**. It beats plain B06's observed percentage in
each of the six half-years under either barrier, but this is not proof that the
true advantage is positive or stable outside the researched sample. The 2026 H2
thrust cell drops from 5/5 to 4/5; a twenty-point percentage change represents
exactly one outcome. Keep the counts beside the percentages.

**Learning 4 — thrust plus staircase retains more observations and becomes the
higher-ranked of the two larger-sample candidates under −10.** B03 gives 180/317
(56.8%), versus opening-range immediate's 145/260 (55.8%). Their order was reversed
under −15: 58.0% versus 58.8%. B03 still exceeds all-entry B06 in all six halves.
B03 includes thrust entries; it is not a staircase-only result or independent
confirmation of the B02 result. B09 is the separate one-minute staircase transfer
hypothesis and gives 52.0% over 5,560 entries. It must not inherit B03's percentage.

**Learning 5 — opening-range immediate is more sensitive to the tighter barrier,
and retest's pooled percentage still hides weak older evidence.** Immediate loses
eight previous wins and 3.1 percentage points, the largest reduction among these
thirteen rows. It now trails B06 in 2024 H2: **47.2% versus 50.1%**. Retest keeps
37/61 (60.7%) overall but its 2024 halves are just **5/13 (38.5%) and 8/16 (50.0%)**.
Its small 2026 H1 result of 10/11 does not override those earlier observations.
Band rebound and RSI remain inconsistent; RSI has only 36 entries across the
whole research set and no 2026 H2 entries. T, stall/reclaim, failed breakdown,
one-minute staircase and B06 retest do not establish a stable major improvement.

#### Half-year check for the leading candidates under −10

Cells show +5-first rate (wins/N). The linked full findings retain all thirteen
variants, all outcome counts and all half-year changes; this compact table is
only the candidate comparison.

| Period | Thrust | Thrust + staircase | Opening-range immediate | Plain B06 |
| --- | --- | --- | --- | --- |
| 2024 H1 | 60.0% (9/15) | 56.9% (37/65) | 50.0% (29/58) | 46.8% (260/555) |
| 2024 H2 | 63.2% (12/19) | 58.7% (37/63) | 47.2% (25/53) | 50.1% (263/525) |
| 2025 H1 | 58.3% (14/24) | 54.1% (33/61) | 65.0% (26/40) | 52.2% (201/385) |
| 2025 H2 | 53.8% (7/13) | 49.2% (31/63) | 50.0% (28/56) | 46.3% (216/467) |
| 2026 H1 | 81.2% (13/16) | 61.5% (32/52) | 68.2% (30/44) | 57.2% (207/362) |
| 2026 H2, partial | 80.0% (4/5) | 76.9% (10/13) | 77.8% (7/9) | 69.3% (61/88) |

#### Repeated signals: a concrete reason the headline and spaced results differ

**Learning 6 — the two lost thrust winners are later repeated signals.** The
existing first-per-day thrust result is **48/68 (70.6%) under both barriers**.
The existing 60-minute-spacing result is **55/81 (67.9%) under both barriers**.
Their retained target counts do not change. The exact excluded repeats are:

| Date | Earlier strict-VT thrust | Later entry | Entry SPX | −10 first observed | +5 first observed under −15 |
| --- | --- | --- | --- | --- | --- |
| 2025-05-15 | 11:45 ET | 12:10 ET, 25 minutes later | 5,913.69 | 12:27 ET | 13:03 ET |
| 2026-08-07 | 10:20 ET | 10:30 ET, 10 minutes later | 7,755.11 | 10:36 ET | 11:25 ET |

Both earlier entries reached +5 first under both barriers. These examples explain
the arithmetic of the unchanged thrust sensitivities; they do not independently
prove that every repeated signal is bad. First-per-day and 60-minute spacing
were already defined before this sensitivity. Do not optimize a new time gap
from these two examples, or generalize their result to every entry family.

B06 first-per-day changes from **180/311 (57.9%) to 170/311 (54.7%)**; its
60-minute-spaced result changes from **419/810 (51.7%) to 404/810 (49.9%)**.
B03 first-per-day is **112/191 (58.6%)** under −10. Opening-range immediate already
has at most one entry per date and stays at **145/260 (55.8%)** under these
sensitivities. Thus filtering repeats does not universally improve results or
make the adverse barrier irrelevant. Spacing is based on entry clocks only,
not previous outcomes or an assumed time at which an option position closed.

#### Why this evidence differs from the early attractive headlines

**Learning 7 — market movement, calendar mix and repeated entries matter.** The
full 2024 extension reduced pooled hit rates before the adverse barrier changed.
The fixed +5 target was a larger move relative to early-2024 five-minute ATR:
median +5/ATR at B06 entry was **1.45 in 2024 H1 versus 0.88 in 2026 H1**.
In the original −15 comparison, early-2024 B06 had **252 neither outcomes versus
41 adverse-first outcomes among 555 entries**. Much of the lower hit percentage
there was failure to travel five points in time. This is descriptive evidence
consistent with smaller moves, not a causal decomposition or a newly tested ATR
filter. The target is deliberately still five points in every period.

The first-per-day comparisons also reduce the apparent advantage of candidate
families over all-entry B06. Different families enter at different times and on
different dates. A family-versus-family percentage difference is therefore not
the same evidence as the clean, identical-entry −15-versus−10 comparison. The
earlier-hour B01 matched-control differences are selected-path timing diagnostics:
later trigger formation selects information after the control entry. They must
not be presented as causal uplift.

#### What to carry forward without turning the results into a tuned strategy

For the stated **accuracy-first** objective, retain thrust as the leading
research candidate, explicitly showing its N and uncertainty. For the objective
of accuracy with more opportunities, retain thrust plus staircase and
opening-range immediate as separate candidates; −10 makes the former look
slightly stronger by pooled hit rate. Keep all-entry, first-per-day and fixed
60-minute-spacing versions visible. Retest's 60.7% headline is not sufficient
reason to elevate it above its weak 2024 replication.

Do not promote −10 as the optimal adverse barrier. This is one user-requested
sensitivity, not a search across barriers. Do not add retrospectively selected
ATR, calendar, sector-IV or repeat-count filters, claim a new untouched holdout,
or count posttarget reversals as failures. The score remains **did price reach
+5 first within the hour?** No actual option P&L or cost/benefit of an executable
stop was calculated. At most, the observations show that most old winners survive
the tighter price criterion and specify exactly which outcomes do not.

#### Verification and durable evidence

The −10 study preserves **21,239 raw identities and 20,821 distinct opportunities**;
the primary strict-VT research subset is **16,016 entries** across the thirteen
variants. All old −15 outcomes, first-touch minutes, entry prices and endpoint
changes reproduce. Both barriers were independently scanned across **17,351
native date/minute windows**. Every causal VT flag was rechecked; new targets are
a subset of previous targets. All **390 summary rows** preserve their original
denominators and −15 outcome counts. Twelve targeted scorer tests and Ruff pass.

Intervals resample whole qualifying dates **10,000 times, seed 20260919**, retaining
zero-event dates. Paired changes use matching resampled dates for both barriers.
This addresses within-date dependence but does not erase serial dependence,
regime changes, overlapping families or prior selection among many ideas. An
individual hit-rate interval is not a significance test for a between-family
advantage. The small recent half-year is not equivalent to a full six-month test.

- [2024 extension and all six half-years](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_2024_halfyear_2026-09-19/FINDINGS.md): project commit `815f1a2`, central registry `da23739`.
- [Complete −10 paired findings](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_stop10_2026-09-19/FINDINGS.md) and [frozen protocol](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_stop10_2026-09-19/PROTOCOL.md): project commit `935b5bb`, central registry `9dad4fe`.
- [Paired comparison rows](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_stop10_2026-09-19-v1/comparison.csv), [outcome transitions](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_stop10_2026-09-19-v1/outcome_transitions.csv), and [individual entries](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_stop10_2026-09-19-v1/distinct_event_outcomes.csv).
- [Native-score verification](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_stop10_2026-09-19-v1/score_verification.json), [summary verification](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_stop10_2026-09-19-v1/analysis_verification.json), and [data dictionary](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_stop10_2026-09-19-v1/DATA_DICTIONARY.md).

This learning-note update introduces no new data, fetch, signal, result or code
change. The original experiments, frozen manifests and prior notes remain intact.


### 11.30 — September 19: prior IV rules on the full 2024–2026 population, +5/−10

This completes the earlier IV-rule comparison, separately from MAD magnitude.
All 172 selected 2024 dates were checked across all eleven ETFs: 1,816 captured
sector-days, 76 with no allowed expiry bracket (XLRE43/XLB33), none pending.
Across 421 dates there are 4,488 captured sector-days and 143 expiry gaps. The
primary analysis uses 411 research dates; ten development dates stay separate.
All new native/derived data reside in
`/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_iv_full_2024_2026_2026-09-19-v1/`.
There were 5,293 new successful ThetaData SDK data calls; original exact-parameter
caches were reused and existing raw files preserved. Captured does not mean all
minute measurements pass quote quality.

**Learning 1 — the old B06 advantage did not generalize.** Under +5 before−10
within sixty native minutes, plain B06 is 1,208/2,382 (50.7%). Falling IV in six
sectors is 729/1,454 (50.1%); falling plus downward acceleration is 315/632 (49.8%).
Allowing midpoint recovery when bid IV fails gives 341/678 (50.3%). Balanced nearby
recovery gives 328/655 (50.1%). These reject many winners without supplying a
meaningful broad B06 advantage. Capitalization weighting and confirmation during
the breakout do not repair it. Post-target givebacks never affect this score.

The original IV measurements reproduce exactly across 45,760 sector/policy events,
with zero numerical differences. The expanded evidence, not a silently changed
version of those measurements, is driving the changed assessment. Even excluding
2024, original acceleration on the expanded 2025–2026 data is 187/349 (53.6%) versus
plain B06's 685/1,302 (52.6%). The early attractive percentages are not durable
estimates for the expanded population. A 2026 H1 benefit does not appear uniformly
in other halves. Different score barriers, cohorts and VT gates remain distinct.

**Learning 2 — B07 is the simpler transfer lead.** Failed breakdown/range reclaim
with original six-sector acceleration is 96/157 (61.1%), versus 393/769 (51.1%)
unfiltered,254/539 (47.1%) definite nonqualifiers and 350/696 (50.3%) measurable.
The qualifier has 121 distinct dates and a higher observed percentage in all six
halves. First/day is 72/121 (59.5%) versus 141/283 (49.8%); spaced 60 is 82/137 (59.9%)
versus 239/470 (50.9%). Its unadjusted whole-date difference interval versus all B07
is+3.4 to+16.7 percentage points. Midpoint recovery is 100/163 (61.3%).
Guarded 50 with majority prior-session IVV weight is 68/104 (65.4%), but has 363
unknowns and the additional historical-weight proxy limitation. No thrust+B07
union was predeclared, so none was constructed retrospectively for this report.

**Learning 3 — guarded eight-sector B09 is the strongest predeclared N lead.**
The one-minute staircase's guarded 100 acceleration-in-eight rule gives 69/105
(65.7%,69 dates); guarded 50 gives 44/66 (66.7%,39 dates). Adding these executions
to thrust gives 128/197 (65.0%) and 103/158 (65.2%), versus thrust 59/92 (64.1%).
The additions do not share thrust's date/minute identities: N rises 114.1% or 71.7%.
Simple midpoint recovery without these guards adds more B09 entries but dilutes
the combined percentage to 200/332 (60.2%). The quote policy is part of the observed
candidate, not a negligible data-cleaning implementation choice.

Guarded 50's first/day union is 68/97 (70.1%) versus thrust 48/68 (70.6%); its spaced
union is 87/124 (70.2%) versus 55/81 (67.9%). Guarded 100 supplies more N but has lower
first/spaced percentages than thrust. Neither tiny pooled-rate difference proves
an accuracy gain. Union 95% rate intervals are 57.7–71.8% and 57.2–72.5%; these are
not superiority/noninferiority tests versus thrust. Both settings were already
in the frozen registry; choosing between them now still incurs selection risk.
Half-year samples are uneven: guarded 50 adds 21/30 winners in 2024 H1 but 0/1 in 2026 H2.

**Learning 4 — opening-range confirmation is a secondary, smaller N lead.**
Thrust plus midpoint-recovered six-sector-acceleration B10 is 77/120 (64.2%), adding
18 winners/28 entries. Guarded 100 is 69/106 (65.1%), adding 10/14. The spectacular-looking
standalone B10 guarded 100 rate 13/17 (76.5%) is a seventeen-entry cell, not a reliable
champion. Original eight-sector or shape diagnostics do not rescue B06. All four
conservative bid/ask-envelope rules yield zero qualifiers; their NaN rate meansN=0
after evaluating a condition, not an unfinished download.

**Learning 5 — comparable-price matching leaves a narrow falling-IV hint.**
Within-half original falling-IV matches give 223/421 (53.0%) versus 194/421 (46.1%);
global matches give 208/432 (48.1%) versus 201/432 (46.5%). Acceleration within-half
is 252/497 (50.7%) versus 247/497 (49.7%). Matching fixes rising-sector count and
uses a 10 bps median-return caliper without replacement, before outcomes are joined.
The effect's dependence on the matched subset matters; it has not yielded a broad
operational B06 improvement. The same-sector price/IV rule is 409/801 (51.1%) in
the full B06 pool. T+15 confirmation is a genuinely new entry with fresh VT and
sixty-minute scoring:83/156 (53.2%) versus all delayed B06 1,201/2,381 (50.4%).

**Learning 6 — unknown is informative and has multiple causes.** There are 741
primary recipe entries before 10:05 whose reference starts before 09:30. This is a
structural window issue, distinct from quotes or expiry brackets. The additive
coverage audit separates it from remaining unresolved quote/expiry conditions and
rejected issuer snapshots. Unknown groups retain their own outcomes. B09 guarded 50
has 1,479/2,736 (54.1%) unknown winners; B06 original acceleration unknowns are
203/365 (55.6%). Missing values are not failures or free opportunities to discard.
All eleven sectors remain in the voting denominator. Fifty reused validated issuer
bodies lack recorded HTTP status and are labeled that way, rather than claiming
historical HTTP200 evidence that was never captured.

**Verification and interpretation.** The score, native price inputs, entry recipes
and strict through-entry VT gate are unchanged. No future session-low gate is used.
There are 105 registry rules (104 at original entry and one delayed),13 families,
six halves, all/first/spaced modes, and 88 predeclared opportunity unions. All 97,656
comparison rows,1,848 union rows,312 original baseline rows and 4,056 additional
unknown-state disclosure rows reconcile. Independent feature checks cover five
policies/four descriptors and 68,000 scalar comparisons, maxerror 5.44 e−15.
Whole-date bootstrap uses 5,000 draws/seed 20260919, retains zero-event dates and
does not adjust for the many hypotheses. This is expanded descriptive research,
not an untouched holdout. Higher observed rates remain research leads.

Requested Claude Opus 5/xhigh review: **CONDITIONAL PASS** over 16 implementation
files. Medium concerns about structural/informative missingness and zero-qualifier
cells are disclosed; the metadata registration writer was replaced with a tested
durable roll-forward writer that writes its completion inventory last. Canonical
pair IDs, issuer HTTP provenance and actual prior-date checks are recorded. No
numeric result or signal threshold changed after that review. Local validation:
23 tests and Ruff; the verdict remains conditional rather than being relabeledPASS.

- [Extensive findings, all important tradeoffs and evidence links](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/FINDINGS.md).
- [Complete result tables and missingness disclosures](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/RESULT_TABLES.md).
- [Inventory of tested and explicitly untested ideas](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/IDEA_INVENTORY.md).
- [Independent review and dispositions](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/REVIEW_RESOLUTION.md).

MAD magnitude, short-tenor/term-structure, monthly-only expiry and individual
constituent surface strategies were not tested in this comparison. The older
datasets and interactive dashboard remain untouched by this isolated run.


### 11.31 — September 20: B09 sector MAD grid, both direction definitions

**Completed result, not a new validated strategy.** The user froze a 4×6 grid:
scaled-MAD cutoffs 1, 2, 3, 4 exceeded in at least 4–9 of the eleven sector ETFs.
They then explicitly requested both downward acceleration alone and downward
acceleration while IV is already falling: 48 cells. No lower cutoffs, smaller
breadth, new entry recipes or post-target penalties were added after outcomes.

**Population and comparability.** Existing exact MAD coverage supports January 2,
2025–September 18, 2026, with sixty prior-session warmup. It does not supply a
full-2024 MAD outcome test. The parent is 3,141 B09 signals on 178 active dates
within 239 selected research dates; ten development dates remain excluded. Plain
B09 scores 1,704/3,141 = 54.25%. Do not compare new filtered percentages against
the 2,890/5,560 = 51.98% baseline from the larger 2024–2026 population.

Every entry retains the strict causal above-VT rule: all earlier same-session
native minute lows and the entry open exceed same-date VT. Future session prices
do not determine eligibility. Success remains +5 before −10 within sixty native
minute bars including entry; neither and ambiguous outcomes stay in the denominator.
A later giveback after +5 does not undo a win. No option-profitability inference.

**Exact IV definition.** At entry T, read the existing window ending T−1, covering
T−30…T−1. This explicitly differs from the older B06 reference ending T−6. Fit
the inherited actual-time IV slopes b1/b2 within the two fifteen-minute halves;
a=(b2−b1)/15. M=−a/(1.4826×historical MAD). The historical ruler uses sixty
strictly prior sessions, the same ETF/hour block, both acceleration signs, all
regimes and equal total weight per date. This is zero-centered scaled magnitude,
not a median-centered z-score, percentile, probability or quote-resolved signal.

The signed rule requires M>k. The falling rule also requires b2<−1e−12 in the
same qualifying ETF. Thus IV rising more slowly can qualify for signed, while
the falling rule demands an actual downward trend in the latest fifteen minutes.
It does not demand that every individual minute decline. A sector must meet both
conditions itself; votes from different sectors cannot satisfy separate legs.
The cutoff is strictly exceeded; the sector-count condition is inclusive.

**Learning 1 — four sectors at M>1 is the useful N region in the requested grid.**

| Rule | Winners / N | Hit rate | Active dates | Entry retention |
|---|---:|---:|---:|---:|
| Plain B09 | 1,704 / 3,141 | 54.25% | 178 | 100% |
| M>1, ≥4, acceleration alone | 139 / 235 | 59.15% | 100 | 7.5% |
| M>1, ≥4, IV also falling | 115 / 188 | 61.17% | 95 | 6.0% |
| M>1, ≥5, acceleration alone | 53 / 80 | 66.25% | 54 | 2.5% |
| M>1, ≥5, IV also falling | 43 / 64 | 67.19% | 45 | 2.0% |

The predeclared high-N selection first required observed uplift versus plain B09
in each completed half, then ranked retained completed-half N. Signed 1/four
wins that ordering, with 225 completed-half signals. Falling 1/four is a separate
accuracy/N compromise with 181. This ranking is not a significance test or evidence
that 1/four is the globally optimal rule. Both discard most parent opportunities.

At 1/four, relaxing the falling requirement adds 47 signals and 24 winners (51.06%).
Forty are definite falling-rule nonqualifiers, 20/40; seven have an unknown falling
classification, 4/7. Do not relabel all 47 as definitely rising-IV events. Falling
1/four retains only 115 of the parent's 1,704 winners; 1,589 successes are excluded.

**Learning 2 — improvement repeats across completed halves, not every observed period.**

| Rule | 2025 H1 | 2025 H2 | 2026 H1 | Partial 2026 H2 |
|---|---:|---:|---:|---:|
| Plain B09 | 496/897 = 55.30% | 587/1,215 = 48.31% | 514/858 = 59.91% | 107/171 = 62.57% |
| Signed 1/four | 45/78 = 57.69% | 51/89 = 57.30% | 38/58 = 65.52% | 5/10 = 50.00% |
| Falling 1/four | 37/61 = 60.66% | 39/69 = 56.52% | 35/51 = 68.63% | 4/7 = 57.14% |
| Signed 1/five | 18/31 = 58.06% | 18/28 = 64.29% | 15/19 = 78.95% | 2/2 = 100% |
| Falling 1/five | 16/25 = 64.00% | 15/23 = 65.22% | 11/15 = 73.33% | 1/1 = 100% |

Only the three completed halves drive stability ranking. The partial half stops
September 18 and is not an untouched holdout. Its four-sector results are worse
than its plain parent; its five-sector 100% observations contain only one/two
signals. Neither sparse observation establishes success or failure by itself.

**Learning 3 — the four-sector advantage is not solely repeated neighboring signals.**
First qualifying signal/day and greedy sixty-minute spacing are timestamp-only,
reset daily, and occur after applying each filter. Compare like execution policies:

| Rule | First/day | Sixty-minute spacing |
|---|---:|---:|
| Plain B09 | 97/178 = 54.49% | 285/554 = 51.44% |
| Signed 1/four | 60/100 = 60.00% | 84/142 = 59.15% |
| Falling 1/four | 61/95 = 64.21% | 76/121 = 62.81% |
| Signed 1/five | 34/54 = 62.96% | 40/60 = 66.67% |
| Falling 1/five | 28/45 = 62.22% | 33/50 = 66.00% |

Both four-sector rules retain positive observed uplift in each completed half
under all three execution policies. Signed 1/five fails that test in first/day
2025 H1. Filtered first/day events may occur later than plain first/day events;
these are different executable policies, not paired identical-entry causal effects.

**Learning 4 — stronger magnitude or breadth mostly destroys N.** Across cutoffs
2–4, the largest pooled N is 26. At cutoff one, requiring six sectors leaves only
25 signed or 22 falling entries; seven–nine sectors are sparser. The four favorable
raw cells are adjacent at the least restrictive boundaries. There is no broad
robust plateau, and no authorized sub-one/fewer-than-four sweep was performed.

**Learning 5 — unknown coverage is not evidence against an entry.** The eleven
ETFs stay fixed, including XLRE. Qualify when enough observed sectors pass; reject
only when passing plus unknown sectors cannot reach the required count; otherwise
unknown. No forward fill, denominator reduction or missing-as-negative vote.
Signed 1/four has 212 unknown entries, 130 winners (61.32%); falling 1/four has
183, 111 winners (60.66%). Their measurable parent rates are 53.74% and 53.85%.
Missing-sector exclusions are an opportunity cost and cannot be used to claim
the excluded group consists of failures. Scores were usable in all eleven ETFs
at 1,788 entries; remaining entries had six–ten available sectors. No new fetch.

**Learning 6 — the apparent uplift remains uncertain after search.** Five thousand
whole-date draws include zero-event dates and use shared draws for each parent
comparison. Signed 1/four pooled uplift interval is −1.55 to +11.35 percentage
points; falling 1/four is +0.01 to +13.63. These are unadjusted for the 48-cell
search, earlier research and serial dependence. A lower endpoint of +0.01 is not
decisive evidence. Three completed half-years cannot establish regime invariance.

For context, the older guarded-100 eight-sector B09 acceleration rule has 35/54
=64.81% over the SAME 2025–2026 dates. Falling MAD 1/four offers 188 versus 54
signals (3.5×), at 61.17% versus 64.81%. The new calculation changes timing,
normalization, breadth and measurement policy; its differences cannot be credited
to MAD alone. The old 69/105 headline includes 2024 and is not the correct comparator.

**Verification and review.** All 66 source-file hashes and the original price-score
hash verified. Memberships were frozen without outcome columns. Ten tests and
Ruff pass; a separate local scalar implementation replays 150,768 classifications,
all 3,474 summary rows and twelve inherited half-year/execution baselines. Threshold,
breadth and falling-subset nesting hold. These checks were performed by the same
assistant. Independent Claude code review remains NOT RUN under the side-thread
prohibition on separate reviewers; no PASS or conditional sign-off is implied.

The next work is a proposal only: transfer fixed candidate RULES to all eligible
events of a small, declared price-parent set; never select historical winning
events for the test. Index-IV normalization remains untested. Preserve every
cell and tradeoff instead of retrospectively selecting a single winner as proven.

- [Full findings](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_grid_2026-09-19/FINDINGS.md).
- [All 48 half-year cells](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_grid_2026-09-19/ALL_48_RESULTS.md).
- [Frozen protocol](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_grid_2026-09-19/PROTOCOL.md).
- Central evidence: `/Users/dgrissen/Dev/central_trade_data/thetadata/b09_mad_grid_2026-09-19-v1/`.


### 11.32 — September 20: independent Claude strategy review executed and recorded

The saved review request was not an actual queued job: the original side
conversation had prohibited separate reviewers. The user explicitly requested
execution in the main task. Claude Opus 5 / xhigh, tools enabled, completed the
first independent strategy review in 451 seconds: **FAIL, twelve findings**.
After an evidence-based author revision, a focused recheck completed in 523
seconds: **CONDITIONAL PASS, seven findings**, suitable for exploratory research
with conditions. The original proposal, the reviewed revision and both full
outputs are preserved. Final author amendments after the recheck have not had a
third review. This is not unconditional approval or proof of an edge.

**Learning 1 — preserve the user's actual objective.** The first reviewer proposed
a linear +5/−10 payoff calculation. That is not the user's first-movement question
or the actual option payoff. Reject that objective substitution. Retain target,
adverse, neither and ambiguous counts: S4 is 139/61/35/0 among 235; plain B09 is
1704/685/751/1 among 3141. Higher target share (59.1% versus 54.3%) accompanies
higher adverse share (26.0% versus 21.8%) and fewer timeouts. It is an observed
first-target improvement, not evidence of safer trades or option profitability.
The recheck accepted this distinction.

**Learning 2 — disclose prior searching and uncertainty.** The prior broad IV
comparison already contains 105 distinct labels including baseline, across 13
parents and three policies. B05 and B07 are not fresh unseen parent selections.
S4's unadjusted uplift intervals cross zero under all entries, first/day and
60-minute spacing. F4's all-entry lower bound is only +0.013 percentage points.
Repeated half-year positivity is descriptive, not a calibrated validation rule.
The recheck reproduced all amended counts and intervals from primary artifacts.

**Learning 3 — simple sign controls do not isolate normalization.** The recheck
calculated the two proposed B09 sign-control outcomes despite the explicit
instruction not to run new strategy tests: 2,544 qualifiers at 54.17% for a<0 in
at least four sectors, and 1,933 at 54.11% when those sectors also have falling IV.
These are reviewer-reported replays from frozen event files and are now inspected
research. They cannot later be called untouched prospective controls. Their
much broader participation than S4/F4 means the comparison mixes magnitude and
selectivity. It describes the fixed rules' tradeoff; it does not isolate MAD
normalization from raw acceleration. A matched raw-magnitude control would need
its own frozen design before claiming that attribution. No new threshold sweep
was added to this round.

**Learning 4 — coverage can imitate period differences.** Require per-half/hour
valid-sector counts and yes/no/unknown rates, plus exactly one all-eleven-observed
sensitivity with the same rules and restricted parent. Keep its lost N/dates
visible. Do not search alternative ETF subsets. Unknown is not a failed signal
or an observed near miss. The review suggests fixing coverage, but existing XLRE
completion evidence already records 94 missing-bracket target dates, zero XLRE
provider-history failures and additional rejected quote windows. Reconcile the
causes at affected entries; refetching cannot create an eligible expiry. Any
quality/tenor change needs a new version and symmetric replay.

**Learning 5 — transfer does not guarantee more N or new evidence.** Keep B07 as
the failed-breakdown/reclaim hypothesis and B05 as a skeptical stalled-pullback
transfer. B05 has more parent events than B07/B03, but fewer than B09, and prior
analogue retention does not support expecting it to beat B09's filtered N. Remove
the high-N-challenger label. Report pooled date-based uncertainty first, then
half-year patterns; explicitly allow underpowered/uninformative conclusions.
Add the fixed diagnostic split for date/hour blocks with versus without a
qualifying B09 entry. Shared IV windows limit independent evidence; the
nonoverlapping subset still uses already examined dates.

**Learning 6 — keep the index question bounded.** The planned SPX rule remains
M>1 with recent IV slope negative, compared with sector F4 on the same B09 entries,
with all unknown combinations separate. Report SPX participation before outcomes.
A per-ETF participation proxy is not observed SPX participation and does not
predict how many unique OR additions will survive overlap. Retain one fixed rule;
do not silently add participation matching or a threshold grid. Conclusions would
concern that rule's usefulness, not isolated information-source superiority.

The final comparison budget is four primary transfer cells and six sign controls:
two B09 controls already inspected during review and eight unrun comparisons.
The SPX disagreement test is separately declared. No B07/B05 transfer, coverage
sensitivity or SPX outcome test ran in this review task. The user-authorized SPX
measurement history from 2024 is being built separately; it does not extend
sector MAD history to 2024 or constitute a trading test.

- [Original independent review](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_followup_plan_2026-09-20/CLAUDE_STRATEGY_REVIEW.md).
- [Independent recheck](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_followup_plan_2026-09-20/CLAUDE_STRATEGY_RECHECK.md).
- [Author response and scope disclosure](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_followup_plan_2026-09-20/REVIEW_RESPONSE.md).
- [Final bounded proposal](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_followup_plan_2026-09-20/CHARLIE_PROPOSAL.md).

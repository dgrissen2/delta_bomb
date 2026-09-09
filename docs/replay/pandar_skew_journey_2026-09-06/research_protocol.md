# Pandar call-skew journey: frozen research protocol

Frozen September 6, 2026 before viewing this experiment's outcomes. These are project
hypotheses informed by canonical Charlie/Brent persona simulations, not their actual
recommendations or Pandar prescriptions. No strategy deployment or trade is requested.

## Scope and time

Use the September 3 HIRO membership snapshot backwards: 398 instruments, with 323
classified as stocks by the existing scanner. SPY supplies the actual session calendar.
This is a current-universe retrospective study, not point-in-time historical membership;
survivorship and stale/renamed symbols remain limitations. Retain a coverage row for every
requested stock. Collect 2023-01-01 through 2026-09-03; evaluate 2024-01-02 onward.
No current option-volume/OI filters are imposed on historical dates. The daily sample
requires positive valid surface IV, summary confidence >=50 and prior/current trailing
20-session adjusted-price-times-adjusted-volume average >=$20m. This is a dollar-turnover
proxy; it does not establish historical option execution liquidity.

Features use observations through signal EOD t. Entry reference is next-session EOD t+1.
Measure 1, 2 (primary), and 3 holding sessions after that reference. This deliberate lag
avoids treating an EOD-derived signal as executable at that same EOD. All reference
prices/IVs are snapshots, not option fills. Report 2024–2025 and 2026 separately, calling
2026 a later chronological slice rather than a pristine unseen holdout.

## Features fixed before outcomes

- Front-tail wing W = 100 × (10-calendar-day 5-call-delta IV − ATM IV10), in vol points.
  Also retain the separate 30-day 25-call-delta ex-earnings skew and its rank.
- R = percentile of W against the prior 252 market sessions, at least 126 valid prior
  observations; strictly below, excluding the current observation. Baseline high R>=85.
- A high-wing episode begins at a crossing into R>=85 and ends at the first lower rank.
  Missing observations interrupt it and flag the following episode as left-censored.
  Record consecutive age, cumulative (R−85)/15, peak W known so far, distance below that
  peak in vol points, and the first below-threshold observation with the prior age.
  Descriptive age bins: 1–2, 3–5, and 6+ sessions. No thresholds are fitted to outcomes.
- Expanding: W rises on each of the last two completed sessions. Rolling over: W falls
  on each. Temporal acceleration aW = W[t]−2W[t−1]+W[t−2]. This is not option gamma.
- Price deceleration aS = r[t]−r[t−1], r=log(adjusted close[t]/close[t−1]). Charlie
  exhaustion: preceding three sessions had positive cumulative return, aS<0 and
  IV10[t]−IV10[t−1]<0. Add aIV<0 as a separately reported acceleration sensitivity.
- RV30/RV60: annualized sqrt(252 × mean of squared daily log returns in the trailing
  30/60 **calendar-day** window). Require complete observed returns over that window
  on the SPY calendar. These are zero-drift trailing estimates, not forward forecasts.
- Annual variance premia P30=IV30²−RV30² and P60=IV60²−RV60², using decimals.
  Test both >0. Raw IV is compared with raw realized variance. Ex-earnings IV and
  IV10−exErnIV10 are separate context; without matched ex-earnings realized returns,
  do not label the premia pure diffusion or event-free. A <=2-vol-point modeled front
  earnings premium is a separate descriptive slice, not proof of no upcoming event.
- Retain ORATS rDrv30 (cross-strike curvature) separately from temporal aW/aIV.
  It is neither dealer gamma nor a direct measure of future price acceleration.

## Fixed comparisons

Include all eligible dates as a reference and high-rank days as the baseline. Compare
high-rank age bins, expanding versus rolling-over wings, mature (age>=3) rollover,
both positive variance premia, Charlie exhaustion, and mature rollover with premia
and exhaustion. Keep aIV<0 as one named sensitivity. Include first episode exits.
No grid search, optimized weights, or selection based on the best observed result.
For variance-feature comparisons, repeat the baseline on identical available coverage.
Show all signal dates and a per-rule nonoverlap sensitivity: greedily admit the earliest
eligible signal per ticker, then no new position until its t+4 exit has passed. Different
rules can enter at different dates; comparisons are observational, not causal effects.

Primary outcomes: spot down AND IV10 down after the two-session holding interval.
Report spot return, ATM IV10/IV30 change, W change, spot-down rate, IV-down rate,
wing-compression rate and downside/IV-up rate separately. Missing entry/exit or interim
stock/surface observations censor the relevant joint outcome, never count as failures
or zero returns. Calendar-month block bootstrap intervals show sampling uncertainty;
multiple exploratory comparisons and current-universe bias limit inference.

## Contract and HIRO bridge

Attach these prior-only features to all 73 recent selected calls, including rejects from
the stricter project surface. Retain call delta, % OTM, DTE and log(K/S)/(ATM_IV sqrt(T));
S is a spot approximation because a matched forward is unavailable. Do not infer strike
or strike-touch probability from delta. Normalize distance using ATM, not the rich tail's
own IV. Review bid-tail excess, deferred comparable-delta IV and matched-history z separately.

The long-history test studies stock/surface outcomes at fixed delta/tenor; it does not
backtest exact-contract delta/OTM placement, option P&L or delayed conversion. The existing
HIRO capture coverage remains separately labelled: a member of the ticker set does not
imply historical intraday HIRO exists. Exact option quotes, event calendars and available
historical gamma terrain are needed for those further execution tests. Keep short-call
premium contraction, ATM-IV decline, call-wing compression, and buying the nearer long
as distinct outcomes. A price decline can coincide with rising IV and put demand.

## Brent's pre-outcome refinements

Add W>0 as its own high-rank comparison: a high percentile can describe a still-negative
wing. Report signal-to-entry return and IV movement separately from post-entry outcomes.
For journey/variance/exhaustion comparisons, form a descriptive comparison to other
high-rank dates within fixed calendar-quarter, rank (85–90/90–95/95–100), absolute-wing
(<=0/0–5/5–15/>15 points), ATM-IV10 (<=30%/30–60%/>60%), and modeled event-premium
(<=2/>2 points) cells. Require at least five valid control outcomes per cell. Show
common-support sample size and the weighted treated-minus-control joint-outcome rate.
This controls some starting-state differences, not all selection bias or causal effects.
The monthly bootstrap resamples whole cross-sectional panel months together. Nonoverlap
uses the maximum holding horizon, regardless of which outcome later looks favorable.

Age-based comparisons exclude left-censored episode starts (first valid high reading
after missing history), because their observed age is only a lower bound. Those rows
remain in the broad baseline and a separately labelled unknown-age group.

## Descriptive bridge addition after primary results

The 73-contract bridge also records the number of high-rank days in the preceding/current
20-session window and distance below its raw-wing peak, to expose cases where a brief
threshold dip resets the strict streak. These additions are descriptive; no new arm or
outcome-optimized gate is tested. They do not alter the frozen ablation results.

## Brent Kochuba

1. **Put-flow absorption at gamma landmarks.** Near Vol Trigger or Put Wall, detect extreme negative put-line flow while SPX stops making lows: 5-minute put flow ≤ expanding minute-of-day 10th percentile, but SPX drawdown per $1B falls below its prior-30-minute median. Enter **sell-first** when SPX reclaims the shock bar’s midpoint and put flow gives back ≥25%. Thesis: forced hedging hit inventory support and is exhausted; worst case is support failure.

2. **Dealer vacuum after a failed downside auction.** Require a new 30-minute low, ≥3-point decline, then both call and put 3-minute flows inside their minute-of-day ±25th-percentile “flat” bands. If SPX cannot extend lower for three bars, sell-first above the highest vacuum-bar close. This tests whether cessation of forced flow—not opposite flow—creates the tradable bounce.

3. **Elasticity collapse and snapback.** During a negative 15-minute HIRO shock, calculate marginal response for each minute: SPX return / HIRO increment. Identify three consecutive negative-flow bars whose price response falls ≥60% versus the episode’s first three bars, followed by positive flow acceleration. Sell-first on the first higher high. Separate put exhaustion from call buying; fail immediately if the low breaks.

## Charlie McElligott

1. **Retail chase versus basket refusal.** Standardize retail and all-scope rolling flow separately by minute of day. Find retail flow at an extreme in the direction of the latest price move while all-scope flow diverges by ≥1.5 z-scores and price stalls. Fade retail: sell-first after downside retail capitulation; long-first after upside retail chase. “Price is news”: the important observation is that price stopped confirming the loud cohort.

2. **Spot-up, demand-up analogue.** Test upside bars where call and put HIRO lines both accelerate positively, nextExp share rises, and SPX is above Vol Trigger. Rather than fade “late” flow, enter **long-first** only after a 2–4-point bounce from a 30-minute low, then a negative price bar despite still-positive flow. Hypothesis: options demand is tightening into strength, producing unstable spot-up/convexity-up behavior and a downside air pocket. Follow-up must verify actual SPX IV rose.

3. **Systematic de-gross bounce failure.** On negative-gamma days, require a ≥75th-percentile prior-60-minute realized range, negative 30-minute basket flow, and a 3–7-point bounce accompanied by call-flow recovery but continued put-flow deterioration. Long-first when the bounce loses its midpoint. This targets CTA/vol-control-style selling resuming after dealer-supported relief.

## Joint shortlist

1. **Put absorption at Vol Trigger/Put Wall**

   - **Hypothesis:** extreme put-driven pressure that loses price impact near a gamma landmark precedes a 3–7-point rebound.
   - **Features:** distance to level; 5-minute put flow percentile; price/$B elasticity; new-low failure; put giveback.
   - **Entry/exit:** sell-first on shock-midpoint reclaim; fill at +3/+5/+7; scratch if flow remains shut off but price stalls, stop on low break, 15-minute timeout.
   - **Metrics:** target-fill rate, time-to-fill, MAE, worst trade, credit obtainable in SPX quotes.
   - **Control:** clock-, level-distance-, and pullback-matched negative-flow episodes.
   - **Pass:** ≥15 episodes, +12 percentage-point 3-point fills, median MAE no worse, and positive leave-one-day-out result.

2. **Systematic de-gross bounce failure**

   - **Hypothesis:** high-range, negative-gamma sessions produce failed bounces when call relief masks persistent put pressure.
   - **Features:** SG regime, SPX versus VT, 60-minute range percentile, bounce size, 30-minute flow, call/put divergence.
   - **Entry/exit:** long-first on loss of bounce midpoint; targets −3/−5/−7; stop above bounce high; 15-minute timeout.
   - **Metrics/control:** mirror metrics versus matched bounces on down days.
   - **Pass:** ≥60% 3-point fills and ≥15pp over controls, profitable on at least four distinct sessions.

3. **Retail capitulation divergence**

   - **Hypothesis:** retail extremes are fadeable only when basket flow and price refuse confirmation.
   - **Features:** retail/all z-score spread, price extension, three-bar non-confirmation, nextExp share.
   - **Entry/exit:** fade on local-extreme break; 3/5/7-point targets; extreme-break stop.
   - **Control:** equally extreme retail episodes without divergence.
   - **Pass:** ≥10pp target lift with lower tail no worse than control.

4. **Post-shock dealer vacuum**

   - **Hypothesis:** a failed auction followed by two-sided flow silence creates a brief pin/rebound window.
   - **Features:** shock percentile, new low, call/put flatness, three-bar extension failure.
   - **Entry/exit:** sell-first above vacuum range; target +3/+5; stop below range; 10-minute timeout.
   - **Control:** matched shocks where either flow line remains active.
   - **Pass:** ≥70% +3 fills, median completion ≤6 minutes, worst MAE < target width.

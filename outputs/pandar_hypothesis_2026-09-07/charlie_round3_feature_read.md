# Charlie — Round 3 feature read, before trade outcomes

The current feature set mainly describes young, elevated call wings. It does not yet describe a broad exhaustion sample. Across the 50 frozen episodes, 35 are age one or two, nine are age three to five, and six are age six or older. Thirteen wings are expanding, only one has two completed sessions of contraction, and 36 satisfy neither condition. The lone rollover is CPNG, age four. The six stocks with measured variant-strike richness contain **no rollover observations**. Their subsequent trade results therefore cannot supply the missing rollover-versus-expansion comparison by themselves.

Delta and distance must travel together. The original 49 selected far calls have a median signal delta of 5.10 points, but their distance ranges from 5.63% to 63.47% OTM. ASML and ASTS are both roughly five-delta, seven-day calls, yet they sit 19.70% and 63.47% above spot. Delta is local model sensitivity, not a strike-touch probability or a bound on loss. Moving toward ten delta increases the short call's local directional exposure; changing the band does not eliminate the upside-chase risk before the nearer call is acquired.

The table below uses the **variant** strikes from the richness table. The eligibility table's stored contract coordinates belong to the original selection and must not be silently relabeled. Variant OTM is calculated from its strike and the matching frozen signal-chain spot. All coordinates are at the signal, before actual-entry rechecks.

| Stock | Delta points | OTM | Calendar DTE | Distance in ATM move units | Bid IV minus ATM, vol points | Prior dates: delta / forward coordinate |
|---|---:|---:|---:|---:|---:|---:|
| PLTR | 9.51 | 11.33% | 7 | 1.47 | +3.71 | 117 / 115 |
| DIS | 8.86 | 7.21% | 14 | 1.43 | −0.26 | 103 / 95 |
| MRVL | 9.77 | 36.56% | 11 | 1.62 | +14.95 | 111 / 30 |
| ORCL | 9.96 | 15.54% | 11 | 1.50 | +5.64 | 124 / 126 |
| QCOM | 10.43 | 26.74% | 11 | 1.47 | +7.59 | 112 / 38 |
| CRM | 9.42 | 11.21% | 10 | 1.50 | +4.07 | 126 / 112 |

Large percentage distances become much closer when scaled by each stock's volatility: these six calls span about 1.43–1.62 ATM move units. That calculation is `log(K/F)/(ATM_IV*sqrt(DTE/365))`, using the table's carry-model forward and matched ATM IV. The forward is internally model-consistent, not independently observed or verified. These units are descriptive coordinates, not probabilities or risk equivalence.

All six have at least 60 prior comparable delta/DTE dates. Only four meet that requirement for forward-moneyness/DTE: MRVL has 30 dates and QCOM 38, so their forward-coordinate z-scores and percentiles remain unavailable. The table's overall `ok` status does not override those coordinate-level failures. Forty-four population rows have no requested history because they lacked preliminary entry feasibility; missing richness is not a zero or evidence of cheapness.

DIS makes the distinction between relative rank and absolute richness concrete. Its exact call-bid IV is about 0.26 volatility points below matched ATM IV, yet its delta/DTE percentile is 84.5 because comparable prior bid wings averaged roughly −3.02 points. The original admission proxy was a positive five-delta, ten-day wing; that is a different coordinate from this roughly nine-delta, fourteen-day exact call. Conversely, MRVL's +14.95-point bid wing reaches the 99.1st delta/DTE percentile, while CRM is near the 96th percentile in both supported coordinates. Those are relative-pricing observations, not prospective returns. They do not authorize a new post-result richness gate.

Age, depth and rollover answer separate questions. Age counts consecutive observed sessions above the threshold; depth is the current percentile excess above 85; cumulative normalized excess sums that intensity through the episode. Pullback measures distance below the peak already known at the signal. A large pullback is not automatically two consecutive declines. ZS, for example, is age 16 and 10.22 volatility points below its known peak, but its latest two-session wing state is expanding. Among the six measured variant names, PLTR, MRVL and ORCL are expanding; DIS, QCOM and CRM are mixed. All six are age one or two. This is chiefly a test of selling elevated upside inventory during young episodes, not an established exhaustion basket.

The 30/60-day variance comparisons are also distinct from exact-strike wing richness. In the full population, implied variance exceeds trailing realized variance in 13 rows at 30 days and 23 at 60 days; 13 are positive at both horizons, while 27 are negative at both. Among the six measured names, only DIS is positive at both:

| Stock | 30-calendar-day IV / RV | 60-calendar-day IV / RV |
|---|---:|---:|
| PLTR | 49.0% / 59.5% | 53.6% / 54.2% |
| DIS | 24.9% / 19.1% | 28.5% / 26.7% |
| MRVL | 105.0% / 148.5% | 103.5% / 113.8% |
| ORCL | 53.3% / 81.9% | 54.1% / 67.3% |
| QCOM | 79.3% / 93.1% | 77.7% / 96.2% |
| CRM | 41.6% / 55.8% | 42.9% / 52.6% |

MRVL can have a rich exact call wing while ATM implied variance is below recent realized variance. Its reported adjusted return includes a 32.52% jump on June 2, which materially affects both trailing windows. The population also flags large historical moves in RDW, ZS and, over 60 days, DDOG. These flags warrant context; they are not proof of bad data, and no move was deleted. Trailing realized variance describes the past and is not a forecast of the option's remaining life.

The frozen delayed purchase is a **price-financing experiment with a fixed nearer strike**. HIRO's fifteen-minute call-flow reversal plus price break governs only the alternative initial short-sale time. After that sale, the D0, D1 and D2 arms buy the already selected adjacent lower call at the first quote that meets the financing, OTM, positive-delta, earnings and execution gates within the specified window. There is no later HIRO confirmation requirement: no renewed bullish call flow, rebound or second exhaustion signal is required. Adding one would be another experiment, not an interpretation of this protocol.

That choice separates the initial flow-timing question from the value of the second purchase. D0 scans after the sale through 15:30 ET; D1 and D2 scan 09:31–15:30 in their respective sessions. The original short sale and the D4/D5 closing deadlines stay fixed across the acquisition arms. Known failure to purchase retains the short until the common cover; missing paths remain censored. Financing alone cannot establish that the nearer call was worth buying: the comparisons remain immediate spread purchase, final short cover and conversion-time short cover. No trade P&L, timing advantage or execution success is asserted in this draft.

Sources: [eligibility features](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/eligibility_features.csv), [strike richness](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/strike_richness.csv), [feature definitions](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/feature_definitions.md), [frozen protocol](/Users/dgrissen/Dev/delta_bomb/hypothesis_tracking/pandar_seed_and_frozen_protocol.md), and [variant specification](/Users/dgrissen/Dev/delta_bomb/hypothesis_tracking/pandar_round2_delta_variant.md). This is a canonical Charlie persona simulation, not communication with the actual person.

Read-version SHA256: eligibility features `33337863c14dbf3dc8edd4522f66379f48565d473a646e1e3f79f40f05c556f2`; strike richness `84ab4630822d2b3a870740f1259cb23d5a8c300a126d38141dda4d3245be3456`. The draft uses signal features and prior comparable histories only; it makes no provider calls and reads no option outcome paths.

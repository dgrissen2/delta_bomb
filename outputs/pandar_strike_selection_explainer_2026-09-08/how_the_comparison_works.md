# How expiry and strike richness would be compared

Follow-up: [Charlie and Brent's proposed method](charlie_brent_good_trade_method.md) audits this calculation for skew sensitivity, execution costs, actual strike kinks, and evidence for mean reversion.

The June backtest did not choose the highest-richness expiry or strike. It first chose the expiry nearest ten days inside its 7–14-day range, then the call nearest the target delta. Richness was measured afterward for the entry-feasible selections. The later proposal to rank multiple expiries and strikes was a proposed improvement, not a description of that completed selection.

This is a new explanatory calculation using cached MRVL signal-day data from June 15, 2026. It reads no trade outcomes, changes no frozen selection and makes no provider calls. The historical sample has already been examined, so this is not a new unseen test.

## One option, one calculation

For the June 26 $425 call, the June 15 bid was $2.74 and its bid-implied volatility was 125.19%. Matched ATM call IV in that same expiry was 110.24%. The call wing was therefore 125.19 − 110.24 = **14.95 volatility points**. This isolates the far-call pricing relative to the expiry's general volatility level.

The comparison history asks what the same measurement looked like on each earlier day for calls with similar delta and the same time remaining. It does not follow today's $425 contract backward. Supported strike and expiry interpolation supplies the comparable observation; unsupported dates remain unavailable. The 126-session lookback produced 111 valid prior delta/DTE observations for this example.

That prior wing averaged 1.92 points, with a sample standard deviation of 4.94 points. Today's z-score was therefore `(14.95 − 1.92) / 4.94 = 2.64`. Its historical midrank percentile was 99.1. These describe unusual relative pricing, not a 99.1% chance of profit or proof of mispricing.

## Compare expiries at roughly the same delta

All values are from the same June 15 signal snapshot. Each expiry uses the listed OTM call nearest ten delta solely to make this explanation comparable. This sampling choice is not asserted to be optimal.

| Expiry / strike | Days left | Delta points | Call bid IV | Same-expiry ATM IV | Current wing | Prior usual wing | Z-score | Prior delta/DTE dates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| June 18 / $365 | 3 | 10.55 | 130.71% | 124.11% | 6.59 | 1.37 | 0.95 | 73 |
| June 26 / $425 | 11 | 9.77 | 125.19% | 110.24% | 14.95 | 1.92 | 2.64 | 111 |
| July 2 / $460 | 17 | 9.48 | 122.17% | 107.56% | 14.61 | 0.90 | 2.66 | 101 |

June 18 has the highest outright IV, but its ATM IV is also high. June 26 and July 2 have more unusual extra call-wing pricing relative to their own comparable histories. Their nearly equal z-scores do not choose a winner: time exposure, spread costs, stressed losses and the intended holding period still matter. June 18 and July 2 were outside the original frozen 7–14-day expiry envelope.

## Compare strikes within one expiry

| June 26 strike | Delta points | OTM distance | Bid / ask | Current wing | Prior usual wing | Z-score |
|---|---:|---:|---|---:|---:|---:|
| $420 | 10.55 | 34.95% | $2.97 / $3.30 | 13.95 | 1.75 | 2.67 |
| $425 | 9.77 | 36.56% | $2.74 / $3.00 | 14.95 | 1.92 | 2.64 |
| $430 | 9.06 | 38.17% | $2.42 / $2.91 | 14.80 | 1.97 | 2.33 |

The $420 call pays more but is closer to the stock. The $425 call sacrifices some premium for more distance and has a narrower displayed quote. The $430 call is farther away again, with less premium and a wider displayed quote. Richness makes those alternatives visible; it does not resolve their risk trade-offs by itself. No different strike or expiry has been substituted into the frozen P&L study.

## What remains unproven

The separate comparable forward-moneyness/DTE histories have only 41, 30 and 17 supported dates for the three expiry examples, and 33/30/27 for the three June 26 strikes. All are below the required 60. None receives full two-coordinate richness clearance. Matching a roughly ten-delta call is not the same as matching its percentage distance above the underlying.

ATM here uses the existing carry-model forward with an internal ORATS model-consistency check; the forward is not independently observed. Prior histories include earnings periods. These EOD quote-derived measurements are signal features, not actual June 16 entry prices or proof of fills. Richness still needs a separate test of later normalization and net trade economics.

Reproducible numeric results: [comparison CSV](mrvl_comparison.csv) and [per-date support details](comparison_detail.json). Sources are the existing signal chains, prior strike history, forward-coordinate audit and richness acquisition calendar under `/Users/dgrissen/Dev/delta_bomb/data/pandar_hypothesis_2026-09-07/` and `/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/`. Calculation uses `/Users/dgrissen/Dev/delta_bomb/scripts/pandar_hypothesis_richness.py` without changing its rules.

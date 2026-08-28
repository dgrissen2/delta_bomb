# HIRO daily call-path table: 2026-08-11 through 2026-08-21

> This file is the **exact-chain-executable subset**. The complete requested set
> of all 58 qualifying HIRO ticker/date signals is in
> `hiro_all_qualifying_strategy_signals.md`. Exact-chain failure does not remove
> a ticker from that full qualifying set.

Run date: 2026-08-23

HIRO source: `/Users/dgrissen/Dev/core_spotgamma_spx_vix_data/hiro_tickers.csv`

Refreshed symbols: 398

Source SHA-256: `30c95d3307e3557bf6be88f9870976e50322edb5df113b4a02a4eb778db40a86`

## Interpretation

- High RR Rank plus low call-skew rank (`CS`) means downside IV is rich relative
  to upside calls. This supports **buy first**.
- Low RR Rank plus high CS, an extreme front call wing, and a positive call kink
  means the upside tail is rich. This supports **sell first**.
- IV Rank measures the whole surface versus the ticker's trailing year. Low IV
  strengthens a buy. Midrange IV can support a sell when the local call wing is
  extreme.
- A **puke buy** enters the complete cheap call spread. A **standard buy** buys
  the roughly 15-delta call first and rests the upper-call sale. A **sell-first
  grab** sells the far 2--6-delta call and rests a bid for the nearer call, with
  a mandatory breakout stop while the first leg is naked.

The refreshed 398-name list contains ETFs and indices. Applying the same
single-stock and strict-liquidity gates as the broad screen left 305--306 eligible
stocks and 260--270 liquid stocks per session. The HIRO membership is the list
refreshed on 2026-08-23 applied retrospectively; the ORATS ranks and quotes are
point-in-time, but the membership set is not a historical HIRO snapshot.

## Daily funnel

| Date | Eligible HIRO stocks | Strict liquid | Surface rows: puke / standard / sell | Exact-chain rows | Exact names |
|---|---:|---:|---:|---:|---|
| 08-11 | 305 | 266 | 6 / 1 / 1 | 1 | NOK |
| 08-12 | 305 | 260 | 4 / 2 / 2 | 0 | No executable ticket |
| 08-13 | 305 | 265 | 2 / 0 / 2 | 0 | No executable ticket |
| 08-14 | 305 | 264 | 3 / 0 / 0 | 1 | JD |
| 08-17 | 306 | 268 | 4 / 2 / 2 | 2 | JD, LCID |
| 08-18 | 306 | 268 | 2 / 3 / 0 | 2 | DJT, QS |
| 08-19 | 305 | 268 | 3 / 2 / 2 | 4 | RDW, LMND, INTC, MSTR |
| 08-20 | 305 | 267 | 3 / 2 / 3 | 3 | BB, RDW, MSTR |
| 08-21 | 305 | 270 | 2 / 2 / 3 | 2 | SOUN, MSTR |

## Exact-chain daily strategy table

All ranks are causal trailing-252-session percentiles. Prices are signal-close
quotes. For puke buys, the maximum debit is long-call ask minus short-call bid.
For sell-first, the initial credit is the far-call bid and the nearer-call price
is the resting buy target.

| Date | Ticker | Path | RR Rank | IV Rank | Why this path | Exact signal-date strategy |
|---|---|---|---:|---:|---|---|
| 08-11 | NOK | Buy-first puke | 69.8 | 50.8 | RR passes, CS 23.0, and -15.5% drawdown. IV is near the upper end of the buy exception but still below 65. | Buy Oct-16 12/17C for no more than $0.30; enter the full spread and scale out into a rebound. |
| 08-14 | JD | Buy-first puke | 61.1 | 8.8 | RR barely clears the floor, but outright IV is very cheap, CS is 22.2, and drawdown is -13.1%. | Buy Oct-16 37/42C for no more than $0.16. |
| 08-17 | JD | Buy-first puke | 78.2 | 13.2 | RR strengthened materially, IV stayed cheap, CS fell to 15.9, and drawdown reached -14.6%. | Buy Oct-16 36/41C for no more than $0.11. |
| 08-17 | LCID | Buy-first puke | 61.9 | 11.2 | RR passes, IV is cheap, CS 24.6, and drawdown is -23.6%. | Buy Sep-18 8/12C for no more than $0.12. |
| 08-18 | DJT | Buy-first puke | 65.9 | 37.8 | Moderate-high RR, acceptable IV, CS 28.2, and deep -22.1% drawdown. | Buy Sep-18 10/13C for no more than $0.15. |
| 08-18 | QS | Buy-first puke | 61.5 | 9.2 | RR barely passes, but very cheap IV, CS 21.0, and -8.7% drawdown reinforce the buy. | Buy Sep-18 7/11C for no more than $0.15. |
| 08-19 | RDW | Buy-first puke | 84.9 | 22.5 | Strong RR, cheap IV, CS 20.2, and -9.4% drawdown. | Buy Sep-18 16/21C for no more than $0.30. |
| 08-19 | LMND | Buy-first puke | 64.3 | 0.0 | IV is at the bottom of its yearly range; RR passes, CS 31.7, and drawdown is -17.8%. | Buy Sep-18 65/70C for no more than $0.20. |
| 08-19 | INTC | Buy-first puke | 65.1 | 40.5 | RR and CS 34.1 are buy-valid after a -10.6% drawdown; IV is moderate rather than exceptionally cheap. | Buy Sep-18 125/130C for no more than $0.22. |
| 08-19 | MSTR | Sell-first grab | 0.4 | 47.7 | RR is near its yearly floor, CS 96.8, front call wing 92.1, and kink 84.9: the upside tail is exceptionally rich while overall IV is midrange. | Sell Aug-28 140C at $0.24 or better; rest a buy of the 135C at $0.14. Cover or cap if the breakout tell fires. |
| 08-20 | BB | Buy-first puke | 62.7 | 27.9 | Cheap IV and passing RR after -9.5%; CS 38.9 is close to the buy cutoff, so quality is lower. | Buy Sep-18 10/13C for no more than $0.10. |
| 08-20 | RDW | Buy-first puke | 88.9 | 21.2 | Excellent high-RR/low-IV combination, CS 24.6, and -14.5% drawdown. | Buy Sep-18 15/20C for no more than $0.30. |
| 08-20 | MSTR | Sell-first grab | 0.0 | 54.9 | RR at the yearly floor, CS 99.2, call wing 96.4, and kink 88.9 confirm extreme upside richness. | Sell Aug-28 150C at $0.32 or better; rest a buy of the 145C at $0.22. The subsequent breakout means cover/cap, not add. |
| 08-21 | SOUN | Buy-first puke | 80.6 | 4.3 | Calls are relatively and outright cheap: high RR, very low IV Rank, CS 15.9, and -8.7% drawdown. | Buy Oct-16 9/14C for no more than $0.31. This was a fresh unresolved setup at the end of the window. |
| 08-21 | MSTR | Sell-first grab | 0.4 | 55.3 | RR remains near zero, CS 98.4, call wing 97.2, and kink 79.4. The rank signal persists, but the multi-day breakout override is active. | Mechanical screen: sell Aug-28 160C at $0.26 or better and rest a 155C buy at $0.16. Sequence-aware action: do not initiate/add while the breakout stop is active. |

No standard buy-first ticket survived exact-chain validation in this HIRO replay.
The rank surface produced standard candidates on seven dates, but each failed the
exact strike, quote-width, OI, or earnings check. Likewise, MSTR was the only
sell-first name to survive exact-chain validation.

## Reproducible artifacts

- `single_name_call_screen_candidates.csv` contains all 58 surface rows.
- `single_name_call_screen_chain_checks.csv` contains every exact-chain pass and
  failure reason.
- `single_name_call_screen_finalists.csv` contains the best confirmed row per
  ticker/scenario; repeated daily signals remain in the chain-check file.
- `single_name_call_screen_all.parquet` contains every eligible HIRO stock/day,
  including names with no signal.

The combined ORATS ledger stood at 331 / 500 calls after this run.

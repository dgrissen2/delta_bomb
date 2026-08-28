# HIRO daily call-path table: 2026-08-11 through 2026-08-27

> Exact-chain-executable subset. The complete 87-row surface-qualified set is in `hiro_all_qualifying_strategy_signals.md`.

Charlie’s unified analysis of all three methods is in [`three_call_methods_charlie_analysis.md`](three_call_methods_charlie_analysis.md). It also explains why the four MSTR sell-first confirmations are one squeeze episode, not four independent validations.

Run date: 2026-08-28

HIRO source: `/Users/dgrissen/Dev/core_spotgamma_spx_vix_data/hiro_tickers.csv`

Refreshed symbols: 398

Source SHA-256: `30c95d3307e3557bf6be88f9870976e50322edb5df113b4a02a4eb778db40a86`

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
| 08-24 | 305 | 270 | 3 / 3 / 3 | 1 | MSTR |
| 08-25 | 305 | 271 | 3 / 3 / 2 | 1 | RDW |
| 08-26 | 306 | 271 | 3 / 2 / 0 | 1 | SOUN |
| 08-27 | 304 | 270 | 3 / 3 / 1 | 1 | RDW |

## Exact-chain strategy table

| Date | Ticker | Path | RR Rank | IV Rank | Why this path | Exact signal-date strategy |
|---|---|---|---:|---:|---|---|
| 08-11 | NOK | Buy-first puke | 69.8 | 50.8 | RR 69.8 >=60, CS 23.0 <=40, IV 50.8 <=65, drawdown -15.5%, and 5d -5.0%. | Buy Oct-16 12/17C for <=$0.30; enter the full spread and scale out into a rebound. |
| 08-14 | JD | Buy-first puke | 61.1 | 8.8 | RR 61.1 >=60, CS 22.2 <=40, IV 8.8 <=65, drawdown -13.1%, and 5d -11.9%. | Buy Oct-16 37/42C for <=$0.16; enter the full spread and scale out into a rebound. |
| 08-17 | JD | Buy-first puke | 78.2 | 13.2 | RR 78.2 >=60, CS 15.9 <=40, IV 13.2 <=65, drawdown -14.6%, and 5d -14.6%. | Buy Oct-16 36/41C for <=$0.11; enter the full spread and scale out into a rebound. |
| 08-17 | LCID | Buy-first puke | 61.9 | 11.2 | RR 61.9 >=60, CS 24.6 <=40, IV 11.2 <=65, drawdown -23.6%, and 5d -5.5%. | Buy Sep-18 8/12C for <=$0.12; enter the full spread and scale out into a rebound. |
| 08-18 | DJT | Buy-first puke | 65.9 | 37.8 | RR 65.9 >=60, CS 28.2 <=40, IV 37.8 <=65, drawdown -22.1%, and 5d -9.6%. | Buy Sep-18 10/13C for <=$0.15; enter the full spread and scale out into a rebound. |
| 08-18 | QS | Buy-first puke | 61.5 | 9.2 | RR 61.5 >=60, CS 21.0 <=40, IV 9.2 <=65, drawdown -8.7%, and 5d -8.4%. | Buy Sep-18 7/11C for <=$0.15; enter the full spread and scale out into a rebound. |
| 08-19 | RDW | Buy-first puke | 84.9 | 22.5 | RR 84.9 >=60, CS 20.2 <=40, IV 22.5 <=65, drawdown -9.4%, and 5d -8.2%. | Buy Sep-18 16/21C for <=$0.30; enter the full spread and scale out into a rebound. |
| 08-19 | LMND | Buy-first puke | 64.3 | 0.0 | RR 64.3 >=60, CS 31.7 <=40, IV 0.0 <=65, drawdown -17.8%, and 5d -1.4%. | Buy Sep-18 65/70C for <=$0.20; enter the full spread and scale out into a rebound. |
| 08-19 | INTC | Buy-first puke | 65.1 | 40.5 | RR 65.1 >=60, CS 34.1 <=40, IV 40.5 <=65, drawdown -10.6%, and 5d -7.5%. | Buy Sep-18 125/130C for <=$0.22; enter the full spread and scale out into a rebound. |
| 08-19 | MSTR | Sell-first grab | 0.4 | 47.7 | RR 0.4 <=10 while call wing 92.1 and kink 84.9 are >=85/>=70; IV 47.7, 5d +9.4%, drawdown 0.0%. | Sell Aug-28 140C at >=$0.24; rest buy of 135C at $0.14; breakout stop mandatory. |
| 08-20 | BB | Buy-first puke | 62.7 | 27.9 | RR 62.7 >=60, CS 38.9 <=40, IV 27.9 <=65, drawdown -9.5%, and 5d -9.5%. | Buy Sep-18 10/13C for <=$0.10; enter the full spread and scale out into a rebound. |
| 08-20 | RDW | Buy-first puke | 88.9 | 21.2 | RR 88.9 >=60, CS 24.6 <=40, IV 21.2 <=65, drawdown -14.5%, and 5d -11.9%. | Buy Sep-18 15/20C for <=$0.30; enter the full spread and scale out into a rebound. |
| 08-20 | MSTR | Sell-first grab | 0.0 | 54.9 | RR 0.0 <=10 while call wing 96.4 and kink 88.9 are >=85/>=70; IV 54.9, 5d +14.4%, drawdown 0.0%. | Sell Aug-28 150C at >=$0.32; rest buy of 145C at $0.22; breakout stop mandatory. |
| 08-21 | SOUN | Buy-first puke | 80.6 | 4.3 | RR 80.6 >=60, CS 15.9 <=40, IV 4.3 <=65, drawdown -8.7%, and 5d -0.9%. | Buy Oct-16 9/14C for <=$0.31; enter the full spread and scale out into a rebound. |
| 08-21 | MSTR | Sell-first grab | 0.4 | 55.3 | RR 0.4 <=10 while call wing 97.2 and kink 79.4 are >=85/>=70; IV 55.3, 5d +27.6%, drawdown 0.0%. | Sell Aug-28 160C at >=$0.26; rest buy of 155C at $0.16; breakout stop mandatory. |
| 08-24 | MSTR | Sell-first grab | 1.2 | 54.1 | RR 1.2 <=10 while call wing 94.8 and kink 98.0 are >=85/>=70; IV 54.1, 5d +25.0%, drawdown 0.0%. | Sell Aug-28 155C at >=$0.22; rest buy of 152.5C at $0.12; breakout stop mandatory. |
| 08-25 | RDW | Buy-first puke | 75.8 | 19.0 | RR 75.8 >=60, CS 32.9 <=40, IV 19.0 <=65, drawdown -16.4%, and 5d -10.7%. | Buy Sep-25 14.5/19C for <=$0.35; enter the full spread and scale out into a rebound. |
| 08-26 | SOUN | Buy-first puke | 71.4 | 0.0 | RR 71.4 >=60, CS 13.9 <=40, IV 0.0 <=65, drawdown -12.8%, and 5d -1.4%. | Buy Oct-16 9/14C for <=$0.18; enter the full spread and scale out into a rebound. |
| 08-27 | RDW | Buy-first puke | 86.9 | 17.1 | RR 86.9 >=60, CS 11.9 <=40, IV 17.1 <=65, drawdown -18.0%, and 5d -4.1%. | Buy Sep-25 13.5/18C for <=$0.40; enter the full spread and scale out into a rebound. |

Exact-chain result: **19 rows** (15 puke, 4 sell-first) across **11 unique ticker/scenario finalists** after retaining each ticker's highest-ranked confirmed date.

No standard buy-first row passed the strict historical contract quote/OI/width/earnings checks. MSTR remained the only sell-first ticker with confirmed tickets; its confirmed dates are listed separately because each is a distinct signal-date chain.

ORATS ledger: **416 / 500 calls used**.

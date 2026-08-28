# All qualifying HIRO call-path signals: 2026-08-11 through 2026-08-21

This is the complete qualifying set: **58 ticker/date rows across 40 unique
tickers**. Qualification here means the point-in-time ORATS surface, path regime,
and aggregate-liquidity rules passed. Exact-chain status is an annotation, not
an inclusion filter.

The universe is the 398-symbol HIRO list refreshed from SpotGamma on 2026-08-23.
That current membership list is applied retrospectively; the ORATS ranks and
quotes are point-in-time, but the HIRO membership is not a historical snapshot.

## How to read the columns

- **Buy-first puke:** RR Rank >= 60, call-skew rank (CS) <= 40, IV Rank <= 65,
  20-day drawdown <= -8%, and negative five-day return. Enter the complete cheap
  20-35%-OTM call spread and scale out into a rebound.
- **Buy-first standard:** a Good/Better/Best cheap-call surface plus the technical
  overlay. Buy the roughly 15-delta call first, then rest the adjacent upper-call
  sale into strength.
- **Sell-first grab:** RR Rank <= 10, front call-wing rank >= 85, kink >= 70,
  positive five-day return, within 5% of the 20-day high, IV Rank 30-70, and no
  near earnings. Sell the far call first, rest the nearer-call buy, and enforce
  the breakout stop.
- High RR plus low CS supports owning calls. Low RR plus high CS/wing/kink
  supports selling the call wing. IV Rank measures the whole surface versus its
  own year; it is not itself the direction signal.
- **Exact chain?** says whether the historical chain also passed the contract
  quote, OI, bid/ask-width, DTE, delta, and earnings checks. A No does not remove
  the surface qualifier; it means the generic strategy lacked an executable
  ticket under the strict contract rules.

## All 58 qualifying ticker/date rows

| Date | Ticker | Path | RR Rank | IV Rank | CS Rank | Wing | Kink | 20d DD | 5d return | Strategy expression | Exact chain? |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 08-11 | CIFR | Buy-first puke | 92.1 | 20.6 | 3.2 | 42.5 | 70.2 | -32.9% | -16.2% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-11 | GME | Buy-first puke | 78.2 | 23.0 | 10.3 | 9.5 | 33.3 | -15.5% | -2.1% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-11 | JBLU | Buy-first puke | 81.3 | 7.9 | 10.7 | 49.6 | 67.5 | -10.1% | -10.1% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-11 | NOK | Buy-first puke | 69.8 | 50.8 | 23.0 | 29.4 | 65.1 | -15.5% | -5.0% | Buy 10-16 12/17C <= $0.30 | Yes |
| 08-11 | STX | Buy-first puke | 61.1 | 60.7 | 29.8 | 33.3 | 55.2 | -10.2% | -4.3% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-11 | VFC | Buy-first puke | 65.9 | 0.0 | 14.7 | 40.1 | 69.4 | -18.9% | -3.5% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-11 | MELI | Buy-first standard (good) | 72.6 | 32.2 | 27.8 | 63.5 | 57.9 | 0.0% | 3.3% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-11 | FANG | Sell-first grab | 6.0 | 53.1 | 82.1 | 87.7 | 87.7 | -1.8% | 5.5% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |
| 08-12 | LCID | Buy-first puke | 60.3 | 13.3 | 24.2 | 70.2 | 89.3 | -20.1% | -2.0% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-12 | M | Buy-first puke | 90.5 | 61.6 | 1.6 | 34.5 | 48.8 | -9.2% | -7.5% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-12 | VFC | Buy-first puke | 88.9 | 0.0 | 10.7 | 10.3 | 38.9 | -19.1% | -3.7% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-12 | XPEV | Buy-first puke | 82.5 | 47.1 | 4.4 | 45.2 | 44.0 | -17.0% | -0.3% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-12 | HUM | Buy-first standard (good) | 74.2 | 41.2 | 21.4 | 8.3 | 22.2 | -4.4% | 6.4% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-12 | LYFT | Buy-first standard (good) | 78.2 | 0.0 | 25.4 | 42.1 | 81.3 | -6.6% | 0.9% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-12 | FDX | Sell-first grab | 8.3 | 31.9 | 93.3 | 97.2 | 73.4 | 0.0% | 4.8% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |
| 08-12 | LRCX | Sell-first grab | 0.4 | 56.7 | 96.8 | 93.7 | 77.8 | 0.0% | 4.7% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |
| 08-13 | CVS | Buy-first puke | 75.0 | 7.6 | 21.0 | 32.1 | 49.6 | -14.2% | -2.1% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-13 | HUT | Buy-first puke | 69.4 | 31.0 | 26.2 | 54.4 | 42.5 | -28.4% | -8.6% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-13 | LRCX | Sell-first grab | 0.4 | 57.5 | 99.6 | 96.8 | 79.8 | 0.0% | 9.2% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |
| 08-13 | SMCI | Sell-first grab | 1.6 | 63.2 | 94.8 | 94.8 | 80.2 | 0.0% | 32.6% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |
| 08-14 | JD | Buy-first puke | 61.1 | 8.8 | 22.2 | 12.3 | 53.2 | -13.1% | -11.9% | Buy 10-16 37/42C <= $0.16 | Yes |
| 08-14 | LI | Buy-first puke | 77.8 | 9.6 | 3.6 | 2.8 | 23.8 | -11.3% | -5.5% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-14 | LUV | Buy-first puke | 64.3 | 19.3 | 11.1 | 61.5 | 63.9 | -9.8% | -6.1% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-17 | JBLU | Buy-first puke | 72.2 | 8.2 | 13.1 | 29.4 | 48.8 | -18.1% | -6.7% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-17 | JD | Buy-first puke | 78.2 | 13.2 | 15.9 | 34.9 | 75.0 | -14.6% | -14.6% | Buy 10-16 36/41C <= $0.11 | Yes |
| 08-17 | LCID | Buy-first puke | 61.9 | 11.2 | 24.6 | 11.5 | 40.1 | -23.6% | -5.5% | Buy 09-18 8/12C <= $0.12 | Yes |
| 08-17 | LI | Buy-first puke | 62.3 | 10.6 | 11.1 | 6.0 | 73.4 | -10.1% | -3.3% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-17 | FHN | Buy-first standard (better) | 80.2 | 10.6 | 4.0 | 36.1 | 26.2 | -1.1% | 2.7% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-17 | LLY | Buy-first standard (good) | 61.1 | 27.2 | 31.0 | 31.7 | 56.3 | -3.4% | -3.4% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-17 | GS | Sell-first grab | 1.6 | 37.9 | 95.6 | 99.2 | 86.5 | -4.4% | 1.7% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |
| 08-17 | LRCX | Sell-first grab | 2.0 | 50.2 | 94.4 | 92.9 | 79.0 | 0.0% | 11.2% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |
| 08-18 | DJT | Buy-first puke | 65.9 | 37.8 | 28.2 | 2.4 | 10.3 | -22.1% | -9.6% | Buy 09-18 10/13C <= $0.15 | Yes |
| 08-18 | QS | Buy-first puke | 61.5 | 9.2 | 21.0 | 22.6 | 54.4 | -8.7% | -8.4% | Buy 09-18 7/11C <= $0.15 | Yes |
| 08-18 | HUM | Buy-first standard (good) | 65.9 | 45.2 | 38.9 | 5.6 | 28.6 | -3.9% | 2.1% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-18 | LLY | Buy-first standard (good) | 72.2 | 24.1 | 32.5 | 3.2 | 46.0 | -0.2% | 0.7% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-18 | TEVA | Buy-first standard (good) | 73.8 | 3.7 | 10.3 | 7.9 | 46.8 | -0.8% | 0.6% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-19 | INTC | Buy-first puke | 65.1 | 40.5 | 34.1 | 29.8 | 46.0 | -10.6% | -7.5% | Buy 09-18 125/130C <= $0.22 | Yes |
| 08-19 | LMND | Buy-first puke | 64.3 | 0.0 | 31.7 | 7.1 | 27.8 | -17.8% | -1.4% | Buy 09-18 65/70C <= $0.20 | Yes |
| 08-19 | RDW | Buy-first puke | 84.9 | 22.5 | 20.2 | 46.4 | 54.8 | -9.4% | -8.2% | Buy 09-18 16/21C <= $0.30 | Yes |
| 08-19 | CRSP | Buy-first standard (good) | 67.1 | 22.3 | 29.8 | 9.5 | 67.1 | 0.0% | 8.5% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-19 | WBD | Buy-first standard (good) | 73.0 | 17.5 | 25.4 | 13.1 | 26.6 | 0.0% | 3.6% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-19 | COIN | Sell-first grab | 2.4 | 59.2 | 92.5 | 88.9 | 70.2 | -5.0% | 6.9% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |
| 08-19 | MSTR | Sell-first grab | 0.4 | 47.7 | 96.8 | 92.1 | 84.9 | 0.0% | 9.4% | Sell 08-28 140C >= $0.24; rest buy 135C at $0.14 | Yes |
| 08-20 | BB | Buy-first puke | 62.7 | 27.9 | 38.9 | 36.5 | 9.1 | -9.5% | -9.5% | Buy 09-18 10/13C <= $0.10 | Yes |
| 08-20 | QS | Buy-first puke | 69.0 | 7.5 | 27.0 | 7.9 | 32.1 | -10.6% | -9.0% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-20 | RDW | Buy-first puke | 88.9 | 21.2 | 24.6 | 9.1 | 32.9 | -14.5% | -11.9% | Buy 09-18 15/20C <= $0.30 | Yes |
| 08-20 | GILD | Buy-first standard (good) | 83.7 | 25.0 | 29.4 | 90.1 | 86.1 | -3.1% | 4.7% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-20 | LYFT | Buy-first standard (good) | 61.9 | 11.4 | 30.2 | 44.4 | 68.7 | -2.0% | 1.0% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-20 | COIN | Sell-first grab | 0.0 | 68.5 | 98.0 | 98.4 | 78.6 | 0.0% | 11.7% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |
| 08-20 | MSTR | Sell-first grab | 0.0 | 54.9 | 99.2 | 96.4 | 88.9 | 0.0% | 14.4% | Sell 08-28 150C >= $0.32; rest buy 145C at $0.22 | Yes |
| 08-20 | NEM | Sell-first grab | 0.4 | 50.8 | 96.8 | 97.2 | 76.2 | 0.0% | 11.9% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |
| 08-21 | RDW | Buy-first puke | 85.3 | 21.3 | 9.5 | 36.1 | 46.0 | -11.5% | -11.5% | Buy complete 20-35% OTM 30-90 DTE cheap call spread | No |
| 08-21 | SOUN | Buy-first puke | 80.6 | 4.3 | 15.9 | 4.4 | 37.3 | -8.7% | -0.9% | Buy 10-16 9/14C <= $0.31 | Yes |
| 08-21 | ANF | Buy-first standard (good) | 73.0 | 44.7 | 13.5 | 59.1 | 98.8 | -7.8% | 0.5% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-21 | LLY | Buy-first standard (good) | 74.6 | 32.0 | 31.3 | 33.3 | 34.5 | -2.3% | 6.5% | Buy ~15-delta 30-60 DTE call; rest adjacent upper-call sale | No |
| 08-21 | MRK | Sell-first grab | 4.0 | 67.9 | 91.7 | 93.7 | 73.8 | 0.0% | 12.9% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |
| 08-21 | MSTR | Sell-first grab | 0.4 | 55.3 | 98.4 | 97.2 | 79.4 | 0.0% | 27.6% | Sell 08-28 160C >= $0.26; rest buy 155C at $0.16 | Yes |
| 08-21 | NEM | Sell-first grab | 2.4 | 54.5 | 94.4 | 96.4 | 73.0 | 0.0% | 12.6% | Sell 2-6 delta 5-19 DTE call; rest nearer-call buy; breakout stop | No |

## Supporting data

- `single_name_call_screen_candidates.csv` is the raw 58-row qualifying set.
- `single_name_call_screen_chain_checks.csv` adds the exact-chain failure reason
  and any selected contract details.
- `single_name_call_screen_all.parquet` contains every eligible HIRO ticker/day,
  including non-qualifiers.

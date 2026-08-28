# Single-name call-side screen: 2026-08-12 through 2026-08-21

Run date: 2026-08-23

Branch/worktree: `nvda_call_strat`

Status: research screen; not a deployment recommendation

## Bottom line

Yes, the NVDA call-side discovery generalizes, but almost entirely through the
**buy-the-puke call-spread branch** in this eight-session sample.

- **15 liquid names** had a valid buy-the-puke surface and an executable 20--35%-OTM,
  roughly $5-wide call spread costing $0.05--$0.50.
- **PGY** was the only valid standard 15-delta buy-first leg-in. It had not paired by
  the 2026-08-21 close.
- **MSTR** was the only valid sell-first chain. The signal was real, but the trade had
  moved adversely and activated the breakout tell by 2026-08-21. It is evidence that
  the screen detects the grab, not evidence that selling the grab is automatically safe.
- No post-shock-smile sell-first name survived chain checks. AMLX passed the surface
  screen, but its selected far call was 0.00 x 0.75 with zero open interest.
- NVDA itself did not qualify in this window. Its front call wing stayed below the
  85th-percentile sell threshold, while RR/call-skew still said calls were relatively
  rich rather than cheap.

The strongest observed buy-first result was **BTDR**: the 2026-09-18 11/16 call spread
cost $0.45 on 2026-08-14 and had a conservative bid-side value of $1.00 on 2026-08-21
(2.22x). **UUUU** reached 1.86x after one close; **LMND** 1.25x; **DJT** 1.13x.
These are early marks, not completed lifecycle results.

## Funnel and data integrity

| Stage | Result |
|---|---:|
| ORATS symbols per target close | about 6,013 |
| Point-in-time single-stock universe | 1,835--1,883 |
| Strict liquid subset | 525--597 |
| Surface signal rows | 122 across 90 tickers |
| Exact-chain-valid rows | 24 |
| Unique ticker/scenario finalists | 17 |
| ORATS call budget used | 315 / 500 |

The broad universe required a recognized equity sector, no ORATS synthetic/index alias,
20-day average option volume of at least 150, OI of at least 1,000, stock price of at
least $5, and market cap of at least $100 million. The final liquidity gate required
average option volume of at least 2,000, OI of at least 25,000, stock dollar volume of
at least $20 million, and ORATS surface confidence of at least 50.

All RR, skew, wing, kink, and IV percentiles are causal: today's observation is compared
with the prior 252 trading sessions only (minimum 126). The data were fetched as the full
ORATS cross-section on each actual SPY trading date, so names were not selected using
future outcomes.

## Path decision table: RR Rank, IV Rank, and trade expression

RR Rank is the causal percentile of 30-day 25-delta risk reversal. A high rank means
downside IV is rich relative to upside-call IV and therefore supports **buy first**. A
low rank means upside calls are rich relative to downside IV and supports **sell first**
when the exact call wing and kink also confirm. IV Rank answers a different question:
whether the ticker's overall IV is cheap or expensive versus its own trailing year.
Low IV Rank strengthens a buy; a midrange IV Rank can support a sell when the local call
wing is exceptionally rich. `CS rank` below is the causal percentile of 25-delta call
skew; low CS reinforces buy-first, while high CS reinforces sell-first.

| Ticker | Signal | Path | RR Rank | IV Rank | Why this path | Exact strategy |
|---|---|---|---:|---:|---|---|
| ASX | 08-20 | Buy-first puke | 83.7 | 48.7 | High RR, CS 12.7, and -8.4% drawdown: calls cheap relative to puts despite only midrange outright IV. | Buy Sep-18 47.5/50C for no more than $0.20; scale out into a rebound. |
| GRPN | 08-17 | Buy-first puke | 61.9 | 29.9 | RR clears the buy floor, CS 32.9 and IV are cheap, with a -27.7% drawdown. | Buy Sep-18 26/31C for no more than $0.35; scale out rather than hold mechanically. |
| BB | 08-20 | Buy-first puke | 62.7 | 27.9 | RR clears the floor and IV is cheap; CS 38.9 is near the maximum but still buy-valid after a -9.5% drawdown. | Buy Sep-18 10/13C for no more than $0.10. |
| RDW | 08-20 | Buy-first puke | 88.9 | 21.2 | Strong high-RR/low-IV combination, CS 24.6, and -14.5% drawdown. | Buy Sep-18 15/20C for no more than $0.30. |
| SOUN | 08-21 | Buy-first puke | 80.6 | 4.3 | Calls are relatively and outright cheap: high RR, very low IV Rank, CS 15.9, and -8.7% drawdown. | Buy Oct-16 9/14C for no more than $0.31; fresh setup with no later mark. |
| JD | 08-17 | Buy-first puke | 78.2 | 13.2 | High RR, cheap IV, CS 15.9, and -14.6% drawdown. | Buy Oct-16 36/41C for no more than $0.11. |
| BTDR | 08-14 | Buy-first puke | 71.8 | 31.4 | RR and CS 18.7 make upside cheap relative to downside after a -27.2% drawdown. | Buy Sep-18 11/16C for no more than $0.45; the later $1.00 mark is a scale-out zone. |
| NVTS | 08-18 | Buy-first puke | 69.4 | 16.1 | Cheap IV plus acceptable RR, CS 17.1, and -9.9% drawdown. | Buy Sep-18 17/22C for no more than $0.32. |
| UUUU | 08-20 | Buy-first puke | 71.4 | 0.0 | Overall IV is at the bottom of its yearly range; RR is buy-valid after a -9.0% drawdown, although CS 36.9 is nearer the cap. | Buy Sep-18 18/21C for no more than $0.14; the later $0.26 mark is near the 2x scale-out. |
| DJT | 08-18 | Buy-first puke | 65.9 | 37.8 | Moderate-high RR, acceptable IV, CS 28.2, and a deep -22.1% drawdown. | Buy Sep-18 10/13C for no more than $0.15. |
| QS | 08-18 | Buy-first puke | 61.5 | 9.2 | RR barely clears the floor, but very cheap IV and CS 21.0 strengthen the buy after an -8.7% drawdown. | Buy Sep-18 7/11C for no more than $0.15. |
| LCID | 08-17 | Buy-first puke | 61.9 | 11.2 | RR clears the floor, IV is cheap, CS 24.6, and drawdown is -23.6%. | Buy Sep-18 8/12C for no more than $0.12. |
| LWLG | 08-18 | Buy-first puke | 67.9 | 29.3 | Buy-valid RR and cheap IV after a -17.9% drawdown; CS 38.9 is close to the cutoff, so this is lower quality. | Buy Sep-18 8/13C for no more than $0.45. |
| LMND | 08-19 | Buy-first puke | 64.3 | 0.0 | IV is at the bottom of its yearly range, RR clears the floor, CS 31.7, and drawdown is -17.8%. | Buy Sep-18 65/70C for no more than $0.20. |
| INTC | 08-19 | Buy-first puke | 65.1 | 40.5 | RR and CS 34.1 are buy-valid after a -10.6% drawdown; IV is moderate rather than exceptionally cheap. | Buy Sep-18 125/130C for no more than $0.22. |
| PGY | 08-19 | Buy-first standard | 61.1 | 4.0 | Very cheap outright IV plus buy-valid RR and CS 29.4; unlike the puke names, its technical/relative-strength overlay was constructive. | Buy Sep-18 25C at up to $0.30, then rest a sale of the 26C at $0.40 to create the spread. |
| MSTR | 08-20 | Sell-first grab | 0.0 | 54.9 | RR is at its yearly floor while CS is 99.2; front call wing 96.4 and kink 88.9 confirm extreme local upside richness. Overall IV is midrange, not a cheap-vol buy. | Original plan: sell Aug-28 150C at $0.32 or better, then rest a buy of the 145C at $0.22. The breakout stop subsequently triggered, so cover/cap rather than initiate or add now. |

The buy-first puke tickets are entered as complete debit spreads because the exception
is designed for cheap, high-convexity rebound exposure. PGY uses the standard leg-in:
own the roughly 15-delta call first, then sell the adjacent upper call into strength.
MSTR reverses that order because the far call wing was the expensive instrument, but
the first leg is temporarily naked and therefore requires the breakout stop.

## Chain-confirmed finalists and observed marks

The table uses signal-close quotes for ticket selection and later close quotes for the
observed mark. Long spreads are valued conservatively as `max(long bid - short ask, 0)`.
For the standard leg-in, P&L is the still-unpaired long call. For sell-first, P&L is the
unpaired naked short marked at the ask. A close-cross is a conservative fill proxy; lack
of one does not rule out an intraday fill.

| Branch | Signal | Ticker | Exact ticket | Initial cash | Latest through 08-21 | Read |
|---|---|---|---|---:|---:|---|
| Puke buy | 08-14 | **BTDR** | Sep-18 11/16C | $0.45 debit | **$1.00 / 2.22x** | Demonstrated hit; scale-out zone |
| Puke buy | 08-20 | **UUUU** | Sep-18 18/21C | $0.14 debit | **$0.26 / 1.86x** | Fast hit, just below 2x |
| Puke buy | 08-19 | **LMND** | Sep-18 65/70C | $0.20 debit | **$0.25 / 1.25x** | Above cost after two closes |
| Puke buy | 08-18 | **DJT** | Sep-18 10/13C | $0.15 debit | **$0.17 / 1.13x** | Modestly above cost |
| Puke buy | 08-20 | RDW | Sep-18 15/20C | $0.30 debit | $0.25 / 0.83x | Slightly below cost; one close |
| Puke buy | 08-20 | BB | Sep-18 10/13C | $0.10 debit | $0.06 / 0.60x | Below cost; one close |
| Puke buy | 08-18 | NVTS | Sep-18 17/22C | $0.32 debit | $0.19 / 0.59x | Below cost after three closes |
| Puke buy | 08-18 | QS | Sep-18 7/11C | $0.15 debit | $0.08 / 0.53x | Below cost after three closes |
| Puke buy | 08-19 | INTC | Sep-18 125/130C | $0.22 debit | $0.09 / 0.41x | Below cost after two closes |
| Puke buy | 08-18 | LWLG | Sep-18 8/13C | $0.45 debit | $0.10 / 0.22x | Below cost after three closes |
| Puke buy | 08-20 | ASX | Sep-18 47.5/50C | $0.20 debit | $0.00 / 0.00x | Wide exit after one close |
| Puke buy | 08-17 | GRPN | Sep-18 26/31C | $0.35 debit | $0.00 / 0.00x | Wide exit after four closes |
| Puke buy | 08-17 | JD | Oct-16 36/41C | $0.11 debit | $0.00 / 0.00x | Wide exit after four closes |
| Puke buy | 08-17 | LCID | Sep-18 8/12C | $0.12 debit | $0.00 / 0.00x | Below cost after four closes |
| Puke buy | 08-21 | **SOUN** | Oct-16 9/14C | $0.31 debit | no later close | Fresh, unresolved setup |
| Standard buy | 08-19 | **PGY** | BTO Sep-18 25C @ $0.30; rest 26C @ $0.40 | $0.30 long | long bid $0.35; upper bid $0.25 | Valid but still unpaired |
| Sell-first | 08-20 | **MSTR** | STO Aug-28 150C @ $0.32; rest BTO 145C @ $0.22 | $0.32 credit | short ask $0.50; **-$18** | Unpaired; breakout tell active |

The ten buy-first spreads still below cost had only one to four observed closes and
30--64 DTE at entry. They are unresolved, not declared failed. Conversely, BTDR's 2.22x
mark is an available scale-out, not evidence that holding to expiry is optimal.

## The sell-first result: MSTR is a warning, not a green light

MSTR produced the cleanest NVDA-like spot-up/vol-up grab in the universe:

- 2026-08-20 spot $112.06, up 14.4% in five sessions and at its 20-day high;
- RR25 at the 0th percentile and 25-delta call skew at the 99.2nd percentile;
- front 5-delta call wing at the 96.4th percentile and kink at the 88.9th;
- IV Rank 54.9 and average option volume about 397,000 contracts;
- Aug-28 150C (4.3 delta) quoted 0.32 x 0.38 with OI 2,474; its IV was 28.3
  vol points above same-expiry ATM.

But the tape kept squeezing. By the next close MSTR was $119.14, the 150C was
0.47 x 0.50, and the nearer 145C was 0.65 x 0.71 rather than filling at $0.22.
The naked short was down $18 per contract at the ask. The earlier 08-19 140C signal
was worse: 0.24 bid at signal versus 1.00 ask on 08-21, or -$76 before fees.

This is exactly P1's named breakout failure. Wing percentile rose while spot moved
more than 5% toward the strike, so the breakout-stop variant says cover or cap it.
The conclusion is: **MSTR is structurally suitable for the setup, but the observed
August episode says do not fade it mechanically and do not add a new naked short now.**

## The two useful buy-first reads

### 1. Buy-the-puke moon spreads

The strongest practical cohort is:

`BTDR, UUUU, LMND, DJT, RDW, BB, NVTS, QS, INTC, LWLG, ASX, GRPN, JD, LCID, SOUN`

These names met the puke exception (at least 8% below the 20-day high, RR at or above
the 60th percentile, call skew at or below the 40th, IV Rank at or below 65), passed the
strict aggregate liquidity gate, and had a two-sided 20--35%-OTM spread with adequate
per-leg OI. This is the Pandar-style branch: buy both legs cheaply and feed scale-outs
into a V. It is not the capital-heavy 15-delta leg-in.

### 2. Standard 15-delta buy-first

Only **PGY** survived. On 08-19 it had IV Rank 4.0, RR at the 61.1st percentile,
call skew at the 29.4th, and a Good surface/technical setup. The Sep-18 25C was
0.25 x 0.30 at 15.2 delta with OI 6,708; the next strike, 26C, was 0.15 x 0.20.
The prescribed resting sale was $0.40. By 08-21 PGY was up 5.5%, the long bid was
$0.35, but the 26C bid was only $0.25, so the bomb had not paired.

## Rejections that matter

- **COIN, LRCX, GS, KLAC, PSX, SMCI, CTSH and other sell-grab surface hits** failed
  the exact NVDA-style weekly requirement: the selected 2--6 delta call was below a
  $0.20 bid, wider than $0.10, lacked OI, or some combination. Their aggregate option
  volume did not make the actual tail ticket tight enough.
- **AMLX**, the only post-shock-smile surface candidate, had no usable far-call market.
- **XPEV, LI, CRML, KSS and several other buy-first names** were rejected because the
  selected expiry contained or was estimated to contain earnings.
- Many otherwise attractive buy-first surfaces had a dead upper call, insufficient
  per-strike OI, or more than $0.20 of combined leg width.

## NVDA control

The same calculations recover the known May 2026 NVDA grab: on 05-20 the abbreviated
available baseline put RR near the 2nd percentile, call skew and the front call wing
near the 98th, and kink near the 96th. That is directionally consistent with the
canonical full-history NVDA screen. In the requested window NVDA did not fire:

- 08-12: front call wing 75th percentile, below the 85 threshold;
- 08-21: front call wing 79th percentile, still below threshold; RR 6th and call skew
  94th continued to say calls were rich, not a buy-first puke.

## Limits

1. Signals use the ORATS close. The P1 spec enters at the next open; ticket selection
   here uses the signal-close chain as a tradability confirmation, not a simulated fill.
2. Follow-through uses EOD bid/ask only. A close-cross confirms a conservative fill;
   lack of one cannot exclude an intraday touch.
3. The observation window ends 2026-08-21. Most buy spreads have only one to four
   subsequent closes and remain unresolved.
4. The screen finds surface/chain analogs. It does not establish positive expectancy
   or safe naked-short sizing for a new ticker; that requires the full P1 lifecycle and
   stress backtest.

## Reproducible artifacts

- `scripts/single_name_call_screen.py` -- resumable fetch, causal screen, exact-chain
  selection, and conservative follow-through marks.
- `tests/test_single_name_call_screen.py` -- percentile, regime, alias, and contract
  selection tests.
- `docs/replay/single_name_call_screen_candidates.csv` -- all strict-liquid surface hits.
- `docs/replay/single_name_call_screen_chain_checks.csv` -- all exact-chain passes/fails.
- `docs/replay/single_name_call_screen_finalists.csv` -- one best confirmed row per
  ticker/scenario.
- `docs/replay/single_name_call_screen_outcomes.csv` -- observed close marks through
  2026-08-21.
- `docs/replay/single_name_call_screen_followup_paths.csv` -- daily mark path.

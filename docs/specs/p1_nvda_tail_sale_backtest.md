# Spec — P1 "Tail-sale book with buybacks" backtest, NVDA, 2023 → present

Version 0.1 · 2026-08-17 · owner: delta_bomb · status: draft for review

## 0. What this is and what decision it informs

P1 is PandarBear's core NVDA book as reconstructed from the PMTraders thread (§5f of `docs/delta_bombs.html`):
**sell a far-OTM option in the front expiry when that wing is unusually rich, sized to be held to expiry; immediately
rest a buy on the strike one notch nearer at (sale − c); if it fills you keep most of the premium and are left long a
$5-wide spread carried at a credit ("the free long spread"); if it never fills you hold the short to expiry.**

Decision this backtest informs (CIO memo, §10): whether P1 is promoted to paper-trading on NVDA, held as research-only,
or dropped. Pass/fail criteria are in §9. Nothing else (SPX legging, penny-spread inventory P2, the §5e 15Δ buy-first
structure) is in scope.

## 1. Universe and window

- Underlying: **NVDA only.**
- Signal history: ORATS daily surface 2018-01-02 → 2026-08-14 (thresholds are *fitted* on 2018–2022, *tested* on
  2023-01-03 → 2026-08-14). Trades are simulated only from **2023-01-03** forward (option quotes start there).
- Sessions: NYSE calendar. Signal evaluated at the close of day *t*; entry executed at day *t* 15:55 (EOD proxy) or,
  where 1-min data exist, at 15:55 exactly.
- 10:1 split 2024-06-10: all strikes and premiums are **normalized to post-split units** (pre-split ÷ 10; contract
  multiplier ×10 for P&L equivalence). ORATS `clsPx` is already split-adjusted; ThetaData quotes are as-traded and must
  be normalized in the loader.

## 2. Data

| Need | Source (all in `~/Dev/central_trade_data`) | Notes |
|---|---|---|
| Daily surface for the trigger | `orats/delta_bomb_refresh_2026-08-17/NVDA_cores.parquet` (+ `NVDA_ivrank`, `NVDA_dailies`) | fields below; corrupt tick 2025-04-04 (`iv30d`=381) filtered |
| Earnings dates | `orats/earnings/earnings_long.parquet` (`ticker==NVDA`, `earnDate`, `affected_trading_day`) | expiries containing an earnings date are **excluded** |
| Option quotes for entry / buyback / marks | **to acquire:** ThetaData `option/history/eod` for NVDA, every listed expiration with 1–35 DTE, 2023-01-03 → 2026-08-14 (close bid/ask, all strikes, both rights) — one call per expiration; est. ~190 calls, ~200 MB | store as `thetadata/nvda_p1_eod_<date>-v1/eod/NVDA_<exp>.parquet` + manifest; dictionary + changelog entries |
| Intraday fill validation | `thetadata/nvda_delta_bomb_1m_2026-08-17-v1/greeks/` (171 sessions, May–Aug 2026, 1-min NBBO) | used only to measure EOD-fill bias (§7) |

Fields (ORATS cores, all 10-day tenor unless noted): `iv10d`, `dlt5Iv10d` (5Δ call), `dlt95Iv10d` (5Δ put),
`dlt5Iv30d`, `dlt95Iv30d`, `iv30d`, `exErnIv30d`, `exErnDlt25Iv30d`, `exErnDlt75Iv30d`, `ivRank1y`, `clsPx`.
Convention: ORATS `dltXX` = IV at XX **call** delta.

## 3. Definitions

```
call_wing_10  = dlt5Iv10d  - iv10d            # front far-call wing over ATM (vol pts)
put_wing_10   = dlt95Iv10d - iv10d            # front far-put wing over ATM
call_kink     = dlt5Iv10d  - dlt5Iv30d        # front far-call vs 30d far-call
put_kink      = dlt95Iv10d - dlt95Iv30d
pct252(x)     = share of the prior 252 sessions with x below today's value (×100); min 126 obs
```
Ranks are computed on the raw 10-day series (there is no `exErn` variant of the 10-day wing fields); the earnings
exclusion in §5 handles the event ramp.

## 4. Trigger (evaluated at each close, per side)

- **Sell-put signal** at close *t* if `pct252(put_wing_10) ≥ P_thr` **and** `pct252(put_kink) ≥ K_thr`.
- **Sell-call signal** at close *t* if `pct252(call_wing_10) ≥ P_thr` **and** `pct252(call_kink) ≥ K_thr`.
- Baseline `P_thr = 85`, `K_thr = 70` (the values used in §8b/8c). These are **judgment values**; §8 sets them from
  the fitted distribution and reports the sensitivity grid.
- Cool-down: at most one new position per side per expiry; a new signal while a position on that side/expiry is
  open adds nothing.
- Regime tag stored with every signal: `ivRank1y`, `RR25_pct` (from the 30d ex-earn series), `clsPx` vs 50-day
  SMA, drawdown from 20-day high — for the regime splits, not for gating.

## 5. Instrument selection

- Expiry: the **nearest listed expiration with 5 ≤ DTE ≤ 12** at signal (front weekly; if none, nearest ≤ 19 DTE).
  Skip the signal if the chosen expiry contains an NVDA earnings date (`earnDate` ≤ expiry and `earnDate` ≥ t).
- Strike: the far option on the signalled side with **delta closest to 0.04 (|Δ| in [0.02, 0.06])** using the
  ThetaData EOD greeks if present, else the strike nearest **25% OTM**; must have bid ≥ 0.05 and ask−bid ≤ 0.10.
  Record moneyness (% OTM), delta, IV.
- Buyback strike: **one listed strike nearer to the money** (5.00 spacing above ~$180 post-split, 2.50 below; use the
  chain as listed). Record the width actually available.

## 6. Entry, buyback, exit

- **Entry (t, 15:55):** STO 1 far option at the **bid**. Fees: $0.65/contract (ToS) and $0.00 (Robinhood-style) both
  reported.
- **Resting buyback:** BTO 1 of the nearer strike, limit `L = sale − c`, `c ∈ {0.05, 0.10}` (baseline 0.10). Working
  from the next session's open until expiry.
- **Fill rule (EOD proxy):** fills on the first session *s > t* where close **ask** ≤ L, at price L. (Conservative:
  intraday touches are invisible; §7 measures the bias against the 1-min store.)
- **After a fill:** book = long nearer / short farther = a debit spread carried at credit `sale − L = c`. Hold to
  expiry; also record the daily bid-side value (sell nearer at bid, buy farther at ask) and its max, and the first
  session it reaches 1.00 / 2.00 / 3.00 (for a later "scale-out" variant; the baseline holds).
- **If never filled:** hold the naked short to expiry. Record daily mark (ask). Terminal = max(0, intrinsic).
- **Defensive rule (variant, not baseline):** if the far option's ask ≥ 3 × sale at any close, buy the strike one
  notch *farther* (synthetic spread) and stop. Report with and without.
- **Expiry settlement:** intrinsic from `clsPx` on the expiration date (equity options: physical; we treat as cash
  intrinsic).

## 7. Fill-bias check (mandatory)

For every P1 trade dated within the 1-min store's coverage (2026-05-04 → 2026-08-14), recompute the buyback fill with
1-min NBBO (`ask ≤ L` at any minute) and report: (a) fraction of trades where the 1-min fill occurs but the EOD rule
misses it, (b) mean days-to-fill EOD vs 1-min, (c) P&L difference. This scalar is applied as a stated caveat to
the 2023–2026 EOD results, not as an adjustment.

## 8. Threshold fitting and sensitivity

- Fit window 2018–2022 (surface only, no trades): choose `P_thr, K_thr` as the pair maximizing the *ex-post* 5-session
  wing-crush (fall in `*_wing_10` from t to t+5) subject to ≥ 12 signals/year/side. Report the objective surface;
  if the maximum is flat, keep the baseline 85/70 and say so.
- Test window 2023-01-03 → 2026-08-14 with the fitted thresholds only.
- Sensitivity grid reported (test window): `P_thr ∈ {75, 85, 90}`, `K_thr ∈ {50, 70, 85}`, `c ∈ {0.05, 0.10}`,
  target |Δ| ∈ {0.03, 0.04, 0.06}, DTE band ∈ {5–12, 8–19}. Fees on/off.

## 9. Metrics and pass criteria (from the CIO memo)

Per side and combined, test window:

1. Signals per month; trades per month after exclusions.
2. Buyback fill rate within 5 sessions; median credit kept (`sale − L` at fill, i.e. `c`) and median premium
   collected (`sale`).
3. Distribution of **unfilled** trades: count, days held, terminal P&L, worst single, and their mark-to-market path.
4. P&L per contract: mean, median, worst month, worst 12-month rolling; hit rate.
5. **Free-spread payoff:** of spreads left after a fill, how many finished ITM (any intrinsic) and how much; the
   distribution of max bid-side value before expiry (the "sell the inflation" opportunity).
6. Regime split: 2023 (trend), 2024-H1 (grind), 2024-H2 → 2025 (chop, two shocks: 2024-08-05, 2025-01-27, and the
   Apr-2025 crash), 2026 (grind + May blow-off).
7. Fee sensitivity: results at $0.65 and $0.00 per contract.

**Pass (→ promote to paper-trading):** in the test window, on the baseline settings, (a) fill rate within 5 sessions
≥ 60%, (b) worst rolling-12-month P&L ≥ −0.5 × trailing-12-month median income, (c) results at $0.65 fees remain
positive in ≥ 3 of the 4 regimes, (d) the fill-bias check does not flip the sign of any regime.
**Hold research-only:** any of (a)–(d) fails but the combined P&L is positive.
**Stop:** combined P&L negative at $0.00 fees, or the unfilled tail alone exceeds total income in the test window.

## 10. Sizing note (out of scope for pass/fail, reported)

All results are per 1 contract. Report the notional at risk per trade under Pandar's stated rule (loss if the stock
goes to zero on puts / doubles on calls ≤ 10% NLV) for a $250k and a $1M account, i.e. the contract count that rule
allows, so the per-contract P&L can be scaled honestly.

## 11. Deliverables

- `scripts/p1_fetch_eod.py` (acquisition + manifest + dictionary/changelog entries), `scripts/p1_backtest.py`
  (signals → trades → metrics), `docs/replay/p1_trades.csv`, `docs/replay/p1_summary.md`, and a section §11 in the
  report with the tables above.
- Every number in the deliverable is reproducible from the store with one command.

## 12. Non-goals

- No SPX; no P2 (penny-spread inventory); no §5e buy-first calls; no intraday planting; no portfolio-level margin
  simulation (PNR) beyond the sizing note; no optimisation of exit timing (the scale-out variant is recorded, not
  optimised).

## 13. Open questions for review

1. Is `|Δ| ≈ 0.04` in the 5–12 DTE weekly the right instrument, or should the far option be defined by moneyness
   (25–40% OTM) as Pandar describes ("$5-wide under $0.10", "80P with the stock at 135")?
2. Is "one strike nearer" always the right buyback, or should the buyback be "the nearest strike whose ask ≤ L"
   (which is what a resting ladder of bids would actually do)?
3. Should the trigger require the *other* wing to be non-extreme (i.e. a genuine one-sided grab) or accept both-wing
   blow-outs (post-shock smile, Jan 31 2025)? Both are Pandar sales in the record.
4. EOD fill proxy: is a "close ask ≤ L" rule too conservative to be decision-useful, given the 1-min store shows the
   fills are gap-open events?

## 14. Review — Charlie McElligott (2026-08-17)

Bottom line: the object is right — the SELL side of Pandar's book, buyback as the profit-take, no paper toys. Changes
required before code:

1. **Fill proxy.** Buybacks fill on the gap (§5b/5d: 09:31–10:25). Use ThetaData EOD **low** ≤ L as the fill test,
   close-ask as the conservative bound; report both; §7 1-min check decides which is truth.
2. **Split the two sell archetypes at the trigger.** (a) spot-up/vol-up grab: wing pct ≥ 85 AND that side's
   RR extreme (calls: RR25 pct ≤ 10; puts: ≥ 90) AND spot moving that way; (b) post-shock smile: both wings ≥ 85,
   `iv10d` pct ≥ 80. Tag every trade a/b; split every metric. (a) fails as a breakout, (b) as a second leg.
3. **2023 = squeeze stress test.** Report the sell-call tail there as the headline risk, not averaged. Add a gap
   scenario (overnight ±15% through the strike, per contract, at the 10%-of-NLV rule) to §10.
4. **Breakout stop as a named variant:** after entry, if wing pct rises further AND spot has moved ≥ 5% toward the
   strike → cover / synthetic-spread. Report with/without.
5. **Instrument:** keep |Δ| 0.04 / 5–12 DTE; record moneyness and dollar premium; add a 25–40% OTM moneyness variant
   to §8's grid.
6. **Threshold objective:** fit on ex-post 5-session P&L of the short (premium − mark), not wing-crush alone.
7. **Counterfactual (mandatory):** same signals held naked to expiry, no buyback.
8. **Earnings:** also exclude the session before the print on the call side.
9. **Not modelable here, say so:** dealer gamma / call-OI stacking (the amplifier for (a)).

Disposition: incorporate 1–8 into v0.2 (fill rule, archetype tags, stress section, breakout variant, moneyness grid,
P&L objective, counterfactual, earnings rule); 9 becomes a stated limitation.

## 15. In plain terms — what review points #2 and #4 mean

### 15a. For the CIO

**#2 — "split the two archetypes."** The screen says "the far wing is unusually expensive, sell it." But there are two
different reasons a far wing gets expensive, and they fail in opposite ways:

- **(a) The grab.** The stock is ripping and the crowd is paying up for far *calls* only (or, mirror image, dumping and
  paying up for far *puts* only). One side of the smile is lifted; the other is not. If we sell that side and it keeps
  going, the loss is a *breakout*: the stock runs at our strike and the option we sold at 60¢ is worth $3–5.
- **(b) The post-shock smile.** Something just happened (DeepSeek, a tariff headline); *both* far wings are expensive
  because everyone is paying for lottery tickets in both directions and overall vol is very high. If we sell the far
  call here and it fails, it isn't a breakout — it's a *second leg down* (our sold call is fine; it's the naked put we
  might also have sold that hurts, or the portfolio around it).

Same order ticket, different disaster. If we throw both kinds of trade into one P&L column, the many quiet
post-shock sales (b) will produce a healthy-looking average that hides the few (a) trades that blow up in a melt-up.
So: stamp each trade "a" or "b" at entry using the surface (a = that side's wing high AND that side of the
risk-reversal at its extreme AND spot moving that way; b = both wings high AND overall front vol high), and report
every statistic for a and b separately. Decision consequence: we might promote (b) and shelve (a), or size them
differently — we cannot know unless they're separated.

**#4 — "the breakout stop."** Pandar's protection was *sizing*: sell few enough that if the stock reaches the strike
you can hold to expiry. Fine for a $1M PM account; brutal in a 2023-type melt-up. The variant adds a *tell*: after
we sell, if the wing keeps getting *more* expensive AND the stock has already moved 5% toward our strike, that's no
longer a grab that will fade — it's a trend — so we cover (or buy a further-out option to cap it). We run the
backtest both ways. The difference between the two P&Ls is the *price of the tell*: what we give up in premium
(covering grabs that would have faded) versus what we save in the ones that didn't. If the tell costs more than it
saves, we drop it and keep sizing as the only defence; if it saves more, it becomes part of the rule.

### 15b. From first principles

Look at what you actually sold: a ticket that pays only if NVDA is above, say, 300 in two weeks. You sold it for 62¢
because on that day people were unusually eager to own it. Now ask *why* they were eager — because there are two very
different reasons, and the reason tells you what can go wrong.

Reason one: the stock has been screaming higher for a week and buyers are chasing *up* — they want the far calls and
they don't care about the far puts. That is a crowd leaning one way. It usually tires; the ticket goes back to 11¢
and you keep 50¢. But sometimes the crowd is right and the stock keeps running, straight at your 300 line — then the
ticket you sold for 62¢ becomes worth $3, $5, more. Reason two: something scary just happened, prices are jumping
around, and people are buying far tickets in *both* directions — up and down — because they simply don't know. That
crowd isn't leaning; it's flinching. Your far-call ticket almost always dies quietly here, because a scared market
rarely runs 27% higher in two weeks; the danger from a flinching market is the *other* direction. Same 62¢ ticket,
sold into two different crowds, with two different ways of losing. If you pour both into one jar and average, the
many quiet flinch-sales make the jar look calm, and the rare leaning-crowd sale that ran you over is invisible in
the average — until it isn't. So we label each sale by which crowd we sold to, and we look at the two jars
separately. That is all #2 says.

#4 is about what to do when the leaning crowd turns out to be right. The stock keeps going and the far tickets get
*more* expensive, not less — that combination is the market telling you "this isn't a mood, it's a move." Pandar's
answer was to sell so few tickets that being run over doesn't matter. Ours can be the same, plus one rule: if the
tickets are still getting pricier and the stock has already covered a third of the distance to your line, buy the
ticket back (or buy the next one out to cap it) and stop arguing. Then measure it. Some grabs you cover would have
faded — that's the cost of the rule; some wouldn't — that's its benefit. The backtest reports both numbers so the
rule earns its place or doesn't. The simplification: "5% toward the strike" and "wing still rising" are one
reasonable definition of "this is a move"; the test may show a different line is better, and if no line beats
"just size small," that's a real answer too.

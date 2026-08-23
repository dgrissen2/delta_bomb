# Proposal — v3.0 "Real resting-limit fills" (spec/design/task deltas)

*Drafted 2026-08-23 from the option-midpoint repricing of the 19 rehearsal
trades. GOAL (user): every completed bomb nets **+0.10 ($10) by construction**
— the second leg RESTS at a 0.10 net credit vs the first leg's actual fill and
the system only counts a bomb when that limit demonstrably fills on the
option's own 1-minute data. No more "SPX moved 3 points so we assume done."*

## 0. Why (evidence)

- Repricing all 15 completed rehearsal bombs at real SPXW chain mids: average
  legging cost **$46/bomb** (range −$45 credit to +$120), not ~$0. A 3-pt SPX
  move shifts a 20Δ put ~0.6 while stepping 5 strikes shifts it ~1.0 — the
  touch proxy structurally overstates completion economics by ~0.4–0.5 pts.
- Data feasibility (probed 2026-08-23): these strikes TRADE in ~6 of 391
  minutes → **trade-OHLC cannot be the fill test**. 1-min NBBO quotes exist
  every minute (ThetaData SDK, verified) → **quote-based fill** is the faithful
  mechanic: a resting BUY limit at L is filled in minute m iff ask(m) ≤ L; a
  resting SELL limit at L iff bid(m) ≥ L. (Marketable-against-us = guaranteed
  fill; no queue-position assumptions.)
- Historical SPXW 1-min chains ARE available via the ThetaData SDK (greeks
  incl. bid/ask/delta; verified across all 8 sessions) — the spec's standing
  premise "no stored chain exists for backtests" (R2.5) is obsolete.

## 1. The new mechanic (normative once adopted)

1. **Leg 1 (entry)** executes at the NEXT bar (unchanged timing, R1.4). Price =
   the option's 1-min NBBO at the execution minute, CONSERVATIVE side:
   sell-first sells K at the **bid**; long-first buys K at the **ask**.
   (Mid is a sensitivity diagnostic, never the booked price.)
2. **Leg 2 rests immediately** at the 0.10-credit limit:
   sell-first → BUY K+5 limit **L = fill1 − 0.10**;
   long-first → SELL K−5 limit **L = fill1 + 0.10**.
3. **Fill detection, each completed minute** (backtest and live, one code
   path): BUY limit filled iff ask(K+5, m) ≤ L; SELL limit filled iff
   bid(K−5, m) ≥ L. Booked at L. Completed bomb = 5-wide spread + **+0.10
   credit, by construction**.
4. **Everything else about the trade unchanged**: entry signals (R6), vetoes
   (R4), windows (R5), scratch/veto/state-flip/clock/resolution (R7) still
   govern the lone leg; exits now BOOK at the lone leg's conservative NBBO
   (buy back at ask / sell out at bid) so scratch/timeout losses are real
   dollars, not SPX-point proxies.
5. **Strike selection in backtests becomes real** (R1.2): −0.20Δ from the
   historical chain at signal time, constrained to strikes where the 5-wide
   partner is listed (observed grid: 10s with 5s at 25-pt anchors).

## 2. Spec deltas (requirements.md v3.0)

| Rule | Change |
|---|---|
| R1.2 | Backtests use the historical chain for strike selection (drop "no chain in backtests"); tie-breaks unchanged |
| R1.4 | REPLACE the ±3.0 touch proxy with §1 above (leg-1 NBBO fill + resting limit + quote-fill test). The 3-pt touch is retired from fills; it survives ONLY inside R11.4/R11.5 matched controls where noted below |
| R2.5 | Rewrite: historical SPXW 1-min chain (ThetaData SDK) is a REQUIRED backtest input for full tier; live chain = same SDK snapshot path (spike required) with Schwab as fallback; cache under `~/Dev/central_trade_data/thetadata/spxw_bomb_chains/` (strike-windowed, manifest-hashed, per central-data rules) |
| R7.1 | Fill = the resting limit filling per §1.3; minutes-to-fill = minutes from entry to the fill minute |
| R7.2/R7.4 | Unchanged conditions; exit BOOKING at conservative NBBO |
| R7.3 | Cap: option-mid trigger becomes computable in backtests (real mids); spot proxy retained only where chain data is missing (logged) |
| R7.6 | Implied debit test becomes real in backtests (ask(K+5) − fill1 etc.) |
| R8.1 | Event rows gain: leg1_fill, limit_price, leg2_fill, quote_ts columns (schema_v=2) |
| R9 | Thresholds MUST be re-registered: fill under limit semantics is strictly harder than the 3-pt touch. Process: run the v3.0 rehearsal ONCE over the 8 stored sessions, set B/A fill-rate thresholds and sample minimums from it in one sitting, freeze (no iteration — anti-overfit discipline), new CONFIG_HASH, clock resets (has not started) |
| R11.4/R11.5 | Controls re-specified as: same clock/midpoint matching, indicator = "would a limit placed per §1 at that minute have filled within the horizon" computed from the cached chains. (The SPX-touch indicator is retired with R1.4) |
| R12 | New verification artifact v2: the first clean v3.0 rehearsal trade list is reviewed row-by-row (spot-check legs against raw quotes), then hash-pinned like R12.1. R12.1 + the existing golden gate REMAIN (they verify the ported research core, which is untouched) |
| R13.1 | full tier now requires HIRO + SPX + chain cache per date; **price tier keeps the old ±3 SPX touch** as a coarse screen (no chains for the 2022+ archive at acceptable cost), stamped `tier=price` as always — price-tier numbers were already quarantined from full-rule claims |
| R13.2 | Sweep whitelist gains exactly one knob: `credit` {0.05, 0.10, 0.15, 0.20} (the resting-limit offset). Nothing else |

## 3. Design deltas (design.md v2)

- **New module `chains.py`**: `ChainStore` — fetch-on-demand + local cache of
  SPXW 1-min NBBO/greeks per (date, expiry, strike window around the day's
  entries); manifest with sha256s; DATA_DICTIONARY/CHANGELOG updates. The ONLY
  module that talks to the option endpoints (live snapshots included).
- **Executor**: `SimTrade` gains leg1_fill, limit_price, leg2_fill;
  `execute_pending` books leg 1 from ChainStore quotes; per-bar `apply` asks
  ChainStore "limit filled this minute?"; exits book at conservative NBBO.
  Executor stays a pure state applier — quote lookups behind a `QuoteView`
  protocol so replay and live share the code path.
- **RuleEngine untouched** except the fill condition moves out: rules no longer
  detect fills from SPX bars; the Executor reports fills (rules keep exit
  precedence for everything else). One owner per concern, as before.
- **FeatureEngine untouched.** Signals are HIRO/tape; options are pricing.
- **Scorecard/controls**: fill/pnl definitions read the new columns; control
  functions consume the chain cache; day-clustered bootstrap unchanged.
- **Explicitly NOT built**: order-book queue modeling, partial fills,
  multi-lot, smart routing, intra-minute quote interpolation.

## 4. Task deltas (tasks.md v2 — new tasks 13–18)

- [ ] 13. ChainStore: fetch/cache/manifest + loaders; store the 8 rehearsal
      sessions' strike windows; central-data docs updated. Tests: cache hit
      determinism; hash guard; missing-date refusal (R13.1).
- [ ] 14. Pricing layer: leg-1 NBBO booking, resting limit, quote-fill test,
      NBBO exit booking; schema_v=2 events + round-trip/crash-resume updates.
      Tests: table-driven fill/no-fill minutes incl. limit==ask boundary;
      credit arithmetic (+0.10 by construction); one leg at a time preserved.
- [ ] 15. Scorecard/controls/summarizer on v3 semantics; R11.4/11.5 limit-fill
      controls; golden fixture updated by hand.
- [ ] 16. v3.0 rehearsal over the 8 sessions → ONE-SITTING threshold
      re-registration (R9) → spec numbers frozen → verification artifact v2
      generated, reviewed, hash-pinned.
- [ ] 17. Live chain snapshot SPIKE (market hours): minutely SDK snapshots of
      2 strikes — latency/coverage; STOP if it fails (Schwab fallback design).
- [ ] 18. Re-run full battery + reviews; RUNBOOK/ops updates (chain cache
      freshness in morning check).

## 5. Open decisions (for architect/PM below)

A. NBBO conservatism: leg-1 at bid/ask (proposed) vs mid — affects whether the
   +0.10 is real-world-credible or paper-flattering.
B. Fill test tick tolerance: ask ≤ L (proposed) vs ask < L.
C. Do we keep logging the SPX ±3 touch as a diagnostic column (proposed: yes,
   it is the bridge to all prior research)?
D. R9 threshold re-registration numbers — set from the v3.0 rehearsal in one
   sitting (proposed) — PM to confirm the anti-overfit protocol.

---

## 6. Architect × PM review (2026-08-23) — findings APPLIED above where noted

**Architect (simple/DRY/robust, no overengineering):**
1. **Executor must stay I/O-free.** The draft had the Executor querying
   ChainStore. Corrected: Session fetches the minute's two-strike NBBO and
   attaches it to the tick (exactly like vetoes/health); the Executor consumes
   attached quotes. Replay and live share one code path; fixture quotes make
   the pricing layer table-testable. (§3 amended.)
2. **Schema v2 is ADDITIVE**: new columns appended, `schema_v=2` stamped,
   reader accepts v1 rows (old logs stay parseable); crash-resume and
   console==CSV tests regenerate against v2.
3. **Cache scope precisely**: (a) full-chain snapshot at SIGNAL minutes only
   (for the −0.20Δ pick), (b) full-day 1-min NBBO for the two chosen strikes
   only. No whole-chain full-day hoards. (Task 13 amended.)
4. **Live-quotes hard gate**: task 17 must prove ONE of (i) SDK live option
   snapshots or (ii) Schwab chain quotes at 1-min cadence. If neither works,
   v3.0 CANNOT go live — there is no spot-proxy fallback for fills, because
   that would fork live vs backtest semantics (the sin this upgrade removes).
5. **NBBO timing convention pinned**: the fill test uses the minute's NBBO as
   served by the 1-min series; live uses the post-bar-close snapshot. Same
   convention both paths, documented once.
6. **TierPolicy gains one field** (`fill_mode: limit | spot_touch`) instead of
   scattered conditionals; price tier = spot_touch (quarantined as ever).

**PM (risk & governance):**
1. **Conservatism is the product.** Endorse leg-1 booking at bid/ask (never
   mid) and fill test `ask ≤ L` / `bid ≥ L` (marketable = guaranteed). Limit
   prices round to valid ticks AGAINST us (down for buys, up for sells) —
   these puts trade on a 0.10 grid, so the credit knob is {0.00, 0.10, 0.20,
   0.30} (tick-valid; 0.00 = any-credit baseline). (§2 R13.2 amended.)
2. **Unfilled-leg risk becomes the dominant risk** under limit semantics (more
   lone legs ride to clock/resolution). R9 re-registration MUST add two
   pre-registered risk lines in OPTION dollars: median unfilled-leg realized
   loss, and a max single-trade loss cap analogue. Numbers set in the same
   one sitting as the fill thresholds.
3. **Mechanical threshold derivation (anti-overfit)**: pre-commit the criteria
   FORM first (same structure as today's R9); then derive numbers from the
   v3.0 rehearsal by a stated rule — floor = point estimate minus one
   day-clustered bootstrap SD, rounded down to 0.05 — no judgment pass, no
   second look. (Task 16 amended.)
4. **The $10 is the floor, not the objective.** The bomb's value is the owned
   spread (max $500/lot); no criterion may reward avoiding completion. The
   scorecard reports credits captured AND spreads planted, together.

**Joint verdict: APPROVED to proceed to red-team + codex-plan-review** with the
amendments above. Scope is judged proportionate: one new data module, a
pricing layer swap, scorecard re-derivation, two market-dependent spikes; the
signal engine (features/rules) is untouched.

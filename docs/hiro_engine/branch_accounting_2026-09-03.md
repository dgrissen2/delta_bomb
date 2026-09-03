# Branch A / Branch B — full accounting across every session tried (as of 2026-09-03)

**Scope:** all 16 sessions run through the frozen v3.0 engine (CONFIG_HASH `80c3a41026c8…`):
the 8 frozen in-sample/rehearsal sessions (2026-08-12→08-21, the R11.4 control set) and
the 8 out-of-sample sessions (2026-08-24→09-02; 7 countable + 08-31 event_standdown).
Sources: `docs/replay/hiro/paper_log_backtest.csv` (frozen 8, full tier) and the five
`paper_log_oos_*.csv` logs. Real closing-NBBO fills, 1-lot, $ = ×100. Every session was
identity-verified (HIRO basket px vs SPX 1-min, cross-day winner, median < 1 pt).

**What the two branches are.** Both build the same thing — a 5-wide SPX put vertical held
for a +$0.10 credit ("a planted bomb": worth up to $500 if SPX falls through the strikes,
costs nothing to hold). **Branch A = buy-first** (buy the ~20Δ put on a negative-flow
dip, rest the SELL of K−5 at cost+0.10; bets the DOWNSWING resumes). **Branch B =
sell-first** (sell the ~20Δ put into a strong positive put-selling run, rest the BUY of
K+5 at sale−0.10). A failed attempt (no fill in 60 min / scratch / veto) closes the lone
leg — that is where every loss comes from.

## 1. Scorecard

| set | branch | entries | fills | fill rate | timeouts | scratch | veto_exit | credits | losses | **net $** | worst | median fill (min) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IN (8) | A | 13 | 8 | 0.62 | 5 | 0 | 0 | +80 | −480 | **−400** | −290 | 18.5 |
| IN (8) | B | 6 | 2 | 0.33 | 0 | 2 | 2 | +20 | −290 | **−270** | −100 | 30.5 |
| OOS (8) | A | 9 | 5 | 0.56 | 4 | 0 | 0 | +50 | −440 | **−390** | −300 | 15 |
| OOS (8) | B | 1 | 1 | 1.00 | 0 | 0 | 0 | +10 | 0 | **+10** | +10 | 12 |
| **ALL** | **A** | **22** | **13** | **0.59** | 9 | 0 | 0 | +130 | −920 | **−790** | −300 | 16 |
| **ALL** | **B** | **7** | **3** | **0.43** | 0 | 2 | 2 | +30 | −290 | **−260** | −100 | 12 |
| **ALL** | both | 29 | 16 | 0.55 | 9 | 2 | 2 | +160 | −1,210 | **−1,050** | −300 | 15.5 |

Registered floors for reference (R9): a_fill_rate ≥ 0.55, b_fill_rate ≥ 0.10,
max_single_trade_loss $150. A sits ON its floor across all data (0.59 / 0.56 OOS); B is far
above its floor but on n=7. Two losses (−290 in-sample, −300 OOS) breach the $150 line —
both Branch A timeouts.

## 2. Signal pipeline — why B barely trades

| set | branch | signals | entries | blocked: vt_broken | blocked: levels_invalid | LATE (R6.3) | gate_fail | 3/day cap | one-leg-at-a-time |
|---|---|---|---|---|---|---|---|---|---|
| IN | A | 13 | 13 | — | — | 0 | 0 | 2 | 8 |
| IN | B | 6 | 6 | 19 | 0 | 6 | 19 | 2 | 3 |
| OOS | A | 9 | 9 | — | — | 0 | 0 | 3 | 7 |
| OOS | B | 1 | 1 | 12 | 2 | 8 | 8 | 1 | 3 |

B's constraint is OPPORTUNITY, not execution: 33 sell-first setups were refused across the
16 sessions (31 by the below-Vol-Trigger rule R4.1, 2 for missing levels) and 14 more were
LATE-suppressed. B has been legal on only a handful of mornings. Whether those refusals
saved money is UNTESTED (the blocked-B counterfactual is the review's priority-3 item).

## 3. Every trade

| set | date | time | br | legs | exp | leg1 | limit | r30@sig | outcome | min | exit | adverse | P&L $ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IN | 2026-08-12 | 10:15 | B | 7475/7480 | 09-11 | 35.1 | 35.0 | — | fill | 10 | 35.0 | 1.3900000000003274 | +10 |
| IN | 2026-08-12 | 10:48 | B | 7520/7525 | 09-11 | 40.9 | 40.8 | — | scratch | — | 41.7 | 4.0700000000006185 | -80 |
| IN | 2026-08-12 | 11:35 | B | 7475/7480 | 09-11 | 35.5 | 35.4 | — | fill | 51 | 35.4 | 3.449999999999818 | +10 |
| IN | 2026-08-13 | 10:42 | A | 7575/7570 | 09-11 | 37.5 | 37.6 | -0.79 | fill | 22 | 37.6 | 0.9200000000000728 | +10 |
| IN | 2026-08-13 | 11:20 | A | 7530/7525 | 09-11 | 33.5 | 33.6 | -1.39 | fill | 8 | 33.6 | 0.7699999999995271 | +10 |
| IN | 2026-08-13 | 11:36 | A | 7530/7525 | 09-11 | 36.1 | 36.2 | -3.03 | timeout | — | 35.0 | 6.680000000000291 | -110 |
| IN | 2026-08-14 | 10:37 | A | 7575/7570 | 09-11 | 37.5 | 37.6 | -4.67 | fill | 38 | 37.6 | 1.699999999999818 | +10 |
| IN | 2026-08-14 | 11:37 | B | 7570/7575 | 09-11 | 38.7 | 38.6 | — | scratch | — | 39.7 | 2.600000000000364 | -100 |
| IN | 2026-08-14 | 13:13 | B | 7570/7575 | 09-11 | 38.1 | 38.0 | — | veto_exit | — | 38.7 | 5.479999999999563 | -60 |
| IN | 2026-08-17 | 11:52 | B | 7505/7510 | 09-18 | 40.7 | 40.6 | — | veto_exit | — | 41.2 | 2.740000000000691 | -50 |
| IN | 2026-08-17 | 13:43 | A | 7480/7475 | 09-18 | 41.8 | 41.9 | -0.75 | timeout | — | 40.9 | 2.25 | -90 |
| IN | 2026-08-18 | 11:04 | A | 7420/7415 | 09-18 | 42.8 | 42.9 | -0.90 | fill | 16 | 42.9 | 3.1799999999993815 | +10 |
| IN | 2026-08-19 | 11:20 | A | 7475/7470 | 09-18 | 39.5 | 39.6 | -0.74 | fill | 12 | 39.6 | 0.569999999999709 | +10 |
| IN | 2026-08-19 | 11:45 | A | 7465/7460 | 09-18 | 40.0 | 40.1 | -1.82 | timeout | — | 39.9 | 14.44000000000051 | -10 |
| IN | 2026-08-19 | 13:01 | A | 7460/7455 | 09-18 | 40.0 | 40.1 | -1.65 | fill | 21 | 40.1 | 2.990000000000691 | +10 |
| IN | 2026-08-20 | 10:51 | A | 7420/7415 | 09-18 | 40.8 | 40.9 | -0.18 | fill | 32 | 40.9 | 13.61999999999989 | +10 |
| IN | 2026-08-20 | 11:28 | A | 7415/7410 | 09-18 | 40.5 | 40.6 | -0.37 | fill | 8 | 40.6 | 3.3299999999999272 | +10 |
| IN | 2026-08-20 | 11:48 | A | 7405/7400 | 09-18 | 41.3 | 41.4 | -1.58 | timeout | — | 38.4 | 9.699999999999818 | -290 |
| IN | 2026-08-21 | 12:22 | A | 7430/7425 | 09-18 | 38.3 | 38.4 | -2.47 | timeout | — | 38.5 | 2.300000000000182 | +20 |
| OOS | 2026-08-25 | 10:46 | B | 7375/7380 | 09-25 | 39.9 | 39.8 | — | fill | 12 | 39.8 | 2.2100000000000364 | +10 |
| OOS | 2026-08-25 | 11:03 | A | 7380/7375 | 09-25 | 40.1 | 40.2 | -0.11 | timeout | — | 37.1 | 12.800000000000182 | -300 |
| OOS | 2026-08-26 | 10:37 | A | 7425/7420 | 09-25 | 42.6 | 42.7 | -1.83 | timeout | — | 42.1 | 10.340000000000146 | -50 |
| OOS | 2026-08-27 | 10:48 | A | 7475/7470 | 09-25 | 37.4 | 37.5 | -0.69 | timeout | — | 36.7 | 16.11999999999989 | -70 |
| OOS | 2026-08-28 | 11:19 | A | 7530/7525 | 09-25 | 34.4 | 34.5 | -0.14 | fill | 22 | 34.5 | 8.86999999999989 | +10 |
| OOS | 2026-08-28 | 11:55 | A | 7525/7520 | 09-25 | 37.8 | 37.9 | -4.78 | fill | 2 | 37.9 | 0.2600000000002183 | +10 |
| OOS | 2026-08-28 | 12:04 | A | 7480/7475 | 09-25 | 34.0 | 34.1 | -5.25 | fill | 15 | 34.1 | 5.530000000000655 | +10 |
| OOS | 2026-09-01 | 12:24 | A | 7375/7370 | 10-02 | 40.9 | 41.0 | -4.69 | fill | 4 | 41.0 | 0.1199999999998908 | +10 |
| OOS | 2026-09-01 | 12:40 | A | 7375/7370 | 10-02 | 43.6 | 43.7 | -5.67 | fill | 22 | 43.7 | 1.5700000000006185 | +10 |
| OOS | 2026-09-02 | 10:51 | A | 7425/7420 | 10-02 | 42.9 | 43.0 | -0.61 | timeout | — | 42.7 | 9.050000000000182 | -20 |

(r30@sig = 30-min HIRO flow at the signal minute, $B; blank for B, whose gate uses run/rate.
"timeout" with +20 on 08-21: the put appreciated but the resting sell never became marketable.)

## 4. The r30 "discriminator" — tested on all 22 A trades: FALSIFIED at −1.0

Conclusions §14 (2026-09-02) proposed that A wins when 30-min flow is deeply negative and
loses when it is thin, and the Charlie/codex review proposed a shadow gate at r30 ≤ −1.0 $B.
Two corrections after the full accounting:

1. **Labeling error:** the 08-26 loser had r30 = **−1.83** (I had reported only its r15,
   −0.44, and grouped it with the thin readings). It is a deep-r30 LOSS.
2. **On all 22 A trades the −1.0 split has NO discriminating power:**

| r30 at signal | n | fills | fill rate | net $ | worst | sessions |
|---|---|---|---|---|---|---|
| deep, ≤ −4.0 | 5 | 5 | **1.00** | +50 | +10 | 3 (08-14, 08-28, 09-01) |
| mid, (−4, −1] | 7 | 2 | **0.29** | −420 | −290 | 5 |
| thin, (−1, 0] | 10 | 6 | 0.60 | −420 | −300 | 9 |
| split ≤ −1.0 | 12 | 7 | 0.58 | −370 | | |
| split > −1.0 | 10 | 6 | 0.60 | −420 | | |

The relationship is non-monotonic: the MIDDLE bucket is the worst, the extreme tail is
perfect. That is the signature of a regime effect, not a flow-depth effect — the five
≤ −4 trades all came from three sessions where SPX was already falling hard (08-14,
08-28, 09-01). A Charlie-style r30 ≤ −1.0 shadow gate would have changed nothing.
**Status: the §14 hypothesis is withdrawn as stated.** What survives as a candidate is
narrower and needs its own pre-registration: "A only when r30 ≤ −4 $B" (n=5, 3 sessions,
zero losses — too thin to act on, but the right thing to shadow-track). The three
review-ordered shadow items (contemporaneous regime panel, per-branch credit ladder,
blocked-B counterfactual) stand.

## 5. Bomb inventory — every completed bomb still open, marked at the 2026-09-02 close

| set | planted | br | long/short | exp | mark $ |
|---|---|---|---|---|---|
| IN | 2026-08-12 | B | 7480/7475 | 09-11 | 45 |
| IN | 2026-08-12 | B | 7480/7475 | 09-11 | 45 |
| IN | 2026-08-13 | A | 7575/7570 | 09-11 | 95 |
| IN | 2026-08-13 | A | 7530/7525 | 09-11 | 70 |
| IN | 2026-08-14 | A | 7575/7570 | 09-11 | 95 |
| IN | 2026-08-18 | A | 7420/7415 | 09-18 | 90 |
| IN | 2026-08-19 | A | 7475/7470 | 09-18 | 65 |
| IN | 2026-08-19 | A | 7460/7455 | 09-18 | 90 |
| IN | 2026-08-20 | A | 7420/7415 | 09-18 | 90 |
| IN | 2026-08-20 | A | 7415/7410 | 09-18 | 55 |
| OOS | 2026-08-25 | B | 7380/7375 | 09-25 | 50 |
| OOS | 2026-08-28 | A | 7530/7525 | 09-25 | 180 |
| OOS | 2026-08-28 | A | 7525/7520 | 09-25 | 95 |
| OOS | 2026-08-28 | A | 7480/7475 | 09-25 | 80 |
| OOS | 2026-09-01 | A | 7375/7370 | 10-02 | 60 |
| OOS | 2026-09-01 | A | 7375/7370 | 10-02 | 60 |

| expiry | bombs | mark $ |
|---|---|---|
| 09-11 | 5 | 350 |
| 09-18 | 5 | 390 |
| 09-25 | 4 | 405 |
| 10-02 | 2 | 120 |
| **all** | **16** | **1,265** |

Marks are closing-NBBO mids (indicative — adjacent-strike inconsistencies like the 08-28
$180/$95 pair are quote noise that nets out). **All 16 are the same bet — SPX 7370–7575
by mid-September to early October, vs 7667 at the 09-02 close (1.2–3.9% below).** They pay
together or expire together.

## 6. The whole book, honestly

| | $ |
|---|---|
| credits banked (16 bombs × $10) | +160 |
| losses on 13 failed attempts | −1,210 |
| **realized cash** | **−1,050** |
| inventory mark (16 bombs) | +1,265 |
| **mark-to-market** | **+215** |

Read it this way: every $10 of credit costs, on average, $76 of failed-attempt losses
(13 fails × $93 avg). The strategy's cash P&L is negative by construction unless the
bombs pay — the whole edge is in the inventory, which is a single correlated position in
a September decline. The failure-cost side is what the pre-registered candidates target;
the inventory side resolves on the calendar (09-11 first).

## 7. Two adjustments tested (2026-09-03): $0.30 minimum credit, $150 hard stop

Offline counterfactual over all 29 trades using the chain caches; the frozen engine was not
touched. Mechanics: resting limit at leg1 ∓ credit (0.10 grid, rounded against us), fill =
minute closing-NBBO marketable from signal+2 through the 60-min clock; the stop closes the
lone leg at the conservative NBBO side on the first minute its mark-to-market loss reaches
the level. Flow exits (scratch / veto_exit) are kept at their recorded minutes. **Self-check:
at 0.10 / no stop the replay reproduces all 29 actual outcomes and fill minutes exactly.**

### 7.1 The 2×2

| scenario | fills | stops | credits | losses | **net $** | worst |
|---|---|---|---|---|---|---|
| baseline (0.10, no stop) | 16 | — | +160 | −1,210 | **−1,050** | −300 |
| 0.30 credit only | 15 | — | +450 | −1,180 | **−730** | −300 |
| $150 stop only | 13 | 10 | +130 | −2,050 | **−1,920** | −240 |
| both | 12 | 10 | +360 | −2,020 | **−1,660** | −240 |

### 7.2 $0.30 minimum credit: +$320, zero A fills lost — ADOPTED as the leading candidate

All 13 A fills still fill at 0.30 (A fill rate unchanged at 0.59); the only casualty is the
slowest B fill (08-12 11:35, 51 min), which becomes a +$30 timeout. Credits $160 → $450.
This confirms the in-sample "0.30 keeps every A fill" finding (conclusions §10) on the
full 22-trade A sample and adds out-of-sample support (5/5 OOS A fills held; the 08-25 B
fill held at 34 min). It is the one adjustment the data backs. Governance: it is R7.2
candidate (3); the frozen $0.10 stays live until the candidate is promoted through its
evidence bar — but the shadow ledger at 0.30 now runs alongside every session.

### 7.3 $150 hard stop: −$870 — REJECTED

The stop fires on 10 of 29 trades. It rescues the two big losers (−290 → −160, −300 →
−160; +$270) and pays for it by (a) **killing three winners** — 08-20 10:51, 08-28 11:19,
08-28 12:04 went ≥ $150 underwater and THEN filled (minutes 32/22/15) — and (b) inflating
five small timeouts (−10/−20/−50/−70/−90) into full −$150…−$170 stops.

Mechanism: A's fills come from volatility, and volatility means adverse excursion first.
Winners' max adverse excursion before the fill: $0–$100 for ten of thirteen, but **$160,
$180, $300** for the other three (23% of A winners). A $150 stop sits inside the working
range of the trade. Stop-level sensitivity with the 0.30 credit held: none −730 · $150
−1,660 · $200 −1,300 · $250 −1,470 · $300 −1,290 · $350 −730 (= the frozen 3.5-pt cap).
**No stop level below the existing cap improves the book.** The loss we want to cut (the
−$300 timeout) has the same early shape as the excursion a winner survives; a price stop
cannot tell them apart. The lever that can is entry selection (the regime panel), not a
tighter exit. Decision (user + engine, 2026-09-03): take the credit, not the stop.

### 7.4 Per-trade, both adjustments (Δ vs actual)

| date | br | actual | → new | Δ |
|---|---|---|---|---|
| 08-12 10:15 | B | fill +10 | fill +30 | +20 |
| 08-12 11:35 | B | fill +10 (51m) | timeout +30 | +20 |
| 08-13 ×2, 08-14, 08-18, 08-19 ×2, 08-20 11:28 | A | fill +10 | fill +30 | +20 each |
| 08-17 13:43 | A | timeout −90 | stop −170 | −80 |
| 08-19 11:45 | A | timeout −10 | stop −170 | −160 |
| 08-20 10:51 | A | fill +10 | stop −240 | −250 |
| 08-20 11:48 | A | timeout −290 | stop −160 | +130 |
| 08-25 10:46 | B | fill +10 | fill +30 (34m) | +20 |
| 08-25 11:03 | A | timeout −300 | stop −160 | +140 |
| 08-26 | A | timeout −50 | stop −150 | −100 |
| 08-27 | A | timeout −70 | stop −170 | −100 |
| 08-28 11:19 | A | fill +10 | stop −150 | −160 |
| 08-28 11:55, 09-01 ×2 | A | fill +10 | fill +30 | +20 each |
| 08-28 12:04 | A | fill +10 | stop −150 | −160 |
| 09-02 | A | timeout −20 | stop −150 | −130 |
| scratches / veto exits (4) | B | unchanged | unchanged | 0 |

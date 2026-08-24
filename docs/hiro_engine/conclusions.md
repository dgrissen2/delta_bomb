# hiro_engine — Conclusions & Learnings

*Running record of what the engine has established, in order of discovery.
Each entry states the evidence, the decision, and what remains open. Companion
docs: `requirements.md` (the frozen rules), `build_notes.md` (implementation
decisions), `bh_scratch_forensics_2026-08-23.md`, `registration.json`.*

---

## 1. HIRO is a thermometer, not a barometer (research phase, 2026-08-21/22)

Across 845 tape sessions and 8 HIRO sessions with matched controls: HIRO is
coincident with price (ρ≈0.7 same-minute, no 1–15-min lead). Every entry-side
"HIRO confirms the move" claim died under matched controls — EXCEPT the
negative-flow filter (below). Exit-side value (flow-shutoff, negative-flow
veto) survived every test in touch-semantics research. The engine exists to
test the surviving composition without human fudging.

## 2. The ±3-pt touch proxy overstated bomb economics by ~$50/bomb (2026-08-23)

Repricing all completed rehearsal bombs at real SPXW chain mids: the "free"
bomb legged in for ~$46 average at the 3-pt touch (a 3-pt SPX move shifts a
20Δ put ~0.6 while 5 strikes shift ~1.0). Trade prints are too sparse for
fill detection (6/391 minutes on a bomb strike); marketable 1-min NBBO is the
faithful mechanic. → spec v3.0: leg 1 books at conservative NBBO, leg 2 rests
at fill1 ∓ 0.10, a bomb exists only when that limit fills. Every completed
bomb now nets ≥ +$10 by construction.

## 3. Exit rules must be measured, never reasoned-by-analogy (BH scratch, 2026-08-23)

The Branch-A bounce-high scratch was authored as a "common sense" mirror of
B's researched flow-shutoff and shipped unbacktested. First honest test: 8/8
scratches would have filled, 38.1 pts surrendered, and it CREATED the only
adverse>10 event. Root cause: the exit watched the same variable as the entry
(the bounce), so it fired on the entry's own signature. → removed (v2.3);
standing rule now in the spec: no exit may trigger off its entry variable,
and nothing ships without a backtest showing it saves more than it costs.

## 4. The honest baseline: a random-minute $10-credit limit fills ~46% of the time

The v3 control frame (2,168 candidate minutes, 8 sessions): sell-first
baseline 0.470, long-first 0.454; weighted to actual entry clocks, B's
baseline is 0.583 (B trades in GOOD slots) and A's midpoint-matched control
is 0.500. Any claimed edge has to beat THESE numbers, not the old 0.77 touch
fiction.

## 5. Branch A's edge is real and it is the FLOW FILTER (v3 rehearsal, 2026-08-23)

A (buy the put into a weak bounce on a heavy, big-range tape): 8/12 scored
fills = 0.667 vs 0.500 midpoint control (+16.7 pp, clears the +10 pp bar).
The control differs from A by exactly one condition — 30-min HIRO flow NOT
negative — so the +16.7 pp IS the surviving entry-side HIRO value. Cleaner
still: A's five timeouts were limit-replayed and ZERO would have filled — the
signal separates fills from duds with nothing left on the table, and its only
exits (clock/resolution) cost nothing.

## 6. Branch B's entries are fine; its EXITS are mistimed for limit fills (2026-08-24)

B scored 0.333 (2/6) vs its 0.583 control — but the no-exit counterfactual is
0.667, ABOVE control. Decomposition of B's four non-fills:
| trade | exit | limit would have filled? |
|---|---|---|
| 08-12 scratch (−$80) | correct — never fills |
| 08-14 scratch (−$100) | **yes, minute 39** |
| 08-14 veto (−$60) | **yes, minute 58** |
| 08-17 veto (−$50) | correct — never fills |
The flow exits were researched under touch semantics (fills in minutes 1–28);
real fills arrive in minutes 8–58, and exits tuned to the fast world clipped
two slow winners. Mixed (2 correct / 2 harmful, n=4) — NOT the BH pattern
(8/8 harmful). Also: 5 of 8 sessions were below the Vol Trigger, so B was
starved to 6 entries from 28 qualifying signals; n is tiny.
**Decision (user, 2026-08-24): run the live test AS FROZEN; the B-exit
re-timing is PRE-REGISTERED as an inactive candidate in R7.2** (test on stored
sessions across ≥ 20 B episodes before any activation; any activation is a
spec edit + full R9a re-registration + test reset).

## 7. The registered exam (R9a record, stated plainly)

The run-once boundary was exercised three times; the TRADE LIST never changed
(19 trades / 10 fills / −$670 cash, independently verified each time); only
the grading derivation was corrected, each time toward the frozen text, each
time making the test HARDER: data_invalid mis-scoping fixed → p95 population
per R11.3 (cap $250→$150) → countable-only population (A floor 0.50→0.55).
Final registered thresholds: fills ≥ 11 (10-session projection), sessions
with ≥1 fill ≥ 7, B rate ≥ 0.10 and not below its control, A rate ≥ 0.55 and
≥ control +10 pp, max single loss ≤ $150, median scratch ≤ $140.

## 8. The honest v3 rehearsal economics (8 in-sample sessions, 1-lot)

19 attempts → 10 bombs planted (0.526). Credits +$100, losing legs −$770,
net cash −$670; the 10 owned 5-wide spreads marked +$645 at completion
(max payout $5,000) → MTM ≈ −$25 with the payoff optionality intact. Fills
took 8–51 minutes. The rehearsal FAILS its own registered thresholds on the
two count floors (10-session projections graded against 7 countable
sessions — an incomplete-test artifact) and on the $290 max loss vs the $150
p95 cap (a 08-20 timeout; the cap intentionally demands better tail control
than the rehearsal's worst trade). None of that is tuning feedback.

## 9. Process lessons that now bind

- A hand-computed fixture written BEFORE the code catches real bugs: it
  caught the cap-vs-leg-1-fill deviation — but only after its hand-derived
  MINUTES became load-bearing assertions. Decorative expecteds catch nothing.
- Silent search-and-replace is how "fixed" bugs survive: assert every patch.
- Controls must share the mechanics of the thing they benchmark (limit
  replay, same rounding, same gap rules) or the comparison is fiction.
- Every review round (2 planning + 2 build break points, red-team + codex in
  parallel) produced at least one finding that would have corrupted the live
  record. None were style nits. The 98%-adherence discipline (fix blockers/
  majors, log-and-accept documented residuals) held throughout.

## Open questions for the live test

1. Does A's +16.7 pp edge survive out of sample? (The 8 sessions were one
   heavy, below-VT week — A's home field.)
2. Does B reach 20 qualifying signals on executable days, and does the frozen
   exit set keep costing fills? (The pre-registered candidate waits on this.)
3. Live/backtest parity: do post-bar snapshots match the historical series
   within 1 tick / 95%? (Shakedown gate.)
4. Are 10 fills per 10 sessions (the registered floor: 11) realistic at
   exactly 0.10 credit, or is the honest bomb a 0.20-credit trade? (Only a
   post-test re-registration may ask this.)

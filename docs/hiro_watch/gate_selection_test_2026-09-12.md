# Does the A gate SELECT, or does it only reduce exposure? (22 sessions, 2026-08-12 → 09-11)

Prompted by the owner, 2026-09-12: *"how does it know to trade less?"* It doesn't. There is no
"take fewer marginal setups" rule — `a_r30_lt` **is** the depth premise, and trading half as often is
its side effect. So "trade fewer, lose smaller" is not a finding that survives the premise: it is the
same knob described twice. This file tests the knob directly.

Reproduce: `python scripts/hiro_watch/gate_test.py [--lt -2.0] [--branch A]` (reporting only, never a bar).

## Method

A gate that keeps N of M trades improves a losing book by arithmetic alone. So the question is not
"is the gated book better than the whole book" (it always is, when the average trade loses) but
**"are the kept trades better than an arbitrary N-of-M cut?"** Baseline (v1) Branch-A trades are joined
to the FIRST signal of each setup — where the engine reads its own flow number — and the gated subset's
cash and completion rate are compared against 20,000 random same-size subsets of the SAME trades
(seed 7). Portfolio caveat below.

## Result — the registered gate (r30 < −2) is indistinguishable from chance

| | n | bombs | rate | cash | **per trade** |
|---|---|---|---|---|---|
| kept (r30 < −2) | 10 | 6 | 0.60 | −580 | **−58.0** |
| blocked (r30 ≥ −2) | 22 | 12 | 0.55 | −1,220 | **−55.5** |

Random 10-of-32 subsets: mean cash −566 [p5 −1,090, p95 −80]. The gate's −580 is the **45th percentile**
of chance; its completion rate 0.60 vs random 0.57 is the **45th percentile**. The trades it keeps lose
at the same rate as the trades it blocks.

## The depth ladder — the relationship is not monotone; only the ≤ −4 tail beats chance

| gate | n kept | bombs | cash | per trade | cash percentile vs chance | completion percentile |
|---|---|---|---|---|---|---|
| r30 < −1 | 19 | 11 (0.58) | −950 | −50.0 | 64th | 44th |
| **r30 < −2 (registered)** | 10 | 6 (0.60) | −580 | −58.0 | **45th** | **45th** |
| r30 < −3 | 8 | 5 (0.62) | −610 | −76.2 | 28th | 48th |
| **r30 < −4** | 5 | 5 (1.00) | **+50** | +10.0 | **94th** | **95th** |
| r30 < −5 | 2 | 2 (1.00) | +20 | +10.0 | 66th | 69th |

The −2…−4 band is where the damage lives: the three trades at r30 −3.13, −3.03, −3.02 lost −$170,
−$110 and **−$380** (the worst trade of the program, 09-11 CPI). The five trades deeper than −4 all
completed. So the premise is alive ONLY in the extreme tail — which `conclusions.md` §15 already
flagged as regime-confounded (those 5 sit in 3 falling sessions) and which the owner's higher-N
objective deliberately traded away.

## Where `a2_size1_c30`'s Branch-A improvement actually comes from

v1 Branch A: 32 trades, 18 bombs, **−1,800**. The pick: 14 trades, 9 bombs, **−320**. The +1,480:

| source | n | cash |
|---|---|---|
| simply not being in the trades the gate blocked | 22 | **+1,220 (82 %)** |
| $0.30 credit on the 10 trades both took (+$20 × 6 bombs) | 10 | +120 |
| trades only the candidate reached — capacity freed when a shallow leg is blocked | 4 | +140 |

Branch B, same decomposition: blocked trades +410, credit effect 0 (B stays at 0.10), freed capacity
−80. Same shape — the B run cap also earns by not being there.

**Reading:** 82 % of the A edge is exposure reduction whose selection is no better than random. The
genuinely earned parts are the credit (+120, a payout change, not a selection change) and possibly the
freed-capacity trades (+140, n=4).

## Caveats

- **Portfolio, not isolated.** The candidate's book is not a subset of v1's: 4 of its 14 A trades are
  setups v1 never reached (one unpaired leg at a time — blocking a shallow leg frees a later one). The
  permutation test samples v1's own trades, so it answers "is this subset better than another subset of
  the same trades", not "is the candidate's whole book better". The decomposition above covers the rest.
- n = 32 A trades, 22 sessions, one tape. The −4 row is n = 5.
- Most of these sessions are DISCOVERY for both registered candidates; this is a diagnostic of the
  premise, not a verdict against a candidate. Verdicts still print at the 10-session checkpoints.

## Consequences

1. The A-depth premise (R7.2 candidate (1)) is now contested at the depth we actually registered.
   Confirmation so far: 09-10 three shallow A signals went 3-for-3 (+$30, both variants sat out);
   09-11 the deepest signal in weeks produced −$380.
2. Branch A is 80 % of v1's total loss (−1,800 of −2,260) and loses ≈ $56/trade regardless of flow
   depth. The untested control is **A-OFF** — we built and tested `b_enabled: false` but never the
   mirror. One yaml; it would say whether the long-first structure earns anything at all.
3. The credit is the only change that has added money in a way this test can attribute to the change
   itself. It is +$20/bomb.

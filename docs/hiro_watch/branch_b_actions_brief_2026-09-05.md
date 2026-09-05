# Branch B — ACTIONABLE recommendations wanted (brief for Charlie McElligott / Brent Kochuba)

The owner's reaction to the last review, verbatim: "well no shit I'm exposed with a naked short. That's
the point of using HIRO." Being short the put until the second leg fills is the DESIGN; HIRO flow is the
edge that is supposed to make that hour of exposure acceptable. Do not restate the structure. The
question is: **given the ten trades, what should change?** Give ranked, concrete, testable recommendations.
Each must be expressible as ONE rule/threshold change (it becomes a registered candidate config in the
watch and is scored on the next 10–40 confirmation sessions), must cite the data below that motivates
it, and must say what it would have done to these ten trades. Reject hypotheses the data does not
support. Add your own. ~700 words. No code review.

## The rules (identical v1 / a_depth_m4)
Entry R6.2: ARM when pull30 (30-min pullback from high) ≥ 3 pts AND the HIRO run has dur ≥ 10 min,
rate ≥ 2 $B/hr, both ΔC,ΔP > 0 with min/max ≥ 0.25, next-expiry share ≥ 0.5, run drawdown < 0.6 $B.
GATES: r15 > 0; before 14:30; weak side ≥ 0.15 $B. SELL the −0.20Δ put at the bar's closing bid; REST
the buy of K+5 at (fill − 0.10). Blocks: VT broken / levels invalid / flow veto (r15 & r15n < −0.8);
LATE (rate ≥ 4 & r30 ≥ 1). One unpaired leg; ≤ 3/day. Exits on the lone short: fill (bomb +$10);
SCRATCH within 3 min if L drops ≥ 0.3 $B below entry or the run breaks; VETO EXIT if the flow veto
activates; cap 3.5 pts; 60-min clock. A bomb pays $500 at/below the lower strike at expiry.

## Every Branch-B trade (a_depth_m4 = v1's 7 + 3 capacity-freed), with what happened AFTER entry

| date | sig | run $B | run age | rate | r15 | pull30 | SPX low/high next 60m vs S0 | SPX at exit | held | exit | P&L | MAE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 08-12 | 10:14 | 1.00 | 10m | 6.0 | +.40 | **12.2** | −8 / +9 | +4.9 | 10m | **FILL** | +10 | −30 |
| 08-12 | 10:47 | 0.87 | 15m | 3.5 | +.87 | 6.9 | −10 / +1 | −1.1 | 4m | scratch | −80 | −80 |
| 08-12 | 11:34 | 0.64 | 11m | 3.5 | +.19 | 4.4 | −3 / +8 | +6.6 | 51m | **FILL** | +10 | −90 |
| 08-13 | 12:09 | 0.88 | 10m | 5.3 | +.53 | 3.1 | −3 / +14 | −2.9 | 4m | scratch | −60 | −50 |
| 08-14 | 11:36 | 1.08 | 10m | 6.5 | +.51 | 5.9 | −4 / +6 | −2.6 | 4m | scratch | −100 | −70 |
| 08-14 | 13:12 | 1.27 | 10m | 7.6 | +.56 | 3.2 | −5 / +3 | −5.1 | 25m | veto | −60 | −60 |
| 08-17 | 11:51 | 1.64 | 10m | 9.9 | +.66 | 4.3 | −5 / +3 | −1.8 | 17m | veto | −50 | −80 |
| 08-25 | 10:45 | 0.59 | 15m | 2.3 | +.59 | **12.4** | −2 / +14 | +4.4 | 12m | **FILL** | +10 | −40 |
| 08-25 | 11:37 | 2.26 | 34m | 4.0 | +1.14 | 3.5 | −7 / +7 | −2.1 | 4m | scratch | −80 | −80 |
| 08-28 | 12:53 | 1.31 | 29m | 2.7 | +.41 | 4.0 | **−19** / +1 | −12.1 | 10m | veto | −220 | −290 |

HIRO all-basket cumulative flow L after entry (Δ$B at +3 / +10 / +30 min):
```
08-12 10:14 FILL     +0.97 / +0.97 / +0.79     08-14 13:12 veto    −0.11 / +0.32 / −0.82
08-12 10:47 scratch  −0.46 / −0.75 / −1.75     08-17 11:51 veto    +0.18 / −0.37 / +0.04
08-12 11:34 FILL     +0.02 / +0.06 / +1.69     08-25 10:45 FILL    +0.00 / −0.21 / −0.23
08-13 12:09 scratch  −0.44 / −1.00 / −0.93     08-25 11:37 scratch −0.64 / −1.17 / −0.12
08-14 11:36 scratch  −0.33 / +0.40 / +1.40     08-28 12:53 veto    +0.23 / −0.65 / −1.36
```

## Patterns in the ten (n = 10; treat as hypotheses to rank, not conclusions)
1. **Pullback depth at arm.** The two clean fills came off 12-pt pullbacks (pull30 12.2, 12.4); every
   loser came off 3–7 pts. The arm threshold is 3 pts. The third fill (pull30 4.4) took 51 minutes and
   was −$90 underwater. Hypothesis: B is selling into wiggles, not dips.
2. **Run age / size.** Fills: run ≤ 1.0 $B, age 10–15 min. The two oldest runs (34 m, 29 m) both lost,
   one for −$220. The biggest runs (1.27, 1.64, 2.26, 1.31) all lost. Hypothesis: B chases mature runs;
   the LATE rule (rate ≥ 4 AND r30 ≥ 1) does not catch them (08-25 11:37 was LATE at 11:34 and cleared at
   11:37 as the rate slipped under 4 — then scratched in 4 minutes).
3. **What B needs after entry is price UP** (the higher put must cheapen). The fills saw SPX +5/+7/+4
   at fill. Seven losers saw SPX go DOWN first (low60 −3 to −19). Flow at +3 min was ≥ 0 on all three
   fills and < −0.3 on all four scratches (by construction of the scratch rule).
4. **Scratch window.** All four scratches fired at exactly 4 minutes held (the 3-min window). Two of them
   (08-14 11:36, 08-12 10:47) then saw flow recover (+1.40, no) — 08-14 11:36's flow was +1.40 $B at
   +30 min and SPX +6: it would likely have filled. Hypothesis: the 3-minute window is too twitchy.
5. **Time of day.** Fills 10:14 / 10:45 / 11:34; losers 10:47–13:12. Weak.
6. **Credit.** Resting the buy at fill − 0.10: on the credit ladder B lost one bomb per extra dime
   (0.10: 3 bombs, 0.20: 2, 0.30: 1). Hypothesis in the other direction: rest at fill − 0.00 (no
   credit; the bomb is the payoff) or fill + 0.10 (pay a dime) to shorten naked time.

## Candidate rule changes the data suggests — rank, reject, or replace
- **B-PULL**: arm requires pull30 ≥ 8 (or 10) pts instead of 3.
- **B-FRESH**: run age ≤ 15 min and/or run ≤ 1.0 $B at signal (don't chase).
- **B-LATE-STICKY**: once LATE suppresses an episode, that episode stays suppressed (no 3-min re-arm).
- **B-SCRATCH-10**: scratch window 3 → 10 min (or scratch threshold 0.3 → 0.5 $B).
- **B-CREDIT-0**: rest the buy at fill − 0.00 / fill + 0.10 for B only.
- **B-OFF**: disable B; give its capacity to A (a_depth_m4 already shows the capacity spill costs −$360).
- Anything else the numbers support.

Constraints: one change per candidate; nothing changes v1; every candidate is scored on the same
confirmation tape (currently 1 session, no B trade yet). Discovery: 16 sessions, 10 B trades.

# Branch B under `a_depth_m4` — diagnose the failure modes (brief for Charlie McElligott and Brent Kochuba)

ONE question: why does Branch B (sell-first) lose, and what are its failure modes — in `a_depth_m4`
specifically, where it is worse than in v1? Plain language for the owner; ~600 words; no code review;
no new research programme. Say what the ten trades show, which failure modes are structural to the
sell-first leg and which are artefacts of capacity, and whether anything in this sample says B
should exist at all.

## The rules (verbatim summary; identical in v1 and a_depth_m4)
- **Entry R6.2 (sell first):** ARM when the 30-min pullback ≥ 3 pts AND the HIRO run has: duration ≥ 10 min,
  rate ≥ 2 $B/hr, both call and put flow positive with min/max ≥ 0.25, next-expiry share ≥ 0.5, no run
  drawdown ≥ 0.6 $B. GATES: r15 > 0; before 14:30; weak side ≥ 0.15 $B. Action: SELL the −0.20Δ put at the
  bar's closing bid; REST the buy of the strike 5 higher at (fill − $0.10).
- **Blocks:** no shorts while VT broken (R4.1) or SpotGamma levels invalid (R4.2) or flow veto (r15 AND r15n
  < −0.8 $B, R4.3); LATE suppression when rate ≥ 4 $B/hr AND r30 ≥ 1.0 $B (R6.3); one unpaired leg at a
  time; ≤ 3 entries/day; A beats B on the same bar.
- **Exits on the lone short put:** R7.1 fill (bomb, +$10 credit); R7.2 flow-shutoff SCRATCH within 3 min
  of entry if L drops ≥ 0.3 $B below its entry value or the run breaks; R7.4 VETO EXIT if the flow veto
  activates while short; R7.3 cap at 3.5 pts against; R7.5 60-min clock (timeout).
- Bomb = long the higher strike put / short the lower: pays $500 at expiry if SPX settles at or below the
  lower strike, proportionally less between the strikes, $0 above the upper — plus the $10 credit already banked.

## The only difference between v1 and a_depth_m4
a_depth_m4 refuses Branch-A signals with r30 ≥ −4 $B. That empties the one-trade slot on days v1 had a
shallow A leg open, so THREE B setups v1 refused for capacity ("one unpaired leg at a time" / "3 entries/day")
are taken in a_depth_m4. The B rules themselves are byte-identical.

## Every Branch-B trade, 17 sessions (08-12 → 09-03)

v1 (7 trades, 3 bombs, cash −$260):
```
2026-08-12 10:14 S0=7746 sold 7475P@35.10 rest 7480P@35.00 | run=1.00$B rate=6.0 dC=.53 dP=.47 share=.74 r15=+.40 | FILL 10m +10 (mae −30)
2026-08-12 10:47 S0=7748 sold 7520P@40.90 rest 7525P@40.80 | run=0.87 rate=3.5 dC=.19 dP=.68 share=.76 r15=+.87 | SCRATCH −80
2026-08-12 11:34 S0=7742 sold 7475P@35.50 rest 7480P@35.40 | run=0.64 rate=3.5 dC=.39 dP=.24 share=1.18 r15=+.19 | FILL 51m +10 (mae −90)
2026-08-14 11:36 S0=7784 sold 7570P@38.70 rest 7575P@38.60 | run=1.08 rate=6.5 dC=.33 dP=.75 share=1.02 r15=+.51 | SCRATCH −100
2026-08-14 13:12 S0=7782 sold 7570P@38.10 rest 7575P@38.00 | run=1.27 rate=7.6 dC=.60 dP=.67 share=.73 r15=+.56 | VETO EXIT −60
2026-08-17 11:51 S0=7774 sold 7505P@40.70 rest 7510P@40.60 | run=1.64 rate=9.9 dC=.58 dP=1.06 share=.90 r15=+.66 | VETO EXIT −50
2026-08-25 10:45 S0=7661 sold 7375P@39.90 rest 7380P@39.80 | run=0.59 rate=2.3 dC=.16 dP=.43 share=.87 r15=+.59 | FILL 12m +10 (mae −40)
```
a_depth_m4 = the same 7 plus the three capacity-freed setups (10 trades, 3 bombs, cash −$620):
```
2026-08-13 12:09 S0=7783 sold 7525P@35.00 rest 7530P@34.90 | run=0.88 rate=5.3 dC=.42 dP=.45 share=.78 r15=+.53 | SCRATCH −60   (v1: A leg open, skipped)
2026-08-25 11:37 S0=7670 sold 7420P@43.30 rest 7425P@43.20 | run=2.26 rate=4.0 dC=1.03 dP=1.23 share=.81 r15=+1.14 | SCRATCH −80  (v1: A leg open; note this setup was first LATE-suppressed at 11:34)
2026-08-28 12:53 S0=7720 sold 7475P@33.90 rest 7480P@33.80 | run=1.31 rate=2.7 dC=.52 dP=.79 share=.68 r15=+.41 | VETO EXIT −220 (mae −290)  (v1: 3 entries/day used)
```
Exit tally, a_depth_m4 B: 3 fills (+$30) · 4 scratches (−$320) · 3 veto exits (−$330) · 0 timeouts · 0 caps.
Fills: 10, 51, 12 minutes; the 51-minute one was −$90 underwater on the way.
Bombs are the same three in both engines (planted 08-12 10:14, 08-12 11:34, 08-25 10:45). Marked at the
09-04 close (SPX 7718): 7480/7475 exp 09-11 = $15 each, 7380/7375 exp 09-25 = $25 → B inventory $55.
B full lifecycle to date: cash −$620 + inventory $55 = −$565 (v1: −$260 + $55 = −$205).

## Refusals in the same 17 sessions (baseline)
31 B setups refused for VT-broken (26 of them also late/flow/capacity-blocked), 2 for levels invalid, 14 LATE.
Turning the two safety blocks off loses money (diag configs: VT off −$205 vs v1, levels off −$370); LATE off is a wash (+$45).

## Context
- Discovery = 16 sessions; confirmation = 1 (09-03, no B trade). All numbers above are discovery.
- Sessions: mostly rallying tape 08-12 → 08-20, a falling tape 08-21 → 08-28 (SPX 7780 → 7630), rally
  09-02 → 09-03 (7635 → 7748). Two of the three bombs were planted in the first 75 minutes of a session.
- Tally through 09-04: v1 MTM −$880; a_depth_m4 MTM −$270. Cash: +$900 vs v1 (A +$1,260, B −$360);
  inventory: −$290 vs v1 (8 bombs marked $300 vs 16 marked $590); MTM +$610.

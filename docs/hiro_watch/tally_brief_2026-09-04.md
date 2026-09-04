# hiro_watch tally through 2026-09-04 — what is broken and not working? (brief for Charlie McElligott and Brent Kochuba)

You are asked ONE thing: in plain language, for the owner (a solo quant/trader), explain what is broken
and not working in this SPX put delta-bomb program, based only on the numbers below. Be blunt and
specific. Do not review the code. Do not propose a new research programme; say what the evidence says
is wrong and what, if anything, the tape has actually confirmed. ~600 words max.

## The strategy in one paragraph
SPX 30-DTE put vertical, 5 wide, 1 lot, paper. "Bomb" = both legs done for a $0.10 net credit (buy the
higher-strike put, rest a sell 10¢ below, or sell first and rest a buy). Entry on SpotGamma HIRO
dealer-flow signals: Branch A (buy first) needs a 60-min range expansion + 30-min negative net flow
(r30 < 0 $B) + price below its 30-min mid; Branch B (sell first) needs a sustained positive flow run.
Exits on the lone leg: 60-minute clock, 3.5-pt cap (≈ $350), flow veto, scratch. Frozen engine v1
(CONFIG_HASH 80c3a4…). Six pre-registered candidate configs run beside it every evening; verdicts only at
10/20/30/40 confirmation sessions. Discovery = 08-12 → 09-02 (16 sessions, the data the candidates were
chosen on). Confirmation started 09-03.

## Tally — all 18 sessions 08-12 → 09-04, marked at the 09-04 close (SPX 7718; 09-03 close 7748; 09-02 7667)

| candidate | A trades/bombs | B trades/bombs | cash | inventory (open bombs) | MTM | vs v1 |
|---|---|---|---|---|---|---|
| v1 baseline | 24 / 13 | 7 / 3 | −1,470 | +590 (16 bombs) | −880 | — |
| a_depth_m4 (A only if r30 < −4 $B) | 5 / 5 | 10 / 3 | −570 | +300 (8) | −270 | +610 |
| credit030 (rest the second leg 30¢ away) | 24 / 13 | 7 / 1 | −1,110 | +550 (14) | −560 | +320 |
| diag_late_off (late-suppression off) | 24 / 13 | 7 / 3 | −1,450 | +615 (16) | −835 | +45 |
| diag_levels_off (levels-invalid short-block off) | 24 / 13 | 10 / 3 | −1,840 | +590 (16) | −1,250 | −370 |
| diag_vt_off (VT-broken short-block off) | 24 / 13 | 13 / 7 | −1,790 | +705 (20) | −1,085 | −205 |

Baseline detail: 31 trades, 16 bombs (fill rate 0.52); exits: 16 fills, 10 timeouts (−$300 … +$20),
2 scratches, 2 flow-veto exits, 1 cap (−$350). Credits banked 16 × $10 = $160; failed attempts −$1,630.
Every $10 of credit has cost ~$100 of failed attempts. All 16 open bombs are the same bet: SPX
7370–7575 by 09-11 / 09-18 / 09-25 / 10-02 (i.e. 2–4.5 % below spot), and they mark as one position:
+$1,265 on 09-02, +$165 after the 09-03 rally (+80 pts), +$590 after today's −30.

## The last two sessions (the only confirmation data)
- 09-03 (countable): SPX 7687 → 7748 (+80, rally). v1 took two Branch-A trades on shallow negative
  flow (r30 −0.96 and −1.20 $B): cap exit −$350, timeout −$70 → −$420. a_depth_m4 took neither
  (both gated). credit030 took both, same prices, same −$420 (no second leg ever filled).
  diag_levels_off entered one B setup v1 had refused (levels invalid AND flow-vetoed): −$200.
- 09-04 (NFP): engine stood down by rule. No trades for anyone. Not a confirmation session.
- Confirmation count: 1 of 10 to the first checkpoint.

## Findings already on record (discovery data)
- Branch A's losses come from shallow-flow signals: over the 22 discovery A trades the bomb rate by
  flow depth at the signal minute was r30 < −1: 58 % (12) · < −2: 71 % (7) · < −3: 83 % (6) ·
  < −4: 100 % (5) · < −5: 100 % (2). The −4 bucket is 5 for 5 but from 3 falling sessions
  (regime-confounded). A −1 discriminator was FALSIFIED on the full sample (0.58 vs 0.60).
- Branch B is starved: 7 trades in 17 sessions; 31 setups refused for VT-broken, 2 for levels
  invalid, 14 suppressed as LATE (most overlap). Turning those rules off loses money.
- credit030 keeps all 13 A fills but loses 2 of 3 B fills when the engine's own exits run in
  sequence (an earlier isolated replay had said it would fill at +34 min — it was wrong).
- The a_depth gate frees capacity that Branch B then uses and loses (10 B trades vs 7, −$620 vs −$260).
- A $150 max-loss stop was tested and rejected (−$870; 3 of 16 winners were > $150 underwater
  before filling). The engine's exits stay the 60-min clock and the 3.5-pt cap.

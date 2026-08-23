# BH-Scratch Forensics — hiro_engine rehearsal (8 sessions, 2026-08-12..21)

*Independent diagnosis agent, 2026-08-23. Read-only investigation of the rehearsal
FAIL ("18 trades, 6 fills; Branch-A BH scratch cut 8 episodes, 9 scratches would
have filled vs the ≤1 criterion"). No rules were changed; the 10-session test has
not started. Analysis script: scratchpad `bh_forensics.py` (session-local).*

## 1. Per-scratch table (all 8 Branch-A scratches; BH recomputed from stored SPX, matches engine-stamped `bh_level` to the cent)

| date | sig | S0 | BH | BH−close@sig | fired (min after entry) | margin high−BH | S0−3 touch absent scratch | pnl | give-up vs fill |
|---|---|---|---|---|---|---|---|---|---|
| 08-13 | 657 | 7801.12 | 7801.77 | 0.63 | 0 (entry bar) | 0.59 | YES +6m | −1.17 | 4.17 |
| 08-13 | 679 | 7794.86 | 7794.93 | 0.11 | 0 | 0.45 | YES +3m | +0.12 | 2.88 |
| 08-14 | 636 | 7794.19 | 7794.28 | 0.15 | 0 | 1.31 | YES +18m | +1.20 | 1.80 |
| 08-17 | 822 | 7756.44 | 7756.49 | 0.00 | 0 | 1.11 | YES +49m | −0.82 | 3.82 |
| 08-18 | 663 | 7700.06 | 7700.42 | 0.47 | 0 | 2.08 | YES +5m | −1.78 | 4.78 |
| 08-19 | 704 | 7724.92 | 7724.98 | 0.00 | 0 | 0.06 | YES +9m | −0.15 | 3.15 |
| 08-20 | 650 | 7686.34 | 7693.65 | 7.33 | 10 | 5.17 | YES +18m | **−11.57** | 14.57 |
| 08-20 | 687 | 7683.73 | 7683.72 | 0.11 | 0 | 1.63 | YES +5m | +0.06 | 2.94 |

**8/8 scratches would have filled within the 60-min horizon** (+ the 08-14 B
scratch at +23m = the 9 counted by stage6). 7/8 fired on the **entry bar itself**
(lag 0). Total give-up: **38.1 pts** (−14.1 realized vs +24.0 counterfactual).
The sole adverse>10 trade (08-20 #1, adverse 12.48) is the scratch's own exit
print — absent the scratch it fills +3 at minute 669. The tape delivered a 12/12
fill environment for Branch A; the BH scratch turned it into 4/12 = 0.333.

## 2. Root cause: (b) spec-design flaw, compounded by unresearched provenance. Not (a) implementation, not (c) adverse sample.

- **Not an implementation bug.** `features.py` bh_level (max highs from the
  30-bar close-low through the signal bar) and `rules.py` `_exit_decision`
  (`bar.high > bh_level`, fill checked first, BH frozen at signal) match R7.2's
  text exactly; independent reconstruction reproduces every stamped bh_level.
- **Geometry.** BH − close at signal across all 12 A entries: min 0.00 / p25
  0.11 / **median 0.55** / p75 6.04 / max 9.02. Scratched entries had median
  clearance **0.13 pts**; the 4 fills had 2.47–9.02. R6.1 requires bounce30 ≥ 3
  off the 30-bar low, so the signal-bar close is typically the running post-low
  high — close ≈ BH by construction. The rule then demands a 3.0-pt fall before
  a ~0.1–0.6-pt uptick: a ~0.85/0.15 race against the fill on any tape.
- **Provenance: never backtested.** The researched TAPE rule (E2) is an outcome
  measurement with NO exits (`hiro_experiments.outcome_row` counts touches; zero
  scratch logic in any research script; `rg` for "bounce high"/BH across
  research code: no hits). The scratch first appears as authored prose in the
  playbook (§4 "scratch if price re-takes the bounce high") as an analogue of
  Branch B's researched flow-shutoff, then was formalized in R7.2. The quoted
  0.88 in-sample fill rate is literally the no-scratch counterfactual the
  scratch now destroys. These sessions were favorable (12/12 touches): the rule
  loses on geometry, not on draw.

## 3. Branch B: 0.333 vs 0.771 control

6 executed B entries → 2 fills, 2 scratches, 2 veto_exits. Only one exited trade
(08-14 scratch, +23m) would have filled; the other 3 never touch S0+3 in 60 min.
Exits cost 0.167 of fill rate (0.333 → 0.50 no-exit counterfactual); the rest of
the gap vs 0.771 is entry selection / small n (n=6, wide CI). The daily cap and
one-leg rule crushed n, not the rate: 20 B skips = 15 vt_broken + 5 daily-cap.

## 4. Options (frozen — any change is a spec edit + R9 reset; R13.2 has NO BH knob)

1. **Drop the A-scratch entirely** (revert to researched E2 exits: fill/cap/
   clock/resolution). The 0.88 was measured scratch-free; the scratch saved 0
   pts of tail here (cap + clock never bound) while costing 38.1 pts and
   *creating* the only adverse>10 event. **Strongest option on current evidence.**
2. **Clearance buffer** (high > BH + X): X=2 still scratches 2 would-fill trades
   incl. the −11.57. No X helps in these 8 sessions.
3. **BH from highs since ENTRY** (trailing): removes the lag-0 pathology, still
   races the fill; needs replay evidence it ever exits a real loser.
4. **Premise-based invalidation** (e.g. close back above mid30 = the E2 premise
   failed): the true analogue of B's "reason vanished"; testable on stored data.
5. **Time-boxing** (3-min window like B) does NOT help: 7/8 fired at lag 0.

Decision is the user's; nothing resets since the live test has not begun.

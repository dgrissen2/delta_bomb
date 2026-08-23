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

---

## CIO memo — the bounce-high scratch (plain terms)

Team — the paper engine's dress rehearsal failed, and we now know exactly why. It was not the market and it was not a coding error. One exit rule — "if price ticks back above the recent bounce high, abandon the trade" — killed eight of our twelve long-side entries, usually within the very first minute. Every single one of those abandoned trades would have finished as a winner within the hour. We gave up about 38 index points of paper profit to a rule that, over these eight sessions, protected us from exactly nothing. Worse, the only scary loss in the whole test (an 11.6-point hit) was *caused* by this rule's own exit, not prevented by it.

The uncomfortable part is where the rule came from. Our researched entry signal was validated with simple exits: take profit at the target, cut at a hard cap, give up after an hour. The 88% success number we quoted came from *that* configuration. The bounce-high scratch was added later, during document drafting, as a "common sense" mirror of a rule that works on the other side of the book — and it was never run through the data before we froze it. The geometry is self-defeating: our entry requires a 3-point bounce, which means we enter almost exactly *at* the bounce high, so the tiniest uptick triggers the scratch before the trade has any room to work. We built a tripwire and then stood on it.

Options on the table: (1) delete the scratch and revert to the researched exits — cap, clock, and the 15:30 close still protect us; (2) require a real breach — say two points above the bounce high — before scratching, though no buffer level actually helps in the data we have; (3) trail the invalidation from our entry price instead of the pre-entry high; (4) replace it with a premise check. Direction matters here, so to be explicit: Branch A is "long-first" on a PUT — we buy a ~20-delta put first, and the trade finishes when SPX *falls* 3 points so we can sell the put 5 strikes lower. It is the bearish leg. The entry buys that put *into* a small bounce (bounce30 ≥ 3) purely to get a better price, while the tape is still heavy (30-min flow negative, price still below the midpoint of the last 30 bars). So no — we never *want* price closing higher after entry; higher is against us. The premise check says: if price climbs all the way back above that 30-bar midpoint (mid30), the "heavy tape, fade-the-bounce" story we bought is objectively dead — the bounce became a real reversal — so leave. That is a fundamentally different tripwire than the bounce high: mid30 sits well ABOVE the entry (2.9 pts above on 08-18, not 0.4), so it only fires when the premise actually breaks, not on the first wiggle; (5) put a time window on it, which the data says does nothing since it fires immediately. Any of these is a rule change, which by our own charter means editing the spec and restarting the 10-session clock — but the clock has not started, so today is the cheapest day this fix will ever be.

My recommendation: take option 1 now — remove the long-side bounce-high scratch entirely and rely on the exits the research actually validated — and register option 4 (the midpoint premise check) as a pre-registered candidate to test on stored data before anyone proposes adding an invalidation rule back. We should also write down the process lesson, because it is the real finding: no exit rule enters the frozen spec again without a backtest showing at least one session where it saved more than it cost. Rules earn their place with evidence, or they do not ship.

## Feynman explanation — why the rule had to fail

Imagine you are waiting to buy a ball that is bouncing down a staircase. Your rule for buying is: "wait until the ball has bounced at least three steps up off its low — that proves it can bounce." Fine. But then somebody adds a safety rule: "if the ball ever goes even a hair above the top of that bounce, run away." Now look at what you have done. You only ever buy *right at the top of a bounce* — that is what your entry rule demands — so the "danger line" is sitting a fraction of an inch above your head the moment you walk in. Any little wiggle, any noise, and the safety rule fires. You did not build a safety net; you built a doorframe exactly at forehead height.

The numbers say precisely this. On the eight days we tested, the gap between where we entered and the "run away" line was about a tenth of a point — the market wiggles more than that every single minute. Seven of the eight scratches triggered on the very first bar after entry. The trade never had a chance to be right or wrong; it was disqualified by its own entry condition. And here is the beautiful, brutal part: all eight of those abandoned trades went on to hit their profit target within the hour. The rule was not measuring danger. It was measuring the same bounce that made us enter — and calling it a reason to leave.

Why did nobody catch this? Because the rule was never tested — it was *reasoned*. It looks like a rule we trust on the short side: "if the flow that justified the trade shuts off, get out." That rule works because it watches something *different* from the entry signal — the flow can die while the price sits still. But the bounce-high version watches the *same thing* as the entry: the bounce. When your exit trigger and your entry trigger are the same measurement, the exit is just the entry wearing a disguise, and it will fire roughly whenever the entry does. Symmetry by analogy is not symmetry in fact. You have to do the arithmetic.

The general lesson is the one that never gets old: it does not matter how sensible a rule sounds, how much it rhymes with a rule that works, or how smart the person who wrote it is. If you did not run it against the data, you do not know what it does — and here, the moment we ran it, the answer was unambiguous in eight days flat. The fix is equally unambiguous: go back to the version of the experiment that was actually measured, and if you want a new safety rule, measure *it* first. Nature — and the tape — cannot be fooled by a plausible sentence in a document.


---

## Walkthrough — two real scratches, bar by bar (what the variables said, and what happened)

**Remember the trade's direction first**: Branch A buys a ~20-delta SPX **put**
(that is the "long-first" leg — long the put). It wins when SPX **drops 3
points** from our entry mark (S0), letting us sell the put 5 strikes lower and
complete the vertical for roughly free. The entry deliberately buys the put
while price is *bouncing up* (bounce30 ≥ 3 pts off the 30-bar low) — a bounce
makes the put cheaper — as long as the tape still looks heavy: 30-minute HIRO
flow negative (r30 < 0), price still below the middle of the last 30 bars
(close < mid30), on a big-range day (range60 ≥ its 75th percentile). The BH
scratch rule then says: BH = the highest HIGH printed between the 30-bar low
and our signal bar; if any bar after entry ticks ABOVE that high, abandon ship.

### Example 1 — 2026-08-18, signal 11:03 (the tripwire-at-your-forehead case)

What the variables said at 11:03: the 30-bar close low was 7695.36, printed at
**11:01 — just two minutes earlier**. Signal close 7699.95, so bounce30 = 4.59
(≥ 3 ✓); mid30 = 7702.90, close below it ✓; flow negative ✓. Because the low
was only 2 minutes old, BH = the highest high of a **three-minute window**
(11:01–11:03) = **7700.42** — sitting 0.47 pts above our close. We entered at
11:04's open: S0 = 7700.06, needing 7697.06 (−3) to win, scratching above
7700.42 (+0.36). Read that again: the rule gave the trade **0.36 points of
breathing room upward** against a 3-point objective downward. The 11:04 entry
bar itself printed a high of 7702.50 — through BH by 2.08 — so the trade was
condemned *on its own entry bar*, and we exited at 11:05's open, 7701.84, for
−1.78. What happened next: the bounce exhausted and SPX hit 7697.06 at **11:09
— five minutes after entry**. No scratch → +3.00 fill. The scratch converted a
five-minute winner into a loss because "the bounce continued for one more bar,"
which is exactly what the entry rule (buy INTO a bounce) makes likely.

### Example 2 — 2026-08-20, signal 10:50 (the "even with room, it hurts you" case)

This one had real clearance, and it was still wrong. At 10:50: 30-bar low
7679.85 (10:21), close 7686.32, bounce30 = 6.47, mid30 = 7686.53 (barely
below ✓). BH over 10:21–10:50 = **7693.65**, a healthy 7.33 pts above the
close. Entry 10:51 at S0 = 7686.34, target 7683.34. Then the bounce kept
running: ten minutes later, at 11:01, SPX spiked to 7698.82 — through BH by
5.17 — and the rule dumped us at 11:02's open, **7697.91**, for **−11.57**,
the single worst print of the entire rehearsal (and the one "adverse > 10"
event in the test — *created by this exit*). What happened next: that spike
was the top. SPX rolled straight over and touched 7683.34 at **11:09 — seven
minutes after our forced exit**, eighteen minutes after entry, well inside the
60-minute clock. No scratch → we ride 12 points of paper drawdown (still under
the 15-point cap, which exists precisely for this) and collect +3.00. The
scratch didn't just miss the win — it *locked in the exact worst moment* of a
trade that the cap and the clock were already protecting.

**The pattern in one sentence**: the entry rule requires price to be near the
top of a fresh bounce, so BH is almost always a whisker overhead (median 0.13
pts on the scratched trades) and the "invalidation" fires on noise; and even
when BH is far away (Example 2), piercing it marks the bounce's *exhaustion* —
statistically the best moment to be short — so the rule systematically sells
the put back at bounce tops, right before the drop it was bought for. Across
all 8 scratches: every one reached its −3 target within the horizon; total
surrendered, 38.1 points.

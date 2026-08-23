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

## Walkthrough — two real scratches, in plain English

### First, the bet itself — no jargon

**We are trying to catch a DOWNSWING. Full stop.** Branch A is a bet that the
S&P is about to fall. We win when the index drops 3 points from where we got
in. That's the whole game: get in, market falls 3 points, we're done, paid.

**So why do we get in while the market is popping UP?** Timing. On the days
this setup looks for, the market is grinding lower all day but keeps making
little 3-4 point pops upward along the way — like a ball bouncing as it goes
down the stairs. Our bet (a put option) gets **cheaper** during each little
pop. So the play is: wait for one of those pops, buy the down-bet near the top
of the pop at a discount, then collect when the slide resumes. Buying during
the pop is not a mistake — it IS the strategy. The pop is our entrance, the
slide is our payday.

**Now the broken rule.** Someone added a safety rule that says: look at the
highest price the pop has reached so far; if the market goes even ONE TICK
above that, assume the pop is actually a real rally, panic, and cancel the
bet. Sounds reasonable — until you remember we *deliberately entered near the
top of the pop*. The pop's high is basically where we're standing when we walk
in. So "one tick above the pop's high" is usually a coin-flip away — the
scratched trades had a median of **0.13 points** of headroom, on an index that
wiggles more than that every single minute. We ask the market to fall 3 points
without ever wiggling up a dime first. Markets don't move like that.

### Example 1 — Aug 18, 11:03am: canceled by a wiggle, paid off 5 minutes later

The market had been sliding, bottomed at 7695 around 11:01, and popped ~4.5
points up — our discount window. At 11:04 we bought the down-bet with the
market at **7700**. To win we needed **7697** (3 points down). The cancel line
— the pop's high so far — was **7700.42**. Look at those numbers: we needed
the market to fall 3.00 points, but the rule canceled us if it rose **0.36**
first. In the very first minute the market wiggled up to 7702.50 — pops
overshoot, that's what pops do — cancel triggered, out at a 1.78-point loss.
And then? The pop died, the slide resumed, and the market hit 7697 at
**11:09 — five minutes after we entered**. The win was sitting right there.
The rule threw it away because a 4-point pop briefly became a 6-point pop.

### Example 2 — Aug 20, 10:50am: the rule sold the exact top

Here the cancel line wasn't a whisker away — it was 7+ points up, at 7693.65.
Room to breathe, right? We bought the down-bet at **7686**, needing **7683**.
The pop kept climbing — 10 minutes later it spiked to 7698.82, through the
cancel line — and the rule dumped us at **7698**, a **BRUTAL 11.6-point loss**,
the single worst print of the whole test. Here's the sickening part: that
spike WAS the top. The very thing that triggered the cancel — the pop running
out of steam in one last surge — is the classic look of a pop *ending*. The
market rolled straight over and hit our 7683 target **seven minutes after the
rule kicked us out**. And we didn't even need the rule for protection: we
already carry a hard stop at 15 points against us and a 60-minute time limit.
The market never got near either. The "safety" rule didn't prevent the big
loss — it **manufactured** it, by selling at the exact top and skipping the
payoff.

### The one-sentence takeaway

We enter during pops on purpose, so a rule that panics "when the pop goes any
higher" cancels us on routine noise (Example 1) — and when the pop genuinely
runs further, its final surge is usually the top, so the rule dumps us at the
worst possible price right before the drop we paid for (Example 2). Eight
trades were canceled this way across the test; **all eight** would have hit
their 3-point target in time; the rule saved nothing and cost 38 points.

---

## Charlie × CIO joint review — the simple fix (2026-08-23)

**Charlie (flows):** The pop you're buying into on these days is mechanical —
a squeeze in a heavy tape. Squeezes *overshoot by construction*; a pop ticking
past its old high is the signature of the squeeze burning out, not of a trend
change. So a cancel rule keyed to "the pop made a new high" is keyed to noise
at best and to the exact top at worst — the data showed both. Iron rule: **an
exit must watch a DIFFERENT dial than the entry.** You entered on price
(the bounce); if you ever want an invalidation, it has to be flow (the
negative 30-minute HIRO reading flipping hard positive) or structure (price
reclaiming the range midpoint) — never the bounce itself.

**CIO (what ships):** Three tests for any rule: implementable, backtested,
scales. The bounce-high scratch fails test two — it was never run before it
was frozen, and the first time it WAS run it destroyed the strategy it was
guarding. The protections that were researched — the 15-point hard cap, the
60-minute clock, the 15:30 close-everything — bounded every trade in the
rehearsal without help. Buffers, trailing versions, time-boxes: all rejected,
no version saves a single point in the data. And we will not swap in the
midpoint check today either — that would repeat the original sin of shipping
an untested rule because it sounds sensible.

**THE FIX (three lines):**
1. **Delete the bounce-high scratch.** The down-bet keeps exactly the exits
   the research validated: hit the target, hard 15-point stop, 60-minute
   clock, everything closed by 15:30. Nothing else.
2. **New standing rule for the spec:** no exit may trigger off the same
   variable as its entry, and no rule enters the frozen document without a
   backtest that shows it saving more than it costs. One sentence, permanent.
3. **Park the midpoint check as a pre-registered candidate.** Test it on the
   stored sessions first; it gets in later only if the numbers say so.

Cost of doing this now: a one-line spec edit and a config change, which resets
a 10-session test that hasn't started. Cost of not doing it: the rehearsal
numbers, live.

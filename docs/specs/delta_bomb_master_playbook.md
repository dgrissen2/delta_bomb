# SPX Delta Bomb — Master Playbook (decision tree)

*v1.2 — 2026-08-22. v1.1 content unchanged in substance; every section now carries a plain-English companion (Feynman treatment) per trader annotation. Reviews: Charlie (inline), `/codex-plan-review` (14 findings applied), red-team audit (12 findings + 8 missed rules applied), CIO junior-analyst readthrough (§10). Evidence: `spx_1min_delta_bomb_leg_in_strategy.md` (EV), 845-session touch stats, 8 HIRO sessions, live trades 2026-08-17.*

> **PAPER ONLY. 1 lot. Everything here runs inside the pre-registered 10-session test (§8). Real size requires BOTH: the acceptance test passing AND the SPXW quote-level replay (still owed). Spot-touch success alone never authorizes live sizing.**

**Status tags:** **[SETTLED]** data-supported, survived review · **[DISCIPLINE]** no measured edge; keeps you out of trouble · **[HYPOTHESIS]** plausible, thin data · **[FROZEN]** part of the frozen 10-session composition — do not modify (any change resets the test) · **[EXCLUDED]** defined for completeness, NOT traded during the test · **[OPS]** operational task.

---

## 0. The trade, in one line

A **delta bomb** = 5-wide SPX put vertical legged in for zero or small credit: **sell the put on a dip, buy the put 5 points higher on a bounce** (sell-first), or the reverse (long-first). Tenor 20–40 DTE, ~20Δ base strike (white paper §2.2). The second leg needs ~**3 pts of SPX movement** (strike gap ÷ Δ; ≈3 pts at 21Δ/IV 14 — *an estimate: a 50-day above-VT stress test is running; quote the measured range from `docs/replay/gap_delta_stress.csv` once written* [HYPOTHESIS until then]). The edge is the tape's own oscillation — a 3-pt move arrives within an hour **~80% of the time, either direction, regardless of any signal we tested** [SETTLED, 845 sessions, EV §1].

> **In plain English:** You're building a small insurance package (a put spread) without paying for it. You do it in two steps: sell one put while the market is dipping (puts fetch good prices then), and buy a slightly more valuable put while the market is bouncing (puts get cheap then). If you catch one ordinary 3-point wiggle between the two steps, the package costs you nothing. The market hands out 3-point wiggles about four times out of five in any given hour — that generosity, not prediction, is the whole edge. Everything below exists because between step one and step two you're holding one naked option, and once in a while the market runs 15+ points against it. The rules pick which step to do first, when to do it, and how to bail out cheaply.

```
   fills  = the tape's 80%/hr oscillation        danger = the lone leg while you wait
   timing = place legs at turns (discipline)     safety = scratch, cap, clock
```

## 1. Pre-market (5 minutes)

```
scheduled macro event (CPI/FOMC/opex)? ──yes──► STAND DOWN                        [DISCIPLINE]
SpotGamma levels loaded (VT, CW, SG index)?
   ├─ no, or CW−VT ≤ 0, or IM unavailable ──► LONG-FIRST ONLY today               [DISCIPLINE]
   └─ yes ──► note regime: SG ≥ ~1.5 & open > VT = calmer tail (30-pt runs 2.6% vs 6.4%)
              → context tag only; size fixed at 1 lot during the test              [HYPOTHESIS]
HIRO backfill run? (vendor retains ~5 sessions; flag partial captures)             [OPS]
```

> **What the SpotGamma levels are and where they come from:** SpotGamma is a research service that estimates, from options open interest, the price levels where market-makers' hedging behavior changes. We pull three numbers each morning (scraped daily into `~/Dev/core_spotgamma_spx_vix_data/offset_historical_spotgamma_data.csv`; shown in their Founders Note and dashboard): **Vol Trigger (VT)** — below this level dealers' hedging *amplifies* moves instead of damping them; think of it as the line between "calm pool" and "rapids". **Call Wall (CW)** — the strike with the heaviest call positioning; rallies tend to stall into it. **SG index** — their summary score for how strongly dealers are positioned to damp moves (higher = calmer). We use VT as a safety tripwire and CW/SG as context. **HIRO** (also SpotGamma) is different: a live intraday feed estimating the dollar buying/selling pressure options trades are forcing on dealers — we use it only for exits and vetoes (§5).

**Never, on any day: the ATM "anchor" put** — ≈ $127/bomb cost vs ≈ $50 credit over 102 replayed days; −$120 in 23 min live (2026-08-17). The cap + one-leg rule replace it. [SETTLED]

> **In plain English:** The white paper suggests buying an expensive at-the-money put as "insurance" while you leg in. We measured it: the insurance costs about 2.5× what the trade earns. The cheap replacements are rules 5 and 6 — one lone leg at a time, and a fixed bail-out price.

## 2. Session clock

| time | rule |
|---|---|
| 09:30–10:00 | **observe only** [DISCIPLINE] |
| 10:00–14:30 | entry window (Branch A needs 60 bars of history → earliest ~10:35) |
| **14:30** | **last new unpaired leg** (Branch B's own gate is ≤14:30 [FROZEN]) |
| entry+60 min | each leg's own clock: second leg unfilled → close the lone leg [SETTLED] |
| 15:30 | hard resolution: finish any survivor as a small debit spread or close it; **nothing overnight** [DISCIPLINE] |

> **In plain English:** Don't trade the open (the first half hour fakes people out — our one test entry at 9:59 sat through a 13-point slide). Do your business between 10:00 and 2:30pm. Every lone leg gets one hour to become a finished pair — waiting a second hour barely improves the odds but exposes you to all the day's disasters. By 3:30pm everything is either finished, paid off, or closed. You never take a lone leg home.

## 3. Which trade, in what order (precedence)

**The three entry setups, plainly:** we have two live setups (A and B) and one backup (C). **A** fires on heavy selling days when a weak bounce rolls over — you buy the put first. **B** fires on any day when a dip has just ended and the options-flow gauge turns up — you sell the put first. **C** is a no-HIRO fallback using price alone. The order below decides conflicts.

```
P0  SAFETY CHECKS FIRST (they always win; they only ever BLOCK short-selling):
      • SPX closed any 1-min bar below the Vol Trigger today → no lone short put   [DISCIPLINE]
      • SpotGamma levels missing/invalid → long-first only                          [DISCIPLINE]
      • HIRO: 15-min flow of BOTH "all trades" and "next expiry" < ≈ −0.8 $B
        → no lone short put (that state triples the odds of a 15-pt run-over:
        18% vs 5–7%) [asymmetry SETTLED; the −0.8 number HYPOTHESIS]
P1  BRANCH A — if today qualifies (see §4A conditions) and a bounce is failing → buy-first.
P2  BRANCH B — otherwise, when a dip ends with the flow turning up AND no safety check
      blocks shorts → sell-first.
P3  Nothing else. (Branch C only when the HIRO feed is down — and never during the test.)
TIES: A and B in the same minute → take A. One entry per episode (a continuous setup counts
      once, not every minute it stays true). ≤ 3 entries/day. One lone leg at a time. [FROZEN]
```

> **What "P0/P1/P2" means in practice:** before every entry, run three quick safety questions (has the market broken its danger line today? do I even have the SpotGamma numbers? is the options flow dumping hard right now?). If any answer says "unsafe for short puts," you simply don't do the sell-first trade — the buy-first trade is still allowed. Then: if the down-day setup (A) is on, trade it. If not, and the everyday setup (B) triggers and shorts aren't blocked, trade that. That's the entire flowchart.

**STATE FLIP** [DISCIPLINE]: *if the reason you chose your leg disappears, get out.* Concretely: you're carrying a short put because the day read as UP; by early afternoon the day now reads DOWN (definition below). Don't wait for the price cap — scratch the leg the way you would on a flow shut-off. Same for a carried long when the day flips UP.

**The leg-order context read** (~10:30, re-read ~13:00; unreadable at the open — classifiers score barely above a coin flip before 10:30):
- Technical: UP = drift from open ≥ +0.10 IM ∧ ≥80% of last 10 bars above VWAP (SPY volume-VWAP proxy) ∧ EMA5>EMA9>EMA20; DOWN = mirror; else CHOP. Provenance: spy_chaser trend toolkit Variant B. [HYPOTHESIS — sets expectations; never overrides P0–P2]
- > **In plain English:** Around 10:30, ask "what kind of day is this so far?" If the market is up from the open, has spent most of the last 10 minutes above its average traded price, and the short/medium/long moving averages are stacked upward — call it an UP day, and prefer selling the put first on dips (the day's drift helps your bounce arrive). Mirror logic for DOWN days: buy the put first on bounces. Can't tell? Buy first. Why: while you wait, a lone *long* put loses about **$22 per SPX point** if the market rallies (its delta is ~0.21 × $100/point), but a lone *short* at-the-money-ish position loses about **$49 per point** — a wrong lone long hurts less than half as much as a wrong lone short. That's the whole reason "unsure → long-first."

## 4. Entry branches — narrative first, then the exact conditions

### Branch A — the "failed bounce on a heavy day" trade (buy-first) [FROZEN — primary]

> **The story:** It's a wide-ranging, sell-pressured day — the market has already travelled a lot and the options flow has been net selling for half an hour. The market tries to bounce: it lifts 3+ points off its recent low. The bounce stalls and sags back through the midpoint of its last half-hour's range. Historically that sag finishes the move down ~88% of the time. So the moment the midpoint gives way, you buy the put (the safe leg on a down day), then rest an order to sell the put 5 points lower at your cost + 0.10 — the next leg down fills it, and your bomb is planted for a credit.

Exact conditions (all at the close of a 1-min bar; act at the next bar's open):
1. Prior-60-min SPX range ≥ its causal expanding 75th percentile (per `scripts/hiro_experiments.py::exq`; needs 60 bars → ≥ ~10:35);
2. 30-min HIRO all-flow < 0 (eligibility filter, not a direction signal — see §7 graveyard note);
3. Bounce ≥ 3 pts off the 30-bar low; 4. Close back below the 30-bar midpoint ((30-bar high + low)/2 of closes).
→ BUY the put at next open; rest the SELL 5 lower at (cost + 0.10) on the bid. Exit: scratch if price re-takes the bounce high; else §5 cap/clock. Evidence: −3 fills 0.88 (8 sessions), low adverse; C/P-divergence add-on = noise (p≈0.4). Caveat: 5 of 8 sample days were down days — expect degradation in an up week; that's what the test measures. [SETTLED for the sample]

### Branch B — the "dip just ended" trade (sell-first) [FROZEN — provisional volume generator]

> **The story:** Any ordinary day. The market dips at least 3 points. Then the options-flow gauge, which had been sinking, turns and climbs for ten straight minutes — and it's a *believable* turn: call buyers and put sellers pushing the same way, the shortest-dated options carrying at least half of it, the climb not already given back. The dip is ending. You sell the put into the last of the weakness, rest the buy 5 points higher at your sale − 0.10, and the bounce fills it. This fires 2–3 times a day and completes about half the time; its job is volume, and it's on probation because the newest sessions filled no better than random minutes.

Exact conditions: pullback ≥ 3 pts (strict 30-bar high of closes); HIRO trough-turn = run ≥ 10 min at ≥ 2 $B/hr, ΔC > 0 ∧ ΔP > 0 with min/max ≥ 0.25, ΔnextExp > 0 with share ≥ 0.5, run drawdown < 0.6 $B; gates: 15-min flow > 0, clock ≤ 14:30, weak side ≥ 0.15 $B, one entry per episode. → SELL at next open (work the bid); rest the BUY 5 higher at (sale − 0.10) on the ask. **If the flow is already steep and loud (rate ≥ 4 $B/hr and 30-min ≥ 1 $B) you're late — no entry**; the tradable moment was the quiet turn ten minutes ago. Numbers: fill 0.52 all-sample, 0.44 vs 0.48 newest 3 sessions. [FROZEN; numbers SETTLED]

### Branch C — the no-HIRO fallback (price only) [EXCLUDED during the test]

> **The story:** The HIRO feed is down. Price alone can still tell you a swing is exhausted: it has stopped making new extremes for five minutes and crossed back over its own recent average. That's worth +1–3 percentage points at best — it mostly just stops you from selling into a falling knife.

Sell-first: pullback ≥ 8 pts from the running high ∧ no new low for 5 completed bars ∧ close > running mean of typical price since the low. Long-first mirror: bounce ≥ 8 pts ∧ no new high 5 bars ∧ close < running TPM. Trading this during the test resets the test.

**Serial bombs (2–3/day):** after a fill, never re-sell where the tape is — puts are cheapest right after the bounce you just used. Rest the next order at the **neighbour strike's live quote** (next sell at its current ask-side value + 0.10; next buy at bid-side value − 0.10) and wait for the next ~3-pt swing. Realistic yield **1–2 completed/day; 3 is a good day, not a target** [SETTLED].

> **In plain English:** each finished bomb used up one wiggle. You need a fresh wiggle for the next one — so re-set your order at today's prices and let the tape come to you again. Chasing the second bomb immediately means selling cheap puts, which turns a free trade into a bet.

## 5. In-trade management — the three bail-outs

> **The story:** From the moment one leg is on and the other isn't, you own risk. Three tripwires, any of which ends the wait: (1) **the reason vanishes** — for Branch B, if within 3 minutes the flow that justified you gives back ≥ 0.3 $B or the climb formally breaks *before your first 3 points print*, scratch at the next open (cost: 1–3 pts; this rule killed 10+ bad trades across every test and never killed a winner); for Branch A the same idea reads "price re-takes the bounce high". (2) **the price cap** — the lone option marks 3.5 pts against your entry (~15 SPX pts, ≈ $350 planned loss): buy it back / sell it out, and never "fix" it by adding another strike — that manufactures a directional spread you didn't choose. (3) **the clock** — 60 minutes without the second leg: close the lone leg. Plus the P0 flow veto while carrying a short, and the state-flip scratch.

Technical: scratch constants −0.3 $B / 3 min are [HYPOTHESIS] (robustness sweep −0.2..−0.6 $B, 2–5 min pre-registered); the mechanism is [SETTLED in-sample]. Cap [DISCIPLINE]. Clock [SETTLED: hour 2 adds ~6 pp of fills and all of the tail]. Scratch is direction-appropriate: "before the completion move prints" means +3 for sell-first, −3 for long-first.

## 6. Hard limits (never override)

1. One unpaired leg at a time. [FROZEN]  2. ≤ 3 entries/day; one entry per episode. [FROZEN]  3. No ATM anchor. Ever. [SETTLED]  4. No new unpaired leg after 14:30; 15:30 hard resolution; nothing overnight. [DISCIPLINE]  5. Cost-neutral or credit only, except the 15:30 resolution. [DISCIPLINE]  6. During the test: no threshold changes; log every signal including skips and vetoes; any change resets the test. [FROZEN]  7. 1 lot, paper, until §8 passes AND the SPXW quote-level replay is done. [FROZEN]

## 7. Graveyard — tested and rejected

| idea | verdict |
|---|---|
| ATM 50Δ anchor | costs ~2.5× the credit it protects [SETTLED] |
| HIRO direction/slope/EMA-cross as entry confirmation | coincident with price (ρ≈0.7 same-minute, no 1–15-min lead) [SETTLED] |
| Smooth HIRO up-trend → sell-first mid-trend | untestable on sample after geometry fix; the "6% vs 42%" was an artifact [WITHDRAWN] |
| Steep aligned high-volume flow as a "go" | end of the move in positive gamma; ignition = the pre-steep turn [SETTLED, Aug-18 re-fire caveat] |
| ER / flip / alligator "chop" gates | weak, unstable; low-ER × mid-range stays a live lead (§8) [SETTLED-weak] |
| Prior-hour range as a directional GO | vol dial — raises fills AND tail; kept only as Branch A eligibility filter [SETTLED] |
| Retail divergence, flow vacuum, put-absorption at levels | controls matched or beat them [SETTLED, small n] |
| Quality scores / persistence bonuses | inverted — persistence anti-selects fresh turns [SETTLED] |
| Union U1–U6 tight flow scratches | right cadence, wrong exits (fill 0.32) [SETTLED] |
| C/P divergence on Branch A | p ≈ 0.4 vs matched control [SETTLED] |

> **In plain English:** we tried a dozen clever ways to make the flow gauge predict the next move. None survived a fair comparison. What survived is boring: the gauge is honest about *the present* — use it to quit, not to enter.

## 8. Acceptance test (verbatim) & what unlocks next

10 sessions, rules frozen, every signal logged (including skips, vetoes, rejects): signals ≥ 7/10 sessions · 1–3 executable entries ≥ 6/10 · ≥ 8 completions AND ≥ 1 completion on 6/10 · ≤ 3 entries/session, one leg at a time · BASE ≥ 20 signals, fill ≥ 0.45, not below its frozen clock control · TAPE ≥ 8 episodes, fill ≥ 0.70, ≥ +10 pp over its frozen midpoint control · branches reported separately, overlaps once · adverse > 10 pts on ≤ 10% of entries, max one · scratch median ≤ 3 pts · ≤ 1 scratch that would have completed · safety holds excluding the best session. Under-minimum branch → inconclusive. Any change resets the test.
**Follow-ups (≥ 20 sessions):** matched-pullback (≥ 25 pairs ≈ 4–6 weeks) and price-residualization of any HIRO entry claim; scratch-constant sweep; low-ER × mid-range; SG > 1.5 tail test at option level; negative-gamma days UNTESTED. **Option-level truth still owed** (all fills are spot-touch proxies). **[OPS]:** daily HIRO backfill; SPX 1-min refresh; flag partial captures; logs to `docs/replay/hiro/`.

> **In plain English:** we wrote the exam before sitting it. Ten sessions, no tinkering, everything logged — then the numbers either clear the pre-set bars or they don't. Touching the rules restarts the exam. Passing the exam still only unlocks the next exam (real option prices, not index touches).

## 9. The one-paragraph version

Trade the oscillation, not a view. Safety checks first; on heavy down days buy the put when the weak bounce folds (Branch A); on ordinary days sell the put when a dip ends with the flow turning up (Branch B); unsure, buy first. Rest the other leg 5 points away at cost ± 0.10 and let the tape's 80%-per-hour wiggle finish the pair. Guard the lone leg three ways — scratch when your reason disappears, bail at 3.5 points against, close at the hour — and never two lone legs, never the anchor, never overnight. One to two finished bombs a day is the honest yield. Paper, 1 lot, ten frozen sessions; nothing sizes up until the exam is passed twice.

## 10. CIO readthrough (junior-analyst comprehension check) — pending; will be appended after review.

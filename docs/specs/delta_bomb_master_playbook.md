# SPX Delta Bomb — Master Playbook (decision tree)

*v1.1 — 2026-08-22. Rewritten after three reviews: Charlie (inline), `/codex-plan-review` (FAIL 14 → all addressed), red-team completeness audit (CONDITIONAL PASS, F1–F12 + 8 missed rules → all addressed). Review artifacts: `playbook_codex_plan_review_2026-08-22.md`, `playbook_redteam_audit_2026-08-22.md`, evidence in `spx_1min_delta_bomb_leg_in_strategy.md` (EV) and the 845-session touch stats.*

> **PAPER ONLY. 1 lot. Everything here runs inside the pre-registered 10-session test (§8). Real size requires BOTH: the acceptance test passing AND the SPXW quote-level replay (still owed). Spot-touch success alone never authorizes live sizing.**

**Status tags:** **[SETTLED]** data-supported, survived review · **[DISCIPLINE]** no measured edge; keeps you out of trouble · **[HYPOTHESIS]** plausible, thin data · **[FROZEN]** part of the frozen 10-session composition — do not modify (any change resets the test) · **[EXCLUDED]** defined here for completeness but NOT traded during the test · **[OPS]** operational task, not a trading rule.

---

## 0. The trade, in one line

A **delta bomb** = 5-wide SPX put vertical legged in for zero or small credit: **sell the put on a dip, buy the put 5 points higher on a bounce** (sell-first), or the reverse (long-first). Tenor 20–40 DTE, ~20Δ base strike (white paper §2.2). The second leg needs ~**3 pts of SPX movement** (strike gap ÷ Δ; ≈3 pts at 21Δ/IV 14 — recompute from the live chain). The edge is the tape's own oscillation — a 3-pt move arrives within an hour **~80% of the time, either direction, regardless of any signal we tested** [SETTLED, 845 sessions, EV §1]. Everything else here manages *which leg you carry, when you place it, and how you bail out.*

```
   fills  = the tape's 80%/hr oscillation        danger = the lone leg while you wait
   timing = place legs at turns (discipline)     safety = scratch, cap, clock
```

## 1. Pre-market (5 minutes)

```
scheduled macro event (CPI/FOMC/opex)? ──yes──► STAND DOWN                        [DISCIPLINE]
SpotGamma levels loaded (VT, CW, SG index)?
   ├─ no, or CW−VT ≤ 0, or IM unavailable ──► LONG-FIRST ONLY today               [DISCIPLINE, EV §2a]
   └─ yes ──► note regime: SG ≥ ~1.5 & open > VT = calmer tail (30-pt runs 2.6% vs 6.4%)
              → context tag only; size is fixed at 1 lot during the test           [HYPOTHESIS]
HIRO backfill run? (vendor retains ~5 sessions; flag partial captures)             [OPS]
```

**Never, on any day: the ATM "anchor" put** — ≈ $127/bomb cost vs ≈ $50 credit over 102 replayed days; −$120 in 23 min live (2026-08-17). The cap + one-leg rule replace it. [SETTLED]

## 2. Session clock (consistent set — reviews caught the old one contradicting itself)

| time | rule |
|---|---|
| 09:30–10:00 | **observe only** (first-hour whips; the one 09:59 fire took a 13-pt slide) [DISCIPLINE] |
| 10:00–14:30 | entry window (TAPE needs 60 bars of history → earliest ~10:35 for Branch A) |
| **14:30** | **last new unpaired leg** (BASE gate is ≤14:30 by construction [FROZEN]) |
| entry+60 min | each leg's own clock: unfilled → close the lone leg (hour 2 adds ~6 pp of fills and all of the tail) [SETTLED] |
| 15:30 | hard resolution: any surviving leg → pay to finish as a small debit spread or close it; **nothing carried overnight** [DISCIPLINE] |

*(A leg opened at 14:30 runs its clock to 15:30 and hits resolution exactly — no contradiction.)*

## 3. Precedence — one ordered list (reviews: the old doc had no total order)

```
P0  SAFETY VETOES (block shorts; always win):
      • SPX closed a 1-min bar below VT today → no unpaired short           [DISCIPLINE — safety veto;
        EV labels the rule an untested adaptation, kept for crash-day cover]
      • SG levels missing/invalid → long-first only                          [DISCIPLINE]
      • HIRO 15-min all AND nextExp both < ≈ −0.8 $B → no unpaired short    [asymmetry 18% vs 5–7%
        observed, EV §4; the −0.8 threshold itself is HYPOTHESIS (one week's 60th pct)]
      • mirror veto for longs in strongly positive flow: HYPOTHESIS ONLY — the data so far
        lean AGAINST needing it (carried longs ≈ 0–1% adverse); log, don't block.
P1  BRANCH A (TAPE, long-first) — fires whenever its conditions hold          [FROZEN, primary]
P2  BRANCH B (BASE, sell-first) — only if no P0 veto blocks shorts            [FROZEN, provisional]
P3  nothing else. Branch C exists below for completeness                      [EXCLUDED during test]
TIE: A and B same minute → A. One entry per episode; overlapping signals dedupe to the earlier
     episode. ≤ 3 entries/day. (The 30-min cooldown from earlier drafts is NOT part of the frozen
     composition — episode dedup replaces it.)                                [FROZEN]
STATE FLIP: if the day-state that justified your carried leg flips against it (Charlie),
     treat it like a flow shut-off → scratch.                                 [DISCIPLINE]
```

**Leg-order context read (~10:30 and again ~13:00; NOT readable at the open — AUC 0.52–0.61 early):** UP = drift from open ≥ +0.10 IM ∧ ≥80% of last 10 bars above VWAP (SPY volume-VWAP as declared proxy) ∧ e5>e9>e20; DOWN = mirror; else CHOP. Provenance: spy_chaser trend toolkit Variant B [HYPOTHESIS — informs which branch you *expect* to fire; it never overrides P0–P2]. Rally risk on a carried long ≈ $22/pt (0.21Δ × $100) vs $49/pt on a carried short-side anchor (0.49Δ) — why unsure defaults long-first. [arithmetic from deltas]

## 4. Entry branches

### Branch A — TAPE down-day rule [FROZEN — primary]
```
prior-60-min SPX range ≥ its causal expanding 75th percentile (pooled session history,
  as implemented in scripts/hiro_experiments.py::exq — needs 60 bars, so ≥ ~10:35)
AND 30-min HIRO all-flow < 0        ← a state FILTER, not a go-signal; the graveyard row
                                       "range as a GO signal" rejected chasing range direction,
                                       not using range as an eligibility filter (EV §2d vs §7)
AND bounce ≥ 3 pts off the 30-bar low
AND close back below the 30-bar midpoint ((30-bar high + 30-bar low)/2 of closes)
   └──► BUY the put at the next bar's open (long-first); rest the SELL 5 lower at (cost + 0.10) on the bid
Evidence: −3 fills 0.88 (pooled treatment+control episodes, 8 sessions), low adverse; the HIRO
C/P-divergence add-on tested as noise (p ≈ 0.4) [SETTLED for the sample; regime-concentrated —
5 of 8 sample days were down days (Charlie): expect degradation in an up-tape week; that is
what the 10-session test measures]
EXIT (this branch): scratch if price re-takes the bounce high; else cap/clock as §5.
```

### Branch B — BASE early-turn engine [FROZEN — provisional volume generator]
```
ARM:   SPX pullback ≥ 3 pts (strict 30-bar high of closes)
       AND HIRO trough-turn: run ≥ 10 min at ≥ 2 $B/hr, calls AND puts both up (min/max ≥ 0.25),
       nextExp up with share ≥ 0.5, run drawdown < 0.6 $B
GATES: 15-min flow > 0 · clock ≤ 14:30 · weak side ≥ 0.15 $B · ONE entry per episode
   └──► SELL the put at the next bar's open (work the bid); rest the BUY 5 higher at (sale − 0.10) on the ask
Evidence: ~2–3 fires/day; fill 0.52 over all 8 sessions (0.56 on the first 5 corrected; 0.44 vs
0.48 on the newest 3 — ≈ baseline, hence "provisional") [SETTLED numbers, FROZEN rule].
Steep/loud flow (rate ≥ 4 $B/hr ∧ 30-min ≥ 1 $B) = you're LATE — no new entry. [mostly SETTLED;
Aug-18 steep re-fires won, so "late" ≈ "the early fire already happened", not "always loses"]
```

### Branch C — plain price stall, no HIRO [EXCLUDED during the 10-session test]
For reference/manual days only (HIRO feed down): sell-first = pullback ≥ 8 pts from the running high ∧ no new low for 5 completed 1-min bars ∧ close > running mean of typical price since the low → sell at next open. **Long-first mirror** (required for P0-blocked days): bounce ≥ 8 pts off the running low ∧ no new high 5 bars ∧ close < running TPM → buy at next open. Adds +1–3 pp only [SETTLED: small]; it stops you selling a falling knife. Trading this during the test resets the test.

**Serial bombs (2–3/day):** after a fill, never re-sell where the tape is (puts are cheap right after the bounce). Re-anchor the next resting order to the **neighbour strike's live quote**: next sell rests at (that strike's current ask-side value + 0.10); next buy at (current bid-side value − 0.10). Wait for the next ~3-pt swing. One unpaired leg at a time. Realistic yield **1–2 completed/day; 3 is a good day, not a target** [SETTLED, 102-day replay + live].

## 5. In-trade management

```
                    you are carrying ONE unpaired leg
                          │
   ┌──────────────────────┼────────────────────────────┐
   ▼                      ▼                            ▼
FLOW-SHUTOFF SCRATCH   PRICE CAP [DISCIPLINE]      60-MIN CLOCK [SETTLED]
(Branch-B entries;     the lone leg's option       second leg unfilled at
 direction-appropriate) marks 3.5 pts against      entry+60 → close the leg.
 within 3 min of entry, the entry (≈15 SPX pts,
 BEFORE the completion  ≈$350 planned loss) →
 move prints: HIRO      BUY IT BACK / SELL IT OUT.
 gives back ≥ 0.3 $B    Never "cap" with another
 or the run breaks →    strike (builds an
 scratch at next open.  unplanned directional
 Constants −0.3/3 min   spread) [SETTLED].
 are HYPOTHESIS
 (robustness sweep
 −0.2..−0.6 $B, 2–5 min
 pre-registered);
 mechanism: killed 10+
 duds ≤ 3 pts, cancelled
 no winner, across every
 test [SETTLED in-sample].
 Branch-A scratch = bounce-high re-take (see A).
```
Plus the P0 HIRO veto while carrying (§3) and the state-flip scratch (Charlie).

## 6. Hard limits (never override)

1. One unpaired leg at a time. [FROZEN]
2. ≤ 3 entries/day; one entry per episode; overlaps dedupe. [FROZEN]
3. No ATM anchor. Ever. [SETTLED]
4. No new unpaired leg after 14:30; 15:30 hard resolution; nothing overnight. [DISCIPLINE]
5. Cost-neutral or credit only, except the 15:30 resolution. [DISCIPLINE]
6. During the test: no threshold changes, log every signal including skips and vetoed entries; any change resets the test. [FROZEN]
7. 1 lot, paper, until §8 passes AND the SPXW quote-level replay is done. [FROZEN]

## 7. Graveyard — tested and rejected (don't resurrect without new data)

| idea | verdict |
|---|---|
| ATM 50Δ anchor (paper §2.1b) | costs ~2.5× the credit it protects [SETTLED] |
| HIRO direction/slope/EMA-cross as entry confirmation | coincident with price (ρ≈0.7 same-minute, no 1–15-min lead) [SETTLED] |
| Smooth HIRO up-trend → sell-first mid-trend | untestable on the sample after geometry fix (1–2 clean episodes); earlier "6% vs 42%" was an artifact [WITHDRAWN, not settled-dead] |
| Steep aligned high-volume flow as a "go" | marks the end of the move in positive gamma; the ignition is the pre-steep turn [SETTLED, with the Aug-18 re-fire caveat] |
| ER / flip-count / alligator "chop" gates | weak (2–6 pp), unstable; **low-ER × mid-range remains a live test lead (§8)** [SETTLED-weak] |
| Prior-hour range as a directional GO signal | it's a vol dial — raises fills AND tail together; kept only as Branch A's eligibility filter [SETTLED] |
| Retail divergence, flow vacuum, put-absorption at levels | controls matched or beat them [SETTLED, small n] |
| Quality scores / persistence bonuses | inverted — persistence anti-selects fresh turns [SETTLED] |
| Union U1–U6 tight flow scratches | right cadence (2.4/day), wrong exits (fill 0.32) [SETTLED] |
| C/P divergence on Branch A | p ≈ 0.4 vs matched control [SETTLED] |

## 8. Acceptance test (verbatim from the frozen registration) & what unlocks next

Over the next 10 sessions, rules frozen, every signal logged (including skips, vetoes, and rejects):
- **Frequency:** signals on ≥ 7/10 sessions; 1–3 executable entries on ≥ 6/10.
- **Production:** ≥ 8 completed bombs total AND ≥ 1 completion on 6/10 sessions; ≤ 3 entries/session; one leg live at a time.
- **Efficacy:** BASE ≥ 20 qualifying signals with fill ≥ 0.45 and not below its frozen clock-matched control; TAPE ≥ 8 qualifying episodes with fill ≥ 0.70 and ≥ +10 pp over its frozen midpoint-matched control; BASE, TAPE and composite reported separately, overlaps counted once.
- **Risk:** adverse > 10 pts on ≤ 10% of entries and no more than one such trade; median scratch loss ≤ 3 pts; ≤ 1 scratch that would have completed within its 60-min horizon; safety criteria still hold excluding the best session.
- Branch below its sample minimum → **inconclusive** (not failed, not validated). Any rule change resets the test.

**Pre-registered follow-ups (≥ 20 sessions):** matched-pullback test (needs ≥ 25 pairs ≈ 4–6 more capture weeks) and price-residualization of any HIRO entry claim; scratch-constant robustness sweep (−0.2..−0.6 $B / 2–5 min); low-ER × mid-range price-only candidate; gamma-regime (SG > 1.5) tail test at option level; negative-gamma days are UNTESTED — assume nothing transfers. **Option-level truth:** all fills are spot-touch proxies until the SPXW quote-level replay runs. **[OPS]:** daily HIRO backfill; SPX 1-min refresh; flag partial captures (e.g. a session cut at 15:26 censors late windows); logs to `docs/replay/hiro/`.

## 9. The one-paragraph version

Trade the oscillation, not a view. Let the safety vetoes speak first, carry the leg the day is helping (down-day tape rule long-first when it fires; otherwise the early-turn sell-first if shorts aren't vetoed; unsure → long-first), place the leg at a turn after a real 3-pt swing, rest the other leg 5 points away at cost ± 0.10, and let the tape's 80%-per-hour wiggle finish the pair. Protect the lone leg with the scratch, the 3.5-pt cap, and the 60-minute clock; never two lone legs, never the anchor, never overnight. The flow gauge's proven job is telling you when your reason is gone — the entries themselves are tape. One to two finished bombs a day is the honest yield; the next ten sessions test this exact composition once, on paper, and nothing sizes up until they pass and the option-level replay agrees.

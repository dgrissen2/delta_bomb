# SPX 1-min delta-bomb leg-in strategy — evidence, errata, CIO memo, plain-mechanism explanation

> Moved verbatim from `p1_nvda_tail_sale_backtest.md` §18 on 2026-08-18 (only section numbers changed: 18 → 1). Codex reviews: `s18_codex_plan_review_2026-08-18.md`, `spx_bomb_codex_strategy_review_2026-08-17.md`. Touch-stat data: `docs/replay/spx_touch_stats_full.parquet`, `spx_touch_stats_full_dn.parquet`.

## 1. SPX leg-in evidence from the 1-min trend-catching work (spy_chaser) — added 2026-08-18

> Scope note: this section is about the **SPX put delta bomb** (the white paper's intraday 5-wide legged spread), not the
> NVDA tail-sale program P1 above. It is filed here because it is the same research thread and the same reviewers.
> §1.0 is reproduced word for word from the working session; §1.1 is the CIO memo; §1.2 the plain-mechanism explanation.

### 1.0 Findings and implications (verbatim)

What the 1-min trend-catching work found (SPX, 485 gate days + 107 below-VT days)

1. Trend is not detectable early enough to act on. 09:35–09:45 classifiers (OR breakout, VWAP persistence, EMA stack, drift-vs-VT) have OOF AUC 0.52–0.61; only by noon 0.78–0.86 — descriptive, not tradeable. The one 09:35-detectable thing (the "popper", move935 ≥ θ) is already priced the moment you see it.
2. Every ride/trailing-stop rule captured ≈ 0. On S1 grind days the true peak was +12 pts, but the grind's own ~10–12 pt (≈2.5 OR-spread) pullbacks whipsawed every trailing exit; >50% of exits sold below the 09:45 level. Below-VT: 61/85 sub-par days had a genuine ≥70 bp up-leg (median 92 bp) and three independent approaches — churn, hold, wait-for-clean-alligator — all captured −2% of it; the clean entries landed 60% up the day's range with 33 bp left. Verdict quote: "a wide/steep/clean alligator here is an exhaustion signal, not a continuation one → if anything the edge is in FADING it."
3. The one live remnant was a 09:45 veto (VT held on a closing basis, Call Wall respected — WHETHER to trade, not WHEN), and sizing on the popper (1.5× on detected up-context days), never timing.

What that means for the delta bomb — it's confirmation, and it hands you the placement rule

- The bomb is a fade structure (sell the put when the down-swing is spent, buy when the up-swing is spent). The trend work says the 1-min SPX tape is mean-reverting at exactly the amplitude you need (10–12 pt pullbacks against 3–7 pt legs), and that "clean trend" on 1-min is where moves die. So Rule 1 isn't a heuristic — it's the empirical result of a whole worktree that tried the opposite and lost.
- Use the roll-over triggers as leg triggers, mirrored: sell leg = down-move stalled: no new session low for 3–5 one-min bars + close back above the 5-bar typical-price mean/VWAP (or a failed probe of a level, e.g. VT/Put Wall) → sell the put at the bid now and rest the buy at sale − 0.10. Buy leg = the mirror (no new high for 3–5 bars + close back below TPM, or a failed Call-Wall probe). This replaces "park a number and hope" with "act at exhaustion", which is what the paper's 7-minute plants actually were.
- Use the veto for whether to leg at all: Brent's band position — pos = (O−VT)/(CW−VT) ≥ 0.7 or room_to_CW ≤ 0.5 → up-move capped → sell-first (which needs the bounce) is the worse order; long-first is fine. VT lost on a closing basis → don't open an unpaired short. Live efficiency = |close−open|/path over the last 60 bars > ~0.5 → one-way tape, hold off; < ~0.3 → chop, go.
- The 60-minute rule is cheap: from my touch table, 4 bp completes 80% within 60 min vs 86% within 120 — the second hour buys only +6 pts of completion while carrying the whole adverse tail. Paper's rule stands.
- Don't try to time direction with these tools — the worktree proved the ORACLE value exists (+$2k/yr) but is locked behind a sign nobody can read at decision time. Bombs don't need it; they need the retrace, which is the 85% event.

Reusable code, specifically

- Triggers/toolkit: spy_chaser/scripts/{calibrate_rollover.py, decision_timing.py, classify_945_states.py, detect_early_movers.py, popper_935_rule.py, tune_S1_rollover.py}; below-VT: .claude/worktrees/below_vol_trigger/eda/{bvt_ride_v3.py, bvt_day_chart.py, bvt_day_chart_backtest.py, bvt_r2_clean_trend_days.py, bvt_5m_brutal_reversal_test.py} — the entry/exit detectors are exactly the exhaustion detectors you want, just run with the sign flipped.
- Data: §34 parity spot 1-min / real SPX 1-min OHLC (853 days), SG levels, spx_l1_l2_strict_universe_2020-2026.csv for VT/CW/IM per day.

Next concrete step, if you want it: condition my touch table on "entered at a stall trigger" vs "entered anytime" — P(complete in 60 min) and P(adverse > 20 bp) for each — so we know how much the exhaustion trigger actually buys. That's a ~1-hour script on data already local; I'd write it as scripts/spx_legin_ev.py.

Supporting table referenced above ("my touch table"; SPX 1-min OHLC, 845 sessions 2022-01-03→2026-06-30, starts every 15 min 10:00–14:30, 16,055 attempts; `docs/replay/spx_touch_stats_full.parquet`):

| X (bp of SPX) | window | P(up-touch) | P(down-touch) | P(up X then back down X) | median adverse move before up-touch | P(adverse > 20 bp) | P(adverse > 40 bp) |
|---|---|---|---|---|---|---|---|
| 4 (~3 pts) | 60 min | 0.80 | 0.78 | 0.56 | 4 bp | 15% | 5% |
| 4 (~3 pts) | 120 min | 0.86 | 0.84 | 0.68 | 4 bp | 17% | 7% |
| 8 (~6 pts) | 60 min | 0.64 | 0.62 | 0.32 | 7 bp | 22% | 7% |
| 8 (~6 pts) | 120 min | 0.74 | 0.71 | 0.46 | 8 bp | 27% | 11% |

By SpotGamma regime (X = 8 bp, 120 min): open above Vol Trigger — up-touch 0.73, adverse > 40 bp 10%; open below — 0.79 and 14%.
Sources: `~/Dev/spy_chaser/hypothesis_tracking/uptrend_timing_full_investigation_2026-06-10.md`, `intraday_timing_trend_toolkit_2026-06-10.md`,
`.claude/worktrees/below_vol_trigger/outputs/bvt_daychart_overtrade_and_ride_findings.md`; touch table computed 2026-08-17 in this repo.

### 1.0a Errata and clarifications after Codex plan review (2026-08-18) — §1.0 is left verbatim; read it with these

1. **AUC figures** come from `below_vol_trigger/hypothesis_tracking/h-bvt-019_trend-vs-chop-classifier_2026-06-27.md` (strong-trend day: OOF AUC 0.609 at 09:35, 0.589 at 09:45, 0.777 by noon; era-stable) and `h-bvt-001_c-classifier-gate_2026-06-27.md` (no-reclaim regime: 0.52 / 0.60 / 0.86). AUC is discrimination, not accuracy.
2. **Touches are spot moves, not option fills.** The table measures whether SPX travels X bp; a bomb leg fills when the *option* moves gap + c, which at ~21Δ / 32 DTE / IV ≈ 14 is ≈ 3 SPX pts, but that mapping changes with delta, IV and quote width and is not modelled here. "Completes" in §1.0 means "the one-way spot move needed to fill the second leg occurred". The **round trip** (leg fills, then the next opposite leg's move also occurs) is the `alt` column: 56% / 68% at 4 bp for 60 / 120 min — the second hour adds ~11 pp to the round trip, ~6 pp to the one-way move.
3. **Exhaustion placement is a hypothesis, not a measured rule.** The mechanism is supported by the trend work; its effect on P(complete) / P(adverse) for this trade is untested. Pre-registered test (`scripts/spx_legin_ev.py`): trigger = no new session low (high) for 5 one-min bars and close back above (below) the 5-bar mean of typical price (H+L+C)/3; baseline = anytime entry at the same clock minute; fit 2022–2024, hold out 2025–2026-07; adopt only if P(one-way move within 60 min) rises ≥ 5 pp **or** P(adverse > 20 bp) falls ≥ 5 pp out of sample, with bootstrap 90% CI excluding zero; otherwise the trigger is dropped and only the timing-agnostic rules stand (no anchor, one unpaired leg, 60-min clock, price cap).
4. **Units:** the source describes the grind pullbacks as ≈ 2.5 u where u = max(0.10 × IM, 4 pts) (uptrend doc §5.2–5.3), not 2.5 opening-range spreads. The below-VT clean-rule failure is attributed by its source primarily to entering ~60% up the range with ~33 bp left; its three approaches were churn, hold, and wait-for-clean. The alligator quote ends "…if anything the edge is in FADING it, not following."
5. **Definitions for the live rules** (proposed, to be calibrated in the same script): efficiency = |close_now − close_60 bars ago| / Σ|Δclose| over the last 60 bars (0.5 / 0.3 cut-points are placeholders); "hard price cap" = the unpaired short is bought back or capped with the next-lower strike when its mark ≥ sale + 3.5 (≈ 15 SPX pts at 21Δ). If SpotGamma levels are missing, or CW − VT ≤ 0, or IM is unavailable, the band-position rule is not applied and only long-first is permitted.
6. **Band position selects leg order; the veto is VT-hold.** pos ≥ 0.7 or room_to_CW ≤ 0.5 → prefer long-first (a capped up-move is the sell-first leg's fill path). The veto on opening any unpaired short is a 1-min close below the Vol Trigger (toolkit's untested "trade veto"). §1.1 is worded accordingly.
7. **Adverse-tail figures are per direction, both computed:** before an up-move of 4 bp within 120 min, adverse > 20 bp in 17.4% / > 40 bp in 7.3% of attempts (`spx_touch_stats_full.parquet`, `mae_up`); before a down-move, 17.5% / 6.0% (`spx_touch_stats_full_dn.parquet`, `mae_dn`). 20/40 bp ≈ 15/30 pts only at SPX ≈ 7,500–7,800. Static-delta cost of a 30-pt excursion at 21Δ ≈ $630 per contract; the "≈ $800" in the memo allows for gamma (delta rising as SPX falls) and is an estimate, not a model output.
8. **Provenance:** raw store 853 sessions (2022-01-03 → 2026-07-10); 8 half-days with < 380 bars excluded (2023-07-03, 2023-11-24, 2024-05-30, 2024-07-03, 2024-12-24, 2025-07-03, 2025-11-28, 2025-12-24) → 845 eligible sessions, endpoint 2026-07-10 (not 06-30 as written above).

### 1.1 CIO memo — in simple terms (revised after Codex review)

**What we looked at.** Our own `spy_chaser` research spent a full cycle trying to catch intraday SPX trends on 1-minute bars (485 positive-gamma "gate" days plus 107 below-Vol-Trigger days). It failed in a specific and useful way: whether the day will trend cannot be read at the open (the classifiers barely separate trend from chop until noon), every trailing-stop or "ride the move" rule was shaken out by the market's own 10–12 point pullbacks, and on the below-Vol-Trigger days three different approaches — trade often, hold, or wait for a clean trend — each captured about nothing of the moves that were there, because by the time a trend looked clean most of it was spent. The only things that survived were a veto (do not trade when the Vol Trigger fails on a closing basis) and position sizing — never timing.

**Why that matters for the SPX delta bomb.** The bomb is the mirror-image trade. It does not need SPX to trend; it needs SPX to move about 3–7 points, because we sell the put on a dip and buy the strike above on the bounce (or the reverse). Measured on 845 sessions of 1-minute SPX data (16,055 attempts), a 3-point move in the needed direction arrives within 60 minutes 78–80% of the time and within two hours 84–86% of the time — the same up or down — so the process does not require being right on direction. Two honest caveats: those are moves in the index, not option fills, and the full cycle (one leg fills, then the next opposite leg's move also arrives) is 56% within an hour and 68% within two. What the trade does require is surviving the path: in about 17% of attempts SPX first runs 15+ points against the open leg (6–7% run 30+ points) before giving us the move we need, and that is where the losses in this strategy live.

**What changes in how we trade it.** Two rules are settled by data, two are hypotheses we will trade cautiously and test. Settled: (1) no ATM "anchor" put — in the 102-day replay it cost about $127 per bomb against ~$50 of credit and is the whole reason the first live bomb lost money; (2) one unpaired leg at a time, the paper's 60-minute clock, and a hard cap on any unpaired short (bought back or capped when it is 3.5 points against us, about 15 SPX points) — the second hour adds only ~6 points of probability that the needed move arrives while carrying the entire adverse tail, and a 30-point excursion costs roughly $630–800 per contract, which the small credits cannot pay for; only the spread's exit or hedge value can. Hypotheses: (3) place each leg at exhaustion, using the roll-over detectors the trend work already built with the sign flipped (down-move stalls → sell the put; up-move stalls → buy the higher strike); (4) use the gamma-band position to choose which leg goes first (pressed to the Call Wall → long-first) and a 1-minute close below the Vol Trigger as the veto on opening any unpaired short.

**Decision.** Hold as operating rules for discretionary 1–3 lot trading; do not promote to a systematic program. The anchor question is closed (drop it). The exhaustion-trigger claim is mechanistically supported but not yet measured for this trade — the one experiment worth funding is `scripts/spx_legin_ev.py` (about an hour on data already local): the same touch table conditioned on "entered at a stall trigger" versus "entered anytime", fit on 2022–2024 and held out on 2025–2026, reporting P(needed move within 60 min) and P(adverse > 20 bp). Adoption is pre-registered: the trigger stays only if it improves one of those two numbers by at least 5 percentage points out of sample; otherwise it is dropped and we keep the settled rules — a high-hit-rate process with a managed tail, not a directional call.

### 1.2 The mechanism in plain terms — a Feynman-style explanation

Let's not start with the names. Look at one thing: a one-minute chart of the S&P 500 on an ordinary day. It does not go anywhere in a straight line. It goes up ten points, gives back seven, goes up eight, gives back nine. If you slow it down and measure — and we did, 845 days of it — a three-point wiggle in whichever direction you happen to need shows up within an hour about four times out of five, and it does not care which way you were leaning. Now, the trend-catching project asked the opposite question of the same chart: can I ride the ten-point moves? Every rule it tried got shaken off by the seven-point give-backs, and by the time a move looked "clean" enough to trust it was mostly over. So the chart told us something in two different ways at once: at this scale it wiggles more than it walks.

Here is why that is exactly what the delta bomb needs. The bomb is two orders that only make sense as a pair: sell a put when the market has just dipped (puts are a little dearer then), and buy the put five points nearer to the money when the market has just bounced (puts are a little cheaper then). The two prices differ by about sixty cents at any instant, so to buy the dearer strike for no more than you sold the cheaper one, the whole put ladder has to sag by sixty-odd cents between your two orders — which is about a three-point rise in the index. That is all. You are not predicting where the S&P closes; you are waiting for one three-point wiggle, and the chart hands those out generously. Direction is not the trade. The wiggle is.

So where does the money get lost? Not on the pair — a finished pair is free by construction. It is lost in the gap between the two orders, when you are holding one leg alone. Four times in five the wiggle comes quickly and nothing happens. But about one time in six the market first walks fifteen points the wrong way, and one time in fourteen it walks thirty, before it comes back — and while it walks, your lone leg bleeds, and your resting second order sits further away than ever. That is the whole risk in one sentence: the trade fails not because you were wrong about direction, but because you had to wait, and waiting occasionally costs more than many finished pairs are worth. That is why the rules are about the wait, not the view: one lone leg at a time, a clock on it, a price at which you give up, and no expensive "anchor" put bought to feel safe during the wait — that anchor cost more than the pair it was guarding.

Here is how you could catch me if this picture were wrong. If the index at one-minute scale trended more than it wiggled, the touch table would show the second leg arriving rarely and the adverse excursions dominating — it shows the reverse. If placing legs "at exhaustion" (right after a small move stalls) really helps, then attempts entered at those moments should complete more often, or get run over less, than attempts entered at random minutes; we have not measured that yet, so it stays a hypothesis with a pre-registered test, and if the numbers do not move, we drop it. And here is what I have simplified: the sixty-cent gap is not fixed — it grows when volatility rises and shrinks when it falls, so "three points" is today's number, not a law. The sentence to say back is: I am not betting on where the market goes; I am selling one leg on a dip and buying the other on a bounce, the bounce almost always comes, and the entire job is to make sure the rare times it doesn't come quickly are small.

## 2. The signal stack for planting quickly — assembled from the 1-min evidence (verbatim, 2026-08-18)

Here's the stack, assembled only from what the 1-min work actually measured. Everything below is "confirmed turn", not "knife" — the one lesson that repeated in every worktree (trend timing, VT-reclaim, bottom-detection): **precise-extreme callers were more precise and made less; the confirmed reclaim paid.**

### The signal stack for planting quickly (SPX, 1-min)

**0. Units first (so thresholds don't drift with vol)**
- `u = max(0.10 × IM, 4 pts)` — the "ruler" from the trend toolkit; grind pullbacks measured ≈ 2.5 u (10–12 pts). Your leg needs ~0.75 u. Alternative unit: `ORspread` = 09:30–09:34 range.
- ATR(1-min) for bar-shape tests; IM from `im_estimator.py`; VT/CW/PW from `spotgamma_fixed`.

**1. Regime & veto (decides WHETHER and WHICH LEG FIRST — the only things the trend work found survivable)**
- Veto on any unpaired short: a 1-min **close below VT** (toolkit's live remnant). No SG levels → long-first only.
- Band position `pos=(O−VT)/(CW−VT)`, `room=(CW−O)/IM`: pos ≥ 0.7 or room ≤ 0.5 → up-move capped → **long-first**; 0.25 < pos < 0.7 & room ≥ 1 → either order; pos ≤ 0.25 (sitting on VT) → coin-flip tape, smallest size.
- Time window **10:00–14:00**: first touches before 2 pm whip (median 4 episodes, only 25% commit); the last ~1.5 h is where pokes become breaks (25–34% of first touches, single sustained move). Don't open an unpaired leg after ~14:30.
- Below-VT/sg<0 days: more oscillation ("the close round-trips") but fatter adverse tail (>40 bp 14% vs 10%) → same rules, half size.

**2. Setup — the swing must be *spent*, not starting (arm the leg)**
- Run from the last swing extreme ≥ **2 u** (≈ 8–12 pts) or ≥ 0.2 IM — that's the measured pullback amplitude; below that you're fading noise, above 3 u you're in a trend leg (efficiency test below).
- **Mature alligator in the direction you're about to fade** — the v3 gate run as an *exhaustion* detector (its own verdict): `e5<e9<e20`, `(e20−e5)/ATR ≥ 0.8`, 5-bar steepness ≥ 0.5, ≥ 90% of last 10 closes below e5, clean bodies (mean body/range ≥ 0.5). When that prints on a down-move, the sell-put setup is armed; mirror (`e5>e9>e20`) arms the buy-leg.
- Chop confirmation over the last 10–20 bars: Kaufman ER(10) < ~0.3 or ≥ 4 VWAP flips → oscillating tape (both legs will fill); ER > 0.5 over 60 bars → one-way tape, stand down.

**3. Trigger — the confirmed turn (fire the leg)** — need 2 of 3, all price-only, all from the toolkit/BVT scripts:
- **Stall:** no new session/swing low for **3–5 one-min bars** (Chart-Analyst roll-over rule, mirrored).
- **Reclaim:** 1-min close back above the 5-bar TPM ((H+L+C)/3 mean) or e5, and/or a lower-low that fails by < 0.15 ORspread (the "lower swing high" rule inverted).
- **Reversal bar / failed probe:** bullish version of the 5-min "brutal reversal" (close>open, range ≥ 1.2×ATR, body/range ≥ 0.55, close > prior-2-bar high) **or** a failed probe of a level — low within 0.1–0.25 IM of VT/Put Wall/round strike then close back above (dealer-buy-the-dip signature; pokes are median 2/day, ~7 pts deep, revert ≈ breach by depth so don't try to read depth).
- Optional vol tell (needs the 1-min IV legs, §35/§36): put-skew **steepening into the flush** → bounce more likely (ρ +0.51); ATM IV **still rising** → stays down (ρ −0.37). If ATM IV is still rising, don't fire.

**4. Execution (the paper's rules with the numbers attached)**
- On trigger: **sell the put at the bid immediately**, rest the buy 5 higher at sale − 0.10. Clock 60 min (one-way move arrives 80% in 60 vs 86% in 120 — the second hour isn't worth the tail). Cap: unpaired short ≥ sale + 3.5 (~15 pts) → cap with the next-lower strike or buy back. One unpaired leg. No anchor.
- **Buy leg = the exact mirror** at the top of the bounce: no new high 3–5 bars + close below TPM/e5, or bearish brutal-reversal bar, or failed CW probe (tag CW − 0.1·IM, no new high 3 bars).
- After a fill, re-anchor the next resting limit to the neighbour's current ask + c, not to the last number.

**5. Anti-signals (what the evidence says to ignore or fear)**
- Don't classify direction at 09:35–09:45 (AUC 0.52–0.61); don't use EMA crosses as a trend engine (demoted in the toolkit); don't wait for the "clean" alligator to *follow* it (captured −2%).
- Fast early mover (`emove ≥ 5u` by 09:50) = the day's pop is already priced; treat the first hour as veto/observation, not planting.
- A brutal-reversal bar *against* your open leg = exit/cap now, don't wait for the clock.

**Status:** every component is measured on its original question; the *combination as a bomb trigger* is not — that's `scripts/spx_legin_ev.py` (trigger = stall + reclaim; baseline = anytime; fit 2022–24, hold out 2025–26; adopt only if P(one-way move in 60 min) +5 pp or P(adverse > 20 bp) −5 pp). All inputs are local: SPX 1-min OHLC (853 d), SPY 1-min w/ volume for VWAP, SG levels, IM estimator, and the BVT/toolkit scripts named above.

### 2b. Timeframes and exact code references per component (added 2026-08-18)

Each row states the bar size and lookback the source actually used, the data it ran on, and the file/function/constant. Where the bomb rule adapts the source (different bar size, mirrored sign, new threshold), it is marked **adaptation**.

| # | Component | Timeframe / lookback in the source | Source data | Code reference | Adaptation for the bomb |
|---|---|---|---|---|---|
| 0 | `u = max(0.10 × IM, 4 pts)` ruler | daily IM (prior-day IV), applied to 1-min spot | SG implied move; `im_estimator.py` | `~/Dev/spy_chaser/scripts/tune_S1_rollover.py` (`day["u"]`, `exit_tw`), `scripts/detect_early_movers.py` (`u`), `hypothesis_tracking/uptrend_timing_full_investigation_2026-06-10.md` §5.2–5.3; `.claude/worktrees/worktree-implied-move/scripts/{im_estimator.py, im_common.py}` | none |
| 0 | `ORspread` | 09:30–09:34 (five 1-min bars) | SPX parity spot 1-min (§34) | `hypothesis_tracking/intraday_timing_trend_toolkit_2026-06-10.md` §A (Chart-Analyst) | none |
| 1 | VT close-below veto | 1-min **close** vs VT, source window 09:30–09:45 | SG levels `spotgamma_fixed/offset_historical_FIXED_2026-06-14.csv`; parity spot | toolkit §A "VT-hold integrity"; `below_vol_trigger/hypothesis_tracking/h-bvt-001_c-classifier-gate_2026-06-27.md` (`close<vt` regime); `eda/bvt_common.py: anchored_series()` | **adaptation:** applied all session, not just 09:30–09:45 |
| 1 | Band position `pos`, `room_to_CW` | daily open vs VT/CW/IM | `below_vol_trigger/data/spx_l1_l2_strict_universe_2020-2026.csv` (vt, im, gap_im) | toolkit §A (Brent) cut-points 0.7 / 0.5 / 0.25 / 1.0 | **adaptation:** used for leg order, not trade veto |
| 1 | Time window 10:00–14:00 | first-touch time-of-day on **5-min** parity underlying, 214 touch days | `thetadata/spx_0dte_intraday_underlying` (§28) | `scripts/run_intraday_touch.py`, `scripts/run_intraday_breach_timing.py` (`feats`, `main`); `hypothesis_tracking/sgi-voltrigger-0dte-call-harvest_2026-06-08.md` §33–35 | **adaptation:** touch stats were for a level above spot; the "last 1.5 h commits" read is transferred, untested for dips |
| 1 | Below-VT half size | daily regime; my touch table by regime on SPX 1-min | `spotgamma_fixed`; `docs/replay/spx_touch_stats_full.parquet` | `below_vol_trigger/hypothesis_tracking/memo-bvt-below-vt-regime_2026-06-27.md`; this repo `scripts/spx_touch_stats.py` | none |
| 2 | Run ≥ 2 u from last swing | 1-min parity spot, S1 days 09:45 → peak; pullbacks ≈ 2.5 u | §34 parity spot | `scripts/tune_S1_rollover.py: exit_tw(a, c, cap), exit_ml(L)`; uptrend doc §5.3 | **adaptation:** 2 u arm threshold is proposed, not measured |
| 2 | Mature alligator (exhaustion) | **SPY 1-min OHLCV**: EMA5/9/20, ATR (1-min), VWAP; rails 10 bars, steepness 5 bars, clean 5 bars, size CV 3 bars | `databento/spy_ohlcv_1m/spy_ohlcv_1m.parquet` | `below_vol_trigger/eda/bvt_ride_v3.py: strong_up()` with `SPREAD_MIN=0.8, STEEP_MIN=0.5, RAIL_N=10, RAIL_FRAC=0.9, CLEAN_N=5, CLEAN_BODY=0.5, SIZE_CV_MAX=0.6`; `eda/bvt_day_chart.py` (`JAW_WIDE=0.30, JAW_MIN=0.15, MID_MIN=0.15, EXPANSION_T=1.6, DISP_ATR=1.0, ADX_MIN=20`) | **adaptation:** run on SPX 1-min (or SPY as proxy) with the sign flipped (down alligator arms the sell) — the source ran it as an entry, found it marked exhaustion |
| 2 | ER(10) / VWAP flips | 1-min bars, 10-bar Kaufman ER; VWAP-flip count over prior 10 bars; 5-min ER + ADX(14) diagnostic | SPY 1-min | `below_vol_trigger/outputs/chop_avoidance_brief.md` (ER buckets <0.15/0.15–0.30/0.30–0.50/>0.50; ≥6 flips), `eda/bvt_5m_er_compare.py` (`ER_REF=0.40`) | **adaptation:** cut-points 0.3 / 0.5 and 4 flips are proposed |
| 2 | Efficiency over 60 bars | source computes day-level `efficiency = |close−open| / path` | SPY 1-min | `eda/bvt_r2_clean_trend_days.py: cleanness()` | **adaptation:** rolling 60-bar version is new |
| 3 | Stall (no new low 3–5 bars) | 1-min: toolkit §B "no new session high for 5 bars (alt 3)"; `exit_ml(L)` = spot < spot[i−L]; early-mover stall = two down closes off a fresh high (09:35–10:15) | parity spot 1-min | toolkit §B; `scripts/tune_S1_rollover.py: exit_ml`; `scripts/detect_early_movers.py: stall_exit()` | mirrored to lows |
| 3 | Reclaim (TPM / e5 / failed lower-low) | 1-min: TPM = running mean of typical price (persona spec, uptrend doc §5.2); "fresh VWAP loss"; lower swing high < HH − 0.15·ORspread; ride_v3 exit = 2 consecutive closes below e9 | parity spot / SPY 1-min | toolkit §B; `bvt_ride_v3.py: ride()` | mirrored; 5-bar TPM window is proposed |
| 3 | Reversal bar | **5-min** bars: close<open, range ≥ 1.20×ATR(5-min), body/range ≥ 0.55, close < prior-2-bar low | SPY 5-min aggregated from 1-min | `below_vol_trigger/eda/bvt_5m_brutal_reversal_test.py` (`REVERSAL_RANGE_ATR_MULT=1.20`) | mirrored (bullish) for the sell leg |
| 3 | Failed level probe | 1-min bars vs SG levels: tag CW − 0.1·IM + no new high 3 bars; touch ≥ CW − 0.25·IM then close back below; poke depth stats on 5-min underlying (median 6.8 pt revert / 7.1 pt breach; 2 pokes/day) | SG levels; §28 5-min underlying | toolkit §B (Brent); sgi doc §33–35; `scripts/run_intraday_touch.py` | mirrored to VT/Put Wall for dips |
| 3 | IV tell (optional) | **daily** correlations at 10:30 across 104 VT-loss days (put-skew steepening ρ +0.51; ATM IV rising ρ −0.37); 1-min IV legs exist | `thetadata/spx_0dte_1m_iv_vtloss` (§35), `§36` opening IV; `worktree-implied-move/scripts/build_vtday_iv_1m.py` | `hypothesis_tracking/vt_breakdown_recovery_2026-06-11.md` | **adaptation:** intraday use at 1-min is untested |
| 4 | 60-min clock, cap, one leg | SPX real 1-min OHLC, 845 sessions, starts 10:00–14:30 | `thetadata/spx_index_1m_ohlc` | this repo `scripts/spx_touch_stats.py` → `docs/replay/spx_touch_stats_full{,_dn}.parquet` | cap = sale + 3.5 is proposed |
| 4 | Buy-leg mirror / re-anchor limit | live quotes | Schwab chain | this repo (session notes; `scripts/replay_50_20.py` fills at limit on 5-min greeks) | — |
| 5 | AUC / no early direction | features at 09:35, 09:45, 12:00 cuts (`CUTS = open 575, early 585, noon 720`) | SPY 1-min + parity spot | `below_vol_trigger/eda/bvt_r1_features.py`; `h-bvt-019`, `h-bvt-001` | none |
| 5 | Popper / early mover | 1-min: `emove = (max spot 09:35–09:50 − open)/u`; `move935 = (spot_0935 − open)/u` | parity spot 1-min | `scripts/detect_early_movers.py`, `scripts/popper_935_rule.py` (`GRID 575..660, RIDECAP 630`) | used as veto only |

**Timeframe consistency note.** The sources mix three price series: SPX 0DTE parity spot 1-min (toolkit, poppers, roll-over), SPY 1-min OHLCV (all BVT alligator/ER/VWAP work — SPY, not SPX), and 5-min bars (reversal bar, touch/revert depth). For the bomb, standardise on **real SPX 1-min OHLC** for every price rule, aggregate to 5-min only for the reversal bar, and use SPY 1-min only where volume is required (VWAP). Thresholds ported from SPY (ATR multiples, bp) must be re-derived on SPX before use.

### 2a. Adjustments after `/codex-strategy-review` (2026-08-18; verdict FAIL, 13 findings — full text in `spx_signal_stack_codex_strategy_review_2026-08-18.md`)

§2 and §2b are left as written. The review is accepted on the substance: the stack was assembled from components that were each measured on a *different* question (0DTE calls, SPY bars, positive-gamma days, top-detection), then combined and mirrored without an end-to-end test. Dispositions, then the reduced stack that survives.

| # | Finding | Disposition |
|---|---|---|
| 1 | Stack untested as specified; proposed test covers only stall + reclaim | Accepted. The live stack is reduced to what the test covers (below); everything else becomes a diagnostic column in the test, not a rule. |
| 2 | Evidence transferred across SPY/SPX, 0DTE/32-DTE, positive/negative gamma | Accepted. All price rules re-derived on real SPX 1-min OHLC; SPY used only for VWAP; option-level outcomes measured on SPXW greeks (5-min, 102 days) and 1-min quotes, not inferred from spot. |
| 3 | `≥ 2u or ≥ 0.2 IM` collapses to the weaker test; 0.75u leg claim unmeasured | Accepted. Arm rule = run ≥ 2u only (u = max(0.10·IM, 4)). "~0.75u per leg" withdrawn; the leg requirement is gap/Δ measured from the chain at the time (≈ 3 pts on 2026-08-17). |
| 4 | Failed continuation ≠ validated fade; mirrored alligator is a new detector | Accepted. Alligator removed from the live stack; kept as a diagnostic (does a mature down-alligator at trigger time change plant rate / adverse excursion?). |
| 5 | Chop gate contradicts the chop brief (ER ρ≈0; 6+ flips best) | Accepted. ER / flip-count / rolling-efficiency gates removed from the live stack; ER(10) and flip count logged as diagnostics only. |
| 6 | Stall/reclaim don't match cited code (`exit_ml`, `stall_exit`, TPM running mean, e9 two-close) | Accepted. Trigger restated to the toolkit's own definitions: no new running low over the last 5 completed 1-min bars **and** a completed-bar close above the **running** TPM (mean of (H+L+C)/3 since the running low). `exit_ml` / `stall_exit` citations withdrawn as definitions (they remain as related code). |
| 7 | 2-of-3 votes double-count the same bars; discretion in alternatives | Accepted. Single composite trigger (stall ∧ reclaim); the 5-min reversal bar and failed-probe rules are alternative triggers *for the test*, not live votes. |
| 8 | Look-ahead in "last swing extreme"; fills assumed at bar close/bid | Accepted. Extremes are running (causal) extremes since 10:00 or since the last opposite trigger; execution = first quote **after** the completed trigger bar, sell at that bid; resting-order fills tested against 1-min bid/ask sequence, not bar touch. |
| 9 | IV veto misstates source (10:30 daily correlations, 0DTE; ATM gate = IV above its 09:35 value) | Accepted. IV rule removed from the live stack; recorded as a diagnostic with the source's definitions. |
| 10 | Time-window / probe rules are top-side 0DTE transfers; round strikes unsourced | Accepted. Time window kept only as a *conservative* restriction (no unpaired leg after 14:30) pending a dip-side measurement; failed-probe and round-strike rules dropped from live use. |
| 11 | Cap mixes units; "cap with next-lower strike" makes a bullish credit spread | Accepted. Cap = **buy back** the unpaired short when its mark ≥ sale + 3.5 (planned max loss ≈ $350 + slippage; expected frequency to be measured in option terms — spot proxy 15–17% of attempts see > 20 bp adverse). The next-lower-strike branch is withdrawn. |
| 12 | Acceptance metrics are spot-path, not economic | Accepted. Test outcomes restated at option level: plant rate within 60 min, net credit at plant, unpaired-leg P&L (mean, ES₉₅), stop frequency, day P&L including leftover legs — same accounting as `scripts/replay_variants.py`. |
| 13 | 2025–26 holdout contaminated | Accepted. Spec frozen before the run; walk-forward selection inside 2022–2024; 2025–26 reported as *contaminated* out-of-sample; the clean test is a prospective paper log of Schwab fills against the frozen rules; day-clustered bootstrap for intervals. |

**Reduced live stack (v2 — what is actually used until the test reports)**

1. **Gate:** SPX has not closed below the Vol Trigger on a 1-min bar this session; no scheduled macro event; clock 10:00–14:00 for opening a leg, nothing unpaired after 14:30. If SG levels are missing → long-first only.
2. **Leg order (hypothesis, not gate):** band position pos ≥ 0.7 or room_to_CW ≤ 0.5 → long-first; otherwise sell-first when the down-swing is the one being faded, long-first when the up-swing is. Default when unsure: long-first.
3. **Arm:** running move from the causal extreme ≥ 2u.
4. **Trigger (single, causal):** no new running low over the last 5 completed 1-min bars **and** the latest completed 1-min close > running TPM since that low. Mirror for the buy leg (no new running high, close < running TPM).
5. **Execution:** first quote after the trigger bar; sell at bid; rest the buy 5 higher at sale − 0.10; 60-min clock; buy back if mark ≥ sale + 3.5; one unpaired leg; no anchor; after any fill, re-anchor the next resting limit to the neighbour's current quote + c.
6. **Diagnostics logged, not rules:** mature alligator (v3 parameters, SPX-recomputed), ER(10), VWAP flips, 5-min reversal bar, level probes, ATM IV vs 09:35, put-skew change, `emove`/`move935`.

**Test that decides it (`scripts/spx_legin_ev.py`, spec frozen here):** entries at (a) trigger minutes vs (b) every 15-min clock minute 10:00–14:00; instruments = the −0.20Δ 5-wide put pair from the SPXW 5-min greeks store (102 sessions 2024–25) with 1-min quote sequence where available; outcomes per §12 disposition; adoption only if plant rate within 60 min rises ≥ 5 pp **and** unpaired-leg ES₉₅ does not worsen, with day-clustered 90% CIs, on the walk-forward folds; then a 20-session prospective paper log before any size increase.

### 2c. First measurement of the v2 trigger on spot (2026-08-18, corrected after review) — a small, real, sub-threshold effect; no speed edge

`scripts/spx_legin_ev.py` (defaults) on real SPX 1-min OHLC, 845 sessions, leg-open window 10:00–14:00, one fire per 15 min. **Trigger** = pullback ≥ 8 pts from the running high since 10:00, running low unbroken for the last 5 completed 1-min bars, latest close > running mean of typical price since that low; outcome measured over exactly the next 60 bars from the trigger bar's close. **Baseline** = every minute 10:00–14:00 (203,645 starts), reported uniform **and re-weighted to the trigger's clock distribution**. Adverse excursion excludes the touch bar (intrabar order unknown) and is floored at 0. Artifacts: `docs/replay/spx_legin_trigger_x4_w60_p8_s5.parquet`, `spx_legin_anytime_x4_w60.parquet`.

| | trigger (n = 7,337; 8.7/day) | anytime, uniform | anytime, clock-matched |
|---|---|---|---|
| P(SPX +4 bp within 60 min) | **0.817** | 0.806 | 0.803 |
| P(adverse > 20 bp before it) | 0.152 | 0.152 | 0.150 |
| P(adverse > 40 bp before it) | 0.050 | 0.050 | — |
| P(hit within 5 min) / within 15 min | 0.416 / 0.642 | 0.401 / 0.622 | 0.389 / — |
| median minutes to hit (given hit) | 5 | 6 | — |
| P(the stalled low breaks before the move) | 0.236 | — | — |

Day-clustered bootstrap of the difference in P(up), trigger − anytime: **+2.6 pp, 90% CI [+1.9, +3.2]**. By pullback size: 8–12 pt → 0.78 fill / 0.33 low breaks; 40+ pt → 0.86 / 0.16 but adverse > 40 bp 0.078.

**Reading (corrected).** The trigger's effect on the needed move is real but small (+1–3 pp; below the pre-registered +5 pp bar) and it does not touch the adverse tail. It does **not** buy speed: the anytime baseline also fills at a 5–6-minute median, and the within-5-minute rate differs by ~3 pp. One in four "stalls" is false (the low breaks first). Consistent with the trend work: at 1-min scale, confirmation arrives after the information is spent. **Status:** stall ∧ reclaim is kept only as a disciplined way to place the leg at a sensible price after the tape has turned; it is not an edge and not a speed edge. Completion probability is set by the tape's oscillation (~80%/hour). Option-level test (plant rate, credit, unpaired-leg P&L, stop frequency on SPXW greeks) still owed. Trend state → leg order (UP: sell-first on pullback stalls; DOWN: long-first; CHOP: long-first) remains a **hypothesis** — not tested by these tables.

### 2d. "Chop" conditions, measured (2026-08-18, corrected after review) — ER/flips are weak, prior-hour range is a vol effect; neither is a validated selection rule

`scripts/spx_legin_ev.py`: causal features over the prior 30/60 bars at each 15-min start 10:30–14:00 (12,675 starts; `docs/replay/spx_legin_chop_x4.parquet`): Kaufman ER (w returns), realized range over exactly w bars (bp), 5-bar direction flips ignoring zero returns. Outcomes for X = 4 bp within 60 min.

| prior-60-bar feature (quartiles) | P(needed move) | P(both directions) | P(round trip) | adverse > 20 bp | > 40 bp |
|---|---|---|---|---|---|
| ER low → high (choppy → directional) | 0.785 → 0.811 | 0.55 → 0.61 | 0.54 → 0.59 | 0.15 → 0.16 | 0.04 → 0.05 |
| direction flips few → many | 0.809 → 0.791 | 0.60 → 0.56 | 0.58 → 0.55 | ~0.15 | ~0.045 |
| realized range < 21 bp | 0.73 | 0.44 | 0.43 | 0.11 | 0.026 |
| 21–30 bp | 0.80 | 0.55 | 0.54 | 0.13 | 0.03 |
| 30–45 bp | 0.82 | 0.60 | 0.58 | 0.17 | 0.05 |
| > 45 bp | 0.86 | 0.72 | 0.69 | 0.19 | 0.07 |

ER × range terciles: range ordering holds inside every ER tercile; the ER effect is 1–3 pp on P(up) in low/high range and up to 5–8 pp in the middle-range tercile (0.825 → 0.769 P(up), 0.590 → 0.513 P(round trip)) — small, not zero, and unstable across cells.

**Reading (corrected).** (i) ER and flip counts are *weak*, not null: 2–6 pp effects, in the direction "slightly more directional prior hour → slightly more fills", with no clustered intervals or holdout, and VWAP-flip / alligator states were **not** measured here (they remain untested diagnostics, not "dropped for good"). (ii) The prior-hour realized range moves completion **and** the adverse tail together — but a fixed 4 bp barrier is mechanically easier to touch when vol is high, so this is largely volatility persistence under a fixed barrier, and the required option move itself grows with IV. It does not by itself say whether to prefer, avoid, or down-size busy tapes; that needs option-level net EV and ES₉₅ by range bucket, raw and vol-normalised. Range is also confounded with time of day (high-range observations cluster at 10:30). **Status:** the "half size above 30 bp / let legs rest longer when quiet" rules stated earlier were policies, not results — withdrawn as rules, kept as hypotheses for the option-level test. Pandar's "tails expand and contract" is the mechanism being described; the sizing response to it is not yet derived from data.

### 2e. Review dispositions for §2c/§2d (2026-08-18)

`/codex-review` on `scripts/spx_legin_ev.py` (FAIL, 7; `spx_legin_ev_codex_review_2026-08-18.md`): all fixed in code — exact-N horizon in both scripts (`spx_touch_stats.py` regenerated), clock-matched baseline added, parametrised self-describing artifacts, argument validation, exact-w range window, zero-return flips excluded, adverse excursion floored at 0 and touch bar excluded. `/codex-strategy-review` on the conclusions (FAIL, 9; `spx_2c2d_codex_strategy_review_2026-08-18.md`): #1 speed claim withdrawn (baseline median also 5–6 min); #2 clock-matched baseline added, "armed-vs-trigger" matched comparison still owed; #3 doc numbers reconciled to the script; #4 day-clustered CI added, walk-forward/holdout and option economics still owed; #5 "ER carries nothing" softened to "weak"; VWAP flips/alligator marked untested; #6/#7 range read restated as vol effect, sizing rules withdrawn to hypotheses; #8 time-of-day confound noted; #9 trend leg-order kept as hypothesis. Net: v2 stays five lines (gate, leg order as hypothesis, arm ≥ 2u, stall ∧ reclaim as placement discipline, execution with one leg / 60-min clock / buy-back cap / no anchor); no rule in it claims a measured probability edge except the tape's own ~80%/hour oscillation.

### 2f. "Can anything make the oscillation happen?" — Chart-Analyst synthesis (Claude) vs Codex chart-analyst pass (2026-08-18)

Inputs: all sections above, `scripts/spx_legin_ev.py` output, and an extra cut of round-trip vs adverse by state joined to the SG regime table (`docs/replay/spx_ratio_by_state_2026-08-18.md`: 12,225 starts / 815 days). Codex output: `spx_chart_analyst_codex_review_2026-08-18.md` (12 findings).

**Agree (both):** no tested price state materially raises P(3–7 pt retrace in 60 min) or lowers P(15–30 pt adverse run); prior-hour range is the largest raw effect and it is volatility scaling (fills and tail move together); stall∧reclaim is small (+1.1 pp pooled / +1.4 pp clock-matched / +2.6 pp equal-day-weighted, CI excl. 0) and non-protective — placement discipline, zero claimed edge; kill ER/flip gates, alligator-as-fade, raw level probes, early OR direction calls; keep one leg / no anchor / 60-min timeout / long-first default / price cap as conservative controls, not "optimal"; the decisive test is a chronological quote-level SPXW state machine (plant rate, credit, stop frequency, net P&L, ES₉₅); turn-candidate ranking identical.

**Codex catches accepted:** (1) Simpson's paradox — within every range tier *low* ER is better (mid-range 82.5 vs 76.9% one-way, 59.0 vs 51.3% round trip); low-ER × mid-normalised-range is the best remaining price-only test candidate; (2) disclose the estimand of the +2.6 pp (equal-day weighting) alongside pooled figures; (3) bp barriers ≠ fixed points across 2022–26 — re-run with +3/+5/+7 pt targets and −15/−30 pt adverse; (4) the stall cohort is confounded with being armed after a decline — control = armed-not-triggered at matched clock/excursion/vol (immediate-at-arm vs stall-only vs reclaim-only vs both); (5) overlapping starts are not executable opportunities under the one-leg rule; (6) a 20-session paper log cannot validate a 5–7% tail — freeze the spec, run all future sessions sequentially with a precision stopping rule.

**Disagree (open):** (a) gamma regime — Claude synthesis: SG index > 1.5 & above VT cuts 30-pt runs ~60% (2.6% vs 6.4%) for ~8% fewer fills → #1 test candidate; Codex: not a price/volume feature under the persona's red line, unranked. Kept as test candidate #1 (option-level). (b) SPY VWAP — Codex: violates SPX-only scope; Claude: allowable as a *declared* proxy (SPX has no volume). (c) the flat round-trip/adverse ratio (~3.6–3.9 across states) — Claude used it as the summary; Codex: descriptive, overlapping, not payoff-weighted. Downgraded to a picture, not a decision statistic.

**Net:** the tape's own ~80%/hour oscillation is the edge; the rules manage the tail; the two remaining leads are low-ER × mid-range (price-only) and positive-gamma regime selection (deep tail), both only via the quote-level replay with fixed-point barriers.

### 3. Playbook on real tape (2026-08-18)

Each v2 rule with one session where it helped and one where it did not (SPX 1-min store; SG levels from `spotgamma_fixed`; ~$21/pt at 21Δ):

| Rule | Helped | Didn't help |
|---|---|---|
| Gate: 1-min close < VT → no unpaired leg; 10:00–14:00 | **2025-10-10** open 6740 > VT 6725, closed below ~10:55, 6633 by 11:30, close 6552 (−190): gate = flat from 10:55 | **2025-08-15** VT 6445 undercut to 6442 at 11:45 then 6450–6465 all afternoon; 85% fills, 4% adverse: gate benched a textbook oscillation day |
| Leg order by trend state / band | **2026-02-12** DOWN by 11:00 (−52) → long-first: buy at the 11:35–11:40 bounce stall (6877), sell 5 lower on the 11:50–12:00 leg (6862–6857); sell-first would have carried a short into a −125 close | **2025-06-11** UP at 11:00 (+9, weak) → sell-first on the 11:40 stall (6050); tape rolled to 6011 by 14:20; the cap, not the state read, limited it |
| Arm ≥ 2u pullback | **2025-06-04 10:13** ~20-pt pullback (5990→5968), stall + TPM reclaim 5976.8, +3 pts two bars later | **2026-02-12 10:30** 12-pt pullback armed and triggered, then −100 pts |
| Trigger stall∧reclaim (discipline) | 2025-06-04 10:13: filled in 2 min, adverse 0.4 bp (82% of fires vs 80% anytime) | 2026-02-12 10:30: textbook print, then −142 bp (≈1 in 4 stalls false) |
| 60-min clock | 2026-02-12 10:30: unfilled at 60 min, SPX −97; second hour went to −133 | **2025-12-10 11:30** drifted 7 pts against, filled at minute 85 — clock closed it at 60 (~6% of attempts fill in 61–120 min) |
| Buy-back cap sale + 3.5 (~15 pts) | 2025-10-10: any 10:00–10:45 short capped near 6730–6735 (~11:00): −$350 vs −$2,000+ by 11:30 | **2026-01-13 11:21** leg 6965.5, dip to 6950 at 11:27 (cap prints), 6971 by 11:42 — stopped 6 min before the plant |
| No anchor | **2026-08-17** (live): bomb $0.00, anchor −$120 in 23 min; 102-day replay ≈ $127/bomb | 2025-10-10: an ATM anchor would have made ~$5,000; the cap (−$350) and gate cover that day for a fraction of the anchor's cost on the other ~100 |
| Regime: prefer SG index > 1.5 & above VT (test candidate) | **2025-06-09** SG 1.57, 5999–6021 all day, 86% fills, worst adverse 18 bp | **2025-06-11** SG 2.0, above VT — 61% fills, 40% of attempts saw a 15-pt run, 83-bp slide; positive gamma halves deep-tail frequency, doesn't abolish it |

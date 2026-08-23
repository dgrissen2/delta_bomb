# Proposal v2 — spec v3.0 "Real resting-limit fills"

*2026-08-23. Draft 1 was reviewed by Architect × PM (inline), then FAILED both
the red-team audit (4 blockers / 5 majors) and codex-plan-review (3 blockers /
6 majors, 2 de-scopes). This is the full rewrite with every finding resolved
in the body text. Review artifacts: session scratchpad; summary in §7.*

## 0. Goal and evidence

**GOAL (user):** every completed bomb nets **+0.10 ($10) by construction** —
the second leg RESTS at a 0.10-credit limit against the first leg's actual
fill, and a bomb only counts when that limit demonstrably fills on the
option's own 1-minute data. The $10 is the anti-slippage floor, not the
objective: the product is the owned 5-wide spread (max $500/lot); no criterion
may reward avoiding completion.

Evidence: repricing the 15 completed rehearsal bombs at real SPXW mids showed
the ±3-pt SPX touch proxy costs ~$46/bomb on average (a 3-pt move shifts a 20Δ
put ~0.6 while 5 strikes shift ~1.0). Trade prints are too sparse for fill
detection (measured 6/391 minutes on a bomb strike); 1-min NBBO is dense.
Historical SPXW 1-min chains are available via the ThetaData SDK (verified all
8 sessions; full-chain full-day greeks pull = ~138k rows in ~13 s/day).

## 1. The mechanic (normative once adopted)

**Causal sequence (one timeline, live == backtest):**
1. Signal fires at the close of bar *t* (R6 unchanged).
2. **Leg 1 books at the END-OF-MINUTE NBBO of bar *t+1*** (the execution bar's
   closing snapshot; live = the post-bar-close snapshot — same instant, both
   paths), CONSERVATIVE side: sell-first sells K at the **bid**; long-first
   buys K at the **ask**. Mid is never a booked price. Entry minute (clock,
   window, episode anchors) remains *t+1*.
3. **Leg 2 rests from that moment**: sell-first → BUY K+5 limit
   **L = fill1 − 0.10**; long-first → SELL K−5 limit **L = fill1 + 0.10**.
   L rounds to a valid tick AGAINST us (down for buys, up for sells; these
   puts trade on a 0.10 grid).
4. **First fill-eligible minute is *t+2*.** In each completed minute *m*, the
   limit fills iff that minute's closing NBBO is marketable against it:
   BUY limit → ask(m) ≤ L; SELL limit → bid(m) ≥ L. Booked at L. No
   same-snapshot leg1+leg2 fills, no look-ahead, by construction.
5. **Cancel semantics:** any R7 exit decision (scratch, cap, veto_exit,
   state_flip, clock, resolution) CANCELS the resting limit at the decision
   bar's close (one `limit_canceled` event), then the exit books per §1.6.
   Same-minute race: **fill wins** — R7 precedence is unchanged and evaluated
   at one point (§3, arbitration stays in RuleEngine).
6. **Exit booking (non-fill exits):** decision at close of bar *j* → lone leg
   books at the close-of-bar *j+1* NBBO, conservative side (buy back at ask /
   sell out at bid); session end → bar *j*'s closing NBBO. Losses are option
   dollars, not SPX-point proxies.
7. **15:30 resolution completes NOTHING (v3.0):** the resting limit is
   canceled and the lone leg closes (`resolution_close`). `resolution_debit`
   is RETIRED — completing a pair at a ≤0.50 debit violates the credit
   invariant. Invariant: **every event labeled a completed bomb booked leg 2
   at L and carries credit ≥ 0.10.**
8. **Strike selection (backtest and live):** −0.20Δ from the chain at the
   signal-minute snapshot, constrained to strikes whose 5-wide partner is
   listed (grid: 10s with 5s at 25-pt anchors); ties → lower strike.

**Signals, vetoes, windows, episodes, caps, and B-scratch conditions are all
untouched.** This proposal swaps the pricing/fill layer only.

## 2. Option-data health (new R10.4 — fail closed, never fall back to SPX fills)

- No valid quote at the execution bar → entry ABORTED, logged
  `entry_aborted_no_quote`; the signal still counts as qualifying (R11.1), the
  aborted entry joins neither fill-rate numerator nor denominator.
- Quote gap while a limit rests: minutes logged `quote_gap`; a gap ≥ 5
  consecutive minutes while a trade is open → the trade's outcome is
  `data_invalid` (excluded from numerator AND denominator, reported
  separately). Fill status is never guessed across a gap.
- Exit booking with no fresh quote: book at the last valid NBBO if ≤ 3 min
  old, else `data_invalid`.
- Cumulative option-quote outage inside 10:00–14:30 counts toward R10.3
  PARTIAL exactly like HIRO/SPX outages. There is NO spot-proxy fill fallback,
  live or backtest — if quotes are unavailable live, the engine stands down
  from new entries (banner), keeping cap(spot)/clock/resolution guards for any
  open leg.

## 3. Ownership (design contract — unchanged principles)

- **Session** fetches the minute's quotes (execution-bar chain snapshot at
  signal+1; the two working strikes each minute after) and ATTACHES them to
  the row — exactly like vetoes/health. Session performs no trading logic.
- **RuleEngine remains the ONLY owner of R7 precedence.** It computes
  `limit_filled` from the attached quotes and arbitrates fill > scratch > cap
  > veto_exit > state_flip > clock > resolution in one place, as today.
- **Executor stays a pure, I/O-free state applier**: books prices (leg 1,
  limit fills at L, conservative exit NBBO), maintains the resting-limit
  state, emits ENTRY/EXIT/limit events. Fixture quotes make it table-testable.
- **FeatureEngine untouched.**
- **TierPolicy gains one field** `fill_mode: limit | spot_touch`. Price tier =
  `spot_touch` (legacy ±3 touch, no chains for the 2022+ archive), stamped and
  quarantined as always; this is the ONLY surviving production use of the
  touch. Schema v2 is ADDITIVE (new columns: leg1_fill, limit_price,
  leg2_fill, quote_age, outcome data_invalid label; readers accept v1).

## 4. Metrics & controls (R11 rewritten in two explicit unit families)

- **Economic ($, drives R9):** `leg_liq_loss_usd` = worst conservative
  liquidation of the lone leg vs leg-1 fill; realized exit P&L in $; median
  scratch loss in $; max single-trade realized loss in $. Best-session
  tie-break #2 becomes summed realized $ P&L.
- **Contextual (SPX pts, drives nothing):** `spx_adverse_pts` retained for
  continuity with prior research, reported only.
- **Fill rate (R11.6):** limit fills ÷ executable entries with complete,
  data-valid horizons (censored and `data_invalid` excluded from both sides).
- **Would-have-completed scratch re-check:** replays the RESTING LIMIT (not
  any SPX touch) over the remaining horizon from the pinned chain data.
- **Heartbeat** prints both families.
- **Matched controls (R11.4/R11.5):** same clock/midpoint matching; indicator
  = "a limit placed per §1 at that minute fills within the horizon." Control
  candidates need their own strike pick + limit + horizon per minute →
  computed ONCE by a `controls_build` job over the full-day full-chain cache
  and persisted as a **hash-pinned derived control frame** (parquet + sha256
  in CONFIG). Scorecard-time controls read the pinned frame only. Candidate
  eligibility mirrors trade rules: valid quotes at the candidate's execution
  minute, partner listed, complete data-valid horizon; ineligible minutes are
  excluded and counted in the frame's manifest.

## 5. Data, pinning, verification (three separate gates)

- **ChainStore (new module `chains.py`):** full-chain, full-day 1-min
  NBBO+greeks per session (one SDK pull/day, ~seconds), cached under
  `~/Dev/central_trade_data/thetadata/spxw_bomb_chains/` with a manifest;
  DATA_DICTIONARY/CHANGELOG updated. **The chain-cache manifest sha256 AND the
  thetadata SDK version go into CONFIG (R8.2)** — a silent re-fetch or vendor
  revision changes CONFIG_HASH visibly. Acknowledged: verification artifacts
  are reproducible against the pinned cache, not against the vendor.
- **Gate 1 (unchanged):** legacy golden gate — verify.py reproduces the v1
  27-trade research artifact through the ported core. Verifies the research
  port, nothing about v3.
- **Gate 2 (new, pre-implementation):** a HAND-COMPUTED v3 fixture — small
  synthetic quote series covering both sides, tick rounding, the t+2 first
  eligibility, same-minute fill-vs-scratch race, cancel paths, quote gaps,
  session-end booking. Expected outputs calculated by hand BEFORE the pricing
  layer is written (TDD; the forensics lesson made mandatory).
- **Gate 3:** the first clean v3 rehearsal trade list, row-spot-checked
  against raw quotes, then hash-pinned as verification artifact v2 (with the
  chain manifest + control frame + preregistration hashes in CONFIG).

## 6. R9 re-registration (pre-registered BEFORE the first v3 rehearsal run)

Task 16a freezes, in the spec, before any v3 rehearsal runs:
- **Criteria FORM:** inherited unchanged from R9 v2.3 (structure, not
  numbers) + the $-risk lines replacing SPX-point lines per §4.
- **Sample minimums:** carried over UNCHANGED (B ≥ 20 qualifying signals, A ≥
  8 episodes) — qualifying semantics don't change; no re-derivation, no
  judgment.
- **Fill-rate floors formula:** floor = max(0.10, point estimate − 1
  day-clustered bootstrap SD), rounded DOWN to 0.05. Bootstrap resamples with
  zero entries for a branch are dropped from that branch's SD; if > 30% of
  resamples are empty the branch is pre-declared underpowered (reported).
- **$-risk lines formula:** max single-trade loss cap = rehearsal p95 realized
  loss rounded UP to $25; median scratch loss cap = rehearsal median × 1.5
  rounded UP to $10.
- Rounding, denominators, and the defect/re-run policy (a code defect found
  after 16b → fix, re-run ONCE, document; a disliked number is not a defect).
Then 16b runs the rehearsal ONCE and populates the numbers mechanically.
Honesty note: we have seen v2.3 touch-fill rehearsal numbers but no v3
limit-fill numbers; the pre-registration boundary is the first v3 run.

## 7. De-scoped (review-driven; 98% principle)

- **No credit sweep knob.** The 0.10 credit is FROZEN. R13.2 gains nothing.
- **No production SPX-touch diagnostic column.** The old-vs-new comparison is
  computed once in the offline verification report.
- No queue modeling, partial fills, multi-lot, intra-minute interpolation,
  quote-persistence rules in the mechanic (a 2-consecutive-minute marketable
  sensitivity is ONE diagnostic column in the rehearsal report only).

## 8. Task plan (replaces draft §4; ordering is the contract)

- [ ] 13. **ChainStore + pins**: full-day full-chain cache for the 8 sessions;
      manifest; CONFIG gains chain-cache hash + SDK version. Tests: cache
      determinism, hash guard, refusal on missing dates.
- [ ] 14. **LIVE QUOTE SPIKE (before any pricing code — schedule risk lives
      here)**: prove ONE of (i) SDK live option snapshots or (ii) Schwab chain
      quotes, at 1-min cadence, for BOTH workloads: full-chain snapshot at a
      signal minute AND two-strike freshness afterward, within the 5-s budget.
      Neither works → STOP; v3.0 cannot go live (no fallback exists).
- [ ] 15. **Gate-2 hand fixture** (written and hand-computed first), then the
      pricing layer: Session quote attachment; RuleEngine `limit_filled` +
      cancel arbitration; Executor booking + resting-limit state; R10.4
      health; InstrumentSelector historical-chain path; schema v2; crash-
      resume round-trip on v2 rows.
- [ ] 16a. **Pre-registration freeze** (§6) — spec text + hashes committed.
- [ ] 17. **Scorecard/controls v3**: $ metrics; controls_build → pinned
      control frame; summarizer unchanged otherwise.
- [ ] 16b. **One rehearsal run** → thresholds populated mechanically →
      verification artifact v2 pinned.
- [ ] 18. **Battery + parity gate**: full test battery; live/backtest parity
      diff test as a SHAKEDOWN GATE — capture live snapshots for a session,
      fetch the historical series next day, compare: 100% fill-decision
      agreement and booked prices within 1 tick on ≥ 95% of minutes
      (pre-registered tolerance; miss → investigate before the clock starts).
- [ ] 19. **RUNBOOK/ops**: chain-cache freshness in morning check; quote-gap
      lines documented; evening check verifies chain manifest hashes.

## 9. Review trail

Draft 1: Architect×PM amendments (Executor I/O-free, additive schema, tick
grid, live hard gate) — incorporated. Red-team FAIL: R1.4/R11 contradiction,
controls data contract, R7.6 invariant breach, cancel semantics, orphaned
SPX-point metrics, NBBO flicker honesty, parity untested, cache unpinned,
floor formula ill-defined at small n, leg-1 instant — ALL resolved in §§1–6.
Codex-plan-review FAIL: R7.6 (same), t+1 look-ahead, precedence ownership,
quote-failure semantics/denominators, unit mixing, control data volume,
pre-registration discretion, verification circularity, task ordering,
unapplied amendments, credit-sweep/touch-diagnostic overengineering — ALL
resolved (de-scopes adopted in §7). Residual accepted risks: 1-min NBBO
snapshot granularity (flicker) is mitigated by closing-snapshot convention +
the sensitivity column, not eliminated; artifact reproducibility is
cache-relative, not vendor-relative.

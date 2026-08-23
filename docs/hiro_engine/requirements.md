# Requirements — Delta Bomb Signal Engine ("hiro_engine")

*v3.0 — 2026-08-23. REAL RESTING-LIMIT FILLS: the ±3.0-pt SPX touch proxy (R1.4) is replaced by the
actual second-leg mechanics — leg 1 books at conservative NBBO, leg 2 rests at a 0.10-credit limit, a
bomb completes ONLY when that limit becomes marketable on the option's own 1-min NBBO. Motivated by the
2026-08-23 repricing (completed bombs cost ~$46 at real mids under the touch proxy, not ~$0; see
`limit_fill_upgrade_proposal.md`, `limit_fill_reviews_2026-08-23.md`,
`../replay/hiro/bomb_repricing_2026-08-23.csv`). Consequences: R1.2/R1.4/R2.5/R7/R8/R9/R10.4/R11/R12/R13
amended below; `resolution_debit` RETIRED (violated the credit invariant); risk metrics move to option
dollars; R9 thresholds are re-registered by the pre-committed formulas in R9a BEFORE the first v3
rehearsal run. Rule change: CONFIG_HASH changes, the 10-session test resets (it has not started).
Prior: v2.3 — 2026-08-23. v2.2 + removal of the Branch-A bounce-high (BH) scratch from R7.2 after the
rehearsal forensics (`bh_scratch_forensics_2026-08-23.md`: never backtested, 8/8 scratches would
have filled, 38.1 pts surrendered, created the sole adverse>10 event; Charlie×CIO joint review).
Branch A keeps only the researched exits: fill, cap, clock, resolution. New standing rule and one
pre-registered candidate recorded in R7.2. This is a rule change: CONFIG_HASH changes and the
10-session test resets (it had not started). Prior: v2.2 — 2026-08-22. v2.1 + final plan review (6 blockers, 2 majors → fixed: signal/entry split, R7.0 exit-timing table, controls as deterministic scorecard functions, R13 backtest definitions, best-session re-check enumerated, full-tier source contract, single-backlink rule restored). Prior: v2.0 + red-team audit (31 findings, verdict FAIL → all fixed: controls and metrics defined in R11, verification artifact pinned, chain/SPY sources added, state-flip mapping, price-tier behavior enumerated, boundary and denominator rules). Self-contained: every trading rule is stated in this document with an R-number; acceptance
criteria reference R-numbers only. Research provenance, evidence and status history: see
[`../specs/delta_bomb_master_playbook.md`](../specs/delta_bomb_master_playbook.md) (the only external reference in this spec).*

## User Story

As a **discretionary SPX options trader running the frozen 10-session paper test**,
I want **one console program that watches live SPX 1-min bars and HIRO flow, prints entry/exit signals from the
frozen rules the moment a bar completes, silently simulates every trade the rules would take, and grades the
accumulated sessions against the pre-registered acceptance criteria**,
So that **I can hand-execute signals in my broker while an incorruptible, rule-exact log and scorecard decide —
without human fudging — whether this strategy earns the next stage**.

## Scope

- **In:** live signal evaluation (rules R1–R8 below); silent paper executor; console event stream; session logs;
  backtesting in three roles (verification, whitelist-knob research, scorecard rehearsal) over two data tiers;
  `scorecard` command implementing the acceptance test (R9); config freeze via hash.
- **Out (this build):** order placement; human-fill capture; push/mobile alerts; the NVDA program; the SPXW
  quote-level replay; live sizing (hard-coded 1 lot, paper).

---

# Part 1 — The Rules (normative)

## R1. Instruments & sizing
- **R1.1** Trade = 5-wide SPX/SPXW put vertical, both legs same expiry, expiry nearest 30 DTE within 20–40.
  "5 higher/lower" always means strike points. Sell-first = sell put K, then buy K+5. Long-first = buy put K,
  then sell K−5.
- **R1.2** Base strike K = the put closest to −0.20 delta on the chain at the SIGNAL-minute snapshot —
  live: the live chain (log the quote timestamp); backtest: the historical chain (R2.5). K is constrained
  to strikes whose 5-wide partner is LISTED (observed grid: 10s with 5s at 25-pt anchors); ties → lower
  strike. If no chain is available live, the entry is ABORTED per R10.4 (signals still print the
  "nearest −0.20Δ put" hint) — there is no chain-less trade in v3.0.
- **R1.3** Size = 1 contract, paper, always (this build).
- **R1.4** Fills (v3.0 — one causal timeline, live == backtest):
  (a) Signal at the close of bar t (R6 unchanged). **Entry bar = bar t+1**; S0 = its open (retained as the
  SPX context anchor for windows/clocks and `spx_adverse_pts`; S0 prices nothing).
  (b) **Leg 1 books at bar t+1's END-OF-MINUTE NBBO** (live: the post-bar-close snapshot — same instant),
  CONSERVATIVE side: sell-first sells K at the BID; long-first buys K at the ASK. Mid is never booked.
  (c) **Leg 2 rests from that moment**: sell-first → BUY K+5 limit **L = fill1 − 0.10**; long-first →
  SELL K−5 limit **L = fill1 + 0.10**. L rounds to a valid tick AGAINST us (down for buys, up for sells;
  0.10 grid at these premia). The 0.10 credit is FROZEN (not a knob).
  (d) **First fill-eligible minute is t+2.** In each completed minute m the limit FILLS iff that minute's
  closing NBBO is marketable against it: BUY limit → ask(m) ≤ L; SELL limit → bid(m) ≥ L. Booked at L.
  (e) INVARIANT: every event labeled a completed bomb booked leg 2 at L → net credit ≥ 0.10 ($10/lot),
  by construction, plus the owned 5-wide spread. The $10 is the anti-slippage floor, not the objective;
  no criterion may reward avoiding completion.

## R2. Data inputs
- **R2.1** SPX 1-min OHLC bars, live (ThetaData terminal) and stored (`~/Dev/central_trade_data/thetadata/spx_index_1m_ohlc/`).
- **R2.2** HIRO S&P 500 basket payload (scopes `all`, `nextExp`; call/put split), re-pulled each minute via the
  logged-in Chrome CDP session; stored partitions at `~/Dev/central_trade_data/spotgamma/hiro/sp500_basket/v1/`.
- **R2.3** SpotGamma daily levels CSV (`~/Dev/core_spotgamma_spx_vix_data/offset_historical_spotgamma_data.csv`):
  Vol Trigger (VT), Call Wall (CW), SG index, implied move (IM; fallback: nearest-expiry ATM straddle mid ÷ spot at 09:35 via R2.5; if neither available, IM is missing and R3.4 returns CHOP).
  Levels are VALID only if the CSV row carries today's date and CW − VT > 0.
- **R2.4** Event calendar: CPI, FOMC decision day, NFP, quarterly opex Friday, month-end rebalance day.
- **R2.5** Option chain, SPXW 1-min NBBO + greeks (bid/ask/delta):
  **Backtest/full tier (REQUIRED input)**: historical full-chain, full-day 1-min data via the ThetaData
  Python SDK, cached per session under `~/Dev/central_trade_data/thetadata/spxw_bomb_chains/` with a
  manifest; the manifest sha256 AND the SDK version are pinned in CONFIG (R8.2) — a re-fetch or vendor
  revision changes CONFIG_HASH visibly. Verification artifacts are reproducible against the pinned cache,
  not against the vendor (acknowledged).
  **Live**: minute snapshots from the same SDK (or Schwab chain quotes as fallback) — whichever the R-task
  spike proves at 1-min cadence for BOTH workloads (full-chain snapshot at a signal minute; two-strike
  freshness afterward) within the 5-s budget. Neither works → v3.0 does not go live; there is NO SPX-proxy
  fill fallback in any mode. Chain uses beyond fills: R2.3 IM fallback (live), R7.3 cap mid (all tiers now).
  The legacy R12.1 verification artifact predates v3.0 and is verified through the legacy research
  harness only (R12).
- **R2.6** SPY 1-min OHLCV for VWAP: live via ThetaData stock endpoint; stored at
  `~/Dev/central_trade_data/databento/spy_ohlcv_1m/`. VWAP = cumulative Σ(typical price × volume) ÷ Σ(volume)
  from 09:30.

## R3. Derived quantities (all causal, computed at each completed 1-min bar)
- **R3.1** HIRO lines: L = cumulative `all` total since 09:30 ($B); Lc/Lp its call/put parts; N = cumulative
  `nextExp` total. r5/r15/r30 = 5/15/30-min change of L (r15n for N).
- **R3.2** Run (trough-anchored): track the running low of L; run high = max L since that low; if L falls
  ≥ 0.6 $B from the run high, the run BREAKS and both reset at the current bar. run = L − L(trough);
  dur = minutes since trough; rate = run ÷ dur × 60 ($B/hr); ΔC/ΔP/ΔN = change of Lc/Lp/N since the trough;
  weak side = min(ΔC, ΔP); share = ΔN ÷ run; **run drawdown** = (run high) − L, i.e. the same quantity whose ≥ 0.6 $B value breaks the run.
- **R3.3** Price: pull30 = (30-bar rolling max of closes) − close, requiring a full 30-bar window;
  bounce30 = close − (30-bar rolling min); mid30 = (30-bar high + 30-bar low)/2 of closes;
  range60 = prior-60-min high − low (needs 60 bars); range60_pct = causal expanding 75th percentile of range60 over the pooled HIRO-era session history (all sessions from 2026-08-12 through the current bar), shifted one bar, min 300 observations; with < 300 observations Branch A is inactive and the engine logs `warmup`.
- **R3.4** Context read (10:30 and 13:00 only): UP = (close − open₀₉:₃₀) ≥ +0.10 × IM ∧ ≥ 80% of the last
  10 bars closed above VWAP (SPY volume-VWAP proxy) ∧ EMA5 > EMA9 > EMA20 (1-min closes); DOWN = mirror;
  else CHOP.
- **R3.5** Episode: per branch (A episodes and B episodes are independent; R6.4 limits still bind across both).
  A branch's condition-set staying continuously true counts once; the episode ends when its conditions lapse
  ≥ 3 consecutive minutes or (Branch B) the run breaks; a new entry requires a new episode of that branch.

## R4. Safety vetoes (P0 — always evaluated first; R4.1–R4.3 only ever block or exit SHORT legs; R4.4 blocks everything)
- **R4.1** VT break: if any 1-min bar has CLOSED below VT today → no new unpaired short for the rest of the day.
- **R4.2** Levels invalid (R2.3) → long-first only, all day.
- **R4.3** Flow veto: r15 < −0.8 $B AND r15n < −0.8 $B simultaneously → no new unpaired short while true.
- **R4.4** Event day (R2.4) → no signals at all; session logged `event_standdown`.

## R5. Session clock
- **R5.1** 09:30–10:00 observe-only: state tracked and printed, no entries, no simulated trades.
- **R5.2** Entries allowed 10:00–14:30 (Branch A additionally ≥ 10:35 — range60 completes at 10:30 and the extra bars are a deliberate frozen margin; Branch B's gate is ≤ 14:30). No new unpaired leg after 14:30.
- **R5.3** Each open leg: 60-minute clock from entry (R7.5).
- **R5.4** 15:30 hard resolution (R7.6) — it overrides a pending 60-min clock (a 14:30 entry resolves at 15:30 exactly). After 15:30 the engine only tracks and logs state until 16:00. Nothing survives past 15:30.

## R6. Entries
- **R6.1 Branch A (long-first; primary — wins same-bar ties):** fire when ALL of: (i) range60 ≥ range60_pct;
  (ii) r30 < 0; (iii) bounce30 ≥ 3 pts; (iv) close < mid30. Action: BUY the −0.20Δ put at the entry bar, BOOKED per
  R1.4(b) (entry bar's closing NBBO ask); rest the SELL of K−5 at (fill1 + 0.10) per R1.4(c).
- **R6.2 Branch B (sell-first; only if no R4 veto blocks shorts):** ARM when pull30 ≥ 3 pts AND the run has:
  dur ≥ 10 min, rate ≥ 2 $B/hr, ΔC > 0 ∧ ΔP > 0 with min(ΔC, ΔP) ÷ max(ΔC, ΔP) ≥ 0.25, ΔN > 0 with share ≥ 0.5, and run drawdown < 0.6 $B (implied by an unbroken run; stated for explicitness). GATES: r15 > 0; time ≤ 14:30; weak side ≥ 0.15 $B. Action: SELL the −0.20Δ put at the
  entry bar, BOOKED per R1.4(b) (entry bar's closing NBBO bid); rest the BUY of K+5 at (fill1 − 0.10) per R1.4(c).
- **R6.3 Late-state suppression:** if rate ≥ 4 $B/hr AND r30 ≥ 1.0 $B, suppress Branch B entries (one
  `LATE — NO ENTRY` line per episode).
- **R6.4 Limits:** one unpaired leg at a time; ≤ 3 entries/day; one entry per episode (R3.5); A beats B on the
  same bar.
- **R6.5 Serial entries:** every entry, including the day's 2nd/3rd, requires a fresh R6.1/R6.2 signal. All
  strikes and reference prices are recomputed from the LIVE chain at the new entry — never reused from an
  earlier bomb. "Neighbour strike" = the NEW trade's second-leg strike (K+5 sell-first / K−5 long-first); the
  signal line quotes its current bid/ask so the resting limit ((cost + 0.10) / (sale − 0.10)) is anchored to
  live prices.

## R7. Exits (precedence: fill > scratch > cap > veto_exit > state_flip > clock > resolution; first to fire wins)
- **R7.0 Timing & prices (applies to every exit):** each exit condition is evaluated at the close of bar j.
  Booking: fills = leg 2 at the limit L in the fill minute (R1.4d); every other exit books the lone leg at
  the close-of-bar j+1 NBBO, CONSERVATIVE side (buy back at ask / sell out at bid); if no bar j+1 exists
  (session end), bar j's closing NBBO. The 15:30 resolution evaluates at the 15:30 bar and books at that
  bar's closing NBBO. **Cancel semantics: any exit decision CANCELS the resting limit at the decision
  bar's close (one `limit_canceled` event) before the exit books. Same-minute race (limit marketable AND
  another exit condition true at the close of the same bar): FILL WINS — the R7 precedence above is
  arbitrated in ONE place (the rule engine) from quotes attached to the bar.** `spx_adverse_pts` (context
  only, drives nothing) runs from S0 over bars from the entry bar through the exit bar inclusive.
- **R7.1** Fill: the resting limit fills per R1.4(d) → completed bomb; minutes-to-fill = fill minute −
  entry minute. (The retired ±3.0 SPX touch survives NOWHERE in production; price tier uses its own
  legacy screen per R13.1, stamped and quarantined.)
- **R7.2** Flow-shutoff scratch (Branch B only): within 3 minutes of entry, L drops ≥ 0.3 $B below its entry
  value OR the run breaks, before the resting limit fills (R1.4d) → scratch, booked per R7.0. **Branch A has NO scratch**
  (v2.3): its exits are R7.1/R7.3/R7.5/R7.6 exactly as researched. *Standing rule: no exit may trigger off the
  same variable as its entry condition, and no rule enters this spec without a backtest showing it saves more
  than it costs.* Pre-registered candidate (NOT active; requires stored-session backtest + spec edit before
  activation): Branch-A premise invalidation — exit if a bar CLOSES above mid30 while the leg is open.
- **R7.3** Cap: the lone leg's option mid ((bid+ask)/2) moves 3.5 pts against its leg-1 fill → close it
  (`cap`). The option-mid trigger is now computable in ALL tiers with chain data (R2.5); the 15.0-pt SPX
  spot proxy survives only as the quote-gap fallback (chain data missing at that bar — logged
  `cap_source=proxy`). Never convert by adding a different strike.
- **R7.4** Veto exit: R4.3 activating while a short is carried → exit the leg (`veto_exit`), booked per R7.0.
  State-flip exit (13:00 read only): mapping is by SIDE — an open sell-first leg exits if the 13:00 read is
  DOWN; an open long-first leg exits if it is UP; CHOP never triggers it. Applies regardless of when the leg
  was opened (in practice only 12:00–13:00 entries can still be open). Same-bar tie: `veto_exit` before
  `state_flip`.
- **R7.5** Clock: 60 minutes after entry without a fill → close the lone leg (`timeout`). A horizon truncated by
  session end is `censored`, never `timeout`.
- **R7.6** 15:30 resolution (v3.0): cancel the resting limit, then CLOSE the lone leg
  (`resolution_close`, booked per R7.0). **`resolution_debit` is RETIRED** — completing a pair at up to a
  0.50 debit violated the R1.4(e) credit invariant. A pair either completes at the limit (R7.1) or does
  not complete.

## R8. Logging & config
- **R8.1** Every event — signal, entry, exit, veto change, skip (with reason), gate failure on an armed episode,
  outage, heartbeat, `limit_canceled`, `entry_aborted_no_quote`, `quote_gap` — is one row in
  `docs/replay/hiro/paper_log.csv`: ts, mode (live/backtest/shakedown), tier, branch, event, rule id, S0,
  strikes, run/rate/ΔC/ΔP/share/r15, outcome (fill mins / scratch $ / timeout / censored / data_invalid),
  **schema_v=2 additive columns: leg1_fill, limit_price, leg2_fill, quote_age, leg_liq_loss_usd,
  spx_adverse_pts** (readers accept v1 rows), CONFIG_HASH, session date. Console and file are ONE stream.
- **R8.2** CONFIG = the frozen thresholds file: every numeric in R1–R7, plus the R11.4/R11.5 control-dataset
  identifier (path + data hash), the R12.1 legacy artifact hash, **and (v3.0): the chain-cache manifest
  sha256, the thetadata SDK version, the derived control-frame sha256 (R11.4), the R9a pre-registration
  hash, and the R12 v2 artifact hash once pinned**. CONFIG_HASH = its SHA-256 on every row. A hash change
  vs the prior session prints a loud reset warning.

## R9. Acceptance test (the frozen 10-session exam; graded by `scorecard`; all terms per R11)
Over 10 countable sessions (live, non-shakedown, non-PARTIAL, non-event-standdown — PARTIAL and event days are
excluded from the denominator and do not consume test slots) of one CONFIG_HASH: qualifying signals on ≥ 7/10
sessions · 1–3 executable entries on ≥ 6/10 · **≥ 11 limit fills total AND ≥ 1 fill on 7/10 sessions** ·
≤ 3 entries/session, one leg at a time · Branch B ≥ 20 qualifying signals with fill rate (R11.6) ≥ **0.1**
and not below its frozen clock-matched control (R11.4) · Branch A ≥ 8 qualifying episodes with fill rate ≥
**0.55** and ≥ +10 pp over its frozen midpoint-matched control (R11.5) · branches reported separately; a
minute qualifying for both counts once (as A) · **max single-trade realized loss (R11.3, $) ≤ 150 on every
trade** · **median scratch loss (R11.3, $) ≤ 140** · ≤ 1 scratch whose RESTING LIMIT would have filled
within its ORIGINAL 60-minute horizon absent the scratch (pure limit replay from the pinned chain cache,
no other R7 exits applied; single invalid/missing minutes are skipped with no fill decision; a gap ≥ 5
consecutive minutes inside the replay makes that counterfactual INDETERMINATE — excluded from this count
and reported in its own column, never guessed) · the RISK RE-CHECK
holds: with the best session removed (best = most fills; ties → highest summed realized $ P&L; ties →
earliest date), recompute over the remaining sessions' entries — the $ risk lines and the would-have-filled
count still hold; thresholds unchanged, denominators reduced. A branch below its sample minimum is
INCONCLUSIVE. `data_invalid` trades (R10.4): REMAIN executable entries for the entries-per-session
criteria and the one-leg/3-day limits (they occupied the slot); are EXCLUDED from fill totals,
sessions-with-fill, both fill-rate sides (R11.6), the $-risk lines, and the would-have-filled re-check;
and are reported in their own column. Any rule change resets the test. **Thresholds populated 2026-08-23 by the R9a mechanical derivation (registration.json, hash-pinned; two grading-layer defects fixed + re-run per the defect policy — trade list identical, documented).**

## R9a. Threshold pre-registration (FROZEN before the first v3.0 rehearsal run; hashed in CONFIG)
- Criteria FORM: inherited unchanged from R9 v2.3 (structure above); $-risk lines replace SPX-point lines.
- Sample minimums: carried over UNCHANGED (B ≥ 20 qualifying signals, A ≥ 8 episodes) — qualifying
  semantics are untouched by v3.0; no re-derivation.
- Fill-rate floors: floor = max(0.10, rehearsal point estimate − 1 day-clustered bootstrap SD), rounded
  DOWN to 0.05. Bootstrap resamples containing zero entries for a branch are dropped from that branch's
  SD; if > 30% of resamples are empty, the branch is pre-declared underpowered (reported as such).
- Count floors — ONE bootstrap procedure for both: resample countable rehearsal sessions with
  replacement (2,000 draws, numpy default_rng(42)); per draw compute (i) fills_projected = total fills in
  the draw × 10 ÷ sessions-per-draw, and (ii) prop = share of drawn sessions with ≥ 1 fill. Fills-total
  floor = floor(mean(fills_projected) − 1·SD(fills_projected)), minimum 5. Sessions-with-fill floor =
  floor(10 × (mean(prop) − 1·SD(prop))), minimum 5.
- $-risk lines: max single-trade loss cap = rehearsal p95 realized loss rounded UP to $25; median scratch
  loss cap = rehearsal median × 1.5 rounded UP to $10.
- Defect policy: a CODE defect found after the rehearsal → fix, re-run ONCE, document. A disliked number
  is not a defect. The rehearsal runs exactly once otherwise.
- Honesty note: v2.3 touch-fill rehearsal numbers have been seen; no v3.0 limit-fill numbers have. The
  pre-registration boundary is the first v3.0 rehearsal run.

## R11. Metric & control definitions (everything R9 needs, computable from this document)
- **R11.1 Qualifying signal / episode / executable entry:** Branch B qualifying signal = a minute satisfying
  R6.2 arm + gates inside the R5.2 window, counted per episode (R3.5) regardless of R4/R6.4 blocks. Branch A
  qualifying episode = an episode whose first minute satisfies R6.1 inside the window. **Executable entry** = a
  qualifying signal/episode that opened a simulated trade (not blocked by one-leg, the 3/day cap, or an R4 veto).
- **R11.2 Contextual SPX excursion (`spx_adverse_pts`, drives NOTHING in R9):** in SPX points against the
  completion direction, measured from S0, maximum over bars from the entry bar through the exit bar
  inclusive. Reported for continuity with prior research only.
- **R11.3 Economic P&L ($ — drives R9; contract multiplier 100, 1-lot):**
  Non-fill exit realized P&L in POINTS = sell-first: fill1 − (exit buy-back price); long-first: (exit sale
  price) − fill1. **Realized P&L in $ = points × 100.** Realized LOSS of a trade = max(0, −realized $ P&L),
  defined for EVERY trade (winners contribute zero losses — the R9a p95 population includes them).
  A completed bomb contributes its BOOKED credit × 100 (≥ +$10 by the R1.4e invariant; tick rounding can
  only raise it; the owned spread's value is reported, never scored). Summed realized $ P&L of a session (best-session tie-break) = Σ non-fill exit $ P&L +
  $10 × fills. Scratch loss ($) = realized loss of a scratch. `leg_liq_loss_usd` = the worst mark-to-
  conservative-NBBO liquidation of the lone leg vs its leg-1 fill over the trade's life, in $ (heartbeats
  print both families).
- **R11.4 Frozen clock-matched control (Branch B):** a deterministic FUNCTION computed by `scorecard` at grading
  time: over the frozen control dataset (the eight research sessions 2026-08-12..21, fixed forever, identified
  in CONFIG by path + data hash), take every minute 10:00–14:30 with a complete 60-min horizon; weight minutes
  to match the clock-minute distribution of the test's Branch-B executable entries; control = weighted mean
  of the v3.0 LIMIT-FILL indicator: treat the candidate minute as a SIGNAL minute t — strike pick from
  t's chain snapshot, leg 1 booked per R1.4(b) at t+1, limit per R1.4(c), fills tested per R1.4(d) —
  indicator = 1 iff the limit fills within min(60 minutes, session end) of the entry minute, **with NO R7
  exits applied** (a pure fill-probability baseline, exactly parallel to the old touch control). Complete
  data-valid horizon required (no quote_gap ≥ 5 min inside it). Precomputed ONCE by the `controls_build`
  job over the pinned chain cache and persisted as a hash-pinned derived control frame (sha256 in CONFIG).
  Candidate
  eligibility mirrors trade rules (valid quotes at its execution minute, partner listed, complete
  data-valid horizon); ineligible minutes are excluded and counted in the frame's manifest. Deterministic
  given the test log + the pinned frame.
- **R11.5 Frozen midpoint-matched control (Branch A):** same deterministic-function form over the same frozen
  dataset; candidate minutes satisfy R6.1 conditions (i), (iii), (iv) but FAIL (ii) (r30 ≥ 0); same weighting
  and indicator.
- **R11.6 Fill rate:** limit fills ÷ executable entries with complete, DATA-VALID horizons (censored and
  `data_invalid` (R10.4) excluded from numerator and denominator; scratches and timeouts remain in the
  denominator). `entry_aborted_no_quote` events are not executable entries.

## R13. Backtesting definitions
- **R13.1 Tiers:** `full` requires HIRO + SPX 1-min + the chain cache (R2.5) per date (missing → date refused
  and listed) and runs **fill_mode=limit** (R1.4). `price` runs the whole SPX archive with: Branch B disabled;
  Branch A as "price-A" (R6.1 (i), (iii), (iv) only); R4.3 and R7.2 disabled; **fill_mode=spot_touch — the
  legacy ±3.0-pt SPX screen, the ONLY surviving use of the touch, with SPX-point bookkeeping**; all else
  identical; every output stamped `tier=price` (price-tier numbers are never full-rule claims).
- **R13.2 Sweep whitelist (fully enumerated; one knob per run; all else frozen):** scratch drop magnitude
  {0.2, 0.3, 0.4, 0.5, 0.6 $B below entry L} · scratch window {2, 3, 4, 5 min} · pullback {3, 5, 8 pts} ·
  cap {3.0, 3.25, 3.5, 3.75, 4.0} · clock {45, 60, 75 min}. Any other knob is rejected; changing this list
  means editing this spec. (v3.0: the 0.10 credit is NOT a knob — frozen by design.)
- **R13.3 Summary contract (every backtest/sweep output):** per variant — trade count, episode count, days
  covered, matched control per entry type (R11.4 form for sell-first-style, R11.5 form for long-first-style,
  computed over the run's own dataset with the R11.4 limit-fill indicator where chain data exists, else the
  tier's own fill indicator), day-clustered bootstrap 90% CI on the fill rate (resample days with
  replacement, 2,000 draws, seed 42), censored and data_invalid trades reported separately.
- **R13.4 Leaderboards:** print the number of cells examined at the top; cells with < 15 trades or < 4 days are
  displayed greyed out and excluded from ranking.

## R12. Verification (three SEPARATE gates in v3.0)
- **R12.1 (legacy core-port gate, unchanged):** `docs/replay/hiro/verification_trades_v1.csv` — the 27-trade
  research-sequential result — must be reproduced row-for-row THROUGH THE LEGACY RESEARCH HARNESS (verify.py)
  built on the ported feature core. It verifies the research port; it says nothing about v3.0 fills.
- **R12.2 (hand-computed v3 fixture, written BEFORE the pricing layer):** a small synthetic quote series with
  hand-calculated expected outputs covering both sides, tick rounding, the t+2 first-eligibility rule, the
  same-minute fill-vs-scratch race, every cancel path, quote gaps → data_invalid, and session-end booking.
  The pricing layer is built against this fixture (TDD; the BH-forensics standing rule made mandatory).
- **R12.3 (v3 rehearsal artifact):** the first clean v3.0 rehearsal trade list is spot-checked row-by-row
  against raw cached quotes, then hash-pinned in CONFIG as verification artifact v2. Reproducible against
  the pinned chain cache (not the vendor).

## R10. Degraded mode
- **R10.1** HIRO pull fails → print `HIRO DOWN`; no new entries (no substitution); open trades keep R7.3/R7.5/
  R7.6 exits; R7.2/R7.4 flow exits log `scratch_unavailable` if their inputs are missing; print `HIRO RESTORED`
  + outage span on recovery.
- **R10.2** SPX bar feed stalls > 2 minutes → same treatment.
- **R10.3** Cumulative outage > 15 minutes inside 10:00–14:30 (HIRO, SPX, or option-quote outages combined),
  or bars ending before 15:55 → session PARTIAL.
- **R10.4 Option-quote health (v3.0 — fail closed; NEVER an SPX fill fallback):**
  **Quote validity**: a strike's quote at a minute is VALID iff bid > 0 AND ask ≥ bid (locked ok, crossed
  or zero-bid invalid). **Freshness**: entry booking and fill decisions use ONLY the quote OF that minute
  (backtest: the 1-min series row for minute m; live: the snapshot taken after bar m closes) — quote_age =
  0 for decisions, no carry-forward ever. The ≤ 3-minute last-valid-NBBO allowance applies SOLELY to exit
  BOOKING (below), never to entries or fills. At the entry bar, BOTH working strikes (K and K±5) must have valid quotes in the
  closing snapshot, else the entry is ABORTED (`entry_aborted_no_quote`; the signal still counts as
  qualifying per R11.1; the aborted entry joins neither side of R11.6). · While a limit rests, a minute
  whose working-strike quote is missing/invalid is a `quote_gap` minute (no fill decision that minute);
  **on the 5th consecutive quote_gap minute of an open trade the engine CANCELS the resting limit
  (`limit_canceled`, reason quote_gap) and labels the trade's eventual outcome `data_invalid`** — the
  position itself remains open under the surviving guards (R7.3 spot-fallback cap, R7.5 clock, R7.6
  resolution) and still occupies the one-leg lock and the 3/day count until it closes. · Exit booking with
  no valid quote at bar j+1 → book at the last valid NBBO if ≤ 3 minutes old, else the exit itself is
  booked `data_invalid` (position closed administratively at the last valid NBBO regardless, so no
  position survives; the trade is unscored). ·
  live loss of option quotes → stand down from NEW entries (banner), keep cap(spot fallback)/clock/
  resolution guards on any open leg.

---

# Part 2 — Acceptance Criteria

### Modes & lifecycle

**WHEN** the operator runs `hiro_engine live` with Chrome (CDP 9222, logged into SpotGamma) and the ThetaData terminal up
**THE SYSTEM SHALL** start a session: validate levels per R2.3, print the R4 state banner, and begin per-minute evaluation.

**WHEN** levels are invalid per R2.3
**THE SYSTEM SHALL** print `LEVELS MISSING → LONG-FIRST ONLY` and enforce R4.2 all session.

**WHEN** today matches R2.4
**THE SYSTEM SHALL** print `EVENT DAY — STAND DOWN` and enforce R4.4.

**WHEN** the operator runs `hiro_engine backtest --from D1 --to D2`
**THE SYSTEM SHALL** replay stored sessions through the identical rule module used live (one code path), emitting the identical console event stream with replay timestamps, and SHALL refuse dates lacking a required data source (listing them) rather than silently skipping.

### Evaluation & signals

**WHEN** a 1-min SPX bar completes during 09:30–16:00
**THE SYSTEM SHALL** within 5 seconds re-pull the HIRO payload (R2.2), recompute R3, and evaluate R4 → R6.1 → R6.2 in that order.

**WHEN** the time is OUTSIDE the R5.2 entry window (i.e., during R5.1 observe-only, or after 14:30)
**THE SYSTEM SHALL** track and print state changes but emit no entry signals and open no simulated trades.

**WHEN** the clock reaches 10:30 and 13:00
**THE SYSTEM SHALL** compute and print the R3.4 context read and retain it for R7.4.

**WHEN** a Branch A signal fires (R6.1, R6.4, R5.2 all satisfied) at a bar close
**THE SYSTEM SHALL** print `SIGNAL A LONG-FIRST | t | strike (R1.2) | <condition values>` immediately, and at the entry bar print `ENTRY A | bought K @ <ask, R1.4b> | resting SELL K−5 @ <fill1+0.10>` — leg 1 booked at the entry bar's closing NBBO ask, the limit resting per R1.4(c) (leg-1 price is unknowable at signal time and never appears on a SIGNAL line).

**WHEN** a Branch B signal fires (R6.2 arm + gates, no R4 block, R6.4, R5.2)
**THE SYSTEM SHALL** print the equivalent `SIGNAL B SELL-FIRST` line immediately and, at the entry bar, `ENTRY B | sold K @ <bid, R1.4b> | resting BUY K+5 @ <fill1−0.10>`, opening the simulated sell-first trade with its resting limit.

**WHEN** Branch A and Branch B fire on the same bar
**THE SYSTEM SHALL** take only Branch A (R6.4).

**WHEN** a setup remains continuously true
**THE SYSTEM SHALL** signal once per episode (R3.5).

**WHEN** R6.3 holds
**THE SYSTEM SHALL** suppress Branch B and print one `LATE — NO ENTRY` line per episode.

**WHEN** any R4 veto state changes
**THE SYSTEM SHALL** print one state-change line.

**WHEN** a 2nd or 3rd entry of the day fires
**THE SYSTEM SHALL** include the R6.5 neighbour-strike pricing in the signal line.

### Simulated executor & exits

**WHEN** a simulated trade is open
**THE SYSTEM SHALL** evaluate exits each completed bar in the R7 precedence order and close on the first that fires, printing `EXIT <type>` with realized $ P&L (R11.3) and both excursion families (R11.2/R11.3).

**WHEN** the resting limit becomes marketable per R1.4(d) (first eligible minute t+2)
**THE SYSTEM SHALL** record `fill` booked at the limit L, with minutes-to-fill and the credit (>= 0.10 by construction).

**WHEN** any non-fill exit decision fires while a limit is resting
**THE SYSTEM SHALL** emit `limit_canceled` at the decision bar's close before booking the exit (R7.0); on a same-minute race the fill wins.

**WHEN** option quotes are missing per R10.4 (entry bar, resting gap >= 5 min, or stale exit booking)
**THE SYSTEM SHALL** abort the entry / mark the outcome `data_invalid` / book at the last <= 3-min-old NBBO respectively, and never substitute an SPX-based fill.

**WHEN** R7.2 triggers
**THE SYSTEM SHALL** record `scratch`, booked per R7.0 (close-of-bar j+1 NBBO, conservative side).

**WHEN** R7.4 triggers (veto activation while carrying a short, or an opposite 13:00 read)
**THE SYSTEM SHALL** exit per R7.0 booking, recording `veto_exit` / `state_flip` respectively.

**WHEN** R7.3 triggers
**THE SYSTEM SHALL** record `cap`, logging whether option mid or spot proxy was used.

**WHEN** R7.5 or R7.6 applies
**THE SYSTEM SHALL** record `timeout`/`censored` or `resolution_close` per those rules (`resolution_debit` is retired in v3.0).

**WHEN** a trade is open
**THE SYSTEM SHALL** print a heartbeat every 5 minutes (state, clock remaining, current adverse), logged like every other event (R8.1).

### Degraded mode

**WHEN** R10.1/R10.2 conditions occur
**THE SYSTEM SHALL** behave exactly as those rules state, and flag the session PARTIAL when R10.3 is met.

### Logging & config freeze

**WHEN** any event occurs
**THE SYSTEM SHALL** append the R8.1 row; console and file are one stream.

**WHEN** the engine starts with a CONFIG_HASH differing from the previous session
**THE SYSTEM SHALL** print a loud warning that mixing hashes resets the acceptance test (R9).

### Backtesting

**WHEN** backtest runs with `--tier full` (default)
**THE SYSTEM SHALL** require HIRO partitions + SPX 1-min + the pinned chain cache (a date lacking any is refused and listed per R13.1); SPY 1-min and levels are used when present and degrade exactly per the live rules when absent (no SPY → R3.4 returns CHOP, logged `degraded_vwap`; invalid levels → R4.2), evaluating R1–R7 with fill_mode=limit.

**WHEN** backtest runs with `--tier price`
**THE SYSTEM SHALL** apply R13.1's price-tier behavior exactly, stamping every output `tier=price` so a price-tier number can never be quoted as a full-rule result.

**WHEN** the operator runs the legacy verification (R12.1)
**THE SYSTEM SHALL** reproduce `docs/replay/hiro/verification_trades_v1.csv` row-for-row through the legacy research harness — a defect, not a tolerance, on any mismatch.

**WHEN** the v3.0 pricing layer is graded (R12.2/R12.3)
**THE SYSTEM SHALL** pass the hand-computed quote fixture exactly, and reproduce the pinned v2 rehearsal artifact row-for-row against the pinned chain cache.

**WHEN** the operator runs `hiro_engine backtest --day <date> --verbose`
**THE SYSTEM SHALL** print the full live-format console stream for that day for bar-by-bar cross-checking.

**WHEN** `--config <file>` is supplied to a backtest
**THE SYSTEM SHALL** run with those overrides, stamp outputs with that config's hash, and never count any backtest row toward the live test.

**WHEN** the operator runs `hiro_engine sweep <knob>`
**THE SYSTEM SHALL** sweep exactly ONE knob per R13.2, holding all else frozen and rejecting unlisted knobs.

**WHEN** any backtest or sweep summarizes results
**THE SYSTEM SHALL** emit the R13.3 summary contract; sweep leaderboards SHALL follow R13.4.

**WHEN** the operator runs `hiro_engine scorecard --rehearsal --from D1 --to D2`
**THE SYSTEM SHALL** grade historical sessions with the full R9 logic, labeled REHEARSAL, excluded from the live record.

### Shakedown & scorecard

**WHEN** the operator marks a session `--shakedown` (the first two live sessions)
**THE SYSTEM SHALL** log it fully, tagged `shakedown`, excluded from all scorecard counts.

**WHEN** the operator runs `hiro_engine scorecard`
**THE SYSTEM SHALL** read all non-shakedown live sessions of the current CONFIG_HASH and print the full R9 table — each criterion, measured value, threshold, PASS/FAIL/INCONCLUSIVE — including both frozen controls, PARTIAL-session handling, the best-session-excluded re-check, and an overall verdict line.

**WHEN** sessions with different CONFIG_HASHes exist
**THE SYSTEM SHALL** refuse to combine them in one scorecard and say why.

**WHEN** a branch is below its R9 sample minimum
**THE SYSTEM SHALL** report it INCONCLUSIVE.

## Non-functional

Console only; no GUI, no notifications. Single Python process, started manually each morning; local Mac; venv
`~/Dev/virtualenvs/gamma_chaser`. Evaluation latency ≤ 5 s after bar close. All timestamps ET. Crash recovery: on
restart mid-session, reload today's log and resume state (open simulated trade reconstructed from its entry row).
One rule module shared verbatim between live and backtest.

## Acceptance of this spec

Verification backtest reproduces R12.1 exactly (row-for-row match); two
shakedown sessions run clean (no crash, no console/log divergence); then the 10-session clock starts.

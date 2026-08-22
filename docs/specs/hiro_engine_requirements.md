# Requirements — Delta Bomb Signal Engine ("hiro_engine")

*v2.0 — 2026-08-22. Self-contained: every trading rule is stated in this document with an R-number; acceptance
criteria reference R-numbers only. Research provenance, evidence and status history: see
[`delta_bomb_master_playbook.md`](delta_bomb_master_playbook.md) (the only external reference in this spec).*

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
- **R1.2** Base strike K = put closest to −0.20 delta on the live chain at decision time (broker greeks; log the
  quote timestamp). If no chain feed, signals say "nearest −0.20Δ put".
- **R1.3** Size = 1 contract, paper, always (this build).
- **R1.4** Completion proxy (simulation): the second leg is deemed filled when SPX moves 3.0 pts in the required
  direction from the entry reference S0 (S0 = the entry bar's open). Measured requirement is 3.0–3.8 pts
  (plan on 3.5); 3.0 is the frozen simulation threshold for continuity with the research record.

## R2. Data inputs
- **R2.1** SPX 1-min OHLC bars, live (ThetaData terminal) and stored (`~/Dev/central_trade_data/thetadata/spx_index_1m_ohlc/`).
- **R2.2** HIRO S&P 500 basket payload (scopes `all`, `nextExp`; call/put split), re-pulled each minute via the
  logged-in Chrome CDP session; stored partitions at `~/Dev/central_trade_data/spotgamma/hiro/sp500_basket/v1/`.
- **R2.3** SpotGamma daily levels CSV (`~/Dev/core_spotgamma_spx_vix_data/offset_historical_spotgamma_data.csv`):
  Vol Trigger (VT), Call Wall (CW), SG index, implied move (IM; fallback: ATM straddle ÷ spot at the open).
  Levels are VALID only if the CSV row carries today's date and CW − VT > 0.
- **R2.4** Event calendar: CPI, FOMC decision day, NFP, quarterly opex Friday, month-end rebalance day.

## R3. Derived quantities (all causal, computed at each completed 1-min bar)
- **R3.1** HIRO lines: L = cumulative `all` total since 09:30 ($B); Lc/Lp its call/put parts; N = cumulative
  `nextExp` total. r5/r15/r30 = 5/15/30-min change of L (r15n for N).
- **R3.2** Run (trough-anchored): track the running low of L; run high = max L since that low; if L falls
  ≥ 0.6 $B from the run high, the run BREAKS and both reset at the current bar. run = L − L(trough);
  dur = minutes since trough; rate = run ÷ dur × 60 ($B/hr); ΔC/ΔP/ΔN = change of Lc/Lp/N since the trough;
  weak side = min(ΔC, ΔP); share = ΔN ÷ run.
- **R3.3** Price: pull30 = (30-bar rolling max of closes) − close, requiring a full 30-bar window;
  bounce30 = close − (30-bar rolling min); mid30 = (30-bar high + 30-bar low)/2 of closes;
  range60 = prior-60-min high − low (needs 60 bars); range60_pct = causal expanding 75th percentile of range60
  over all pooled session history to date, shifted one bar, min 300 observations.
- **R3.4** Context read (10:30 and 13:00 only): UP = (close − open₀₉:₃₀) ≥ +0.10 × IM ∧ ≥ 80% of the last
  10 bars closed above VWAP (SPY volume-VWAP proxy) ∧ EMA5 > EMA9 > EMA20 (1-min closes); DOWN = mirror;
  else CHOP.
- **R3.5** Episode: a condition-set that stays continuously true counts once; it ends when its conditions lapse
  ≥ 3 consecutive minutes or the run breaks; a new entry requires a new episode.

## R4. Safety vetoes (P0 — always evaluated first; they only ever block or exit SHORT legs)
- **R4.1** VT break: if any 1-min bar has CLOSED below VT today → no new unpaired short for the rest of the day.
- **R4.2** Levels invalid (R2.3) → long-first only, all day.
- **R4.3** Flow veto: r15 < −0.8 $B AND r15n < −0.8 $B simultaneously → no new unpaired short while true.
- **R4.4** Event day (R2.4) → no signals at all; session logged `event_standdown`.

## R5. Session clock
- **R5.1** 09:30–10:00 observe-only: state tracked and printed, no entries, no simulated trades.
- **R5.2** Entries allowed 10:00–14:30 (Branch A additionally ≥ 10:35 for its 60-bar history; Branch B's gate is
  ≤ 14:30). No new unpaired leg after 14:30.
- **R5.3** Each open leg: 60-minute clock from entry (R7.5).
- **R5.4** 15:30 hard resolution (R7.6). Nothing survives past 15:30.

## R6. Entries
- **R6.1 Branch A (long-first; primary — wins same-bar ties):** fire when ALL of: (i) range60 ≥ range60_pct;
  (ii) r30 < 0; (iii) bounce30 ≥ 3 pts; (iv) close < mid30. Action: BUY the −0.20Δ put at the next bar's open;
  rest the SELL of K−5 at (cost + 0.10) limit on the bid side.
- **R6.2 Branch B (sell-first; only if no R4 veto blocks shorts):** ARM when pull30 ≥ 3 pts AND the run has:
  dur ≥ 10 min, rate ≥ 2 $B/hr, ΔC > 0 ∧ ΔP > 0 with min/max ≥ 0.25, ΔN > 0 with share ≥ 0.5, and run
  drawdown < 0.6 $B. GATES: r15 > 0; time ≤ 14:30; weak side ≥ 0.15 $B. Action: SELL the −0.20Δ put at the
  next bar's open (limit at current bid); rest the BUY of K+5 at (sale − 0.10) limit on the ask side.
- **R6.3 Late-state suppression:** if rate ≥ 4 $B/hr AND r30 ≥ 1.0 $B, suppress Branch B entries (one
  `LATE — NO ENTRY` line per episode).
- **R6.4 Limits:** one unpaired leg at a time; ≤ 3 entries/day; one entry per episode (R3.5); A beats B on the
  same bar.
- **R6.5 Serial entries:** every entry, including the day's 2nd/3rd, requires a fresh R6.1/R6.2 signal. The
  signal line for serial entries prints neighbour-strike pricing: resting sell = neighbour's live bid + 0.10;
  resting buy = neighbour's live ask − 0.10 (never reuse an earlier bomb's prices).

## R7. Exits (precedence: fill > scratch > cap > veto/state exits > clock > resolution; first to fire wins)
- **R7.1** Fill: SPX touches S0 + 3.0 (sell-first) / S0 − 3.0 (long-first) → completed; record minutes-to-fill.
- **R7.2** Flow-shutoff scratch (Branch B): within 3 minutes of entry, L drops ≥ 0.3 $B below its entry value OR
  the run breaks, before the fill touch → scratch at the next bar's open. Branch A analogue: price re-takes the
  bounce high before the fill touch → scratch.
- **R7.3** Cap: the lone leg's option mid ((bid+ask)/2; spot ±15-pt proxy if no chain, logged which) moves
  3.5 pts against entry → close it (`cap`). Never convert by adding a different strike.
- **R7.4** Veto exit: R4.3 activating while a short is carried → scratch it at the next bar's open (`veto_exit`).
  State-flip exit: the 13:00 context read (R3.4) is the OPPOSITE of the state that justified the carried leg →
  exit at the next bar's open (`state_flip`).
- **R7.5** Clock: 60 minutes after entry without a fill → close the lone leg (`timeout`). A horizon truncated by
  session end is `censored`, never `timeout`.
- **R7.6** 15:30 resolution: complete the pair as a debit spread only if the implied debit ≤ 0.50
  (`resolution_debit`, log the debit); otherwise close the lone leg (`resolution_close`).

## R8. Logging & config
- **R8.1** Every event — signal, entry, exit, veto change, skip (with reason), gate failure on an armed episode,
  outage, heartbeat — is one row in `docs/replay/hiro/paper_log.csv`: ts, mode (live/backtest/shakedown), tier,
  branch, event, rule id, S0, strikes, run/rate/ΔC/ΔP/share/r15, outcome (fill mins / scratch pts / timeout /
  censored), adverse, CONFIG_HASH, session date. The console stream and the log are the SAME stream.
- **R8.2** CONFIG = the frozen thresholds file (every numeric in R1–R7); CONFIG_HASH = its SHA-256 on every row.
  A hash change vs the prior session prints a loud reset warning.

## R9. Acceptance test (the frozen 10-session exam; graded by `scorecard`)
Over 10 non-shakedown live sessions of one CONFIG_HASH: signals on ≥ 7/10 sessions · 1–3 executable entries on
≥ 6/10 · ≥ 8 completions total AND ≥ 1 completion on 6/10 sessions · ≤ 3 entries/session, one leg at a time ·
Branch B ≥ 20 qualifying signals with fill ≥ 0.45 and not below its frozen clock-matched control · Branch A ≥ 8
qualifying episodes with fill ≥ 0.70 and ≥ +10 pp over its frozen midpoint-matched control · branches reported
separately, overlaps counted once · adverse > 10 pts on ≤ 10% of entries, max one such trade · median scratch
loss ≤ 3 pts · ≤ 1 scratch that would have completed within its 60-min horizon · all risk criteria still hold
excluding the best session. A branch below its sample minimum is INCONCLUSIVE (not failed, not passed). Any rule
change resets the test. PARTIAL sessions (R10.3) are excluded from the denominator.

## R10. Degraded mode
- **R10.1** HIRO pull fails → print `HIRO DOWN`; no new entries (no substitution); open trades keep R7.3/R7.5/
  R7.6 exits; R7.2/R7.4 flow exits log `scratch_unavailable` if their inputs are missing; print `HIRO RESTORED`
  + outage span on recovery.
- **R10.2** SPX bar feed stalls > 2 minutes → same treatment.
- **R10.3** Cumulative outage > 15 minutes inside 10:00–14:30, or bars ending before 15:55 → session PARTIAL.

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

**WHEN** the time is inside an observe-only or post-entry window (R5.1, R5.2)
**THE SYSTEM SHALL** track and print state changes but emit no entry signals and open no simulated trades.

**WHEN** the clock reaches 10:30 and 13:00
**THE SYSTEM SHALL** compute and print the R3.4 context read and retain it for R7.4.

**WHEN** a Branch A signal fires (R6.1, R6.4, R5.2 all satisfied)
**THE SYSTEM SHALL** print `ENTRY A LONG-FIRST | t | S0 | strike (R1.2) | rest SELL K−5 @ cost+0.10 | <condition values>` and open a simulated long-first trade at the next bar's open.

**WHEN** a Branch B signal fires (R6.2 arm + gates, no R4 block, R6.4, R5.2)
**THE SYSTEM SHALL** print the equivalent `ENTRY B SELL-FIRST` line and open a simulated sell-first trade at the next bar's open.

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
**THE SYSTEM SHALL** evaluate exits each completed bar in the R7 precedence order and close on the first that fires, printing `EXIT <type>` with leg P&L proxy and adverse excursion.

**WHEN** the R7.1 fill touch prints
**THE SYSTEM SHALL** record `fill` with minutes-to-fill.

**WHEN** R7.2 triggers
**THE SYSTEM SHALL** record `scratch` at the next bar's open.

**WHEN** R7.4 triggers (veto activation while carrying a short, or an opposite 13:00 read)
**THE SYSTEM SHALL** exit at the next bar's open recording `veto_exit` / `state_flip` respectively.

**WHEN** R7.3 triggers
**THE SYSTEM SHALL** record `cap`, logging whether option mid or spot proxy was used.

**WHEN** R7.5 or R7.6 applies
**THE SYSTEM SHALL** record `timeout`/`censored` or `resolution_debit`/`resolution_close` per those rules.

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
**THE SYSTEM SHALL** use HIRO partitions + SPX 1-min and evaluate R1–R7 completely, accepting only dates with both sources.

**WHEN** backtest runs with `--tier price`
**THE SYSTEM SHALL** run over the full SPX 1-min archive with every HIRO-dependent condition disabled or explicitly stubbed, stamping every output `tier=price` so a price-tier number can never be quoted as a full-rule result.

**WHEN** backtest runs the frozen config over the stored HIRO sessions (verification)
**THE SYSTEM SHALL** reproduce the reviewed research trade list EXACTLY — same entry minutes, branches, exit types — reporting any discrepancy as a defect, not a tolerance.

**WHEN** the operator runs `hiro_engine backtest --day <date> --verbose`
**THE SYSTEM SHALL** print the full live-format console stream for that day for bar-by-bar cross-checking.

**WHEN** `--config <file>` is supplied to a backtest
**THE SYSTEM SHALL** run with those overrides, stamp outputs with that config's hash, and never count any backtest row toward the live test.

**WHEN** the operator runs `hiro_engine sweep <knob>`
**THE SYSTEM SHALL** sweep exactly ONE knob from the fixed whitelist — scratch drop {−0.2…−0.6 $B}, scratch window {2…5 min}, pullback {3, 5, 8 pts}, cap {3.0…4.0}, clock {45, 60, 75 min} — holding all else frozen, rejecting any knob not listed (whitelist changes require editing this spec).

**WHEN** any backtest or sweep summarizes results
**THE SYSTEM SHALL** report per variant: trade AND episode counts, days covered, the matched control for the entry type (clock-matched for Branch B-style entries, midpoint-matched for Branch A-style), a day-clustered bootstrap 90% CI on the headline fill rate, censored trades separately; sweep leaderboards SHALL print the number of cells examined and grey out (not rank) cells with n < 15 trades or < 4 days.

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

Verification backtest reproduces the corrected 18-trade sequential research result exactly (trade-list match); two
shakedown sessions run clean (no crash, no console/log divergence); then the 10-session clock starts.

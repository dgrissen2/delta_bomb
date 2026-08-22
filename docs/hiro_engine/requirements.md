# Requirements — Delta Bomb Signal Engine ("hiro_engine")

*v2.2 — 2026-08-22. v2.1 + final plan review (6 blockers, 2 majors → fixed: signal/entry split, R7.0 exit-timing table, controls as deterministic scorecard functions, R13 backtest definitions, best-session re-check enumerated, full-tier source contract, single-backlink rule restored). Prior: v2.0 + red-team audit (31 findings, verdict FAIL → all fixed: controls and metrics defined in R11, verification artifact pinned, chain/SPY sources added, state-flip mapping, price-tier behavior enumerated, boundary and denominator rules). Self-contained: every trading rule is stated in this document with an R-number; acceptance
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
- **R1.2** Base strike K = put closest to −0.20 delta on the live chain at decision time (broker greeks; log the
  quote timestamp). If no chain feed, signals say "nearest −0.20Δ put".
- **R1.3** Size = 1 contract, paper, always (this build).
- **R1.4** Completion proxy (simulation): the second leg is deemed filled when SPX touches S0 + 3.0 (sell-first)
  / S0 − 3.0 (long-first). **S0 = the open of the EXECUTION bar** — the bar immediately after the signal bar;
  "entry bar" always means the execution bar. (Real-world required move measures 3.0–3.8 pts per the stress test recorded in the playbook; 3.0 is the frozen simulation threshold.)

## R2. Data inputs
- **R2.1** SPX 1-min OHLC bars, live (ThetaData terminal) and stored (`~/Dev/central_trade_data/thetadata/spx_index_1m_ohlc/`).
- **R2.2** HIRO S&P 500 basket payload (scopes `all`, `nextExp`; call/put split), re-pulled each minute via the
  logged-in Chrome CDP session; stored partitions at `~/Dev/central_trade_data/spotgamma/hiro/sp500_basket/v1/`.
- **R2.3** SpotGamma daily levels CSV (`~/Dev/core_spotgamma_spx_vix_data/offset_historical_spotgamma_data.csv`):
  Vol Trigger (VT), Call Wall (CW), SG index, implied move (IM; fallback: nearest-expiry ATM straddle mid ÷ spot at 09:35 via R2.5; if neither available, IM is missing and R3.4 returns CHOP).
  Levels are VALID only if the CSV row carries today's date and CW − VT > 0.
- **R2.4** Event calendar: CPI, FOMC decision day, NFP, quarterly opex Friday, month-end rebalance day.
- **R2.5** Live option chain (Schwab API, `option_chains`): strikes, bid/ask, delta — used for R1.2 strike hints,
  R7.3 option-mid cap, R7.6 implied debit, R2.3 IM fallback. **No stored chain exists for backtests**: in ALL
  backtest tiers the mandatory proxies are — strike hints omitted; cap = spot proxy (R7.3); R7.6 debit test
  skipped (always `resolution_close`); IM from the levels CSV only (missing → R3.4 returns CHOP). The
  verification artifact (R12.1) was generated under exactly these proxies.
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
  (ii) r30 < 0; (iii) bounce30 ≥ 3 pts; (iv) close < mid30. Action: BUY the −0.20Δ put at the next bar's open;
  rest the SELL of K−5 at (cost + 0.10) limit on the bid side.
- **R6.2 Branch B (sell-first; only if no R4 veto blocks shorts):** ARM when pull30 ≥ 3 pts AND the run has:
  dur ≥ 10 min, rate ≥ 2 $B/hr, ΔC > 0 ∧ ΔP > 0 with min(ΔC, ΔP) ÷ max(ΔC, ΔP) ≥ 0.25, ΔN > 0 with share ≥ 0.5, and run drawdown < 0.6 $B (implied by an unbroken run; stated for explicitness). GATES: r15 > 0; time ≤ 14:30; weak side ≥ 0.15 $B. Action: SELL the −0.20Δ put at the
  next bar's open (limit at current bid); rest the BUY of K+5 at (sale − 0.10) limit on the ask side.
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
  Execution price: fills = the touch level S0 ± 3.0 at the touch bar; every other exit = the OPEN of bar j+1;
  if no bar j+1 exists (session end), the close of bar j. The 15:30 resolution evaluates at the 15:30 bar and
  executes at its open. R11.2 adverse excursion runs over bars from the execution bar through the exit's
  execution price inclusive (fills: touch bar excluded).
- **R7.1** Fill: SPX touches S0 + 3.0 (sell-first) / S0 − 3.0 (long-first) → completed; record minutes-to-fill.
- **R7.2** Flow-shutoff scratch (Branch B): within 3 minutes of entry, L drops ≥ 0.3 $B below its entry value OR
  the run breaks, before the fill touch → scratch at the next bar's open. Branch A analogue: define BH = the highest high from the bar of the trade's reference 30-bar low through the signal bar; a bar's high > BH before the fill touch → scratch.
- **R7.3** Cap: with a chain (R2.5), the lone leg's option mid ((bid+ask)/2) moves 3.5 pts against its entry
  value → close it (`cap`). Without a chain (all backtests), the proxy trigger is SPX moving 15.0 pts against
  S0. The log records which trigger was used. Never convert by adding a different strike.
- **R7.4** Veto exit: R4.3 activating while a short is carried → scratch it at the next bar's open (`veto_exit`).
  State-flip exit (13:00 read only): mapping is by SIDE — an open sell-first leg exits if the 13:00 read is
  DOWN; an open long-first leg exits if it is UP; CHOP never triggers it. Applies regardless of when the leg
  was opened (in practice only 12:00–13:00 entries can still be open). Same-bar tie: `veto_exit` before
  `state_flip`.
- **R7.5** Clock: 60 minutes after entry without a fill → close the lone leg (`timeout`). A horizon truncated by
  session end is `censored`, never `timeout`.
- **R7.6** 15:30 resolution: implied debit (chain required) = sell-first: ask(K+5) − sale price; long-first:
  cost − bid(K−5). If debit ≤ 0.50 → complete the pair (`resolution_debit`, log the debit); otherwise, or
  whenever no chain is available (all backtests), close the lone leg (`resolution_close`).

## R8. Logging & config
- **R8.1** Every event — signal, entry, exit, veto change, skip (with reason), gate failure on an armed episode,
  outage, heartbeat — is one row in `docs/replay/hiro/paper_log.csv`: ts, mode (live/backtest/shakedown), tier,
  branch, event, rule id, S0, strikes, run/rate/ΔC/ΔP/share/r15, outcome (fill mins / scratch pts / timeout /
  censored), adverse, CONFIG_HASH, session date. The console stream and the log are the SAME stream.
- **R8.2** CONFIG = the frozen thresholds file: every numeric in R1–R7, plus the R11.4/R11.5 control-dataset
  identifier (path + data hash) and the R12.1 artifact hash. CONFIG_HASH = its SHA-256 on every row.
  A hash change vs the prior session prints a loud reset warning.

## R9. Acceptance test (the frozen 10-session exam; graded by `scorecard`; all terms per R11)
Over 10 countable sessions (live, non-shakedown, non-PARTIAL, non-event-standdown — PARTIAL and event days are
excluded from the denominator and do not consume test slots) of one CONFIG_HASH: qualifying signals on ≥ 7/10
sessions · 1–3 executable entries on ≥ 6/10 · ≥ 8 fills total AND ≥ 1 fill on 6/10 sessions · ≤ 3 entries/session,
one leg at a time · Branch B ≥ 20 qualifying signals with fill rate ≥ 0.45 and not below its frozen clock-matched
control (R11.4) · Branch A ≥ 8 qualifying episodes with fill rate ≥ 0.70 and ≥ +10 pp over its frozen
midpoint-matched control (R11.5) · branches reported separately; a minute qualifying for both counts once (as A)
· adverse excursion (R11.2) > 10 pts on ≤ 10% of executable entries, max one such trade · median scratch loss
(R11.3) ≤ 3 pts · ≤ 1 scratch whose fill touch would have printed within its 60-min horizon absent the scratch ·
the RISK RE-CHECK holds: with the best session removed (best = most fills; ties → highest summed R11.3 pnl;
ties → earliest date), recompute over the remaining sessions' entries — adverse > 10 pts still ≤ 10% of the
reduced entry count AND ≤ 1 trade; median scratch loss still ≤ 3 pts; would-have-completed scratches still ≤ 1;
thresholds unchanged, denominators reduced. A branch below its sample minimum is INCONCLUSIVE. Any rule change
resets the test.

## R11. Metric & control definitions (everything R9 needs, computable from this document)
- **R11.1 Qualifying signal / episode / executable entry:** Branch B qualifying signal = a minute satisfying
  R6.2 arm + gates inside the R5.2 window, counted per episode (R3.5) regardless of R4/R6.4 blocks. Branch A
  qualifying episode = an episode whose first minute satisfies R6.1 inside the window. **Executable entry** = a
  qualifying signal/episode that opened a simulated trade (not blocked by one-leg, the 3/day cap, or an R4 veto).
- **R11.2 Adverse excursion:** in SPX points against the completion direction, measured from S0, as the maximum
  over bars from the execution bar to the exit bar; for fills the touch bar is excluded (intrabar order unknown);
  for scratches/timeouts the exit reference price is included.
- **R11.3 Leg P&L proxy / scratch loss:** pnl = (exit reference − S0) for sell-first and (S0 − exit reference)
  for long-first, in SPX points; exit reference = S0 ± 3.0 for fills, otherwise the exit bar's next-bar open
  (or close at session end). Scratch loss = −pnl of a scratch.
- **R11.4 Frozen clock-matched control (Branch B):** a deterministic FUNCTION computed by `scorecard` at grading
  time: over the frozen control dataset (the eight research sessions 2026-08-12..21, fixed forever, identified
  in CONFIG by path + data hash), take every minute 10:00–14:30 with a complete 60-min horizon; weight minutes
  to match the clock-minute distribution of the test's Branch-B executable entries; control = weighted mean of
  the R7.1 fill-touch indicator. Deterministic given the test log; no stored constant needed.
- **R11.5 Frozen midpoint-matched control (Branch A):** same deterministic-function form over the same frozen
  dataset; candidate minutes satisfy R6.1 conditions (i), (iii), (iv) but FAIL (ii) (r30 ≥ 0); same weighting
  and indicator.
- **R11.6 Fill rate:** fills ÷ executable entries with non-censored horizons (censored excluded from the
  denominator; scratches and timeouts remain in it).

## R13. Backtesting definitions
- **R13.1 Tiers:** `full` requires HIRO + SPX 1-min per date (missing → date refused and listed); `price` runs
  the whole SPX archive with: Branch B disabled; Branch A as "price-A" (R6.1 (i), (iii), (iv) only); R4.3 and
  R7.2 disabled (BH scratch retained); all else identical; every output stamped `tier=price`.
- **R13.2 Sweep whitelist (fully enumerated; one knob per run; all else frozen):** scratch drop magnitude
  {0.2, 0.3, 0.4, 0.5, 0.6 $B below entry L} · scratch window {2, 3, 4, 5 min} · pullback {3, 5, 8 pts} ·
  cap {3.0, 3.25, 3.5, 3.75, 4.0} · clock {45, 60, 75 min}. Any other knob is rejected; changing this list
  means editing this spec.
- **R13.3 Summary contract (every backtest/sweep output):** per variant — trade count, episode count, days
  covered, matched control per entry type (R11.4 form for sell-first-style, R11.5 form for long-first-style,
  computed over the run's own dataset), day-clustered bootstrap 90% CI on the fill rate (resample days with
  replacement, 2,000 draws, seed 42), censored trades reported separately.
- **R13.4 Leaderboards:** print the number of cells examined at the top; cells with < 15 trades or < 4 days are
  displayed greyed out and excluded from ranking.

## R12. Verification artifact
- **R12.1** The normative verification target is `docs/replay/hiro/verification_trades_v1.csv` — the 27-trade
  sequential result (day, entry minute, S0, steep flag, exit type, fill flags, minutes-to-fill, adverse) produced
  by the reviewed research pipeline over the eight stored sessions under the R2.5 backtest proxies. A frozen-config
  full-tier backtest over those sessions must reproduce it row-for-row.

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

**WHEN** the time is OUTSIDE the R5.2 entry window (i.e., during R5.1 observe-only, or after 14:30)
**THE SYSTEM SHALL** track and print state changes but emit no entry signals and open no simulated trades.

**WHEN** the clock reaches 10:30 and 13:00
**THE SYSTEM SHALL** compute and print the R3.4 context read and retain it for R7.4.

**WHEN** a Branch A signal fires (R6.1, R6.4, R5.2 all satisfied) at a bar close
**THE SYSTEM SHALL** print `SIGNAL A LONG-FIRST | t | strike (R1.2) | <condition values>` immediately, and at the next bar's open print `ENTRY A | S0=<that open> | rest SELL K−5 @ cost+0.10` and open the simulated long-first trade (S0 is unknowable at signal time and never appears on a SIGNAL line).

**WHEN** a Branch B signal fires (R6.2 arm + gates, no R4 block, R6.4, R5.2)
**THE SYSTEM SHALL** print the equivalent `SIGNAL B SELL-FIRST` line immediately and the `ENTRY B | S0=<next open> | rest BUY K+5 @ sale−0.10` line at execution, opening the simulated sell-first trade.

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
**THE SYSTEM SHALL** require HIRO partitions + SPX 1-min (a date lacking either is refused and listed per R13.1); SPY 1-min and levels are used when present and degrade exactly per the live rules when absent (no SPY → R3.4 returns CHOP, logged `degraded_vwap`; invalid levels → R4.2), evaluating R1–R7 under the R2.5 backtest proxies.

**WHEN** backtest runs with `--tier price`
**THE SYSTEM SHALL** apply R13.1's price-tier behavior exactly, stamping every output `tier=price` so a price-tier number can never be quoted as a full-rule result.

**WHEN** backtest runs the frozen config over the stored HIRO sessions (verification)
**THE SYSTEM SHALL** reproduce `docs/replay/hiro/verification_trades_v1.csv` (R12.1) row-for-row — same entry minutes, sides, exit types — reporting any discrepancy as a defect, not a tolerance.

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

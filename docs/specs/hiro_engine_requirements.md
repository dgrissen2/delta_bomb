# Requirements — Delta Bomb Signal Engine ("hiro_engine")

*v1.1 — 2026-08-22 (v1.0 + backtesting grill: all three backtest purposes; two data tiers; whitelist-knob sweeps, one knob at a time; exact-match verification; verbose single-day replay). Derived from `delta_bomb_master_playbook.md` v1.3 (the playbook is normative for all trading
logic; this spec covers the software). Decisions taken in the grill session: mode (c) engine+alerts with silent
paper executor · console-only output, unified live/backtest · degraded mode (a)+(c) · no human-trade capture (for
now) · scorecard in scope · two uncounted shakedown sessions · manual morning start.*

## User Story

As a **discretionary SPX options trader running the frozen 10-session paper test**,
I want **one console program that watches live SPX 1-min bars and HIRO flow, prints entry/exit signals from the
frozen playbook rules the moment a bar completes, silently simulates every trade the rules would take, and grades
the accumulated sessions against the pre-registered acceptance criteria**,
So that **I can hand-execute signals in my broker while an incorruptible, rule-exact log and scorecard decide —
without human fudging — whether this strategy earns the next stage (option-level replay, then size)**.

## Scope

- **In:** live signal evaluation (playbook §3 precedence, §4 Branches A/B, §5 exits, §6 limits); silent paper
  executor; console event stream; session logs (`docs/replay/hiro/paper_log.csv`, playbook Appendix A schema);
  backtesting in three roles — verification harness, research tool (whitelist-knob sweeps), scorecard rehearsal —
  over two data tiers (full = HIRO sessions; price = the 845+-session SPX archive); `scorecard` command implementing
  playbook §8 including frozen controls; config freeze via hash.
- **Out (this build):** any order placement; human-fill capture/reconciliation; Branch C signals; push/mobile
  alerts; the NVDA P1 program; the SPXW quote-level replay; live sizing (hard-coded 1 lot, paper).

## Definitions

Playbook v1.3 Appendix A definitions apply verbatim (episode, run, rate, weak side, share, cap mark, event list,
level validity). CONFIG = the frozen thresholds file; CONFIG_HASH = its SHA-256, stamped on every log row.
PARTIAL SESSION = any session with a HIRO or SPX-bar outage > 15 min inside 10:00–14:30, or bars ending before 15:55.

## Acceptance Criteria

### Modes & lifecycle

**WHEN** the operator runs `hiro_engine live` on a morning where Chrome (CDP 9222, logged into SpotGamma) and the ThetaData terminal are up
**THE SYSTEM SHALL** start a session: load today's SG levels CSV and validate its date, print the P0 state banner (levels valid? VT intact? event day?), and begin per-minute evaluation.

**WHEN** the SG levels CSV is stale or missing or CW − VT ≤ 0
**THE SYSTEM SHALL** print `LEVELS MISSING → LONG-FIRST ONLY` and suppress all sell-first signals for the session.

**WHEN** today is on the event stand-down list (CPI, FOMC, NFP, quarterly opex, month-end)
**THE SYSTEM SHALL** print `EVENT DAY — STAND DOWN`, evaluate nothing, and log the session as `event_standdown`.

**WHEN** the operator runs `hiro_engine backtest --from D1 --to D2`
**THE SYSTEM SHALL** replay stored sessions through the identical rule module used live (one code path, no duplicated logic), emitting the identical console event stream with replay timestamps, and SHALL refuse dates lacking a required data source (listing them) rather than silently skipping.

### Backtesting

**WHEN** backtest runs with `--tier full` (default)
**THE SYSTEM SHALL** use HIRO partitions + SPX 1-min and evaluate the complete rule set (both branches, all HIRO features), and SHALL only accept dates with both sources present.

**WHEN** backtest runs with `--tier price`
**THE SYSTEM SHALL** run over the full SPX 1-min archive (845+ sessions) with every HIRO-dependent condition disabled or explicitly stubbed, and SHALL stamp every output row and summary `tier=price` so a price-tier number can never be quoted as a full-rule result.

**WHEN** backtest runs with the frozen config over the stored HIRO sessions (verification harness)
**THE SYSTEM SHALL** reproduce the reviewed research trade list EXACTLY — same entry minutes, branches and exit types as the corrected sequential result — and SHALL report any discrepancy as a defect, not a tolerance.

**WHEN** the operator runs `hiro_engine backtest --day <date> --verbose`
**THE SYSTEM SHALL** print the full live-format console stream for that day (state banners, veto changes, arms, gate evaluations, entries, heartbeats, exits) so any single day can be cross-checked bar-by-bar against the dashboards.

**WHEN** the operator supplies `--config <file>` to a backtest
**THE SYSTEM SHALL** run with those overrides, stamp all outputs with that config's hash, and the scorecard SHALL never count any backtest row toward the live acceptance test regardless of hash.

**WHEN** the operator runs `hiro_engine sweep <knob>`
**THE SYSTEM SHALL** sweep exactly ONE knob at a time from the fixed whitelist — scratch drop {−0.2…−0.6 $B}, scratch window {2…5 min}, pullback {3, 5, 8 pts}, cap {3.0…4.0}, clock {45, 60, 75 min} — holding all other parameters at the frozen values, and SHALL reject any knob not on the whitelist (extending the whitelist requires editing this spec).

**WHEN** any backtest or sweep summarizes results
**THE SYSTEM SHALL** report, per variant: trade AND episode counts, days covered, the matched control for the entry type (clock-matched or midpoint-matched, reusing the reviewed control logic), a day-clustered bootstrap 90% CI on the headline fill rate, and censored trades counted separately; sweep leaderboards SHALL print the number of cells examined at the top and SHALL grey out (not rank) cells with n < 15 trades or < 4 days.

**WHEN** the operator runs `hiro_engine scorecard --rehearsal --from D1 --to D2`
**THE SYSTEM SHALL** grade historical sessions with the full §8 logic as a dry run, clearly labeled REHEARSAL and excluded from the live test record.

### Evaluation & signals

**WHEN** a 1-min SPX bar completes during 09:30–16:00
**THE SYSTEM SHALL** within 5 seconds re-pull the HIRO S&P 500 payload, recompute all features (playbook §4 conditions, Appendix A definitions), and evaluate P0 → P1 → P2 in that order.

**WHEN** a Branch A signal fires (all four §4A conditions true, ≥ 10:35, no P0 block, flat, < 3 entries today, new episode)
**THE SYSTEM SHALL** print one entry line: `ENTRY A LONG-FIRST | t | S0=<next-open ref> | buy ~20Δ put (strike hint if chain available) | rest SELL K−5 @ cost+0.10 | reason: <condition values>`, and open a simulated long-first trade at the next bar's open.

**WHEN** a Branch B signal fires (arm + all gates, no P0 block on shorts, flat, < 3 entries, new episode)
**THE SYSTEM SHALL** print the equivalent `ENTRY B SELL-FIRST` line and open a simulated sell-first trade at the next bar's open.

**WHEN** Branch A and Branch B fire on the same bar
**THE SYSTEM SHALL** take only Branch A.

**WHEN** a setup remains continuously true
**THE SYSTEM SHALL** signal it exactly once per episode (episode per Appendix A).

**WHEN** the steep/late condition holds (rate ≥ 4 $B/hr ∧ 30-min flow ≥ 1 $B)
**THE SYSTEM SHALL** suppress Branch B entries and print a single `LATE — NO ENTRY` state line per episode.

**WHEN** any P0 veto state changes (VT first broken; HIRO 15-min all ∧ nextExp < −0.8 $B begins/ends)
**THE SYSTEM SHALL** print one state-change line.

### Simulated executor & exits

**WHEN** a simulated trade is open
**THE SYSTEM SHALL** evaluate exits each completed bar in the frozen precedence order — fill > flow-shutoff scratch > price cap > state flip (13:00 read only) > 60-min clock > 15:30 resolution — and close the trade on the first that fires, printing `EXIT <type>` with the leg P&L proxy and adverse excursion.

**WHEN** the completion touch prints (S0 + 3.5-planning is NOT used here; completion = ±3 pts spot proxy per the frozen registration)
**THE SYSTEM SHALL** record `fill` with minutes-to-fill.

**WHEN** a sell-first trade is open and within 3 minutes of entry the HIRO all-line drops ≥ 0.3 $B below its entry level or the run breaks, before +3 prints
**THE SYSTEM SHALL** record `scratch` at the next bar's open (long-first mirror: bounce-high re-take).

**WHEN** the carried leg's mid moves 3.5 pts against entry
**THE SYSTEM SHALL** record `cap` (mid = (bid+ask)/2 when a chain feed is present; spot ±15-pt proxy otherwise, and the log SHALL say which was used).

**WHEN** 60 minutes pass unfilled, or 15:30 arrives
**THE SYSTEM SHALL** record `timeout` / `resolution` respectively; a horizon truncated by session end SHALL be recorded `censored`, never `timeout`.

**WHEN** a trade is open
**THE SYSTEM SHALL** print a one-line status heartbeat every 5 minutes (state, clock remaining, current adverse).

### Degraded mode

**WHEN** the HIRO pull fails
**THE SYSTEM SHALL** print `HIRO DOWN`, suppress all new entries (never substituting Branch C), continue managing any open simulated trade with the non-HIRO exits (logging `scratch_unavailable`), and print `HIRO RESTORED` with the outage span on recovery.

**WHEN** cumulative HIRO outage inside 10:00–14:30 exceeds 15 minutes
**THE SYSTEM SHALL** flag the session PARTIAL.

**WHEN** the SPX bar feed stalls > 2 minutes
**THE SYSTEM SHALL** treat it identically (no entries; flag if > 15 min).

### Logging & config freeze

**WHEN** any event occurs (signal, entry, exit, veto change, skip with reason, outage, heartbeat suppressed from file)
**THE SYSTEM SHALL** append one row to `docs/replay/hiro/paper_log.csv` in the Appendix A schema, stamped with CONFIG_HASH, session date, and mode (live/backtest/shakedown).

**WHEN** the engine starts with CONFIG whose hash differs from the previous session's
**THE SYSTEM SHALL** print a loud warning stating that mixing hashes resets the acceptance test.

### Shakedown & scorecard

**WHEN** the operator marks a session `--shakedown` (the first two live sessions)
**THE SYSTEM SHALL** log it fully but tag it `shakedown`, and the scorecard SHALL exclude it from all counts.

**WHEN** the operator runs `hiro_engine scorecard`
**THE SYSTEM SHALL** read all non-shakedown live sessions of the current CONFIG_HASH and print the full §8 table — each criterion, its measured value, its threshold, PASS/FAIL/ INCONCLUSIVE — including the frozen clock-matched control for BASE and midpoint-matched control for TAPE (reusing the reviewed logic from `hiro_uptrend_confirm.py` / `hiro_experiments.py`), partial-session handling, the best-session-excluded safety re-check, and an overall verdict line.

**WHEN** sessions with different CONFIG_HASHes exist in the log
**THE SYSTEM SHALL** refuse to combine them in one scorecard and say why.

**WHEN** fewer than a branch's minimum observations exist (BASE < 20 signals, TAPE < 8 episodes)
**THE SYSTEM SHALL** report that branch INCONCLUSIVE, not failed or passed.

## Non-functional
Console only; no GUI, no notifications. Single Python process, started manually each morning; runs on the local
Mac; venv `~/Dev/virtualenvs/gamma_chaser`. Evaluation latency ≤ 5 s after bar close. All timestamps ET. Crash
recovery: on restart mid-session, reload today's log and resume state (open simulated trade reconstructed from its
entry row). The rule code SHALL be one module shared verbatim between live and backtest (no duplicated logic).

## Acceptance of this spec
Verification backtest reproduces the corrected 18-trade sequential result exactly (trade-list match); two shakedown sessions run clean (no crash, no unexplained divergence between console and log); then
the 10-session clock starts.

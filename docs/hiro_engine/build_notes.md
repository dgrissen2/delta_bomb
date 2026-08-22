# hiro_engine — build notes (frozen interpretation decisions & known gaps)

*Started 2026-08-22 during implementation of tasks.md v1.2. Each entry is either a
spec interpretation frozen during the build (with the R-number) or a logged
artifact/spec issue per the task-3a artifact-rot guard. Nothing here changes a
threshold; thresholds live only in `scripts/hiro_engine/config.yaml`.*

## Artifact-rot guard log (task 3a)

1. **Artifact reproduced before porting (2026-08-22).** `hiro_uptrend_confirm.sequential()`
   over the 8 stored sessions reproduces `verification_trades_v1.csv` 27/27.
   sha256 `a95ffe33…a9630` pinned in config. Golden gate passes through the
   engine's ported core (engine loaders + `apply_run_machine` + rule predicates).
2. **The artifact encodes RESEARCH semantics, not live R5/R6.4.** It contains a
   09:59 entry (t=599 < 10:00), 7 trades on 2026-08-12 (> the 3/day cap), no VT
   veto, +5-touch completion with a 60-min one-trade-at-a-time loop. A live-rule
   backtest therefore CANNOT reproduce it and never will. Resolution: `verify.py`
   replays the pinned research semantics through the engine's ported core (that
   is what the artifact verifies: loaders, run machine, condition thresholds,
   outcome math). Logged as a spec/artifact issue, not silently fixed. The
   live-rule stream is separately validated by the task-6 determinism test and
   the table-driven R4–R7 suite.
3. **R7.2 scratch window off-by-one vs research.** Research invalidation runs
   j−signal ≤ 3 bars (= entry bar + 2). The spec says "within 3 minutes of
   entry" — the engine implements j−entry ≤ 3 (spec text wins for live rules;
   verify.py keeps the research form).

## Frozen interpretation decisions

- **R5.2 windows bind the SIGNAL minute** (B: 10:00 ≤ t ≤ 14:30, A: ≥ 10:35);
  execution is at t+1 open (research convention; artifact contains a t=870 trade).
- **R7.2 Branch-B flow anchor = L at the SIGNAL bar** (research `L0`), carried on
  the PendingEntry; Branch-A BH likewise fixed at signal time from the signal row.
- **R7.3 spot-proxy cap** compares the bar CLOSE to S0 (conditions evaluate at
  bar close per R7.0); the option-mid path is live-only (R2.5).
- **R3.4 VWAP leg** compares SPY closes to the SPY volume-VWAP (SPX has no
  volume; SPY is the spec'd proxy). EMA legs use SPX 1-min closes.
- **R3.3 pooled range60 history**: full tier seeds causally from stored HIRO-era
  sessions before the run/current day; price tier accumulates over the run's own
  days (pre-HIRO-era dates have no HIRO-era history by construction).
- **Backtest event stream** goes to `paper_log_backtest.csv` (separate file, same
  schema/stream) so backtest bytes can never contaminate the live R9 record;
  R8.1's "one stream" holds per run (console == CSV, same Event objects).
- **Episode ids** are per-branch counters; Branch-B episodes hard-break on run
  break (R3.5); a lapse of ≥ 3 consecutive false minutes ends either branch's episode.

## Known data gaps (ops)

- **Levels CSV has no implied-move column** → IM is None in every backtest →
  R3.4 returns CHOP → state_flip cannot fire in backtests (spec-conformant
  fail-closed path; live IM comes from the R2.5 straddle fallback).
- **SPY 1-min store ends 2026-06-11** → HIRO-era backtests run DEGRADED_VWAP.
  Live uses ThetaData SPY. Evening ops script flags SPY staleness; backfill when
  convenient.
- **Event calendar CSV ships empty for CPI/FOMC** (fabricating release dates is
  worse than warning); NFP/quarterly-opex/month-end are computed. The morning
  ops script warns when the current month has no CPI/FOMC rows.

## Break point 1 review (2026-08-22, after tasks 1–6 + 8–9)

Red-team-auditor: FAIL (1 blocker, 3 majors, 6 minors). Codex review: FAIL
(1 blocker, 7 majors; two overlapped the red team). ALL applied:

- **range60 definition (blocker)**: was closes-range excl. current bar; now the
  researched rolling-60 HIGHmax − LOWmin INCLUDING the current bar
  (hiro_lab.py:77); threshold (expanding p75) stays shifted one bar. Fixed in
  features/session/control.
- **price tier ≠ HIRO outage (blocker)**: TierPolicy.requires_hiro; price-tier
  archive runs no longer flag HIRO_DOWN/partial or skip price-A entries.
- **crash-resume**: `Session.warm_replay` rebuilds ALL warm state (features,
  vt_broken, episodes, rule dedup, executor) by muted deterministic replay,
  cross-checked against the log-derived state (RESUME WARNING on divergence);
  test proves resumed stream == uninterrupted stream.
- **resolution adverse** stops at the 15:30 OPEN (the bar's later range never
  counts); **r5/r15/r30/r15n** are true MINUTE diffs (bisect on minute), equal
  to row offsets on a gapless grid, correct across stalls.
- **A-episode window (R11.1)**: an A episode only fires if its FIRST minute is
  ≥ 10:35 (episode start minutes now tracked).
- **range60 pool** for day D = ALL stored sessions in [pool_start, D),
  independent of the run's requested dates (test: 08-21 solo == 08-21 in a
  gapped pair). pool_start = hiro_era_start (full) / archive start (price).
- signal/skip/gate/late events now carry run/rate/ΔC/ΔP/share/r15/pull30/
  bounce30 + the R1.2 strike hint; skips dedupe per (branch, episode, reason);
  scratch_unavailable is a real logged line owned by rules; backtest sessions
  write sessions_backtest.csv and the R8.2 hash warning reads live rows only;
  backtests always echo; NFP first-Friday can be overridden (reason `none`
  clears a computed event day); chain-path cap reads row.option_mid_move
  (Session attaches it live — wired in task 7).
- exit precedence now tested for EVERY feasible simultaneous pair (20 cases;
  clock+resolution and state_flip+resolution are infeasible by construction).

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

## Break point 2 review (2026-08-22, after tasks 7–11)

Codex: FAIL (2 blockers, 12 majors). Eleven applied; two declined with cause;
one reclassified:

- **Applied**: resume now warm-replays only bars ≤ the last LOGGED minute and
  processes downtime bars live (they are evaluated AND logged, never muted);
  16:00 shutdown does a final catch-up pull so 15:59 is always processed; HIRO
  stale-but-nonempty payload (max minute < bar − 2) is HIRO_DOWN with outage
  minutes; SPX gaps > 2 min emit an R10.2 SPX_STALLED outage row; scorecard
  below-minimum branch rows are INCONCLUSIVE (never FAIL); would-have-filled
  window includes the timeout bar (fill beats clock there); ordinary backtests
  print the R13.3 summary; morning incomplete-SPX and missing-manifest checks
  are RED, not warnings; spike script exits nonzero on FAIL.
- **Decision flipped** (spec letter wins): R6.3 late-suppressed episodes DO
  count as qualifying (R11.1's arm+gates are satisfied; suppression only blocks
  the entry) — stage3 now consumes late_no_entry events too.
- **Declined — veto_exit is not an R11.3 "scratch"**: R7.4 uses "scratch it" as
  the verb but assigns the distinct outcome `veto_exit`; R11.3/R9 "scratch"
  metrics bind to the R7.2 outcome. Counting veto exits as scratches would mix
  a veto-driven exit into a flow-shutoff quality metric.
- **Declined — cap sweep scales the spot proxy**: in backtests the option-mid
  cap is structurally dead (R2.5 proxies); sweeping cap_option_pts alone would
  be a literal no-op and the R13.2 cap knob meaningless. The proxy scales by
  the frozen 15.0/3.5 ratio; both values are stamped into the variant's
  CONFIG_HASH so nothing is hidden.
- **Chain adapter**: chain-less operation is a spec-defined mode (R1.2 "if no
  chain feed…", R2.5 proxies). live now prints a loud NO CHAIN FEED banner;
  wiring Schwab (option-mid cap, debit resolution, IM straddle) remains open
  work that needs a live session to validate.

Red-team bp2 (same milestone, ran in parallel with codex): findings 1–3 and
8–9 were already covered by the codex-round fixes. Additionally applied:
- **hiro_fresh was vacuously true** — the minute-frame reindex extended flat to
  16:00, so a stale-but-successful live payload looked healthy. The frame now
  truncates at the last RAW payload minute; staleness → HIRO_DOWN + outage.
- **Chain cap can never go capless**: if the option mid is unavailable on a bar
  of a chain-mode trade, the 15-pt spot proxy applies (`cap_source=proxy_fallback`).
- **Control fill window aligned to the engine** (entry..entry+60 incl. the
  timeout bar, where fill beats clock): golden B control repinned 0.7102 → 0.7081.
- Scorecard: one-leg-at-a-time criterion row added (chronological log scan);
  loud warning when the graded log's hash differs from the CURRENT config hash.
- Control r30 row-offset concern: verified all 8 frozen sessions are minute-
  gapless, so row offset == minute offset on the control dataset (no change).
- Chain wiring (Schwab option-mid cap / debit resolution / IM straddle) remains
  OPEN, needs a live session; live runs proxy-mode with a loud banner until then.


## ThetaData access correction (2026-08-23, user direction)

- live.py now uses the **ThetaData Python SDK** (`ThetaClient(creds_file=
  ~/Dev/ThetaData/creds.txt)`, project convention per fetch_nvda_1m.py) instead
  of raw REST against a local terminal — the v3 SDK authenticates directly, no
  terminal process at all. Verified: SDK SPX 1-min == stored parquet exactly
  (2026-08-20, 391 bars, 0 diff).
- **SPY stock history is PERMISSION_DENIED on the current index-only ThetaData
  subscription** → live sessions run the spec'd DEGRADED_VWAP path (R3.4 →
  CHOP), logged once. No practical impact while the chain (and hence IM) is
  unwired — context reads were CHOP regardless. Options if wanted later:
  ThetaData stock tier, or Schwab price_history as the SPY source (spec edit).
- **2026-08-21 SPX parquet stays truncated (15:27) FOREVER**: it is part of the
  R11.4 frozen control dataset ("fixed forever", hash-pinned in config).
  Yesterday's note suggesting a refresh was wrong — refreshing would invalidate
  the control-data pin and potentially the verification artifact. Ops scripts
  now exempt frozen control days from the completeness RED and say
  "hash-pinned, DO NOT refresh".

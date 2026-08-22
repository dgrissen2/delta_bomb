# Implementation Tasks — hiro_engine

*Architect breakdown of `design.md` v1.1 against `requirements.md` v2.2. Order is dependency order; every task
ends green (tests pass) before the next starts. "Rn" = requirement section in requirements.md. Junior notes are
inline — when in doubt, the requirement text wins over this file.*

- [ ] 1. Scaffold & frozen config
    - `hiro_engine/` package under `scripts/` (plain Python, no framework); venv `gamma_chaser`
    - `config.py` + `config.yaml`: every numeric from R1–R7 (copy them one by one from the spec),
      control-dataset path + data hash, verification artifact hash
    - `CONFIG_HASH` = sha256 of the yaml bytes; unit test: editing any value changes the hash
    - Tests: config loads; a missing key raises (fail closed, no defaults)
    Requirements: R8.2

- [ ] 2. Stored-data loaders (backtest inputs first — no live plumbing yet)
    - SPX Bar reader (per-date parquet), SpyBar reader (databento parquet, has volume)
    - `levels.py` LevelsLoader: parse the SG CSV; valid only if row date == session date AND CW − VT > 0;
      invalid → `Levels.valid=False` (never guess)
    - `calendar.py` CalendarLoader: the R2.4 list, one function `is_event_day(date)`
    - `feeds.ReplayFeed` (tier=full): yields completed bars in order; refuses+lists dates missing
      HIRO or SPX (R13.1); SPY/levels absent → flags for degraded handling, not errors
    - Tests: known day loads bar-for-bar; missing-date refusal lists the dates; stale levels → invalid
    Requirements: R2.1–R2.4, R13.1 (full tier only)

- [ ] 3. FeatureEngine (pure functions — the file a junior should study first)
    - HIRO lines L/Lc/Lp/N from the normalized CSV minutes (R3.1); rolling r5/r15/r30/r15n
    - Trough-anchored run machine (R3.2): port from `hiro_setup_dashboard.detect()` VERBATIM, then make
      the dashboard import it from here (delete the copy — DRY ledger)
    - Price windows (R3.3) incl. strict 30-bar mins/periods, range60_pct via startup replay of stored
      HIRO-era sessions (log `warmup` below 300 obs)
    - EMA5/9/20, SPY VWAP (cumulative from 09:30), context read at 10:30/13:00 only (R3.4), retained fields
    - Per-branch episode tracker (R3.5)
    - Tests: hand-built fixtures for trough/break/re-anchor; VWAP against a hand-computed day;
      context read fixture (UP day, DOWN day, CHOP); warmup path
    Requirements: R3

- [ ] 4. RuleEngine (all judgment lives here; nothing else decides anything)
    - R4 vetoes as pure checks producing VetoChange events on transitions
    - R6 entries: Branch A (R6.1), Branch B arm+gates (R6.2), late suppression (R6.3), limits (R6.4),
      serial pricing note (R6.5), A-beats-B tie (emit PendingEntry)
    - R7 exits incl. full precedence (R7.0 order) emitting ExitDecision; state-flip side mapping (R7.4)
    - Tests: table-driven — one fixture bar per rule; every pair of simultaneous exits (higher wins);
      entry blocked by each veto; one-entry-per-episode
    Requirements: R4, R5, R6, R7

- [ ] 5. Executor + EventLog (state and prices, no judgment)
    - `execute_pending()` at bar open (S0 = that open, R1.4); `apply()` prices exits per R7.0
    - SimTrade with every field from design.md; all fields persisted in ENTRY/EXIT events
    - Event schema v1 (explicit columns, no catch-all); ONE formatter → console line == CSV row
    - Crash-resume: on start, replay today's CSV to rebuild EngineState; kill/restart test must
      reconstruct the open SimTrade field-for-field
    - Tests: property (≤1 open trade; ≤3 entries/day; PendingEntry executes exactly once at next open);
      console/CSV identity per event type; round-trip resume
    Requirements: R1.4, R7.0, R8.1, non-functional (crash recovery)

- [ ] 6. Backtest CLI + THE verification milestone
    - `cli.py backtest --from --to [--day --verbose] [--tier] [--config]`
    - Determinism test: same day twice → byte-identical streams
    - **GOLDEN GATE: full-tier frozen-config backtest over the 8 stored sessions reproduces
      `docs/replay/hiro/verification_trades_v1.csv` row-for-row (R12.1). Do not proceed past this task
      until it passes — every later task builds on trusted rule code.**
    - `--day 2026-08-18 --verbose` manually checked against the entry carousel
    Requirements: R12, backtest ACs (modes & lifecycle)

- [ ] 7. Live plumbing + degraded mode
    - LiveFeed: ThetaData SPX bars; HIRO snapshot via the CDP session (import the pull from
      HIRO_finder backfill code — do not copy it); Schwab chain (R2.5); SPY bars
    - Session health machine: OK/HIRO_DOWN/SPX_STALLED/DEGRADED_VWAP; outage minutes; recovery lines;
      `scratch_unavailable`; end-of-session SessionRow disposition (R10.3, partial/event/shakedown)
    - `cli.py live [--shakedown]`; startup banner (levels, vetoes, event day); 5-s post-bar budget measured
    - Tests: fake feed that drops HIRO mid-trade → R10.1 path; SPX stall → first-bar-after semantics;
      chain-absent → proxy paths with cap_source logged
    Requirements: R2.5, R2.6, R10, live ACs

- [ ] 8. Controls + Scorecard
    - `control.py`: clock_matched (R11.4), midpoint_matched (R11.5) ported once from
      `hiro_uptrend_confirm.py`/`hiro_experiments.py`; those scripts then import from here
    - Golden test: control values over the 8 sessions == the published research numbers
    - `scorecard.py`: the six-stage pipeline from design.md, each stage writing its frame;
      R9 criteria table incl. best-session re-check tie-breaks; refuses mixed hashes;
      INCONCLUSIVE below minimums; `--rehearsal`
    - Golden test: synthetic 10-session fixture log == hand-computed R9 table (build the fixture to
      exercise qualifying-vs-executable, censored denominators, A-over-B dedupe, every tie-break)
    Requirements: R9, R11, shakedown & scorecard ACs

- [ ] 9. Price tier + sweep + summarizer
    - TierPolicy objects (`full`, `price`) consumed by features/rules; tier stamp on every row
    - `summarize.py`: one summarizer (R13.3) incl. day-clustered bootstrap (2,000 draws, default_rng(42))
    - `sweep.py`: whitelist dict literally from R13.2; one knob per run; leaderboard per R13.4
    - Tests: same fixture day under full vs price shows exactly the enumerated R13.1 differences;
      unknown knob rejected; leaderboard greys out small cells
    Requirements: R13, backtest ACs (tiers, sweep, summaries)

- [ ] 10. Integration validation & shakedown readiness
    - Boundary table: 14:30 entry → 15:30 resolution; session-end censoring; post-15:30 log-only
    - End-to-end: two full replayed sessions live-style (wall-clock compressed) with a forced crash+resume
    - Docs: one-page RUNBOOK.md (morning start checklist, what each console line means, what to do on
      each banner) — written for the trader, not the engineer
    - Then: run the two live shakedown sessions (spec acceptance); fix only defects, never thresholds
    Requirements: spec acceptance, R5 boundaries, non-functional

Estimated shape: tasks 1–6 are the core (must be perfect); 7 is plumbing; 8–9 are offline analytics; 10 is
verification. If time-boxed, nothing ships until task 6's golden gate passes.

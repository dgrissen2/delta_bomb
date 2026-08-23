# Implementation Tasks — hiro_engine

*Architect breakdown v2.0 (2026-08-23): tasks 1–12 (spec v2.x build) are COMPLETE — kept below for the
record. Tasks 13–20 implement spec v3.0 "real resting-limit fills" per design.md v2.0 (both docs passed
their multi-round reviews; see `limit_fill_reviews_2026-08-23.md` and the git log). Order is dependency
order; every task ends green before the next starts; junior notes inline — when in doubt the
requirements text wins over this file. DO NOT START without the user's explicit go.*

## v3.0 tasks (build order is the contract)

- [ ] 13. ChainStore + pins (`chains.py`) — the ONLY module touching the option-chain client
    - full-chain full-day 1-min NBBO+greeks cache per session (one SDK pull/day) under
      `~/Dev/central_trade_data/thetadata/spxw_bomb_chains/` + manifest; fetch the 8 rehearsal sessions;
      update central-data DATA_DICTIONARY/CHANGELOG in the same pass
    - CONFIG pins (R8.2): frozen-rehearsal cache manifest sha256 + thetadata SDK version (PIN SCOPE:
      the frozen set only — live chain data is never a rolling pin)
    - QuoteView builder (R10.4 validity: bid>0, ask≥bid; quote_age=0 for decisions);
      signal_snapshot(min); strike_series(strike)
    - MIGRATION: delete/absorb the existing `live.py` ChainAdapter — after this task, chains.py is the
      only production module importing any option-chain client. Boundary test: an import-scan test
      asserts no module outside chains.py references the option client (the task-14 spike script is
      the ONE named diagnostic exception)
    - REAL-CACHE SANITY (strategy-blind, protects the one-shot rehearsal): on the fetched 8 sessions
      assert tick-grid conformance (all quotes on the 0.05/0.10 grid), put mids ≥ intrinsic − 1 tick,
      delta monotonic in strike, minute alignment == the SPX bar grid; any violation → stop, units/
      timezone bug
    - Tests: cache determinism (re-load == bytes); hash guard raises on any byte change; R13.1 refusal
      lists missing dates; validity table (crossed/zero-bid/locked); the import-boundary scan; the
      real-cache sanity suite
    Requirements: R2.5, R10.4 (validity), R13.1

- [ ] 14. LIVE QUOTE SPIKE (market hours; BEFORE any pricing code — the schedule risk lives here)
    - prove ONE of (i) SDK live option snapshots or (ii) Schwab chain quotes, at 1-min cadence, for BOTH
      workloads: full-chain snapshot at a signal minute AND two-strike freshness afterward, inside the
      5-s post-bar budget; measure latency/failure/staleness like the HIRO spike
    - script: `scripts/hiro_engine/spike_chain_live.py`, PASS/FAIL verdict, nonzero exit on FAIL
    - **HARD GATE: neither works → STOP; v3.0 cannot go live (no fallback exists by spec).** Backtest
      work (15–18) may proceed regardless — only live/shakedown blocks on this
    Requirements: R2.5 (live)

- [ ] 15A. GATE-2 HAND FIXTURE (independent, closes BEFORE 15B may begin — R12.2)
    - write `tests/fixtures/v3_quotes_fixture.py` + hand-computed expected outputs with the derivation
      arithmetic in comments: both sides, tick rounding against us, t+2 first eligibility, same-minute
      fill-vs-scratch race (fill wins), every cancel path, 5th-gap data_invalid, session-end booking,
      entry-abort
    - CLOSE CONDITION: fixture + derivations COMMITTED and reviewed while `scripts/hiro_engine` contains
      ZERO v3 pricing code (the commit history proves the ordering); expected values may never be
      edited to match observed behavior afterward — a mismatch is a defect investigation

- [ ] 15B. Pricing layer (built against the frozen 15A fixture)
    - 15b. models: QuoteSnap/QuoteView/RestingLimit; SimTrade v3 fields; Event schema_v=2 ADDITIVE columns
      (design "Event v2" list); TierPolicy.fill_mode (+ spot_touch for price tier); config.yaml v3 keys
      (resolution_debit_max REMOVED; new pins as placeholders)
    - 15c. session: attach QuoteView + quote_gap streak (Session counts, like vetoes);
      resolve_instruments (chains.signal_snapshot + InstrumentSelector, R1.2 constraints; missing →
      entry_aborted_no_quote); LIVE OPTION-OUTAGE HEALTH: chain-loss banner (`NO OPTION QUOTES —
      STAND DOWN`), new-entry stand-down while quotes are absent (even with no open trade), outage
      minutes counted toward R10.3 PARTIAL; fake-feed test drops quotes for 10 min with no open
      trade and asserts no pending entries + outage counted; delta-ledger docstring updates
    - 15d. rules: limit_filled + t+2 guard INSIDE the single R7 arbitration; 5th-gap limit cancel;
      heartbeat carries streak + last-valid NBBO; quote_gap rows carry them too
    - 15e. executor: leg-1 closing-NBBO conservative booking; RestingLimit lifecycle; leg-2 booking at L
      (+0.10 invariant asserted in code); conservative NBBO exit booking per R7.0; resolution_debit
      branch DELETED; data_invalid as horizon property
    - 15f. eventlog + SIDECAR CONTRACT: v2 columns; rebuild_state learns fill/limit_canceled/
      quote_gap/entry_aborted; the snapshot-sidecar SCHEMA + writer + reader live HERE (frozen
      interface, exercised by a fixture sidecar in tests) with the resume authority rules (sidecar
      quotes; logged decisions authoritative; widened RESUME WARNING) — 15f's resume tests run
      against a SYNTHETIC sidecar built from the frozen schema (no live capture exists yet); task 19
      only WIRES the writer into the live loop, it may not change the format
    - 15g. EXISTING-TEST MIGRATION TABLE (the old suite CANNOT simply "stay green" — v2.x tests assert
      SPX-touch fills, next-bar-open booking, S0 targets, resolution_debit, point risk lines).
      Disposition, test by test, committed WITH the code changes:
        SUPERSEDED by the 15A fixture (delete): test_rules fill checks via bar.high>=target; every
          test_exit_pairs "fill+X" pair; executor touch/target assertions; resolution_debit round-trip
        RE-PARAMETERIZED to price tier (spot_touch keeps them meaningful): boundary open-booking tests
          that survive as legacy-tier checks — EXCEPT Branch-B pairs (B is disabled in price tier):
          those are fixture-superseded, not re-parameterized
        UPDATED in place: config key assertions (fill_touch_pts → the R1.4 constants), scorecard
          goldens (→ $ lines), determinism/e2e (same shape, v3 stream)
      Weakening an assertion without a row in this table is a review-rejectable change
    - R11.3 $-P&L math is ONE shared function defined in 15b (models/metrics), imported by executor,
      scorecard (17) and register (16) — never re-implemented
    - 15d MUST NOT rename Core/b_aligned/b_gates/late_state or the feature core (verify.py's legacy
      gate imports them; R12.1 stays green throughout)
    - Task 15 (15b–15g) is ONE green unit: transient breakage inside it is expected (e.g. removing
      resolution_debit_max breaks Executor.__init__ until 15e); the suite is green at the 15-boundary
    - INTERLOCK (protects the R9a boundary): while `r9a_formulas_hash` is EMPTY, `backtest` over any
      of the 8 control sessions under full tier prints a loud REFUSAL (override flag exists for the
      15A-fixture and unit tests only, which use synthetic days) — no accidental rehearsal
    - Tests: the ENTIRE 15A fixture passes; round-trip SimTrade⊕RestingLimit from rows; property tests
      (one leg, 3/day, credit ≥ 0.10 on every fill); golden gate R12.1 still green
    Requirements: R1.2, R1.4, R7.0–R7.6, R8.1, R10.4, R12.2

- [ ] 16. Pre-registration freeze (R9a) — BEFORE any v3 rehearsal runs
    - `register.py` + `cli register-thresholds`: the frozen R9a derivation (one bootstrap, count floors,
      fill-rate floors, $-risk caps, empty-resample rule)
    - TWO DISTINCT CONFIG PINS, never reused: `r9a_formulas_hash` (pinned HERE, pre-rehearsal — the
      hash of the derivation code+formulas text) and `r9a_registration_hash` (EMPTY until task 18 pins
      registration.json). register-thresholds REFUSES to run if (a) `r9a_registration_hash` is already
      non-empty (run-once), OR (b) `r9a_formulas_hash` is empty or does not match the self-hash of its
      own derivation code (the freeze must be real before the shot is spent)
    - SCOPE: task 16 is register.py + pins ONLY — the stage6 rewiring moves to task 17 so every task
      still ends green; scorecard (from 17 on) REFUSES to grade LIVE sessions while
      `r9a_registration_hash` is empty (rehearsal-labeled runs allowed)
    - Tests: derivation on a synthetic log matches hand-computed floors incl. empty-resample and
      rounding edges; refuses to run twice
    Requirements: R9, R9a

- [ ] 17. Scorecard/controls/summarizer v3
    - scorecard: $ metrics (R11.3 ×100, realized loss, +$10/fill), data_invalid scoping per R9,
      limit-replay would-have-filled with INDETERMINATE on ≥5-min gaps, best-session $ tie-break
    - `controls_build` job → derived ControlFrame (indicator per R11.4/5: signal-minute candidate,
      pure limit replay, no R7 exits, min(60, session end)); manifest cross-links source-cache sha;
      frame sha pinned in CONFIG; scorecard verifies frame.source_sha == pinned cache sha
    - stage6 rewired to read thresholds FROM CONFIG (moved here from 16; hardcoded v2 thresholds
      deleted HERE so this task ends green); refuse-to-grade-live-unregistered rule + test
    - controls_build PLAUSIBILITY BAND: if the control fill-indicator base rate is ≈0% or ≈100%,
      STOP — that is a units/sign bug, not a market fact (protects the one-shot rehearsal)
    - summarizer units per TierPolicy.fill_mode (spot_touch = SPX pts, $ suppressed)
    - Tests: hand-computed weighting fixture; control frame pinned at first build; synthetic-log
      scorecard golden updated to v3 semantics
    Requirements: R9, R11, R13.3
    (Sweep: NO new knob — R13.2 unchanged; the 0.10 credit is frozen)

- [ ] 18. One rehearsal run → thresholds → verification artifact v2
    - run the v3.0 full-tier rehearsal over the 8 sessions ONCE; `register-thresholds` populates the
      «16b» markers (spec + config patch applied and committed); registration.json hash pinned into
      `r9a_registration_hash` (the formulas pin from task 16 is untouched)
    - spot-check the trade list row-by-row against raw cached quotes; pin as verification artifact v2
      (R12.3) in CONFIG; document the after picture (fills, credits, $ risk) in build_notes
    - defect policy per R9a (fix → re-run ONCE → document)
    Requirements: R9a, R12.3

- [ ] 19. Readiness battery + parity plumbing (MARKET-INDEPENDENT — closes offline)
    - full test battery green from repo root AND scripts/; determinism (same day twice byte-identical)
      re-proven under v3; crash-resume e2e re-proven against a FIXTURE sidecar (15f contract)
    - wire the 15f sidecar writer into the live loop; `cli parity-check <date>` implemented and proven
      against a synthetic capture (fixture live-snapshots vs fixture historical series, incl. a
      deliberate 1-tick mismatch case) — tolerance pre-registered: 100% fill-decision agreement,
      prices within 1 tick on ≥95% of minutes
    - RUNBOOK/ops: chain-cache freshness + sidecar presence in morning/evening checks; quote-gap and
      stand-down console lines documented for the trader
    - LIVE-STARTUP INTERLOCKS: `cli live` REFUSES to start unless (a) the task-14 spike artifact
      exists and says PASS, and (b) the sidecar path is writable — task-20 preconditions become
      mechanical, not textual (RUNBOOK documents both refusal messages)
    - docs: master-playbook gets a one-line v3.0 status note (fills are now real resting-limit
      fills; ±3-pt touch retired); build_notes records that CONFIG_HASH legitimately churns at
      13/15b/16/17/18 during the build (hash tests stay RELATIVE; each churn re-triggers the R8.2
      loud warning — expected until the clock starts)
    - READINESS GATE (deterministic): everything above green with NO live session required
    Requirements: R12.3 parity mechanics, R2 [OPS], non-functional

- [ ] 20. Shakedown sequence (market-dependent, after 14 PASS + 19's readiness gate)
    - shakedown day 1 (live `--shakedown`) → NEXT DAY: `parity-check day1` must PASS → shakedown day 2
      → NEXT DAY: `parity-check day2` must PASS → only then does the 10-session clock start
    - dispositions written; ops green both days; fix only defects, never thresholds; a parity FAIL
      stops the sequence (investigate, fix, restart shakedown)
    Requirements: spec acceptance, R12.3 parity gate (live)

Estimated shape: 13+15 are the bulk (the fixture in 15a is the single most important artifact — hand
derivations reviewed before code); 14 is the schedule risk (first market morning); 16–17 are offline;
18 is one afternoon IF 15's fixture was honest. Do NOT parallelize 15d and 15e (shared arbitration
contract). Nothing goes live before 14 and 19's parity gate.

---

## v2.x build record (COMPLETE 2026-08-22/23 — retained for reference)

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

- [ ] 3a. FeatureEngine part 1 — HIRO lines & run machine
    - ARTIFACT-ROT GUARD (do this FIRST): re-run the research pipeline, pin the sha256 of
      `verification_trades_v1.csv`; rule: the port must MATCH the artifact — any genuine bug found while
      porting is logged as a spec/artifact issue, never silently fixed
    - HIRO lines L/Lc/Lp/N from the normalized CSV minutes (R3.1); rolling r5/r15/r30/r15n
    - Trough-anchored run machine (R3.2): port from `hiro_setup_dashboard.detect()` VERBATIM, then make
      the dashboard import it from here (delete the copy — DRY ledger)
    - Tests: hand-built fixtures for trough/break/re-anchor; run values on one stored day == dashboard parquet
    Requirements: R3.1, R3.2

- [ ] 3b. FeatureEngine part 2 — price, VWAP, context, episodes
    - Price windows (R3.3) incl. strict 30-bar min_periods; range60_pct via startup replay of stored
      HIRO-era sessions (log `warmup` below 300 obs)
    - EMA5/9/20, SPY VWAP (cumulative from 09:30), context read at 10:30/13:00 only (R3.4), retained fields
    - Per-branch episode tracker (R3.5)
    - Ownership note (junior): FeatureEngine computes ONLY market-derived fields. `vetoes` and `health` on
      FeatureRow are immutable inputs attached by Session (task 5b) — FeatureEngine never populates them
    - Tests: VWAP against a hand-computed day; context fixtures (UP/DOWN/CHOP days); warmup path
    Requirements: R3.3–R3.5

- [ ] 4. RuleEngine (all judgment lives here; nothing else decides anything)
    - R4 vetoes as pure checks producing VetoChange events on transitions
    - R6 entries: Branch A (R6.1), Branch B arm+gates (R6.2), late suppression (R6.3), limits (R6.4),
      serial pricing note (R6.5), A-beats-B tie (emit PendingEntry)
    - R7 exits incl. full precedence (R7.0 order) emitting ExitDecision; state-flip side mapping (R7.4)
    - Tests: table-driven — one fixture bar per rule; every pair of simultaneous exits (higher wins);
      entry blocked by each veto; one-entry-per-episode
    Requirements: R4, R5, R6, R7

- [ ] 4b. InstrumentSelector (owns R1.1–R1.3 — previously orphaned)
    - Expiry selection: listed expiry nearest 30 DTE within 20–40 (tie → shorter)
    - Strike selection: put closest to −0.20 delta (tie → lower strike); 5-wide partner strike
    - Sizing: hard-coded 1 contract, paper (R1.3)
    - No-chain fallback: emit "nearest −0.20Δ" hint text (R1.2)
    - Tests: expiry picker across month boundaries; delta tie-break; width always 5 strike points; size fixed
    Requirements: R1.1–R1.3

- [ ] 5. Executor + EventLog (state and prices, no judgment)
    - `execute_pending()` at bar open (S0 = that open, R1.4); `apply()` prices exits per R7.0
    - SimTrade with every field from design.md; all fields persisted in ENTRY/EXIT events
    - Event schema v1 (explicit columns, no catch-all) — MUST include every SimTrade field (incl.
      resting_limit_ref, target, bh_level, entry_L, cap_value, cap_source, state, resolution_debit);
      test: serialize ENTRY+EXIT for a fixture trade, replay, assert SimTrade == original field-for-field
    - ONE formatter → console line == CSV row
    - Crash-resume: on start, replay today's CSV to rebuild EngineState; kill/restart test must
      reconstruct the open SimTrade field-for-field
    - RuleEngine owns ALL event generation incl. `skip` (with reason), armed-episode gate failures, and
      periodic state lines; test matrix: one formatter/schema test per R8.1 event type and reason
    - Tests: property (≤1 open trade; ≤3 entries/day; PendingEntry executes exactly once at next open);
      console/CSV identity per event type; round-trip resume
    Requirements: R1.4, R7.0, R8.1, non-functional (crash recovery)

- [ ] 5b. Session (the orchestrator — the per-bar contract lives here, nowhere else)
    - Lifecycle: startup (config, loaders, banner) → per bar: (1) executor.execute_pending at open,
      (2) features.update, (3) Session attaches vetoes/health to the row, (4) rules.evaluate at close,
      (5) executor.apply, (6) log.emit → end-of-session (disposition SessionRow)
    - Health transitions (moved here from task 7's scope creep): the state machine shell, fed by feed
      exceptions; task 7 supplies only the live feed that raises them
    - Tests: ordering test (a scripted day asserts the exact call sequence and that entries execute at the
      bar AFTER their signal); disposition written exactly once
    Requirements: design "Main loop", R10 shell, non-functional

- [ ] 6. Backtest CLI + THE verification milestone
    - TierPolicy objects (`full`, `price`) defined HERE (moved up from task 9) and threaded through
      ReplayFeed/features/rules; task 2's ReplayFeed refactored to consume TierPolicy instead of a flag
    - `cli.py backtest --from --to [--day --verbose] [--tier] [--config]`
    - Determinism test: same day twice → byte-identical streams
    - **GOLDEN GATE (runs under TierPolicy `full`): frozen-config backtest over the 8 stored sessions reproduces
      `docs/replay/hiro/verification_trades_v1.csv` row-for-row (R12.1). Do not proceed past this task
      until it passes — every later task builds on trusted rule code.**
    - `--day 2026-08-18 --verbose` manually checked against the entry carousel
    Requirements: R12, backtest ACs (modes & lifecycle)

- [ ] 7. Live plumbing + degraded mode
    - SPIKE FIRST (half-day, schedule risk lives here): poll the HIRO payload once a minute via CDP for a
      full session; measure latency + failure rate. The pull has only ever run as a daily batch — if minutely
      polling doesn't hold, STOP and revisit the design before building anything on top
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

- [ ] 9. Sweep + summarizer (TierPolicy already exists from task 6; this task adds price-tier TESTS + tools)
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
    - READINESS GATE (deterministic, market-independent): all tests green, golden gates pass, crash-resume
      demo, runbook reviewed — this gate completes task 10
    Requirements: spec acceptance (readiness), R5 boundaries, non-functional

- [ ] 11. Daily operations (BEFORE shakedown — the live sessions depend on these)
    - Morning script: HIRO backfill freshness check, SPX 1-min refresh, levels CSV date check —
      one command, green/red output, referenced from the RUNBOOK
    - Evening script: append session logs, verify partition + manifest hashes, flag partial captures
    - RUNBOOK entries for both
    Requirements: R2 [OPS] items, R10.3 inputs

- [ ] 12. Shakedown (operational acceptance — market-dependent, after tasks 10 AND 11)
    - Run the two live `--shakedown` sessions; pass = no crash, no unexplained console/log divergence,
      dispositions written, ops scripts green both days; fix only defects, never thresholds
    Requirements: spec acceptance (shakedown)

Estimated shape (CTO-adjusted): tasks 1–6 (incl. 3a/3b, 4b, 5b) ≈ 60% of real effort (the '80% done' trap lives here); task 7's
spike is the schedule risk — run it the first morning of task 7; 8–9 offline analytics; 10–11 verification and
ops. Do NOT parallelize tasks 4 and 5 (shared state contract). Nothing ships until task 6's golden gate passes.

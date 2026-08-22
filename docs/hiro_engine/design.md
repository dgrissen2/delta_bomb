# Design — hiro_engine

*Architect design v1.1 for `requirements.md` v2.2 (v1.0 reviewed via codex-plan-review: FAIL, 5 blockers + 4 majors — all applied; review: `design_review_2026-08-22.md`). Principles: DRY (one rule module, one event stream, reuse the
reviewed research code), simple and interpretable (a trader can read the engine loop top to bottom), robust
(crash-resume, fail-closed on bad data). Deliberately not built: plugins, async frameworks, databases, GUIs.*

## Overview

One Python package, one process, one loop. The same `rules.py` runs live and in backtest; the only thing that
changes is which `Feed` supplies bars and which `Clock` supplies time. Console lines and CSV rows are the same
event objects, formatted twice.

## Architecture

    CLI (live | backtest | sweep | scorecard)
       ↓
    Session
       ↓
    Feed (LiveFeed | ReplayFeed)          ← SPX bars, HIRO payload, levels, SPY, [chain]
       ↓  one completed 1-min bar at a time
    FeatureEngine (R3)                    ← pure functions, no I/O
       ↓  FeatureRow
    RuleEngine (R4–R7)                    ← pure: (FeatureRow, EngineState) → [Event]
       ↓  Events
    Executor                              ← applies entry/exit Events to the one open SimTrade
       ↓
    EventLog                              ← single stream → console + paper_log.csv
    
    Scorecard (R9/R11) and SweepRunner (R13) are offline readers of paper_log.csv / ReplayFeed.

## Components

    cli.py
        argparse; subcommands live / backtest / sweep / scorecard; loads Config; builds Session.

    config.py
        Config: every R1–R7 numeric + control-dataset id + verification-artifact hash (R8.2).
        Loaded from config.yaml; sha256() = CONFIG_HASH. Frozen file checked into the repo.

    feeds.py
        Feed protocol: next_bar() -> Bar | None, spy_bar(), hiro_snapshot(), chain() (live only).
        LiveFeed: ThetaData SPX bars; CDP HIRO pull; Schwab chain; SPY via ThetaData. Retries once, then
        raises FeedDown(scope) — Session's health machine handles it (below).
        ReplayFeed: stored parquets/CSVs; refuses missing required sources per R13.1 (listing dates).
        levels.py / calendar.py: LevelsLoader (validates date + CW−VT>0, fail-closed) and CalendarLoader
        (R2.4 list, checked at session start). range60_pct history: initialized at startup by replaying the
        stored HIRO-era SPX sessions (2026-08-12 →) through the same FeatureEngine — one code path, causal.

    features.py
        FeatureEngine (R3): consumes Bars + HIRO snapshots, maintains L/Lc/Lp/N series, the trough-anchored
        run state machine (R3.2 — ported once from hiro_setup_dashboard.detect(), which is then retired),
        price windows (R3.3), context read (R3.4), episode tracker (R3.5). Emits an immutable FeatureRow
        per bar. Pure computation; unit-testable from fixture frames.

    rules.py
        RuleEngine — the ONLY owner of ALL condition logic: R4 vetoes, R6 entries, and R7 exits including
        their precedence. evaluate(row, state) returns Events (VetoChange, Signal, PendingEntry, ExitDecision,
        StateLine). Pure: no I/O, no clock access. Shared verbatim by live and backtest.

    executor.py
        Executor — a pure STATE APPLIER, no trading judgment. Order per bar: (1) if a PendingEntry exists,
        execute it at THIS bar's open (that open = S0) and emit the ENTRY event; (2) hand the bar's
        ExitDecision (if any) its execution price per R7.0; (3) update EngineState (open SimTrade | None,
        PendingEntry | None, entries_today, per-branch episode ids). One owner per rule: conditions in
        rules.py, state/prices in executor.py, never both.

    eventlog.py
        Event dataclass → one formatter for console, one CSV writer; same fields (R8.1). Append-only.
        On startup with an existing file for today: replay it to rebuild EngineState (crash-resume).

    scorecard.py
        A staged pipeline with an inspectable intermediate record per stage (each stage writes its frame):
        1 filter    rows by mode=live, disposition=countable, single config_hash (mixed → refuse)
        2 entries   build the entries table (one row per executable entry; SimTrade fields from events)
        3 qualify   per R11.1: qualifying signals/episodes incl. blocked ones; A∧B same-minute → A only
        4 metrics   fills, fill rates (R11.6, censored excluded), adverse (R11.2), scratch loss (R11.3)
        5 controls  control.py functions over the frozen dataset, weighted to stage-2 clock distributions
        6 criteria  the R9 table, one row per criterion, incl. the best-session re-check (ties per R9)
        `--rehearsal` runs the same pipeline over backtest rows, output labeled REHEARSAL.

    summarize.py
        ONE summarizer shared by backtest and sweep (R13.3): trade+episode counts, days, own-dataset
        controls (R11.4/R11.5 form), day-clustered bootstrap CI (resample days with replacement,
        2,000 draws, numpy default_rng(42)), censored separate; leaderboard formatting per R13.4.

    control.py
        clock_matched() and midpoint_matched() (R11.4/R11.5): ported once from the reviewed logic in
        hiro_uptrend_confirm.py / hiro_experiments.py (exq(), cm_base()); those scripts then import from
        here — one implementation, research and engine agree by construction.

    sweep.py
        SweepRunner: whitelist dict {knob: [values]} literally from R13.2; runs ReplayFeed sessions per
        value; emits R13.3 summary + R13.4 leaderboard. Rejects unknown knobs by looking up the dict.

## Data model

    Bar          { ts, open, high, low, close }                  # SPX
    SpyBar       { ts, open, high, low, close, volume }          # for VWAP (R2.6)
    Levels       { date, vt, cw, sg_index, im, valid }           # LevelsLoader (R2.3), fail-closed
    Calendar     { date, is_event_day, reason }                  # CalendarLoader (R2.4)
    FeatureRow   { ts, bar, open_0930, L, Lc, Lp, N, r5, r15, r30, r15n,
                   run, dur, rate, dC, dP, dN, weak_side, share, drawdown,
                   pull30, bounce30, mid30, ref_low_bar, range60, range60_pct, warmup,
                   ema5, ema9, ema20, vwap, context_1030, context_1300,
                   vetoes {vt_broken, levels_invalid, flow_veto}, health (OK|HIRO_DOWN|SPX_STALLED|DEGRADED_VWAP) }
    PendingEntry { branch, side, signal_ts, expiry, strike_hint, chain_quote_ts | None }
    SimTrade     { id, branch, side, signal_ts, entry_ts, s0, expiry, leg_strikes,
                   entry_option_mid | None, resting_limit_ref, target,
                   bh_level (Branch A), entry_L (Branch B), cap_source (chain|proxy), cap_value,
                   state, exit_type, exit_ref, resolution_debit | None, minutes, adverse }
                   # every field persisted in the ENTRY/EXIT events → crash round-trip is lossless
    Event        explicit versioned columns, schema_v=1 — no catch-all field:
                 { ts, mode (live|backtest|shakedown), tier, session_date, config_hash, schema_v,
                   event_type, rule_id, branch, side, s0, expiry, leg_strikes, strike_quote_ts,
                   run, rate, dC, dP, share, r15, pull30, bounce30, context, health,
                   outcome_type, outcome_minutes, exit_ref, cap_source, resolution_debit,
                   adverse, notes }                              # == one CSV row == one console line
    SessionRow   { date, disposition (countable|shakedown|partial|event_standdown), outage_min }
    Config       { R1..R7 numerics, control_dataset {path, data_hash}, verification_hash }
    TierPolicy   immutable per run (R13.1): { branch_b_enabled, price_a_conditions, r43_enabled,
                 r72_enabled, tier_stamp } — consumed by FeatureEngine and RuleEngine; `full` and `price`
                 are the only two instances, defined next to the whitelist, tested individually.

## Reuse (DRY ledger)

    run state machine      hiro_setup_dashboard.detect()  → features.py (single home; dashboard imports it)
    controls + exq         hiro_uptrend_confirm / hiro_experiments → control.py (single home)
    HIRO payload pull      HIRO_finder historical_backfill session code → feeds.LiveFeed (imported, not copied)
    verification target    docs/replay/hiro/verification_trades_v1.csv (pinned, hash in Config)
    New code is: feeds glue, executor, eventlog, cli, scorecard assembly. No new analytics.

## Main loop (the whole engine, interpretable)

    for bar in feed:
        state, entry_events = executor.execute_pending(bar, state)   # PendingEntry fills at THIS open (S0)
        row    = features.update(bar, feed.hiro_snapshot(), feed.spy_bar())
        events = rules.evaluate(row, state)          # R4 → R6 (may emit PendingEntry) → R7 (ExitDecision)
        state, trade_events = executor.apply(events, row, state)     # exit prices per R7.0
        log.emit(entry_events + events + trade_events)

## Error handling

    Session health state machine: OK → HIRO_DOWN / SPX_STALLED → OK, with cumulative outage minutes.
      HIRO_DOWN (R10.1): no new entries; open trade keeps R7.3/R7.5/R7.6; R7.2/R7.4 flow exits log
        `scratch_unavailable`; `HIRO RESTORED <span>` on recovery.
      SPX_STALLED (R10.2): with no bars nothing evaluates; on the first bar after a stall, time-based exits
        (clock, resolution) fire per R7.0 using that bar; stall span added to outage minutes.
      DEGRADED_VWAP: SPY missing → R3.4 returns CHOP, logged once per transition.
      End of session: disposition computed (countable | partial per R10.3 | shakedown | event_standdown)
        and written as the SessionRow — the scorecard consumes dispositions, never re-derives them.
    Bad levels row:    fail closed → R4.2 long-first-only; loud banner.
    Chain call fails:  fall back to spot proxies (R2.5) and log which path was used.
    Crash mid-session: restart replays today's log; open SimTrade rebuilt from its entry row (spec NFR).
    Hash mismatch:     loud reset warning (R8.2); scorecard refuses mixed hashes (R9).

## Testing strategy

    Property:     replaying any day twice yields byte-identical event streams (determinism).
    Property:     at most one open SimTrade; entries_today ≤ 3; PendingEntry always executes exactly once,
                  at the bar after its signal, with S0 == that bar's open (R1.4 timing).
    Golden:       full-tier backtest over the 8 sessions == verification_trades_v1.csv row-for-row (R12.1).
    Golden:       control.py values on the 8 sessions == the research scripts' published numbers.
    Golden:       scorecard over a synthetic 10-session fixture log == a hand-computed R9 table
                  (covers qualifying vs executable, censored denominators, A-over-B dedupe,
                  best-session re-check with each tie-break exercised).
    Table-driven: R7 precedence — every pair of simultaneously-firing exits; boundary bars (14:30 entry,
                  15:30 resolution vs 60-min clock, session-end censoring, first bar after an SPX stall).
    Table-driven: TierPolicy — the same fixture day under `full` vs `price` produces the enumerated
                  R13.1 differences and correct tier stamps.
    Unit:         features.py run machine (trough, break, re-anchor); EMA/VWAP/context reads at 10:30/13:00;
                  range60_pct warmup behavior below 300 observations.
    Unit:         chain-present vs proxy paths for cap and resolution (cap_source recorded correctly).
    Integration:  HIRO outage mid-trade → scratch_unavailable + PARTIAL; levels invalid → R4.2 banner.
    Integration:  crash-resume — kill after entry, restart, SimTrade reconstructed field-for-field from
                  events (lossless round-trip), exits still fire on schedule.
    Integration:  console line == CSV row for every event type (one formatter test per type).
    Manual:       backtest --day 2026-08-18 --verbose vs the entry carousel, bar by bar.

## Explicitly not built

    No database (CSV + parquet suffice at 391 rows/day). No async/websockets (1-min cadence; sequential
    pulls fit in the 5-s budget). No plugin system, no strategy abstraction beyond the two branches the
    spec names. No dashboard (console is the contract). No live order routing of any kind.

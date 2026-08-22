# Design — hiro_engine

*Architect design for `requirements.md` v2.2. Principles: DRY (one rule module, one event stream, reuse the
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
        Feed protocol: next_bar() -> Bar | None, plus levels(), spy_bar(), hiro_snapshot(), chain() (live only).
        LiveFeed: ThetaData SPX bars; CDP HIRO pull; Schwab chain; SPY via ThetaData. Retries once, then
        raises FeedDown(scope) — Session turns that into R10 degraded mode.
        ReplayFeed: reads the stored parquets/CSVs; --tier selects sources; raises on missing per R13.1.

    features.py
        FeatureEngine (R3): consumes Bars + HIRO snapshots, maintains L/Lc/Lp/N series, the trough-anchored
        run state machine (R3.2 — ported once from hiro_setup_dashboard.detect(), which is then retired),
        price windows (R3.3), context read (R3.4), episode tracker (R3.5). Emits an immutable FeatureRow
        per bar. Pure computation; unit-testable from fixture frames.

    rules.py
        RuleEngine (R4–R7): the ONLY place trading logic lives. evaluate(row, state) returns Events
        (VetoChange, Signal, EntryOrder, ExitOrder, StateLine). No I/O, no clock access — time comes in on
        the row. Shared verbatim by live and backtest (spec non-functional requirement).

    executor.py
        Executor: holds EngineState (open SimTrade | None, entries_today, episode ids). Applies EntryOrder
        at next bar's open (R1.4/R7.0), checks exits in R7 precedence each bar, emits Trade events.
        SimTrade dataclass below.

    eventlog.py
        Event dataclass → one formatter for console, one CSV writer; same fields (R8.1). Append-only.
        On startup with an existing file for today: replay it to rebuild EngineState (crash-resume).

    scorecard.py
        Reads paper_log.csv; filters mode/hash; computes R9 with R11 metrics; controls via control.py.

    control.py
        clock_matched() and midpoint_matched() (R11.4/R11.5): ported once from the reviewed logic in
        hiro_uptrend_confirm.py / hiro_experiments.py (exq(), cm_base()); those scripts then import from
        here — one implementation, research and engine agree by construction.

    sweep.py
        SweepRunner: whitelist dict {knob: [values]} literally from R13.2; runs ReplayFeed sessions per
        value; emits R13.3 summary + R13.4 leaderboard. Rejects unknown knobs by looking up the dict.

## Data model

    Bar        { ts, open, high, low, close }
    FeatureRow { ts, bar, L, Lc, Lp, N, r5, r15, r30, r15n, run, dur, rate, dC, dP, dN,
                 weak_side, share, drawdown, pull30, bounce30, mid30, range60, range60_pct,
                 context (UP|DOWN|CHOP|None), vetoes {vt_broken, levels_invalid, flow_veto},
                 warmup flags }
    Event      { ts, mode, tier, branch, event, rule_id, s0, strikes, features_subset,
                 outcome, adverse, config_hash, session_date }        # == one CSV row == one console line
    SimTrade   { id, branch, side, signal_ts, entry_ts, s0, target, bh_level, entry_L,
                 state, exit_type, exit_ref, minutes, adverse }
    Config     { R1..R7 numerics, control_dataset {path, data_hash}, verification_hash }

## Reuse (DRY ledger)

    run state machine      hiro_setup_dashboard.detect()  → features.py (single home; dashboard imports it)
    controls + exq         hiro_uptrend_confirm / hiro_experiments → control.py (single home)
    HIRO payload pull      HIRO_finder historical_backfill session code → feeds.LiveFeed (imported, not copied)
    verification target    docs/replay/hiro/verification_trades_v1.csv (pinned, hash in Config)
    New code is: feeds glue, executor, eventlog, cli, scorecard assembly. No new analytics.

## Main loop (the whole engine, interpretable)

    for bar in feed:
        row    = features.update(bar, feed.hiro_snapshot(), feed.spy_bar())
        events = rules.evaluate(row, state)          # R4 → R6 → (R7 for the open trade)
        state  = executor.apply(events, row, state)  # entries at next open; exits per R7.0
        log.emit(events + executor.trade_events)

## Error handling

    FeedDown(hiro):    R10.1 — no entries; open trade keeps R7.3/R7.5/R7.6; scratch → `scratch_unavailable`.
    FeedDown(spx):     R10.2 — same shape.
    Outage > 15 min:   session flagged PARTIAL (R10.3) in every subsequent row.
    Bad levels row:    fail closed → R4.2 long-first-only; loud banner.
    Chain call fails:  fall back to spot proxies (R2.5) and log which path was used.
    Crash mid-session: restart replays today's log; open SimTrade rebuilt from its entry row (spec NFR).
    Hash mismatch:     loud reset warning (R8.2); scorecard refuses mixed hashes (R9).

## Testing strategy

    Property:     replaying any day twice yields byte-identical event streams (determinism).
    Property:     at most one open SimTrade at any bar; entries_today never exceeds 3 (R6.4).
    Golden:       full-tier backtest over the 8 sessions == verification_trades_v1.csv row-for-row (R12.1).
    Golden:       control.py values on the 8 sessions == the research scripts' published numbers.
    Unit:         features.py run machine against hand-built HIRO fixtures (trough, break, re-anchor).
    Unit:         R7 precedence — one fixture bar where multiple exits fire; only the highest wins.
    Integration:  simulated HIRO outage mid-trade → scratch_unavailable path + PARTIAL flag.
    Integration:  crash-resume — kill after entry, restart, exits still fire on schedule.
    Manual:       backtest --day 2026-08-18 --verbose vs the entry carousel, bar by bar.

## Explicitly not built

    No database (CSV + parquet suffice at 391 rows/day). No async/websockets (1-min cadence; sequential
    pulls fit in the 5-s budget). No plugin system, no strategy abstraction beyond the two branches the
    spec names. No dashboard (console is the contract). No live order routing of any kind.

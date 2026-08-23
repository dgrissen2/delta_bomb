# Design — hiro_engine

*Architect design v2.0 for `requirements.md` v3.0 (real resting-limit fills). v3.0 additions: ONE new
data module (ChainStore), quotes attached by Session like vetoes/health, RuleEngine keeps sole ownership
of R7 arbitration with a `limit_filled` input, Executor books conservative NBBO and carries the
resting-limit state, R10.4 quote-health states, $-metrics scorecard, derived control frame, five new
CONFIG pins. The signal path (features, entry rules, vetoes) is UNTOUCHED. Prior: v1.1 for v2.2
(codex-plan-review FAIL 5B+4M applied; `design_review_2026-08-22.md`). Principles: DRY (one rule module, one event stream, reuse the
reviewed research code), simple and interpretable (a trader can read the engine loop top to bottom), robust
(crash-resume, fail-closed on bad data). Deliberately not built: plugins, async frameworks, databases, GUIs.*

## Overview

One Python package, one process, one loop. The same `rules.py` runs live and in backtest; the only thing that
changes is which `Feed` supplies bars and which `Clock` supplies time. Console lines and CSV rows are the same
event objects, formatted twice.

## Architecture

    CLI (live | backtest | sweep | scorecard | verify | controls_build)
       ↓
    Session
       ↓
    Feed (LiveFeed | ReplayFeed)          ← SPX bars, HIRO payload, levels, SPY
    ChainStore                            ← SPXW 1-min NBBO+greeks (cache | live snapshots), R2.5
       ↓  one completed 1-min bar at a time (Session attaches the bar's QuoteView)
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

    chains.py  (NEW, v3.0 — the ONLY module that touches option endpoints)
        ChainStore: per-session full-chain full-day 1-min NBBO+greeks cache (one SDK pull/day).
        PIN SCOPING (R8.2): CONFIG pins the FROZEN REHEARSAL set only — the 8 control sessions'
        cache manifest + the ControlFrame + the SDK version. Live sessions' chain data is NOT
        CONFIG-pinned (pinning a rolling cache would reset the test daily); the live record's
        authority is the event log + the per-session snapshot sidecar. CROSS-LINK: the ControlFrame
        manifest records its source-cache manifest sha; scorecard verifies frame.source_sha ==
        the pinned cache sha, so a re-fetched cache with a stale frame can never pass silently.
        signal_snapshot(min) for the R1.2
        strike pick; strike_series(strike) for fills/exits; live: minute snapshots (SDK or Schwab —
        whichever the spike proves). QuoteView = the two working strikes' VALID quotes for ONE minute
        (R10.4 validity; quote_age=0 for decisions), attached to the tick by Session.
        signal_snapshot(t): on a bar where RuleEngine emitted a PendingEntry, Session fetches the
        SIGNAL-minute full-chain snapshot and calls InstrumentSelector (pure: expiry nearest-30,
        −0.20Δ pick, partner-listed constraint, lower-strike tie-break, R1.2) to resolve
        {expiry, K, K2} INTO the PendingEntry before the next bar; snapshot missing/invalid →
        the pending entry is dropped and `entry_aborted_no_quote` logged (R10.4). controls_build:
        offline job → derived control frame (R11.4/R11.5 limit-fill indicators), parquet + sha256
        pinned in CONFIG. No other module imports the OPTION-CHAIN client (feeds.py keeps its
        SPX/SPY/HIRO sources; options are exclusively ChainStore's).

    feeds.py
        Feed protocol: next_bar() -> Bar | None, spy_bar(), hiro_snapshot(). NO chain access here —
        every option quote (historical cache, live snapshots, Schwab fallback) lives behind
        ChainStore in chains.py, the SINGLE owner of option endpoints.
        LiveFeed: ThetaData SPX bars (SDK); CDP HIRO pull; SPY via SDK. Retries once, then raises
        FeedDown(scope) — Session's health machine handles it (below).
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
        RuleEngine — the ONLY owner of ALL condition logic AND the single R7 arbitration point (v3.0):
        R4 vetoes, R6 entries, R7 exits. `limit_filled` is computed from the row's attached QuoteView
        (ask ≤ L / bid ≥ L, first eligible minute t+2) INSIDE evaluate(), so fill > scratch > cap > … is
        decided in one place; a winning non-fill exit also emits `limit_canceled` (R7.0). Emits
        Fill | ExitDecision | LimitCancel | Signal | PendingEntry | VetoChange | StateLine.
        Pure: no I/O, no clock access. Shared verbatim by live and backtest.

    executor.py
        Executor — a pure, I/O-FREE state applier (quotes arrive on the row; fixture quotes make it
        table-testable). Per bar: (1) a PendingEntry books leg 1 at THIS bar's closing NBBO conservative
        side (R1.4b; entry aborted per R10.4 if either working strike lacks a valid quote) and creates
        the RestingLimit (L tick-rounded against us, R1.4c); (2) applies the RuleEngine's decision:
        Fill → book leg 2 at L (+0.10 credit invariant), LimitCancel(+ExitDecision) → cancel, then book
        the lone leg at close-of-NEXT-bar NBBO per R7.0 (pending-exit mechanism unchanged); (3) updates
        EngineState. Executor performs NO cancellation judgment: Session counts the quote_gap streak
        (health, like vetoes) and attaches it to the row; RULEENGINE — the single arbiter — emits the
        5th-gap `limit_canceled(reason=quote_gap)`. `data_invalid` is a PROPERTY (the open horizon
        contained a ≥5-min gap), stamped on whatever exit eventually books — so a simultaneous 5th gap +
        clock expiry is one arbitration: clock exit wins the booking, the cancel event rides with it,
        the outcome carries data_invalid. S0 stays the SPX context anchor only. One owner per concern:
        conditions+arbitration in rules.py, streak counting in session.py, state+booking in executor.py.

    eventlog.py
        Event dataclass → one formatter for console, one CSV writer; same fields (R8.1, schema_v=2
        additive). Append-only. rebuild_state handles the v3 event types (fill, limit_canceled,
        quote_gap, entry_aborted_no_quote) with explicit columns — no notes-string parsing.
        CRASH-RESUME DETERMINISM (v3.0): live quote snapshots are decision inputs, so live resume
        NEVER re-decides the past — (a) the per-minute snapshot sidecar (live_quotes_<date>.parquet,
        written for the parity gate anyway) is the quote source for warm replay; (b) LOGGED decisions
        are AUTHORITATIVE: while replaying bars ≤ the last logged bar, fill/cancel/exit outcomes are
        taken from the log, never recomputed — recomputation is only a cross-check, and any
        divergence prints the RESUME WARNING (now including fill-state and limit-price drift, not
        just trade identity). Backtest resume needs none of this (historical quotes are the record).

    scorecard.py
        v3.0: $-metrics per R11.3 (points × 100, realized loss, +$10 per fill; spread value reported
        never scored); data_invalid trades stay in entry-count criteria, leave fills/rates/risk (R9);
        would-have-filled = pure limit replay, INDETERMINATE on ≥5-min gaps (excluded+reported);
        controls read the PINNED derived control frame only. Staged pipeline as before (each stage
        writes its frame):
        1 filter    rows by mode=live, disposition=countable, single config_hash (mixed → refuse)
        2 entries   build the entries table (one row per executable entry; SimTrade fields from events)
        3 qualify   per R11.1: qualifying signals/episodes incl. blocked ones; A∧B same-minute → A only
        4 metrics   fills, fill rates (R11.6, censored excluded), adverse (R11.2), scratch loss (R11.3)
        5 controls  control.py functions over the frozen dataset, weighted to stage-2 clock distributions
        6 criteria  the R9 table, one row per criterion, incl. the best-session re-check (ties per R9)
        `--rehearsal` runs the same pipeline over backtest rows, output labeled REHEARSAL.
        (Stage frames are kept deliberately: the BH-scratch forensics was conducted FROM these frames;
        auditability is a standing requirement, not speculation.)

    summarize.py
        ONE summarizer shared by backtest and sweep (R13.3): trade+episode counts, days, own-dataset
        controls (R11.4/R11.5 form), day-clustered bootstrap CI (resample days with replacement,
        2,000 draws, numpy default_rng(42)), censored + data_invalid separate; leaderboard per R13.4.
        UNITS follow TierPolicy.fill_mode: limit → $ columns (R11.3); spot_touch → SPX-point columns
        with the $ columns suppressed (never mixed, never NaN-crashed).

    control.py
        clock_matched() and midpoint_matched() (R11.4/R11.5): the WEIGHTING math is unchanged (single
        home, research scripts import it); the indicator is v3.0 limit-fill, read from the pinned
        derived control frame built by chains.controls_build (no scorecard-time chain crunching).

    register.py  (NEW, v3.0 — owns R9a)
        `cli register-thresholds`: runs the FROZEN R9a derivation (one bootstrap procedure, count
        floors, fill-rate floors, $-risk caps, empty-resample rule) over the first v3 rehearsal log;
        writes registration.json (inputs, formulas, outputs) whose sha256 goes into CONFIG; populates
        the «16b» markers (spec + config edit emitted as a printed patch for the operator to apply).
        Run-once boundary: refuses to run if a registration hash is already pinned.

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
    QuoteSnap    { strike, bid, ask, valid }                     # one strike, one minute (R10.4 validity)
    QuoteView    { minute, leg1: QuoteSnap|None, leg2: QuoteSnap|None }   # attached by Session per bar
    RestingLimit { side (buy|sell), strike, price L, placed_min, first_eligible_min (t+2),
                   status (resting|filled|canceled), cancel_reason | None }
    PendingEntry { branch, side, signal_ts, expiry, K, K2, chain_quote_ts }   # strikes now real (R1.2)
    SimTrade     { id, branch, side, signal_ts, entry_ts, s0, expiry, leg_strikes,
                   leg1_fill, limit: RestingLimit, leg2_fill | None, credit | None,
                   entry_L (Branch B), cap_source (chain|proxy), cap_value,
                   quote_gap_streak, data_invalid: bool,
                   state, exit_type, exit_ref ($ booking), minutes,
                   spx_adverse_pts, leg_liq_loss_usd }         # schema_v=2, ADDITIVE (readers accept v1)
    Event v2     adds explicit columns (ALL v1 columns retained — signal_min, entry_min, s0, entry_L,
                 episode etc. already exist in v1 and keep carrying SimTrade identity; resolution_debit
                 kept for v1 parsing, legacy-always-None): expiry, K, K2, leg1_fill, limit_price,
                 limit_status, limit_cancel_reason, first_eligible_min, leg2_fill, credit, quote_age,
                 quote_gap_streak, last_valid_bid, last_valid_ask, last_valid_quote_min,
                 data_invalid, leg_liq_loss_usd, spx_adverse_pts.
                 EVERY quote_gap event row carries quote_gap_streak + last_valid_* (not only
                 heartbeats), so the resume anchor is the LATEST of (entry, heartbeat, quote_gap,
                 limit event) rows — minute-accurate, no between-heartbeat blind spot; round-trip
                 test: SimTrade ⊕ RestingLimit reconstructed field-for-field from ENTRY + limit +
                 latest quote_gap/heartbeat + EXIT rows.
                   # every field persisted in the ENTRY/EXIT events → crash round-trip is lossless
    Event        explicit versioned columns, schema_v=2 — no catch-all field. The full v1 column set
                 (as implemented in models.EVENT_FIELDS) is retained verbatim:
                 { ts, mode (live|backtest|shakedown), tier, session_date, config_hash, schema_v,
                   event_type, rule_id, branch, side, s0, expiry, leg_strikes, strike_quote_ts,
                   run, rate, dC, dP, share, r15, pull30, bounce30, context, health,
                   outcome_type, outcome_minutes, exit_ref, cap_source, resolution_debit (legacy,
                   always None), adverse, trade_id, entry_min, signal_min, entry_option_mid,
                   resting_limit_ref, target, bh_level, entry_L, cap_value, episode, notes }
                 plus the v2 additions listed under "Event v2" above.
                 # == one CSV row == one console line; readers accept v1 rows
    SessionRow   { date, disposition (countable|shakedown|partial|event_standdown), outage_min }
    Config       { R1..R7 numerics, control_dataset {path, data_hash}, verification_hash }
    TierPolicy   immutable per run (R13.1): { branch_b_enabled, price_a_conditions, r43_enabled,
                 r72_enabled, requires_hiro, fill_mode (limit|spot_touch), tier_stamp } — `full`
                 (fill_mode=limit) and `price` (fill_mode=spot_touch, the only surviving touch use)
                 are the only two instances, tested individually.
    ChainDay     cached parquet per session: full-chain 1-min NBBO+greeks; manifest {sha256, sdk_version}
    ControlFrame derived parquet (controls_build): per candidate minute — eligibility, limit-fill
                 indicator, exclusion reason; manifest sha256 pinned in CONFIG

## Reuse (DRY ledger)

    run state machine      hiro_setup_dashboard.detect()  → features.py (single home; dashboard imports it)
    controls + exq         hiro_uptrend_confirm / hiro_experiments → control.py (single home)
    HIRO payload pull      HIRO_finder historical_backfill session code → feeds.LiveFeed (imported, not copied)
    verification target    docs/replay/hiro/verification_trades_v1.csv (pinned, hash in Config)
    New code is: feeds glue, executor, eventlog, cli, scorecard assembly. No new analytics.

## Main loop (the whole engine, interpretable)

    for bar in feed:
        quotes = chains.quote_view(bar.min, state)                   # two working strikes, THIS minute
        state, entry_events = executor.execute_pending(bar, quotes, state)  # leg 1 books at closing
                                                                     # NBBO; RestingLimit created (R1.4b/c)
        row    = features.update(bar, feed.hiro_snapshot(), feed.spy_bar())
        row    = row + vetoes/health/QuoteView/quote_gap_streak      # Session attaches (streaks counted HERE)
        events = rules.evaluate(row, state)          # R4 → R6 → R7 single arbitration incl. limit_filled
                                                     # and the 5th-gap limit cancel
        if pending_entry in events:                                  # fresh signal this bar:
            events = session.resolve_instruments(events)             # chains.signal_snapshot(t) +
                                                                     # InstrumentSelector → {expiry,K,K2}
                                                                     # into PendingEntry (+ SIGNAL line's
                                                                     # strike text); snapshot missing →
                                                                     # entry_aborted_no_quote instead
        state, trade_events = executor.apply(events, row, state)     # bookings per R7.0 ONLY (no judgment)
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
    Option quotes (R10.4): entry bar without both valid working-strike quotes → entry ABORTED (event).
      quote_gap minutes → no fill decision; 5th consecutive while open → limit canceled, outcome
      data_invalid, guards (cap-spot/clock/resolution) keep running, one-leg + 3/day slots stay occupied.
      Exit booking: last valid NBBO ≤ 3 min old, else administrative close at last valid NBBO + unscored.
      Live quote loss → stand down from NEW entries (banner); NEVER an SPX-based fill in any mode.
    Bad levels row:    fail closed → R4.2 long-first-only; loud banner.
    Chain failures are FOUR distinct policies (R1.2/R10.4 — never blended):
      signal-minute snapshot missing → pending entry dropped, `entry_aborted_no_quote`;
      entry-bar working-strike quotes invalid → entry aborted (same event);
      resting-strike quote missing/invalid → `quote_gap` minute (5th consecutive → cancel per rules);
      cap-evaluation quote missing → R7.3 SPX spot proxy FOR THE CAP ONLY (`cap_source=proxy`).
    Crash mid-session: restart replays today's log; open SimTrade rebuilt from its entry row (spec NFR).
    Hash mismatch:     loud reset warning (R8.2); scorecard refuses mixed hashes (R9).

## Testing strategy

    Property:     replaying any day twice yields byte-identical event streams (determinism).
    Property:     at most one open SimTrade; entries_today ≤ 3; PendingEntry always executes exactly once,
                  at the bar after its signal, with S0 == that bar's open (R1.4 timing).
    Golden:       R12.1 legacy gate — verify.py reproduces verification_trades_v1.csv through the
                  ported research core (unchanged; says nothing about v3 fills).
    Golden:       R12.2 HAND-COMPUTED quote fixture, written before the pricing layer: both sides,
                  tick rounding, t+2 first eligibility, same-minute fill-vs-scratch race (fill wins),
                  every cancel path, quote gaps → data_invalid, session-end booking.
    Golden:       R12.3 pinned v2 rehearsal artifact == full-tier v3 backtest, row-for-row, against the
                  pinned chain cache.
    Gate:         live/backtest parity diff (shakedown gate): in live mode chains.py persists a
                  snapshot artifact per session (live_quotes_<date>.parquet: minute, strike, bid, ask,
                  L, marketable?, decision) for EVERY evaluated minute incl. non-fills; `cli
                  parity-check <date>` fetches the historical series next day and diffs — 100%
                  fill-decision agreement, booked prices within 1 tick on ≥ 95% of minutes
                  (pre-registered tolerance). Report written next to the artifact.
    Golden:       control weighting math == hand-computed fixture; control-frame indicator values
                  pinned at first controls_build (v3 semantics — the old touch-based research numbers
                  are OBSOLETE for this comparison and are not a target).
    Golden:       scorecard over a synthetic 10-session fixture log == a hand-computed R9 table
                  (covers qualifying vs executable, censored denominators, A-over-B dedupe,
                  best-session re-check with each tie-break exercised).
    Table-driven: R7 precedence — every pair of simultaneously-firing exits; boundary bars (14:30 entry,
                  15:30 resolution vs 60-min clock, session-end censoring, first bar after an SPX stall).
    Table-driven: TierPolicy — the same fixture day under `full` vs `price` produces the enumerated
                  R13.1 differences and correct tier stamps.
    Unit:         features.py run machine (trough, break, re-anchor); EMA/VWAP/context reads at 10:30/13:00;
                  range60_pct warmup behavior below 300 observations.
    Unit:         cap chain-mid vs spot-proxy fallback paths (cap_source recorded; resolution has no
                  proxy path in v3 — resolution_close books per R7.0).
    Integration:  HIRO outage mid-trade → scratch_unavailable + PARTIAL; levels invalid → R4.2 banner.
    Integration:  crash-resume — kill after entry, restart, SimTrade reconstructed field-for-field from
                  events (lossless round-trip), exits still fire on schedule.
    Integration:  console line == CSV row for every event type (one formatter test per type).
    Manual:       backtest --day 2026-08-18 --verbose vs the entry carousel, bar by bar.

## v3.0 delta ledger (contract rewrites an implementer must NOT miss)

    session.py   per-bar contract docstring: step (1) becomes "book pending leg 1 at THIS bar's
                 closing NBBO"; new steps: attach QuoteView + quote_gap streak; resolve instruments
                 for fresh PendingEntries via chains.signal_snapshot + InstrumentSelector.
    executor.py  every booking moves from bar OPEN to closing NBBO per R7.0; the resolution_debit
                 branch and config key are DELETED; RestingLimit lifecycle added.
    rules.py     R7.1 fill check rewritten (limit marketability from the attached QuoteView, t+2
                 guard); 5th-gap cancel emitted here; heartbeat gains streak/last-valid fields.
    eventlog.py  schema_v=2 columns; rebuild_state learns the four new event types; resume
                 authority rules above.
    config.yaml  resolution_debit_max removed; adds: chain cache pin, SDK version, control-frame
                 pin, R9a registration hash, «16b» thresholds once registered.
    scorecard.py stage6 thresholds come FROM CONFIG (populated by register.py), never hardcoded.

## Explicitly not built

    No database (CSV + parquet suffice at 391 rows/day). No async/websockets (1-min cadence; sequential
    pulls fit in the 5-s budget). No plugin system, no strategy abstraction beyond the two branches the
    spec names. No dashboard (console is the contract). No live order routing of any kind.
    v3.0 additions to this list: no order-book queue modeling, no partial fills, no multi-lot, no
    intra-minute quote interpolation, no credit knob (0.10 frozen), no quote carry-forward for decisions.

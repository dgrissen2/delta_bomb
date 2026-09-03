# Implementation Tasks — hiro_watch

*Build spec v1.2 (2026-09-03) for `requirements.md` v1.2a and `design.md` v1.3 — v1.1 + CIO/architect plan review (governance gate split from build acceptance; contract fixes). Review closed. Written for a junior
engineer: every task says what to build, where, what "done" looks like, and what NOT to touch. Order
is dependency order; every task ends green (`pytest scripts/hiro_watch/tests`) before the next starts.
When this file and the requirements disagree, the requirements win; when this file and the design
disagree, the design wins. **DO NOT START without the user's explicit go. Never edit anything under
`scripts/hiro_engine/` — the engine is frozen; if you think you need to, stop and ask.***

## Ground rules (read twice)

1. **The engine is a library you import, not code you change.** `from hiro_engine.session import
   Session` etc. Task 10's test hashes every engine file and artifact before and after a full run —
   if that test ever fails, you changed something you must not.
2. **No DECISION numbers in code.** Every threshold, count, credit, window, seed, shock lives in
   the registration payload (task 2) and is read from it. The few STRUCTURAL constants (design
   §12: `MAX_ISOLATED`, `USD_MULT`, `FLOAT_TOL`, `CLOSE_WINDOW_MIN`; spread width and tick are
   READ from the engine config) live in `constants.py` with a one-line reason each. If you find
   yourself typing `0.30` or `20` anywhere else, stop.
3. **Nothing partial ever lands.** Compute everything into a staging directory, validate, then commit
   in one rename (task 9). If anything raises, the ledger must look exactly as it did before.
4. **Same venv as the engine:** `~/Dev/virtualenvs/gamma_chaser/bin/python`. Run tests from
   `scripts/` (`cd scripts && python -m pytest hiro_watch/tests -q`).
5. **Real data is available for smokes** (the 16 stored sessions); tests that need it are marked
   `@pytest.mark.integration` and skipped if `~/Dev/central_trade_data/thetadata/spxw_bomb_chains`
   is absent.

## Package layout (create exactly this)

```
scripts/hiro_watch/
  __init__.py  __main__.py  cli.py
  constants.py  registration.py  inputs.py  shadow.py  panel.py  ladder.py  refused.py
  book.py  stats.py  verdicts.py  ledger.py  report.py
  tests/  conftest.py  fixtures/  test_*.py
docs/hiro_watch/registrations/        (created by `watch register`)
docs/hiro_watch/nyse_holidays.csv     (task 3; one date per line, 2026-2027)
docs/replay/hiro_watch/<WATCH_HASH>/  (created by the first commit)
docs/replay/hiro_watch/marks/         (mark cache)
```

## Tasks (build order is the contract)

- [ ] **1. Skeleton + exceptions + `--debug`** (`__init__.py`, `__main__.py`, `cli.py`)
    - `WatchError` hierarchy exactly as design §Error handling (all 14 classes); `constants.py`
      (design §12); `cli.py` with FIXED argparse subcommands `register`, `backfill`, `run <date>`,
      `report`, `rebind`, `rebuild` — each a stub that raises `NotImplementedError` for now;
      `--debug` sets `logging.DEBUG` and prints `[debug] on`.
    - DONE: `python -m hiro_watch --help` lists every command; `test_cli_lists_commands` passes.

- [ ] **2. Registration** (`registration.py`) — W8, design §1
    - `Registration` dataclass with EVERY constant from requirements W3.1 (Θ, θ*), W3.4 (every
      count and threshold, including 20/10/10/5/25%/0.55/−150/40), W3.5 (checkpoints 10/20/30/40),
      W3.6 (2/2/3), W4.1 (C), W4.3 (15/1.5/−150/−350/10/5), W5.4 (20), W2.8 (20 sessions, 100
      minutes, 10 sessions minimum, [0.5, 2.0]), W6.2 (0.50, 5%, 3 minutes), W6.5 (DRAWS/SEED
      imported from `hiro_engine.register`), W6.6 shock list, W6.4 reconciliation 0.50, plus
      `classifier_columns` / `scorer_inputs` per candidate, `registration_date`,
      `engine_config_hash`, `frozen_manifest_hash`, `schema_version = 1`, and the sha of
      `docs/hiro_watch/nyse_holidays.csv` (task 3 writes the file; task 2's test uses a fixture
      copy).
    - `watch_hash(payload)`: canonical JSON (sorted keys, `separators=(",", ":")`), sha256; the
      payload never contains the hash. `code_hash()`: sha256 over sorted `*.py` under the package
      excluding `tests/` and `__pycache__`.
    - File lifecycle per design §1: `register()`, `register(supersede=True, reason=...)`,
      `load_active()`, `require_code_match()`, `append_code_line(reason)`. Guard rule, stated
      once: `register` (first time) and `rebind` do NOT call `require_code_match` — the first has
      nothing to match, the second exists to recover from a mismatch; every other command calls it
      first.
    - Firewall: `classifier_columns ⊆ panel.W22_COLUMNS` (import the tuple from task 4's module —
      create `panel.py` with just `W22_COLUMNS` now if needed) else `RegistrationError`.
    - Junior note: "canonical" means two dicts with the same content but different key order or
      whitespace produce the SAME hash — write that test first.
    - DONE: tests — hash invariance; payload with hash field rejected; register twice refuses;
      supersede repoints; code_hash changes when a `.py` changes and not when a test changes;
      firewall rejects `post_hoc_x`.

- [ ] **3. Inputs + calendar** (`inputs.py`, `docs/hiro_watch/nyse_holidays.csv`) — W1, W10.3, W1.7
    - `SessionInputs` with the paths and sha256s listed in design §2; `resolve(cfg, reg, date)`
      (needs the registration for the engine hash and the holiday sha) raising `CalendarExpired`
      past the holiday file's `# coverage_end`, and
      `MissingInputs([...])` (list everything missing, not just the first), `Unverified(date)` when
      the HIRO manifest note lacks `day-identity verified`, `MissingSession(date)` when there is no
      disposition row with the registration's engine hash.
    - `calendar_gaps(reg, upto)`: weekdays from the registration date to `upto` that are not in
      `nyse_holidays.csv` and have no disposition row. `nyse_holidays.csv` is the ONLY holiday
      authority (the engine's `event_calendar.csv` is the CPI/FOMC event list — do not read it for
      holidays). Write the holidays file (NYSE 2026–2027, `# coverage_end: 2027-12-31`) and
      register its sha.
    - Manifest-declared shas are re-hashed from bytes and compared → `InputTampered(path)` on
      mismatch (never trust a manifest).
    - DONE: tests with a temp directory tree — all four refusal types plus `InputTampered`; a
      holiday is not a gap; an event_standdown day (has a disposition row) is not a gap; a missing
      weekday is.

- [ ] **4. Shadow harness** (`shadow.py`) — design §3. THE load-bearing task; budget half the build.
    - `Policy`, `MemoryLog`, `ShadowSession`, `ShadowRuleEngine`, `ShadowExecutor`, `run_shadow`,
      `engine_identity_guard`, `assert_matches_log`, `engine_artifact_hashes` — exactly as in the
      design, including: ONE `super()._entry_events` call per bar; post-filter only; gated-episode
      memory; NaN r30 cannot enter under the gate; `credit` class property with setter and
      `_current_branch`; `_vetoes` records `(row, vetoes, health, quote_gap_streak)`;
      `_write_session_row` stores, never writes.
    - Junior notes: (a) `FeatureRow` and `Vetoes` are frozen dataclasses — use
      `dataclasses.replace`, never assignment. (b) `state.pending_entry` is created by
      `Executor.apply` from the `pending_entry` EVENT — dropping the event is the whole trick.
      (c) Build `range60_history` with `hiro_engine.session.build_range60_history` over the stored
      sessions BEFORE the day, the same way `backtest.run_backtest` does, or features will not
      match the log.
    - DONE (unit, on the engine's `tests/fixtures/v3_quotes_fixture.py` scenarios): baseline policy
      reproduces the fixture's expected events; gate flips only when r30 > θ or NaN; θ boundary
      (r30 == θ) passes; gated episode does not re-signal; `late` off changes only `late_state`;
      `vt_broken` override changes only that flag; entry_filter drops other setups and they never
      enter; (A,0.30) leaves a B leg at 0.10 and the fill assert sees 0.30 for A; super called once
      per bar; NaN r30 under the gate → skip line emitted, NO entry, and the panel later labels it
      `unclassifiable` (both asserted); `events_df` carries `candidate_id`; `trade_id` on trades is
      the engine's (never re-numbered). DONE (integration): `assert_matches_log` passes on
      2026-08-24, 2026-08-25, 2026-08-28, 2026-09-01 — exact EVENT_FIELDS equality (NaN-aware).

- [ ] **5. Panel** (`panel.py`) — W2, design §4
    - `W22_COLUMNS`, `REFUSAL_MAP_V1` + precedence, `build_panel(run, reg, baseline=None)`,
      `attach_outcomes(panel, trades, chains)` (join on `(candidate_id, session_date, trade_id)`;
      adds `trade_id`, `bomb_id`, `passed_theta_star`, `forgone`, `credit_variant`,
      `refused_table`), the COMPLETE eligibility mapping from design §4 (write it as one dict),
      `assert_features_match_log(panel, log_path)` (the per-session panel self-check),
      `r30_scale`, `scale_monitor` (zero/missing denominator → INSUFFICIENT), health mapping (raw
      `health` kept), `set` labeling from the registration date.
    - DONE: dedup (`gate_fail` + `skip` same minute → one row, `vt_broken` wins); unknown note →
      `other:` unscored; NaN r30 → `unclassifiable`; MAE ≤ 0 ≤ MFE; `flow_accel` formula; scale
      monitor INSUFFICIENT / OK / SCALE_DRIFT on a synthetic history; integration: panel features
      equal the engine log's `r15/run/rate/share/pull30/bounce30` on every signal row of 2026-08-28.

- [ ] **6. Ladder + excursions** (`ladder.py`) — W4a, design §5
    - `replay_limit`, `ladder_table` (self-check raises `LadderDrift`), `excursions`.
    - DONE: `test_ladder_self_check_29_of_29` on the stored sessions (integration); a deliberately
      perturbed quote makes the self-check raise; excursion sign convention.

- [ ] **7. Refused-B tables** (`refused.py`) — W5, design §6
    - population, three portfolio runs, sole-blocker attribution by `entry` event, isolated runs
      under the GLOBAL `MAX_ISOLATED` cap with the stated priority, `naked_short_min`;
      capacity-refused setups written with `table = capacity`, `layer = reported`, unscored.
    - DONE: attributed-but-`data_invalid` is reported not scored; `multi_blocked` when no entry
      event; cap enforced across tables; integration: 2026-08-24's five vt_broken refusals produce
      a table (values are whatever they are — the test checks shape, attribution, and that the
      baseline ledger is untouched).

- [ ] **8. Book** (`book.py`) — W6, design §7
    - `trades_from_events` (reads the engine's `trade_id` from entry/exit events — the watch
      never assigns ids), `bombs_from_trades`, `MarkCache` (full chain via
      `hiro_engine.chains._sdk_pull_day`, ONE pull, atomic `.tmp`+`os.replace` write, sha
      re-verified on read → `MarkTampered`, `mark_sha` on every inventory/book row), `quality`,
      `closing_quote` ([L−3, L]), `mark_inventory` (nullable `Int64` marks), `settle`
      (expiry-session, clamp 0..5 ×100 — width and multiplier from `constants`/engine config,
      provenance + reconciliation, PINNED into the row; on rebuild the committed `settle_source`
      is reused and its sha re-verified), `mark_sha`/`mark_shas` per design §7,
      `book_state(candidate, date, prev)` where the open set is `prev.inventory` rows
      with `session_date == prev.date` only, cumulative + split columns, `shock_grid`.
    - Junior note: the ThetaData client is reached ONLY through `hiro_engine.live.theta_client`;
      in tests it is a stub that counts calls — the second mark of the same (date, expiry) must
      make zero calls.
    - DONE: UNMARKED excluded from sums; bomb present in inventory the session before expiry and in
      settlements on expiry; payoff clamp; early-close L; reconciliation warning at > 0.50 pt;
      shock grid monotone; cumulative book over 3 synthetic sessions equals a from-scratch
      recomputation; integration: marking the 16 real bombs at 2026-09-02 reproduces the
      accounting's per-bomb mids EXACTLY (same quotes, tolerance 0) for every bomb that is not
      UNMARKED, and lists any UNMARKED with the failing quote.

- [ ] **9. Stats + verdicts + ledger** (`stats.py`, `verdicts.py`, `ledger.py`) — W6.5, W3.4–3.7,
  W4.3, W5.4, W9.3–9.4, W8.3
    - `lb95(…, draws, seed)` with the constants PASSED from `reg` (no defaults), Clopper–Pearson
      min, `None` below 2 sessions; `is_checkpoint(n, reg)`, `representation(panel, reg)`,
      `cohort_expectancy`; `a_depth_tables(reg, panel, cpanel)` (the Θ ladder diagnostic + θ*
      portfolio table); verdict state machines with every status incl. the terminal-checkpoint
      rule (any deferral at the last checkpoint → `REJECT-EXPIRED`); snapshot layout with
      `prev_snapshot` chain, `stage`, `commit` (rename + `current` pointer), `open_current`,
      orphan detection off the chain, `chronology_guard` (discovery + confirmation, backfill
      order), `verify_identity`, `rebuild`, `single_writer_lock` (flock; second writer →
      `LedgerLocked`), `Stamp` (code_hash in manifest only). NO prune.
    - DONE: LB95 1-session None, 10/10 ≈ 0.74, empty sessions excluded; checkpoint gating (session
      9 none, 10 verdict); each A-DEPTH status on fixture registrations; CREDIT variants (0.30
      REJECT while 0.20 PROMOTE; B < 5 fills no verdict; −$150 immediate; MAE < −$350); B-REFUSED
      never PROMOTE; crash injected after `os.rename` before the pointer write → `current`
      unchanged and orphan removed on next run; byte-identical re-run no-op; input sha mismatch
      refuses; chronology refusal names the missing session; `credit_ladder` key unique across two
      sessions; `calendar_sha` in stamps; second writer refused; terminal-checkpoint deferral →
      REJECT-EXPIRED; settlement unchanged after an EOD value appears later.

- [ ] **10. Main loop + report + shadow-guarantee test** (`cli.py`, `report.py`) — design §Main loop
    - Wire `watch run <date>`, `backfill`, `report`, `register --supersede`, `rebind`, `rebuild`
      (no prune) — `run` opens the single-writer lock FIRST and everything happens inside it;
      `report.py` prints
      the book (baseline + candidates side by side), progress lines, verdict tables, shock grid,
      DIAGNOSTIC labels, and the W10.4 caveat under every CREDIT table.
    - DONE: `test_engine_artifacts_untouched` — sha256 of every file under `scripts/hiro_engine/`,
      `docs/hiro_engine/registration.json`, `config.yaml`, and every `paper_log*.csv` before and
      after `watch backfill` + `watch <date>` on the real store are identical (integration);
      `watch report` output contains every table header; `test_runtime_budget`: one real session
      end-to-end < 120 s (integration).

- [ ] **11. Register for real + backfill + first confirmation session** (ops, not code)
    - `watch register` with the v1.2 constants (the user confirms the payload before the hash is
      written — it is frozen forever after); `watch backfill` over the 16 discovery sessions;
      verify `watch report` reproduces `branch_accounting_2026-09-03.md` §1 and §7 numbers on the
      discovery columns (fills, P&L, the 0.30 ladder) — any difference is a bug, not a new finding.
    - Then the standing daily loop gains one step: capture → identity → ingest → engine replay →
      `watch <date>`. Add it to `docs/hiro_engine/RUNBOOK.md` (one line) and to
      `docs/hiro_watch/build_notes.md` with the WATCH_HASH.

- [ ] **12. Investment gate (governance, not code) — separate from build acceptance**
    - Build acceptance (tasks 1–11 green, shadow guarantee, byte-identity) says the WATCH works.
      It says NOTHING about the strategy. No candidate is promoted, no rule is edited, no capital
      is committed on the basis of a build sign-off.
    - Investment decisions happen ONLY at the registered checkpoints (W3.5: confirmation sessions
      10/20/30/40), only on the confirmation set, only through the verdict the watch prints, and
      then only via the human R7.2 → spec-edit → R9a re-registration path. The calibration record
      for every registered constant is `../hiro_engine/branch_accounting_2026-09-03.md` and
      `../hiro_engine/conclusions.md` §13–§16 (discovery data); the payload cites them as
      `calibration_ref`. Program-level risk stays the engine's (1-lot paper; R9 loss lines); the
      watch adds visibility (W6.6 shock grid), not limits — by design, until a candidate is
      promoted and the engine spec is re-registered.

## Review gates for this build
After task 4 and after task 9: `/red-team-auditor` + architect `/codex-review` for adherence to
requirements/design/tasks (98% target, no nitpick loops). After task 11: the full test battery, the
shadow-guarantee test, and a byte-identity `watch rebuild --verify-only` before sign-off.

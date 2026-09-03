# Design — hiro_watch

*Architect design v1.2 (2026-09-03) for `requirements.md` v1.2a — v1.1 + review round 2 (FAIL 23/8 → applied: identity guard wired into the loop, LB95 constants from the registration, A-DEPTH diagnostics producer, panel feature self-check, terminal-checkpoint rule, capacity-refused contract, manifest shas re-verified against bytes, holiday file in the payload, marks via `chains._sdk_pull_day` with atomic write + sha on rows, settlement pinned at commit, open-inventory derivation rule, `candidate_id` in every key, pruning REMOVED, snapshot chain via `prev_snapshot`, nullable $ columns, zero-denominator scale rule, single-writer lock, runtime-budget test, NaN test wording, `backfill` in the CLI; spec W8.3 aligned to snapshot-granularity code lineage in requirements v1.2a). Design review closed at two rounds per the 98% discipline. v1.1 = v1.0 + round 1 (FAIL 20/8 → all applied: single-pass post-filter hook with gated-episode memory, NaN gate semantics, credit property with setter, registration/rebind lifecycle made possible (code lineage in manifests not rows; `register --supersede`), engine-identity guard, holiday-aware calendar, versioned refusal map, entry-event-based sole-blocker, global isolated-replay cap, full-chain mark cache, 3-minute close window, composite ledger keys, calendar sha stamp, cohort attribution, discovery backfill order, cumulative snapshot state, health capture point). One principle decides everything
below: **the watch never re-implements the engine — it RUNS the engine, read-only, in memory, with
a candidate injected through three subclass hooks.** Every counterfactual fill, exit, capacity effect
and bomb comes out of `hiro_engine`'s own `Session → RuleEngine → Executor` loop (W0.3), so the
physics cannot drift from the frozen rules. The engine package is imported, never edited; its
artifacts are hashed before and after every run (W0.1). Prior art reused: the accounting replay of
2026-09-03 (`../hiro_engine/branch_accounting_2026-09-03.md` §7 — self-checked 29/29), the R9a
bootstrap constants, `ChainStore`, `FeatureEngine`, `EVENT_FIELDS`. Deliberately not built:
databases, services, GUIs, async, plugins, any threshold search.*

## Overview

`watch <date>` = **guards → pin inputs → ~12 in-memory engine runs → panel → diagnostics → books →
verdicts → snapshot commit → report.** One package `scripts/hiro_watch/` (13 modules, ~1,800 lines
incl. tests), one CLI, one ledger root `docs/replay/hiro_watch/<WATCH_HASH>/` made of immutable
snapshot directories. Runtime budget: ≤ 120 s/session (W: non-functional); measured engine replay of
one session ≈ 2–4 s, so 12 runs ≈ 50 s worst case.

## Architecture

```
                 hiro_engine (frozen, imported read-only)
   ┌──────────────────────────────────────────────────────────────┐
   │ config.load_config  feeds.ReplayFeed  chains.ChainStore       │
   │ session.Session ─▶ rules.RuleEngine ─▶ executor.Executor      │
   │ features.FeatureEngine   models.EVENT_FIELDS   register.DRAWS │
   └───────▲──────────────────────────────────────────────────────┘
           │ subclass hooks only (no edits)
   ┌───────┴──────────────────────────────────────────────────────┐
   │ hiro_watch.shadow                                             │
   │   Policy ─▶ run_shadow(cfg, day, policy, chains) ─▶ ShadowRun │
   │   ShadowSession(_vetoes, _write_session_row, hooks)           │
   │   ShadowRuleEngine(_entry_events: a-depth gate, late off)     │
   │   ShadowExecutor(credit per branch on book AND fill)          │
   │   MemoryLog(emit → list[Event])                               │
   └───────┬──────────────────────────────────────────────────────┘
           │ ShadowRun = events_df (EVENT_FIELDS) + rows_df (per-minute FeatureRow+Vetoes)
   ┌───────┴──────────────────────────────────────────────────────┐
   │ panel ── ladder ── refused ── book ── stats ── verdicts       │
   │            (all pure functions over DataFrames)               │
   └───────┬──────────────────────────────────────────────────────┘
           │ tables
   ┌───────┴───────────────┐   ┌──────────────┐   ┌─────────────┐
   │ ledger (snapshots)    │   │ registration │   │ report      │
   └───────────────────────┘   └──────────────┘   └─────────────┘
```

## Components

### 1. `registration.py` — W8
- `Registration` dataclass = the W8.1 payload (candidates Θ/θ*/C, every evidence-bar number, W2.8
  constants, W6.5 constants, `registration_date`, `engine_config_hash`, `frozen_manifest_hash`,
  `schema_version`, each candidate's `classifier_columns` / `scorer_inputs`).
- `watch_hash(payload) -> str`: `sha256(json.dumps(payload, sort_keys=True, separators=(",",":"),
  ensure_ascii=False).encode())` — the payload never contains the hash (W8.1). Unit-tested for key-
  order and whitespace invariance.
- `code_hash() -> str`: sha256 over `sorted(Path(pkg).rglob("*.py"))` of (relative path + b"\0" +
  bytes) — tests excluded (`tests/` subtree), `__pycache__` excluded.
- Files: `docs/hiro_watch/registrations/<WATCH_HASH>.json`, `<WATCH_HASH>.code` (append-only lines
  `code_hash,utc_ts,reason`), `active.txt` (the hash). **Lifecycle:** `watch register` — refuses if
  `active.txt` exists (W8.2), otherwise writes the JSON, the first `.code` line, `active.txt`, and
  an empty ledger root (no code-match guard: there is nothing to match yet). `watch register
  --supersede --reason` — the ONLY way to replace a registration: writes the new JSON/.code,
  repoints `active.txt`, creates the new ledger root, leaves the old root read-only. `watch rebind
  --reason` — runs WITHOUT the guard (that is its purpose): `ledger.rebuild(verify_only=True)`
  under the current code; on success appends the new `.code` line, on failure changes nothing and
  prints the first non-identical table. Every other command runs `require_code_match()` first
  (`CodeMismatch` unless `code_hash()` == last `.code` line).
- Firewall at register time (W2.4): every `classifier_columns` entry ∈ `panel.W22_COLUMNS` else
  `RegistrationError`.

### 2. `inputs.py` — W1, W0.4, W1.6, W1.7, W10.3
- `SessionInputs` (frozen): paths + sha256 for chain cache (from chain manifest), SPX parquet, SPY
  parquet or `absent`, HIRO normalized CSV (sha from the HIRO manifest entry — and the manifest
  `note` must contain `day-identity verified`, else `Unverified(date)` → refuse, W10.3), levels row
  bytes or `absent`, the engine log file, `event_calendar.csv`, disposition row (from
  `sessions_backtest.csv` / `sessions.csv` — the row whose `config_hash` == the registration's
  engine hash; missing → `MissingSession(date)`, W1.7).
- `resolve(cfg, date) -> SessionInputs`; raises `MissingInputs([...])` listing everything absent
  (W0.4) — never partial. Manifest-declared shas (chain, HIRO) are NOT trusted: the file bytes are
  re-hashed and compared; a mismatch raises `InputTampered(path)`.
- `nyse_holidays.csv` is part of the registration payload (its sha is in the JSON, W8.1) and is
  re-verified at every run like any other input.
- `calendar_gaps(reg, upto_date) -> list[date]`: weekdays not in `event_calendar.csv` holidays and
  without a disposition row (W1.7) — used by `ledger.chronology_guard`.

### 3. `shadow.py` — the heart (W0.3, W3b, W4b, W5b)
- `Policy` (frozen dataclass): `a_depth_theta: float | None`; `credit_by_branch: dict[str, float]`
  (default `{"A": 0.10, "B": 0.10}`); `disable: frozenset[str]` ⊆ `{"vt_broken", "levels_invalid",
  "late"}`; `entry_filter: frozenset[SetupId] | None` (isolated replays: only these setups may
  enter); `candidate_id: str` (`baseline`, `a_depth_-4.0`, `credit_A_0.30`, `refused_vt`, …).
- `MemoryLog`: `emit(events)` appends `Event` objects to a list; exposes `csv_path=None`; never
  writes. `ShadowSession(Session)` is constructed with `mode="backtest"`, `resume=False`,
  `log=MemoryLog()`, the SAME `ChainStore` instance the engine uses (read-only) and:
  - `_vetoes(row)`: calls `super()`, then `dataclasses.replace(v, vt_broken=False)` if
    `"vt_broken" in policy.disable`, `levels_invalid=False` if `"levels_invalid"` — nothing else
    changes (flow_veto untouched). Also RECORDS `(row, vetoes, self.health, self.quote_gap_streak)`
    into `rows` — this is the panel source. Capture point is safe: in `process_tick`, `self.health`
    is assigned from `_health(tick)` BEFORE the `dataclasses.replace(row, vetoes=self._vetoes(row),
    health=self.health, …)` line (session.py:243-253), so the hook sees the minute's final health.
    The engine carries ONE health string; the panel maps it by precedence — `hiro_health =
    HIRO_DOWN if health == "HIRO_DOWN" else DEGRADED_VWAP if health == "DEGRADED_VWAP" else OK`;
    `option_quotes_health = OPTION_QUOTES_DOWN if health == "OPTION_QUOTES_DOWN" else OK` — and
    records the raw `health` too (the mapping is lossy when two conditions coincide; the raw
    column is authoritative). The engine exposes exactly one health state per minute (R10); the
    watch cannot observe two independent states the engine never computed — requirements v1.2a
    records `hiro_health`/`option_quotes_health` as DERIVED from the single engine state.
  - `_write_session_row(row)`: stores the `SessionRow` on the run; writes nothing.
  - `__init__` swaps `self.rules = ShadowRuleEngine(cfg, tier, selector, policy)` and
    `self.executor = ShadowExecutor(cfg, selector, tier, policy)` after `super().__init__` — the
    two engine objects are replaced, not modified.
- `ShadowRuleEngine(RuleEngine)`: overrides ONLY `_entry_events(row, state)`, as ONE pass:
  ```python
  def _entry_events(self, row, state):
      if "late" in self.policy.disable:
          row = dataclasses.replace(row, late_state=False)          # (pre) LATE off, nothing else
      events = super()._entry_events(row, state)                     # exactly ONE super call
      return self._post_filter(events, row, state)                   # (post) gate / filter
  ```
  `_post_filter` acts only on the events super produced, so it never invents a setup that the
  engine would not have signaled (no spurious skips) and dedup state inside super is touched once:
  1. A-DEPTH: if super emitted an A `signal`(+`pending_entry`) and the policy has `a_depth_theta`:
     PASS iff `row.r30 is not None and row.r30 <= theta`. Otherwise (r30 > θ **or r30 is NaN** —
     the candidate policy is "enter only when r30 ≤ θ", so NaN cannot enter and cannot consume
     capacity; the panel still labels the NaN case `unclassifiable`, W2.7) the two events are
     replaced by ONE `Event(event_type="skip", rule_id="W3", branch="A", episode=row.episode_a,
     signal_min=row.min, notes="skip: shadow_gate a_depth r30=<v>|nan theta=<θ>")` and the
     episode id is added to `self._gated_a_episodes`. Because the engine marks an episode as
     entered only in `Executor._register_entry`, a gated episode would otherwise re-signal every
     minute its conditions hold; the hook therefore drops any later A `signal`/`pending_entry` for
     an episode in `_gated_a_episodes` silently (one skip line per episode, like the engine).
  2. `entry_filter`: any `pending_entry`/`signal` event whose `SetupId` ∉ filter is dropped from
     the list and replaced by `skip: shadow_filter` (one per episode via the same gated-episode
     memory). Nothing in `state` needs clearing: `state.pending_entry` is created by
     `Executor.apply` FROM the `pending_entry` event (executor.py:232), so a dropped event never
     becomes a pending entry. Skips/gate-fails/late lines always flow (they are panel inputs).
- `ShadowExecutor(Executor)`: `self.credit` becomes a property reading
  `policy.credit_by_branch[self._current_branch]`, with `_current_branch` set in overrides of
  `_book_limit_entry(bar, pe, quotes, state)` (from `pe.branch`) and `_apply_fill(tr, row, state)`
  (from `tr.branch`) and restored in `finally`. Both the booking (`raw_l = leg1_fill ∓ self.credit`,
  executor.py:170) and the R1.4e invariant assert (`tr.credit < self.credit − 1e-9`, executor.py:246)
  therefore see the branch's credit (W4.1a). `Executor.__init__` assigns `self.credit = cfg.num(...)`
  (executor.py:35); the subclass defines `credit` as a class property WITH a setter (`__init__`'s
  assignment stores into `self._base_credit`; the getter returns
  `policy.credit_by_branch.get(self._current_branch, self._base_credit)`) — the base Executor code
  is untouched and its own assignment keeps working. `_current_branch` defaults to `None` (base
  credit) outside the two overridden methods. Everything else —
  conservative bookings, cancels, cap, clock, resolution — is the engine's code untouched.
- `engine_identity_guard(cfg, chains, reg)`: `cfg.config_hash == reg.engine_config_hash` and
  `chains.verify_frozen(cfg)` (the frozen 8 pin) must both hold before ANY shadow run; violation →
  `EngineIdentityError` (W1.4/W8.1 binding). Called once per `watch` invocation.
- `run_shadow(cfg, day, policy, chains, range60_history) -> ShadowRun`: builds `ReplayFeed(cfg,
  [day])`, `ShadowSession(...)`, calls `run_replay(feed)` exactly like `backtest.run_backtest` (same
  pooled `range60_history` computed by `session.build_range60_history` over stored sessions before
  `day`, so features match the engine bit-for-bit), returns `ShadowRun(candidate_id, policy,
  events_df: DataFrame[EVENT_FIELDS], rows_df: per-minute frame of every FeatureRow field +
  vetoes, session_row: SessionRow)`. `events_df` is stamped by the engine itself (ts/mode/tier/
  session_date/config_hash) — identical columns to the log.
- **Baseline self-check** (W9.4): `run_shadow(policy=BASELINE)` must equal the engine's logged rows
  for the date on every EVENT_FIELDS column (NaN-aware equality). Mismatch → `ShadowDrift(date)` →
  refuse. This single check proves the harness reproduces the engine before any candidate runs.

### 4. `panel.py` — W2
- `W22_COLUMNS` (frozen tuple, the firewall vocabulary) and `POST_HOC_PREFIX = "post_hoc_"`.
- `build_panel(run: ShadowRun, reg) -> DataFrame`: one row per `SetupId = (session_date, branch,
  signal_min, episode)` from `events_df` rows of type `signal | skip | gate_fail | late_no_entry |
  pending_entry | entry | entry_aborted_no_quote`; `refusal_reason` from a VERSIONED normalization map `REFUSAL_MAP_V1` (engine note string →
  enum): `"short blocked: vt_broken" → vt_broken`, `"short blocked: levels_invalid" →
  levels_invalid`, `late_no_entry → late`, `gate_fail → gate_fail`, `"3 entries/day reached" →
  capacity_daycap`, `"one unpaired leg at a time" → capacity_oneleg`, `"shadow_gate…" →
  shadow_gate`, `"shadow_filter" → shadow_filter`; anything else → `other:<raw>` (tallied, never
  scored); a `skip` without `signal_min` is keyed by its bar minute. Precedence (min wins):
  `vt_broken 0 < levels_invalid 1 < late 2 < gate_fail 3 < capacity_* 4 < shadow_* 5 < none 6`;
  `refusal_reasons_all` = sorted set. Changing the map bumps `schema_version` (W8.1). Feature columns are taken from `rows_df`
  at `signal_min` (the engine's own FeatureRow — hence "recomputed with the engine's feature
  module"); `flow_accel = r15 − (r30 − r15)`; `vt_state` from levels + close; `eligibility` per
  W2.9 enum; `unclassifiable = r30 is NaN`.
- `attach_outcomes(panel, trades, chains)`: W2.3 columns from `book.trades_from_events` joined on
  `(candidate_id, session_date, trade_id)` where the trade's `(branch, signal_min, episode)` gives
  the panel `setup_id`; `mae_usd/mfe_usd` from `ladder.excursions`.
- **Eligibility mapping (complete, versioned with `REFUSAL_MAP_V1`):** entered trade with outcome
  ∈ {fill, timeout, scratch, cap, veto_exit, state_flip, resolution_close} → `scored`; outcome
  `data_invalid` → `data_invalid`; outcome `censored` → `censored`; `entry_aborted_no_quote` →
  `entry_aborted`; refused with reason `vt_broken|levels_invalid` → `safety_blocked`; `late` →
  `late_blocked`; `gate_fail` → `gate_failed`; `capacity_*` → `capacity_blocked`; `shadow_gate` →
  `gated` (candidate panels only); `shadow_filter` → `filtered`; classifier input NaN →
  `unclassifiable` (overrides `scored`); anything else → `other`. Only `scored` enters rates.
- **Lineage:** `setup_id → (candidate_id, session_date, trade_id) → bomb_id = (candidate_id,
  session_date, trade_id)` — the same triple keys `trades`, `bombs`, `inventory` rows (per session)
  and `settlements`; every panel row for an entered setup carries `trade_id` and `bomb_id` (null if
  not completed). Verdict selectors are explicit panel columns: `passed_theta_star: bool|null`
  (A-DEPTH, baseline panel, null when unclassifiable), `forgone = (branch == "A") &
  (passed_theta_star == False)`, `credit_variant ∈ {A_0.20, A_0.30, B_0.20, B_0.30, null}` on
  candidate panels, `refused_table ∈ {vt, levels, late, capacity, null}`.
- `r30_scale(stored_sessions_before, D)` and `scale_monitor(reg, D) -> {"status": OK|SCALE_DRIFT|
  INSUFFICIENT, "ratio": …}` (W2.8; constants from `reg`).
- Candidate panels: `build_panel(candidate_run)` + `attach_outcomes(…, trades_from_events(
  candidate_run.events_df))` + `in_baseline = setup_id ∈ baseline panel` (W2.9) — candidate
  panels carry outcomes exactly like the baseline's, so eligibility, CREDIT and sole-blocker
  logic read one schema. Attribution columns on every panel row: `branch`, `set`
  (DISCOVERY/CONFIRMATION from the registration date), `candidate_id`.

### 5. `ladder.py` — W4a diagnostic + excursions
- `replay_limit(chain_day, trade, credit, stop=None) -> (outcome, minute, pnl)` — the accounting
  replay verbatim (self-checked 29/29 on 2026-09-03), parameterised; `stop` retained for reporting
  only (the $150 stop was REJECTED; not a candidate).
- `ladder_table(chain_store, trades) -> DataFrame` for C = {0.10, 0.20, 0.30} per trade; asserts the
  0.10 row reproduces `outcome`, `minutes_to_fill`, `pnl_usd` for every trade (W9.4 self-check) —
  any mismatch raises `LadderDrift`.
- `excursions(chain_day, trade) -> (mae_usd, mfe_usd)`: conservative-side marks of the lone leg from
  `entry_min` through the exit-decision minute (W2.6).

### 6. `refused.py` — W5
- Population from the baseline panel: `refusal_reason ∈ {vt_broken, levels_invalid, late}` and
  branch B (W5.1); capacity-refused setups are written to the same `b_refused` table with
  `table = capacity`, `layer = reported`, no replay and no score (W5.1's "reported separately").
- Alignment note on W5.2a ("each refused setup is entered…"): the PORTFOLIO layer replays every
  refused setup (that is where every one is entered when its sole blocker is off); the ISOLATED
  layer is capped because it is diagnostic. Requirements v1.2a records this reading.
- Portfolio layer: three `run_shadow` calls with `disable={"vt_broken"}`, `{"levels_invalid"}`,
  `{"late"}` (one rule each, W5.2b). **Sole-blocker attribution:** a refused setup is attributed to
  a table iff the candidate run for that rule contains an `entry` event with the same `setup_id`
  (it actually entered once the rule was off); its `eligibility` then follows the trade's outcome
  (`scored`, or `data_invalid` / `censored` / `entry_aborted` — reported, not scored). A setup with
  no `entry` event in that run is `multi_blocked` with `refusal_reasons_all` from the candidate
  panel.
- Isolated layer: for attributed setups, `run_shadow(disable=<same rule>, entry_filter={setup})`;
  **global cap `MAX_ISOLATED = 20` per session across all three tables** (priority vt → levels →
  late, earliest signal first; beyond → `DIAGNOSTIC_TRUNCATED`). Run budget per session is
  therefore bounded at 1 + 1 + 4 + 3 + 20 = 29 engine runs ≈ 60–90 s worst case, inside the
  120 s target; the portfolio layer is the verdict basis so truncation loses no evidence.
- Output rows per W5.2/W5.3 incl. `naked_short_min = (fill_or_exit_min − entry_min)`.

### 7. `book.py` — W6
- `trades_from_events(events_df) -> DataFrame` (entry+exit join; the accounting extractor); 
  `bombs_from_trades(trades)` → one row per completed bomb: `bomb_id = (candidate_id, session_date,
  trade_id)`, `long_k`, `short_k` (A: long k1/short k2; B: short k1/long k2), `expiry`, `credit_usd`.
- `MarkCache`: `docs/replay/hiro_watch/marks/<date>_<expiry>.parquet` = the FULL put chain
  (every strike, `strike="*"`, minutes [L−5, L] where L is the session's last regular bar) for
  that (date, expiry), pulled ONCE through `hiro_engine.chains._sdk_pull_day(day, expiry)` (the
  engine's own pull function, so the mark path is the ChainStore module's code, not a second
  client) — written atomically (`.tmp` + `os.replace`), sha256 recorded BOTH in the snapshot
  manifest and on every `inventory`/`book` row that used it (`mark_sha`), and re-hashed on every
  read (`MarkTampered` on mismatch). Because
  the whole chain is persisted, a strike needed by a later candidate is always present (no
  expansion problem). `mark(date, expiry, strike)`: the day's `ChainStore` cache if the expiry
  matches `expiry_of(date)`, else the mark cache, else the single pull (W6.2, W10.2).
- `quality(bid, ask) -> usable | stale | invalid` (W6.2: valid per R10.4 and spread ≤ max(0.50,
  0.05·mid)); `closing_quote(date, expiry, strike)`: the LAST `usable` quote with minute in
  [L−3, L] (L = 960 normally; the last regular bar on an early-close session, from the SPX file)
  else `UNMARKED` — the W6.2 three-minute window exactly.
- `mark_inventory(bombs, date) -> DataFrame[bomb_id, mark_mid_usd, mark_liq_usd, unmarked]`
  (`mark_*_usd` are nullable `Int64`; null iff `unmarked`);
- Settlement is PINNED at commit: the `settlements` row stores `settle_value`, `settle_source`,
  and the source file's sha; a later-populated EOD table never changes a committed settlement
  (snapshots are immutable; a rebuild reads the pinned value from the prior snapshot, not the
  source).
  `settle(bombs, date, spx_close, source)` per W6.4 (`clamp(intrinsic, 0, 5)·100`, on the expiry
  session, provenance `index_eod` if `~/Dev/central_trade_data/…/index_eod` has the date else
  `spx_1m_close`, reconciliation warning > 0.50 pt).
- **Cumulative state (the snapshot contract):** every snapshot holds the COMPLETE tables to date,
  so the previous snapshot IS the prior state. `book_state(candidate_id, date, prev: Snapshot) ->
  BookRow` reads `prev.inventory` rows for the candidate WHERE `session_date == prev.date`
  (the open set is the previous session's inventory rows — never a union over history, so a bomb
  can never be duplicated as open) (open bombs with their planting session,
  credit, and per-session liq marks — the drawdown series), `prev.settlements`, and `prev.book`'s
  cumulative realized cash; adds today's new bombs and failed attempts from the run's trades; marks
  everything open today; settles today's expiries (W6.4); writes today's `inventory` rows (one per
  open bomb per session — the aging history), `settlements`, and a `book` row whose realized/
  settled columns are cumulative and whose split columns `realized_cash_A/B`, `credits_A/B`,
  `failed_pnl_A/B`, and `*_discovery/*_confirmation` carry the W3.3 attribution. Verdicts and
  checkpoints read the cumulative `panel`/`candidate_panels`/`book` tables of the CURRENT snapshot
  only — nothing is recomputed from history, so evidence bars are deterministic functions of one
  snapshot. The first snapshot's `prev` is the empty state. Shock grid (`shock_grid(bombs,
  spx_close)`) per W6.6; concentration by expiry/strike band.

### 8. `stats.py` — W6.5, W3.5, W3.6
- `lb95(successes_by_session: Series, n_by_session: Series, draws: int, seed: int) -> float |
  None` — `draws`/`seed` are ALWAYS passed from `reg` (which recorded them from
  `hiro_engine.register.DRAWS/SEED` at registration); no defaults in code: universe = sessions with n ≥ 1; < 2 → `None`; bootstrap pooled rate, 5th percentile
  (`numpy.percentile(..., 5, method="linear")`); `min(bootstrap, clopper_pearson_lower(k, n, 0.05))`
  with `scipy.stats.beta.ppf(0.05, k, n−k+1)` (k=0 → 0). `DRAWS`, `SEED` imported from
  `hiro_engine.register` — the R9a constants, one home.
- `cohort_expectancy(panel_rows, trades, bombs_marks) -> float`: the W3.3 formula over a cohort
  selected by (`candidate_id`, `branch`, `set`, passed/forgone flag) — one function, called with
  different selectors for baseline / candidate / forgone; realized cash split by branch comes from
  the trades' `branch` column, bombs' marks from the candidate's own `inventory` rows.
- `is_checkpoint(n_countable_confirmation_sessions, reg) -> bool` (n ∈ reg.checkpoints);
  `representation(passed_panel, reg) -> OK | UNREPRESENTED` (W3.6). **Terminal checkpoint rule:**
  at the LAST registered checkpoint a deferral of any kind (UNREPRESENTED, SCALE_DRIFT,
  DEFERRED_UNMARKED, count bars unmet) resolves to `REJECT-EXPIRED` — a registration always ends
  with a verdict. `scale_monitor`: a zero or missing reference denominator → `INSUFFICIENT`
  (never a division).

### 9. `verdicts.py` — W3.4, W4.3, W5.4
- Pure functions `a_depth_verdict(reg, baseline_panel, candidate_run_panel, books, session_ctx) ->
  Verdict(status, reasons, progress)` with `status ∈ {PROMOTE, REJECT, REJECT-EXPIRED, INCONCLUSIVE,
  SCALE_DRIFT, UNREPRESENTED, DEFERRED_UNMARKED}`; `credit_verdict(reg, branch, c, …)`;
  `b_refused_status(reg, …) -> INCONCLUSIVE | REPORTED` (never a promotion, W5.4).
- Immediate REJECT paths evaluated every session; everything else only when
  `stats.is_checkpoint(...)`; the 4th checkpoint is terminal (W3.5). All numbers come from `reg`.

### 10. `ledger.py` — W9.3, W9.4, W8.3
- Layout: `docs/replay/hiro_watch/<WATCH_HASH>/snap_<NNNN>_<date>/{panel,a_depth,credit_ladder,
  b_refused,book,inventory,settlements,candidate_panels}.parquet` + `manifest.json` (input shas,
  code_hash, engine hash, table row counts, sha256 of every table) and the pointer file `current`.
- `chronology_guard(reg, date)`: `inputs.calendar_gaps` must be empty and EVERY session with a
  disposition row before `date` (discovery AND confirmation, countable or not — book state depends
  on all of them) must already be in the snapshot chain (W9.3). **Discovery backfill:** `watch
  backfill` runs the discovery sessions (frozen 8 + 08-24 → registration date) in chronological
  order as the first snapshots of a new registration; `watch <date>` refuses until backfill is
  complete. `inputs.calendar_gaps` treats a weekday as a session iff it is not in
  `docs/hiro_watch/nyse_holidays.csv` (registered by sha; event_standdown days ARE sessions with a
  disposition row, so they never read as gaps).
- `commit(staging_dir, date)`: validate → `os.rename(staging, snap_dir)` (atomic on the same
  filesystem) → write `current.tmp` + `os.replace(current.tmp, current)`. `open_current()` follows
  `current`. Each snapshot manifest carries `prev_snapshot` (the name of its predecessor; null for
  the first); the CHAIN is `current` → `prev_snapshot` → … → first. A directory not on that chain
  is an orphan and is deleted at the next run start. **No pruning:** snapshots are small (tables
  for ≤ ~250 sessions ≈ tens of MB) and every one is needed for `verify_identity(date)` and for
  `rebuild`; the `prune` command is removed.
- `verify_identity(date)`: recompute into staging, compare each table's sha256 with the committed
  snapshot's manifest (byte-identity, W9.4); `rebuild(verify_only)`: chronological recompute of
  every snapshot. `single_writer_lock(reg)`: `fcntl.flock` on `<root>/.lock` held for the whole
  command; a second writer refuses immediately (`LedgerLocked`).
- Every table row carries `watch_hash, engine_config_hash, chain_sha, spx_sha, spy_sha, hiro_sha,
  levels_sha, log_sha, calendar_sha` (W8.3/W1.6) — a `Stamp` dataclass applied by
  `ledger.stamp(df)`. **`code_hash` is recorded in the snapshot `manifest.json` (code lineage),
  NOT in table rows** — otherwise a rebind could never be byte-identical. Byte-identity (W9.4)
  compares TABLE bytes; manifests are compared on everything except the code-lineage block.
  (Requirements W8.3's "stamped with code_hash" is satisfied at snapshot granularity — noted for
  the spec's next revision.)

### 11. `report.py` — printing: book (baseline + each candidate side by side), progress lines,
verdict tables, the shock grid, the standing W10.4 caveat under every CREDIT table, DIAGNOSTIC
labels. Text only, ≤ 120 columns, tables via `DataFrame.to_string`.

### 12. `cli.py` / `__main__.py` — `watch <date> [--debug]`, `watch report`, `watch register
[--supersede --reason]`, `watch backfill`, `watch rebind --reason`, `watch rebuild [--verify-only]`. `--debug` sets
`logging.DEBUG` and prints `[debug]` per the global CLI rule. Every command begins with
`registration.require_code_match()` (except `rebind`, which begins with it and then re-verifies).

### 13. `tests/` — see Testing strategy.

## Data model

| table | key | notable columns |
|---|---|---|
| `panel` | `setup_id` (+ `candidate_id=baseline`) | W2.2 (all), `refusal_reason`, `refusal_reasons_all`, `eligibility`, `unclassifiable`, W2.3 outcome cols, `mae_usd`, `mfe_usd`, `set ∈ {DISCOVERY, CONFIRMATION}` |
| `candidate_panels` | `(candidate_id, setup_id)` | same as `panel` + `in_baseline` |
| `a_depth` | `(session_date, theta)` | n_passed/rejected/unclassifiable (diagnostic), portfolio-run trades & P&L for θ* only, `passed_days`, `max_day_share` |
| `credit_ladder` | `(candidate_id, session_date, layer ∈ {diagnostic, portfolio}, branch, c, trade_id)` | diagnostic Δ row per trade per c; portfolio-run outcome per (branch,c) |
| `b_refused` | `(table ∈ {vt,levels,late}, setup_id)` | layer ∈ {portfolio, isolated}, `scored|multi_blocked`, fill, minutes, pnl, mae, naked_short_min, `data_invalid` |
| `book` | `(candidate_id, session_date)` | realized_cash, credits, failed_attempt_pnl, settled_usd, inv_mid, inv_liq, n_bombs, n_unmarked, drawdown_liq, mtm_liq, shock grid as 9 columns |
| `inventory` | `(candidate_id, bomb_id, session_date)` | long_k, short_k, expiry, credit_usd, mark_mid_usd, mark_liq_usd, unmarked, mark_source |
| `settlements` | `(candidate_id, bomb_id)` | expiry, settle_value, settle_source, payoff_usd |
| `verdicts` (in manifest) | `(candidate_id)` | status, reasons, progress, checkpoint_no |

Units as in W2.6; every `$` column is `×100` integers stored as int64; rates float64; dates as ISO
strings (the engine's convention). Snapshots are immutable; the ONLY mutable file is `current`.

## Reuse (DRY ledger)
`Session/RuleEngine/Executor/FeatureEngine/InstrumentSelector/ReplayFeed/ChainStore/EVENT_FIELDS`
(engine, read-only); `build_range60_history` (engine); `DRAWS/SEED` (engine `register.py`);
`hiro_engine.live.theta_client` (marks only); the accounting replay (`ladder.replay_limit`) and
trade extractor (`book.trades_from_events`) lifted from `branch_accounting_2026-09-03` scripts; the
evening ops identity note (read, not recomputed). No numeric constant lives outside `registration`.

## Main loop (the whole watch, interpretable)

```python
def watch(date):
    reg = registration.load_active(); registration.require_code_match()
    with ledger.single_writer_lock(reg):                          # flock on <root>/.lock
      before = shadow.engine_artifact_hashes()                    # W0.1
      shadow.engine_identity_guard(cfg, chains, reg)              # engine hash + frozen pin, ENFORCED
    inp = inputs.resolve(cfg, date)                               # W0.4/W1.6/W10.3, refuses
    ledger.chronology_guard(reg, date)                            # W1.7/W9.3
    chains = ChainStore(); hist = build_range60_history(cfg, TIER_FULL, stored_before(date))
    base = shadow.run_shadow(cfg, date, BASELINE, chains, hist)
    shadow.assert_matches_log(base, inp.log_path)                 # W9.4 self-check → refuse
    runs = {p.candidate_id: shadow.run_shadow(cfg, date, p, chains, hist)
            for p in policies(reg)}      # a_depth θ*, (A,.2),(A,.3),(B,.2),(B,.3), refused vt/levels/late
    panel = panel.build_panel(base, reg); panel.assert_features_match_log(panel, inp.log_path)   # W9.4 panel self-check
    cpanels = {k: panel.attach_outcomes(panel.build_panel(r, reg, base), book.trades_from_events(r.events_df), chains)
               for k, r in runs.items()}
    a_depth = verdicts.a_depth_tables(reg, panel, cpanels["a_depth"])   # W3.3a ladder over Θ (diagnostic) + θ* portfolio
    trades = book.trades_from_events(base.events_df); panel = panel.attach_outcomes(panel, trades, chains)
    ladder = ladder.ladder_table(chains, trades)                  # W4a + self-check → refuse
    refused = refused.tables(reg, base, runs, cpanels, chains)     # W5 (+ isolated, capped)
    books = {k: book.book_state(k, date, ...) for k in ["baseline", *runs]}   # marks, settle, grid
    verdicts = verdicts.all(reg, panel, cpanels, ladder, refused, books, ctx(date))
    stage = ledger.stage(date, panel, cpanels, a_depth, ladder, refused, books, verdicts, inp, reg)
    assert shadow.engine_artifact_hashes() == before              # W0.1
    ledger.commit(stage, date); report.print_session(...)
    # (indentation: everything from `before` onward runs inside the lock)
```

`watch report` = `open_current()` + `report.print_cumulative`. `watch rebuild` = the loop above per
snapshot in order with `commit` replaced by `verify_identity`.

## Error handling
Exception hierarchy `WatchError` → `MissingInputs`, `Unverified`, `MissingSession`, `ChronologyError`,
`ShadowDrift`, `LadderDrift`, `CodeMismatch`, `RegistrationError`, `MarkError`. Any exception before
`commit` leaves the ledger untouched (snapshot design); the CLI prints the class + message and exits
2. No exception is ever swallowed; `data_invalid` and `UNMARKED` are DATA states, not errors, and are
tallied. Network failure in the single mark pull → `MarkError` → refuse (re-run later); a persisted
mark cache makes retries idempotent.

## Testing strategy
- **Harness fidelity (the load-bearing tests):** `test_shadow_baseline_matches_engine_log` over the
  stored sessions 2026-08-24 (zero trades), 2026-08-25 (B fill + A timeout), 2026-08-28 (3 A fills,
  3/day cap) — exact EVENT_FIELDS equality; `test_engine_artifacts_untouched` (hash before/after the
  full loop); `test_ladder_self_check_29_of_29` (the accounting trades).
- **Hooks:** `test_a_gate_flips_a_conditions_only_when_r30_gt_theta` (θ boundary equal passes; NaN
  untouched); `test_credit_branch_isolation` ((A,0.30) leaves a B leg at 0.10 in the same session,
  and the fill-invariant assert sees 0.30 for A); `test_late_off_only_changes_late_state`;
  `test_veto_override_only_named_flag`; `test_entry_filter_drops_other_setups_and_clears_pending`;
  `test_freed_capacity_setup_appears_only_in_candidate_panel`.
- **Panel:** dedup + precedence (`gate_fail`+`skip` same minute → one row, `vt_broken` wins);
  eligibility enum coverage; MAE ≤ 0 ≤ MFE; unclassifiable on NaN r30; scale monitor
  INSUFFICIENT/OK/SCALE_DRIFT with a synthetic history.
- **Book:** UNMARKED excluded from sums and defers verdicts; mark cache reused (second call makes no
  pull — the client is a stub that counts calls); settlement day-of (present day before, settled on
  expiry, clamp 0..500, early close last bar); reconciliation warning; shock grid monotone in shock.
- **Stats/verdicts:** LB95 (1 session → None; 10/10 → ≈0.74 via Clopper–Pearson; empty sessions
  excluded); checkpoints (session 9 no verdict, 10 verdict); each A-DEPTH status path on a fixture
  registration; CREDIT variants (0.30 REJECT while 0.20 PROMOTE; B < 5 fills → no verdict; −$150
  immediate REJECT; MAE < −$350 REJECT); B-REFUSED never PROMOTE; sole-blocker `multi_blocked`.
- **Ledger/registration:** canonical hash invariance; firewall rejects a `post_hoc_` column; register
  twice refuses; code mismatch refuses; rebind verify; chronology refusal; atomic commit with a
  crash injected after `os.rename` but before `current` write → `current` unchanged, orphan removed
  next run; byte-identical re-run no-op; input sha mismatch refuses.
- **Round-2 additions:** `test_runtime_budget` (one real session under 120 s, integration);
  `test_second_writer_refused`; `test_settlement_pinned_after_eod_appears`; `test_open_inventory_
  from_prev_session_only`; `test_manifest_sha_mismatch_refuses`; `test_mark_file_tampered_refuses`;
  `test_terminal_checkpoint_deferral_is_reject_expired`; `test_capacity_rows_reported_unscored`;
  `test_nan_r30_gate` asserts BOTH the skip line and the `unclassifiable` panel label.
- **Review-driven additions:** NaN-r30 A signal under the gate → skip, no entry, no capacity used;
  gated episode does not re-signal next minute; super called exactly once per bar (call counter);
  `register` on an empty tree succeeds, `--supersede` repoints, `rebind` verifies then appends;
  holiday weekday is not a gap, event_standdown day is not a gap, a missing weekday is; unknown
  refusal note → `other:` and unscored; entered-but-`data_invalid` refused setup is attributed but
  not scored; `MAX_ISOLATED` global across tables; mark cache holds every strike of the chain;
  closing mark uses [L−3, L] and early-close L; `credit_ladder` key unique across two sessions;
  calendar_sha present in stamps; candidate panel rows carry outcomes; cumulative book equals a
  from-scratch recomputation over 3 synthetic sessions (state-flow test).
- Fixtures: the engine's `tests/fixtures/v3_quotes_fixture.py` scenarios (already hand-computed)
  driven through `run_shadow` with policies; a 3-session synthetic mini-store for stats/ledger tests;
  real-data smokes on the stored sessions above (skipped if the store is absent).

## Decision record
This repository keeps no ADR directory; design decisions are recorded in `build_notes.md` (as the
engine does). The decisions above that a future reader must not re-open: (1) run the engine, never
re-implement it; (2) hooks are post-filters on events, never edits to engine state; (3) code
lineage lives in snapshot manifests, definitions in WATCH_HASH; (4) snapshots are cumulative and
immutable, `current` is the only mutable file; (5) the $150 stop is not a candidate.

## Explicitly not built
Intraday/live watch; any candidate not in W3–W5; any θ or c outside Θ/C; parameter search; the $150
stop (rejected 2026-09-03); engine edits of any kind; a database; a GUI; automatic promotion into the
engine (promotion remains the human R7.2 → spec → R9a path).

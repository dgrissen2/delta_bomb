# Build notes — hiro_watch v2 (2026-09-04)

Decisions taken while building that are not in the spec, and why.

- **`a_r30_lt`, strict `<`, applied in `a_fires`.** Review round 1 found two defects in the first
  cut: (a) `<=` with 0.0 is not v1 — `feeds.py:36` reindexes HIRO gaps with 0.0, so r30 == 0.0 is
  reachable; (b) the knob inside `a_conditions` re-numbered A episodes (the tracker consumes it),
  which broke the cross-candidate join. Now `a_conditions` is byte-identical to v1 and the gate sits
  on the signal in `a_fires`.
- **`late_enabled` is applied inside `RuleEngine._entry_events`** (both uses of `row.late_state`),
  not in `FeatureEngine`: the feature row stays identical to v1's, only the rule consumes the knob.
- **Veto knobs are applied in `Session._vetoes`** so the `veto_change` log rows also reflect the
  knob — the diag logs show what the engine actually believed that day.
- **v2's `chains.fetch` raises.** The clone never touches the network or the chain manifest; the v1
  daily loop is the only writer of the chain cache. `LiveChains` and `_update_manifest` removed.
- **`credit030` runs through v1** (`python -m hiro_engine --config`). v1's loader ignores the
  `watch:` section and the four knobs (fail-closed means missing keys raise; extra keys are fine).
- **Candidate logs are rebuildable, not ledgers.** The engine appends; `run.py` refuses duplicates
  and `--rebuild` regenerates from scratch. The baseline (v1) log is the only ledger.
- **`refusals()` dedups to one row per setup.** The engine logs a `skip: short blocked` line per
  minute the setup persists (31 rows → 21 vt_broken episodes on discovery data). Episodes are the
  unit W5 counts.
- **Marks:** closing mid of the spread, capped at the width, via v1's `_sdk_pull_day` cached under
  `docs/replay/hiro_watch/marks/`. Reproduces accounting §5 to the dollar (+$1,265).
- **Bars live in `compare.py::BARS`** with the W5.3 reference — one place, frozen with
  requirements v2.0. The old spec's "no decision numbers in code" rule was judged ceremony
  (`simplicity_audit_architect_2026-09-04.md`); a change to a bar is a change to requirements.md.
- **`portfolio` replay is the only replay.** No isolated per-trade counterfactuals anywhere. The
  first backfill already showed why: `credit030` loses 2 of 3 B fills under the engine's own exits
  where the isolated replay had predicted a fill.

## Review round 1 (`/code-review`, 2026-09-04) — 10 findings, all fixed

| # | finding | fix |
|---|---|---|
| 1 | verdict books built over the whole log (discovery + both branches) | `_books()` builds CONFIRMATION-only books; branch-only for `credit030`, whole-portfolio for `a_depth_m4` (W5.2a) |
| 2 | join key included `signal_min`, which shifts when a candidate re-signals the same episode later | `SETUP = (session_date, branch, episode)`; `trades()` asserts one entry per setup |
| 3 | `label()` by date only — partial/standdown sessions after registration fed the bars | `confirmation_dates()` = first 40 countable after registration; everything else after registration is EXCLUDED |
| 4 | knob inside `a_conditions` re-numbered A episodes | gate moved to `a_fires`; `a_conditions` byte-identical to v1 (see above) |
| 5 | byte-identity test appended 16 rows to the committed `baseline_v2/sessions_backtest.csv` on every pytest run | `Session._write_session_row` monkeypatched; `load_sessions` refuses duplicate dates |
| 6 | every REJECT printed off-checkpoint; no terminal handling past 40 | verdicts return `(text, immediate)`; only the three registered immediate paths print off-checkpoint; confirmation capped at 40 |
| 7 | `<=` vs v1 `<` at r30 == 0.0 | strict `<` (see above) |
| 8 | mark cache persisted empty / pre-close pulls forever; `asof` could be an incomplete session | refuse and do not cache a pull that stops > 5 min before the close; `spx_close(asof)` refuses bars that stop before 16:00; frames memoised per run |
| 9 | `--rebuild` `rmtree` on whatever `logging.paper_log` pointed at (could be the baseline ledger) | `registry.py` refuses any log dir that is not `docs/replay/hiro_watch/<name>/`; `rebuild()` re-checks before deleting |
| 10 | `refusals()` kept one reason per setup (first in log order) — 31 vt_broken setups reported as 21 | one row per (setup, reason); `diag_table` shows `other_reasons` |

Also fixed from the review's overflow list: name-keyed dispatch now refuses an unmapped promotable /
diagnostic; `rebuild` takes its day set from the baseline sessions file, not `spx_dir`; the duplicate
guard also reads paper-log banners; `compare.load_log` checks `config_hash == sha256(yaml)`; the
sessions path derives from `logging.sessions_log`; `lb95` resamples every confirmation session (zero-
trade sessions included); `scripts/hiro_engine_v2/config.yaml` == `baseline_v2.yaml` is a test; marks
moved to `~/Dev/central_trade_data/thetadata/spxw_marks/` per the data-sources rule.

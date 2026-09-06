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

## Branch-B knobs (2026-09-05/06)

Added to the clone at v1-equivalent defaults after the Charlie/Brent failure-mode reviews:
`b_enabled`, `b_run_max`, `b_dur_max` (in `_entry_events`, on `b_qualifies`), `late_sticky` (uses the
engine's own `_late_logged_episode`), `credit_b` (executor: booking and the R1.4e invariant pick the
branch's credit). Tests per knob; byte-identity holds. The candidate yamls gained the five lines (hashes
changed, behaviour and tally identical — `configs/README.md` note). `b_pull_min_pts` needed no code.
Diagnostic replays and the 60-cell grid: `knob_results_2026-09-05.md`; none registered yet.

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

## Review round 2 (`/code-review` verification pass on dfb8dc5, 2026-09-04) — 10 findings, all fixed; loop closed

| # | finding | fix |
|---|---|---|
| 1 | `book()` ignored `asof` — an earlier `--asof` counted future cash and marked not-yet-opened bombs | `book()` filters `session_date <= asof` |
| 2 | a_depth expectancy mixed A-only cash with whole-portfolio inventory | expectancy terms use A-only confirmation books (`cbA/bbA`); MTM terms keep the whole-portfolio books (W5.2a) |
| 3 | candidate A trades are not necessarily the "passed" cohort (baseline first-signal r30 at 2 dp vs the per-minute gate) | scored cohort = candidate A trades whose setup is a passed baseline signal; strays reported as "outside the passed cohort, unscored" |
| 4 | settlement demanded a complete session at expiry → a half-day expiry Friday would have stopped every evening's report | settlement uses the last stored close (`require_complete=False`); only `asof` must be complete |
| 5 | terminal verdict re-marked at a moving `asof` after session 40 | books for verdicts pinned at `conf[-1]` once `n_conf >= 40`; printed as `[terminal — books pinned at …]` |
| 6 | REJECT-EXPIRED only reachable through the count-bar branch | every non-PROMOTE/REJECT tail past 40 signals returns REJECT-EXPIRED (wrapping the reason) |
| 7 | `--rebuild` deleted the log dir before discovering an SPX day the baseline lacks | stored SPX days in range must equal the baseline sessions BEFORE any rmtree; compare also refuses candidate-minus-baseline sessions |
| 8 | `a_deep` applied in the price tier, where v1 has no r30 clause | `a_deep = tier.price_a_conditions or (r30 < a_r30_lt)` |
| 9 | the engine logs one short-block reason per setup, so a co-active `flow_veto` was invisible | `flow_veto` mapped; `other_reasons` also read from the diag run's own skip rows |
| 10 | a setup refused early but entered by the baseline later in the episode was scored as knob-attributed | anti-join baseline-entered setups out of the refused population |

Overflow items taken: zero-row SPX parquet → REFUSED; type hints on the verdict/report functions.
Accepted as-is: `BARS["a_depth"]["theta"]` duplicates the yaml knob (asserting equality would couple
compare.py to one candidate's file; the value is frozen in requirements W5.3 alongside); name-keyed
verdict dispatch refuses an unmapped promotable rather than skipping it (loud > silent); registry's
path resolution mirrors `config._expand` for the two keys it needs.

**Loop closed after two rounds** (review-loop discipline: no endless nitpick loops; every finding
either fixed with a test or accepted here in writing). Further defects go through the normal
"found in use → fix → note" path.

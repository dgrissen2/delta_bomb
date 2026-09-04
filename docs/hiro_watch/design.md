# Design — hiro_watch v2 (the clone route)

*v2.0, 2026-09-04, for `requirements.md` v2.0.*

## Layout

```
scripts/hiro_engine/            frozen v1 — untouched
scripts/hiro_engine_v2/         copy of v1 + 4 knobs − live/ops/spikes/parity/register/verify/sweep
  tests/                        v1 tests renamed + test_knobs.py (W0.2 byte-identity, each knob)
scripts/hiro_watch/
  run.py                        the evening command (W3)
  compare.py                    the accounting (W4, W5)
  tests/test_compare.py         fixture-log tests for the joins, LB95, checkpoint guard, book
docs/hiro_watch/configs/        one yaml per candidate (W1) — full copies of config.yaml
docs/replay/hiro_watch/<name>/  paper_log_backtest.csv, sessions_backtest.csv (engine-written)
docs/replay/hiro_watch/marks/   <date>_<expiry>.parquet mark cache (compare-written, pull once)
```

## The clone — exact edits (all line refs = v1)

| v1 file:line | edit in v2 |
|---|---|
| `rules.py:67` | `(c.r30 is not None and c.r30 < 0)` → `(c.r30 is not None and c.r30 <= cfg.num("r6_entries", "a_r30_max"))`. Differs from v1 only at r30 == 0.0 exactly (never observed; noted). |
| `rules.py:149,175` | `row.late_state` → `(row.late_state and self.e6["late_enabled"])` at both uses. |
| `session.py:128-130` | `Vetoes(vt_broken=self.vt_broken and cfg.get("r4_vetoes","vt_broken_enabled"), levels_invalid=(not self.levels.valid) and cfg.get("r4_vetoes","levels_invalid_enabled"), …)`. |
| `chains.py:52-55` | `_sdk_pull_day` and `ChainStore.fetch` raise `RuntimeError("hiro_engine_v2 never fetches chains — run the v1 daily loop")`. |
| `cli.py` | `prog="hiro_engine_v2"`; keep `backtest` + `scorecard`; delete `live`, `verify`, `sweep`, `parity-check`, `register` subcommands and their imports. |
| deleted | `live.py ops/ spike_*.py parity.py register.py verify.py sweep.py summarize.py?` — no: `summarize.py` stays (backtest prints the R13.3 summary through it). |
| `config.yaml` | `baseline_v2.yaml` lives in `docs/hiro_watch/configs/`; the clone's own `config.yaml` is that file too (same bytes), so `python -m hiro_engine_v2 backtest` without `--config` is the baseline. |
| `tests/` | `sed s/hiro_engine/hiro_engine_v2/`; drop tests of deleted modules; add `test_knobs.py`. |

`REPO_ROOT` (`config.py:13`, two parents up) still resolves to the repo root from
`scripts/hiro_engine_v2/`. The frozen pins in the yaml (`control_dataset`, `verification`,
`chains.*_hash`, `r9a_*`) are copied unchanged: they pin data and derivation, not rules, and the
`backtest.py:36-46` interlock passes on the shared chain cache.

## A candidate yaml

A full copy of the engine's `config.yaml` (fail-closed loader needs every section) with:

```yaml
watch:                          # hashed with everything else
  engine: hiro_engine_v2        # or hiro_engine
  registered: "2026-09-04"      # W5.1 firewall date = commit date of this file
  kind: promotable              # or control | diagnostic
logging:
  paper_log: docs/replay/hiro_watch/a_depth_m4/paper_log.csv
  sessions_log: docs/replay/hiro_watch/a_depth_m4/sessions.csv
r6_entries:
  a_r30_max: -4.0               # the one change
```

The engine derives `paper_log_backtest.csv` / `sessions_backtest.csv` from those paths
(`cli.py:53`, `session.py:369`), and stamps sha256(yaml bytes) on every row (`config.py:88`).

## run.py (~70 lines)

```
run.py <date>            for yaml in configs/*.yaml (sorted):
                           refuse if <date> in <log dir>/sessions_backtest.csv
                         refuse if <date> not in baseline sessions_backtest.csv
                         for yaml: subprocess python -m {watch.engine} backtest --day <date> --config yaml
                           non-zero exit → stop, print which candidate, exit 2 (W0.3)
run.py --rebuild NAME    rm -rf log dir; backtest --from <first stored> --to <last stored>
run.py --rebuild all     same for every yaml
```

Baseline sessions = `docs/replay/hiro/sessions_backtest.csv`. Baseline events = the concatenation
of `docs/replay/hiro/paper_log_backtest.csv` and `paper_log_oos_*.csv` (the way v1's log is kept).

## compare.py (~200 lines, pure pandas over the logs)

```
load_log(path) -> DataFrame[EVENT_FIELDS]           refuse duplicate session_date
setup_id = (session_date, branch, signal_min, episode)   the join key across candidates
trades(ev)  -> one row per trade_id: branch, signal_min, entry_min, k1, k2, side, expiry,
               leg1_fill, leg2_fill, outcome_type, pnl_usd, leg_liq_loss_usd, minutes_to_fill
signals(ev) -> one row per baseline `signal` event + r30 parsed from notes (A only)
refusals(ev)-> `skip`/`late_no_entry` rows with reason ∈ {vt_broken, levels_invalid, late, capacity}
book(trades, asof) -> cash, marks (MarkCache), settlements, MTM   (W4.2)
lb95(fills_by_session) -> min(bootstrap_p5, clopper_pearson_lo)    (W4.4)
label(ev, registered) -> DISCOVERY | CONFIRMATION                  (W5.1)
verdict_a_depth / verdict_credit(branch) / status_diag             (W5.3), gated by checkpoint(n)
main: print per-candidate tables; verdict lines only if checkpoint (W5.2)
```

`MarkCache.get(date, expiry)` → `chains._sdk_pull_day(date, expiry)` from **v1** (read-only library
use), written once to `marks/<date>_<expiry>.parquet`. Closing mark = mid at the last minute ≤ 16:00
with a valid two-sided quote on both legs, else `UNMARKED`.

## What is deliberately absent

No shadow harness, no hooks, no WATCH_HASH (CONFIG_HASH is it), no snapshot chain (logs are
engine-written and rebuildable), no lineage files (git), no exception hierarchy (`SystemExit(2)`
with a message), no regime panel beyond what the log already carries, no isolated replays.

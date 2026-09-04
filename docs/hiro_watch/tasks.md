# Tasks — hiro_watch v2 (the clone route)

*v2.0, 2026-09-04. Seven tasks, dependency order. Each ends green before the next. Never edit
`scripts/hiro_engine/`. venv: `~/Dev/virtualenvs/gamma_chaser/bin/python`, run from `scripts/`.*

1. **Clone.** `cp -r scripts/hiro_engine scripts/hiro_engine_v2`; delete `live.py ops/ spike_*.py
   parity.py register.py verify.py sweep.py __pycache__`; `sed` the package name in imports and
   tests; trim `cli.py` to `backtest` + `scorecard`; make `chains.fetch`/`_sdk_pull_day` raise.
   Done: `python -m hiro_engine_v2 backtest --day 2026-08-27` runs and writes under the paths in
   its config (temporarily the v1 paths — fix in task 2 before committing).
2. **Knobs + baseline yaml.** The four knob reads (design table); `docs/hiro_watch/configs/
   baseline_v2.yaml` = v1 `config.yaml` + `watch:` section + knobs at v1 values + its own log paths;
   copy it to `scripts/hiro_engine_v2/config.yaml`. Done: `test_knobs.py::test_baseline_byte_identity`
   — backtest all 16 stored sessions through v2 and assert equality with the concatenated v1 logs
   on every `EVENT_FIELDS` column except `config_hash` (integration-marked). Plus one unit test per
   knob on the v3 quote fixture (A gate blocks at r30 −3.9 / passes at −4.0; each veto/late flag
   off admits the previously blocked B entry).
3. **Candidate yamls.** `credit030.yaml` (engine v1), `a_depth_m4.yaml`, `diag_vt_off.yaml`,
   `diag_levels_off.yaml`, `diag_late_off.yaml`. Each = baseline_v2.yaml with the one change, its
   own log paths, `watch.kind`. Done: each loads through its engine's `load_config` and its sha256
   differs from every other; a `README.md` in `configs/` lists name → hash → change.
4. **run.py.** Per design. Done: `run.py --rebuild all` writes six log dirs for the 16 sessions;
   `run.py 2026-09-02` refuses (already present); a bogus date refuses (baseline lacks it).
5. **compare.py — trades, signals, refusals, joins, LB95, firewall, checkpoint guard.** Done:
   `tests/test_compare.py` on a small hand-written fixture log (two sessions, one A fill, one A
   timeout, one B refused-then-entered under diag) asserts each table; `lb95` on 10/10 → < 1.0 and
   on 0/10 → 0.0; checkpoint guard prints no verdict at n=9, prints at n=10.
6. **compare.py — book.** MarkCache, settle, MTM, W5.4 unmarked deferral. Done: on the 16 stored
   sessions `compare.py` reproduces `branch_accounting_2026-09-03.md` §1 and §7 numbers (baseline
   29/16 −$1,050; credit030 +$320 with 13/13 A fills held); the 16-bomb inventory marks agree with
   §5 within quote noise (report the diff).
7. **Docs + RUNBOOK line + commit.** Add the evening step to `docs/hiro_engine/RUNBOOK.md`
   ("after the v1 backtest: `python hiro_watch/run.py <date>`; `compare.py` when you want the
   table"); STATUS.md → "built, backfilled, first confirmation session = next capture"; commit the
   six yamls with the registration date = commit date. Then `/code-review`.

**Review gate:** `/code-review` on the whole diff after task 7. Findings fixed or explicitly
accepted in `build_notes.md`.

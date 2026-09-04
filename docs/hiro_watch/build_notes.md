# Build notes — hiro_watch v2 (2026-09-04)

Decisions taken while building that are not in the spec, and why.

- **`r30 <= a_r30_max` vs v1's `r30 < 0`.** Differ only at r30 == 0.0 exactly (never observed in
  16 sessions; W0.2 byte-identity holds). Chosen so `-4.0` reads "at least 4 $B negative".
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

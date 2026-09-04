# hiro_watch candidates — registered 2026-09-04 (W0: never edit; a change is a new file)

| name | engine | kind | CONFIG_HASH | change |
|---|---|---|---|---|
| `a_depth_m4` | hiro_engine_v2 | promotable | `7338f8fb17e8…` | r6_entries.a_r30_max 0.0 -> -4.0 (Branch A only when r30 <= -4 $B) |
| `baseline_v2` | hiro_engine_v2 | control | `97fdcccd0b23…` | none — v1 rules with the four knobs at v1-equivalent values (W0.2 byte-identity control) |
| `credit030` | hiro_engine | promotable | `da90bc59d1fc…` | r1v3_limits.credit 0.10 -> 0.30 (both branches; read per branch off the log) |
| `diag_late_off` | hiro_engine_v2 | diagnostic | `06c2655654cd…` | r6_entries.late_enabled true -> false (R6.3 suppression off; never promoted) |
| `diag_levels_off` | hiro_engine_v2 | diagnostic | `73bd8e022f2c…` | r4_vetoes.levels_invalid_enabled true -> false (R4.2 short-block off; never promoted) |
| `diag_vt_off` | hiro_engine_v2 | diagnostic | `a6fa6bddcf79…` | r4_vetoes.vt_broken_enabled true -> false (R4.1 short-block off; never promoted) |

Each file is a full copy of the engine config (the loader is fail-closed) with ONE rule change plus its own
`logging` paths and the `watch:` section. Run with `python -m <engine> backtest --day <date> --config <file>`;
`scripts/hiro_watch/run.py <date>` does that for all of them.

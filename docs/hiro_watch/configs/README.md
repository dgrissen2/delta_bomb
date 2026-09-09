# hiro_watch candidates — committed 2026-09-04, registered (last session inspected) 2026-09-02 (W0: never edit; a change is a new file)

| name | engine | kind | CONFIG_HASH | change |
|---|---|---|---|---|
| `a_depth_m4` | hiro_engine_v2 | promotable | `5cec98f771bf…` | r6_entries.a_r30_lt 0.0 -> -4.0 (Branch A signal only when r30 < -4 $B) |
| `a2_pull8_c30` | hiro_engine_v2 | promotable | `c1de88368295…` | the pick with the reviewers' B filter (registered 2026-09-08): a_r30_lt −2.0 + b_pull_min_pts 3 -> 8 (b_run_max stays v1) + credit (A) 0.30; differs from `a2_size1_c30` in the B filter ONLY |
| `a2_size1_c30` | hiro_engine_v2 | promotable | `4c7de67e412a…` | three-knob pick (registered 2026-09-04): a_r30_lt 0.0 -> -2.0 + b_run_max 1e9 -> 1.0 + credit (A) 0.10 -> 0.30; credit_b stays 0.10 |
| `baseline_v2` | hiro_engine_v2 | control | `b1a4fa6d001c…` | none — v1 rules with the four knobs at v1-equivalent values (W0.2 byte-identity control) |
| `credit030` | hiro_engine | promotable | `cbc2a005e82a…` | r1v3_limits.credit 0.10 -> 0.30 (both branches; read per branch off the log) |
| `diag_late_off` | hiro_engine_v2 | diagnostic | `d4108e4b3904…` | r6_entries.late_enabled true -> false (R6.3 suppression off; never promoted) |
| `diag_levels_off` | hiro_engine_v2 | diagnostic | `d6cc1c7f3405…` | r4_vetoes.levels_invalid_enabled true -> false (R4.2 short-block off; never promoted) |
| `diag_vt_off` | hiro_engine_v2 | diagnostic | `60d425288b6d…` | r4_vetoes.vt_broken_enabled true -> false (R4.1 short-block off; never promoted) |

**Registration note (2026-09-08; owner's choice confirmed 2026-09-09):** `a2_size1_c30` is the owner's higher-N pick from `knob_results_2026-09-05.md`; registered 2026-09-04 (last session inspected when it was defined), first confirmation session 2026-09-08. It bundles THREE knobs — the singles (`a_depth_m2`, `b_size1`) are not registered, so confirmation on this candidate cannot attribute earnings to one knob. `a2_pull8_c30` (registered 2026-09-09, firewall 2026-09-08) is the same candidate with pull30 ≥ 8 in place of run ≤ 1.0: every A trade is shared, so any divergence between the two logs is the B filter — the pair separates B-SIZE from B-PULL under the `portfolio` bar.

**Hash note (2026-09-06):** five Branch-B knobs were added to the v2 schema at v1-equivalent values
(`late_sticky`, `b_enabled`, `b_run_max`, `b_dur_max`, `credit_b`). Every yaml gained exactly those five lines
and nothing else; hashes changed, behaviour did not (byte-identity test; tally identical to the dollar).
Registration date unchanged (2026-09-02).

Each file is a full copy of the engine config (the loader is fail-closed) with ONE rule change plus its own
`logging` paths (must be `docs/replay/hiro_watch/<name>/…` — `registry.py` refuses anything else) and the
`watch:` section. Run with `python -m <engine> backtest --day <date> --config <file>`;
`scripts/hiro_watch/run.py <date>` does that for all of them. `compare.py` refuses a log whose
`config_hash` is not the sha256 of the yaml as it stands — editing a yaml after its log exists is detected.

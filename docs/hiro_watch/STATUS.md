# hiro_watch — STATUS (2026-09-04)

Single page that says exactly where the WATCH program is and what happens next. Update this file
whenever the state changes; it is the first thing to read after a context reset.

## Where we are — DECIDED 2026-09-04: clone route, build approved

The shadow-harness spec (requirements v1.2a / design v1.3 / tasks v1.2, ~1,180 lines, 1,800 lines
of code implied) was audited for over-engineering by two independent architects
(`simplicity_audit_architect_2026-09-04.md`, `simplicity_audit_codex_2026-09-04.md`): both said
over-engineered. The owner then asked why not clone the engine and modify the clone; the architect's
answer (`decision_clone_2026-09-04.md`) is that the engine's existing `--config` override, per-config
log paths and CONFIG_HASH stamping already give every candidate its own frozen identity and ledger,
so the whole program is ~250 new lines and 3 concepts:

1. **A candidate is a yaml** under `docs/hiro_watch/configs/`; its CONFIG_HASH on every log row is
   its registration; committed before its first confirmation session; never edited (a change is a
   new file).
2. **`scripts/hiro_engine_v2/`** is a copy of the frozen engine with four config knobs
   (`a_r30_max`, `vt_broken_enabled`, `levels_invalid_enabled`, `late_enabled`) and no live/ops
   code. At v1-equivalent knob values it must reproduce v1's log byte-for-byte (except
   `config_hash`) — checked once, before any candidate exists.
3. **`scripts/hiro_watch/compare.py`** reads the N candidate logs beside v1's, joins on setup,
   marks open bombs, prints per-candidate accounting and — only at checkpoints 10/20/30/40
   confirmation sessions — the verdict lines.

The old spec and its reviews were removed from the tree in this commit (history: `90b1d24`,
`5515402`). New slim spec: `requirements.md`, `design.md`, `tasks.md` (this directory), written
next; then build; then `/code-review`.

## Standing constraints that bind this program

- Never edit `scripts/hiro_engine/`; never refresh the 8 frozen control days; never point the HIRO
  backfill `--force` at the store (staging → ingest only).
- HIRO `stock_price` and any SpotGamma `Ref Px` are verification-only, never a price source.
- The daily capture loop continues regardless — vendor retention is ~5 sessions; a missed capture
  is permanent data loss. Next session to capture: 2026-09-03.

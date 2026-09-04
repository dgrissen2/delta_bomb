# hiro_watch — STATUS (2026-09-04)

Single page that says exactly where the WATCH program is and what happens next. Update this file
whenever the state changes; it is the first thing to read after a context reset.

## Where we are — BUILT 2026-09-04, backfilled, `/code-review` round 1 applied (10/10 fixed)

| piece | where | size |
|---|---|---|
| clone | `scripts/hiro_engine_v2/` | v1 minus live/ops/spikes/parity/register/verify/sweep; +4 knobs (≈10 edited lines); 140 tests green incl. W0.2 byte-identity over the 16 stored sessions |
| candidates | `docs/hiro_watch/configs/*.yaml` (+ `README.md` with hashes) | 6 files: `baseline_v2` (control), `credit030` (v1 engine), `a_depth_m4`, `diag_vt_off`, `diag_levels_off`, `diag_late_off` |
| evening command | `scripts/hiro_watch/run.py` | 109 lines |
| registry + accounting | `scripts/hiro_watch/registry.py`, `compare.py` | validated candidate list; accounting; 15 tests |
| outputs | `docs/replay/hiro_watch/<name>/` (engine-written logs); marks in `~/Dev/central_trade_data/thetadata/spxw_marks/` | rebuildable |
| spec | `requirements.md` v2.0, `design.md` v2.0, `tasks.md` v2.0 | 250 lines total |

Registration date for all six candidates: **2026-09-04** (the yamls' `watch.registered`; commit
date). Every stored session (2026-08-12 → 09-02) is DISCOVERY. First CONFIRMATION session = the
next capture (2026-09-03 onward). Checkpoints at 10/20/30/40 countable confirmation sessions.

### Backfill result on the 16 discovery sessions (asof 2026-09-02, marks pulled)

| candidate | A trades/bombs | B trades/bombs | cash | inventory | MTM | note |
|---|---|---|---|---|---|---|
| baseline (v1 log) | 22/13 | 7/3 | −1,050 | +1,265 | **+215** | matches `branch_accounting_2026-09-03.md` §1/§5/§6 exactly |
| `baseline_v2` | 22/13 | 7/3 | −1,050 | +1,265 | +215 | byte-identical to v1 except `config_hash` (W0.2) |
| `credit030` | 22/13 | 7/**1** | −690 | +1,170 | +480 | A: 13/13 fills held; **B: 2 of 3 fills LOST** in the portfolio replay (08-12 ep4, 08-25 ep1) — the isolated replay in accounting §7 had said 08-25 fills at +34 min; the engine's own exits got there first. Charlie's portfolio-vs-isolated point, demonstrated on discovery data. |
| `a_depth_m4` | 5/5 | 10/3 | −570 | +530 | −40 | A 5-for-5 as in §4; B gets the freed capacity (10 trades vs 7) and loses it back. Θ ladder: −1 0.58/12, −2 0.71/7, −3 0.83/6, −4 1.00/5, −5 1.00/2. |
| `diag_late_off` | 22/13 | 7/3 | −1,030 | +1,315 | +285 | 14 LATE episodes (12 also vt-blocked), 2 entered, 1 bomb |
| `diag_levels_off` | 22/13 | 9/3 | −1,220 | +1,265 | +45 | 2 levels_invalid episodes, both entered, 0 bombs, −$170 |
| `diag_vt_off` | 22/13 | 13/7 | −1,370 | +1,460 | +90 | 31 vt_broken episodes (11 also late-blocked), 6 entered, 4 bombs, −$320 cash |

None of this is evidence (all discovery). It is the reference table the confirmation columns will
sit beside.

## What's next

1. Daily loop gains one step (RUNBOOK): after the v1 backtest, `hiro_watch/run.py <date>`;
   `compare.py` whenever you want the table.
2. Next capture: 2026-09-03 (the first confirmation session).
3. Review round 2 (`/code-review` on the fix diff) — optional; round 1's 10 findings are all fixed
   and recorded in `build_notes.md`.

## Standing constraints that bind this program

- Never edit `scripts/hiro_engine/`; never refresh the 8 frozen control days; never point the HIRO
  backfill `--force` at the store (staging → ingest only).
- HIRO `stock_price` and any SpotGamma `Ref Px` are verification-only, never a price source.
- The daily capture loop continues regardless — vendor retention is ~5 sessions; a missed capture
  is permanent data loss. Next session to capture: 2026-09-03.

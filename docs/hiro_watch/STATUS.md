# hiro_watch — STATUS (2026-09-04)

Single page that says exactly where the WATCH program is and what happens next. Update this file
whenever the state changes; it is the first thing to read after a context reset.

## Where we are

**Specified, reviewed, NOT BUILT.** Nothing exists under `scripts/hiro_watch/`. The three
documents are complete and each closed two rounds of `/codex-plan-review`:

| Doc | Version | Lines | Reviewer | Rounds | Findings |
|---|---|---|---|---|---|
| `requirements.md` | v1.2a | 465 | Charlie McElligott + generic | 2 | 25 + 27, all applied |
| `design.md` | v1.3 | 490 | Architect + generic | 2 | 28 + 31, all applied |
| `tasks.md` | v1.2 | 223 | CIO (clarity) + Architect | 1 each | 6 + 8, all applied |

Review transcripts: `requirements_review_2026-09-03.md`, `design_review_2026-09-03.md`,
`tasks_review_2026-09-03.md`. Commit lineage: `dc4023c` → … → `90b1d24` (note: `4a9d1bf` carried
only the tasks review file — its message overstated; the real design v1.3 / tasks v1.2 changes
are in `90b1d24`).

## What the WATCH is (one paragraph)

A read-only shadow program that runs beside the frozen engine (`CONFIG_HASH 80c3a41026c8…`) and
scores Charlie's pre-registered candidates on every new OOS session without touching the engine:
**A-DEPTH** (Branch A only when r30 ≤ −4 $B; Θ ladder −1…−5 diagnostic only), **CREDIT**
(0.10 / 0.20 / 0.30, branch-isolated; 0.30 is the leading candidate — `branch_accounting_2026-09-03.md`
§7: +$320, zero A fills lost), **B-REFUSED** (what B would have done past the vt_broken /
levels_invalid / LATE refusals, sole-blocker attribution, never promoted), a contemporaneous regime
panel per signal, a marked book with settlement and a shock grid, a discovery (≤ 2026-09-02) /
confirmation firewall, and verdicts only at confirmation-session checkpoints 10/20/30/40.

## Design principle that everything hangs on

**Run the engine, never re-implement it.** Each session is replayed in memory through
`Session → RuleEngine → Executor` with the candidate injected via three subclass hooks
(`ShadowRuleEngine._entry_events` post-filter, `ShadowExecutor.credit` property,
`ShadowSession._vetoes` / `late_state` override), a `MemoryLog` instead of the CSV log, and an
engine-identity guard that hashes `scripts/hiro_engine/` before and after every run.

## Accepted residuals (not defects, decided)

- W10.4 fill realism: minute close-NBBO marketability is the fill model (validated 29/29 against
  the engine's actual outcomes); no queue/partial-fill model.
- `code_hash` is recorded per snapshot manifest, not inside `WATCH_HASH` (definitions vs lineage).
- Isolated per-trade replays capped (`MAX_ISOLATED`) and diagnostic only; verdicts come from
  portfolio (sequential) replays — Charlie's round-2 point.
- Build acceptance ≠ investment approval: task 12 is a separate governance gate (CIO's point).

## Simplicity audit — DONE 2026-09-04: verdict OVER-ENGINEERED (both reviewers, independently)

Two audits ran in parallel on the whole trio with the same question ("what is weight vs
load-bearing for the pre-registration discipline?"):

- `simplicity_audit_architect_2026-09-04.md` — in-session architect, read the engine source.
  Verdict: over-engineered, ~85% confidence. ~60% of mechanisms are weight.
- `simplicity_audit_codex_2026-09-04.md` — `/codex-plan-review`, architect persona + generic.
  Verdict: FAIL on over-engineering (8 + 11 findings, 13 synthesized, 8 HIGH).

Where they agree (cut): cumulative snapshot chains / `current` / `prev_snapshot` / orphan GC;
`.code` lineage + `rebind` + `active.txt` / `--supersede`; 14-class exception hierarchy;
isolated per-trade replays + `MAX_ISOLATED` + `entry_filter`; the diagnostic CREDIT layer
(`ladder.py` re-implements fill physics); dual-source settlement + pinning + reconciliation;
mark-row shas / `MarkTampered`; `single_writer_lock`; holiday CSV; scale monitor; 9-value
eligibility enum; per-run engine-artifact hashing (becomes a test); `constants.py`; 13 modules →
5-8. Both put the honest size at ~500-850 production lines + ~400 tests, vs ~1,800.

Where they agree (keep): WATCH_HASH over canonical JSON; discovery/confirmation firewall;
checkpoint-only verdicts with the registered bars; portfolio (sequential) replay as the verdict
basis; per-branch credit; sole-blocker attribution; UNMARKED as a first-class state; LB95 with
the Clopper-Pearson floor; baseline-equals-engine-log runtime check; input shas + byte-identical
re-run; per-session atomic directory.

Two engine-source facts the audit surfaced (verified): (1) a simpler injection point exists —
one row pre-transform in `RuleEngine.evaluate` (`session.py:272`, `rules.py:136-150`) covers
A-DEPTH, LATE-off, vt_broken-off, levels_invalid-off; the design's `_entry_events` post-filter,
gated-episode memory and `_vetoes` override are unnecessary. Two silencers are mandatory:
`MemoryLog`, and a no-op `_write_session_row` (`Session.finish()` writes `sessions_backtest.csv`
unconditionally, `session.py:365-381`). (2) `leg_liq_loss_usd` is updated EVERY bar
(`executor.py:207,266`), so the spec's "recompute MAE from chains" clause (W2.6 / design §5) is
wrong — use the engine's field.

Codex also found three contract defects independent of size: the `attach_outcomes` join on
`trade_id` before it exists; `rebind` vs `require_code_match` contradiction; CREDIT's `leg1_fill`
dependency violating the W2.2-only classifier firewall as written. All three vanish in the
minimal design.

Decision pending from the user: rewrite the trio as v2 (target: requirements ~180 lines, design
~150, tasks 7 tasks) on the minimal design, one review round, then go/no-go on build.

## What's next, in order

1. Simplicity audit (above) → apply → re-review once → commit.
2. User's explicit **go**.
3. Build tasks 1–11 per `tasks.md`; review gates (`/red-team-auditor` + architect `/codex-review`)
   after tasks 4 and 9; user confirms the registration payload at task 11 before `watch register`
   freezes `WATCH_HASH`.
4. Backfill the 16 stored sessions (discovery), then run `watch run <date>` every evening after the
   standing capture loop (capture → identity check → ingest → SPX bars → chains → engine backtest →
   watch).
5. Task 12 investment gate — only at a checkpoint, only with the CIO.

## Standing constraints that bind this program

- Never edit `scripts/hiro_engine/`; never refresh the 8 frozen control days; never point the HIRO
  backfill `--force` at the store (staging → ingest only).
- HIRO `stock_price` and any SpotGamma `Ref Px` are verification-only, never a price source.
- The daily capture loop continues regardless of the WATCH's build state — vendor retention is
  ~5 sessions; a missed capture is permanent data loss. Next session to capture: 2026-09-03.

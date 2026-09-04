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

## Open question — being answered now

**Is this over-engineered?** The user wants the WATCH SIMPLE and easily understood. The next
action is a simplicity audit of all four documents (requirements / design / tasks, plus this
status) by the architect in-session and, in parallel, through `/codex-plan-review`, asking one
question: what can be cut or collapsed without losing the pre-registration discipline (frozen
definitions, firewall, checkpoints, no engine edits)? Expected outcome: a v2 of the trio that is
materially shorter, or an explicit finding that the size is warranted. Nothing is built until that
audit lands AND the user says go.

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

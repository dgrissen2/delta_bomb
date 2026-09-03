# Tasks (spec) review — hiro_watch (2026-09-03)

## CIO lens (clarity for a junior engineer + decision authority) — FAIL 6 → governance gate added as task 12; contract items applied in tasks v1.2

## Codex Plan Review — Verdict: FAIL (7 findings)

| # | Finding | Severity | Dimension | Details |
|---|---------|----------|-----------|---------|
| 1 | Commit protocol contradicts rollback guarantee | Critical | Internal consistency | Ground rule 3 requires the ledger to remain byte-for-byte unchanged after any exception, but task 9 explicitly permits a crash after the snapshot rename to leave an orphan until the next run. The plan must either narrow the guarantee to the reachable snapshot chain or specify a transaction/recovery protocol that restores the directory immediately. |
| 2 | Date CLI grammar is internally inconsistent | High | Logic errors | Task 1 calls `register`, `backfill`, `<date>`, `report`, `rebind`, and `rebuild` argparse subcommands, while task 10 requires `watch <date>`. A variable date cannot be an argparse subcommand alongside fixed commands without an explicit parsing strategy. Define whether the date is a positional alternative, a `run <date>` argument, or another unambiguous form. |
| 3 | Configuration payload omits mandated numeric constants | High | Data contracts | The “no numbers in code” rule says every threshold, count, window, multiplier, and seed must come from registration, but task 2 does not register constants later required by the plan, including the task 8 payoff clamp `0..5`, contract multiplier `100`, closing window `[L−3,L]`, and task 10 runtime threshold `120 s`. The rule and payload contract cannot both be satisfied as written. |
| 4 | Input resolver lacks required registration context | High | Dependencies | `resolve(cfg, date)` must reject a session lacking a disposition row for “the registration’s engine hash,” yet neither `reg` nor a watch/engine hash is part of its declared inputs. The disposition store and reader are also not defined until the ledger work in task 9, despite production resolution being built in task 3. |
| 5 | Refusal test contract references an undefined fourth type | Medium | Internal consistency | Task 3 defines three normal refusal exceptions—`MissingInputs`, `Unverified`, and `MissingSession`—then requires tests for “all four refusal types plus `InputTampered`.” The fourth refusal type, its triggering condition, and its precedence are absent. |
| 6 | Calendar behavior is undefined outside 2026–2027 | High | Edge cases | `calendar_gaps(reg, upto)` has no bounded `upto`, but its authoritative holiday file covers only 2026–2027. Dates beyond that range would incorrectly classify exchange holidays as missing sessions. The plan needs a supported range check, calendar-extension process, or authoritative fallback. |
| 7 | Critical integration assertions lack deterministic pass criteria | High | Test adequacy | The real-book test permits `$1,265` “within quote-quality exclusions” without defining a tolerance or exact exclusion calculation, while the runtime test requires `<120 s` without a hardware/environment baseline. Both can produce subjective or flaky outcomes and therefore cannot serve as reliable completion gates. |

---

## Codex Plan Review — Chief Investment Officer (Decision Authority)
**Verdict**: FAIL (6 findings)

| # | Finding | Severity | Dimension | Details |
|---|---------|----------|-----------|---------|
| 1 | Investment approval lacks a minimum confirmation milestone | Critical | Testability | Task 11 proceeds from 16 discovery sessions to one confirmation session, followed by sign-off checks focused on software correctness. The plan must distinguish build acceptance from investment approval and require the registered minimum sample, completed checkpoints, and explicit performance/risk criteria before promotion. |
| 2 | No incremental-value or ablation test for proposed gates | High | Signal-to-Noise | Replay fidelity proves that the implementation reproduces prior behavior; it does not prove that `r30`, health, late-state, `vt_broken`, refusal, or credit gates improve outcomes. Each gate needs registered baseline-versus-gated and leave-one-gate-out evaluation with acceptance criteria. |
| 3 | Thresholds are frozen without calibration evidence | High | Empirical Calibration | Numerous thresholds and policy values are copied into registration, but the plan never records their empirical distributions, sensitivity ranges, selection method, or expected stability. Registration immutability preserves arbitrary choices unless calibration artifacts and threshold-robustness tests are required before registration. |
| 4 | Subjective/model-derived fields can affect structural decisions without classification | High | Implementability | Candidate classifiers, health mapping, setup categories, refusal precedence, and state overrides influence eligibility or attribution, yet the plan does not classify each input as QUANT, QUANT-BOUNDED, or SUBJ or document uncertainty and fallback behavior. Any model- or judgment-derived field must be barred from veto authority unless reproducibility and historical reconstruction are demonstrated. |
| 5 | Multiple-testing and discovery contamination are unmanaged | High | Statistical Governance | The plan evaluates ladders, candidate variants, credit variants, refusal tables, shocks, and several verdict paths on the same small discovery history. Fixed seeds and confidence bounds do not control selection bias. The plan needs a frozen hypothesis family, multiplicity policy, untouched confirmation set, and rules preventing post-discovery variant selection. |
| 6 | Program-level risk and scaling limits are reporting-only | Medium | System-Level Coherence | The book and shock grid calculate exposures, but no registered limits govern aggregate capital, concentration, correlated candidates, maximum loss, drawdown, stale/unmarked inventory, or escalation. A scalable program requires deterministic risk limits and explicit behavior when marks or data quality deteriorate, not merely report output. |

---

## Codex Plan Review — Panel Synthesis

| # | Finding | Severity | Dimension | Flagged By | Confidence |
|---|---------|----------|-----------|------------|------------|
| 1 | Commit protocol contradicts the byte-for-byte rollback guarantee by permitting an orphaned snapshot after a crash. | Critical | Internal consistency | Generic | High |
| 2 | Investment approval lacks a minimum confirmation milestone distinct from software build acceptance. | Critical | Testability | Chief Investment Officer | High |
| 3 | Date CLI grammar ambiguously mixes fixed argparse subcommands with a variable `<date>` command. | High | Logic errors | Generic | High |
| 4 | Registration configuration omits numeric constants mandated by the “no numbers in code” rule. | High | Data contracts | Generic | High |
| 5 | The input resolver cannot validate the registration’s engine hash because registration context and the required disposition store are unavailable at that stage. | High | Dependencies | Generic | High |
| 6 | Calendar behavior is undefined beyond the authoritative holiday file’s 2026–2027 coverage. | High | Edge cases | Generic | High |
| 7 | Real-book and runtime integration assertions lack deterministic tolerances and environment baselines. | High | Test adequacy | Generic | High |
| 8 | Proposed gates lack baseline-versus-gated and leave-one-gate-out tests demonstrating incremental value. | High | Signal-to-Noise | Chief Investment Officer | High |
| 9 | Thresholds are frozen without calibration artifacts, empirical distributions, sensitivity ranges, selection methods, or robustness tests. | High | Empirical Calibration | Chief Investment Officer | High |
| 10 | Subjective or model-derived fields can affect structural decisions without classification, uncertainty handling, reproducibility, or reconstruction requirements. | High | Implementability | Chief Investment Officer | High |
| 11 | Multiple testing and discovery contamination are unmanaged across variants evaluated on the same small discovery history. | High | Statistical Governance | Chief Investment Officer | High |
| 12 | The refusal-test contract requires an undefined fourth normal refusal type. | Medium | Internal consistency | Generic | High |
| 13 | Program-level risk and scaling limits are reporting-only, with no deterministic limits or deterioration behavior. | Medium | System-Level Coherence | Chief Investment Officer | High |

## Architect lens — FAIL 8 → all applied in tasks v1.2 / design v1.3

## Codex Plan Review — Verdict: FAIL (12 findings)

| # | Finding | Severity | Dimension | Details |
|---|---------|----------|-----------|---------|
| 1 | Registration and rebind guards contradict each other | HIGH | Logic errors | Design §1 says initial registration has no code-match guard and `rebind` must run without one. Design §12 instead requires every command to call `require_code_match()` and explicitly says `rebind` begins with it. That makes recovery from a code mismatch—and potentially first registration—unreachable. |
| 2 | Main loop uses dependencies before constructing them | HIGH | Dependencies | `engine_identity_guard(cfg, chains, reg)` is called before `chains = ChainStore()`, and the pseudocode never loads `cfg`. The declared execution order cannot run as written. |
| 3 | Outcome attachment requires a field it is supposed to create | HIGH | Data contracts | `attach_outcomes` says it joins on `(candidate_id, session_date, trade_id)` while also adding `trade_id` to the panel. Before attachment, panel rows are identified by branch, signal minute, and episode, so the proposed join is circular. |
| 4 | Candidate identity is lost during trade extraction | HIGH | Data contracts | `trades_from_events(events_df)` must produce candidate-keyed trades, but `events_df` is specified as exactly `EVENT_FIELDS` and candidate identity lives only on `ShadowRun`. Calls passing only `r.events_df` cannot reliably populate `candidate_id`, risking collisions across candidate books. |
| 5 | `b_refused` schema cannot represent its planned rows | HIGH | Data contracts | The data model restricts `table` to `{vt,levels,late}` and `layer` to `{portfolio,isolated}`, while the plan requires `table=capacity` and `layer=reported`. Its key `(table, setup_id)` also collides when both portfolio and isolated rows exist for one setup; `layer` must be part of the key. |
| 6 | Atomicity guarantee conflicts with the commit design | HIGH | Edge cases | The plan promises that any failure leaves the ledger exactly unchanged, but a crash after snapshot rename leaves an orphan directory, and mark-cache files are persisted before snapshot commit. Either these writes must be transactional/rolled back or the guarantee must explicitly exclude caches and unreachable snapshots. |
| 7 | Pinned settlement cannot be recovered on its first settlement snapshot | HIGH | Logic errors | Rebuild is told to obtain pinned settlement data from the prior snapshot. On the date a bomb first settles, that row does not exist in the prior snapshot; if an EOD source appears later, rebuilding can select a different value. The target snapshot’s pinned settlement must be supplied as replay input. |
| 8 | Holiday source and lineage are inconsistent | HIGH | Internal consistency | Design §2 defines gaps using holidays from `event_calendar.csv`; the tasks and ledger section use `nyse_holidays.csv`. Both files are inputs, yet only an ambiguous `calendar_sha` is stamped. This can produce inconsistent chronology decisions and unverifiable lineage. |
| 9 | Required exceptions are absent from the declared hierarchy | MEDIUM | Data contracts | `InputTampered`, `EngineIdentityError`, `MarkTampered`, and `LedgerLocked` are required later but omitted from the “exact” `WatchError` hierarchy. Their inheritance and CLI handling are therefore undefined. |
| 10 | `mark_sha` has no valid multi-source representation | MEDIUM | Data contracts | Every `book` row must carry `mark_sha`, but one candidate book can use several expiry-specific mark files—or no mark file. The plan does not define whether this field is a list, map, aggregate hash, or nullable value. |
| 11 | Numeric-constant rules contradict implementation instructions | MEDIUM | Internal consistency | The blanket rule that every number must come from registration conflicts with the specified `Policy` 0.10 defaults, module-level `MAX_ISOLATED = 20`, fixed five-point payoff clamp, and `1e-9` comparison tolerance. The plan must distinguish registered policy parameters from structural/numerical constants. |
| 12 | Tests conflict with behavior and omit critical failure paths | HIGH | Test adequacy | The testing section says NaN `r30` is “untouched,” while the design and task acceptance criteria require it to be gated and skipped. Coverage also omits the circular outcome join, candidate-ID propagation, refused-table key uniqueness, multi-expiry mark lineage, first-settlement rebuild, and safe handling of corrupt `current`/`prev_snapshot` chains before orphan deletion. |

---

## Codex Plan Review — Architect
**Verdict**: FAIL (8 findings)

| # | Finding | Severity | Dimension | Details |
|---|---------|----------|-----------|---------|
| 1 | Main-loop dependency order is invalid | High | Feasibility | The pseudocode calls `engine_identity_guard(cfg, chains, reg)` before either `cfg` or `chains` is initialized. It also visually exits the writer lock after the guard despite claiming the remaining work stays inside it. Task 10 needs an executable, unambiguous orchestration contract. |
| 2 | `rebind` has contradictory guard semantics | High | Lifecycle | Design §1 says `rebind` must run without `require_code_match()` because it exists to recover from a mismatch; §12 says it begins with that guard. The latter makes rebind unusable precisely when needed. |
| 3 | `b_refused` cannot represent its promised rows | High | Data contract | Its declared key `(table, setup_id)` collides when both portfolio and isolated rows exist for one setup; `layer` must be part of the key. Its table enum also excludes `capacity`, although capacity rows are required. |
| 4 | Calendar authority and lineage are inconsistent | High | Integration | Inputs declare `event_calendar.csv`, one `calendar_gaps` definition uses that file, while other sections and tasks require `nyse_holidays.csv`. Only the latter is registered by hash. The plan must define one authoritative holiday source or an explicit mapping and separate hashes. |
| 5 | Historical settlement verification is undefined | High | Reproducibility | Rebuild says pinned settlements come from the prior snapshot, but a settlement first created in the snapshot being verified is absent from its predecessor. If the external EOD source later changes, the plan does not define how that snapshot can reproduce its original pinned value. |
| 6 | Shared mark-cache trust contract is incomplete | High | Provenance | The cache is global across watch registrations and keyed only by date/expiry. “Re-hashed on read” does not identify the trusted expected digest when a new registration reuses an existing file. Define cache ownership/versioning and a durable sidecar or manifest lookup used for verification. |
| 7 | Required exception contract is internally incomplete | Medium | Error handling | The canonical hierarchy omits `InputTampered`, `EngineIdentityError`, `MarkTampered`, and `LedgerLocked`, although later tasks require raising them. Task 1 cannot implement the hierarchy “exactly as design” and still satisfy those tasks. |
| 8 | Registered frozen-manifest identity is not enforced | High | Contract fidelity | Registration stores `frozen_manifest_hash`, but `engine_identity_guard` only compares the config hash and calls `chains.verify_frozen(cfg)`. It must explicitly compare the current manifest digest with the registered digest; otherwise a different internally valid frozen manifest can run under the same watch identity. |

---

## Codex Plan Review — Panel Synthesis

| # | Finding | Severity | Dimension | Flagged By | Confidence |
|---|---------|----------|-----------|------------|------------|
| 1 | Registration and `rebind` guards contradict each other, making mismatch recovery—and potentially initial registration—unreachable. | HIGH | Lifecycle / Logic errors | Generic, Architect | High |
| 2 | Main-loop orchestration uses `cfg` and `chains` before initialization and leaves lock scope ambiguous. | HIGH | Dependencies / Feasibility | Generic, Architect | High |
| 3 | Outcome attachment joins on `trade_id` while also being responsible for creating it, producing a circular data contract. | HIGH | Data contracts | Generic | Medium |
| 4 | Candidate identity is lost when candidate-keyed trades are extracted from an `events_df` that lacks `candidate_id`. | HIGH | Data contracts | Generic | Medium |
| 5 | `b_refused` cannot represent planned rows: its enums exclude `capacity` and `reported`, and its key omits `layer`, causing collisions. | HIGH | Data contracts | Generic, Architect | High |
| 6 | The claimed atomicity guarantee conflicts with pre-commit cache writes and orphan snapshots left by crashes after rename. | HIGH | Edge cases | Generic | Medium |
| 7 | First-time pinned settlements cannot be reproduced from the prior snapshot because they do not yet exist there. | HIGH | Reproducibility / Logic errors | Generic, Architect | High |
| 8 | Holiday authority and lineage are inconsistent between `event_calendar.csv` and `nyse_holidays.csv`, with insufficient hash attribution. | HIGH | Integration / Internal consistency | Generic, Architect | High |
| 9 | The declared exception hierarchy omits required `InputTampered`, `EngineIdentityError`, `MarkTampered`, and `LedgerLocked` exceptions. | MEDIUM | Error handling / Data contracts | Generic, Architect | High |
| 10 | `mark_sha` has no defined representation for books using multiple expiry-specific mark files or no mark file. | MEDIUM | Data contracts | Generic | Medium |
| 11 | The blanket registration rule for numeric constants conflicts with hard-coded policy defaults, structural limits, payoff clamps, and numerical tolerances. | MEDIUM | Internal consistency | Generic | Medium |
| 12 | Tests contradict required NaN `r30` gating behavior and omit several critical data-contract, lineage, rebuild, and corrupt-chain failure paths. | HIGH | Test adequacy | Generic | Medium |
| 13 | The shared mark-cache trust contract is incomplete because globally reused files lack a durable, registration-specific expected digest or ownership/versioning model. | HIGH | Provenance | Architect | Medium |
| 14 | Registered `frozen_manifest_hash` identity is not explicitly compared by `engine_identity_guard`, allowing a different internally valid manifest under the same watch identity. | HIGH | Contract fidelity | Architect | Medium |

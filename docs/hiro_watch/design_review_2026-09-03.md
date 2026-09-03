# Design review — hiro_watch (2026-09-03)

## Round 1 (v1.0) — FAIL 20 generic / 8 architect → all applied in v1.1

## Codex Plan Review — Verdict: FAIL (20 findings)

| # | Finding | Severity | Dimension | Details |
|---|---------|----------|-----------|---------|
| 1 | Shadow entry hook is internally contradictory | CRITICAL | Logic errors | `design.md:98–109` says to call `super()._entry_events()`, filter its result, then call and return `super()` again. The second call discards the filtered result and mutates episode-dedup state twice. It also clears nonexistent `state.pending`; the engine field is `pending_entry`, which is populated later by `Executor.apply()`. |
| 2 | Candidate panels never receive outcomes | HIGH | Cross-milestone gaps | `attach_outcomes()` is defined separately, but the main loop applies it only to the baseline panel. Candidate panels therefore lack W2.3 outcome fields and cannot reliably derive `scored`, `data_invalid`, `censored`, CREDIT statistics, or sole-blocker attribution as W2.9 requires. |
| 3 | NaN A-DEPTH inputs can trade | CRITICAL | Spec fidelity | The shadow gate explicitly leaves `r30 is None` untouched. A NaN also fails the `r30 > theta` comparison, so the engine may enter the setup, consume capacity, and add cash or inventory even though W2.7 says it is unclassifiable, never passed or forgone. |
| 4 | A-DEPTH gate operates before signal eligibility | HIGH | Logic errors | The hook rejects any row with `a_conditions`, without reproducing the engine’s `a_fires` time-window, episode-start, prior-entry, and capacity conditions. It can emit shadow-gate skips for rows that were never Branch-A signal opportunities, creating spurious panel setups. |
| 5 | Credit property conflicts with the base initializer | HIGH | Dependencies | `Executor.__init__()` assigns `self.credit`, while the proposed subclass replaces it with a policy-reading property. A read-only property makes `super().__init__()` fail; a setter/default-current-branch contract is required but unspecified. |
| 6 | CLI guards deadlock registration and rebind | CRITICAL | Dependencies | The design says every command starts with `require_code_match()`, and that rebind also begins with it. Initial registration has no active code binding, while rebind is invoked precisely because the binding mismatches; both paths are blocked as written. |
| 7 | Rebind byte-identity is impossible with current stamping | CRITICAL | Internal consistency | Every row and manifest contains the current `code_hash`, yet rebind recomputes under a new hash and demands byte-identical Parquet tables while leaving the ledger unchanged. The changed stamp guarantees different bytes unless verification explicitly substitutes or excludes the old hash. |
| 8 | No re-registration operation exists | HIGH | Spec fidelity | `register()` always refuses when `active.txt` exists, but W0.5/W7.3/W8.2 require a changed definition to create a new hash, repoint `active.txt`, reset evidence, and preserve the old ledger. No command or transactional workflow performs that transition. |
| 9 | Registered engine identity is not enforced before replay | HIGH | Data contracts | Registration stores `engine_config_hash` and `frozen_manifest_hash`, but the main loop checks only watch-code identity. It never asserts that the loaded config and current engine registration/manifest equal those registered values before running and stamping results. |
| 10 | Calendar-gap logic misidentifies trading sessions | HIGH | Logic errors | The design treats `event_calendar.csv` entries as holidays. The supplied engine code uses that file for CPI/FOMC and other event-standdown days, which still require disposition rows. Conversely, a weekday-only rule treats exchange holidays as missing sessions. |
| 11 | Refusal reasons lack a structured normalization contract | HIGH | Data contracts | `EVENT_FIELDS` has no refusal field; reasons exist in event types and free-text notes such as `short blocked: vt_broken (R4)`, `3 entries/day reached`, and `one unpaired leg at a time`. The plan’s precedence keys use different strings and defines no parser, unknown-reason behavior, or schema-version handling. |
| 12 | Sole-blocker attribution confuses entry with scoreability | HIGH | Logic errors | The design says a setup entered iff `eligibility == scored`. An entered setup may instead be `data_invalid` or `censored`; it was still unblocked by the disabled rule and must not be mislabeled `multi_blocked`. Entry attribution and scoring eligibility need separate fields. |
| 13 | Diagnostic cap violates W5 and the runtime estimate | HIGH | Internal consistency | W5.2 requires an isolated replay for each refused setup, but the design truncates at 20 per reason. Three tables can add 60 runs; at the stated 2–4 seconds each, total runtime is roughly 138–276 seconds plus other runs, contradicting both “about 12 runs” and the 120-second limit. |
| 14 | Mark cache can permanently omit later-needed strikes | HIGH | Data contracts | The first mark pull persists only the current inventory’s exact strikes and is then never repeated for that date/expiry. A later candidate or registration needing another strike will remain unmarked even though data was available. W6.2 calls for an expiry cache reusable by all inventory. |
| 15 | Closing-mark range exceeds the allowed lookback | HIGH | Logic errors | `closing_quote()` searches minutes `[955,960]`, permitting a quote five minutes before a normal close, while W6.2 allows only three minutes. The hard-coded range also cannot mark early-close sessions relative to their actual last regular-hours bar. |
| 16 | CREDIT ledger key collides across sessions | HIGH | Data contracts | `credit_ladder` is keyed by `(candidate_id, trade_id)`, but `EngineState.next_trade_id` resets to 1 each session. Cumulative snapshots therefore produce duplicate keys; `session_date` and the diagnostic credit value/layer must participate in the key. |
| 17 | Event-calendar identity is omitted from row stamps | HIGH | Spec fidelity | W1.6 and W8.3 require every ledger row to carry every replay-input SHA, including `event_calendar` SHA. The proposed `Stamp` fields omit `calendar_sha`, even if the manifest may contain it. |
| 18 | Required cohort economics and book splits are undefined | HIGH | Cross-milestone gaps | W3.3 requires passed/forgone per-signal expectancy, and W6.1 requires realized cash by branch and discovery/confirmation set. The aggregate `(candidate_id, session_date)` book schema and verdict signatures do not define attribution of credits, failed attempts, settlements, and inventory marks to those cohorts. |
| 19 | Discovery backfill has no safe ordering workflow | HIGH | Dependencies | Discovery sessions must be scored, but chronology checks only sessions after registration. The design neither backfills discovery sessions during registration nor prevents appending an older discovery date after newer snapshots, which would corrupt cumulative inventory, settlement, and drawdown state. |
| 20 | Tests miss or codify the highest-risk failures | MEDIUM | Test adequacy | The tests expect NaN A-DEPTH rows to remain untouched rather than proving they cannot affect execution or books. They also lack coverage for double base-hook invocation, rebind with changed stamps, event-day/holiday chronology, cross-session key uniqueness, candidate-panel outcomes, mark-cache strike expansion, and exact three-minute/early-close marks. |

---

## Codex Plan Review — Architect
**Verdict**: FAIL (8 findings)

| # | Finding | Severity | Dimension | Details |
|---|---------|----------|-----------|---------|
| 1 | Cumulative state has no defined data flow | Critical | Architecture | `watch()` builds current-session panels, trades, and books, then computes verdicts before loading or folding in the prior snapshot. `book_state(candidate_id, date, ...)` likewise has no explicit prior inventory, settlements, cash, or drawdown input. The design therefore cannot implement cumulative evidence bars, checkpoints, open-bomb aging, or historical MTM deterministically. |
| 2 | Registration and rebind lifecycle is internally impossible | Critical | Lifecycle | The CLI says `rebind` begins with `require_code_match()`, although rebind exists specifically to recover from a mismatch. Byte-identical rebind is also impossible if recomputed rows are stamped with the new `code_hash`. Separately, `register()` always refuses when `active.txt` exists, leaving no operation that creates and activates the new registration required by W0.5/W8.2. |
| 3 | The shadow entry hook calls the engine twice | High | Integration | The stated sequence filters the result of `super()._entry_events(...)`, then says to return a fresh second call. That discards the filtered result and interacts incorrectly with the rule engine’s mutable dedup fields. The hook contract must specify one superclass call and the exact composition order for synthetic skips and filtering. |
| 4 | Panel capture occurs before required fields are attached | High | Data Contract | `_vetoes(row)` records the pre-attachment `FeatureRow`; `Session.process_tick()` attaches `health`, `quote_view`, and `quote_gap_streak` afterward. Consequently `rows_df` cannot faithfully supply the required health and quote-state fields. The engine’s single mutually exclusive `health` value also does not directly provide W2.2’s separate HIRO and option-quote health columns. |
| 5 | Event-to-panel mappings are incomplete and semantically unsafe | High | Data Contract | No explicit mapping converts engine notes such as `3 entries/day reached`, `one unpaired leg at a time`, and `short blocked: vt_broken (R4)` into the proposed canonical reasons. Processing every `skip` also encounters outage skips without `signal_min` and reasons absent from the precedence map. In W5, `eligibility == scored` is incorrectly treated as equivalent to “entered”; entered-but-censored or data-invalid setups would be mislabeled `multi_blocked`. |
| 6 | Closing-mark window violates the specification | High | Correctness | `closing_quote()` accepts minutes 955–960, permitting quotes up to five minutes old rather than the required three-minute fallback. The hard-coded regular-session window also lacks an early-close contract, so inventory marks and verdict-gating MTM can be wrong on shortened sessions. |
| 7 | Runtime estimate omits most possible engine runs | High | Feasibility | The ≤120-second estimate counts roughly 12 runs, but W5 permits up to 20 isolated replays for each of three refusal tables—60 additional runs. At the stated 2–4 seconds per replay, isolated diagnostics alone require roughly 120–240 seconds. The milestone needs batching, a global cap, deferred diagnostics, or a revised NFR. |
| 8 | No ADR compliance gate exists | Medium | ADR Alignment | The design references requirements and prior analyses but neither identifies applicable ADRs nor defines an implementation/review check proving compliance or recording that none apply. This leaves architectural decisions and integration constraints unenforced. |

---

## Codex Plan Review — Panel Synthesis

| # | Finding | Severity | Dimension | Flagged By | Confidence |
|---|---------|----------|-----------|------------|------------|
| 1 | Shadow entry hook calls the superclass twice, discarding the filtered result and mutating dedup state twice; it also clears nonexistent `state.pending` instead of respecting `pending_entry` lifecycle. | CRITICAL | Logic errors | Generic, Architect | High |
| 2 | Candidate panels never receive outcomes, preventing reliable eligibility, CREDIT, and sole-blocker calculations. | HIGH | Cross-milestone gaps | Generic | Medium |
| 3 | NaN A-DEPTH inputs can still enter trades, consume capacity, and affect books despite being unclassifiable. | CRITICAL | Spec fidelity | Generic | Medium |
| 4 | The A-DEPTH shadow gate runs before full Branch-A signal eligibility is established, creating spurious skipped setups. | HIGH | Logic errors | Generic | Medium |
| 5 | Replacing `credit` with a read-only policy property conflicts with `Executor.__init__()`, which assigns `self.credit`. | HIGH | Dependencies | Generic | Medium |
| 6 | Registration and rebind lifecycle is internally impossible: code-match guards block initial registration and mismatch recovery, changed `code_hash` stamps prevent byte-identical rebind, and no operation creates and activates a replacement registration. | CRITICAL | Lifecycle | Generic, Architect | High |
| 7 | Replay does not enforce the registered engine configuration and frozen-manifest identities before running and stamping results. | HIGH | Data contracts | Generic | Medium |
| 8 | Calendar-gap logic mistakes event-standdown dates for holidays while treating exchange holidays as required weekday sessions. | HIGH | Logic errors | Generic | Medium |
| 9 | Refusal reasons lack a versioned normalization contract covering engine note strings, outage skips, missing `signal_min`, and unknown reasons. | HIGH | Data contracts | Generic, Architect | High |
| 10 | Sole-blocker attribution incorrectly equates `eligibility == scored` with entry, misclassifying entered-but-censored or data-invalid setups. | HIGH | Logic errors | Generic, Architect | High |
| 11 | Per-reason diagnostic caps permit up to 60 extra replays, contradicting the stated run count and 120-second runtime target. | HIGH | Feasibility | Generic, Architect | High |
| 12 | The mark cache can permanently omit strikes needed by later candidates because it persists only the first inventory’s exact strikes and is never expanded. | HIGH | Data contracts | Generic | Medium |
| 13 | Closing marks permit a five-minute fallback and lack an early-close contract, violating the three-minute requirement. | HIGH | Correctness | Generic, Architect | High |
| 14 | The CREDIT ledger key collides across sessions because `trade_id` resets daily while the key omits `session_date` and diagnostic layer/value. | HIGH | Data contracts | Generic | Medium |
| 15 | Ledger row stamps omit the required event-calendar SHA. | HIGH | Spec fidelity | Generic | Medium |
| 16 | Required passed/forgone expectancy and realized-cash splits lack defined attribution across branches and discovery/confirmation cohorts. | HIGH | Cross-milestone gaps | Generic | Medium |
| 17 | Discovery backfill has no chronology-safe workflow, allowing older sessions to corrupt cumulative inventory, settlement, and drawdown state. | HIGH | Dependencies | Generic | Medium |
| 18 | Tests omit or encode the wrong behavior for the highest-risk failures, including NaN execution, double hook calls, rebind stamps, calendar handling, key collisions, candidate outcomes, cache expansion, and closing marks. | MEDIUM | Test adequacy | Generic | Medium |
| 19 | Cumulative state has no defined data flow from prior snapshots into books and verdicts, preventing deterministic evidence bars, checkpoints, inventory aging, settlements, and historical MTM. | CRITICAL | Architecture | Architect | Medium |
| 20 | Panel capture occurs before health and quote fields are attached, and the engine’s single `health` value cannot directly supply separate HIRO and option-quote health columns. | HIGH | Data contracts | Architect | Medium |
| 21 | No ADR applicability or compliance gate is defined. | MEDIUM | ADR alignment | Architect | Medium |

## Round 2 (v1.1) — FAIL 23 generic / 8 architect → applied in v1.2 (+ requirements v1.2a alignment); design review closed at two rounds

## Codex Plan Review — Verdict: FAIL (23 findings)

| # | Finding | Severity | Dimension | Details |
|---|---------|----------|-----------|---------|
| 1 | Rebind guard is contradictory | HIGH | Internal consistency | Section 1 correctly says `rebind` runs without the code-match guard, but section 12 says it begins with that guard. The latter makes rebind impossible precisely when code changed. |
| 2 | `register --supersede` violates registration semantics | HIGH | Spec fidelity | W8.2 requires `watch register` to refuse whenever `active.txt` exists. The design instead permits `watch register --supersede`; this needs a distinct command or a requirements change. |
| 3 | `code_hash` is missing from ledger rows | HIGH | Data contracts | W8.3 explicitly requires every row to carry `code_hash`. The design knowingly stores it only in `manifest.json`, changing the required contract. |
| 4 | Registered LB95 constants do not control execution | HIGH | Data contracts | Registration includes W6.5 constants, but `stats.lb95` imports `DRAWS` and `SEED` from the engine. Consequently WATCH_HASH does not bind the parameters actually used. |
| 5 | A-DEPTH diagnostic ladder has no implementation path | HIGH | Spec fidelity | W3.3 requires diagnostic classification for every θ. No component produces the `a_depth` table, and the main loop neither constructs nor passes one to `ledger.stage`; only θ* receives a portfolio run. |
| 6 | Candidate outcomes are omitted by the main loop | HIGH | Internal consistency | Section 4 promises `attach_outcomes` for candidate panels, but the “whole watch” loop builds `cpanels` without attaching trades, MAE, MFE, or P&L. W2.9 scorers would receive incomplete rows. |
| 7 | Required panel self-check is absent | HIGH | Spec fidelity | W9.4 requires an every-session comparison of W2.2 panel features with logged features. The design checks EVENT_FIELDS before panel construction but never validates the resulting panel columns. |
| 8 | Terminal-checkpoint behavior is impossible | HIGH | Logic errors | Checkpoint 40 is both terminal and deferrable for scale drift, missing marks, or representation failure, yet no later checkpoint exists. Candidates whose count bars mature after session 40 also can never receive a verdict. |
| 9 | Isolated-replay cap violates W5.2 | HIGH | Spec fidelity | W5.2 requires every refused setup to receive an isolated replay. `MAX_ISOLATED = 20` silently truncates that required population and introduces `DIAGNOSTIC_TRUNCATED`, which is absent from the specification and schemas. |
| 10 | Capacity-refused output has no durable contract | MEDIUM | Data contracts | W5.1 requires capacity-refused setups to be reported and scored separately. The design mentions a separate frame, but `b_refused` permits only `vt`, `levels`, and `late`, with no persisted capacity table or aggregate. |
| 11 | Health mapping loses required state | HIGH | Data contracts | The design admits its single-string precedence mapping is lossy when HIRO and quote failures coincide. Raw `health` cannot substitute for correctly populated `hiro_health` and `option_quotes_health` columns required by W2.2. |
| 12 | Manifest SHAs are trusted rather than verified | HIGH | Logic errors | Chain and HIRO identities are read from manifests, but the design does not recompute and compare their actual file hashes at load. `verify_frozen` covers frozen pins, not the stated per-session W1.2 verification contract. |
| 13 | Calendar source is inconsistent and unregistered | HIGH | Dependencies | `inputs.py` describes `event_calendar.csv` as the holiday source, while `ledger.py` introduces `docs/hiro_watch/nyse_holidays.csv`. The latter is a new input absent from W1 and from the registration payload despite being called registered by SHA. |
| 14 | Mark acquisition and provenance violate W6 | HIGH | Spec fidelity | W10.2 requires pulls through `ChainStore`, but the design calls `hiro_engine.live.theta_client` directly. It also records the cache SHA only in the snapshot manifest although W6.2 requires it in the book row. |
| 15 | Historical inventory can be duplicated as open state | HIGH | Logic errors | Cumulative `inventory` contains one row per bomb per session, yet `book_state` reads prior inventory rows as open bombs without defining latest-row selection and settlement exclusion. Re-marking all historical rows would duplicate bombs and settled positions. |
| 16 | CREDIT portfolio rows lack sufficient identity | HIGH | Data contracts | The `credit_ladder` key has only session, layer, branch, c, and trade ID. A target-A replay also contains B trades and vice versa; without `candidate_id` or separate `variant_branch` and `trade_branch`, variants can collide or be misattributed. |
| 17 | Pruning breaks deterministic re-runs | HIGH | Dependencies | `verify_identity(date)` compares against that date’s committed snapshot manifest, but `prune(keep=5)` may delete it. The design provides no retained manifest or reconstruction rule for re-running an older ledgered date. |
| 18 | Candidate refusal states do not map to eligibility | MEDIUM | Data contracts | The refusal map adds `shadow_gate`, `shadow_filter`, and `other:<raw>`, while eligibility is restricted to the W2.9 enum. The design never defines how those reasons map to `gate_failed`, `capacity_blocked`, or another legal value. |
| 19 | Non-nullable dollar types conflict with UNMARKED data | MEDIUM | Data contracts | The design declares every dollar column as `int64`, but UNMARKED inventory requires absent `mark_mid_usd` and `mark_liq_usd`. It must specify nullable integer types or another non-numeric representation. |
| 20 | Scale-ratio denominator is unguarded | MEDIUM | Edge cases | Excluding zero and NaN observations can leave `r30_scale_ref` empty or zero. `scale_monitor` defines no result for division by zero or an undefined reference median. |
| 21 | Concurrent writers can lose snapshots | MEDIUM | Edge cases | There is no lock or compare-and-swap around reading `current`, staging, renaming, and replacing the pointer. Concurrent watch, rebuild, rebind, or prune commands can commit divergent states and delete one another’s snapshots as orphans. |
| 22 | Runtime budget is internally inconsistent | MEDIUM | Test adequacy | The overview budgets approximately 12 runs and 50 seconds, while the detailed path allows 29 runs. At the stated four seconds per replay, replay alone reaches 116 seconds before marking, Parquet, statistics, and reporting; no runtime-budget test is planned. |
| 23 | NaN gate test contradicts required behavior | MEDIUM | Test adequacy | The hooks test says “NaN untouched,” whereas W2.7, the hook design, and a later test require NaN r30 to suppress entry, avoid capacity consumption, and be labeled unclassifiable. |

---

## Codex Plan Review — Architect
**Verdict**: FAIL (8 findings)

| # | Finding | Severity | Dimension | Details |
|---|---------|----------|-----------|---------|
| 1 | Frozen engine identity is not enforced | Critical | Integration contract | `Registration.frozen_manifest_hash` is recorded but never compared by `engine_identity_guard`; the guard checks only CONFIG_HASH and chain pins. Pre/post artifact hashing detects mutation during a run, not engine drift before it. Changed engine code could therefore generate both the source log and shadow replay successfully under the old registration. |
| 2 | Registration lifecycle contradicts both itself and W8.3 | Critical | Spec fidelity | The design intentionally omits `code_hash` from every ledger row although W8.3 explicitly requires it. It also says `rebind` runs without the code-match guard in `registration.py`, while the CLI contract says `rebind` begins with that guard, which would make recovery from a mismatch impossible. |
| 3 | Discovery backfill has no exposed command | High | Dependency ordering | `ledger.py` requires `watch backfill` before normal processing, but the CLI command list omits `backfill`. With chronology requiring all earlier discovery and confirmation sessions, a fresh registration lacks a defined, executable bootstrap path. |
| 4 | Verdict-critical lineage and eligibility mappings are implicit | High | Data contract | The plan never defines the complete event/reason/outcome-to-`eligibility` mapping, despite eligibility controlling all rates and count bars. It also references passed/forgone selectors without those fields in the schemas, and does not specify the join from `setup_id` through trades to bombs, marks, and settlements. Cohort expectancy cannot be implemented unambiguously without this lineage. |
| 5 | Health reporting knowingly loses required state | High | Contract fidelity | `ShadowSession` acknowledges that mapping the engine’s single health string into `hiro_health` and `option_quotes_health` is lossy when conditions coincide. W2 requires both columns independently; retaining a raw column does not make the required columns correct and can misclassify data validity. |
| 6 | Snapshot retention and replay semantics conflict | High | State management | `current` names only the latest snapshot, yet startup deletes snapshot directories “not reachable” from it; no predecessor chain or snapshot index defines older snapshots as reachable. Separately, `prune(keep=5)` can remove manifests that `verify_identity(date)` needs to validate any previously ledgered date. |
| 7 | Valuation inputs are not fully deterministic or atomic | High | Data integrity | Settlement may switch to a later-populated `index_eod` row, but that row/value is not SHA-pinned as an input. Mark files are shared outside the WATCH_HASH tree and lack a specified staging, atomic-write, schema-validation, and hash-verification protocol. Their SHA is placed only in the manifest although W6.2 requires it in the book row, and the pull bypasses the stated ChainStore boundary. |
| 8 | The A-DEPTH diagnostic deliverable has no producer | High | Completeness | The architecture defines an `a_depth` table for all five thresholds, but no component or main-loop operation builds it; only the primary-threshold portfolio run exists. `ledger.stage` is not passed an A-DEPTH diagnostic result. W3.1/W3.3’s per-threshold passed, rejected, unclassifiable, and actual-outcome tables are therefore absent from the implementation plan. |

---

## Codex Plan Review — Panel Synthesis

| # | Finding | Severity | Dimension | Flagged By | Confidence |
|---|---------|----------|-----------|------------|------------|
| 1 | Frozen engine identity is recorded but not enforced | Critical | Integration contract | Architect | High |
| 2 | Rebind guard is contradictory and prevents recovery from code drift | Critical | Internal consistency | Generic, Architect | High |
| 3 | Ledger rows omit the required `code_hash` | Critical | Data contracts | Generic, Architect | High |
| 4 | `register --supersede` violates registration semantics | High | Spec fidelity | Generic | High |
| 5 | Registered LB95 constants do not control execution | High | Data contracts | Generic | High |
| 6 | A-DEPTH diagnostics have no producer or main-loop implementation path | High | Completeness | Generic, Architect | High |
| 7 | Candidate panels omit required trade outcomes | High | Internal consistency | Generic | High |
| 8 | Required per-session panel self-check is absent | High | Spec fidelity | Generic | High |
| 9 | Terminal-checkpoint deferral and late maturity make some verdicts impossible | High | Logic errors | Generic | High |
| 10 | Isolated-replay cap violates the requirement to replay every refused setup | High | Spec fidelity | Generic | High |
| 11 | Capacity-refused results lack a durable reporting and scoring contract | Medium | Data contracts | Generic | High |
| 12 | Health mapping loses independently required HIRO and quote states | High | Data contracts | Generic, Architect | High |
| 13 | Chain and HIRO manifest SHAs are trusted rather than verified against files | High | Logic errors | Generic | High |
| 14 | Calendar sources are inconsistent and the introduced holiday file is unregistered | High | Dependencies | Generic | High |
| 15 | Mark acquisition bypasses `ChainStore` and omits the cache SHA from book rows | High | Spec fidelity | Generic, Architect | High |
| 16 | Settlement can use an unpinned, later-populated index value | High | Data integrity | Architect | High |
| 17 | Shared mark files lack a defined atomic-write, validation, and hash-verification protocol | High | Data integrity | Architect | High |
| 18 | Historical inventory can be duplicated as open state | High | Logic errors | Generic | High |
| 19 | CREDIT portfolio rows lack sufficient candidate and branch identity | High | Data contracts | Generic | High |
| 20 | Snapshot pruning breaks deterministic historical reruns | High | State management | Generic, Architect | High |
| 21 | Snapshot reachability is undefined, risking deletion of valid snapshots | High | State management | Architect | High |
| 22 | Refusal, event, reason, and outcome mappings to `eligibility` are incomplete | High | Data contracts | Generic, Architect | High |
| 23 | Verdict selectors and setup-to-trade-to-valuation lineage are undefined | High | Data contracts | Architect | High |
| 24 | Non-nullable dollar types conflict with UNMARKED inventory rows | Medium | Data contracts | Generic | High |
| 25 | Scale-ratio behavior is undefined for an empty or zero reference denominator | Medium | Edge cases | Generic | High |
| 26 | Concurrent writers can create divergent state and lost snapshots | Medium | Edge cases | Generic | Medium |
| 27 | Runtime budget contradicts the detailed replay path and lacks a budget test | Medium | Test adequacy | Generic | High |
| 28 | NaN gate test contradicts required suppression and classification behavior | Medium | Test adequacy | Generic | High |
| 29 | Discovery backfill is required but has no exposed CLI command | High | Dependency ordering | Architect | High |

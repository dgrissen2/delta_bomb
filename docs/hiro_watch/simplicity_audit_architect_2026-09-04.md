# Simplicity audit — Architect (in-session), 2026-09-04

Inputs: STATUS.md, requirements.md v1.2a, design.md v1.3, tasks.md v1.2, both prior review
transcripts, and the engine files the hooks touch (`session.py` 382, `rules.py` 398,
`executor.py` 292, `eventlog.py` 247, `backtest.py` 62; `models.py` FeatureRow, `chains.py`,
`config.yaml`, `sessions_backtest.csv`, `branch_accounting_2026-09-03.md` §5–7).

Engine-source claims below were independently re-checked after the audit: single injection point
`session.py:272` → `rules.evaluate`; `_entry_events` reads only `row.a_conditions / late_state /
vetoes.*` (`rules.py:136-150`); `Session.finish()` unconditionally appends to
`sessions_backtest.csv` (`session.py:365-381`); `leg_liq_loss_usd` is updated every bar
(`executor.py:207, 266`).

---

## 1. VERDICT

**Over-engineered — confidence high (~85%).** The *purpose* (run the frozen engine read-only with a candidate injected; score three pre-registered rules; verdicts only at checkpoints on confirmation data) is sound and cheap. Roughly 60% of the spec's mechanisms are infrastructure for problems a one-person, one-command-per-evening, ≤ 250-session program does not have: snapshot chains, code-lineage files, rebind lifecycles, writer locks, a 14-class exception taxonomy, a 20-run isolated diagnostic layer, a second fill-physics implementation, dual-source settlement provenance, tamper detection on files the same person wrote five minutes earlier. Two review rounds each on three documents (25+27, 28+31, 6+8 findings, "all applied") is how the weight got in — every finding was accepted, none was weighed against the cost of a junior having to hold it in their head.

The engine source also shows a **simpler injection point than the three hooks in the design**: one row-transform in `RuleEngine.evaluate` covers A-DEPTH, LATE-off, vt_broken-off and levels_invalid-off with no gated-episode memory and no synthetic skip events (§3 below).

---

## 2. WEIGHT vs LOAD-BEARING

Discipline key: **FROZEN** (defs fixed before confirmation data), **FIREWALL** (discovery ≤ 2026-09-02 vs confirmation), **CHECKPOINT** (verdicts at 10/20/30/40 with pre-stated bar), **NO-EDIT** (engine untouched), **LOUD** (no silent skips), **REPRO** (reproducible).

### Modules (tasks.md §Package layout, 13)

| Module | Decision | Reason |
|---|---|---|
| `constants.py` (design §12) | **CUT** | `MAX_ISOLATED` goes with the isolated layer; `USD_MULT`, `FLOAT_TOL`, `CLOSE_WINDOW_MIN` are three literals with one use each. A "no numbers in code" rule that needs its own module has become ceremony. Decision numbers stay in the registration payload (that part is FROZEN and stays). |
| `registration.py` | **KEEP, shrink to ~50 lines** | FROZEN. Payload dict → canonical JSON → sha256 → `WATCH_HASH`. Drop `.code` files, `active.txt`, `--supersede`, `rebind`. |
| `inputs.py` | **COLLAPSE INTO `ledger.py`** | LOUD/REPRO: resolve paths, sha the ~6 inputs, refuse with the full missing list. ~40 lines; does not need its own module. Drop the holiday CSV (see mechanisms). |
| `shadow.py` | **KEEP — the only load-bearing code** | NO-EDIT. But two hooks + two silencers, not three hooks (§3). |
| `panel.py` | **COLLAPSE INTO `tables.py`** | The panel is "FeatureRow at signal minute + refusal reason + outcome". The W2.6 enum policing, health split, `W22_COLUMNS` firewall vocabulary and eligibility enum are weight (below). |
| `ladder.py` (task 6) | **CUT** | It re-implements fill physics (the accounting replay) — the design's own principle says never re-implement the engine. The (A,0.10)/(B,0.10) baseline run *is* the self-check. MAE is already on the engine's exit event (`leg_liq_loss_usd`, executor.py:58/:266 — updated every bar in `_update_marks`, so it is minute-complete; the spec's claim that only heartbeats carry it is wrong). MFE is used by no verdict. |
| `refused.py` | **COLLAPSE INTO `tables.py`** (~30 lines) | Three engine runs with one rule off + a merge on `setup_id` to see which setups actually entered. That is the whole sole-blocker rule. Isolated layer cut. |
| `book.py` | **KEEP, shrink** | Marks need a real pull (the day's chain cache holds only that day's expiry; older bombs need `_sdk_pull_day(day, expiry)`), so the pull-once mark cache is load-bearing. Drop per-row sha, `MarkTampered`, dual-source settlement, settlement pinning, state-flow from `prev` snapshot. |
| `stats.py` | **COLLAPSE INTO `verdicts.py`** | LB95 is ~15 lines; checkpoint test is 1 line. |
| `verdicts.py` | **KEEP** | CHECKPOINT/FIREWALL. This is where the pre-stated bars live; it must stay explicit and boring. |
| `ledger.py` | **KEEP, rewrite to ~100 lines** | LOUD/REPRO. Per-session directory written via `tmp` + `os.rename`; chronology refusal; re-run compares bytes. No snapshot chain, no pointer, no lock, no orphan GC. |
| `report.py` | **KEEP** (~80) | Text tables. Fine. |
| `cli.py` / `__main__.py` | **KEEP, 3 subcommands** | `register`, `run <date>`, `report` (+ `verify` = re-run every ledgered date, 8 lines). Drop `backfill` (it is `run` in a loop), `rebind`, `rebuild`, `--supersede`. |
| `tests/` | **KEEP, ~400 lines** | The harness-fidelity tests are the most important artifact in the package (§4). |

### Mechanisms

| Mechanism | Decision | Reason |
|---|---|---|
| WATCH_HASH = sha256(canonical JSON) (W8.1, design §1) | **KEEP** | FROZEN. It is 2 lines and it *is* the discipline. Ledger dir named by it; `run` refuses if `sha(registration.json) ≠ dir name`. |
| Cumulative immutable snapshot dirs + `current` pointer + `prev_snapshot` chain + orphan GC + `rebuild` (W9.3, design §10) | **CUT → per-session directory, `tmp` + rename** | Exists to make "book state depends on prior state" atomic. Remove the dependency instead: store raw events/rows/marks per session; the book is a pure function of the union of all session dirs. Then "the ledger as of session N" is free (`report --upto`), atomicity is one `os.rename`, and there is no chain to walk or corrupt. REPRO and LOUD fully preserved. |
| Code lineage `.code` files + `rebind` (W8.1/W8.3, design §1) | **CUT → stamp `git rev-parse HEAD` + dirty flag in each session's `meta.json`** | The discipline is REPRO, which `watch verify` (recompute every ledgered date, compare bytes) gives directly. A lifecycle where "every command refuses until rebind" solves a problem git already solves for one engineer. |
| `active.txt` / `register --supersede` (W8.2) | **CUT** | One registration file, `docs/hiro_watch/registration.json`. A re-registration is a new file content → new hash → new ledger dir; old dir stays. `register` refuses if a ledger dir for the hash already exists. FROZEN preserved with zero lifecycle code. |
| 14-class exception hierarchy (design §Error handling, task 1) | **COLLAPSE → 2 classes** | `WatchRefused` (precondition: missing input, chronology, identity) and `WatchDrift` (harness ≠ engine log, re-run ≠ ledger). The CLI prints class + message, exit 2. LOUD needs a loud message, not a taxonomy. |
| Regime panel W2.2 columns | **KEEP (they are free)** | Every column is a `FeatureRow` field the engine already computed; capture the row in the hook and select at signal minutes. |
| W2.6 enums / `hiro_health` + `option_quotes_health` split / nullability policing | **COLLAPSE → raw `health` column, one line "r30 NaN ⇒ unclassifiable"** | The design already admits the split is lossy and the raw column is authoritative. Store the raw one. |
| W2.8 scale monitor (+4 registered constants, `SCALE_DRIFT` deferral) | **CUT → report the session's median \|r30\| as one column** | Not required by any discipline item. At n≈40 a 20-session rolling window has two independent samples. If HIRO's $B scale drifts, θ*=−4 fails its bar — that is the honest verdict, not a deferral. |
| W2.9 opportunity ledger + 9-value eligibility enum + `REFUSAL_MAP_V1` + precedence | **COLLAPSE** | Keep: `refusal_reason` (an 8-entry note→enum dict, needed to group W5 tables), the dedup precedence (one `sort_values`), and a boolean `scored`. The 9-value enum is derivable from `refusal_reason` + `outcome`; a third column that restates two others is a contract nobody needs. `in_baseline` = one `isin`. |
| Θ ladder {−1…−5} diagnostic (W3.1/W3.3a) | **KEEP** | A 5-line groupby over the baseline panel; no replays; registered, so not a search. Shows response shape; cheap. |
| Two-layer diagnostic/portfolio — CREDIT (W4.1a) | **CUT the diagnostic layer** | Second fill implementation (see `ladder.py`). The per-trade Δ table comes from joining the (A,c) run's trades to the baseline's on `setup_id` — with correct exits, not "flow exits held fixed". |
| Two-layer diagnostic/portfolio — B-REFUSED isolated replays + `MAX_ISOLATED=20` + `entry_filter` + `DIAGNOSTIC_TRUNCATED` (W5.2a, design §6) | **CUT** | 20 extra engine runs per session for a layer the spec itself says carries no evidence. Removes `entry_filter`, the gated-episode memory, and the truncation logic. |
| Bootstrap + Clopper–Pearson `min` LB95 (W6.5) | **KEEP** (~15 lines) | CHECKPOINT: it is in the pre-stated bar ("LB95 > 0.55"). `DRAWS`/`SEED` imported from `hiro_engine.register`. Session-clustered bootstrap is the right unit; CP is one scipy line that fixes the 10/10 → 1.0 artefact. |
| Shock grid (W6.6) | **KEEP as 10 report lines** | Not discipline-bearing; kept only because it reuses `settle()` and costs nothing. If it ever grows a second axis, cut it. |
| Per-candidate books (W6.7) | **KEEP as `book(trades, marks, settlements)` called per `candidate_id`** | Needed by the W3.4/W4.3 "candidate MTM ≥ baseline" conditions. Costs nothing if the book is a pure function. |
| Mark cache with sha on every row + re-hash on read + `MarkTampered` (W6.2, design §7) | **KEEP the pull-once cache; CUT the sha/tamper machinery** | The pull is load-bearing (older expiries are not in the day's chain cache). Tamper-detection on a file you wrote yourself is weight; `watch verify` catches any drift anyway. |
| Settlement pinning + dual-source (`index_eod` vs `spx_1m_close`) + reconciliation warning (W6.4, design §7) | **CUT → one source: last regular-hours SPX 1-min close, stamped `spx_1m_close`** | W6.4 already declares the 1-min close an acceptable proxy. Two sources + a pin + a rebuild rule to make them agree is three mechanisms to avoid a ≤ 0.5-pt difference on a $5-wide spread. |
| Holiday authority CSV + `coverage_end` + `CalendarExpired` (design §2, task 3) | **COLLAPSE → a `holidays: [...]` list (≈10 dates) inside the registration payload** | LOUD needs "refuse if a weekday before `<date>` has no disposition row and is not a holiday". A list in the frozen payload does that; a file with its own sha, header and expiry does not add safety. |
| `single_writer_lock` (design §10) | **CUT** | One person, one machine, one evening command. A second run of the same date hits "dir exists → verify bytes"; a concurrent run of two dates hits the chronology check. |
| `engine_identity_guard` + hash all engine artifacts before/after every run (W0.1, design §3) | **COLLAPSE → one `engine_fingerprint()` in the payload, checked at `run` start; the before/after hash becomes a test** | NO-EDIT is enforced by: fingerprint = sha256(config_hash + sorted `scripts/hiro_engine/*.py` bytes) recorded at `register`, refused on mismatch; plus the two silencers in §3 (the only two engine write paths). The before/after runtime hash proves the watch didn't write — that is a test property, not a per-run cost. |
| Task 12 investment gate | **KEEP (it is one paragraph in STATUS.md, zero code)** | CHECKPOINT. The CIO's point stands: build sign-off ≠ promotion. |
| Review gates after tasks 4 and 9 (+ red-team both times) | **COLLAPSE → one gate after the harness, one acceptance check after backfill** | The harness (task 4) is the only place a wrong line silently corrupts evidence. Everything after it is pandas over frames whose correctness is proven by the backfill reproducing `branch_accounting_2026-09-03.md` §1/§5/§7 numbers. |

---

## 3. THE MINIMAL VERSION

### Injection point — what the engine source actually allows

`Session.process_tick` (session.py:243–256) builds the final row — features, vetoes, health, quote_view — and then calls **one** method with it: `self.rules.evaluate(row, self.state)` (step 4). `RuleEngine._entry_events` decides everything off four row fields: `row.a_conditions`, `row.late_state`, `row.vetoes.vt_broken`, `row.vetoes.levels_invalid` (rules.py:120–135). `FeatureEngine` computes `a_conditions`/`late_state` and updates the episode tracker *before* the row is handed over (features.py:272–276), and nothing downstream of `evaluate` (`_resolve_instruments`, the health filter, `Executor.apply`) reads those four fields. `FeatureRow` is frozen, so `dataclasses.replace` is the only way to touch it anyway.

So every candidate that changes *entry* is a **pre-transform of the row**, not a post-filter of events:

```python
class ShadowRules(RuleEngine):
    def evaluate(self, row, state):
        p = self.policy
        if p.a_theta is not None and row.a_conditions and not (row.r30 is not None and row.r30 <= p.a_theta):
            row = replace(row, a_conditions=False)            # A-DEPTH: engine never sees the A setup
        if "late" in p.disable:
            row = replace(row, late_state=False)
        if p.disable & {"vt_broken", "levels_invalid"}:
            row = replace(row, vetoes=replace(row.vetoes,
                          vt_broken=row.vetoes.vt_broken and "vt_broken" not in p.disable,
                          levels_invalid=row.vetoes.levels_invalid and "levels_invalid" not in p.disable))
        self.rows.append(flatten(row))                          # the panel source, final row
        return super().evaluate(row, state)
```

Consequences versus design §3:
- **`ShadowSession._vetoes` override: not needed.** Vetoes are rewritten on the row at the same point.
- **`_entry_events` post-filter, `_gated_a_episodes` memory, synthetic `skip: shadow_gate` events, "super called exactly once" test: not needed.** With `a_conditions=False` the engine simply never fires; the per-minute re-evaluation gives "enter only when r30 ≤ θ" semantics for free. Passed/rejected/unclassifiable is classified on the **baseline** panel (which has every A signal), not read from the candidate run's skip lines.
- **`ShadowExecutor.credit`: needed, but as two plain overrides, not a property with a setter.** `self.credit` is read at executor.py:170 (`raw_l`) and :246 (R1.4e invariant). Only one trade is open at a time (one-unpaired-leg), so:

```python
class ShadowExecutor(Executor):
    def _book_limit_entry(self, bar, pe, quotes, state):
        self.credit = self.policy.credit[pe.branch]; return super()._book_limit_entry(bar, pe, quotes, state)
    def _apply_fill(self, tr, row, state):
        self.credit = self.policy.credit[tr.branch]; return super()._apply_fill(tr, row, state)
```

- **Two silencers are mandatory and are the real NO-EDIT contract**: `MemoryLog` (`emit` → list; `csv_path=None`) because `Session` writes through `self.log`; and `ShadowSession._write_session_row = no-op` because `Session.finish()` (session.py:352) *unconditionally* appends to `sessions_backtest.csv` — an engine artifact. Those two plus `ReplayFeed`/`ChainStore.load` being read-only are the entire write surface.

So: **two hooks (`ShadowRules.evaluate`, `ShadowExecutor` credit) + two silencers.** `ShadowSession.__init__` swaps `self.rules`/`self.executor` after `super().__init__` (2 lines). `run_shadow` = `ReplayFeed(cfg,[day])` + `build_range60_history` over stored days before `day` exactly as `backtest.run_backtest` does (that pooling is what makes features bit-identical) + `run_replay`. Nine engine runs per session: baseline, A-DEPTH θ*, (A,.20), (A,.30), (B,.20), (B,.30), refused-vt, refused-levels, refused-late. ≈ 30 s.

### Modules (8) and line budget

```
scripts/hiro_watch/
  cli.py           ~60   register | run <date> | report [--upto] | verify ; --debug
  registration.py  ~50   payload dict (Θ, θ*, C, every bar number, checkpoints, DRAWS/SEED from
                          hiro_engine.register, registration_date, engine_fingerprint, holidays[])
                          → canonical JSON → WATCH_HASH; load(); check_engine_fingerprint()
  shadow.py       ~120   Policy, MemoryLog, ShadowRules, ShadowExecutor, ShadowSession, run_shadow,
                          POLICIES (the 9), assert_baseline_matches_log
  tables.py       ~170   panel (rows at signal minutes + dedup/precedence + refusal_reason + outcome
                          + set + candidate_id + in_baseline), trades_from_events, bombs_from_trades,
                          refused_attribution (merge on setup_id → scored | multi_blocked),
                          credit_by_variant, a_depth_ladder
  book.py         ~130   MarkCache (pull-once, marks/<date>_<expiry>.parquet), closing_quote
                          (quality + [L-3,L] window → UNMARKED), settle(), book(trades, marks,
                          settlements) per candidate, shock_grid
  verdicts.py     ~130   lb95 (bootstrap ∧ Clopper–Pearson), is_checkpoint, representation,
                          a_depth_verdict, credit_verdict ×4, b_refused_status, immediate rejects
  ledger.py       ~110   resolve_inputs (paths + shas, refuse listing all missing, HIRO identity
                          note), chronology_check, write_session (tmp dir → os.rename),
                          verify_session (recompute, compare bytes, refuse on diff), load_all
  report.py        ~80   text tables: books side by side, progress vs bar, verdicts, shock grid
  tests/          ~400
```

### Data outputs — `docs/replay/hiro_watch/<WATCH_HASH>/<date>/`

| file | content | why it is the ledger |
|---|---|---|
| `events.parquet` | all 9 runs' events, `EVENT_FIELDS` + `candidate_id` | raw truth; everything else derives from it |
| `rows.parquet` | baseline per-minute FeatureRow flattened (features are identical across runs — same feed, same `FeatureEngine`) | the regime panel source |
| `marks.parquet` | one row per open bomb per candidate at the close: `mark_mid_usd, mark_liq_usd, unmarked` | the only thing that needs a network pull; persisted once |
| `meta.json` | `watch_hash, engine_fingerprint, git_sha, dirty, disposition, set, input_shas{chain,spx,spy,hiro,levels,log}` | REPRO stamp |
| `report.txt` | what was printed that evening | the dated record of the verdict printed at that checkpoint |

Global: `docs/replay/hiro_watch/marks/<date>_<expiry>.parquet` (mark cache). Panel, trades, books, verdicts are recomputed from these on every `report` — nothing cumulative is stored, so nothing cumulative can be corrupted.

### How each discipline item is still guaranteed

| Discipline | Guarantee in the minimal version |
|---|---|
| Frozen definitions | `registration.json` → `WATCH_HASH`; ledger dir named by it; `run` refuses if `sha(registration.json) ≠ dir`; any edit = new hash = new empty dir (old retained). |
| Firewall | `set = DISCOVERY if date ≤ registration_date else CONFIRMATION` (one line in `tables.py`); every verdict function starts with `panel[panel.set == "CONFIRMATION"]`; one test. |
| Checkpoints | `n_conf = countable confirmation sessions ledgered`; verdict computed iff `n_conf in payload.checkpoints`; else `INCONCLUSIVE (n/10)`; immediate-REJECT paths evaluated every run; 4th terminal. |
| Never edit engine | fingerprint at `run` start; `MemoryLog` + `_write_session_row` no-op; `test_engine_artifacts_untouched` (hash `scripts/hiro_engine/**`, `docs/replay/hiro/*`, `registration.json` before/after a full run). |
| No silent skips | `resolve_inputs` refuses listing everything missing; `chronology_check` refuses if any disposition-ledger date (or non-holiday weekday) before `<date>` is unledgered; `assert_baseline_matches_log` refuses on drift; `tmp` + rename means a crash leaves nothing. |
| Reproducible | re-run of a ledgered date recomputes and compares bytes, writes nothing, refuses on difference; `verify` does it for every date; `meta.json` shas say which inputs a difference came from. |

---

## 4. WHAT I WOULD NOT CUT (and what a naive simplifier gets wrong)

1. **`assert_baseline_matches_log`** — the baseline run must equal the engine's logged rows on every `EVENT_FIELDS` column, every session, before any candidate runs. This one check is the whole warrant that the harness is the engine. A simplifier who drops it "because the tests cover it" has removed the only runtime proof.
2. **The `_write_session_row` no-op and `MemoryLog`.** They look like trivia. They are the two places the engine writes; without them the watch corrupts `sessions_backtest.csv` and the paper log on the first run.
3. **Per-branch credit in `ShadowExecutor`.** It is 8 lines; Charlie's round-2 insistence that B evidence never pools into A is right, and the alternative ("apply c to both, score per branch") lets an A leg resting longer at 0.30 change which B signals get capacity.
4. **Pooled `range60_history` built exactly like `backtest.run_backtest`.** Skip it and the features silently differ from the log; the baseline self-check will catch it, but a junior will spend a day finding out why.
5. **The portfolio (sequential) replay as the verdict basis** — for all three candidates. The tempting "just classify the baseline signals" version ignores capacity (3/day, one-unpaired-leg), which on 2026-08-28 was binding.
6. **Sole-blocker attribution** (`scored` iff the one-rule-off run actually entered the setup). It is one merge; without it the vt_broken table counts setups that were also capacity-blocked.
7. **UNMARKED as a first-class state** in the book and "verdict defers on UNMARKED". Estimating a mark for a deep-OTM put with no valid quote is exactly the kind of quiet fudge the whole program exists to prevent.
8. **Input shas in `meta.json` and the re-run byte comparison.** Reproducibility is a discipline item; this is the entire mechanism and it is ~20 lines.
9. **LB95 with the Clopper–Pearson floor**, and `DRAWS`/`SEED` imported from the engine. The evidence bar quotes LB95; changing the statistic is changing the bar.
10. **The registration payload holding every decision number.** "No numbers in code" is right; only the `constants.py` module and the rule's policing were weight.

---

## 5. RISKS OF SIMPLIFYING — what is lost, and whether it matters at n ≈ 40

| Lost | Matters at n≈40? |
|---|---|
| Isolated per-setup B-REFUSED replays (W5.2a) | No. Capacity rarely binds on B (B trades ~once a week); the portfolio run enters nearly every refused setup anyway, and the spec already ruled the isolated layer diagnostic-only. |
| Scale monitor / `SCALE_DRIFT` deferral (W2.8) | Marginal. A 20-session rolling median over a 40-session program is two samples. A drifted θ* fails its bar instead of deferring — visible in the median-\|r30\| column. If the program runs to 100+ sessions, revisit. |
| `.code` lineage + `rebind` refusal | Small. A mid-program code change is caught by `verify` (bytes differ → refuse) and attributed by `git_sha`/`dirty` in `meta.json`. What you lose is the *automatic* refusal of every command until you prove identity; you get a warning line instead. |
| Snapshot chain ("ledger as of session N") | Nothing lost — per-session dirs give it for free and more cleanly. |
| Diagnostic CREDIT layer with flow exits held fixed | Nothing lost; the portfolio join gives the same per-trade Δ with *correct* exits. |
| MFE column | Nothing; no verdict uses it. |
| Official-settlement reconciliation (W6.4 `index_eod`) | Rare: only a bomb whose strike is within ~0.5 pt of the expiry close. The spec already accepted the 1-min close as the proxy. Print a one-line caveat on settlement rows. |
| Holiday CSV → list in payload | Nothing, as long as the list is right for 2026–27 (≈ 10 dates; write them once). |
| Writer lock | Nothing for one operator. |
| Per-row mark shas / `MarkTampered` | Nothing; `verify` catches any changed mark file. |
| Two review gates → one | Small. The second gate (after stats/verdicts/ledger) is replaced by the backfill reproducing the accounting doc's numbers, which is a stronger check than a reading. |

The real risk is different and the simplification *reduces* it: the more mechanism sits between the engine's events and the verdict, the more places a subtle bug can change a PROMOTE to a REJECT without anyone noticing at n = 40, where one trade moves the answer. Fewer transformations, all pure functions of `events.parquet`, is the safer design for a small-n program.

---

## 6. LINE BUDGET

| | Current spec (design §Overview) | Minimal |
|---|---|---|
| Modules | 13 + tests | 8 + tests |
| Code | ≈ 1,300 | ≈ 850 (cli 60, registration 50, shadow 120, tables 170, book 130, verdicts 130, ledger 110, report 80) |
| Tests | ≈ 500 (the "minimum list" in requirements is ~45 named tests) | ≈ 400 (~25 tests: baseline==log on 4 stored sessions; artifacts untouched; each hook on the engine's `v3_quotes_fixture.py` scenarios; panel dedup/precedence; NaN r30; lb95 3 cases; each verdict status on a fixture payload; firewall; checkpoint 9/10; ledger tmp/rename crash; chronology; re-run byte identity; UNMARKED; settle clamp/expiry-day; mark cache pull-once) |
| Engine runs per session | 12 nominal, 29 worst case | 9, always |
| Distinct mechanisms a junior must understand | ~22 | ~8 (hash, fingerprint, two hooks, two silencers, per-session dir, checkpoint filter) |
| **Total** | **≈ 1,800** | **≈ 1,250** |

The line count drops ~30%; the *concept* count drops ~60%, and that is the number that decides whether a junior can hold the whole thing in their head. The docs should shrink further than the code: a v2 requirements of ~180 lines (W0, W1 as a six-file list, W2 as "FeatureRow at the signal minute", W3–W5 definitions and bars verbatim, W6 without provenance/sha clauses, W7, W8 as one paragraph, W9 as one paragraph) and a design of ~150 lines (the two hooks with the code above, the per-session dir contract, the verdict function signatures, the test list). tasks.md becomes 7 tasks: harness → tables → book → verdicts → ledger/cli → tests+gate → register/backfill.

One thing to correct while revising, since it is load-bearing: requirements W2.6 and design §5 assert that MAE must be recomputed from the chain cache because the engine only logs liq-loss on heartbeats. The exit event carries `leg_liq_loss_usd` as the per-bar running maximum (executor.py:266 in `_update_marks`, called from `apply` on every bar the trade is open; emitted via `_trade_fields` at :58). Use it; do not build a second excursion calculator.

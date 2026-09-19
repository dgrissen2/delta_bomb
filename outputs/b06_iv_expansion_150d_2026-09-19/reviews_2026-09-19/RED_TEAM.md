# Red-team audit: B06 IV expansion

19 September 2026. Scope: `collect.py`, `iv_rules.py`, `recalculate.py`, transport
adapters and explicitly imported frozen study modules. Rubric:
`docs/adversarial_rubric.md`. Serena traced `evaluate_b06_day`; direct source
inspection and independent cached-data reconstruction covered the other paths.

**Verdict: FAIL for the intended “always above VT” research claim.** The frozen
opening-cohort calculations reproduce, but the intended intraday regime was not
enforced. The separately reported causal VT restrictions resolve the *audit
question*; they do not retroactively repair the original population or certify
a production trading implementation.

## Coverage matrix

| Vector | Code path / evidence | Check | Result |
|---|---|---|---|
| Path traversal / injection | `collect.request_key`, fixed internal methods/symbols; `iv_rules` AST execution | No shell interpolation in collection; cache keys are SHA256; archive trusted-local but executed before freeze verification | CONDITIONAL: no observed injection; latent trust-boundary weakness |
| NaN / Inf / bool coercion | `iv_rules.slopes`, `classify`, `resume_features.numeric_object_array` | Missing-window test; all recorded slope/basket values rebuilt; malformed count probes below | FAIL for strict direct-call input validation; observed integer callers unaffected |
| Unbounded memory | two-worker pools, finite selected dates, each panel processed separately | Code inspection and completed finite 1,615-panel run | PASS for scoped fixed study; arbitrary future unbounded chains not certified |
| Exception disclosure | `collect.authenticate`, cache errors, resume failures | Auth suppresses SDK output and returns exception type; remaining local error logs may contain internal paths | CONDITIONAL: local diagnostics expected; exhaustive SDK secret-disclosure behavior UNKNOWN |
| External input validation | native OHLC aggregation, surface preparation, manifest membership | 150 complete native sessions; source hashes; independent parent/price replay; 1,650 sector-day accounting | PASS for observed run; latent incomplete-manifest guards noted by Claude |
| Silent failure | three-state classification, logged missing panels and auth errors | 4,160 baskets rebuilt; all 1,040 outcomes and table totals reconcile | PASS for observed run; replay overwrite risk below |
| VT intent boundary | `PROTOCOL.md:13`, `replication.parents_for_day`, `evaluate_b06_day` | Every RTH low/close and every entry checked against same-date VT | FAIL: 80 below-VT entries, 54 days cross VT |
| Time causality | entry open after complete five-minute breakout; IV window T−35…T−6 | Independent signal reconstruction; prior-only VT gate excludes future prices | PASS for those calculations; full-day VT selection is descriptive only |
| First-touch objective | `screen.score_path` | Independently locate first up/down timestamps and ties across all 1,040 paths | PASS; no post-target reversal penalty |
| IV slopes / interpolation identity | native stored minute series, archived calculation functions | 44,812 available-panel feature rows reconstructed by least squares; original surfaces replayed by study/Claude checks | PASS for slopes/classifications; provider IV model correctness UNKNOWN |
| Missingness cascade | selected expiry brackets, full 11-sector grid | 1,615 panels + 35 missing = 1,650; 45,760 rows; 4,160 basket classifications | PASS; coverage is informative and not ignored |
| Registry drift | protocol, source hashes, original policy tables | All original parents/outcomes reproduced; original 5 rows reconcile | PASS for recorded data; protocol's opening cohort does not meet clarified intent |
| Inference / overfitting | original/new and date-stratified comparisons | Independent review plus exact date-mix decomposition, date/month bootstrap | CONDITIONAL; earlier sample explored, no causal proof of harm |
| Replay immutability | `recalculate.feature_stage` writes before `freeze_json` timestamp mismatch | Claude source trace, existing artifact hashes | FAIL for safe rerun design; not exercised after completed freeze |

## Findings

| Finding | Severity | Evidence and impact | Resolution / recommended test |
|---|---|---|---|
| Opening-above cohort was interpreted too broadly | HIGH | VT never enters the frozen B06 evaluator; 34 original and 46 added entries are below VT. The intended regime is wrong despite correct arithmetic. | Exact exception ledger plus entry-above and continuous-above-through-entry diagnostic tables. Future implementation must explicitly test a session that starts above then crosses below; preserve original evidence. |
| Re-running `features` can overwrite frozen outputs before raising | MEDIUM | Writes combined artifacts before checking timestamped freeze equality; unordered thread completion can change coverage bytes. All recorded hashes currently match. | Do not rerun writer stages on this snapshot. Use the separate read-only reconstruction and new namespace. A future version should verify/return before any writes and use deterministic ordering. |
| Count classifier is not strict about malformed direct inputs | MEDIUM | `classify(NaN,0)` returns unknown; `(True,False)` returns no; `(6.5,0)` returns yes. Existing callers aggregate integer sector counts; independent actual baskets match. | Future reusable helper should reject non-integer, bool and nonfinite counts. Does not explain this result. |
| Frozen-source execution precedes hash validation | LOW | Archive functions are compiled/executed at module import; current trusted archive matches the frozen hash. | Validate pinned archive hash before execution in a future version. Do not modify the frozen source to disguise its original behavior. |
| Incomplete-stage accounting is not always asserted in code | LOW | Missing selection could be silently absent; original ID check only detects missing original IDs, not extras. | Independent full-grid and exact-ID checks passed; add explicit sets/cardinality checks before future runs. |
| Prior uncertainty was underemphasized in conclusions | MEDIUM | Original intervals span zero; exploratory reuse; changed date/regime weights; negative 34-date 2026 point estimates do not identify cause. | Correct report wording and separate measured decompositions from economic hypotheses in AUDIT_FINDINGS.md. |

Severity uses the requested framework: an observed functional regime gap is HIGH;
latent robustness issues without observed data corruption are MEDIUM/LOW. No
verified corrupted IV arithmetic or altered success definition was found.

## Test evidence and limits

- `python -B -m unittest test_expansion test_transport`: 15 passed.
- `audit_frozen.py`: 150 SPX sessions/VT levels; 1,040 independently rebuilt B06
  parents and outcomes; 44,812 per-panel feature rows; all 4,160 baskets passed.
- `diagnose_shift.py`: exact decomposition identities; no outcome/IV parameter
  changes; date- and month-block intervals for opening, entry-above and
  continuous-above-through-entry scopes.
- Entry eligibility uses the next observed minute open; the prior five-minute
  signal close agrees on VT side for all 1,040 actual events.
- Full-session no-breach results are explicitly hindsight-conditioned, never
  presented as a deployable gate. A subsequent VT crossing is not retrospectively
  used to remove an earlier entry from the causal table.
- The absence of a verified arithmetic bug is not proof that the vendor IV values
  measure new option-market information. That remains a distinct measurement issue.

New rubric vectors recorded: open/entry/full-session regime confusion; replay
reproducing a flawed research assumption; opening-minute availability; and
extension dates being mistaken for an untouched holdout.

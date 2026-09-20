# Independent code review and verification record

Two completed Claude Opus 5/xhigh reviews returned **CONDITIONAL PASS** before
new outcome comparisons. Their findings prompted the changes below. A third
cohesive review of the revised implementation also returned **CONDITIONAL PASS**.
Its findings and dispositions are recorded below; the verdict is not promoted to
PASS based on local follow-up checks.

First review artifacts:
`/Users/dgrissen/.cache/agent-review-runs/20260919T231920Z-claude-review-diff-only-changes-in-outputs-branch_b_iv_full_2024_2026_2026-09-19-45864`.
Second review artifacts:
`/Users/dgrissen/.cache/agent-review-runs/20260919T234730Z-claude-review-diff-only-changes-in-outputs-branch_b_iv_full_2024_2026_2026-09-19-53752`.
Raw stdout/stderr copies are preserved in the central namespace's logs directory.

## First review: concrete repairs

1. Verify frozen receipt hashes before opening them, then trace derived files and
   native payloads back to those receipts. Check feature code and source identities.
2. Apply the canonical complete-prefix VT gate to every delayed entry. Missing
   earlier minute bars now reject the calculation rather than passing a vacuous test.
3. Use the tested three-state count/conjunction functions in production basket rules.
4. Revalidate already retrieved issuer bytes independently of their original
   acceptance status, under a separately versioned parser output. This fetched no
   new data: 404 dates remain accepted and 17 retrieved bodies remain rejected.
5. Handle an empty opportunity union as a boolean row selection.
6. Check the actual 411-date primary population rather than relying on a hardcoded
   completion claim. Preserve the separate ten-date development group.
7. Reject Python optimization mode, which could disable the inherited assertions.
8. Align weighted classifications by date/minute index, not by array position.
9. Normalize the two inherited expiry-manifest schemas without rewriting them.
10. Require all 45,760 old sector/policy measurements to overlap the replay, rather
    than letting an empty intersection appear to pass.
11. Preserve rejected HTTP bodies as raw retrieval evidence; only separately
    validated weights can enter a calculation. This is intentional, not a cleanup.
12. Return an explicit empty weights schema if all issuer snapshots are rejected.

## Second review: concrete repairs and dispositions

1. Suppress both rate and difference confidence intervals when their contributing
   samples have fewer than two dates or no outcome variation. A tiny perfect sample
   must not acquire a precise-looking effect estimate.
2. Check the matching freeze's input hashes as well as output hashes.
3. Share the rule/scope definitions between matching and analysis. Record every
   completed matching stratum and reconcile its pair count, including explicit
   `no_comparable_pairs` cases.
4. Add an expanded execution freeze covering the actual IV reconstruction stored
   inside evidence.json, native transport/calendar helpers, matching algorithm,
   price gate/scorer, all local Python files, and the scope documents. It is frozen
   before event-feature assembly and new outcome comparisons. Native derivation
   occurred earlier, so the audit also checks original surfaces and legacy results;
   the later freeze is not misrepresented as predating those downloads.
5. Make numerical CSV outputs immutable and hash every published analysis table.
   The verification report pins those exact bytes; rendering checks those hashes.
6. Show distinct dates in every half-year cell, alongside wins/N and percentage.
   State explicitly that intervals are pooled only and small-date half-year cells
   cannot establish repeatability.
7. Expand independent feature checks to all five quote policies, all four surface
   descriptors, full/half slopes, acceleration, endpoints, price returns, bid/ask
   envelopes, breakout updates and post-entry observations. Balanced recovery is
   independently reselected and fitted on unique actual timestamps. Full scalar
   comparisons include missingness, not merely finite coincidences.
8. Include development dates in the explicitly labeled cohort table while keeping
   them out of primary pooled, matching and contextual comparisons.
9. Verify delayed-entry inputs and fail if any parent loses its basket context in
   the join. Keep new entry price, complete VT prefix and new 60-minute score.
10. Deliver scope documents alongside the implementation. Temporary review indexes
    are code-only review inputs and do not define the final commit contents.
11. Reconstruct listed expirations from the hashed native contracts response itself,
    avoiding a tautological check when an inherited field held selected expiries.
12. Include price-only controls in measured-baseline and uncertainty calculations;
    display the reason an interval is unavailable.
13. Remove the history phase from this command's public CLI. No MAD collection is
    part of this experiment; the earlier calendar remains useful for dated weights.
14. Treat an orphan response body without a successful retrieval digest as
    unverified, rather than raising KeyError or admitting it as historical weights.

The five new failure-path tests were run first and failed for their intended
reasons; after the repairs, all 21 scoped tests and Ruff passed. Prior source
versions remain under central `source_snapshots/`. No winning percentage was used
to choose these repairs or revise a trading threshold.

## Review transport adjustment

One newly launched review was stopped after the default payload limit planned
16 separate file reviews. It was immediately relaunched with a 160 KB payload
budget as one cohesive implementation review. This was an operational scope
adjustment before a verdict, not rejection of an unfavorable reviewer result.
The interrupted attempt and reason remain in logs/review_batch_adjustment.json.

## Final review: CONDITIONAL PASS, sixteen implementation files

Artifacts:
`/Users/dgrissen/.cache/agent-review-runs/20260920T003421Z-claude-review-diff-only-changes-in-outputs-branch_b_iv_full_2024_2026_2026-09-19-66770`.
The exact report is preserved centrally in logs/claude_review_complete.stdout.

| Finding | Disposition |
|---|---|
| Four quote-envelope rules have zero qualifiers | Explicitly marked in the findings and result tables. They were evaluated and did not qualify; NaN means N=0. We do not adopt the stronger claim that qualification is mathematically impossible on every conceivable dataset. |
| Structural and quote-quality unknowns are conflated | Added entry_missingness_context.parquet and unknown_reason_summary.csv for all 104 original-entry rules. They separate 741 before-10:05 recipe entries, rejected issuer snapshots and remaining unresolved quote/expiry conditions. No outcome classifications changed. |
| Registration sentinel is written before root registries | Original reviewed writer preserved; register_data_safe.py supersedes it. A durable transaction plan allows roll-forward after interruption; each destination is atomically replaced, conflicting intervening edits abort, and inventory.json is last. Two targeted tests first failed, then passed, including a simulated interruption and an unrelated intervening edit. |
| Unknown-cohort performance is absent from the headline display | Added yes/no/unknown/measured/baseline results for the principal B06, B07, B09 and B10 rules to RESULT_TABLES.md and the findings. Complete per-rule/family values are in unknown_performance_summary.csv. Family-level pooled entries overlap and are not claimed as unique executions. |
| Retention can be misread under first/spaced selection | Explicit caveat beside delivery tables: these columns count common winning date/minute identities. They do not count a replacement trade as retained. The original headline tables are all-entry tables, where the subset interpretation is literal. |
| Original pair_id repeats between strata | Preserve original artifacts; add matched_pairs_canonical.parquet with unique rule/scope/stratum/pair_id keys. All 3,524 canonical IDs are unique. Existing results join scores by event identities within groups and are unaffected. |
| Hypothetical colliding freeze keys | Audit all eleven current top-level freeze/completion/verification manifests: zero inconsistent expectations. No result is affected. The original generic merge helper remains preserved in the frozen implementation; future reuse must not introduce conflicting expectations. |
| Missing historical HTTP status defaults to success in old receipts | Added issuer_http_provenance.csv labeling fifty reused bodies as validated cache with unrecorded HTTP status. Acceptance still depends on unchanged payload parsing. We do not claim a recorded HTTP 200 for those bodies. |
| Prior-session index could wrap at calendar start | Confirmed all 421 actual issuer as-of dates precede their target dates; selected dates have the sixty-session warmup and never hit the first calendar element. The unreachable generic edge remains a future-collector constraint, not an unreported current look-ahead. |

The additive audit and reporting helpers do not regenerate or change the strategy
tables. They recheck the verified hashes and write new explanatory artifacts.
The independent numerical audit passed all 97,656 summary rows, 1,848 union rows,
312 prior score rows, 45,760 original sector/policy measures and 68,000 sampled
feature scalars. Final local checks: 23 tests and Ruff. The new metadata/reporting
helpers did not receive a separate fourth Claude review.

The Markdown renderer initially lacked optional tabulate in the working Python
environment. An existing installed tabulate 0.10.0 package and its distribution
metadata were made discoverable after the working environment's normal paths.
No shared package installation or numeric source changed. Both failed render logs
and the successful render dependency receipt are retained.

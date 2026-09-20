# Independent review execution and proposal revision

The original research results remain in project commit 1948538 and central commit
8bcb070; Charlie-framework proposal e083ba7 is preserved as the pre-review snapshot.
This commit executes the previously saved review request, stores both actual
Claude outputs and their execution metadata, revises the proposal, and appends
six detailed learnings in the canonical notebook. It does not change original
48-cell results, price triggers, measurement code, dashboards or raw data.

Actual verdicts: original FAIL (12 findings), revised CONDITIONAL PASS (7 findings).
The final author response narrows claims and specifies coverage, sparse-result and
shared-window conditions. No third review or unconditional approval is claimed.
The first reviewer’s linear-payoff substitution was rejected; the recheck accepted
the user's first +5 before −10 objective and reproduced the amended arithmetic.

Both original/reviewed proposal snapshots and full reviewer outputs are retained,
with SHA-256 in REVIEW_EXECUTION.json and external execution artifact directories.
The reviewer's unauthorized replay of two proposed B09 sign controls is disclosed:
those outcomes are now observed, not prospective. No B07/B05 or SPX strategy tests
were executed. SPX measurement collection remains separately authorized and active.

Verification: primary counts and uncertainty values reconciled; both review wrapper
runs exited successfully; documentation diff checked. No numerical source files
were edited. This is a strategy/logic review, not a substitute for a full independent
code audit. See REVIEW_RESPONSE.md for all 19 finding dispositions and LEARNING_NOTE.md
for the canonical note added by this commit.

## Original proposal commit notes — historical, superseded where revised above

Propose bounded B07/B05 MAD transfers and an SPX IV disagreement test

Preserve the distinction between completed B09 evidence and proposed follow-up
research. Results/learning commit 1948538 and central metadata commit 8bcb070
already record the 48-cell study; this commit adds no new overlay outcome test.

Apply the canonical Charlie market-structure framework within the current
conversation. Treat the mechanism as a hypothesis about contemporaneous IV
information, not a measurement of dealer inventories or forced fund flows.

Fix the first transfer round to B07 failed breakdown/reclaim and B05 stall/reclaim.
Carry forward only M > 1 in at least four of eleven sectors, with and without
the same-sector recent-IV-slope-below-zero requirement. Preserve the five-sector
winners as accuracy references rather than expanding the transfer sweep.

B07 tests whether a failed selloff accompanied by IV relaxation improves +5-first
outcomes. B05 offers a larger existing parent pool: 1,537 events versus B07's 415
and B03's 189 during the matched 2025-2026 period. Those are baseline counts,
not evidence that the new overlay succeeds. Explicitly retain B05's weak partial
2026-H2 baseline and B09's weak partial-H2 overlay evidence. Explain why the current
high-N objective favors B05 over the older persona-panel B03 challenger.

Declare four primary transfer cells and four same-measurement, same-clock raw-sign
controls. The latter isolate the MAD magnitude requirement from falling IV and
negative acceleration alone. No new thresholds, parent changes, sector weights,
cooldowns, expiry tenors, or post-target persistence score. Reuse the causal
above-VT gate, T-1 source clock, +5-before-minus-10/60-minute outcome, explicit
unknown groups, filter-before-thinning policies and completed-half stability test.

Propose one SPXW 30-calendar-day ATM midpoint-IV acceleration MAD feature on B09,
using the same current-window and 60-prior-session normalization principles.
Specify M_SPX > 1 and recent slope < -1e-12, without a threshold/tenor/delta sweep.
Cross-classify against fixed sector F4, keeping sector-negative/SPX-positive
incremental opportunities separate from sector-unknown coverage recovery.
Predeclare one descriptive OR comparison, deduplicated and spaced consistently.
Neither a larger N nor a better agreement group proves the added entries help.

Document bounded SPX cache inspection: the first-order gamma cache has 1,065
Parquets in 0DTE, next-daily, and 3-to-5-DTE buckets; recent put marks have no
native IV fields. These observations do not establish a ready 30-day SPX MAD
dataset. Require an actual coverage inventory, settlement/contract verification,
source-time and interpolation checks, and the full calibration history before
outcome testing. Future data belong under central_trade_data with dictionary
and changelog registration. No market-data collection occurred in this work.

Record the requested independent Claude strategy review as NOT RUN / PENDING:
the side-conversation developer restriction prohibits separate reviewer agents,
including an independent CLI reviewer process. Read the requested skill, prepare
a concrete evidence-based review request, and do not fabricate a verdict, claim
independent Charlie approval, or call an unattempted review a tooling failure.

Validation: reconcile proposal parent counts to the existing comparison table;
check all local Markdown links and scoped whitespace. No execution code changes
or new strategy tests. Preserve all unrelated working changes and existing
frozen experiment/data payloads.

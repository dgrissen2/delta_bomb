# B06 IV comparison: expand fifty dates to 150

Frozen 19 September 2026 before new sampling, option collection, feature generation, or outcomes. User authorized committing the fixed set, fetching 100 more above-VT days in 2025–2026, and recalculating the five-row table.

## Fixed comparison

Carry all rows in [the committed comparison set](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_recovery_findings_2026-09-19/ACTIVE_COMPARISON_SET.md): baseline, original, midpoint, guarded_100, guarded_50. The exact historical experiment and rule constants are archived in evidence.json. Do not alter B06, entry/scoring, IV interpolation, derivative, sector threshold, sample completeness, or quality thresholds to improve results. There is no new model, parameter optimization, persistence score, or post-target veto.

## Population and sampling

Use available same-date recorded SPX Vol Trigger dates from 2025-01-01 through 2026-09-18 (last completed session before this request), from the existing corrected historical VT CSV. Check same-date pre-open founder-note provenance using the existing audit logic. No future note, guessed threshold, backward fill, or carried-forward VT. Preserve missing/conflicting records in the population ledger.

Eligibility stays the original observed 09:30 SPX minute OPEN strictly above positive same-date VT and a complete, valid, unique 390-minute RTH session. This is an opening cohort, not an intraday entry gate. Inventory the entire recorded date universe before sampling, completing missing native SPX coverage through the ThetaData SDK so selective cache availability does not determine the draw. Preserve raw timestamps and partial-day exclusions; never infer/fill a minute.

Exclude all original fifty dates and the ten earlier exploration dates. Draw 100 uniformly without replacement from the remaining eligible dates with a once-generated, stored random seed. No year quota or result-driven date choice. Freeze population ledger, eligibility, source hashes, seed, draw order, and sorted selection before option coverage or outcomes. Never replace a sampled date because of B06 count, option quality, missing expiry, or outcome. If fewer than 100 are eligible, record the actual shortfall rather than silently loosening the rule.

Existing source publication labels and corrected VT archives do not establish contemporaneous ingestion or absence of revisions; preserve this inherited limitation.

## Storage and retrieval

New research slug: /Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_expansion_150d_2026-09-19/

New raw-data root: /Users/dgrissen/Dev/central_trade_data/thetadata/b06_iv_expansion_150d_2026-09-19-v1/

Existing fifty-day raw caches and outputs remain read-only. Reuse exact matching cached inputs after hash/parameter validation. Preserve new raw responses, request parameters, native timestamps, source hashes, SDK version and retrieval times centrally. Use the ThetaData Python SDK, native 1m option IV and first-order Greeks, the same eleven ETFs, both rights, strike_range30, 09:30–14:29 ET, SOFR and version latest. Select nearest expiry brackets around 30 calendar DTE within 8–65 using dated contract listings; exact30 uses one. No extrapolation.

At most two concurrent SDK requests. Base collection ceilings: 100 dated contract listings plus at most 4,400 option-history calls, and at most 500 SPX coverage calls. Reuse reduces requests. Log failures; at most one explicitly logged retry for a transient timeout, rate-limit, or server error, without changing dates or parameters. Permanent errors remain missing and are disclosed. Never log credentials. No new subscription or paid purchase is authorized or required by this protocol.

## Calculation, reporting, and uncertainty

Reproduce all five original fifty-day rows before trusting the expanded implementation. Preserve features and classifications before joining the frozen score. Report at least:
- original fifty days;
- additional 100 days separately;
- combined 150 unique days;
- 2025 and 2026 descriptive counts/rates;
- signals, target/adverse/neither/ambiguous outcomes, hit rate, uplift versus the identical-cohort B06 baseline, and active dates;
- missing/unknown coverage and eligibility exclusions.

The table's IV rows mean confirmed falling-plus-accelerating in at least six sectors, not falling alone. Broad-falling results may be a labeled diagnostic but cannot replace the fixed five-row table.

Use paired whole-date bootstrap draws (10,000, seed 20260919) within each reported cohort, retaining zero-entry dates. Report target-rate differences and intervals with undefined draws explicit. Dates, not individual overlapping entries, are resampling units. Keep unknown states distinct. Same-minute target/adverse ties retain the original scorer's ambiguity rule.

Additional dates are new to this specific comparison, not guaranteed unseen across the wider research project. The combined result blends exploratory and additional data; the new-100 result is the cleaner extension check. No holdout is invented and no thresholds are retuned after either table.

## Verification and completion

Reuse the original scoring and preparation functions where possible; isolate extensions in this slug. Add targeted tests for sampling uniqueness/exclusions, no date replacement, fixed quality boundaries, incomplete samples, score reproduction, and table reconciliation. Verify original source hashes and preserve the raw cache.

Commit the comparison set and this protocol first, with extensive rationale. Then complete retrieval and calculation, document failures/coverage and exact results, and preserve the reproducible expansion artifacts. This request changes research artifacts only; it does not authorize changing the dashboard's selected live filters.

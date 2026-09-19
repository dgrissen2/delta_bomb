# B06 / sector IV: fixed-rule expansion from fifty to 150 dates

**Audit correction (19 September 2026): these frozen tables describe days opening
above VT, not entries continuously above VT. The audit found 80 below-VT entries
and 54 days that crossed VT. Read [the audit and corrected scope comparisons](reviews_2026-09-19/AUDIT_FINDINGS.md)
before interpreting these results. Original tables are preserved.**

Completed 19 September 2026. Comparison-set and sampling-protocol commit: **998c31b**.
Central data/provenance commit: **b6b5057** in central_trade_data.
All four IV policies are retained, including bid-IV recovery. The original five-row table
reproduces exactly before assessing the new results.

**The score is SPX +5 before −15 within sixty native minute intervals. Later reversal does
not change a successful first move. Accuracy is first priority; opportunity count is second.**

## CIO reading

**The apparent IV advantage did not carry to the additional data.** On the 100 additional dates,
plain B06 reached +5 first on 371/666 signals, 55.7%. All four frozen IV requirements had lower observed hit rates:
50.0% original, 51.8% bid-IV recovery, 52.8% with the 100% guard and 50.5% with the 50% guard. None beat plain B06
in the pooled 150 days either. The filters reduced opportunities without increasing observed
accuracy. The earlier 50-day percentages reproduced exactly; they were not corrected away.
They were an encouraging result that failed this extension check.

The 34 newly added 2026 dates also provide no positive replication evidence. On those dates,
plain B06 scored 141/224, 62.9%; the four filters scored 58.0%, 58.6%, 55.3% and 54.5%.
This small subgroup cannot separate a regime effect from sample fragility.
The positive-looking pooled 2026 rows further below include the original 50 dates and must
not be mistaken for a successful replication within 2026.

These results do not support making any of these four IV conditions a required B06 filter.
For the additional 100 days, the original policy’s uplift interval is −11.0 to −0.4 percentage points; the other three
additional-100-day intervals include zero. All pooled-150-day intervals include zero. This does not establish
that IV is harmful or that every possible IV idea is useless. The original 69.6–75.9% observations are not a
reliable basis for expecting higher accuracy from these unchanged rules. We did not select
new thresholds, discard difficult dates or redefine success to recover the earlier result.

## Combined 150-day table

| Rule | Signals | +5 first | Hit rate | Uplift vs B06, pp | Active days | 95% uplift interval, pp |
| --- | --- | --- | --- | --- | --- | --- |
| Plain B06 | 1040 | 610 | 58.7% | +0.0 | 149 | — |
| Original IV validity | 301 | 171 | 56.8% | -1.8 | 121 | -6.6 to +2.7 |
| Allow recovery when bid IV fails | 340 | 196 | 57.6% | -1.0 | 127 | -5.5 to +3.3 |
| Recovery + guards, 100% spread ceiling | 228 | 133 | 58.3% | -0.3 | 102 | -6.1 to +5.3 |
| Recovery + guards, 50% spread ceiling | 128 | 72 | 56.2% | -2.4 | 69 | -10.4 to +5.4 |

These are 1040 distinct B06 parent signals on
149 active dates out of 150 sampled dates.
The IV rows are overlapping selections of this identical baseline, not independent experiments.

## Additional 100 days: the extension check

| Rule | Signals | +5 first | Hit rate | Uplift vs B06, pp | Active days | 95% uplift interval, pp |
| --- | --- | --- | --- | --- | --- | --- |
| Plain B06 | 666 | 371 | 55.7% | +0.0 | 100 | — |
| Original IV validity | 208 | 104 | 50.0% | -5.7 | 86 | -11.0 to -0.4 |
| Allow recovery when bid IV fails | 228 | 118 | 51.8% | -4.0 | 88 | -9.0 to +1.1 |
| Recovery + guards, 100% spread ceiling | 159 | 84 | 52.8% | -2.9 | 70 | -9.7 to +4.0 |
| Recovery + guards, 50% spread ceiling | 99 | 50 | 50.5% | -5.2 | 52 | -14.4 to +3.5 |

This cohort contains 666 signals on the newly sampled dates.
It is the cleaner check of whether the original result carries to additional data. The
combined table blends previously examined dates and extension dates. Do not present pooled
accuracy alone as proof of replication.

## Original fifty days: unchanged reference

| Rule | Signals | +5 first | Hit rate | Uplift vs B06, pp | Active days | 95% uplift interval, pp |
| --- | --- | --- | --- | --- | --- | --- |
| Plain B06 | 374 | 239 | 63.9% | +0.0 | 49 | — |
| Original IV validity | 93 | 67 | 72.0% | +8.1 | 35 | -0.9 to +17.5 |
| Allow recovery when bid IV fails | 112 | 78 | 69.6% | +5.7 | 39 | -2.8 to +14.3 |
| Recovery + guards, 100% spread ceiling | 69 | 49 | 71.0% | +7.1 | 32 | -3.2 to +18.1 |
| Recovery + guards, 50% spread ceiling | 29 | 22 | 75.9% | +12.0 | 17 | -3.1 to +27.7 |

All original counts, targets, adverse outcomes, neither outcomes, active dates, and individual
outcome labels reproduce. Old-versus-new sample comparisons have different date composition;
the additional dates were not chosen based on results.

## How the apparent advantage changed

| Rule | New-100 uplift, pp | Combined uplift, pp | Original hit rate → new hit rate |
| --- | --- | --- | --- |
| Original IV validity | -5.71 | -1.84 | 72.0% → 50.0% |
| Allow recovery when bid IV fails | -3.95 | -1.01 | 69.6% → 51.8% |
| Recovery + guards, 100% spread ceiling | -2.88 | -0.32 | 71.0% → 52.8% |
| Recovery + guards, 50% spread ceiling | -5.20 | -2.40 | 75.9% → 50.5% |

Each uplift compares the IV row with plain B06 on the same cohort. The table shows the result
for every frozen candidate without retuning the six-sector threshold, derivative, window,
spread ceiling, missing-data treatment, or score. A higher row percentage does not by itself
prove a better future policy. Intervals and opportunity counts remain part of the comparison.

## Calendar-year descriptions

### All included 2025 dates

| Rule | Signals | +5 first | Hit rate | Uplift vs B06, pp | Active days | 95% uplift interval, pp |
| --- | --- | --- | --- | --- | --- | --- |
| Plain B06 | 442 | 230 | 52.0% | +0.0 | 66 | — |
| Original IV validity | 158 | 75 | 47.5% | -4.6 | 60 | -10.7 to +1.6 |
| Allow recovery when bid IV fails | 170 | 84 | 49.4% | -2.6 | 61 | -8.1 to +3.1 |
| Recovery + guards, 100% spread ceiling | 121 | 63 | 52.1% | +0.0 | 50 | -8.2 to +8.2 |
| Recovery + guards, 50% spread ceiling | 77 | 38 | 49.4% | -2.7 | 41 | -13.2 to +7.9 |

### All included 2026 dates

| Rule | Signals | +5 first | Hit rate | Uplift vs B06, pp | Active days | 95% uplift interval, pp |
| --- | --- | --- | --- | --- | --- | --- |
| Plain B06 | 598 | 380 | 63.5% | +0.0 | 83 | — |
| Original IV validity | 143 | 96 | 67.1% | +3.6 | 61 | -3.4 to +10.7 |
| Allow recovery when bid IV fails | 170 | 112 | 65.9% | +2.3 | 66 | -4.4 to +9.0 |
| Recovery + guards, 100% spread ceiling | 107 | 70 | 65.4% | +1.9 | 52 | -6.3 to +10.0 |
| Recovery + guards, 50% spread ceiling | 51 | 34 | 66.7% | +3.1 | 28 | -9.3 to +14.3 |

The combined sample contains 66 dates from 2025 and
84 from 2026. These are descriptive strata; no policy
was selected or changed by year. The new 100 contain 66 dates from 2025 and 34 from 2026.
The original fifty are all in 2026.

### The 34 additional dates from 2026, excluding the original fifty

| Rule | Signals | +5 first | Hit rate |
| --- | --- | --- | --- |
| Plain B06 | 224 | 141 | 62.9% |
| Original IV validity | 50 | 29 | 58.0% |
| Allow recovery when bid IV fails | 58 | 34 | 58.6% |
| Recovery + guards, 100% spread ceiling | 38 | 21 | 55.3% |
| Recovery + guards, 50% spread ceiling | 22 | 12 | 54.5% |

This is a descriptive subtraction of the already reported disjoint counts
(additional 100 minus included 2025), with no new selection rule or optimized threshold.
Every IV row trails the 62.9% B06 baseline here too. The small filtered counts are visible;
no new subgroup significance claim is made.

## Exact working rules

The [fixed comparison set](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_recovery_findings_2026-09-19/ACTIVE_COMPARISON_SET.md)
and [earlier extensive findings](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_recovery_findings_2026-09-19/FINDINGS.md)
define the complete logic and earlier evidence.

- Baseline: completed five-minute B06 close above the prior six-bar high; original immediate
  parent generation, entry minute open, distinct-boundary rule, and decision cutoff.
- All IV rows: the same eleven ETFs; constant thirty-calendar-day spot-ATM midpoint IV;
  log-strike variance, expiry total-variance, and call/put variance interpolation; no time fill.
- Per ETF require all thirty actual T−35…T−6 samples, excluding the breakout candle. Fit a
  slope in each fifteen-sample half: b = Σ(i−7)IV_i/280. Acceleration = (b2−b1)/15.
  The same six or more sectors must have b2 < −1e−12 and acceleration < −1e−12.
- Original validity keeps positive ordered bid/mid/ask IV and dollar quotes, endpoint and
  underlying alignment, underlying age, and original expiry/strike checks.
- Midpoint recovery drops only the bid-IV validity and bid-IV≤midpoint-IV requirements.
  Zero dollar bids remain rejected; midpoint and ask IV still must be positive and ordered.
- Guarded versions use midpoint-selected constituents with spread/provider-midpoint ≤1.00
  or ≤0.50, respectively. Require positive ordered same-contract quotes exactly one minute
  earlier. Reject bid<0.50×prior bid with ask≥0.90×prior ask, or ask>2×prior ask with
  bid≤1.10×prior bid. No farther-strike substitution to evade a failed guard.
- Basket membership: yes if known qualifiers≥6; no if qualifiers+missing<6; unknown otherwise.
  Fixed denominator eleven. Unknown is never silently relabeled as no or failure.

## Unknown coverage remains explicit

| Cohort | Rule | Yes | Definite no | Unknown |
| --- | --- | --- | --- | --- |
| original_50 | Original IV validity | 93 | 216 | 65 |
| original_50 | Allow recovery when bid IV fails | 112 | 238 | 24 |
| original_50 | Recovery + guards, 100% spread ceiling | 69 | 169 | 136 |
| original_50 | Recovery + guards, 50% spread ceiling | 29 | 103 | 242 |
| additional_100 | Original IV validity | 208 | 358 | 100 |
| additional_100 | Allow recovery when bid IV fails | 228 | 388 | 50 |
| additional_100 | Recovery + guards, 100% spread ceiling | 159 | 288 | 219 |
| additional_100 | Recovery + guards, 50% spread ceiling | 99 | 198 | 369 |
| combined_150 | Original IV validity | 301 | 574 | 165 |
| combined_150 | Allow recovery when bid IV fails | 340 | 626 | 74 |
| combined_150 | Recovery + guards, 100% spread ceiling | 228 | 457 | 355 |
| combined_150 | Recovery + guards, 50% spread ceiling | 128 | 301 | 611 |

Each row sums to its cohort's complete B06 population. Missing sectors do not automatically
exclude an entire date: six other known qualifiers can still establish yes.

### Valid minute coverage and the cost of guards

| Cohort | Rule | Valid sector-minutes | Recovered from original gaps | Originally valid minutes lost |
| --- | --- | --- | --- | --- |
| additional_100 | Recovery + guards, 100% spread ceiling | 290948 | 1849 | 23644 |
| additional_100 | Recovery + guards, 50% spread ceiling | 245469 | 542 | 67816 |
| additional_100 | Allow recovery when bid IV fails | 321593 | 8850 | 0 |
| additional_100 | Original IV validity | 312743 | 0 | 0 |
| original_50 | Recovery + guards, 100% spread ceiling | 140162 | 810 | 15881 |
| original_50 | Recovery + guards, 50% spread ceiling | 108929 | 23 | 46327 |
| original_50 | Allow recovery when bid IV fails | 160137 | 4904 | 0 |
| original_50 | Original IV validity | 155233 | 0 | 0 |

Recoverability is not an independent certification that midpoint IV reflects a fair quote.
The quote guards can remove plausible as well as distorted observations, and complete
thirty-minute support compounds their coverage cost. This experiment compares the four
fixed measurement policies; it does not tune a new quote-quality threshold.
Capture starts at 09:30, so the previous-minute guard cannot validate 09:30. The eighteen
10:05 B06 parents in the full set include that minute in their IV window and therefore
cannot qualify under either guarded policy. This inherited timing exclusion is preserved.

## Complete outcome accounting

| Cohort | Rule | Signals | Target first | Adverse first | Neither | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- |
| original_50 | Plain B06 | 374 | 239 | 51 | 84 | 0 |
| original_50 | Original IV validity | 93 | 67 | 13 | 13 | 0 |
| original_50 | Allow recovery when bid IV fails | 112 | 78 | 15 | 19 | 0 |
| original_50 | Recovery + guards, 100% spread ceiling | 69 | 49 | 9 | 11 | 0 |
| original_50 | Recovery + guards, 50% spread ceiling | 29 | 22 | 4 | 3 | 0 |
| additional_100 | Plain B06 | 666 | 371 | 72 | 223 | 0 |
| additional_100 | Original IV validity | 208 | 104 | 30 | 74 | 0 |
| additional_100 | Allow recovery when bid IV fails | 228 | 118 | 31 | 79 | 0 |
| additional_100 | Recovery + guards, 100% spread ceiling | 159 | 84 | 22 | 53 | 0 |
| additional_100 | Recovery + guards, 50% spread ceiling | 99 | 50 | 8 | 41 | 0 |
| combined_150 | Plain B06 | 1040 | 610 | 123 | 307 | 0 |
| combined_150 | Original IV validity | 301 | 171 | 43 | 87 | 0 |
| combined_150 | Allow recovery when bid IV fails | 340 | 196 | 46 | 98 | 0 |
| combined_150 | Recovery + guards, 100% spread ceiling | 228 | 133 | 31 | 64 | 0 |
| combined_150 | Recovery + guards, 50% spread ceiling | 128 | 72 | 12 | 44 | 0 |

Neither and ambiguous remain in each rate's denominator as non-target outcomes. Same-minute
first touches of both barriers retain the original ambiguous classification, without an
invented intraminute ordering. No post-target observation affects these tables.

## Sampling and collection

There were 424 recorded VT dates in the requested window and
104 eligible new dates under the inherited complete-session,
same-date pre-open corroboration, and above-VT-at-09:30-open criteria. One uniform sample of
100 was drawn without replacement using seed **16327036225962936691**, excluding both the original
fifty and earlier ten exploration dates. Four eligible dates were not drawn. No sampled
day was replaced because of its signals, option coverage, or outcome.

See [SAMPLING.md](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_expansion_150d_2026-09-19/SAMPLING.md) for the month distribution and exclusions.
The VT archive ends September 11, 2026. The sample is not balanced across 2025–2026 regimes:
most included 2025 dates are August–December, with eight in February and none in March–July.
The original archive/provenance limitations remain; “available same-date pre-open note”
does not certify contemporaneous local capture or lack of later revision.

All 100 dated option listings were retrieved. There are 22 new sector-days
without an allowed expiry bracket (twenty XLRE, two XLB). For example, February 14, 2025 has
7-DTE and 35-DTE contracts for XLB and XLRE; the fixed eight-day minimum excludes the former,
leaving no bracket around thirty. This is a rule-imposed gap, not a failed request.

Collection ended **complete** with **1941 expiry pairs** and
**0 failed pairs**. Final prepared coverage is **1615
sector-days** with **35 missing/invalid sector-days** across 150×11.
Per-panel reasons are in missing_panels.csv; request-level details remain in collection_manifest.json.

New native one-minute responses, original parameters, SDK metadata, timestamps, hashes,
derived minute and event series, sampling records, and final comparison data are stored in
/Users/dgrissen/Dev/central_trade_data/thetadata/b06_iv_expansion_150d_2026-09-19-v1/.
Original caches remain read-only. The collection uses the ThetaData Python SDK 1.0.9, both
rights, strike_range30, 09:30–14:29 ET, SOFR, latest version, and at most two concurrent calls.
The initial collection encountered SDK authentication errors. The interrupted manifest and
request log are retained; a transport-only resume adapter renews the session every five
minutes, retains the two-attempt ceiling, and reads successful cached responses without
refetching. See [TRANSPORT_RECOVERY.md](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_expansion_150d_2026-09-19/TRANSPORT_RECOVERY.md).

## Uncertainty

Intervals use 10,000 shared whole-date bootstrap draws, seed20260919, within each displayed
cohort. They retain zero-entry dates and account for same-day overlapping signals through
date resampling; they do not assume independent entries. Each group's resampled denominator
is its own selected count. Defined-draw counts and complete endpoints are in
paired_date_bootstrap.json.

The four rules were fixed before this extension. No threshold was selected from these
results. They originate in earlier exploratory research, so these intervals are not adjusted
for the full history of hypothesis selection, cross-date regime dependence, or the universe's
provenance/coverage restrictions. Newly added dates are new to this comparison, not certified
unseen across every earlier project. No claim about sustained rallies or option execution
is required for, or inferred from, the +5-first score.

## Verification and reproducibility

- Original 374 parent identities and prices reproduced before new outcome calculation.
- All 537 original surface panels reproduced from raw data.
- Original availability, acceleration values, and all policy classification counts checked
  before joining outcomes; the full original five-row result then reproduced exactly.
- Ten frozen guard boundary checks, sampling freeze/no-reroll checks, missing-sample checks,
  and first-touch/ambiguous/later-reversal scoring tests pass.
- 4 real-data prefix checks remove future observations and
  verify earlier midpoint/guard values stay unchanged.
- Features and basket membership were saved and hashed before the new outcome join.
- The final comparison encountered a numeric column stored as pandas object dtype after
  concatenating zero-row panels. A recorded adapter converts already-numeric validation
  containers to float64; it rejects nonnumeric values and preserves the exact original
  tolerance. No data value, classification or frozen calculation source was changed.
- 5848 raw input hashes were verified unchanged.
- The source adapter imports the exact three rule functions from the committed experiment
  archive. It never executes that archive's earlier study main body.
- No dashboard or main-thread research filter was changed.

Important files: PROTOCOL.md, SAMPLING.md, selected_days.csv, combined_days.csv,
population_ledger.csv, sampling_manifest.json, parent_freeze.json,
feature_freeze_before_outcomes.json, comparison_table.csv, state_summary.csv,
event_ledger.csv, event_paths.csv, daily_counts.csv, paired_date_bootstrap.json,
surface_coverage.csv, missing_panels.csv, and verification.json.

Execution order, using the existing Python environment in this study directory:

    python -B collect.py sample
    python -B resume_collect.py
    python -B recalculate.py parents
    python -B recalculate.py features --watch
    python -B resume_features.py  # numeric-container compatibility for final validation
    python -B recalculate.py analyze
    python -B report.py
    python -B archive_data.py

The collector resumes exact cached requests, and the sample refuses changed frozen inputs.
Existing source modules and central raw caches are required; a documentation checkout alone
is not the complete data distribution. The per-sector derived files retain auditability
without copying the raw options cache into Git.
This completed version is a frozen snapshot. The sequence records how it was produced;
do not overwrite its finalized feature freeze to rerun it. Use a new namespace for a replay
that writes new artifacts, and retain these frozen results for comparison.
The central dataset README, detailed data dictionary, archive manifest and inventory identify
the canonical files. The root central_trade_data CHANGELOG.md and DATA_DICTIONARY.md also
record the completed capture and storage moves. Project data filenames are links to the
central files. Frozen snapshots should be read as immutable evidence; a new experiment or
changed capture belongs in a new namespace rather than overwriting this version.

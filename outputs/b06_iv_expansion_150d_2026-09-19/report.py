"""Write the expansion findings from verified tables; do not recalculate or tune rules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from collect import OUT, digest

LABELS = {
    "baseline": "Plain B06",
    "original": "Original IV validity",
    "midpoint": "Allow recovery when bid IV fails",
    "guarded_100": "Recovery + guards, 100% spread ceiling",
    "guarded_50": "Recovery + guards, 50% spread ceiling",
}


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    return "\n".join(["| " + " | ".join(headers) + " |",
                      "| " + " | ".join(["---"] * len(headers)) + " |"]
                     + ["| " + " | ".join(map(str, row)) + " |" for row in rows])


def percentage(value: float) -> str:
    return f"{100*value:.1f}%" if pd.notna(value) else "—"


def main() -> None:
    """Render only the already frozen, verified results."""
    verification = json.loads((OUT / "verification.json").read_text())
    for path, expected in verification["outcome_artifacts"].items():
        if digest(Path(path)) != expected:
            raise ValueError(f"Outcome artifact changed: {path}")
    results = pd.read_csv(OUT / "comparison_table.csv")
    intervals = json.loads((OUT / "paired_date_bootstrap.json").read_text())
    states = pd.read_csv(OUT / "state_summary.csv")
    features = json.loads((OUT / "feature_freeze_before_outcomes.json").read_text())
    collection = json.loads((OUT / "collection_manifest.json").read_text())
    sampling = json.loads((OUT / "sampling_manifest.json").read_text())
    days = pd.read_csv(OUT / "combined_days.csv")
    coverage = pd.read_csv(OUT / "surface_coverage.csv")

    def comparison(cohort: str) -> str:
        rows = []
        for row in results[results.cohort.eq(cohort)].itertuples(index=False):
            interval = intervals.get(cohort+"__"+row.variant, {}).get("interval_pp")
            uncertainty = "—" if interval is None else f"{interval[0]:+.1f} to {interval[1]:+.1f}"
            rows.append([LABELS[row.variant], row.signals, row.target_first,
                         percentage(row.hit_rate), f"{row.uplift_pp:+.1f}",
                         row.active_days, uncertainty])
        return markdown_table(
            ["Rule", "Signals", "+5 first", "Hit rate", "Uplift vs B06, pp",
             "Active days", "95% uplift interval, pp"], rows)

    old = results[results.cohort.eq("original_50")].set_index("variant")
    new = results[results.cohort.eq("additional_100")].set_index("variant")
    full = results[results.cohort.eq("combined_150")].set_index("variant")
    year2025 = results[results.cohort.eq("year_2025")].set_index("variant")
    new2026_rows = []
    for variant in LABELS:
        count = int(new.loc[variant, "signals"] - year2025.loc[variant, "signals"])
        targets = int(new.loc[variant, "target_first"] - year2025.loc[variant, "target_first"])
        new2026_rows.append([LABELS[variant], count, targets, percentage(targets/count)])
    broad = [
        [LABELS[v], f"{new.loc[v, 'uplift_pp']:+.2f}",
         f"{full.loc[v, 'uplift_pp']:+.2f}",
         f"{old.loc[v, 'hit_rate']*100:.1f}% → {new.loc[v, 'hit_rate']*100:.1f}%"]
        for v in LABELS if v != "baseline"]
    state_rows = []
    for cohort in ["original_50", "additional_100", "combined_150"]:
        for variant in list(LABELS)[1:]:
            subset = states[states.cohort.eq(cohort) & states.variant.eq(variant)
                            & states.condition.eq("accelerating")].set_index("state")
            state_rows.append([cohort, LABELS[variant],
                               *[int(subset.loc[state, "signals"])
                                 for state in ["yes", "no", "unknown"]]])
    outcome_rows = [
        [r.cohort, LABELS[r.variant], r.signals, r.target_first,
         r.adverse_first, r.neither, r.ambiguous]
        for r in results[results.cohort.isin(
            ["original_50", "additional_100", "combined_150"])].itertuples(index=False)]
    cov = coverage.groupby(["cohort", "variant"]).agg(
        valid_minutes=("valid_minutes", "sum"), recovered_minutes=("recovered_minutes", "sum"),
        lost_minutes=("lost_original_minutes", "sum")).reset_index()
    cov_rows = [[r.cohort, LABELS[r.variant], r.valid_minutes,
                 r.recovered_minutes, r.lost_minutes] for r in cov.itertuples(index=False)]
    pair_errors = [r for r in collection["pairs"] if r["status"] != "ok"]
    listed_missing = [r for r in collection["selections"] if not r["expirations"]]
    document = f"""# B06 / sector IV: fixed-rule expansion from fifty to 150 dates

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

{comparison("combined_150")}

These are {verification["total_parents"]} distinct B06 parent signals on
{int(full.loc["baseline", "active_days"])} active dates out of 150 sampled dates.
The IV rows are overlapping selections of this identical baseline, not independent experiments.

## Additional 100 days: the extension check

{comparison("additional_100")}

This cohort contains {verification["additional_parents"]} signals on the newly sampled dates.
It is the cleaner check of whether the original result carries to additional data. The
combined table blends previously examined dates and extension dates. Do not present pooled
accuracy alone as proof of replication.

## Original fifty days: unchanged reference

{comparison("original_50")}

All original counts, targets, adverse outcomes, neither outcomes, active dates, and individual
outcome labels reproduce. Old-versus-new sample comparisons have different date composition;
the additional dates were not chosen based on results.

## How the apparent advantage changed

{markdown_table(["Rule", "New-100 uplift, pp", "Combined uplift, pp",
                 "Original hit rate → new hit rate"], broad)}

Each uplift compares the IV row with plain B06 on the same cohort. The table shows the result
for every frozen candidate without retuning the six-sector threshold, derivative, window,
spread ceiling, missing-data treatment, or score. A higher row percentage does not by itself
prove a better future policy. Intervals and opportunity counts remain part of the comparison.

## Calendar-year descriptions

### All included 2025 dates

{comparison("year_2025")}

### All included 2026 dates

{comparison("year_2026")}

The combined sample contains {(days.date.str.startswith("2025")).sum()} dates from 2025 and
{(days.date.str.startswith("2026")).sum()} from 2026. These are descriptive strata; no policy
was selected or changed by year. The new 100 contain 66 dates from 2025 and 34 from 2026.
The original fifty are all in 2026.

### The 34 additional dates from 2026, excluding the original fifty

{markdown_table(["Rule", "Signals", "+5 first", "Hit rate"], new2026_rows)}

This is a descriptive subtraction of the already reported disjoint counts
(additional 100 minus included 2025), with no new selection rule or optimized threshold.
Every IV row trails the 62.9% B06 baseline here too. The small filtered counts are visible;
no new subgroup significance claim is made.

## Exact working rules

The [fixed comparison set]({OUT.parent}/b06_iv_recovery_findings_2026-09-19/ACTIVE_COMPARISON_SET.md)
and [earlier extensive findings]({OUT.parent}/b06_iv_recovery_findings_2026-09-19/FINDINGS.md)
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

{markdown_table(["Cohort", "Rule", "Yes", "Definite no", "Unknown"], state_rows)}

Each row sums to its cohort's complete B06 population. Missing sectors do not automatically
exclude an entire date: six other known qualifiers can still establish yes.

### Valid minute coverage and the cost of guards

{markdown_table(["Cohort", "Rule", "Valid sector-minutes",
                 "Recovered from original gaps", "Originally valid minutes lost"], cov_rows)}

Recoverability is not an independent certification that midpoint IV reflects a fair quote.
The quote guards can remove plausible as well as distorted observations, and complete
thirty-minute support compounds their coverage cost. This experiment compares the four
fixed measurement policies; it does not tune a new quote-quality threshold.
Capture starts at 09:30, so the previous-minute guard cannot validate 09:30. The eighteen
10:05 B06 parents in the full set include that minute in their IV window and therefore
cannot qualify under either guarded policy. This inherited timing exclusion is preserved.

## Complete outcome accounting

{markdown_table(["Cohort", "Rule", "Signals", "Target first", "Adverse first",
                 "Neither", "Ambiguous"], outcome_rows)}

Neither and ambiguous remain in each rate's denominator as non-target outcomes. Same-minute
first touches of both barriers retain the original ambiguous classification, without an
invented intraminute ordering. No post-target observation affects these tables.

## Sampling and collection

There were {sampling["population_count"]} recorded VT dates in the requested window and
{sampling["eligible_additional_count"]} eligible new dates under the inherited complete-session,
same-date pre-open corroboration, and above-VT-at-09:30-open criteria. One uniform sample of
100 was drawn without replacement using seed **{sampling["seed"]}**, excluding both the original
fifty and earlier ten exploration dates. Four eligible dates were not drawn. No sampled
day was replaced because of its signals, option coverage, or outcome.

See [SAMPLING.md]({OUT}/SAMPLING.md) for the month distribution and exclusions.
The VT archive ends September 11, 2026. The sample is not balanced across 2025–2026 regimes:
most included 2025 dates are August–December, with eight in February and none in March–July.
The original archive/provenance limitations remain; “available same-date pre-open note”
does not certify contemporaneous local capture or lack of later revision.

All 100 dated option listings were retrieved. There are {len(listed_missing)} new sector-days
without an allowed expiry bracket (twenty XLRE, two XLB). For example, February 14, 2025 has
7-DTE and 35-DTE contracts for XLB and XLRE; the fixed eight-day minimum excludes the former,
leaving no bracket around thirty. This is a rule-imposed gap, not a failed request.

Collection ended **{collection["status"]}** with **{len(collection["pairs"])} expiry pairs** and
**{len(pair_errors)} failed pairs**. Final prepared coverage is **{features["successful_panels"]}
sector-days** with **{features["missing_panels"]} missing/invalid sector-days** across 150×11.
Per-panel reasons are in missing_panels.csv; request-level details remain in collection_manifest.json.

New native one-minute responses, original parameters, SDK metadata, timestamps, hashes,
derived minute and event series, sampling records, and final comparison data are stored in
/Users/dgrissen/Dev/central_trade_data/thetadata/b06_iv_expansion_150d_2026-09-19-v1/.
Original caches remain read-only. The collection uses the ThetaData Python SDK 1.0.9, both
rights, strike_range30, 09:30–14:29 ET, SOFR, latest version, and at most two concurrent calls.
The initial collection encountered SDK authentication errors. The interrupted manifest and
request log are retained; a transport-only resume adapter renews the session every five
minutes, retains the two-attempt ceiling, and reads successful cached responses without
refetching. See [TRANSPORT_RECOVERY.md]({OUT}/TRANSPORT_RECOVERY.md).

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
- All {features["original_panels_reproduced"]} original surface panels reproduced from raw data.
- Original availability, acceleration values, and all policy classification counts checked
  before joining outcomes; the full original five-row result then reproduced exactly.
- Ten frozen guard boundary checks, sampling freeze/no-reroll checks, missing-sample checks,
  and first-touch/ambiguous/later-reversal scoring tests pass.
- {features["causal_prefix_checks"]} real-data prefix checks remove future observations and
  verify earlier midpoint/guard values stay unchanged.
- Features and basket membership were saved and hashed before the new outcome join.
- The final comparison encountered a numeric column stored as pandas object dtype after
  concatenating zero-row panels. A recorded adapter converts already-numeric validation
  containers to float64; it rejects nonnumeric values and preserves the exact original
  tolerance. No data value, classification or frozen calculation source was changed.
- {verification["source_hashes_unchanged"]} raw input hashes were verified unchanged.
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
"""
    (OUT / "FINDINGS.md").write_text(document)
    print(json.dumps({"findings": str(OUT / "FINDINGS.md"), "words": len(document.split()),
                      "source_results_verified": True}))


if __name__ == "__main__":
    main()

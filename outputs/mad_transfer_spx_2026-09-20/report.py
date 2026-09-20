"""Render the fixed research tables, limits and reproducibility notes."""
from __future__ import annotations

import json

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from prepare import DATA, HALVES, MODES, OUT, digest, save_json  # noqa: E402

LABEL = {"baseline": "Plain parent", "S4": "S4: acceleration", "F4": "F4: acceleration + falling",
         "sign4": "Sign only", "sign_falling4": "Sign + falling", "SPX_F": "SPX falling MAD",
         "OR_F4_SPX": "Sector F4 OR SPX"}


def md(headers: list[str], rows: list[list]) -> str:
    return "\n".join(["| " + " | ".join(headers) + " |",
                      "| " + " | ".join(["---"]*len(headers)) + " |"]
                     + ["| " + " | ".join(str(v) for v in row) + " |" for row in rows])


def nrate(row: pd.Series) -> str:
    return f"{int(row.targets)}/{int(row.n)} = {row.rate:.1f}%" if row.n else "0/0 · unestimable"


def ci(low: float, high: float) -> str:
    return f"{low:+.1f} to {high:+.1f}" if np.isfinite([low, high]).all() else "unestimable"


def get(table: pd.DataFrame, variant: str, rule: str, mode: str = "all",
        period: str = "pooled", cohort: str = "full", state: str | None = None) -> pd.Series:
    state = state or ("all" if rule == "baseline" else "yes")
    scope = table[table.variant.eq(variant) & table.rule.eq(rule) & table["mode"].eq(mode)
                  & table.period.eq(period) & table.cohort.eq(cohort) & table.state.eq(state)]
    if len(scope) != 1:
        raise ValueError(f"Ambiguous report row: {variant}/{rule}/{mode}/{period}/{cohort}/{state}")
    return scope.iloc[0]


def main() -> None:
    table = pd.read_csv(DATA / "summary.csv")
    uncertainty = pd.read_csv(DATA / "uncertainty.csv")
    within = pd.read_csv(DATA / "within_date_block.csv")
    overlap = pd.read_csv(DATA / "b09_overlap.csv")
    cross = pd.read_csv(DATA / "spx_cross.csv")
    gaps = pd.read_csv(DATA / "gap_causes.csv")
    events = pd.read_parquet(DATA / "event_keys.parquet")
    verification = json.loads((DATA / "verification.json").read_text())
    core = [(v, r) for v in ["b09", "b07", "b05"] for r in ["baseline", "S4", "F4"]]
    core += [("b09", "SPX_F"), ("b09", "OR_F4_SPX")]
    head_rows, half_rows, policy_rows, outcome_rows, control_rows, ci_rows = [], [], [], [], [], []
    for variant, rule in core:
        row = get(table, variant, rule)
        head_rows.append([variant.upper(), LABEL[rule], nrate(row), int(row.days)])
        half_rows.append([variant.upper(), LABEL[rule]] +
                         [nrate(get(table, variant, rule, period=half)) for half in HALVES])
        policy_rows.append([variant.upper(), LABEL[rule]] +
                           [nrate(get(table, variant, rule, mode=mode)) for mode in MODES])
        outcome_rows.append([variant.upper(), LABEL[rule], int(row.n), int(row.targets),
                             int(row.adverse_first), int(row.neither), int(row.ambiguous)])
        if rule != "baseline":
            u = uncertainty[uncertainty.variant.eq(variant) & uncertainty.rule.eq(rule)
                            & uncertainty.cohort.eq("full") & uncertainty["mode"].eq("all")
                            & uncertainty.reference.eq("parent")].iloc[0]
            ci_rows.append([variant.upper(), LABEL[rule], f"{u.delta_pp:+.2f}",
                            ci(u.delta_low, u.delta_high), f"{u.low:.1f}–{u.high:.1f}%"])
    for variant in ["b09", "b07", "b05"]:
        control_rows.append([variant.upper()] + [nrate(get(table, variant, rule))
                                                for rule in ["baseline", "sign4", "sign_falling4", "S4", "F4"]])
    matched_rows = []
    for variant, rule in core:
        if rule == "baseline":
            continue
        r = within[within.variant.eq(variant) & within.rule.eq(rule)
                   & within.cohort.eq("full") & within.period.eq("pooled")].iloc[0]
        s = get(table, variant, rule)
        matched_rows.append([variant.upper(), LABEL[rule], f"{s.same_dates_delta_pp:+.2f}",
            f"{r.equal_date_delta_pp:+.2f}", ci(r.low, r.high),
            f"{int(r.yes_n)}/{int(r.no_n)}", int(r.dates),
            f"{int(r.matched_strata)}/{int(r.strata)}"])
    overlap_rows = []
    for variant in ["b07", "b05"]:
        for rule in ["S4", "F4"]:
            group = overlap[overlap.variant.eq(variant) & overlap.rule.eq(rule)
                            & overlap.cohort.eq("full") & overlap.period.eq("pooled")
                            & overlap["mode"].eq("all")]
            values = []
            for split, state in [("with_b09_block", "yes"), ("without_b09_block", "yes"),
                                 ("without_b09_block", "all"), ("exact_b09_minute", "yes")]:
                values.append(nrate(group[group.split.eq(split) & group.state.eq(state)].iloc[0]))
            overlap_rows.append([variant.upper(), rule] + values)
    coverage_rows = []
    for variant in ["b09", "b07", "b05"]:
        for half in HALVES:
            part = events[events.variant.eq(variant) & events.half.eq(half)]
            coverage_rows.append([variant.upper(), half, len(part), int(part.all11.sum()),
                                  f"{100*part.all11.mean():.1f}%", f"{part.valid_sectors.mean():.2f}"])
    all11_rows = [[v.upper(), LABEL[r], nrate(get(table, v, r, cohort="all11")),
                   nrate(get(table, v, "baseline", cohort="all11"))]
                  for v, r in core if r != "baseline"]
    cross_rows = []
    for row in cross[cross.cohort.eq("full") & cross.period.eq("pooled")
                     & cross["mode"].eq("all")].itertuples():
        cross_rows.append([row.sector_state, row.spx_state, nrate(pd.Series(row._asdict())), row.days])
    gap_rows = [[symbol, cause, int(count)] for (symbol, cause), count in
                gaps.groupby(["symbol", "gap_cause"]).entries.sum().items()]

    text = f"""# Reviewed MAD transfers and SPX comparison — findings

Completed September 20, 2026. **January 2025–September 18, 2026; above-VT entries only.**
Target: **+5 before −10 within 60 native minute bars**, including entry. A later
reversal after +5 does not affect the result. Partial 2026 H2 is labeled throughout.

## CIO readout

**B09 accepting sector F4 OR SPX is the most promising opportunity expansion in
this bounded round:** 198/318 = 62.3%, compared with sector F4's 115/188 = 61.2%.
It adds 130 observed entries and 83 targets in the all-entry accounting. Active
dates increase from 95 to 121. With 60-minute spacing it gives 107/175 = 61.1%,
versus sector-only 76/121 = 62.8% and plain B09 285/554 = 51.4%. That is more
opportunities with a modest accuracy tradeoff under spacing, not an across-policy
improvement on the sector-only filter. First/day falls to 70/121 = 57.9%, versus
61/95 = 64.2% for sector F4. SPX alone is particularly sensitive to repeated
signals: 61.5% for all entries, 56.1% spaced, and 48.1% first/day.

**B05 + F4 partly worked as a transfer:** 70/112 = 62.5% versus its parent's 55.6%,
and 65/100 = 65.0% with spacing. Its same-date/hour contrast is also favorable.
However, the improvement is concentrated in blocks that also have a qualifying
B09 signal. Without one, B05 + F4 is 37/70 = 52.9%, versus 53.4% for B05 in those
blocks. This supports a shared favorable market context more than a demonstrated
independent source of extra opportunities. B05 does not exceed B09 F4's retained
events, dates or spaced N. No combined-parent portfolio was tested.

**B07 is underpowered/uninformative for this decision:** F4 reaches 14/21 = 66.7%,
but only 20 dates and 4, 8, 7, 2 events across the four halves. Its uplift interval
is very wide and crosses zero. Without a corresponding B09 qualifying block,
it is 6/12 = 50.0%. S4 is only 19/32 = 59.4%. These samples cannot establish a
reliable transfer or rule out a real effect.

**The broad sign controls show little pooled all-entry benefit:** their changes
range from −2.3 to +0.2 percentage points. This says the
specific stricter rules look different from broad direction filters on these
dates. It does not isolate the value of MAD normalization from selectivity,
date/hour selection, or the previous research search.

## Fixed rule definitions and studied population

S4 requires at least four of the fixed eleven sectors with M>1. F4 requires at
least four sectors each with M>1 **and** b2<−1e−12. b2 is the IV slope in the latest
15-minute half. M=−a/(1.4826×historical MAD), a=(b2−b1)/15. IV may still be rising
under S4 if that rise is slowing sharply. F4 adds that it is already falling.
SPX uses exactly M>1 and b2<−1e−12 on native SPXW 30-day ATM IV. OR means accept
the B09 entry if either sector F4 or SPX qualifies; neither threshold was tuned.

The original price triggers, measurement/recovery guards, and 60-prior-session
scales are unchanged. Every entry uses T−1; every source lies in T−30…T−1.
History is strictly prior. Calibration/diagnostic hour blocks are anchored at
09:30 (09:30–10:29, etc.), not whole clock hours. Prior native RTH lows and entry
open must be strictly above same-day VT. No future all-day condition was used.

There are 239 research dates, including zero-entry dates, and 5,093 distinct
parent entries: B09 3,141, B07 415, B05 1,537. The 10 development dates are excluded.
The SPX measurement backfill includes 2024; the sector-matched outcome experiment
does not. Earlier results from a full 2024–2026 population are not its baselines.

{md(['Parent', 'Rule', 'Target first / N', 'Active dates'], head_rows)}

## Every half-year

{md(['Parent', 'Rule', '2025 H1', '2025 H2', '2026 H1', '2026 H2 partial'], half_rows)}

Both B05 magnitude rules have positive observed uplift in the three completed
halves. Neither B07 rule does. Those are descriptive patterns, not pass/fail
validation tests. B09 OR has a positive observed comparison in every half, but
partial H2 has only 18 qualifying entries. The *incremental* SPX-positive,
sector-negative subgroup does not improve in every completed half; see below.

## Repeated signals and the opportunity tradeoff

{md(['Parent', 'Rule', 'All entries', 'First qualifying/day', '60-minute spacing'], policy_rows)}

Filter before thinning; each parent/rule/cohort has its own chronological policy.
Spacing resets daily and never depends on outcomes. A union can change which
entry is first or which later entries survive spacing. Therefore the 130 raw
additions cannot be added to the spaced/first-day counts as if nothing else changes.
Different parents and execution-policy cohorts must not be summed as independent
trades. The all-entry OR retains 198/1704 = 11.6% of plain B09 targets and excludes
1,506; it expands the selective IV subset, not the unfiltered parent.

## SPX disagreement: what actually supplied the extra entries

SPX scores were available for **all 3,141 B09 entries**, even though three dates
have gaps somewhere in the full SPX measurement history. Before outcomes were
joined, SPX qualified on 187 (6.0%) and OR on 318 (10.1%). That participation was
measured, not inferred from a normal distribution or selected to match sector N.

{md(['Sector F4', 'SPX', 'Target first / N', 'Dates'], cross_rows)}

The useful-looking subgroup is **SPX yes / sector definite no: 72/109 = 66.1%**,
versus 1406/2661 = 52.8% when both definitely fail. Its all-entry date-bootstrap
difference is +13.2 percentage points, with an unadjusted interval of +1.6 to
+24.2. With spacing it is 45/73 = 61.6% and the difference interval crosses zero;
first/day it is 34/59 = 57.6%, slightly below the corresponding negative group.

By half the incremental group is 19/31 = 61.3%, 37/54 = 68.5%, 8/14 = 57.1%, and
8/10 = 80.0%. In 2026 H1 it is below the jointly measurable sector-negative
benchmark of 415/707 = 58.7%. Its strongest evidence comes from 2025 H2; the small
2026 groups cannot establish stable incremental value.

The additional **sector-unknown / SPX-yes** entries are 11/21 = 52.4%. Report them
as coverage recovery, separately from the 109 definite disagreements. OR leaves
162 unresolved sector-unknown/SPX-no entries, with 100 targets (61.7%); unresolved
does not mean these were failures. No unknown vote was imputed.

On the common measurable parent, there are 2,958 entries at 53.9%. F4 retains
115/188 = 61.2%; SPX 104/166 = 62.7%; OR 187/297 = 63.0%. This removes the
sector-unknown additions from the accuracy comparison. All nine state combinations
and common/full/all-eleven comparisons are in the data tables.

Requiring **both** confirmations would leave 32/57 = 56.1%, compared with 83/131 =
63.4% for sector yes / SPX no. Agreement is not the winner in these data. This is
the predeclared cross-table diagnosis, not a new fitted AND strategy.

## Date/hour selection and overlap

The same-selected-date comparison restricts the parent to dates on which the
rule qualifies. The within-date/block comparison uses only strata containing
both qualifiers and definite nonqualifiers, then weights blocks equally within
date and dates equally. These are distinct descriptive comparisons; neither is
a causal treatment effect.

{md(['Parent', 'Rule', 'Same-date parent delta pp', 'Within-block delta pp', '95% interval pp', 'Matched yes/no events', 'Dates', 'Kept/all strata'], matched_rows)}

B09 OR's +8.0-point full-parent contrast becomes +4.7 versus the parent on its
selected dates, then +2.9 within matched date/hour blocks, with the latter interval
crossing zero. SPX alone has only +0.5 within those blocks. Thus the full-sample
advantage cannot yet be separated convincingly from selecting favorable times.
B05 F4 has the stronger within-block contrast (+14.0, interval +3.0 to +26.1),
but its full-parent uncertainty remains wide and the shared-B09 diagnostic matters.

{md(['Parent', 'Rule', 'With B09 block', 'Without B09 block', 'Parent without B09 block', 'Exact-minute overlap'], overlap_rows)}

These block labels look across the whole date/hour block, potentially including
a B09 signal later than the transfer entry. They are **retrospective overlap
diagnostics, not available-at-entry trading gates**. Removing an overlapping
block does not create out-of-sample data; all dates have been used before.
Shared price outcomes and IV windows limit claims that the transfers are new
independent opportunities.

## Broad sign controls

{md(['Parent', 'Plain', 'a<0 in four', 'a<0 + falling in four', 'S4', 'F4'], control_rows)}

The B09 controls reproduce the reviewer-disclosed 2,544 and 1,933 qualifiers
exactly. They were already inspected before this execution. Some thinned-policy
control comparisons improve, particularly B05; all policies are published in
ALL_RESULTS.md. The broad controls are much less selective, so this is not a
matched-retention test and cannot establish a benefit caused by normalization.
No raw-magnitude threshold or retention-matching sweep was added.

## Coverage held constant and gap causes

{md(['Parent', 'Half', 'Entries', 'All 11 observed', 'All-11 share', 'Mean valid sectors'], coverage_rows)}

The all-eleven sensitivity uses the same eleven sectors and thresholds, with
the corresponding restricted parent. It changes the date/time population and
does not cure nonrandom missingness outside that population.

{md(['Parent', 'Rule', 'All-eleven result', 'Restricted parent'], all11_rows)}

The main direction of the B05 F4 and B09 OR comparisons remains favorable here,
but sample sizes fall. B07 S4 becomes 10/19 = 52.6%, essentially its restricted
parent's 52.7%; F4 has only 13 events. Per-half/block valid counts, instrument
coverage, state counts and all unknown outcomes are saved, not suppressed.

{md(['ETF', 'Recorded gap cause', 'Missing ETF-entry slots'], gap_rows)}

There are 2,742 missing ETF-entry slots across the three parents, representing
2,630 distinct ETF/date/endpoints because parents can share observations. Of
these, 1,417 are missing permitted expiry brackets and 1,325 are captured days
with a rejected current window. XLRE contributes 2,051 slots (1,220 bracket,
831 current-window). Every cause is reconciled to the unchanged collection
receipt and source-support table in gap_source_support.csv. Source rejection
is not a claim that the market had no quote; strike coverage and quote guards
are distinct from absent listed expiries. No refetch, guard relaxation, added
expiry, imputation, or selective repair was performed.

## Descriptive uncertainty and limitations

{md(['Parent', 'Rule', 'Observed uplift pp', '95% uplift interval pp', '95% hit-rate interval'], ci_rows)}

Intervals use 5,000 shared whole-date resamples across the 239 selected research
dates, seed 20260920. This new seed means Monte Carlo bounds for the unchanged
B09 references differ slightly from the original seed-20260919 report; no source
or point estimate changed. All modes and restricted-parent/sign-control
comparisons are in uncertainty.csv. Matched-block intervals resample dates with
equal-date weighting. These intervals do not adjust for earlier 105-rule/48-cell
searches, serial dependence across dates, or selection of these parent candidates.
All-eleven/overlap sensitivities are correlated checks, not independent replications.

Wide/sparse comparisons are underpowered or uninformative; zero-entry cells are
unestimable. No universal post-hoc N floor, significance score, threshold change,
or declaration of a validated/stable/deployable strategy is made. The results
support keeping B09 OR and B05 F4 as fixed exploratory candidates, with the
policy and overlap qualifications above. They do not justify another sweep.

## Complete outcome accounting

{md(['Parent', 'Rule', 'N', '+5 first', '−10 first', 'Neither', 'Ambiguous'], outcome_rows)}

Higher target rate does not imply a lower adverse-first share: for example B05
F4 has 37 adverse outcomes among 112 versus 405 among 1,537 in its parent. The
user's first+5 objective is retained; no linear-payout expectancy or posttarget
giveback score was substituted.

## Verification, artifacts and review status

Ten boundary tests and Ruff pass. Local scalar replay reproduced all
{verification['scalar_memberships']:,} memberships and {verification['summary_rows']:,}
summary rows. Direct native-price scans verified all {verification['native_entry_vt_and_outcome_checks']:,}
entries, their strictly causal VT eligibility and first-touch outcomes. All 36
inherited half/policy parent baselines, previous B09 S4/F4 memberships, reviewer
sign controls, 204 within-block rows, and 324 SPX cross rows reconcile. Source
hashes, prior-history date ledgers, score arithmetic and source windows passed.

The external strategy review and conditional recheck were supplied and their
accepted requirements implemented. The new execution has **local verification,
not a new independent Claude code/results sign-off**. The final author amendments
after the recheck remain identified in the supplied review response.

- [Frozen execution protocol]({OUT}/PROTOCOL.md)
- [Every fixed rule, policy and half-year]({OUT}/ALL_RESULTS.md)
- [Entry classifications and input/code hashes]({DATA}/freeze.json)
- [Full summary, unknowns and selected-date comparisons]({DATA}/summary.csv)
- [Uncertainty]({DATA}/uncertainty.csv)
- [Within-date/hour support and estimates]({DATA}/within_date_block.csv)
- [B09 overlap groups]({DATA}/b09_overlap.csv)
- [SPX disagreement groups]({DATA}/spx_cross.csv)
- [Incremental SPX groups]({DATA}/spx_incremental.csv)
- [Per-entry gap source support]({DATA}/gap_source_support.csv)
- [Verification receipt]({DATA}/verification.json)
- [Data dictionary]({DATA}/DATA_DICTIONARY.md)

![Fixed-rule results by half-year]({DATA}/half_year_results.png)
"""
    (OUT / "FINDINGS.md").write_text(text)
    all_text = ["# All fixed comparisons by half-year and execution policy\n",
                "2026 H2 is partial. Counts are targets/N; unknown and adverse breakdowns are in summary.csv.\n",
                "Full and all11 cover all declared rules. Common cohorts restrict B09 to jointly measurable F4/SPX.\n"]
    for cohort in ["full", "all11", "common", "common_all11"]:
        for mode in MODES:
            all_text.append(f"\n## {cohort}; {mode}\n")
            scope = table[table.cohort.eq(cohort) & table["mode"].eq(mode)
                          & table.state.isin(["all", "yes"])]
            rows = []
            for (variant, rule), _ in scope.groupby(["variant", "rule"], sort=False):
                rows.append([variant.upper(), LABEL[rule]] + [nrate(get(
                    table, variant, rule, mode, period, cohort)) for period in HALVES + ["pooled"]])
            all_text.append(md(["Parent", "Rule"] + HALVES + ["Pooled"], rows))
    (OUT / "ALL_RESULTS.md").write_text("\n".join(all_text) + "\n")
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    colors = {"baseline": "#747b85", "S4": "#977536", "F4": "#167a68",
              "SPX_F": "#8b5cad", "OR_F4_SPX": "#165bbb"}
    for ax, variant in zip(axes, ["b09", "b05", "b07"], strict=True):
        rules = ["baseline", "S4", "F4"] + (["SPX_F", "OR_F4_SPX"] if variant == "b09" else [])
        for rule in rules:
            values = [get(table, variant, rule, period=h) for h in HALVES]
            ax.plot(range(4), [x.rate for x in values], marker="o", color=colors[rule],
                    label=LABEL[rule], linestyle="--" if rule == "baseline" else "-")
        ax.set_title(variant.upper())
        ax.set_xticks(range(4), ["2025 H1", "2025 H2", "2026 H1", "2026 H2*"], rotation=20)
        ax.set_ylim(35, 95)
        ax.grid(axis="y", alpha=.2)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="upper right" if variant == "b07" else "upper left", fontsize=8)
    axes[0].set_ylabel("+5 before −10 hit rate (%)")
    fig.suptitle("Fixed MAD rules · all entries · above VT · reused research dates", fontsize=15)
    fig.text(.5, .01, "*Partial through September 18. B07 F4 half-year N: 4, 8, 7, 2. Exact N for every curve is in the findings table.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=[0, .05, 1, .94])
    fig.savefig(DATA / "half_year_results.png", dpi=160)
    plt.close(fig)
    save_json(DATA / "report_receipt.json", dict(
        findings_sha256=digest(OUT / "FINDINGS.md"),
        all_results_sha256=digest(OUT / "ALL_RESULTS.md"),
        code_sha256=digest(OUT / "report.py"),
        chart_sha256=digest(DATA / "half_year_results.png")))
    print(f"Wrote {OUT / 'FINDINGS.md'}", flush=True)


if __name__ == "__main__":
    main()

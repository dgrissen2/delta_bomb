"""Render the fixed volume comparisons and their research limitations."""

import numpy as np
import pandas as pd

from run import DATA, OUT

LABELS = {
    "B09_F4_OR_SPX": "B09 + F4 OR SPX",
    "B05_F4": "B05 + F4",
    "B09_persistence": "B09 five-minute persistence",
    "B07_original_six": "B07 original six-sector acceleration",
    "combined": "All combined, deduplicated",
}


def rate(row: pd.Series) -> str:
    if not row.n:
        return "No coverage"
    return f"{int(row.target_first)}/{int(row.n)} = {row.rate:.1f}%"


def ci(low: float, high: float) -> str:
    return (
        f"{low:.1f} to {high:.1f}"
        if np.isfinite(low) and np.isfinite(high)
        else "Unavailable"
    )


def table(rows: list[dict]) -> str:
    """Render the small fixed tables without an extra runtime dependency."""
    columns = list(rows[0])
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    lines.extend(
        "| " + " | ".join(str(row[column]) for column in columns) + " |" for row in rows
    )
    return "\n".join(lines)


def main() -> None:
    summary = pd.read_csv(DATA / "summary.csv")
    pooled = summary[summary.period.eq("pooled")].set_index(["cohort", "state"])
    comparison, retention, outcome, halves, coverage, controls = [], [], [], [], [], []
    for key, label in LABELS.items():
        h, o, seen, unknown = [
            pooled.loc[(key, s)] for s in ["high", "ordinary", "observed", "unknown"]
        ]
        comparison.append(
            {
                "Cohort": label,
                "Observed, unfiltered": rate(seen),
                "High volume": rate(h),
                "Ordinary volume": rate(o),
                "High − ordinary (pp)": f"{h.delta_vs_reference_pp:+.2f}",
                "95% CI of difference (pp)": ci(h.delta_low, h.delta_high),
                "Unknown N": int(unknown.n),
            }
        )
        retention.append(
            {
                "Cohort": label,
                "Observed N retained": f"{int(h.n)}/{int(seen.n)} ({100 * h.n / seen.n:.1f}%)",
                "Observed winners retained": f"{int(h.target_first)}/{int(seen.target_first)} ({100 * h.target_first / seen.target_first:.1f}%)",
                "Winners excluded by gate": int(o.target_first),
                "Accuracy change vs all observed (pp)": f"{h.delta_vs_observed_pp:+.2f}",
                "95% CI (pp)": ci(h.delta_vs_observed_low, h.delta_vs_observed_high),
            }
        )
        for state, row in [("High", h), ("Ordinary", o)]:
            outcome.append(
                {
                    "Cohort": label,
                    "Volume": state,
                    "Win rate": f"{row.rate:.1f}%",
                    "95% win-rate CI": ci(row.low, row.high),
                    "Stopped first": f"{int(row.adverse_first)}/{int(row.n)} ({100 * row.adverse_first / row.n:.1f}%)",
                    "Neither": f"{int(row.neither)}/{int(row.n)} ({100 * row.neither / row.n:.1f}%)",
                }
            )
        for half in ["2025_H1", "2025_H2", "2026_H1", "2026_H2"]:
            period_rows = summary[
                summary.cohort.eq(key) & summary.period.eq(half)
            ].set_index("state")
            h, o = period_rows.loc["high"], period_rows.loc["ordinary"]
            halves.append(
                {
                    "Cohort": label,
                    "Half-year": half,
                    "High volume": rate(h),
                    "Ordinary volume": rate(o),
                    "High − ordinary (pp)": f"{h.delta_vs_reference_pp:+.2f}"
                    if h.n and o.n
                    else "Not measured",
                    "Unknown N": int(period_rows.loc["unknown", "n"]),
                }
            )
    cov = pd.read_csv(DATA / "coverage.csv")
    for half in ["2025_H1", "2025_H2", "2026_H1", "2026_H2", "pooled"]:
        rows = cov[cov.cohort.eq("combined") & cov.period.eq(half)].set_index("status")

        def count(status):
            return int(rows.loc[status, "n"]) if status in rows.index else 0

        coverage.append(
            {
                "Period": half,
                "Usable": count("ok"),
                "Current date unavailable": count("current_unavailable"),
                "Incomplete 60-session history": count("incomplete_history"),
            }
        )
    for row in pd.read_csv(DATA / "within_block.csv").itertuples():
        controls.append(
            {
                "Cohort": LABELS[row.cohort],
                "Comparable dates / blocks": f"{row.dates} / {row.kept_strata}",
                "High / ordinary entries": f"{row.yes_n} / {row.no_n}",
                "Equal-date difference (pp)": f"{row.delta:+.2f}",
                "95% date-bootstrap CI (pp)": ci(row.low, row.high),
            }
        )
    loo = (
        pd.read_csv(DATA / "leave_one_date_out.csv")
        .groupby("cohort")
        .delta_pp.agg(["min", "max"])
    )
    influence = [
        {
            "Cohort": LABELS[key],
            "High − ordinary after dropping one date (pp)": ci(
                loo.loc[key, "min"], loo.loc[key, "max"]
            ),
        }
        for key in LABELS
    ]
    text = """# Cached SPY relative volume across the five current Branch B cohorts

September 20, 2026. The earlier findings and current-set memory were committed
and pushed first (project consolidation e5259b4). This is the subsequent bounded
volume experiment using existing data only.

## Decision in plain terms

**This particular volume rule has not earned a filter.** The combined signals
already hit +5 first on 371/592 measurable entries (62.7%). Keeping only high
volume leaves 173/274 (63.1%): about half a percentage point more accuracy while
discarding 198 observed winners. Comparing high with ordinary volume directly
gives only +0.87 percentage points, with a 95% interval from −8.08 to +9.52 points.
That is not persuasive evidence of useful additional information.

B09 persistence offers the strongest small positive pooled hint: 63.0% versus
61.4%, but its difference interval is −9.03 to +12.47 points. The other three
individual cohorts have lower pooled accuracy with high volume. None establishes
a reliable benefit. The five overlapping cohorts are not five independent trials.
The current working set stays unchanged; no high-volume gate is adopted.

This is a result about one existing measure of trading activity. It does not
reject signed buying pressure, consolidated volume, or every possible volume
hypothesis. Those were not tested. It also provides no strong reason by itself
to buy or collect more data for this exact threshold.

## Exactly what was measured

At entry minute T, use actual cached SPY share volume from T−5 through T−1,
divided by the median volume for those same five clock minutes across exactly
60 strictly preceding source-calendar sessions. For a 10:15 entry, that means
the completed 10:10–10:14 bars, compared with 10:10–10:14 on each reference date.
The entry minute's volume is never included. RVOL > 1 is high; finite RVOL <= 1
is ordinary. This is the previously fixed threshold, not a newly optimized one.

All five bars must exist and be finite/nonnegative in the current window and
every one of the 60 history windows. The reference median must be positive.
Missing volume never becomes zero, ordinary volume, or a failed trading signal.
There is no stale forward-fill. Reference sessions can precede the 2025 research
sample and need not be above VT: they estimate normal SPY activity, not outcomes.

Source is the existing Databento XNAS.ITCH SPY cache, **Nasdaq-venue volume**.
It is not consolidated SPY trading, SPX index volume, or buyer-initiated pressure.
Cache availability ends June 11, 2026. No provider calls or data downloads occurred.

The four standalone cohorts and their union retain their original definitions,
239 research dates, exact-minute deduplication and no-spacing policy. Win means
native SPX high reaches entry+5 before native low reaches entry−10 within the
60 bars T…T+59. The low need not close there. A reversal after +5 cannot undo a
win. Causal above-VT admission and the fixed entry-based adverse barrier are
unchanged. All 685 price paths and their entry/VT checks were replayed successfully.

## Main comparison on observed volume

Ordinary volume is the comparison group, not a newly proposed inverted rule.
Unknown entries remain a separate coverage group. Full-cohort accuracy and
observed-cohort accuracy can differ because their dates and entries differ.

"""
    text += table(comparison)
    text += """

## Cost in opportunities

The correct unfiltered reference here is the **observed subset of each cohort**,
not its entire historical sample. For example, B05's full-sample 62.5% must not
be compared with high-volume 65.9% as though volume improved it: the same volume-
observable B05 population already achieved 67.0% without the volume gate.

""" + table(retention)
    text += """

Combined high volume retains 46.3% of measurable entries and 46.6% of measurable
winners. The rejected ordinary-volume group itself contains 198 winners at a
62.3% hit rate. This fails the intended balance of accuracy and opportunity count.
The 93 unknown entries are not included in those rejected-by-volume counts.

## Half-year behavior

""" + table(halves)
    text += """

Combined high-volume accuracy is modestly higher in each of the three measurable
halves. That is a descriptive positive hint, but its weights vary sharply: there
are 82, 168 and only 24 high-volume combined entries in those halves. B09's
individual comparisons reverse direction in 2025 H2. B05/B07 cells are thin;
4/4 or 0/1 is not a dependable accuracy estimate. There is no volume test at all
for 2026 H2. These half-years do not establish stability of a volume advantage.

## Outcome mix and uncertainty

""" + table(outcome)
    text += """

For the combined set, high volume has 75/274 stops first (27.4%), versus 69/318
(21.7%) for ordinary volume. Its slightly higher target frequency accompanies
fewer timeouts and more stops, not an obvious reduction in failed entries. This
does not change the objective: reaching +5 first remains the win definition.

Intervals use 5,000 paired whole-date bootstrap resamples, seed 20260920, within
each original half-year/pooled research calendar, including zero-entry dates.
All events on a sampled day move together. Differences use the same draws for
both groups. These are percentile intervals; they address intraday clustering,
not the history of rule selection, multi-day dependence or future regime changes.
Zero-denominator draws are excluded and their counts are recorded. Rate CIs are
suppressed for fewer than two active dates or constant binary outcomes. Sparse
or constant-outcome contrast bootstraps can also be degenerate and must not be
read as evidence of precision. There is no multiplicity correction or untouched
holdout here. The five cohorts are strongly overlapping.

## Does the pooled hint survive comparing similar dates and times?

Use the prior diagnostic: retain only date/hour blocks that contain both high
and ordinary entries. Blocks are anchored at 09:30, using the final completed
minute T−1. Calculate the hit-rate difference in each block, average blocks within
a date, then give each retained date equal weight. This changes both the sample
and weighting; it is not a causal volume estimate or a full price-strength match.

""" + table(controls)
    text += """

Combined remains near zero (+0.44 pp), with a wide −12.72 to +14.47 pp interval
and only 136 entries across 38 dates. Persistence becomes −4.32 pp on its matched
blocks, also uncertain. B05's positive block number comes from only three dates
and eight entries; B07's negative number from two dates and four entries.
Those tiny subsets do not justify a conclusion in either direction.

Price context also differs. Combined high-volume entries had mean pre-entry
30-minute SPX return +7.68 basis points versus +3.16 with ordinary volume, and
mean realized 30-minute movement 10.57 versus 9.17 SPX points. The latter is
sqrt(sum of squared changes from the first open through successive minute
closes), not a directional return. Volume can accompany stronger or noisier
movement already present in prices. We have not isolated an independent mechanism.
The full cohort/half-year balance table is preserved centrally.

## Individual-day sensitivity

Remove every research date in turn, without retuning the threshold or memberships.
The following are sensitivity extrema, **not confidence intervals**:

""" + table(influence)
    text += """

Combined's tiny pooled difference can cross zero after dropping one date. The
small persistence advantage remains positive under single-date deletion, but
its broad cluster interval and negative within-date/hour diagnostic remain.
Surviving a single-date deletion is not proof of useful predictive improvement.

## Coverage and exact missing-entry ledger

""" + table(coverage)
    text += f"""

592/685 unique entries (86.4%) have usable relative volume, on 145 active dates.
The 52 missing current observations occur after the cache end: 13 in late 2026 H1
and all 39 entries in partial 2026 H2. Another 41 earlier entries fail the exact
60-session history requirement. All 93 unknown rows retain date, entry minute,
original cohort flags and specific status in [unknown_entries.csv]({DATA}/unknown_entries.csv).
Cohort-specific unknown counts overlap; do not add them as independent cases.

Unknown combined entries hit 56/93 (60.2%). That describes unavailable coverage;
it is not an estimate of their high/ordinary volume behavior. We neither replace
their volume nor extrapolate their missing measurements from outcomes.

## Reproduction and verification

- `run.py prepare` reuses the earlier causal volume builder and freezes 685
  outcome-free measurements, memberships, calendar, protocol/code and sources.
  It exactly reconciles all 501 overlapping timestamps against earlier features.
- `run.py analyze` independently checks all 685 measurements using direct raw
  five-column sums, joins hash-verified existing outcomes, and publishes 125
  summary rows, coverage, block comparisons, balances and 1,195 date deletions.
- `verify.py` independently replays all 685 native SPX entry paths (41,100 bar
  observations across 163 dates), confirms above-VT admission, recounts all 125
  summary rows and all 1,195 date deletions. Baseline volume counts exactly match
  the earlier 84/136 high, 92/148 ordinary and 22/34 unknown results.
- The existing boundary test confirms RVOL uses strictly prior dates and requires
  all 60 reference windows; Ruff passes. Source hashes and output receipts are
  stored alongside the data. No independent reviewer agent was run in this side chat.

Data: [{DATA}]({DATA}). Code/protocol: [{OUT}]({OUT}). CSV/Parquet bulk artifacts
remain in the central cache under its existing ignore policy; central dictionaries
and hash receipts are committed. Findings and extensive commit notes preserve the
reviewable results in the project repository. Original inputs remain unchanged.

**Research disposition:** keep all five existing cohorts as the working set. Keep
this fixed volume observation as a documented weak result; do not adopt a volume
gate, reverse the threshold, or run a threshold sweep on these same results.
"""
    (OUT / "FINDINGS.md").write_text(text)
    appendix = "\n### 11.36 — September 20: fixed cached-volume test across the five working cohorts\n\n"
    for line in text.splitlines():
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            line = "#### " + line[3:]
        appendix += line + "\n"
    (OUT / "LEARNING_APPEND.md").write_text(appendix)
    print("Rendered findings and learning appendix", len(text.splitlines()), "lines")


if __name__ == "__main__":
    main()

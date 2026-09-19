"""Paired barrier findings, all families and half-years, with fixed denominators."""
from __future__ import annotations

import json

import pandas as pd

from rescore import DATA, OLD, OUT, PERIODS, VARIANTS

LABELS = ['B01 · Fixed time', 'B02 · Thrust', 'B03 · Thrust + staircase', 'B04 · T',
          'B05 · Stall/reclaim', 'B06 · Immediate', 'B06 · Retest', 'B07 · Failed breakdown',
          'B08 · Band rebound', 'B08 · Band + RSI', 'B09 · 1m staircase',
          'B10 · Opening-range immediate', 'B10 · Opening-range retest']


def table(headers: list[str], rows: list[list[str]]) -> str:
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(str(x).replace('|', r'\|') for x in row)+' |' for row in rows])


def main() -> None:
    if (OUT/'FINDINGS.md').exists():
        raise FileExistsError('Findings already exist')
    f = pd.read_csv(DATA/'comparison.csv')
    verification = json.loads((DATA/'score_verification.json').read_text())
    transitions = pd.read_csv(DATA/'outcome_transitions.csv')

    def row(variant: str, group: str = 'combined_non_development', sensitivity: str = 'all') -> pd.Series:
        return f[f.variant.eq(variant) & f.cohort.eq(group) & f.sensitivity.eq(sensitivity)].iloc[0]

    def cell(r: pd.Series) -> str:
        return f'{r.hit_pct:.1f}% ({r.target_first}/{r.n})' if r.n else '— (0 entries)'

    b06, thrust, b03, b10, retest = [row(v) for v in
        ['b06_breakout', 'thrust', 'staircase', 'b10_breakout', 'b10_retest']]
    report = f'''# Branch B rescore: +5 before −10 within 60 minutes

Completed 19 September 2026. The only changed scoring parameter is the adverse
barrier: −15 becomes −10 SPX points. Same native prices, dates, entry clocks,
thirteen frozen variants and strict above-VT eligibility. Success means hitting
+5 first. A later reversal after +5 has no effect on the score.

## Findings

Plain B06 moves from **{b06.hit_pct_15:.1f}% to {b06.hit_pct:.1f}%** on the same
{b06.n:,} entries: {b06.target_first_15:,} previous winners become
{b06.target_first:,} new winners. That is {b06.lost_targets} fewer counted wins,
a {abs(b06.change_pp):.1f}-percentage-point reduction. Some trades that eventually
reached +5 had first fallen ten points and now fail. Same-minute +5/−10 double
touches are unknown ordering and remain ambiguous, not assumed wins or losses.

The earlier candidates now score **thrust {cell(thrust)}**, **thrust plus
staircase {cell(b03)}**, and **opening-range immediate {cell(b10)}**.
Opening-range retest is {cell(retest)}; its small sample and weak 2024 evidence
still matter. Compare all rows and each half-year below rather than using the
pooled leader alone. Thrust and thrust-plus-staircase overlap.

Thrust and thrust-plus-staircase still exceed plain B06's observed hit rate in
all six half-years. Opening-range immediate now trails it in 2024 H2: 47.2%
versus 50.1%. The strongest accuracy candidate remains thrust, while the pooled
ordering between the two larger-sample candidates flips: thrust-plus-staircase
56.8% versus opening-range immediate 55.8%. These rankings remain exploratory.

For B06 specifically, all 33 lost wins become definite −10-first outcomes, not
ambiguous ones. Another 209 previous neither outcomes and the one previous
ambiguous outcome become adverse-first. Thus the new distribution is 1,208
targets, 485 adverse-first and 689 neither, with no ambiguous outcomes. The
modest hit-rate reduction does not mean the number of stop outcomes barely changes.

A tighter barrier cannot increase hit rate on these fixed entries. It may limit
the adverse excursion allowed before failure, but this test does not calculate
option returns or prove that the new tradeoff is economically better. Neither
outcomes also can become adverse-first, so a decrease in winners is not the full
change in outcome distribution. The transition table records both effects.

## Pooled research: identical entries, old versus new score

Primary population: **411 research dates**, with the original ten development
dates excluded. All entries require every prior RTH minute low and entry open
strictly above the same-date Vol Trigger. No future all-day-above condition.
Counts include neither and ambiguous outcomes; N is unchanged in every row.

'''
    report += table(['Variant', 'N', '+5 / −15', '+5 / −10', 'Change (pp)', 'Lost wins',
                     '95% new-rate interval', '95% paired-change interval'],
                    [[label, str(row(v).n), f'{row(v).hit_pct_15:.1f}% ({row(v).target_first_15})',
                      f'{row(v).hit_pct:.1f}% ({row(v).target_first})', f'{row(v).change_pp:.1f}',
                      str(row(v).lost_targets),
                      f'{row(v).date_ci_low_pct:.1f}–{row(v).date_ci_high_pct:.1f}%',
                      f'{row(v).paired_change_ci_low_pp:.1f}–{row(v).paired_change_ci_high_pp:.1f} pp']
                     for v, label in zip(VARIANTS, LABELS, strict=True)])
    report += '''

## New −10 score by half-year

Cells show **hit rate (wins / entries)**. The qualifying research-date counts
remain 87 / 85 / 62 / 92 / 67 / 18. 2026 H2 is partial through September 18;
its tiny high-percentage cells do not establish dependable near-perfect accuracy.

'''
    report += table(['Variant']+[p.replace('_', ' ') for p in PERIODS],
                    [[label]+[cell(row(v, p)) for p in PERIODS]
                     for v, label in zip(VARIANTS, LABELS, strict=True)])
    report += '\n\n## Change in hit rate by half-year\n\nNew minus old, percentage points.\n\n'
    report += table(['Variant']+[p.replace('_', ' ') for p in PERIODS],
                    [[label]+[f'{row(v, p).change_pp:.1f}' if row(v, p).n else '—' for p in PERIODS]
                     for v, label in zip(VARIANTS, LABELS, strict=True)])
    report += '\n\n## Dependence sensitivities: −10 score\n\n'
    report += table(['Variant', 'All entries', 'First per day', '60-minute spacing'],
                    [[label]+[cell(row(v, sensitivity=s)) for s in ['all', 'first_per_day', 'spaced60']]
                     for v, label in zip(VARIANTS, LABELS, strict=True)])
    report += '''

Spacing uses entry times only, not previous outcomes or an assumed position-exit
rule. These are the existing sensitivities, not newly selected cooldowns. Because
each family triggers at different times, differences between families are
descriptive; the −10 versus −15 comparison within a family uses identical entries.

## Full outcome changes, pooled research

Counts before → after. A previous target becoming ambiguous is kept separate
from a definite −10-first loss. Non-targets can never turn into new targets.

'''
    def transition(v: str, before: str, after: str) -> int:
        selected = transitions[transitions.cohort.eq('combined_non_development') &
            transitions.variant.eq(v) & transitions.outcome_15.eq(before) & transitions.outcome_10.eq(after)]
        return int(selected.n.sum())

    report += table(['Variant', 'Target old → new', 'Adverse old → new', 'Neither old → new',
                     'Ambiguous old → new', 'Old win → adverse', 'Old win → ambiguous'],
                    [[label]+[f'{row(v)[k+"_15"]} → {row(v)[k]}' for k in
                               ['target_first', 'adverse_first', 'neither', 'ambiguous']]+
                     [str(transition(v, 'target_first', 'adverse_first')),
                      str(transition(v, 'target_first', 'ambiguous'))]
                     for v, label in zip(VARIANTS, LABELS, strict=True)])
    report += f'''

## Verification, conventions and storage

All **{verification['raw_rows']:,} raw identities** and **{verification['distinct_entries']:,}
unique variant/date/minute opportunities** are unchanged. Both barriers were
independently checked in {verification['unique_native_windows']:,} distinct native
date/minute windows using a separate sequential scan. All previous −15 outcomes,
first-touch minutes, entry prices and endpoint changes reproduce exactly. Every
strict-VT flag was rechecked against original native prices. New targets are a
subset of previous targets. All 390 summary denominators and previous outcome
counts match the earlier study.

The sixty-bar horizon includes the entry bar and ends at minute +59. Both first
barriers touched in the same minute are ambiguous. No intraminute ordering is
invented; price comparison tolerance remains 1e-8. Neither and ambiguous remain
in the hit-rate denominator. Twelve targeted scorer tests cover ordering, same-
minute ambiguity, the horizon boundary, posttarget reversal, invalid parameters,
missing bars and invalid OHLC. Ruff passes.

Intervals use 10,000 whole-date resamples, seed 20260919, retaining zero-event
dates. The paired change interval uses the same resampled dates for both scores.
They address within-date dependence, not all serial dependence or prior research
selection. This is one user-requested barrier sensitivity, not a new holdout,
barrier optimization or strategy profitability model. Existing early-close,
native-data and VT-provenance exclusions remain unchanged.

Original immutable evidence: `{OLD}`.
New evidence: `{DATA}`.
Code and protocol: `{OUT}`.
`comparison.csv` contains all 390 rows, both outcome distributions, rates and
intervals. `outcome_transitions.csv` records every observed old/new category pair;
`daily_counts.csv` retains zero-event dates. The new event ledger preserves old
scores in `outcome_15`/`first_touch_min_15` and uses `outcome`/`first_touch_min` for
−10. No ThetaData, ORATS or other market-data calls were needed.
'''
    with (OUT/'FINDINGS.md').open('x') as file:
        file.write(report)
    print(str(OUT/'FINDINGS.md'))


if __name__ == '__main__':
    main()

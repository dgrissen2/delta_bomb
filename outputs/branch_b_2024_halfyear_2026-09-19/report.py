"""Report every frozen recipe by half-year, including uncertainty and exclusions."""
from __future__ import annotations

import json

import pandas as pd

from pipeline import DATA, OLD_DATA, OUT, analysis, replay, write_json
from periods import PERIODS, cohort, half_year


def table(headers: list[str], rows: list[list[str]]) -> str:
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(str(x).replace('|', r'\|') for x in row)+' |' for row in rows])


def main() -> None:
    if (OUT/'FINDINGS.md').exists():
        raise FileExistsError('Findings already written')
    verification = json.loads((DATA/'independent_verification.json').read_text())
    coverage = json.loads((DATA/'coverage_complete.json').read_text())
    history = pd.read_csv(DATA/'history_ledger.csv')
    changes = json.loads((DATA/'history_changes.json').read_text())
    summary = pd.read_csv(DATA/'comparison.csv')
    primary = summary[summary.gate.eq('always_above') & summary.sensitivity.eq('all')]
    selected = pd.read_csv(DATA/'selected_days.csv')
    population = pd.read_csv(DATA/'population.csv')
    raw = pd.read_parquet(DATA/'event_outcomes.parquet')
    events = raw.drop_duplicates(['variant', 'date', 'known_min'])
    strict = events[events.always_above & events.cohort.ne('development_10')].copy()
    strict['half_year'] = strict.date.map(half_year)
    strict['hit'] = strict.outcome.eq('target_first')
    period_rows = []
    for period in PERIODS:
        audit = population[population.date.map(half_year).eq(period)]
        dates = cohort(selected, period)
        active = strict[strict.half_year.eq(period)].date.nunique()
        period_rows.append({'half_year': period, 'calendar_sessions': len(audit),
                            'research_dates': len(dates), 'active_dates_any_recipe': active,
                            'zero_event_research_dates': len(dates)-active,
                            'development_dates_excluded': int(audit.eligible.mul(audit.cohort.eq('development_10')).sum()),
                            'calendar_exclusions': int((~audit.eligible).sum())})
    periods = pd.DataFrame(period_rows)
    periods.to_csv(DATA/'halfyear_population.csv', index=False)
    primary[primary.cohort.isin(PERIODS)].to_csv(DATA/'halfyear_results.csv', index=False)
    context = strict[strict.variant.eq('b06_breakout')].groupby('half_year')[
        ['atr_at_entry', 'target_in_atr']].median().reset_index()
    context.to_csv(DATA/'halfyear_b06_context.csv', index=False)
    old_events = pd.read_parquet(OLD_DATA/'events_before_outcomes.parquet')
    columns = ['event_id', 'date', 'variant', 'known_min', 'entry_price', 'always_above', 'entry_above']
    pd.testing.assert_frame_equal(
        raw[raw.date.isin(old_events.date)][columns].sort_values('event_id').reset_index(drop=True),
        old_events[columns].sort_values('event_id').reset_index(drop=True), check_dtype=False)
    old_manifest = json.loads((OLD_DATA/'development_reproduction.json').read_text())
    development = raw[raw.cohort.eq('development_10') & raw.variant.ne('b01')]
    assert len(development) == old_manifest['reproduced_identities'] == 441
    write_json(DATA/'development_reproduction.json', {'original_identities': 441,
        'reproduced_identities': len(development), 'exact_prior_event_comparison': True,
        'excluded_from_all_six_primary_halfyears': True})

    def result(variant: str, group: str, sensitivity: str = 'all') -> pd.Series:
        return summary[summary.gate.eq('always_above') & summary.variant.eq(variant) &
                       summary.cohort.eq(group) & summary.sensitivity.eq(sensitivity)].iloc[0]

    def cell(row: pd.Series) -> str:
        return f'{row.hit_pct:.1f}% ({row.target_first}/{row.n})' if row.n else '— (0 entries)'

    report = '''# Branch B: 2024 added, all six half-years compared

Completed 19 September 2026. **Objective: +5 SPX points before −15 within 60 minutes.**
Nothing that happens after reaching +5 changes a win. The same thirteen frozen
entry variants are scored throughout. This is a price-trigger study; no new IV
overlay was applied.

## What seems to work

**B02 five-minute thrust has the highest pooled hit rate: 61/92, or 66.3%.** It
beats plain B06's observed percentage in each of the six periods. Its two 2024
halves were 60.0% and 63.2%, so the result is not entirely a recent-2026 effect.
But only 92 entries survive across 411 research dates. The recent 100% is five
wins from five entries, not evidence of near-perfect reliability. This remains
the accuracy-first candidate, with substantial uncertainty and limited frequency.

**B10 immediate opening-range breakout and B03 thrust plus staircase provide
more observations with lower pooled hit rates:** 153/260 (58.8%) and 184/317
(58.0%). Both also exceed plain B06 in all six half-years. B10's first five
periods range from 50.0% to 75.0%; its 88.9% recent figure is only eight wins
from nine entries. B03's first five range from 49.2% to 61.5%, with 11/13 in the
recent partial half. These are the better candidates for balancing accuracy with
opportunity count. They are not demonstrated causal improvements or validated
trading edges. B03 includes thrust entries; these candidates overlap.

**B10 retest loses its earlier appearance of dependable high accuracy.** Its
pooled figure is 38/61 (62.3%), but the new 2024 halves are 5/13 (38.5%) and
9/16 (56.2%). The 2026 H1 result of 10/11 cannot erase that failure to repeat.
B08 band rebound and its RSI add-on are also inconsistent; RSI has only 36
entries overall and none in 2026 H2. B05, B07, B09, T and B06 retest do not
show a stable, substantial improvement across periods. No filter is promoted
merely because one small cell has a high percentage.

Plain B06 is **1,241/2,382 (52.1%)** across this larger history. Its half-year
rates range from 47.2% to 71.6%. The earlier strong recent result was not a
stable all-period rate. The fixed-time B01 comparison is 844/1,569 (53.8%);
it also changes with the period. Different recipes enter at different times
and on different dates, so these percentage comparisons do not establish
incremental predictive value or option-trade profitability.

## Six half-years: every frozen variant

Cells are **hit rate (+5-first wins / all entries)**. Neither and ambiguous
outcomes remain in N. All cells below use the strict above-VT gate. 2026 H2 is
partial, through September 18, and excludes the ten original development dates.

'''
    report += table(['Entry']+[p.replace('_', ' ') for p in PERIODS]+['Pooled research'],
                    [[analysis.LABELS[v]]+[cell(result(v, p)) for p in
                      PERIODS+['combined_non_development']] for v in replay.VARIANTS])
    report += '''

## Population and the above-VT requirement

The calendar audit covers **681 completed sessions**, including all 252 in 2024.
There are 421 verifiable qualifying dates: 172 newly evaluated 2024 dates and
249 earlier dates. **411 research dates** exclude the original ten development
dates. Earlier 50/100/89 cohort memberships remain unchanged. No date was selected
because it produced a signal or a winning result.

'''
    report += table(['Half-year', 'Calendar sessions', 'Research dates', 'Active dates',
                     'Zero-event dates', 'Development excluded', 'Calendar exclusions'],
                    [[str(x) for x in row] for row in periods.itertuples(index=False, name=None)])
    report += '''

Each qualifying date requires a valid complete 390-minute native SPX session,
an opening price strictly above VT, and a positive same-date VT corroborated by
saved preopen note labels. For an actual entry, **every earlier minute low since
09:30 and the entry open must be strictly above VT**. A touch or breach before
entry disqualifies that entry and later entries on that date. There are no
below-VT entries in these primary tables. Future lows after entry never determine
eligibility, including whether the full day eventually stays above VT.

The same-date publication requirement excludes prior-evening notes. Conflicting,
missing or late note evidence is not resolved by selecting a favorable level.
Publication labels establish the saved document's stated timing, not proof that
the locally captured document was never revised. The existing full-session rule
excludes early closes. Thus this is every **verifiable qualifying date under the
frozen rules**, not a claim that all excluded dates were below VT.

## Why 2024 lowers the pooled percentages

The target is a fixed five points in every year. It was a larger move relative
to the typical five-minute bar in early 2024. This is directly visible in the
known-at-entry ATR, without changing the target or fitting a new threshold:

'''
    report += table(['Half-year', 'B06 entries', '+5 first', '−15 first', 'Neither',
                     'Ambiguous', 'Median 5m ATR', 'Median +5 / ATR'],
                    [[p.replace('_', ' '), str(result('b06_breakout', p).n),
                      str(result('b06_breakout', p).target_first),
                      str(result('b06_breakout', p).adverse_first),
                      str(result('b06_breakout', p).neither),
                      str(result('b06_breakout', p).ambiguous),
                      f'{context.set_index("half_year").loc[p, "atr_at_entry"]:.2f}',
                      f'{context.set_index("half_year").loc[p, "target_in_atr"]:.2f}'] for p in PERIODS])
    report += '''

For example, 252 of 555 B06 entries in 2024 H1 reached neither barrier in the
hour; only 41 reached −15 first. The lower hit rate largely consists of failing
to travel five points in time, not a corresponding explosion in −15-first
outcomes. This is a descriptive explanation consistent with quieter movement;
it is not a causal decomposition of every difference between periods. No new
ATR filter or scaled target was selected after viewing these results.

## Pooled uncertainty and dependence sensitivities

Intervals resample whole qualifying dates 10,000 times, seed 20260919, retaining
zero-event dates. They address within-date dependence, not every cross-date or
research-selection effect. First-per-day and fixed 60-minute spacing are the
same predeclared sensitivities, not newly optimized strategies.

This matters to the candidate ranking: first-per-day B06 is 180/311 (57.9%),
close to B03 at 113/191 (59.2%) and B10 immediate at 153/260 (58.8%). Much of
their apparent advantage over all-entry B06 shrinks when repeated B06 signals
are removed. Thrust retains 48/68 (70.6%) first-per-day and 55/81 (67.9%) with
60-minute spacing. Its pooled 95% interval is still wide, about 56.8–75.5%.
The intervals are for individual rates, not proof that differences are significant.

'''
    report += table(['Entry', 'All entries', 'Active dates', '95% date interval',
                     'First per day', '60-minute spacing'],
                    [[analysis.LABELS[v], cell(result(v, 'combined_non_development')),
                      str(result(v, 'combined_non_development').active_dates),
                      f'{result(v, "combined_non_development").date_ci_low_pct:.1f}–'
                      f'{result(v, "combined_non_development").date_ci_high_pct:.1f}%',
                      cell(result(v, 'combined_non_development', 'first_per_day')),
                      cell(result(v, 'combined_non_development', 'spaced60'))]
                     for v in replay.VARIANTS])
    report += '\n\n## Half-year uncertainty and full outcome counts\n\n'
    for period in PERIODS:
        report += f'### {period.replace("_", " ")}\n\n'
        report += table(['Entry', 'N', 'Active dates', '+5 first', '−15 first', 'Neither',
                         'Ambiguous', 'Hit rate', '95% date interval'],
                        [[r.label, str(r.n), str(r.active_dates), str(r.target_first),
                          str(r.adverse_first), str(r.neither), str(r.ambiguous),
                          f'{r.hit_pct:.1f}%' if r.n else '—',
                          f'{r.date_ci_low_pct:.1f}–{r.date_ci_high_pct:.1f}%' if r.n else '—']
                         for r in primary[primary.cohort.eq(period)].itertuples()])+'\n\n'
    excluded = population[population.date.str.startswith('2024') & ~population.eligible]
    report += '## 2024 exclusions: every date\n\n'
    report += table(['Date', 'Recorded VT', 'Observed open', 'Reason'],
                    [[r.date, str(r.vol_trigger), str(r.spot_open), r.exclusion_reasons]
                     for r in excluded.itertuples()])
    report += f'''

## Native data, reproducibility and limitations

Used the ThetaData Python SDK at one minute for 34 missing/incomplete 2024
sessions. Thirty-three responses normalized to complete native 390-minute
sessions; no minute was synthesized. The May 30 response has 77 invalid OHLC
observations and was rejected. Its old 313-minute source remains incomplete
and its observed open is below VT. It is not admitted to evaluation; only its
existing complete five-minute bins may contribute inherited warmup.
No qualifying date was added by these requests. Their main contribution was
restoring chronological indicator history, including dates below VT.

Warmup now has {len(history):,} source sessions, {int(history.included_5m.sum()):,}
five-minute inclusions and {int(history.included_1m.sum()):,} complete minute-RSI
inclusions. There are {len(changes['added'])} added source dates and
{len(changes['replaced'])} selected-source replacement: the old incomplete
December 30, 2024 file is preserved and the new complete native source is used.
All eight frozen recipe modules remain unchanged. All **12,534 prior raw
signals** reproduce exactly, including clocks, entry prices and VT gates;
common outcomes match. Earlier percentages did not change through a code rewrite.
The new pooled values change because new 2024 observations are included.

The combined replay emits {len(raw):,} raw setup records and {len(events):,}
distinct variant/date/minute opportunities. It has {len(strict):,} strict-VT
research opportunities. All {verification['native_opportunities_checked']:,}
native opportunities and VT flags were independently reread and checked, with
{verification['summary_rows_reconciled']:,} summary rows reconciled and
{verification['prior_summary_rows_compared']} prior summary rows unchanged.
All 441 development identities reproduce and stay outside primary tables.
Three real-data prefix checks confirm later bars cannot alter earlier signals.
Thirty-four targeted tests plus four subtests passed; Ruff passed.

The detailed comparison file also contains opening-only and entry-above diagnostic
gates. **Neither is the primary above-VT result.** Earlier-hour B01 matched
differences condition an earlier entry on later signal formation, so they are
selected-path timing diagnostics and must not be called causal uplift.

The 2026 H2 research result has only 18 qualifying dates, of which some produce
no qualifying recipe entry. Its exceptional small cells require particular
caution. We compared many previously explored ideas; consistency across these
historical halves is useful evidence, not an untouched forward test. Keep the
rules fixed for further evaluation rather than tuning each half-year separately.

Authoritative data: `{DATA}`.
Protocol and code: `{OUT}`.
Main tables: `halfyear_results.csv`, `halfyear_population.csv`, `comparison.csv`.
Source selection: `population.csv`, `vt_note_provenance.json`, `history_ledger.csv`.
Audit: `coverage_complete.json`, `prior_event_comparison.json`,
`prior_summary_changes.csv`, `independent_verification.json`, frozen manifests.
Provider queue stopped: {coverage['provider_stopped']}; pending requests:
{len(coverage['pending_dates'])}. Prior datasets and dashboard remain unchanged.
'''
    with (OUT/'FINDINGS.md').open('x') as file:
        file.write(report)
    print(json.dumps({'findings': str(OUT/'FINDINGS.md'), 'research_dates': len(cohort(selected, 'combined_non_development')),
                      'strict_research_opportunities': len(strict), 'new_2024_dates': int(selected.cohort.eq('new_2024').sum())}))


if __name__ == '__main__':
    main()

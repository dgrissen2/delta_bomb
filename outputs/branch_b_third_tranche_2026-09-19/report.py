"""Document all third-tranche results and the outcome-blind coverage correction."""
from __future__ import annotations

import json

import pandas as pd

from pipeline import DATA, OLD_DATA, OUT, analysis, replay, write_json


def table(headers: list[str], rows: list[list[str]]) -> str:
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(r)+' |' for r in rows])


def main() -> None:
    if (OUT/'FINDINGS.md').exists():
        raise FileExistsError('Report already exists')
    verification = json.loads((DATA/'independent_verification.json').read_text())
    summary = pd.read_csv(DATA/'comparison.csv')
    selected = pd.read_csv(DATA/'selected_days.csv')
    population = pd.read_csv(DATA/'population.csv')
    raw = pd.read_parquet(DATA/'event_outcomes.parquet')
    distinct = raw.drop_duplicates(['variant', 'date', 'known_min'])
    strict = distinct[distinct.always_above].copy()
    strict['hit'] = strict.outcome.eq('target_first')
    third_dates = selected[selected.cohort.eq('third_tranche')]
    third = strict[strict.cohort.eq('third_tranche')]
    admission = third.merge(third_dates[['date', 'publication_format_recovered']], on='date', validate='many_to_one')
    admission_rows = []
    for name, recovered in [('legacy_eligible_remaining_4', False), ('publication_recovered_85', True)]:
        for variant in replay.VARIANTS:
            f = admission[admission.variant.eq(variant) & admission.publication_format_recovered.eq(recovered)]
            admission_rows.append({'group': name, 'variant': variant, 'n': len(f), 'active_dates': f.date.nunique(),
                                   'targets': int(f.hit.sum()), 'hit_pct': f.hit.mean()*100 if len(f) else None})
    pd.DataFrame(admission_rows).to_csv(DATA/'third_admission_comparison.csv', index=False)
    third_dates.assign(month=third_dates.date.str[:7]).groupby('month').size().rename('dates').to_csv(
        DATA/'third_month_counts.csv')
    # The original ten dashboard dates remain development data, with all441 identities intact.
    payload = json.loads((OLD_DATA/'dashboard_reproduction_inputs/chart_data.json').read_text())
    expected = [(d['date'], e['variant'], int(e['known_min']), e.get('episode_id') or '')
                for d in payload['days'] for e in d['events']]
    actual = [(e.date, e.variant, int(e.known_min), '' if pd.isna(e.episode_id) else e.episode_id)
              for e in raw[raw.cohort.eq('development_10') & raw.variant.ne('b01')].itertuples()]
    assert sorted(expected) == sorted(actual)
    write_json(DATA/'development_reproduction.json', {'original_identities': len(expected),
                                                      'reproduced_identities': len(actual), 'equal': True})
    primary = summary[summary.gate.eq('always_above') & summary.sensitivity.eq('all')]
    def result(v: str, c: str, sensitivity: str = 'all') -> pd.Series:
        return summary[summary.gate.eq('always_above') & summary.variant.eq(v) &
                       summary.cohort.eq(c) & summary.sensitivity.eq(sensitivity)].iloc[0]
    def cell(r: pd.Series) -> str:
        return f'{r.target_first}/{r.n} · {r.hit_pct:.1f}%' if r.n else '0 entries'
    report = '''# Third tranche: all remaining verifiable qualifying 2025–2026 dates

Completed 19 September 2026. Same B01–B10 recipes, same13 comparison rows, same
**+5 before−15 within60 minutes** score. Posttarget reversals do not change a win.

## Result for the CIO

The third tranche contains **89 dates:88 from2025 and one from2026**. Its results
weaken the earlier favorites. B08 price re-entry fell to28/60 (46.7%), B07 reclaim
to80/154 (51.9%), B02 thrust to14/25 (56.0%), and B10 retest to7/12 (58.3%). Plain
B06 was281/540 (52.0%), close to its52.9% on the preceding100-date addition.

**B10 immediate opening-range breakout is the more consistent candidate across
the two extensions:**60.3% on the second tranche and61.4% on the third, with96/149
(64.4%) across all239 non-development dates. **B05 stall/reclaim** reached343/570
(60.2%) in tranche3, but its combined rate is57.9%. Neither comparison establishes
a causal improvement: these rules enter at different times on different dates.
The fixed-time B01 control itself reached59.1% in tranche3 and58.8% overall.

B10 retest still has the highest combined point estimate,24/32 (75.0%), but the
new7/12 result does not repeat its previous85% level. B02's combined40/58 (69.0%)
also masks a weaker new tranche. The earlier B08/B07 preference should therefore
be downgraded. No rule is promoted as validated; the evidence changed, so the
candidate assessment changes with it. The one new2026 date cannot establish
robustness in2026. This is mainly a missing-part-of-2025 extension.

## What “all qualifying days” means here

The audit covers every **429 completed NYSE session from2025-01-01 through
2026-09-18**. It identifies249 verifiable qualifying dates:50 original,100 second
tranche,89 third tranche and10 original dashboard-development dates. The primary
research total is **239 dates**; the ten development dates are scored separately
and included only in the explicitly labeled249-date descriptive total.

All qualifying dates have complete native390-minute SPX observations, positive
same-date VT supported by preopen-note labels, and an opening price above VT.
No date is added or removed because of a signal count or outcome. Fourteen of
the89 new dates have no strict-VT entry in these families; all remain in the
date-resampling universe. Qualifying dates are not required to stay above VT
after an entry, which would condition selection on the future.

The primary event gate instead checks every prior minute low from09:30 through
the minute before entry and the entry open. Each must be strictly above VT.
A prior touch/breach blocks the remainder of that date. The entry bar's later
low and future full-day status are never used to approve an entry.

This is a census of **verifiable qualifying dates**, not proof that every other
market day was below VT. Missing/conflicting evidence and incomplete prices stay
explicit. September18,2026 has no saved dated VT or SPX minute input here and
remains unknown; it is not classified below VT. Future2026 sessions cannot be
included. The unchanged full-session rule also excludes the three2025 early closes.

## Important correction to the earlier date audit

The earlier parser required a `Date` field and exact agreement with the first
heading's timestamp. Many older saved notes instead use **`Published`**, sometimes
with a later wrapper heading than the original content heading. The strict parser
reported these as missing preopen corroboration even when the file contained
usable explicit Eastern preopen publication labels and a matching SPX VT table.
That was an avoidable coverage restriction in our earlier implementation.

The new audit reads both metadata formats. It requires at least one explicitly
Eastern publication heading, correct EST/EDT calendar usage, every publication
label on the requested day, and the **latest** such label strictly before09:30.
It preserves differing preopen timestamps rather than claiming they agree.
After-open labels, wrong dates, malformed publication metadata and VT conflicts
are rejected. Scraped-at is never used to establish historical availability.
Publication labels still cannot prove that a saved article had no later revisions.

This recovers **85 additional qualifying dates**, all in2025. Seventy-five of those
new dates have a preserved preopen time discrepancy in at least one usable note.
The other four third-tranche dates were already eligible but not selected in the
earlier random100 draw:2025-09-10,2025-09-11,2025-12-30 and2026-04-16.
The parser correction is disclosed as a change to evidence ingestion; it is not
represented as the old sampler suddenly having more qualifying days.

The old50/100 numeric results remain unchanged and all reproduce. However, the
earlier claim that the recorded eligible universe had only104 new dates was
conditional on this overly restrictive parser. Much of the missing2025 coverage
was recoverable local evidence. This strengthens the need to separate calendar
mix from signal quality; it does not prove why any particular rule deteriorated.

## All13 rows: three tranches and the239-date research total

Cells show successful +5-first signals / distinct entry opportunities, then hit
rate. Overlapping same-variant/date/minute setups count once. Repeated entry times
on the same date and different families can share price paths and are dependent.

'''
    report += table(['Entry', 'Original50', 'Second100', 'Third89', 'Combined239'],
                    [[analysis.LABELS[v]]+[cell(result(v, c)) for c in
                      ['original_50', 'additional_100', 'third_tranche', 'combined_non_development']]
                     for v in replay.VARIANTS])
    report += '''

## Third-tranche uncertainty and outcome accounting

Intervals are95% percentile intervals from10,000 whole-date bootstrap resamples,
seed20260919. They retain zero-event dates and account for dependence within a
date, not every form of serial dependence, regime change or research selection.
The small32-entry combined retest sample remains uncertain; a high pooled rate
does not erase its weak new tranche. Year-specific third2026 intervals have only
one date and cannot support general inference.

'''
    report += table(['Entry', 'N', 'Active dates', '+5 first', '−15 first', 'Neither', 'Hit rate', '95% date interval'],
                    [[r.label, str(r.n), str(r.active_dates), str(r.target_first), str(r.adverse_first),
                      str(r.neither), f'{r.hit_pct:.1f}%', f'{r.date_ci_low_pct:.1f}–{r.date_ci_high_pct:.1f}%']
                     for r in primary[primary.cohort.eq('third_tranche')].itertuples()])
    report += '''

There were no same-minute first-touch ties in these third-tranche strict-VT rows.
They would remain ambiguous and in the denominator if present. B06's neither
rate was36.5%, versus38.4% in tranche2; its adverse rate rose from8.7% to11.5%.
The third-tranche deterioration of the former favorites therefore cannot simply
be described as every rule facing a lower baseline than in tranche2: B01 and
B05 actually improved. No dealer-gamma or IV causal explanation was tested here.

## Repeated-entry sensitivities, third tranche

These are the same predeclared sensitivities, not newly optimized rules.

'''
    report += table(['Entry', 'All entries', 'First per day', 'At least60m apart'],
                    [[analysis.LABELS[v]]+[cell(result(v, 'third_tranche', s))
                      for s in ['all', 'first_per_day', 'spaced60']] for v in replay.VARIANTS])
    report += '''

B06 first-per-day is38/67 (56.7%), while a60-minute cooldown is98/183 (53.6%).
Neither reproduces the original high hit rates. B01's first eligible daily entry
is50/75 (66.7%); time-of-day selection remains a competing explanation for apparent
first-entry improvements. These raw cross-rule rates are not controlled effects.

## What waiting for another condition retained and lost

The paired ledger preserves setups rather than deduplicated entry minutes.
B06 has150 eligible delayed setup records corresponding to146 distinct retest
minutes. On the same150 setups, immediate and retest each hit53.3%; waiting omits
201 successful immediate parents that never produce an eligible delayed entry.

B08 RSI retains9 of60 price-reentry setups. Five of those nine hit either way,
while23 successful price-only parents have no eligible RSI entry. Its55.6% rate
does not establish an independent improvement over those same retained setups.

B10 retest retains12 of57 immediate setups. On those same12, immediate hits5/12
and retest7/12;30 successful immediate parents do not produce a retest. That small
paired improvement is worth preserving as evidence, but is not confirmation of
the previously observed85% retest rate. Each delayed entry has its own60-minute
clock and entry price. These are not equal-start-time causal comparisons.

The inherited same-hour B01 contrasts remain in comparison.csv solely as timing
diagnostics. A later setup selects an earlier control partly using price movement
after the control's entry. Their confidence intervals do not fix this selection
issue, and they are not a promotion rule or proof of signal uplift.

## Complete coverage ledger and remaining exclusions

The180 excluded dates have these mutually exclusive recorded reason combinations:

'''
    reasons = population.loc[~population.eligible, 'exclusion_reasons'].value_counts()
    report += table(['Reason combination', 'Dates'], [[str(k), str(v)] for k, v in reasons.items()])
    report += '''

Above-recorded-VT dates that remain excluded are shown explicitly:

'''
    excluded = population[~population.eligible & population.above_vt_at_open]
    report += table(['Date', 'Recorded VT', '09:30 open', 'Reason'],
                    [[r.date, f'{r.vol_trigger:g}', f'{r.spot_open:.2f}', r.exclusion_reasons]
                     for r in excluded.itertuples()])
    report += '''

The matching preopen Feb7,2025 article has no extracted SPX VT table cell; Sep22–24
have no saved notes. Dec22,2025 and Apr13,2026 publication labels extend past the
open; Apr8,2026 has only an afternoon note. Jun6 and Jul7–8,2025 disagree with
the corrected CSV. These are specific evidence failures, not dates quietly
discarded because of outcomes. The three early-close dates have incomplete
full-session coverage under the frozen390-minute rule.

April7,2025 has four invalid native OHLC observations in the existing SDK response.
The response was reused and rejected; no bars were repaired. September17,2026 was
the single new ThetaData SDK request:391 raw observations,390 normalized RTH bars.
Its09:30 open7631.44 is below the observed preopen VT7660, so it fails eligibility.
Sep14–16 likewise open below their directly observed preopen-note VT values.
Those recent note-only dates extend the audit beyond the CSV's Sep11 endpoint,
without modifying the shared CSV or using next-day levels.

Third-tranche calendar coverage:

'''
    months = third_dates.groupby(third_dates.date.str[:7]).size()
    report += table(['Month', 'Dates'], [[str(k), str(v)] for k, v in months.items()])
    report += '''

This is a historical extension with a substantially different date mix, not a
randomly assigned experiment or guaranteed unseen holdout. The ten original
dashboard dates are shown separately in the full table; their presence in the
249-date descriptive total must not be confused with new evidence.

## Verification and storage

The experiment preserves the committed eight rule-module hashes and scoring
helpers. Input/source/protocol/analysis hashes and entry identities were frozen
before outcomes. The expanded chronological history contains999 source sessions,
with999 included in five-minute history and990 full sessions in minute-RSI history.
Partial history contributes only complete five-minute bins; nothing is filled.
No evaluated event has a prior100-bar calendar gap above four days.

Every prior7,465 raw setup identity and7,313 distinct opportunity reproduces,
including the762 strict-VT B06 subset. Every prior outcome and351 shared summary
rows reproduce exactly. The ten development dates separately reproduce all441
original dashboard identities. Three new-date temporal-prefix checks pass.

The independent verifier rereads native files and checks all12,284 distinct entry
prices, first-touch outcomes and causal VT gates across249 dates; all1,053 summary
rows reconcile. The raw setup ledger contains12,534 records; strict-VT primary
has9,320 distinct opportunities including3,554 in tranche3. Twenty-four targeted
publication, cohort, causal-scoring and accounting tests pass; Ruff passes. No
existing dashboard, rule snapshot, old study or raw source file was changed.

Data was reused wherever available. One new ThetaData index-history request;
zero option-history or ORATS requests. All new data and provenance reside under:

'''
    report += f'''`{DATA}`

- [Full comparison table]({DATA}/comparison.csv):1,053 rows across3 VT scopes,3 sensitivities,9 cohort groups and13 variants.
- [All429 calendar dates and reasons]({DATA}/population.csv), [selected dates]({DATA}/selected_days.csv), [note extracts and timestamps]({DATA}/vt_note_provenance.json).
- [Third-tranche recovered versus legacy-eligible dates]({DATA}/third_admission_comparison.csv).
- [Every distinct event]({DATA}/distinct_event_outcomes.csv), [paired setups]({DATA}/paired_setup_comparison.csv), [independent checks]({DATA}/independent_verification.json).
- [Frozen protocol]({OUT}/PROTOCOL.md), [publication logic]({OUT}/provenance.py), [pipeline]({OUT}/pipeline.py).

Stages are `pipeline.py audit`, `coverage`, `prepare`, `freeze`, `generate`,
`outcomes`, `analyze`, then `verify_results.py` and `report.py`. Existing artifacts
are immutable; deliberate reproduction requires a new namespace. Source metadata,
native hashes and schema inventory are registered in central CHANGELOG and
DATA_DICTIONARY with this isolated study's commit. Earlier notes remain preserved;
this report is the updated candidate assessment after tranche3.
'''
    with (OUT/'FINDINGS.md').open('x') as file:
        file.write(report)
    print(json.dumps({'report': str(OUT/'FINDINGS.md'), 'words': len(report.split()),
                      'verified_opportunities': verification['native_opportunities_checked']}))


if __name__ == '__main__':
    main()

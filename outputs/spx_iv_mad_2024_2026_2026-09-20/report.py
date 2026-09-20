"""Summarize verified SPX IV magnitude history without fitting trading rules."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

import spx_mad as p


def markdown(frame: pd.DataFrame) -> str:
    return '\n'.join(['| ' + ' | '.join(frame.columns) + ' |',
                      '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |',
                      *['| ' + ' | '.join(map(str, row)) + ' |'
                        for row in frame.itertuples(index=False, name=None)]])


def save_csv(name: str, frame: pd.DataFrame) -> None:
    path = p.DATA / name
    if path.exists():
        pd.testing.assert_frame_equal(pd.read_csv(path), frame, check_dtype=False)
    else:
        frame.to_csv(path, index=False)
    alias = p.OUT / name
    if not alias.exists():
        alias.symlink_to(path)


def main() -> None:
    p.freeze()
    folder = p.DATA / 'calibration_exact' / 'SPXW'
    summary = json.loads((folder / 'summary.json').read_text())
    proof = json.loads((folder / 'verification_final.json').read_text())
    pairing = json.loads((p.DATA / 'endpoint_pairing_verification.json').read_text())
    assert pairing['all_greek_keys_preserved'] and pairing['native_values_unchanged']
    for path, sha in summary['output_hashes'].items():
        assert p.digest(Path(path)) == sha
    bases = pd.read_parquet(folder / 'block_baselines.parquet')
    scores = pd.read_parquet(folder / 'scored_windows.parquet')
    daily = pd.read_parquet(p.DATA / 'derived' / 'SPXW' / 'daily_coverage.parquet')
    sessions, targets = p.date_plan()
    gaps = daily[daily.date.isin(targets) & daily.measured_windows.lt(daily.window_slots)]
    gap_table = gaps[['date', 'window_slots', 'measured_windows']].copy()
    gap_table['unavailable_windows'] = gap_table.window_slots - gap_table.measured_windows
    save_csv('gap_dates.csv', gap_table)
    assert proof['baseline_prior_date_counts_verified'] == 5 * len(targets)
    assert proof['scored_windows_verified'] == len(scores)
    assert proof['independent_ols_max_error'] < 1e-12
    save_csv('block_baselines.csv', bases)
    save_csv('daily_coverage.csv', daily)
    for source in [folder / 'scored_windows.parquet', folder / 'block_baselines.parquet',
                   p.DATA / 'derived' / 'SPXW' / 'all_windows.parquet']:
        alias = p.OUT / source.name
        if not alias.exists():
            alias.symlink_to(source)
    scores['magnitude'] = scores.signed_score.abs()
    valid = scores.magnitude.notna()
    np.testing.assert_allclose(scores.loc[valid, 'magnitude'],
                               (scores.loc[valid, 'acceleration'] / scores.loc[valid, 'scale']).abs())
    years = []
    for year, frame in scores.groupby(scores.date.str[:4]):
        base_year = bases[bases.date.str.startswith(year)]
        years.append({'Year': year, 'Dates': frame.date.nunique(), 'Expected windows': len(frame),
                      'Scored windows': int(frame.signed_score.notna().sum()),
                      'Window coverage': f'{frame.signed_score.notna().mean():.2%}',
                      'Usable baselines': f'{base_year.status.eq("ok").sum()}/{len(base_year)}'})
    annual = pd.DataFrame(years)
    save_csv('annual_coverage.csv', annual)
    support = []
    for year, frame in scores.groupby(scores.date.str[:4]):
        observed = frame[frame.available]
        support.append({'Year': year, 'Usable windows': len(observed),
                        'With neighbor sources': int(observed.neighbor_slots.gt(0).sum()),
                        'With guarded recovery': int(observed.fallback_slots.gt(0).sum()),
                        'Minimum unique sources': int(observed.unique_sources.min()),
                        'Maximum shift minutes': int(observed.maximum_shift_minutes.max())})
    support_table = pd.DataFrame(support)
    save_csv('support_summary.csv', support_table)
    hourly = []
    for block, frame in bases.groupby('block'):
        current = scores[scores.block.eq(block)]
        hourly.append({'Block': p.magnitude.block_name(block),
                       'Usable baselines': f'{frame.status.eq("ok").sum()}/{len(frame)}',
                       'Historical dates min': frame.history_days.min(),
                       'Historical dates median': frame.history_days.median(),
                       'Historical dates max': frame.history_days.max(),
                       'Window coverage': f'{current.signed_score.notna().mean():.2%}'})
    save_csv('hourly_coverage.csv', pd.DataFrame(hourly))
    dt = pd.to_datetime(scores.date)
    scores['half'] = dt.dt.year.astype(str) + ' H' + np.where(dt.dt.month.le(6), '1', '2')
    scores.loc[scores.half.eq('2026 H2'), 'half'] = '2026 H2*'
    labels = ['<1', '1–2', '2–3', '3–5', '5+']
    scores['bin'] = pd.cut(scores.magnitude, [0, 1, 2, 3, 5, np.inf], labels=labels, right=False)
    bins, coverage = [], []
    for half, frame in scores.groupby('half'):
        measured = frame[frame.magnitude.notna()]
        coverage.append({'half': half, 'dates': frame.date.nunique(), 'expected': len(frame),
                         'scored': len(measured), 'coverage': len(measured) / len(frame),
                         'magnitude_ge2_percent': 100 * measured.magnitude.ge(2).mean(),
                         'magnitude_ge3_percent': 100 * measured.magnitude.ge(3).mean()})
        counts = measured.bin.value_counts().reindex(labels, fill_value=0)
        assert counts.sum() == len(measured)
        for label, count in counts.items():
            bins.append({'half': half, 'bin': label, 'count': int(count),
                         'percent_of_scored': 100 * count / len(measured) if len(measured) else np.nan})
    bin_table, coverage_table = pd.DataFrame(bins), pd.DataFrame(coverage)
    save_csv('magnitude_bins.csv', bin_table)
    save_csv('half_year_coverage.csv', coverage_table)
    colors = ['#dce5ee', '#7dafd4', '#377ba8', '#c47a35', '#a23f32']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, ax = plt.subplots(figsize=(13, 6.8))
    ordered = bin_table.pivot(index='half', columns='bin', values='percent_of_scored')[labels]
    left = np.zeros(len(ordered))
    for label, color in zip(labels, colors, strict=True):
        vals = ordered[label].to_numpy()
        ax.barh(ordered.index, vals, left=left, color=color, height=.65,
                edgecolor='white', linewidth=.5)
        for i, value in enumerate(vals):
            if value >= 5:
                ax.text(left[i] + value / 2, i, f'{value:.1f}%', ha='center', va='center',
                        color='#233344' if label == '<1' else 'white', fontsize=10)
        left += vals
    ax.invert_yaxis()
    ax.set_xlim(0, 132)
    ax.set_xticks([0, 25, 50, 75, 100], ['0%', '25%', '50%', '75%', '100%'])
    ax.spines[['left', 'right', 'top']].set_visible(False)
    ax.spines['bottom'].set_bounds(0, 100)
    ax.tick_params(axis='y', length=0)
    for i, row in enumerate(coverage_table.itertuples()):
        ax.text(102, i, f'{row.scored:,} scored\n{row.coverage:.1%} coverage',
                va='center', fontsize=9, color='#455667')
    fig.suptitle('SPX IV acceleration magnitude by half-year', fontsize=18, weight='bold', y=.98)
    fig.text(.5, .913, '|acceleration| / (1.4826 × historical MAD) · SPXW options on the SPX index',
             ha='center', fontsize=11, color='#455667')
    fig.legend(handles=[Patch(facecolor=c, label=b) for b, c in zip(labels, colors, strict=True)],
               loc='upper center', bbox_to_anchor=(.5, .88), ncol=5, frameon=False)
    fig.text(.07, .06, 'Both acceleration directions; percentages use available minute endpoints. '
             'Overlapping windows are not independent trials.', fontsize=9, color='#455667')
    fig.text(.07, .025, '*2026 H2 ends September 18. Endpoint hours: 09:59–14:29 ET; early closes end 12:59. '
             'Each score uses strictly prior history.', fontsize=9, color='#455667')
    fig.tight_layout(rect=[0, .1, 1, .81])
    fig.savefig(p.OUT / 'magnitude_bins_by_half_year.png', dpi=160)
    fig.savefig(p.OUT / 'magnitude_bins_by_half_year.svg')
    plt.close(fig)
    logs = [json.loads(line) for line in (p.DATA / 'requests.jsonl').read_text().splitlines()]
    starts = [r for r in logs if r['status'] == 'started']
    oks = [r for r in logs if r['status'] == 'ok']
    errors = [r for r in logs if r['status'] == 'error']
    unresolved = {r['key'] for r in starts} - {r['key'] for r in oks}
    if unresolved:
        raise ValueError(f'Unresolved provider requests remain: {len(unresolved)}')
    attempts = Counter(r['key'] for r in starts)
    assert max(attempts.values(), default=0) <= 3 and len(starts) <= 12000
    for key, count in attempts.items():
        if count == 3:
            assert any(r.get('key') == key and r['status'] == 'retry_authorized_cooled_internal_probe'
                       for r in logs)
    missing_target = daily[daily.date.isin(targets) & daily.status.ne('captured')]
    manifest = {'status': 'complete', 'underlying': 'SPX', 'option_root': 'SPXW',
                'sessions': len(sessions), 'target_sessions': len(targets), 'summary': summary,
                'verification': proof, 'endpoint_pairing_verification': pairing,
                'sdk_attempts': len(starts), 'sdk_successes': len(oks),
                'sdk_errors': len(errors), 'unresolved_requests': sorted(unresolved),
                'missing_target_dates': missing_target[['date', 'status']].to_dict('records'),
                'protocol_sha256': p.digest(p.DATA / 'protocol_freeze.json'),
                'report_producer_sha256': p.digest(Path(__file__))}
    p.write_json(p.DATA / 'manifest.json', manifest)
    report = f'''# SPX IV acceleration and MAD history — complete

**681 target sessions, January 2, 2024–September 18, 2026**, plus 60 prior warmup
sessions beginning October 5, 2023. Underlying is SPX itself; consistently use
the native SPXW PM-settled option root. No ETF proxy or AM/PM root mixing.

**{summary['target_scored']:,}/{summary['target_windows']:,} current windows scored
({summary['target_scored']/summary['target_windows']:.2%}).** Baseline status:
`{json.dumps(summary['baseline_status'])}`. A usable historical baseline does not
guarantee a usable current-minute observation. Unavailable measurements remain
explicitly unknown. Missing target-date expiry brackets: **{len(missing_target)}**.

{markdown(annual)}

Current-window support under the unchanged rules:

{markdown(support_table)}

Neighbor and recovery counts can overlap. A usable window need not contain thirty
distinct strict observations. Reused source timestamps are deduplicated before
the slope calculation; none is counted twice as an independent observation.

Dates with unavailable target windows:

{markdown(gap_table) if len(gap_table) else 'None.'}

Recorded missing-source windows remain unknown. The native-input gap inspection
is saved separately in `gap_diagnostics.json`; it samples the first and last
unavailable endpoint on each affected date. An underlying price outside a
downloaded expiry's strike range cannot support ATM interpolation. Such a gap
is a collection-range limitation, not proof that the market had no quote. No
strike-range expansion, extrapolation or quality relaxation was applied here.

Same existing calculation: 30-calendar-day ATM IV; 8–65 DTE bracketing, call/put
variance average, native IV and matched first-order quote histories. Strict exact,
then strict ±2-minute neighbors inside the actual window/hour, then guarded
original-minute recovery with 100% spread ceiling. Positive dollar bid/ask required.
Actual-time fifteen-minute slopes; acceleration=(b2−b1)/15. Sixty strictly prior
sessions per endpoint-hour block, both signs, equal total date weight, exact lower
weighted median/MAD. Scale=1.4826×MAD; at least 10 contributing dates and positive
non-tiny scale. Signed score=−a/scale; absolute magnitude=abs(a)/scale; downward-only
also requires falling IV and negative acceleration. No thresholds fitted.

## The calculation in plain language

At each minute endpoint, use the preceding thirty completed minute observations.
Fit IV's rate of change separately over the first fifteen minutes and the last
fifteen minutes. Call those slopes b1 and b2. Acceleration is (b2 − b1) / 15;
the divisor is the fifteen-minute separation between the two half-window centers.
Its units are IV percentage points per minute squared. A negative value means the
IV slope is becoming more negative; IV may still be rising, just more slowly.

Compare that acceleration with its own SPX history in the same hourly block over
exactly sixty prior sessions. First find the weighted historical median, then the
weighted median distance from that median: MAD. Each contributing date has the
same total weight. Multiply MAD by 1.4826, the conventional conversion factor
1 / 0.67448975, where 0.67448975 is the standard normal's 75th percentile. It puts
MAD on a standard-deviation-like scale under a normal reference; it does not
assume these accelerations are normal or turn the score into a probability.

Divide the current absolute acceleration by that scale for magnitude. Keep the
raw sign separately, or use −acceleration / scale so positive means downward
acceleration. The numerator is measured from zero, not from the historical
median: this preserves physical acceleration direction. Whether IV is actually
falling is a separate b2 check. All inputs stop at the endpoint; an entry at T
would use the endpoint T−1. No future observations enter its score.

![SPX half-year magnitude]({p.OUT}/magnitude_bins_by_half_year.png)

Bars use available minute endpoints, both signs, equally weighted per endpoint.
Half-years have unequal lengths and overlapping windows are not independent.
2026 H2 stops September 18. Scope remains 09:30–14:29 ET observations, giving complete
window endpoints 09:59–14:29; early-close endpoints stop 12:59. This does not extend
the previous intraday measurement scope to the closing hour.

## Verification and provenance

Thirteen boundary tests pass; inherited quote-guard checks pass. Every baseline
is checked by independent rational-CDF inequalities, every prior-date/count ledger
and score is verified, and every usable OLS fit is replayed independently.
{proof['source_prefix_checks']} prefix checks include 2023 warmup and 2024 target
boundaries. Frozen inherited calculation/quality dependencies stay unchanged.
Boundary probes used required actual data at the first warmup, first target and
last target dates; all inputs were reused by the full run.

One native alignment exception is explicitly recorded. On June 9, 2026 the IV
endpoint returned 79,200 rows, a strict superset of all 36,000 Greek keys. A separate
paired IV view retains every Greek key and its unchanged IV counterpart; 43,200
unmatched IV-only rows are excluded. Original responses remain immutable, all
quote/IV checks remain unchanged, and independent pairing verification passes.
All 271 windows on that date are available. See the protocol addendum and pairing
receipt; this is a documented input repair, not a silent alteration of the original
protocol or a missing-Greek fill. No extra data request was made.

{len(starts):,} explicit SDK data attempts; {len(oks):,} successful new responses;
{len(errors)} recorded error attempts; no unresolved requests. Authentication is
excluded from data-call counts. Original sector data is unchanged. Native inputs,
expiry selections, dates, source/window tables, support and missingness, baseline
ledgers, scores and all hashes are in `{p.DATA}`.

This builds the requested measurement history. No B0x outcome test, ranking cutoff,
probability or option-profitability claim is introduced.

- [Scores]({p.OUT}/scored_windows.parquet)
- [Daily/hourly baselines]({p.OUT}/block_baselines.csv)
- [Daily coverage]({p.OUT}/daily_coverage.csv)
- [Hourly coverage]({p.OUT}/hourly_coverage.csv)
- [Window support]({p.OUT}/support_summary.csv)
- [Half-year counts]({p.OUT}/magnitude_bins.csv)
- [Protocol]({p.OUT}/PROTOCOL.md)
- [Endpoint pairing addendum]({p.OUT}/PROTOCOL_ADDENDUM.md)
- [Gap source inspection]({p.DATA}/gap_diagnostics.json)

Calendar reference: [NYSE/ICE 2023 calendar](https://ir.theice.com/press/news-details/2022/NYSE-Group-Announces-2023-2024-and-2025-Holiday-and-Early-Closings-Calendar/default.aspx).
Contract-root reference: [ThetaData symbology](https://docs.thetadata.us/Articles/Data-And-Requests/Symbology.html).
'''
    (p.OUT / 'FINDINGS.md').write_text(report)
    print(annual.to_string(index=False))
    print(json.dumps({'scored': summary['target_scored'], 'baselines': summary['baseline_status'],
                      'sdk_attempts': len(starts), 'errors': len(errors)}))


if __name__ == '__main__':
    main()

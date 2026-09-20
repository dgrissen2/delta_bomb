"""Render the complete frozen grid and a concise, explicitly exploratory findings note."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pandas as pd

from run import DATA, OUT, ROOT, COMPLETE, digest, save_json

LABELS = {
    'baseline': 'Plain B09',
    'signed_m1_b4': 'M > 1 in ≥4 sectors; acceleration alone',
    'falling_m1_b4': 'M > 1 in ≥4 sectors; IV also falling',
    'signed_m1_b5': 'M > 1 in ≥5 sectors; acceleration alone',
    'falling_m1_b5': 'M > 1 in ≥5 sectors; IV also falling',
}
SHORTLIST = list(LABELS)


def markdown(headers: list[str], rows: list[list]) -> str:
    """Small dependency-free Markdown table renderer."""
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join(['---'] * len(headers)) + ' |']
                     + ['| ' + ' | '.join(str(x) for x in row) + ' |' for row in rows])


def cell(row: pd.Series) -> str:
    return f"{int(row.targets)}/{int(row.n)} · {row.rate:.1f}%" if row.n else '0 signals'


def plot_grid(stability: pd.DataFrame) -> None:
    """Show N, accuracy and worst-half uplift together so small cells stay visible."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    columns = [('completed_n', 'Signals retained', 'Blues'),
               ('completed_rate', 'Hit rate (%)', 'viridis'),
               ('worst_uplift', 'Worst half-year uplift (pp)', 'RdBu')]
    for i, family in enumerate(['signed', 'falling']):
        sub = stability[stability.family.eq(family) & stability['mode'].eq('all')]
        for j, (field, title, cmap) in enumerate(columns):
            values = sub.pivot(index='threshold', columns='breadth', values=field).reindex(index=[1,2,3,4], columns=range(4,10)).to_numpy()
            ax = axes[i, j]
            kwargs = {'vmin': 0, 'vmax': 225} if j == 0 else {'vmin': 0, 'vmax': 100} if j == 1 else {'norm': TwoSlopeNorm(vmin=-60, vcenter=0, vmax=20)}
            im = ax.imshow(values, cmap=cmap, aspect='auto', **kwargs)
            ax.set_xticks(range(6), range(4, 10))
            ax.set_yticks(range(4), [1,2,3,4])
            ax.set_xlabel('Minimum qualifying sectors (of 11)')
            ax.set_ylabel('Exceed scaled-MAD threshold')
            family_label = 'Downward acceleration' if family == 'signed' else 'Downward acceleration + falling IV'
            ax.set_title(f'{family_label}\n{title}', fontsize=11)
            for y in range(4):
                for x in range(6):
                    value = values[y, x]
                    text = '—' if not np.isfinite(value) else f'{value:.0f}' if j == 0 else f'{value:.1f}'
                    rgba = im.cmap(im.norm(value)) if np.isfinite(value) else (1,1,1,1)
                    luminance = .2126*rgba[0] + .7152*rgba[1] + .0722*rgba[2]
                    ax.text(x, y, text, ha='center', va='center', fontsize=10,
                            color='white' if luminance < .5 else '#152238')
            fig.colorbar(im, ax=ax, shrink=.8)
    fig.suptitle('B09 MAD grid: 2025 H1, 2025 H2, 2026 H1\n+5 before −10 within 60 minutes; above VT; 48 exploratory cells', fontsize=15)
    fig.savefig(DATA / 'grid.png', dpi=160)
    plt.close(fig)


def main() -> None:
    """Generate reports only from verified analysis artifacts; no new signal selection."""
    verification = json.loads((DATA / 'verification.json').read_text())
    summary = pd.read_csv(DATA / 'summary.csv')
    stability = pd.read_csv(DATA / 'stability.csv')
    uncertainty = pd.read_csv(DATA / 'uncertainty.csv')
    prior_path = ROOT / 'branch_b_iv_full_2024_2026_2026-09-19-v1/comparison.csv'
    prior = pd.read_csv(prior_path)
    prior = prior[prior.variant.eq('b09') & prior.rule.eq('guarded_100_accelerating_8')
                  & prior['mode'].eq('all') & prior.state.eq('yes')
                  & prior.period.isin(COMPLETE + ['2026_H2'])]
    if int(prior.n.sum()) != 54 or int(prior.targets.sum()) != 35:
        raise ValueError('Prior B09 benchmark changed')

    def get(rule: str, period: str, mode: str = 'all', state: str | None = None) -> pd.Series:
        state = state or ('all' if rule == 'baseline' else 'yes')
        selected = summary[summary.rule.eq(rule) & summary.period.eq(period)
                           & summary['mode'].eq(mode) & summary.state.eq(state)]
        if len(selected) != 1:
            raise ValueError((rule, period, mode, state))
        return selected.iloc[0]

    half_table = markdown(['Rule', '2025 H1', '2025 H2', '2026 H1', '2026 H2, partial', 'Overall'],
        [[LABELS[r]] + [cell(get(r, p)) for p in COMPLETE + ['2026_H2', 'pooled']] for r in SHORTLIST])
    sensitivity = markdown(['Rule', 'All entries', 'First qualifying entry/day', '60-minute spacing'],
        [[LABELS[r]] + [cell(get(r, 'pooled', mode)) for mode in ['all','first','spaced60']] for r in SHORTLIST])
    coverage = markdown(['Rule', 'Yes', 'Definite no', 'Unknown', 'Measurable parent'],
        [[LABELS[r]] + [cell(get(r, 'pooled', state=s)) for s in ['yes','no','unknown','measurable']]
         for r in SHORTLIST[1:]])
    retention_rows = []
    baseline = get('baseline', 'pooled')
    for r in SHORTLIST[1:]:
        row = get(r, 'pooled')
        retention_rows.append([LABELS[r], int(row.n), int(row.days),
            f'{100*row.n/baseline.n:.1f}%', int(row.targets),
            f'{100*row.targets/baseline.targets:.1f}%', int(baseline.targets-row.targets)])
    retention = markdown(['Rule','Signals','Active dates','Signals retained','Winners retained',
                          'Share of B09 winners','Winners excluded'], retention_rows)
    cirows=[]
    for r in SHORTLIST[1:]:
        row=uncertainty[uncertainty.rule.eq(r)&uncertainty['mode'].eq('all')].iloc[0]
        cirows.append([LABELS[r],f'{row.low:.1f}–{row.high:.1f}%',
                       f'{row.uplift_low:+.2f} to {row.uplift_high:+.2f} pp'])
    intervals=markdown(['Rule','95% date-bootstrap rate interval','Uplift versus plain B09'],cirows)
    appendix = ['# All 48 B09 MAD cells', '',
        'Unchanged +5/−10/60-minute score; above VT. Threshold comparison is strictly >; breadth is ≥.',
        '2026 H2 is partial through September 18 and excluded from stability selection.', '']
    for family in ['signed', 'falling']:
        appendix += [f'## {family}', '', markdown(
            ['MAD >','Sectors ≥','2025 H1','2025 H2','2026 H1','2026 H2 partial','Overall','Positive uplift in all completed halves'],
            [[k,b] + [cell(get(f'{family}_m{k}_b{b}', p)) for p in COMPLETE+['2026_H2','pooled']]
             + [bool(stability[stability.rule.eq(f'{family}_m{k}_b{b}') & stability['mode'].eq('all')].iloc[0].positive_all_halves)]
             for k in [1,2,3,4] for b in range(4,10)]), '']
    (OUT / 'ALL_48_RESULTS.md').write_text('\n'.join(appendix))
    note = f'''# B09 MAD grid — both direction definitions

Completed September 20, 2026. **48/48 predeclared cells evaluated. Independent Claude review NOT RUN.**
This side conversation prohibits launching separate reviewer agents. Local checks below are not
a substitute for independent Claude review and do not constitute its sign-off.

## What worked, what did not

**The useful region is M > 1 in four or five sectors. Higher thresholds or broader requirements
largely exhaust N.** Four of the 48 rules improve the observed hit rate over plain B09 in all
three completed half-years. Those four are precisely the two direction definitions at M > 1
with breadth four/five. No threshold was changed or added after seeing outcomes.

The predeclared high-N ordering selects **downward acceleration alone, M > 1 in at least four
sectors**: 139/235 = 59.1% overall, 134/225 = 59.6% in the completed halves. Its completed-half
hit rates are 57.7%, 57.3%, 65.5%, versus parent rates 55.3%, 48.3%, 59.9%. It is the largest
qualifying subset in the entire requested grid, but retains only 7.5% of all B09 entries.

**Requiring IV already falling gives a stronger accuracy candidate at the same 1/four setting:**
115/188 = 61.2% overall. It retains 188 signals on 95 dates and improves on plain B09 in every
completed half. First-per-day reaches 61/95 = 64.2%; sixty-minute spacing reaches 76/121 = 62.8%.
This is a tradeoff candidate, not the automatic winner of the predeclared high-N ranking.

At four sectors, allowing acceleration without the falling condition adds 47 signals and 24
winners (51.1%). Of those, 40 are definite falling-rule nonqualifiers, 20/40 = 50.0%; seven
have an unknown falling classification, 4/7 = 57.1%. Do not describe all 47 as definitely
rising-IV entries: the count rule differs at the basket level and some classifications are unknown.

Requiring five sectors gives 66.3% without the falling condition and 67.2% with it, but only
80 and 64 signals. The latter has the smoothest raw completed-half percentages (64.0%,65.2%,73.3%)
of these four, yet has only 12–18 active dates per completed half. Its first-per-day pooled
rate falls to 62.2%. The more impressive raw percentage does not erase the opportunity cost.

For thresholds 2, 3 or 4, the largest pooled N is only 26. Breadth six at threshold one has
only 25 or 22 signals; breadth seven–nine is sparser still. **This grid has not delivered
thousands of opportunities at a stable high hit rate.** Its candidate region sits on the
least restrictive boundaries of the requested grid, not in a broad plateau of robust settings.
No lower thresholds or smaller breadth values were searched.

## Same-population half-years

{half_table}

This baseline is **1,704/3,141 = 54.3% for 2025–2026**, not the 2,890/5,560 = 52.0% figure
from the longer 2024–2026 price study. There are 239 selected research dates, 178 with B09
signals. 2026 H2 stops September 18. Its four-sector observations are worse than its plain
B09 baseline (50.0% and 57.1% versus 62.6%), but have only ten and seven signals. The five-sector
100% cells contain two and one signals; they cannot establish a continuation of the edge.

For another same-period reference, the previously examined B09 guarded-100 eight-sector IV
acceleration rule gives **35/54 = 64.8%** during 2025–2026. New MAD 1/four with falling IV
retains **188 versus 54 signals (3.5×)** at **61.2% versus 64.8%**. Acceleration alone retains
235 signals at59.1%. This expands N relative to that selective older recipe, not relative to
plain B09. It also changes timing, normalization, sector count and measurement policy, so
the comparison cannot attribute its differences to MAD normalization alone. The older pooled
69/105 =65.7% headline includes2024 and must not be used as the same-period comparator.

## Repeated signals and opportunity cost

{sensitivity}

Filter before thinning; each policy uses its own corresponding unfiltered B09 baseline.
Thinning resets by date and never uses outcomes. These counts are signals, not independent
trades. First-per-day signed 1/five fails to improve on plain B09 in 2025 H1; the four-sector
candidates retain positive observed uplift in every completed half under all three policies.

{retention}

## Missingness remains explicit

{coverage}

The fixed denominator remains eleven ETFs. Missing XLRE observations are not negative votes.
A rule can qualify with sufficient observed sectors despite some unknowns; otherwise it is
unknown when the unavailable sectors could change the answer. No data were fetched or filled.
The four-sector unknown groups themselves have roughly 61% success. Excluding those signals
is a real coverage/opportunity cost, not evidence they are bad entries.

## Uncertainty and selection

{intervals}

Intervals use 5,000 whole-date resamples, seed20260919, all239 selected dates including zero-entry
dates, and shared draws for the rule and baseline. They address within-date dependence, not
serial dependence across dates, searching48 correlated cells or prior research. The falling
1/four raw uplift interval starts only0.01pp above zero; rounding it to a decisive positive
result would be misleading. These are exploratory intervals, not a corrected proof of edge.

Stability selection used only the three completed halves; it required a strictly positive
observed uplift in every half and then ranked retained completed-half N. All48 cells, including
zeros, failures, unknowns and their neighboring cells, remain in the published grid. The
nondominated N/weakest-accuracy/weakest-uplift set is in stability.csv. No fresh holdout exists.

## Exact calculation and timing

M = −a / (1.4826×MAD); a = (b2−b1)/15 using the existing actual-time IV slopes in each
fifteen-minute half. Source is thirty-calendar-DTE ATM midpoint IV, existing strict/neighbor/
guarded-recovery measurement policy. This is zero-centered signed magnitude. MAD describes
historical acceleration dispersion; M is not median-centered, a percentile or a probability.

At B09 entry minute T, use the exact existing window ending T−1 (T−30…T−1 inclusive).
Every actual quote source lies within it; no endpoint carry-forward or future source. This is
a declared timing change from the old B06 IV reference endingT−6. Historical baselines use
sixty strictly prior sessions, same ETF/hour block, both signs/all regimes and equal total
weight per date. Existing minimum support and quote-quality rules were not optimized.

Signed family: M > k. Falling family: M > k AND b2 < −1e−12, in the same ETF.
Count≥b, k∈{{1,2,3,4}}, b∈{{4,5,6,7,8,9}}. Equality to k does not qualify. No weights, dynamic
sector selection, option Greeks or positioning estimates are introduced.

Above-VT means every prior RTH minute low and entry open strictly above same-date VT;
no future full-session-above restriction. +5 before−10 is evaluated in the unchanged60 native
minute bars including entry. Neither and same-minute ambiguous touches remain in N.
Post-target reversal has no effect on success.

## Verification and artifacts

All66 registered MAD source hashes verified; all11×2,145 historical baselines are available.
All source-date ledgers are strictly prior; all usable entry-score arithmetic and actual quote
timestamps were checked. Outcome-free memberships and input/code hashes were frozen before
loading outcome columns. Existing price outcome hash was verified and never changed.

Ten boundary/missingness/execution tests pass. A separate scalar implementation replayed
**{verification['scalar_memberships_replayed']:,} memberships**, all
**{verification['summary_rows_replayed']:,} summary rows**, and all12 inherited B09 half-year/policy
baselines. Threshold, breadth and direction nesting hold. This is local verification by the
same assistant, not independent review. No Claude verdict exists for this run.

- [Frozen protocol]({OUT / 'PROTOCOL.md'})
- [All48 half-year cells]({OUT / 'ALL_48_RESULTS.md'})
- [Summary, including yes/no/unknown/measurable]({DATA / 'summary.csv'})
- [Stability and high-N ranking]({DATA / 'stability.csv'})
- [Whole-date uncertainty]({DATA / 'uncertainty.csv'})
- [Added/removed direction groups]({DATA / 'paired_families.csv'})
- [Membership/source freeze]({DATA / 'freeze.json'})
- [Verification receipt]({DATA / 'verification.json'})

All derived data are in `{DATA}`. No dashboard, original datasets, global registry or unrelated
working-tree edits were modified. No new market-data requests and no commit were made.

![All48 grid]({DATA / 'grid.png'})
'''
    # Normalize typography only; all numbers remain derived from frozen tables.
    spacing = {
        'All48': 'All 48', 'all48': 'all 48', 'all66': 'all 66', 'All66': 'All 66',
        'all11': 'all 11', 'all12': 'all 12', 'all239': 'all 239',
        'seed20260919': 'seed 20260919', 'searching48': 'searching 48',
        'only0.01pp': 'only 0.01 pp', 'unchanged60': 'unchanged 60',
        'endingT−6': 'ending T−6', 'before−10': 'before −10',
        'at59.1%': 'at 59.1%', '=65.7%': '= 65.7%', 'includes2024': 'includes 2024',
    }
    for old, new in spacing.items():
        note = note.replace(old, new)
    (OUT / 'FINDINGS.md').write_text(note)
    plot_grid(stability)
    (DATA / 'DATA_DICTIONARY.md').write_text('''# B09 MAD grid data dictionary

Scope: 2025-01-02 through2026-09-18, B09 strict above-VT research events; development_10 excluded.
All times are integer minutes after midnight in America/New_York. known_min is executable
entry T; end_min=T−1. Each entry_id is date|known_min. All original sources are read-only.

- event_keys.parquet: outcome-free deduplicated3141 B09 entry identities, cohort and half.
- research_dates.csv:239 inherited selected dates including dates without B09 entries.
- sector_at_entry.parquet:34551 rows, one per event/ETF, exact endpoint join. signed_score is
  −acceleration/(1.4826×MAD); b1/b2 IV percentage points/min; acceleration percentage points/min²;
  scale has acceleration units. source_minutes records actual quote timestamps. Existing support
  counts, statuses, recovery diagnostics and historical-scale fields are retained verbatim.
- memberships.parquet:150768 rows,3141 entries×48 rules. family signed/falling; threshold1–4
  uses strict>; breadth4–9 uses≥. state yes/no/unknown; qualifying_sectors and unknown_sectors
  always refer to the fixed eleven-ETF universe. No outcome columns.
- events_with_outcomes.parquet: immutable parent with unchanged score, entry_price and first
  touch minute. Only target_first wins. adverse_first/neither/ambiguous remain in N.
- summary.csv: period, mode, rule, state; n,targets,days,rate (percent), outcome counts, parent
  counts,uplift_pp and winner identity overlap. measurable=yes+no BEFORE independent thinning;
  state counts partition the parent only in all-entry mode. first/spaced groups each filter then
  thin; their Ns must not be added across states. Winner overlap is identity-based, not simply
  a count difference under thinning.
- stability.csv: completed-half N/rate,worst_rate,worst_uplift,half_rate_sd (population pp),
  min_half_n/min_half_days. positive_all_halves requires observed uplift>0 in all three complete
  halves with signals. high_n_stable_rank prioritizes completed N then worst rate; it is not a
  significance rank. pareto is nondominance in N,worst accuracy,worst uplift within each mode.
- uncertainty.csv: pooled rate/uplift descriptive95% date-bootstrap intervals. No multiple-search
  or serial-correlation correction; empty or no-variation/single-date selected groups have no CI.
- paired_families.csv: falling qualifiers versus signed qualifiers definitely failing or having
  unknown falling condition, fixed matching threshold/breadth, all entries only.
- coverage.csv: usable scores at the exact entry endpoint, before any outcome filter.
- freeze.json,analysis_receipt.json,verification.json: input/code/membership hashes and audits.
- grid.png: completed-half grid; no incomplete-half observations drive its stability values.

Mode all=every deduplicated signal; first=first qualifying signal per date; spaced60=greedy≥60
minutes between qualifying signals, daily reset. Filtering precedes either thinning policy.
Partial2026H2 is reported separately; full2024 is outside MAD coverage. Unknowns never become
zeros or negative votes. Experimental cells are correlated; N is not independent observations.
''')
    (DATA / 'CHANGELOG.md').write_text('''# Changelog

2026-09-20: Added isolated B09 48-cell MAD outcome overlay: two direction definitions,
four fixed thresholds, six fixed sector-count cutoffs. Reused hash-verified11-sector exact
MAD scores and unchanged +5/−10 price outcomes. No acquisition or modification of sources.
Wrote causal membership freeze, all states/halves/execution policies, whole-date intervals,
high-N/stability frontier, scalar verification, and findings. Independent Claude review
remains NOT RUN under the side-conversation prohibition on separate reviewers.
''')
    artifacts = [OUT / 'FINDINGS.md', OUT / 'ALL_48_RESULTS.md', DATA / 'grid.png',
                 DATA / 'DATA_DICTIONARY.md', DATA / 'CHANGELOG.md', Path(__file__)]
    save_json(DATA / 'report_receipt.json', {
        'artifacts': {str(p): digest(p) for p in artifacts},
        'descriptive_prior_benchmark': {str(prior_path): digest(prior_path)},
    })
    print(OUT / 'FINDINGS.md')


if __name__ == '__main__':
    main()

"""Render complete comparison tables and an N/accuracy plot from verified outputs."""
from __future__ import annotations

import json

import pandas as pd

from inputs import DATA, OUT
from provenance import checked_execution, check_manifest

KEY_RULES = ['original_falling_6','original_accelerating_6','midpoint_falling_6',
    'midpoint_accelerating_6','guarded_100_falling_6','guarded_100_accelerating_6',
    'guarded_50_falling_6','guarded_50_accelerating_6','balanced_falling_6',
    'balanced_accelerating_6','paired_price_iv_6','original_weighted_falling',
    'original_weighted_accelerating','original_falling_and_breakout5','price_only_6']


def markdown(frame: pd.DataFrame) -> str:
    return frame.to_markdown(index=False,floatfmt='.1f')


def main() -> None:
    checked_execution()
    check_manifest(DATA/'independent_verification.json')
    results = pd.read_csv(DATA/'comparison.csv')
    unions = pd.read_csv(DATA/'unions.csv')
    errors = pd.read_csv(DATA/'uncertainty.csv')
    measured = pd.read_csv(DATA/'measured_baselines.csv')
    registry = pd.read_parquet(DATA/'rule_registry.parquet')
    primary = results[results.period.eq('pooled')&results['mode'].eq('all')]
    text = ['# Full 2024–2026 IV comparison: result tables',
        'Score: **+5 before −10 in sixty native minutes**. All entries pass strict causal '
        'above-VT admission. Primary population: 411 research dates; ten development '
        'dates are separate. Timeouts/ambiguous bars count in N. No post-target penalty.',
        'All results are descriptive on previously examined data. The rule inventory is '
        'broad, and the 95% whole-date intervals are not adjusted for multiple comparisons. '
        'Unknown does not mean that an IV condition failed. N is entries, not independent days.',
        f'Complete numerical outputs: `{DATA}`. See comparison.csv for every rule, family, '
        'half-year and thinning mode; unions.csv for every prespecified union.']
    text += ['## Unfiltered price baselines',markdown(primary[primary.rule.eq('baseline')][
        ['variant','n','targets','rate','days','adverse_first','neither','ambiguous']])]
    for variant in ['b06_breakout','thrust','staircase','b09','b10_breakout']:
        selection = primary[primary.variant.eq(variant)&primary.rule.isin(KEY_RULES)&primary.state.eq('yes')]
        unknown = primary[primary.variant.eq(variant)&primary.rule.isin(KEY_RULES)&primary.state.eq('unknown')].set_index('rule').n
        table = selection[['rule','n','targets','rate','days','retained_baseline_targets']].copy()
        table['unknown_n'] = table.rule.map(unknown)
        eq = measured[measured.variant.eq(variant)&measured['mode'].eq('all')].set_index('rule').rate
        table['measured_baseline_rate'] = table.rule.map(eq)
        ci = errors[errors.variant.eq(variant)&errors['mode'].eq('all')].set_index('rule')
        table['ci_low'],table['ci_high'] = table.rule.map(ci.low),table.rule.map(ci.high)
        table['ci_status'] = table.rule.map(ci.ci_status)
        text += [f'## {variant}: fixed principal rules',markdown(table)]
    text += ['## Half-year repeatability: B06',
        'Each cell shows target-first count / N, hit rate, and distinct trading dates. '
        'Half-year estimates are descriptive; intervals are pooled only. Small date counts '
        'cannot establish repeatability. Empty cells are unavailable, not zero success.']
    half = results[results.variant.eq('b06_breakout')&results['mode'].eq('all')&results.period.str.contains('_H')&
        ((results.rule.isin(KEY_RULES)&results.state.eq('yes'))|results.rule.eq('baseline'))].copy()
    half['cell'] = half.apply(lambda r:f'{int(r.targets)}/{int(r.n)} ({r.rate:.1f}%; {int(r.days)} days)' if r.n else 'N=0',axis=1)
    text.append(half.pivot(index='rule',columns='period',values='cell').reset_index().to_markdown(index=False))
    text += ['## Prespecified ways to expand N beyond thrust',
        'A union includes thrust plus IV-qualified entries from the named family. Same date/minute '
        'is counted once. Extra columns measure executions outside thrust. The all-entry union '
        'retains every thrust entry; first/spaced modes may choose a different entry.']
    union = unions[unions.period.eq('pooled')&unions['mode'].eq('all')].copy()
    text.append(markdown(union[['union','n','targets','rate','extra_n','extra_targets','extra_rate']]))
    text += ['## IV versus comparable sector prices',markdown(pd.read_csv(DATA/'matched_summary.csv')),
        'Same rising-sector count and at most ten basis points difference in median signed '
        'sector return; one-to-one maximum-cardinality matching without replacement. Within-half '
        'matching prevents cross-half pairing. This controls observed price features only.']
    text += ['## T+15 confirmation: new entry and fresh sixty-minute score',
        markdown(pd.read_csv(DATA/'checkpoint_summary.csv').query("period == 'pooled'")),
        'These are new entries at T+15, gated against VT again. They cannot improve the original '
        'entry retrospectively. The earlier pilot used a remaining 45-minute horizon; this run '
        'uses the requested fresh sixty minutes and is labeled accordingly.']
    text += ['## Every rule in the registry',registry.to_markdown(index=False),
        'MAD magnitude, alternate monthly-only/short-tenor constructions and constituent-level '
        'surface strategies are not tested here. They are recorded in IDEA_INVENTORY.md.']
    (OUT/'RESULT_TABLES.md').write_text('\n\n'.join(text)+'\n')
    # The entire registry remains in tables; the picture only compares predeclared principal rules.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes = plt.subplots(1,2,figsize=(14,5),layout='constrained')
    family = primary[primary.variant.eq('b06_breakout')&primary.rule.isin(KEY_RULES)&primary.state.eq('yes')]
    for row in family.itertuples():
        axes[0].scatter(row.n,row.rate,s=45)
        axes[0].annotate(row.rule.replace('original_','').replace('_6',''),(row.n,row.rate),fontsize=7,xytext=(4,3),textcoords='offset points')
    baseline = primary[primary.rule.eq('baseline')&primary.variant.eq('b06_breakout')].iloc[0]
    axes[0].scatter(baseline.n,baseline.rate,marker='*',s=180,color='black',label='Plain B06')
    axes[0].set_title('B06: IV selectivity versus opportunity count')
    for label,group in union.groupby(union['union'].str.split('__').str[0]):
        axes[1].scatter(group.n,group.rate,s=28,alpha=.7,label=label.removeprefix('thrust_plus_'))
    thrust = primary[primary.rule.eq('baseline')&primary.variant.eq('thrust')].iloc[0]
    axes[1].scatter(thrust.n,thrust.rate,marker='*',s=180,color='black',label='Thrust alone')
    axes[1].set_title('Adding IV-qualified entries to thrust')
    for ax in axes:
        ax.set_xlabel('Number of unique entries (N)')
        ax.set_ylabel('+5 before −10 within 60 minutes (%)')
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    fig.savefig(DATA/'accuracy_vs_n.png',dpi=180)
    plt.close(fig)
    print(json.dumps(dict(tables=str(OUT/'RESULT_TABLES.md'),figure=str(DATA/'accuracy_vs_n.png'))))


if __name__ == '__main__':
    main()

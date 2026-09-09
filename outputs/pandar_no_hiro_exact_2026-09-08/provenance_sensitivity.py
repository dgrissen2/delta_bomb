"""Descriptive source-family sensitivity; never changes the frozen exact selectors."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pandar_no_hiro_exact import block_bootstrap, write_json  # noqa: E402

OUT = Path(__file__).resolve().parent
sources = pd.read_csv(OUT/'selected_sources.csv')
paths = sources.drop_duplicates('path').set_index('path').source
trades = pd.read_csv(OUT/'policy_trades.csv', usecols=[
    'signal_source_path', 'ticker', 'signal_date', 'horizon', 'selector',
    'entry_status', 'exit_status', 'common_nonoverlap'])
trades['source_family'] = trades.signal_source_path.map(paths)
if trades.source_family.isna().any():
    raise ValueError('Unknown selected source provenance')
trades['explicit_winner_source'] = trades.source_family.eq('deustrader_wins_recreate_20260823')
paired = pd.read_csv(OUT/'paired_policy_results.csv')
families = trades[['ticker', 'signal_date', 'horizon', 'source_family',
                   'explicit_winner_source']].drop_duplicates()
paired = paired.merge(families, on=['ticker', 'signal_date', 'horizon'], validate='one_to_one')
rows = []
for sample_name, sample in {'all_signals': trades,
                            'common_nonoverlap': trades[trades.common_nonoverlap]}.items():
    for (family, selector, horizon), group in sample.groupby(['source_family','selector','horizon']):
        other = paired[paired.source_family.eq(family) & paired.horizon.eq(horizon)]
        if sample_name == 'common_nonoverlap':
            other = other[other.common_nonoverlap]
        rows.append(dict(sample=sample_name, source_family=family, selector=selector,
            horizon=horizon, cases=len(group), admitted=int(group.entry_status.eq('admitted').sum()),
            priced=int(group.exit_status.eq('priced').sum()),
            paired_observed=int(other.paired_observed.sum()),
            both_entered_priced=int((other.both_entered & other.paired_observed).sum())))
pd.DataFrame(rows).to_csv(OUT/'source_family_counts.csv', index=False)
sensitivity = []
for sample_name, sample in {'all_signals': paired,
                           'common_nonoverlap': paired[paired.common_nonoverlap]}.items():
    subset = sample[~sample.explicit_winner_source]
    for horizon in [2,4]:
        current = subset[subset.horizon.eq(horizon)]
        sensitivity.append(dict(sample=sample_name, horizon=horizon,
                                exclusion='explicit deustrader_wins_recreate source only',
                                **block_bootstrap(current)))
write_json(OUT/'exclude_explicit_winner_source_sensitivity.json', dict(
    interpretation='Descriptive post-result provenance sensitivity, unchanged frozen selections. '
                   'Remaining cache sources are not thereby unbiased or unseen.',
    comparisons=sensitivity))
print(json.dumps(dict(source_families=sorted(trades.source_family.unique()),
                     explicitly_winner_sourced_cases=int(
                         paired[paired.horizon.eq(4)].explicit_winner_source.sum())), indent=2))

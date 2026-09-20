"""Freeze B06 matching identities before any new outcome join."""
from __future__ import annotations

import numpy as np
import pandas as pd

from inputs import DATA, OUT, PRICE, digest, load, write_frame, write_json
from provenance import checked_execution, check_manifest

MATCH_RULES = ['original_accelerating_6','original_falling_6','midpoint_accelerating_6','paired_price_iv_6']
MATCH_SCOPES = ['global','within_half']


def main() -> None:
    checked_execution()
    check_manifest(DATA/'basket_freeze.json')
    matcher = load('full_price_matching',OUT.parent/'b06_iv_matched_price_2026-09-17/matching.py')
    events = pd.read_parquet(PRICE/'events_before_outcomes.parquet')
    base = events[events.always_above & events.cohort.ne('development_10') & events.variant.eq('b06_breakout')]
    base = base.drop_duplicates(['date','known_min']).merge(pd.read_parquet(DATA/'basket_features.parquet'),
        on=['date','known_min'],how='left',validate='one_to_one',indicator=True)
    if not base._merge.eq('both').all():
        raise ValueError('Missing basket context for a matching parent')
    base = base.drop(columns='_merge')
    base['episode_id'] = base.date+'_'+base.known_min.astype(str)
    base['parent_min'] = base.known_min
    base['half'] = base.date.str[:4]+'_H'+np.where(base.date.str[5:7].astype(int)<=6,'1','2')
    pairs_all,ledgers,groups_recorded = [],[],[]
    for rule in MATCH_RULES:
        for scope in MATCH_SCOPES:
            groups = [('all',base)] if scope == 'global' else list(base.groupby('half'))
            for name,frame in groups:
                features = frame[['episode_id','date','parent_min','price_coverage','rising_count',
                    'median_return_bps',rule]].rename(columns={rule:'iv_state'})
                pairs,ledger = matcher.match_pairs(features)
                groups_recorded.append(dict(rule=rule,scope=scope,stratum=name,pairs=len(pairs)))
                for value in [pairs,ledger]:
                    value['scope'],value['rule'],value['stratum'] = scope,rule,name
                pairs_all.append(pairs)
                ledgers.append(ledger)
    write_frame(DATA/'matched_pairs.parquet',pd.concat(pairs_all,ignore_index=True))
    write_frame(DATA/'matched_ledger.parquet',pd.concat(ledgers,ignore_index=True))
    write_json(DATA/'match_freeze.json',dict(before_outcome_join=True,groups=groups_recorded,inputs={str(p):digest(p) for p in
        [PRICE/'events_before_outcomes.parquet',DATA/'basket_features.parquet']},
        output_hashes={str(p):digest(p) for p in [DATA/'matched_pairs.parquet',DATA/'matched_ledger.parquet']}))


if __name__ == '__main__':
    main()

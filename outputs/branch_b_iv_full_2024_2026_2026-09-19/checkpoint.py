"""A T+15 confirmation requires its own entry, VT gate and sixty-minute outcome."""
from __future__ import annotations

import pandas as pd

from analyze import PERIODS, describe
from inputs import DATA, OUT, PRICE, base, digest, load, write_frame, write_json
from provenance import checked_execution, check_manifest, write_csv

gate = load('full_delayed_gate',OUT.parent/'branch_b_150d_rerun_2026-09-19/rerun_core.py').vt_flags


def admission(prices: pd.DataFrame, minute: int, vt: float) -> bool:
    """Apply the exact validated prefix-window VT gate at the new entry."""
    return gate(prices,minute,vt)['always_above']


def main() -> None:
    checked_execution()
    check_manifest(DATA/'basket_freeze.json')
    scorer = load('full_delayed_score',OUT.parent/'branch_b_stop10_2026-09-19/scoring.py')
    raw_events = pd.read_parquet(PRICE/'events_before_outcomes.parquet')
    parents = raw_events[raw_events.variant.eq('b06_breakout') & raw_events.always_above & raw_events.cohort.ne('development_10')]
    parents = parents.drop_duplicates(['date','known_min'])
    parents = parents[['date','known_min','cohort']].merge(pd.read_parquet(DATA/'basket_features.parquet'),
        on=['date','known_min'],how='left',validate='one_to_one',indicator=True)
    if not parents._merge.eq('both').all():
        raise ValueError('Missing basket context for a delayed parent')
    parents = parents.drop(columns='_merge')
    # Freeze eligibility and source identities before evaluating any delayed price path.
    write_frame(DATA/'checkpoint_features.parquet',parents)
    write_json(DATA/'checkpoint_feature_freeze.json',dict(sha256=digest(DATA/'checkpoint_features.parquet'),
        inputs={str(p):digest(p) for p in [PRICE/'events_before_outcomes.parquet',DATA/'basket_features.parquet']},
        entry_clock='parent_plus_15',outcome_window='fresh_60',old_study_remaining_45_not_replicated=True))
    days = pd.read_csv(PRICE/'selected_days.csv',float_precision='round_trip').set_index('date')
    scored = []
    for day,group in parents.groupby('date'):
        source = days.loc[day]
        prices = base.checked_read(source.source_path,source.source_sha256).set_index('min')
        vt = source.vol_trigger
        for parent in group.to_dict('records'):
            minute = int(parent['known_min'])+15
            above = admission(prices,minute,vt)
            result = scorer.score(prices,minute,10)
            # Independent sequential first-touch implementation.
            entry = float(prices.loc[minute,'open'])
            outcome = 'neither'
            for bar in prices.loc[minute:minute+59].itertuples():
                up,down = bar.high>=entry+5-1e-8,bar.low<=entry-10+1e-8
                if up or down:
                    outcome = 'ambiguous' if up and down else 'target_first' if up else 'adverse_first'
                    break
            assert result['outcome'] == outcome
            scored.append(dict(parent,date=day,parent_min=parent['known_min'],known_min=minute,
                               delayed_above_vt=above,**result))
    frame = pd.DataFrame(scored)
    frame['half'] = frame.date.str[:4]+'_H'+frame.date.str[5:7].astype(int).map(lambda m:'1' if m<=6 else '2')
    write_frame(DATA/'checkpoint_outcomes.parquet',frame)
    rows = []
    for period in ['pooled']+PERIODS:
        pool = frame if period == 'pooled' else frame[frame.half.eq(period)]
        eligible = pool[pool.delayed_above_vt]
        candidates = {'all_delayed_b06':eligible,
            'pre_paired_yes':eligible[eligible.paired_price_iv_6.eq('yes')],
            'pre_and_post_paired_yes':eligible[eligible.paired_price_iv_6.eq('yes')&eligible.post15_paired_6.eq('yes')],
            'pre_yes_post_no':eligible[eligible.paired_price_iv_6.eq('yes')&eligible.post15_paired_6.eq('no')],
            'pre_yes_post_unknown':eligible[eligible.paired_price_iv_6.eq('yes')&eligible.post15_paired_6.eq('unknown')]}
        for rule,subset in candidates.items():
            rows.append(dict(period=period,rule=rule,vt_excluded_parents=len(pool)-len(eligible),**describe(subset)))
    write_csv(DATA/'checkpoint_summary.csv',pd.DataFrame(rows))
    write_json(DATA/'checkpoint_complete.json',dict(output_hashes={str(DATA/p):digest(DATA/p) for p in
        ['checkpoint_features.parquet','checkpoint_outcomes.parquet','checkpoint_summary.csv']}))


if __name__ == '__main__':
    main()

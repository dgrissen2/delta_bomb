"""Fixed eleven-sector context registry; outcomes are deliberately absent."""
from __future__ import annotations

import numpy as np
import pandas as pd

from core import EPS, classify, conjunct
from features import DESCRIPTORS, POLICIES
from inputs import DATA, digest, write_frame, write_json
from weights import validation_paths
from provenance import checked_execution

KEYS = ['date','known_min']


def count_states(frame: pd.DataFrame, yes: np.ndarray, known: np.ndarray,
                 threshold: int) -> pd.Series:
    votes = frame[KEYS].assign(yes=np.asarray(yes)&np.asarray(known),missing=~np.asarray(known))
    counts = votes.groupby(KEYS).agg(yes=('yes','sum'),missing=('missing','sum'),n=('yes','size'))
    if not counts.n.eq(11).all():
        raise ValueError('Every context needs all eleven sector rows')
    values = [classify(int(yes),int(missing),threshold) for yes,missing in zip(counts.yes,counts.missing)]
    return pd.Series(values,index=counts.index)


def paired_votes(price: np.ndarray, iv: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    p_ok,iv_ok = np.isfinite(price),np.isfinite(iv)
    good = p_ok & iv_ok & (price>EPS) & (iv < -EPS)
    false = (p_ok & (price<=EPS)) | (iv_ok & (iv>=-EPS))
    return good,good|false


def build(frame: pd.DataFrame, weights: pd.DataFrame | None = None) -> tuple[pd.DataFrame,pd.DataFrame]:
    if frame.duplicated(KEYS+['symbol']).any():
        raise ValueError('Duplicate sector identity')
    result = frame.groupby(KEYS).size().to_frame('sector_rows')
    registry = []

    def add(name: str, yes: np.ndarray, known: np.ndarray, threshold: int,
            category: str, label: str, union: bool = False) -> None:
        result[name] = count_states(frame,yes,known,threshold)
        registry.append(dict(rule=name,category=category,label=label,threshold=threshold,union=union))

    for policy in POLICIES:
        valid = frame[policy+'_available'].to_numpy(dtype=bool)
        b2,a = frame[policy+'_b2'].to_numpy(),frame[policy+'_acceleration'].to_numpy()
        for name,yes in [('falling',b2 < -EPS),('accelerating',(b2 < -EPS)&(a < -EPS))]:
            for k in [6,8]:
                add(f'{policy}_{name}_{k}',yes,valid,k,'primary',f'{policy}: {name}, ≥{k} sectors',True)
        if weights is not None:
            z = frame[KEYS+['symbol']].merge(weights[['date','symbol','equity_weight']],
                on=['date','symbol'],how='left',validate='many_to_one')
            # A missing dated weight snapshot makes the weighted rule unknown in full.
            for name,yes in [('falling',b2 < -EPS),('accelerating',(b2 < -EPS)&(a < -EPS))]:
                z['yes_weight'] = z.equity_weight.where(yes&valid,0)
                z['missing_weight'] = z.equity_weight.where(~valid,0)
                counts = z.groupby(KEYS).agg(yes=('yes_weight','sum'),missing=('missing_weight','sum'),
                    total=('equity_weight','sum'),coverage=('equity_weight','count'))
                complete = counts.coverage.eq(11)&np.isclose(counts.total,1)
                name = f'{policy}_weighted_{name}'
                result[name] = pd.Series(np.where(~complete,'unknown',np.where(counts.yes>.5+EPS,'yes',
                    np.where(counts.yes+counts.missing<=.5+EPS,'no','unknown'))),index=counts.index)
                registry.append(dict(rule=name,category='weighted',label=name,threshold=.5,union=False))

    for desc in DESCRIPTORS:
        valid = frame[desc+'_available'].to_numpy(dtype=bool)
        slope = frame[desc+'_full_slope'].to_numpy()
        b2,a = frame[desc+'_b2'].to_numpy(),frame[desc+'_acceleration'].to_numpy()
        conditions = {'full_falling':slope < -EPS,'full_rising':slope > EPS,
            'second_half_falling':b2 < -EPS,'second_half_rising':b2 > EPS,
            'falling_accelerating':(b2 < -EPS)&(a < -EPS),
            'falling_slowing':(b2 < -EPS)&(a > EPS),
            'rising_accelerating':(b2 > EPS)&(a > EPS),
            'rising_slowing':(b2 > EPS)&(a < -EPS)}
        for name,yes in conditions.items():
            for k in [6,8]:
                add(f'{desc}_{name}_{k}',yes,valid,k,'surface_diagnostic',f'{desc}: {name}, ≥{k}')
    valid = frame.atm_available.to_numpy(dtype=bool)
    resolved = frame.atm_b2_high.to_numpy() < -EPS
    for name,yes in [('falling',resolved),('accelerating',resolved&(frame.atm_acceleration_high.to_numpy() < -EPS))]:
        for k in [6,8]:
            add(f'quote_resolved_{name}_{k}',yes,valid,k,'quote_diagnostic',f'Quote resolved {name}, ≥{k}')

    price = frame.price_return_bps.to_numpy()
    iv = frame.original_endpoint_change.to_numpy()
    yes,known = paired_votes(price,iv)
    for k in [6,8]:
        add(f'paired_price_iv_{k}',yes,known,k,'primary',f'Price rising AND IV endpoint falling, ≥{k}',True)
        add(f'price_only_{k}',price>EPS,np.isfinite(price),k,'price_control',f'Price rising, ≥{k}')
    yes,known = paired_votes(frame.post_price_return_bps.to_numpy(),frame.post_iv_change.to_numpy())
    add('post15_paired_6',yes,known,6,'delayed_only','Paired price/IV at T+15; new entry required')
    change = frame.atm_breakout_slope.to_numpy()
    add('breakout5_falling_6',change < -EPS,np.isfinite(change),6,'confirmation','Breakout five-minute IV falling')
    result['original_falling_and_breakout5'] = [conjunct(a,b) for a,b in
        zip(result.original_falling_6,result.breakout5_falling_6)]
    registry.append(dict(rule='original_falling_and_breakout5',category='confirmation',
                         label='Reference falling plus contemporaneous breakout confirmation',threshold=6,union=False))
    result['price_coverage'] = frame.assign(v=np.isfinite(price)).groupby(KEYS).v.sum()
    result['rising_count'] = frame.assign(v=price>EPS).groupby(KEYS).v.sum()
    result['median_return_bps'] = frame.groupby(KEYS).price_return_bps.median()
    result['falling_count'] = frame.assign(v=valid&(frame.atm_b2.to_numpy() < -EPS)).groupby(KEYS).v.sum()
    result['iv_coverage'] = frame.assign(v=valid).groupby(KEYS).v.sum()
    one,two = frame.price_first_bps.to_numpy(),frame.price_second_bps.to_numpy()
    known = np.isfinite(one)&np.isfinite(two)
    votes = frame[KEYS].assign(first=known&(one>EPS),second=known&(two>EPS),missing=~known)
    counts = votes.groupby(KEYS)[['first','second','missing']].sum()
    difference = counts.second-counts['first']
    result['recruitment'] = np.where(difference-counts.missing>0,'improving',
        np.where(difference+counts.missing<0,'deteriorating',
        np.where(counts.missing.eq(0)&difference.eq(0),'unchanged','unknown')))
    result['current_rising_count'] = counts.second
    result['previous_rising_count'] = counts['first']
    return result.reset_index(),pd.DataFrame(registry)


def main() -> None:
    checked_execution()
    frame = pd.read_parquet(DATA/'sector_features.parquet')
    weights_path,_ = validation_paths()
    weights = pd.read_parquet(weights_path)
    states,registry = build(frame,weights)
    write_frame(DATA/'basket_features.parquet',states)
    write_frame(DATA/'rule_registry.parquet',registry)
    write_json(DATA/'basket_freeze.json',dict(inputs={str(p):digest(p) for p in
        [DATA/'sector_features.parquet',weights_path]},
        output_hashes={str(p):digest(p) for p in [DATA/'basket_features.parquet',DATA/'rule_registry.parquet']}))


if __name__ == '__main__':
    main()

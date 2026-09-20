"""Outcome-blind minute measurements and fixed-window sector features."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path

import numpy as np
import pandas as pd

from core import measure
from inputs import (DATA, PRICE, SYMBOLS, base, balanced, digest, rules, surface,
                    write_frame, write_json)

DESCRIPTORS = ['atm','put_richness','call_richness','risk_reversal']
POLICIES = ['original','midpoint','guarded_100','guarded_50','balanced']


def derive(path: Path) -> dict:
    """Rebuild full ETF coordinates and all four quote-policy series from native inputs."""
    record = json.loads(path.read_text())
    day, symbol = record['date'],record['symbol']
    dest = DATA/'derived'/symbol
    meta_path = dest/'receipts'/f'{day}.json'
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta['record_sha256'] != digest(path):
            raise ValueError(f'Changed input record {path}')
        for name,sha in meta['output_hashes'].items():
            if digest(Path(name)) != sha:
                raise ValueError(f'Changed derived output {name}')
        return meta
    grid = base.minute_grid(day)
    minutes = grid.hour*60+grid.minute
    source = pd.DataFrame({'date':day,'symbol':symbol,'minute':minutes,'spot':np.nan,
                           'original':np.nan,'midpoint':np.nan,'guarded_100':np.nan,
                           'guarded_50':np.nan,'guard100':False})
    for desc in DESCRIPTORS:
        for suffix in ['','_low','_high']:
            source[desc+suffix] = np.nan
    if record['status'] == 'captured':
        raw = {m:[] for m in base.METHODS}
        for item in record['raw_files']:
            raw[item['method']].append(base.checked_read(item['path'],item['sha256']))
        iv,greeks = [pd.concat(raw[m],ignore_index=True) for m in base.METHODS]
        prepared = surface._prepare(iv,greeks)
        if not prepared.session_date.eq(day).all() or not prepared.symbol.eq(symbol).all():
            raise ValueError('Native source date/symbol mismatch')
        prepared = prepared[prepared.timestamp.isin(grid)].copy()
        qualified = rules.add_quality(prepared)
        strict,_ = rules.make_surface(qualified,'valid',grid)
        midpoint,_ = rules.make_surface(qualified,'mid_valid',grid)
        full = surface.build_surface(iv,greeks).set_index('timestamp').reindex(grid)
        np.testing.assert_allclose(strict.iv,full.atm,atol=1e-10,rtol=1e-12,equal_nan=True)
        source['original'] = strict.iv.to_numpy()
        source['midpoint'] = midpoint.iv.to_numpy()
        source['guarded_100'] = midpoint.iv.where(midpoint.guard100).to_numpy()
        source['guarded_50'] = midpoint.iv.where(midpoint.guard50).to_numpy()
        source['guard100'] = midpoint.guard100.to_numpy(dtype=bool)
        for col in ['spot']+[d+s for d in DESCRIPTORS for s in ['','_low','_high']]:
            source[col] = full[col].to_numpy()
    windows = []
    for end in minutes[29:]:
        measured,chosen = balanced.measure_window(np.asarray(minutes),source.original.to_numpy(),
            source.midpoint.to_numpy(),source.guard100.to_numpy(),end=int(end),radius=2)
        measured.update(date=day,symbol=symbol,**base.summarize_window(chosen))
        windows.append(measured)
    sp,wp = dest/'minutes'/f'{day}.parquet',dest/'windows'/f'{day}.parquet'
    write_frame(sp,source)
    write_frame(wp,pd.DataFrame(windows))
    meta = dict(date=day,symbol=symbol,status=record['status'],record_sha256=digest(path),
                native_hashes={r['path']:r['sha256'] for r in record['raw_files']},
                output_hashes={str(p):digest(p) for p in [sp,wp]},
                strict_minutes=int(source.original.notna().sum()),
                recovered_minutes=int(source.midpoint.notna().sum()))
    write_json(meta_path,meta)
    return meta


def derive_available(workers: int) -> None:
    paths = sorted((DATA/'days').glob('*/*.json'))
    pending = [p for p in paths if not (DATA/'derived'/p.parent.name/'receipts'/p.name).exists()]
    print(json.dumps(dict(phase='derive_plan',pending=len(pending),all_records=len(paths))),flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(derive,p):p for p in pending}
        for i,future in enumerate(as_completed(futures),1):
            record = future.result()
            if i%25 == 0 or i == len(futures):
                print(json.dumps(dict(phase='derived',completed=i,total=len(futures),
                                     date=record['date'],symbol=record['symbol'])),flush=True)


def linear_range(frame: pd.DataFrame, desc: str, weights: np.ndarray) -> tuple[float,float]:
    low,high = frame[desc+'_low'].to_numpy(),frame[desc+'_high'].to_numpy()
    if not (np.isfinite(low).all() and np.isfinite(high).all()):
        return np.nan,np.nan
    return (float(np.maximum(weights,0)@low+np.minimum(weights,0)@high),
            float(np.maximum(weights,0)@high+np.minimum(weights,0)@low))


def sector_features(source: pd.DataFrame, windows: pd.DataFrame, entries: list[int]) -> list[dict]:
    """Never read outcomes. Original and recovered series retain identical clock windows."""
    indexed = source.set_index('minute')
    balanced_windows = windows.set_index('end_min')
    rows = []
    halfw = (np.arange(15)-7)/280
    for entry in entries:
        ref = indexed.reindex(range(entry-35,entry-5))
        spot = ref.spot.to_numpy(dtype=float)
        spot_ok = bool(np.isfinite(spot).all() and (spot>0).all())
        row = dict(date=source.date.iloc[0],symbol=source.symbol.iloc[0],known_min=entry,
                   price_available=spot_ok,price_return_bps=np.nan,price_first_bps=np.nan,
                   price_second_bps=np.nan)
        if spot_ok:
            row.update(price_return_bps=float(10000*(spot[-1]/spot[0]-1)),
                       price_first_bps=float(10000*(spot[14]/spot[0]-1)),
                       price_second_bps=float(10000*(spot[-1]/spot[15]-1)))
        for policy in POLICIES[:-1]:
            row.update({policy+'_'+k:v for k,v in measure(indexed[policy],entry).items()})
        if entry-6 in balanced_windows.index:
            z = balanced_windows.loc[entry-6]
            row.update({f'balanced_{k}':z[k] for k in ['available','b1','b2','acceleration']})
            row['balanced_unique_sources'] = int(z.unique_sources)
        else:
            row.update(balanced_available=False,balanced_b1=np.nan,balanced_b2=np.nan,
                       balanced_acceleration=np.nan,balanced_unique_sources=0)
        for desc in DESCRIPTORS:
            row.update({desc+'_'+k:v for k,v in measure(indexed[desc],entry).items()})
            for name,w in [('b2',np.r_[np.zeros(15),halfw]),
                           ('acceleration',np.r_[-halfw,halfw]/15)]:
                low,high = linear_range(ref,desc,w)
                row[f'{desc}_{name}_low'],row[f'{desc}_{name}_high'] = low,high
            breakout = indexed[desc].reindex(range(entry-5,entry)).to_numpy(dtype=float)
            row[f'{desc}_breakout_slope'] = float((np.arange(5)-2)@breakout/10) if np.isfinite(breakout).all() else np.nan
        # Checkpoint is recorded separately; it cannot affect original-entry predicates.
        post = indexed.reindex(range(entry,entry+15))
        post_spot,post_iv = post.spot.to_numpy(),post.original.to_numpy()
        row['post_price_return_bps'] = (float(10000*(post_spot[-1]/post_spot[0]-1))
            if np.isfinite(post_spot).all() and (post_spot>0).all() else np.nan)
        row['post_iv_change'] = float(post_iv[-1]-post_iv[0]) if np.isfinite(post_iv).all() else np.nan
        rows.append(row)
    return rows


def event_day(task: tuple[str,list[int]]) -> list[dict]:
    day,entries = task
    records = []
    for symbol in SYMBOLS:
        basepath = DATA/'derived'/symbol
        sp,wp = basepath/'minutes'/f'{day}.parquet',basepath/'windows'/f'{day}.parquet'
        if not sp.exists() or not wp.exists():
            raise ValueError(f'Unfinished collection/derivation {day} {symbol}')
        records.extend(sector_features(pd.read_parquet(sp),pd.read_parquet(wp),entries))
    return records


def build_events() -> None:
    from provenance import checked_execution
    checked_execution()
    keys = pd.read_parquet(PRICE/'events_before_outcomes.parquet',columns=['date','known_min'])
    keys = keys.drop_duplicates().sort_values(['date','known_min'])
    tasks = [(day,group.known_min.tolist()) for day,group in keys.groupby('date',sort=True)]
    records = []
    with ProcessPoolExecutor(max_workers=3) as pool:
        for (day,_),rows in zip(tasks,pool.map(event_day,tasks)):
            records.extend(rows)
            print(json.dumps(dict(phase='event_features',date=day,rows=len(records))),flush=True)
    result = pd.DataFrame(records)
    assert not result.duplicated(['date','known_min','symbol']).any()
    write_frame(DATA/'sector_features.parquet',result)
    write_json(DATA/'feature_freeze.json',dict(rows=len(result),
        sha256=digest(DATA/'sector_features.parquet'),
        source_hashes={str(p):digest(p) for p in (DATA/'derived').glob('*/receipts/*.json')},
        code_sha256=digest(Path(__file__))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase',choices=['derive','events'])
    parser.add_argument('--workers',type=int,default=3)
    args = parser.parse_args()
    derive_available(args.workers) if args.phase == 'derive' else build_events()

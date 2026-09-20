"""Independent rational-CDF validation of every corrected MAD baseline."""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import (DATA, balanced, date_plan, digest, magnitude, minute_grid, write_json)

EXACT = DATA/'calibration_exact'


def assert_lower_median(values: np.ndarray, dates: pd.Series, candidate: float) -> None:
    """Verify the defining CDF inequalities, independently with Fraction sums."""
    if not np.isfinite(values).all() or not np.isfinite(candidate) or not np.any(values == candidate):
        raise AssertionError('Median must be an observed finite value')
    codes, labels = pd.factorize(dates,sort=True)
    counts = np.bincount(codes)
    before = np.bincount(codes,weights=(values < candidate).astype(int),minlength=len(labels))
    through = np.bincount(codes,weights=(values <= candidate).astype(int),minlength=len(labels))
    below_mass = sum((Fraction(int(n),int(d)) for n,d in zip(before,counts,strict=True)),Fraction(0))
    through_mass = sum((Fraction(int(n),int(d)) for n,d in zip(through,counts,strict=True)),Fraction(0))
    half = Fraction(len(labels),2)
    if not below_mass < half <= through_mass:
        raise AssertionError(f'Not the lower weighted median: {below_mass} < {half} <= {through_mass}')


def verify_symbol(symbol: str) -> dict:
    base, exact = DATA/'derived'/symbol, EXACT/symbol
    summary = json.loads((exact/'summary.json').read_text())
    for path,sha in summary['output_hashes'].items():
        assert digest(Path(path)) == sha,path
    history = pd.read_parquet(base/'all_windows.parquet')
    baselines = pd.read_parquet(exact/'block_baselines.parquet')
    scores = pd.read_parquet(exact/'scored_windows.parquet')
    sessions,targets = date_plan()
    assert len(baselines) == 5*len(targets) and not baselines.duplicated(['date','block']).any()
    assert len(history) == sum(len(minute_grid(d))-29 for d in sessions)
    assert len(scores) == sum(len(minute_grid(d))-29 for d in targets)
    assert set(history.date) == set(sessions) and set(scores.date) == set(targets)
    assert not history.duplicated(['date','end_min']).any()
    assert history.symbol.eq(symbol).all() and scores.symbol.eq(symbol).all()
    assert np.isfinite(history.loc[history.available,'acceleration']).all()
    for day, group in history.groupby('date'):
        grid=minute_grid(day)
        np.testing.assert_array_equal(group.end_min,grid.hour.to_numpy()[29:]*60+grid.minute.to_numpy()[29:])
    rational_replays = 0
    for day,group in baselines.groupby('date'):
        prior = magnitude.prior_sessions(sessions,day)
        previous = history[history.date.isin(prior) & history.available]
        assert len(prior) == 60 and max(prior) < day
        for row in group.to_dict('records'):
            sample = previous[previous.block.eq(row['block'])]
            counts = sample.groupby('date').size()
            assert json.loads(row['windows_by_date']) == counts.to_dict()
            assert json.loads(row['source_dates']) == counts.index.tolist()
            assert row['history_days'] == len(counts) and row['history_windows'] == len(sample)
            assert row['lookback_start'] == prior[0] and row['lookback_end'] == prior[-1]
            if len(counts) < 10:
                assert row['status'] == 'insufficient_history' and np.isnan(row['scale'])
                continue
            values = sample.acceleration.to_numpy()
            assert_lower_median(values,sample.date,row['median'])
            assert_lower_median(abs(values-row['median']),sample.date,row['mad'])
            assert row['scale'] == 1.4826*row['mad']
            assert row['status'] == ('ok' if row['scale'] > 1e-12 else 'zero_or_tiny_scale')
            rational_replays += 1
    joined = scores.merge(baselines,on=['symbol','date','block'],suffixes=('', '_baseline'),validate='many_to_one')
    for field in ['mad','scale']:
        np.testing.assert_allclose(joined[field],joined[field+'_baseline'],rtol=0,atol=0,equal_nan=True)
    valid = joined.available & joined.status_baseline.eq('ok')
    assert joined.signed_score.notna().eq(valid).all()
    assert np.isfinite(joined.loc[valid,'signed_score']).all()
    np.testing.assert_allclose(joined.loc[valid,'signed_score'],-joined.loc[valid,'acceleration']/joined.loc[valid,'scale'],rtol=0,atol=0)
    assert joined.downward_magnitude.notna().eq(valid & joined.b2.lt(-1e-12) & joined.acceleration.lt(-1e-12)).all()
    prefix_checks = 0
    for day in ['2023-10-05','2023-11-24','2024-01-02','2024-07-03','2025-01-02','2025-07-03','2025-12-31','2026-08-06','2026-09-18']:
        source = pd.read_parquet(base/'sources'/f'{day}.parquet')
        for end in (599,630,719,int(source.minute.max())):
            results = []
            for frame in (source,source[source.minute.le(end)]):
                row,mapping = balanced.measure_window(frame.minute.to_numpy(),frame.strict_iv.to_numpy(),
                    frame.recovered_iv.to_numpy(),frame.guard100.to_numpy(),end=end,radius=2)
                results.append((row,pd.DataFrame(mapping)))
            pd.testing.assert_series_equal(pd.Series(results[0][0]),pd.Series(results[1][0]))
            pd.testing.assert_frame_equal(results[0][1],results[1][1])
            prefix_checks += 1
    result = {'symbol':symbol,'calendar_windows_verified':len(history),'scored_windows_verified':len(scores),
              'baseline_prior_date_counts_verified':len(baselines),'exact_rational_median_and_mad_replays':rational_replays,
              'source_prefix_checks':prefix_checks,'independent_ols_max_error':summary['independent_ols_max_error'],
              'source_code_sha256':digest(Path(__file__))}
    write_json(exact/'verification_final.json',result)
    print(json.dumps(result,indent=2),flush=True)
    return result

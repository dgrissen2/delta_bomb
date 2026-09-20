"""Frozen nearby-first XLRE baseline, using unique actual-time observations."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
PILOT = OUT.parent / 'xlre_iv_magnitude_5d_2026-09-19'
DATA = Path('/Users/dgrissen/Dev/central_trade_data/thetadata/xlre_iv_magnitude_5d_2026-09-19-v1')


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit_half(times: np.ndarray, iv: np.ndarray) -> float:
    """OLS slope in IV percentage points per elapsed minute."""
    if len(times) < 2 or len(np.unique(times)) < 2:
        raise ValueError('Two distinct timestamps required')
    if not np.isfinite(times).all() or not np.isfinite(iv).all() or not (iv > 0).all():
        raise ValueError('Finite timestamps and positive finite IV required')
    centered = times - times.mean()
    return float(centered @ (iv - iv.mean()) / (centered @ centered))


def fit_selected(times: np.ndarray, iv: np.ndarray, start: int) -> dict:
    """Deduplicate source minutes before assigning actual first/second halves."""
    times, iv = np.asarray(times), np.asarray(iv)
    if times.shape != iv.shape or times.ndim != 1:
        raise ValueError('Aligned one-dimensional input required')
    unique, indices = np.unique(times, return_index=True)
    for stamp, index in zip(unique, indices, strict=True):
        if not np.all(iv[times == stamp] == iv[index]):
            raise ValueError(f'Conflicting IV at source timestamp {stamp}')
    values = iv[indices]
    if ((unique < start) | (unique > start + 29)).any():
        raise ValueError('Source outside fixed thirty-minute window')
    first = unique < start + 15
    result = {'n_first': int(first.sum()), 'n_second': int((~first).sum()),
              'span_first': int(np.ptp(unique[first])) if first.any() else 0,
              'span_second': int(np.ptp(unique[~first])) if (~first).any() else 0,
              'b1': np.nan, 'b2': np.nan, 'acceleration': np.nan, 'status': 'unfit_half'}
    if min(result['n_first'], result['n_second']) < 2:
        return result
    b1, b2 = fit_half(unique[first], values[first]), fit_half(unique[~first], values[~first])
    result.update(b1=b1, b2=b2, acceleration=(b2-b1)/15, status='ok')
    return result


def measure_window(minutes: np.ndarray, strict_iv: np.ndarray, recovered_iv: np.ndarray,
                   guard_mask: np.ndarray, *, end: int, radius: int) -> tuple[dict, list[dict]]:
    """Select within the fixed window, preserving strict-first priority and cutoff."""
    if radius not in (2, 3) or len(set(minutes)) != len(minutes):
        raise ValueError('Radius 2 or 3 and unique input minutes required')
    start = end - 29
    index = {int(t): i for i, t in enumerate(minutes)}
    strict = np.isfinite(strict_iv) & (strict_iv > 0)
    eligible = strict & (minutes >= start) & (minutes <= end)
    sources = []
    for target in range(start, end + 1):
        if target not in index:
            raise ValueError('All requested minute slots must exist')
        i = index[target]
        chosen, method = None, 'unavailable'
        if strict[i]:
            chosen, method = target, 'strict_exact'
        else:
            candidates = minutes[eligible & (np.abs(minutes-target) <= radius)
                                 & ((minutes-570)//60 == (target-570)//60)]
            if len(candidates):
                chosen = int(min(candidates, key=lambda t: (abs(t-target), t)))
                method = 'strict_nearby'
            elif guard_mask[i] and np.isfinite(recovered_iv[i]) and recovered_iv[i] > 0:
                chosen, method = target, 'recovered_exact'
        value = (recovered_iv[index[chosen]] if method == 'recovered_exact'
                 else strict_iv[index[chosen]]) if chosen is not None else np.nan
        sources.append({'target_minute': target, 'source_minute': chosen,
                        'method': method, 'iv': float(value)})
    selected = [s for s in sources if s['source_minute'] is not None]
    result = {'start_min': start, 'end_min': end, 'block': (end-570)//60,
              'available': False, 'status': 'missing_source', 'b1': np.nan, 'b2': np.nan,
              'acceleration': np.nan, 'supported_slots': len(selected),
              'unique_sources': len({s['source_minute'] for s in selected}),
              'fallback_slots': sum(s['method'] == 'recovered_exact' for s in selected),
              'neighbor_slots': sum(s['method'] == 'strict_nearby' for s in selected),
              'n_first': 0, 'n_second': 0, 'span_first': 0, 'span_second': 0}
    if len(selected) == 30:
        fit = fit_selected(np.array([s['source_minute'] for s in selected]),
                           np.array([s['iv'] for s in selected]), start)
        result.update(fit)
        result['available'] = fit['status'] == 'ok'
    return result, sources


def rebuild_sources(manifest: dict) -> pd.DataFrame:
    audit = load_module('source_audit', PILOT / 'coverage_diagnosis/audit.py')
    surface = load_module('frozen_surface', audit.SURFACE)
    rules = load_module('frozen_rules', OUT.parent / 'b06_iv_expansion_150d_2026-09-19/iv_rules.py')
    assert rules.check_guard_boundaries() == 10
    old_masks = pd.read_csv(PILOT / 'nearby_first_guarded_coverage/source_guards.csv')
    frames = []
    for record in manifest['days']:
        day = record['date']
        grid = pd.date_range(f'{day} 09:30', periods=300, freq='min', tz='America/New_York')
        frame = pd.DataFrame({'date': day, 'minute': np.arange(570, 870),
                              'strict_iv': np.nan, 'recovered_iv': np.nan, 'guard100': False,
                              'expiry_eligible': record['status'] == 'ok'})
        if record['status'] == 'ok':
            raw = {'implied_volatility': [], 'first_order': []}
            for item in record['raw_files']:
                kind = 'implied_volatility' if 'implied_volatility' in item['path'] else 'first_order'
                raw[kind].append(audit.checked_read(item['path'], item['sha256']))
            prepared = surface._prepare(pd.concat(raw['implied_volatility'], ignore_index=True),
                                        pd.concat(raw['first_order'], ignore_index=True))
            qualified = rules.add_quality(prepared)
            strict, _ = rules.make_surface(qualified, 'valid', grid)
            recovered, _ = rules.make_surface(qualified, 'mid_valid', grid)
            frozen = audit.checked_read(record['surface_path'], record['surface_sha256'])
            np.testing.assert_allclose(strict.iv, frozen.atm, atol=1e-10, rtol=1e-12, equal_nan=True)
            assert qualified.loc[qualified.mid_valid, 'bid'].gt(0).all()
            assert qualified.loc[qualified.mid_valid, 'underlying_price'].gt(0).all()
            frame['strict_iv'] = strict.iv.to_numpy()
            frame['recovered_iv'] = recovered.iv.to_numpy()
            frame['guard100'] = recovered.guard100.to_numpy(dtype=bool)
        previous = old_masks[old_masks.date.eq(day)]
        np.testing.assert_array_equal(frame.strict_iv.notna(), previous.strict)
        np.testing.assert_array_equal(frame.guard100, previous.guard100)
        frames.append(frame)
        print('rebuilt', day, flush=True)
    result = pd.concat(frames, ignore_index=True)
    result.to_parquet(OUT / 'source_minutes.parquet', index=False)
    return result


def main() -> None:
    original = json.loads((PILOT / 'verification_manifest.json').read_text())['artifact_hashes']
    assert all(digest(Path(p)) == sha for p, sha in original.items())
    manifest = json.loads((DATA / 'manifest.json').read_text())
    magnitude = load_module('frozen_magnitude', PILOT / 'magnitude.py')
    sources = rebuild_sources(manifest)
    records, mappings = [], []
    exact_replays = 0
    maximum_ols_error = 0.
    for day, group in sources.groupby('date', sort=True):
        group = group.sort_values('minute')
        minutes = group.minute.to_numpy()
        strict_iv, recovered_iv = group.strict_iv.to_numpy(), group.recovered_iv.to_numpy()
        for radius in (2, 3):
            for end in range(599, 870):
                row, selected = measure_window(minutes, strict_iv, recovered_iv,
                                                group.guard100.to_numpy(), end=end, radius=radius)
                row.update(date=day, radius=radius, expiry_eligible=bool(group.expiry_eligible.iloc[0]))
                unique = {s['source_minute']: s['iv'] for s in selected if s['source_minute'] is not None}
                row['source_minutes'] = json.dumps(sorted(unique))
                if row['available']:
                    t = np.array(sorted(unique))
                    y = np.array([unique[v] for v in t])
                    for half, name in [(t < end-14, 'b1'), (t >= end-14, 'b2')]:
                        independently = np.polyfit(t[half]-t[half][0], y[half], 1)[0]
                        maximum_ols_error = max(maximum_ols_error, abs(independently-row[name]))
                    if row['neighbor_slots'] == row['fallback_slots'] == 0:
                        np.testing.assert_allclose([row['b1'], row['b2']],
                            [magnitude.HALF @ y[:15], magnitude.HALF @ y[15:]], atol=1e-12)
                        exact_replays += 1
                records.append(row)
                if day in manifest['pilot']:
                    mappings.extend({'date': day, 'radius': radius, 'end_min': end, **s} for s in selected)
        print('measured', day, flush=True)
    history = pd.DataFrame(records)
    assert len(history) == 65*271*2 and maximum_ols_error < 1e-12
    history.to_parquet(OUT / 'all_windows.parquet', index=False)
    pd.DataFrame(mappings).to_parquet(OUT / 'pilot_source_mapping.parquet', index=False)
    baselines, scored = [], []
    sessions = [r['date'] for r in manifest['days']]
    for radius in (2, 3):
        variant = history[history.radius.eq(radius)]
        for day in manifest['pilot']:
            prior = magnitude.prior_sessions(sessions, day)
            for block in range(5):
                stats = magnitude.robust_baseline(variant, prior, block)
                baselines.append({'date': day, 'radius': radius, 'block': block,
                                  'block_label': magnitude.block_name(block),
                                  'lookback_start': prior[0], 'lookback_end': prior[-1], **stats})
                for row in variant[variant.date.eq(day) & variant.block.eq(block)].to_dict('records'):
                    score = magnitude.score_window(row['b2'], row['acceleration'], stats['scale'])
                    scored.append({**row, 'history_days': stats['history_days'], 'scale': stats['scale'],
                                   **score, 'score_status': 'missing_current_window' if not row['available']
                                   else stats['status']})
    baseline = pd.DataFrame([{**b, 'source_dates': json.dumps(b['source_dates']),
                             'windows_by_date': json.dumps(b['windows_by_date'])} for b in baselines])
    baseline.to_csv(OUT / 'block_baselines.csv', index=False)
    pilot = pd.DataFrame(scored)
    pilot.to_csv(OUT / 'pilot_windows.csv', index=False)
    summary = pilot.groupby(['radius', 'date']).agg(total=('available', 'size'),
        measured=('available', 'sum'), scored=('signed_score', 'count'),
        downward=('downward_magnitude', 'count'), min_unique=('unique_sources', 'min'))
    summary.to_csv(OUT / 'pilot_summary.csv')
    common = pilot[pilot.radius.eq(2)].merge(pilot[pilot.radius.eq(3)],
        on=['date', 'end_min'], suffixes=('_2', '_3'), validate='one_to_one')
    common = common[common.score_status_2.eq('ok') & common.score_status_3.eq('ok')].copy()
    common['absolute_score_difference'] = abs(common.signed_score_3-common.signed_score_2)
    common[['date', 'end_min', 'signed_score_2', 'signed_score_3',
            'absolute_score_difference']].to_csv(OUT / 'sensitivity_common.csv', index=False)
    scales = baseline[baseline.radius.eq(2)].merge(baseline[baseline.radius.eq(3)],
             on=['date', 'block', 'block_label'], suffixes=('_2', '_3'), validate='one_to_one')
    scales['scale_ratio_3_to_2'] = scales.scale_3/scales.scale_2
    scales.to_csv(OUT / 'sensitivity_scales.csv', index=False)
    old = pd.read_csv(PILOT / 'neighbor_radius_waterfall/window_coverage.csv')
    old = old[old.policy.eq('guard100')]
    compare = history.merge(old[['date', 'end_min', 'radius', 'available']],
        on=['date', 'end_min', 'radius'], suffixes=('', '_old'), validate='one_to_one')
    assert not (compare.available & ~compare.available_old).any()
    losses = compare[compare.available_old & ~compare.available]
    losses.to_csv(OUT / 'window_boundary_losses.csv', index=False)
    assert all(digest(Path(p)) == sha for p, sha in original.items())
    verification = {'original_artifacts_unchanged': len(original), 'guard_boundary_checks': 10,
        'all_source_hashes_checked': True, 'all_46_original_surfaces_replayed': True,
        'strict_complete_window_replays_both_radii': exact_replays,
        'independent_polyfit_maximum_slope_error': maximum_ols_error,
        'all_windows': len(history), 'pilot_common_scored_windows': len(common),
        'score_difference_median': float(common.absolute_score_difference.median()),
        'score_difference_p90': float(common.absolute_score_difference.quantile(.9)),
        'acceleration_sign_agreement': float((np.sign(common.acceleration_2) == np.sign(common.acceleration_3)).mean()),
        'scale_ratio_range': [float(scales.scale_ratio_3_to_2.min()), float(scales.scale_ratio_3_to_2.max())],
        'baseline_statuses': baseline.status.value_counts().to_dict(),
        'input_manifest_sha256': digest(DATA / 'manifest.json'),
        'code_sha256': digest(Path(__file__)), 'protocol_sha256': digest(OUT / 'PROTOCOL.md')}
    (OUT / 'verification.json').write_text(json.dumps(verification, indent=2)+'\n')
    print(summary.to_string())
    print(baseline.groupby(['radius', 'block_label']).history_days.agg(['min', 'max']).to_string())
    print(json.dumps(verification, indent=2))


if __name__ == '__main__':
    main()

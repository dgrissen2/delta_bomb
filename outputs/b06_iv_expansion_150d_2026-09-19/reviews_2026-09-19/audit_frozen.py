"""Independent cached-data audit; never imports or rewrites study calculations.

Writes only the separate central audit namespace. No API calls. Full-session
VT status is descriptive: it must never be used as a causal entry filter.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE = Path(__file__).resolve().parent.parent
DEST = Path('/Users/dgrissen/Dev/central_trade_data/thetadata/'
            'b06_iv_expansion_150d_audit_2026-09-19-v1')
POLICIES = ['original', 'midpoint', 'guarded_100', 'guarded_50']


def first_touch(raw: pd.DataFrame, minute: int, price: float) -> tuple[str, int | None]:
    """Independently locate both barrier timestamps, preserving same-bar ties."""
    w = raw.loc[minute:minute + 59]
    assert w.index.tolist() == list(range(minute, minute + 60))
    assert price == w.open.iloc[0]
    up = w.index[w.high.ge(price + 5 - 1e-8)].tolist()
    down = w.index[w.low.le(price - 15 + 1e-8)].tolist()
    a, b = up[0] if up else 9999, down[0] if down else 9999
    if min(a, b) == 9999:
        return 'neither', None
    return ('ambiguous' if a == b else 'target_first' if a < b else 'adverse_first'), min(a, b)


def audit_prices(days: pd.DataFrame, parents: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    daily, events = [], []
    vt_source = pd.read_csv('/Users/dgrissen/Dev/core_spotgamma_spx_vix_data/'
                            'offset_historical_spotgamma_data.csv').set_index('Date')
    for d in days.itertuples(index=False):
        path = Path(d.source_path)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == d.source_sha256
        assert vt_source.loc[d.date, 'Vol Trigger'] == d.vol_trigger
        raw = pd.read_parquet(path).set_index('min').loc[570:959]
        assert raw.index.tolist() == list(range(570, 960))
        # The original CSV round-trip loses one float64 ULP on 2026-06-22.
        np.testing.assert_array_max_ulp(np.array([raw.open.iloc[0]]), np.array([d.spot_open]), 1)
        assert raw.open.iloc[0] > d.vol_trigger and d.spot_open > d.vol_trigger
        low_below = raw.low.le(d.vol_trigger)
        first = int(raw.index[low_below][0]) if low_below.any() else None
        daily.append({'date': d.date, 'cohort': d.cohort, 'vol_trigger': d.vol_trigger,
                      'open': d.spot_open, 'session_low': raw.low.min(),
                      'minutes_low_at_or_below': int(low_below.sum()),
                      'minutes_close_at_or_below': int(raw.close.le(d.vol_trigger).sum()),
                      'first_at_or_below_min': first,
                      'first_at_or_below_et': f'{first//60:02d}:{first%60:02d}' if first else '',
                      'opening_35m_range': raw.loc[570:604].high.max() - raw.loc[570:604].low.min()})
        # Independently reconstruct rolling 6-bar close breakouts and dedup levels.
        highs, bars, seen = [], [], set()
        expected = []
        for start in range(570, 960, 5):
            w = raw.loc[start:start + 4]
            bars.append((start, w.high.max(), w.close.iloc[-1]))
        for j, (start, high, close) in enumerate(bars):
            known = start + 5
            if j >= 6 and 600 <= known < 870:
                ceiling = max(highs[-6:])
                if close > ceiling and ceiling not in seen:
                    seen.add(ceiling)
                    expected.append((known, ceiling))
            highs.append(high)
        actual = parents[parents.date.eq(d.date)]
        assert expected == list(zip(actual.parent_min, actual.boundary))
        for e in actual.itertuples(index=False):
            before = raw.loc[570:e.parent_min - 1]
            outcome, touch = first_touch(raw, e.parent_min, e.parent_price)
            events.append({'episode_id': e.episode_id, 'date': e.date, 'cohort': e.cohort,
                           'parent_min': e.parent_min,
                           'entry_et': f'{e.parent_min//60:02d}:{e.parent_min%60:02d}',
                           'entry_price': e.parent_price, 'vol_trigger': d.vol_trigger,
                           'signal_close': raw.loc[e.parent_min-1, 'close'],
                           'entry_above': bool(e.parent_price > d.vol_trigger),
                           'always_above_through_entry': bool(before.low.min() > d.vol_trigger
                                                             and e.parent_price > d.vol_trigger),
                           'whole_day_above_descriptive': bool(not low_below.any()),
                           'reference30_above': bool(raw.loc[e.parent_min-35:e.parent_min-6].low.min()
                                                    > d.vol_trigger),
                           'outcome': outcome, 'first_touch_min': touch})
    result = pd.DataFrame(events)
    saved = pd.read_csv(SOURCE/'event_paths.csv').set_index('episode_id').loc[result.episode_id]
    assert saved.outcome.tolist() == result.outcome.tolist()
    np.testing.assert_equal(saved.first_touch_min.to_numpy(), result.first_touch_min.to_numpy())
    return pd.DataFrame(daily), result


def audit_features(parents: pd.DataFrame) -> dict[str, int]:
    saved = pd.read_parquet(SOURCE/'sector_event_features.parquet')
    features = saved.set_index(['episode_id', 'symbol', 'variant'])
    checked = 0
    for file in sorted((SOURCE/'minute_series').glob('*.parquet')):
        day, symbol = file.stem.split('_')
        panel = pd.read_parquet(file).set_index('timestamp')
        for event in parents[parents.date.eq(day)].itertuples(index=False):
            end = pd.Timestamp(day, tz='America/New_York') + pd.Timedelta(minutes=event.parent_min-6)
            ix = pd.date_range(end-pd.Timedelta(minutes=29), end, freq='min')
            for policy in POLICIES:
                values = panel.loc[ix, policy].to_numpy(dtype=float)
                row = features.loc[(event.episode_id, symbol, policy)]
                finite = np.isfinite(values)
                assert row.samples == finite.sum() and bool(row.available) == bool(finite.all())
                if finite.all():
                    # Least-squares fit with intercept, independent of weighted-dot implementation.
                    x = np.column_stack([np.arange(15, dtype=float), np.ones(15)])
                    a = np.linalg.lstsq(x, values[:15], rcond=None)[0][0]
                    b = np.linalg.lstsq(x, values[15:], rcond=None)[0][0]
                    acc = (b-a)/15
                    np.testing.assert_allclose([a,b,acc],
                        [row.first_slope,row.second_slope,row.acceleration], rtol=0, atol=1e-10)
                    assert bool(row.falling) == bool(b < -1e-12)
                    assert bool(row.accelerating) == bool(b < -1e-12 and acc < -1e-12)
                else:
                    assert not row.falling and not row.accelerating
                checked += 1
    basket = pd.read_csv(SOURCE/'basket_before_outcomes.csv').set_index(['episode_id','variant'])
    for key, group in saved.groupby(['episode_id','variant']):
        assert len(group) == 11 and group.symbol.nunique() == 11
        n = int(group.accelerating.sum()); missing = int((~group.available).sum())
        state = 'yes' if n >= 6 else 'no' if n+missing < 6 else 'unknown'
        assert basket.loc[key,'accelerating_state'] == state
    return {'native_series_feature_rows_recomputed': checked,
            'all_sector_rows': len(saved), 'baskets_recomputed': len(basket)}


def summarize(events: pd.DataFrame) -> pd.DataFrame:
    ledger = pd.read_csv(SOURCE/'event_ledger.csv')
    rows = []
    for cohort in ['original_50','additional_100','combined_150']:
        base = events if cohort == 'combined_150' else events[events.cohort.eq(cohort)]
        for gate in ['all_open_above','entry_above','always_above_through_entry',
                     'whole_day_above_descriptive']:
            subset = base if gate == 'all_open_above' else base[base[gate]]
            for policy in ['baseline', *POLICIES]:
                selected = subset
                if policy != 'baseline':
                    ids = ledger.loc[ledger.variant.eq(policy) & ledger.accelerating_state.eq('yes'),
                                     'episode_id']
                    selected = subset[subset.episode_id.isin(ids)]
                counts = selected.outcome.value_counts()
                rows.append({'cohort':cohort, 'vt_gate':gate, 'policy':policy, 'n':len(selected),
                    'active_dates':selected.date.nunique(),
                    **{k:int(counts.get(k,0)) for k in ['target_first','adverse_first','neither','ambiguous']},
                    'hit_pct':float(selected.outcome.eq('target_first').mean()*100)})
    return pd.DataFrame(rows)


def main() -> None:
    days = pd.read_csv(SOURCE/'combined_days.csv', float_precision='round_trip')
    parents = pd.read_csv(SOURCE/'b06_parents.csv', float_precision='round_trip')
    daily, events = audit_prices(days, parents)
    summary = {'days_checked':len(days), 'parents_and_outcomes_rebuilt':len(events),
               'all_opened_above':True,
               'days_touched_vt':int(daily.minutes_low_at_or_below.gt(0).sum()),
               'entries_at_or_below':int((~events.entry_above).sum()),
               **audit_features(parents)}
    comparison = summarize(events)
    DEST.mkdir(parents=True, exist_ok=False)
    daily.to_csv(DEST/'day_vt_audit.csv',index=False)
    events.to_csv(DEST/'event_vt_audit.csv',index=False)
    events[~events.entry_above].to_csv(DEST/'below_vt_entries.csv',index=False)
    comparison.to_csv(DEST/'vt_comparison.csv',index=False)
    hashes = {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [Path(__file__),SOURCE/'combined_days.csv',SOURCE/'b06_parents.csv',
                        SOURCE/'event_paths.csv',SOURCE/'event_ledger.csv',
                        SOURCE/'basket_before_outcomes.csv',SOURCE/'sector_event_features.parquet']}
    (DEST/'verification.json').write_text(json.dumps(summary|{'input_hashes':hashes},indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    print(comparison.to_string(index=False))


if __name__ == '__main__':
    main()

"""Causal daily-surface study of high call-wing episodes in the frozen HIRO universe."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from pandar_skew_journey_data import END, OUTPUT


def prior_ranks(values: pd.Series, window: int = 252, minimum: int = 126) -> pd.Series:
    """Compute strict prior-only percentiles without imputing missing sessions."""
    data = np.asarray(values, dtype=float)
    windows = np.lib.stride_tricks.sliding_window_view(
        np.concatenate([np.full(window, np.nan), data]), window+1)
    past, current = windows[:, :-1], windows[:, -1]
    count = np.isfinite(past).sum(axis=1)
    numerator = (past < current[:, None]).sum(axis=1)
    rank = np.divide(numerator*100., count, out=np.full(len(data), np.nan),
                     where=(count >= minimum) & np.isfinite(current))
    return pd.Series(rank, index=values.index)


def episode_features(rank: pd.Series, wing: pd.Series) -> pd.DataFrame:
    """Track only the episode history known at each close, including censored starts."""
    rows = []
    age, episode, area, peak = 0, 0, 0., np.nan
    unknown_start, censored = True, False
    for r, w in zip(rank, wing, strict=True):
        record = dict(age=0., episode_id=episode, intensity=0., peak_minus_wing=np.nan,
                      exit_age=0., left_censored=False)
        if not np.isfinite(r) or not np.isfinite(w):
            age, area, peak, unknown_start = 0, 0., np.nan, True
            record['age'] = np.nan
        elif r >= 85:
            if age == 0:
                episode += 1
                censored = unknown_start
            age += 1
            area += (r-85)/15
            peak = w if not np.isfinite(peak) else max(peak, w)
            record.update(age=age, episode_id=episode, intensity=area,
                          peak_minus_wing=peak-w, left_censored=censored)
        else:
            record['exit_age'] = age
            age, area, peak, unknown_start = 0, 0., np.nan, False
        rows.append(record)
    return pd.DataFrame(rows, index=rank.index)


def trailing_variance(close: pd.Series, days: int) -> pd.Series:
    """Annualize squared returns over complete trailing calendar-day windows."""
    valid_close = close.where(close.gt(0))
    returns = np.log(valid_close/valid_close.shift(1))
    window = f'{days}D'
    count = returns.rolling(window, closed='right').count()
    expected = pd.Series(1., index=close.index).rolling(window, closed='right').count()
    variance = returns.pow(2).rolling(window, closed='right').mean()*252
    full_history = close.index >= close.index[0]+pd.Timedelta(days=days)
    return variance.where(count.eq(expected) & full_history)


def add_outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    """Reference entry at t+1 close, then measure holding outcomes without forward filling."""
    result = frame.copy()
    result['signal_to_entry_return'] = (frame.clsPx.shift(-1)/frame.clsPx-1)*100
    result['signal_to_entry_iv10'] = (frame.iv10d.shift(-1)-frame.iv10d)*100
    for h in (1, 2, 3):
        price_valid = pd.Series(True, index=frame.index)
        vol_valid = pd.Series(True, index=frame.index)
        for step in range(1, h+2):
            price_valid &= frame.clsPx.shift(-step).gt(0)
            vol_valid &= (frame.iv10d.shift(-step).gt(0)
                          & frame.iv30d.shift(-step).gt(0)
                          & frame.wing.shift(-step).notna())
        ret = ((frame.clsPx.shift(-(h+1))/frame.clsPx.shift(-1)-1)*100).where(price_valid)
        iv10 = ((frame.iv10d.shift(-(h+1))-frame.iv10d.shift(-1))*100).where(vol_valid)
        result[f'return_{h}'] = ret
        result[f'iv10_change_{h}'] = iv10
        result[f'iv30_change_{h}'] = ((frame.iv30d.shift(-(h+1))-
                                      frame.iv30d.shift(-1))*100).where(vol_valid)
        result[f'wing_change_{h}'] = (frame.wing.shift(-(h+1))-
                                     frame.wing.shift(-1)).where(vol_valid)
        joint = price_valid & vol_valid
        result[f'joint_down_{h}'] = np.where(joint, (ret < 0) & (iv10 < 0), np.nan)
        result[f'down_vol_up_{h}'] = np.where(joint, (ret < 0) & (iv10 > 0), np.nan)
        if 'hiPx' in frame:
            high = pd.concat([frame.hiPx.shift(-i) for i in range(2, h+2)], axis=1)
            result[f'upside_excursion_{h}'] = ((high.max(axis=1)/frame.clsPx.shift(-1)-1)*100
                ).where(price_valid & high.notna().all(axis=1))
    return result


def features_one(frame: pd.DataFrame) -> pd.DataFrame:
    """Separate fixed-tenor tail richness, temporal changes and cross-strike curvature."""
    x = frame.copy()
    x['wing'] = (x.dlt5Iv10d-x.iv10d)*100
    x['callskew30'] = (x.exErnDlt25Iv30d-x.exErnIv30d)*100
    x['wing_rank'] = prior_ranks(x.wing)
    x['callskew30_rank'] = prior_ranks(x.callskew30)
    x = pd.concat([x, episode_features(x.wing_rank, x.wing)], axis=1)
    for h in (30, 60):
        x[f'rv{h}'] = np.sqrt(trailing_variance(x.clsPx, h))
        x[f'variance_premium{h}'] = x[f'iv{h}d'].pow(2)-x[f'rv{h}'].pow(2)
    x['earnings_premium10'] = (x.iv10d-x.exErnIv10d)*100
    x['log_return'] = np.log(x.clsPx.where(x.clsPx.gt(0))/x.clsPx.shift(1).where(x.clsPx.shift(1).gt(0)))
    x['price_acceleration'] = x.log_return.diff()
    x['prior_three_return'] = np.log(x.clsPx.shift(1)/x.clsPx.shift(4))
    x['wing_slope'] = x.wing.diff()
    x['wing_acceleration'] = x.wing.diff().diff()
    x['iv10_slope'] = x.iv10d.diff()*100
    x['iv10_acceleration'] = x.iv10d.diff().diff()*100
    x['rolling_over'] = x.wing_slope.lt(0) & x.wing_slope.shift(1).lt(0)
    x['expanding'] = x.wing_slope.gt(0) & x.wing_slope.shift(1).gt(0)
    x['charlie_exhaustion'] = (x.prior_three_return.gt(0) & x.price_acceleration.lt(0)
                              & x.iv10_slope.lt(0))
    x['premia_available'] = x.variance_premium30.notna() & x.variance_premium60.notna()
    x['both_premia_positive'] = x.variance_premium30.gt(0) & x.variance_premium60.gt(0)
    x['dollar_turnover20'] = (x.clsPx*x.stockVolume).rolling(20, min_periods=20).mean()
    x['confidence_pct'] = x.confidence*100  # Summary endpoint reports a fraction.
    x['eligible'] = (x.wing_rank.notna() & x.confidence_pct.ge(50)
                     & x.dollar_turnover20.ge(20e6) & x.clsPx.gt(0)
                     & x.iv10d.gt(0) & x.iv30d.gt(0) & x.dlt5Iv10d.gt(0))
    return add_outcomes(x)


def build_panel() -> pd.DataFrame:
    """Align every name to SPY sessions and retain missing requested names in coverage."""
    summaries = pd.read_parquet(OUTPUT / 'summaries.parquet')
    prices = pd.read_parquet(OUTPUT / 'dailies.parquet')
    calendar = pd.DatetimeIndex(prices.loc[prices.ticker.eq('SPY'), 'tradeDate'].sort_values())
    if not calendar.is_unique or calendar[-1] != pd.Timestamp(END):
        raise ValueError('Incomplete or duplicate SPY session calendar')
    universe = pd.read_csv(OUTPUT / 'hiro_universe.csv')
    parts, coverage = [], []
    for ticker in universe.loc[universe.single_stock, 'ticker']:
        s = summaries[summaries.ticker.eq(ticker)].drop(columns='ticker')
        p = prices[prices.ticker.eq(ticker)].drop(columns='ticker')
        x = s.set_index('tradeDate').join(p.set_index('tradeDate'), how='outer').reindex(calendar)
        x.index.name = 'tradeDate'
        if s.empty or p.empty:
            coverage.append(dict(ticker=ticker, summary_rows=len(s), price_rows=len(p),
                status='missing summary or price history', eligible_signal_days=0))
            continue
        x = features_one(x).reset_index()
        x['ticker'] = ticker
        x['session_index'] = np.arange(len(x))
        x = x[x.tradeDate.ge('2024-01-02')]
        coverage.append(dict(ticker=ticker, summary_rows=len(s), price_rows=len(p),
            status='evaluated', eligible_signal_days=int(x.eligible.sum()),
            high_rank_days=int((x.eligible & x.wing_rank.ge(85)).sum()),
            first_summary=str(s.tradeDate.min()), last_summary=str(s.tradeDate.max())))
        parts.append(x)
    pd.DataFrame(coverage).to_csv(OUTPUT / 'coverage.csv', index=False)
    panel = pd.concat(parts, ignore_index=True)
    panel['slice'] = np.where(panel.tradeDate.lt('2026-01-01'), '2024–2025', '2026')
    panel['stratum'] = (panel.tradeDate.dt.to_period('Q').astype(str)+'|'
        + pd.cut(panel.wing_rank, [84.999, 90, 95, 100], include_lowest=True).astype(str)+'|'
        + pd.cut(panel.wing, [-np.inf, 0, 5, 15, np.inf]).astype(str)+'|'
        + pd.cut(panel.iv10d, [-np.inf, .3, .6, np.inf]).astype(str)+'|'
        + np.where(panel.earnings_premium10.notna(),
                   np.where(panel.earnings_premium10.le(2), 'event<=2', 'event>2'), 'event_unknown'))
    panel.to_parquet(OUTPUT / 'daily_features_and_outcomes.parquet', index=False)
    panel[panel.eligible & (panel.wing_rank.ge(85) | panel.exit_age.gt(0))].to_csv(
        OUTPUT / 'high_rank_signal_ledger.csv', index=False)
    print('Daily panel', len(panel), 'rows;', panel.ticker.nunique(), 'observed stocks;',
          panel.eligible.sum(), 'eligible dates', flush=True)
    return panel


def masks(frame: pd.DataFrame) -> dict[str, pd.Series]:
    """A small frozen ablation family, not a threshold optimizer."""
    high = frame.eligible & frame.wing_rank.ge(85)
    known_age = ~frame.left_censored
    mature_roll = high & known_age & frame.age.ge(3) & frame.rolling_over
    return {
        'all_eligible': frame.eligible,
        'high_rank': high,
        'high_positive_wing': high & frame.wing.gt(0),
        'high_age1_2': high & known_age & frame.age.between(1, 2),
        'high_age3_5': high & known_age & frame.age.between(3, 5),
        'high_age6plus': high & known_age & frame.age.ge(6),
        'high_age_unknown': high & ~known_age,
        'high_expanding': high & frame['expanding'],
        'high_rollover': high & frame.rolling_over,
        'high_mature_rollover': mature_roll,
        'high_premia_coverage': high & frame.premia_available,
        'high_both_premia': high & frame.both_premia_positive,
        'high_exhaustion': high & frame.charlie_exhaustion,
        'high_mature_rollover_premia_exhaustion': (mature_roll & frame.both_premia_positive
                                                    & frame.charlie_exhaustion),
        'high_exhaustion_accelerating_iv': high & frame.charlie_exhaustion & frame.iv10_acceleration.lt(0),
        'high_low_modeled_event': high & frame.earnings_premium10.le(2),
        'episode_first_exit': frame.eligible & frame.exit_age.gt(0),
    }


def nonoverlap(frame: pd.DataFrame) -> pd.DataFrame:
    """Greedy admission uses only signal time and the maximum three-session horizon."""
    indices = []
    for _, group in frame.sort_values(['ticker', 'session_index']).groupby('ticker'):
        after = -1
        for row in group.itertuples():
            if row.session_index > after:
                indices.append(row.Index)
                after = row.session_index+4
    return frame.loc[indices]


def interval(frame: pd.DataFrame, outcome: str) -> tuple[float, float]:
    """Resample complete calendar months of the panel; no independent-row assumption."""
    grouped = frame.groupby(frame.tradeDate.dt.to_period('M'))[outcome].agg(['sum', 'count'])
    if len(grouped) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(20260906)
    draws = rng.integers(0, len(grouped), (500, len(grouped)))
    sums, counts = grouped['sum'].to_numpy(), grouped['count'].to_numpy()
    values = sums[draws].sum(axis=1)/counts[draws].sum(axis=1)*100
    return tuple(np.quantile(values, [.025, .975]))


def summarize(panel: pd.DataFrame) -> None:
    """Report every frozen comparison and chronological slice, including unavailable outcomes."""
    rows = []
    for name, mask in masks(panel).items():
        sample = panel[mask]
        for mode in ['all_signals', 'nonoverlap']:
            current = sample if mode == 'all_signals' else nonoverlap(sample)
            for era in ['all', '2024–2025', '2026']:
                group = current if era == 'all' else current[current['slice'].eq(era)]
                for h in (1, 2, 3):
                    valid = group[group[f'joint_down_{h}'].notna()]
                    lo, hi = interval(valid, f'joint_down_{h}') if len(valid) else (np.nan, np.nan)
                    rows.append(dict(rule=name, mode=mode, era=era, horizon=h,
                        signals=len(group), valid_outcomes=len(valid), censored=len(group)-len(valid),
                        stocks=valid.ticker.nunique(), months=valid.tradeDate.dt.to_period('M').nunique(),
                        joint_down_pct=valid[f'joint_down_{h}'].mean()*100,
                        joint_ci_low=lo, joint_ci_high=hi,
                        spot_down_pct=valid[f'return_{h}'].lt(0).mean()*100,
                        iv10_down_pct=valid[f'iv10_change_{h}'].lt(0).mean()*100,
                        wing_down_pct=valid[f'wing_change_{h}'].lt(0).mean()*100,
                        down_vol_up_pct=valid[f'down_vol_up_{h}'].mean()*100,
                        mean_return_pct=valid[f'return_{h}'].mean(),
                        median_return_pct=valid[f'return_{h}'].median(),
                        mean_iv10_change_points=valid[f'iv10_change_{h}'].mean(),
                        mean_iv30_change_points=valid[f'iv30_change_{h}'].mean(),
                        mean_wing_change_points=valid[f'wing_change_{h}'].mean(),
                        signal_entry_return_pct=valid.signal_to_entry_return.mean(),
                        signal_entry_iv10_points=valid.signal_to_entry_iv10.mean()))
    summary = pd.DataFrame(rows)
    summary.to_csv(OUTPUT / 'ablation_results.csv', index=False)
    adjusted = []
    high = masks(panel)['high_rank'] & panel.joint_down_2.notna()
    for name, mask in masks(panel).items():
        if name in {'all_eligible', 'high_rank', 'episode_first_exit'}:
            continue
        for era in ['all', '2024–2025', '2026']:
            period = pd.Series(True, index=panel.index) if era == 'all' else panel['slice'].eq(era)
            treated = panel[high & mask & period]
            controls = panel[high & ~mask & period]
            control = controls.groupby('stratum').joint_down_2.agg(['count', 'mean'])
            control = control[control['count'].ge(5)]
            support = treated.merge(control, left_on='stratum', right_index=True, how='inner')
            adjusted.append(dict(rule=name, era=era, treated=len(treated),
                common_support=len(support), matched_cells=support.stratum.nunique(),
                treated_joint_pct=support.joint_down_2.mean()*100,
                weighted_control_joint_pct=support['mean'].mean()*100,
                descriptive_difference_points=(support.joint_down_2-support['mean']).mean()*100))
    pd.DataFrame(adjusted).to_csv(OUTPUT / 'starting_state_comparisons.csv', index=False)
    print(summary.query("mode=='nonoverlap' and era=='all' and horizon==2")[[
        'rule', 'valid_outcomes', 'joint_down_pct', 'wing_down_pct',
        'mean_return_pct', 'mean_iv10_change_points']].to_string(index=False), flush=True)


def bridge(panel: pd.DataFrame) -> None:
    """Attach journey coordinates to the existing exact-strike inventory without inventing P&L."""
    panel = panel.copy()
    panel['high_days20'] = panel.groupby('ticker').wing_rank.transform(
        lambda s: s.ge(85).where(s.notna()).rolling(20, min_periods=20).sum())
    panel['peak20_minus_wing'] = panel.groupby('ticker').wing.transform(
        lambda s: s.rolling(20, min_periods=20).max())-panel.wing
    root = OUTPUT.parent / 'pandar_leg_timing_2026-09-05/call_search_expansion'
    calls = pd.read_csv(root / 'call_candidates_2_to_10_delta.csv', parse_dates=['tradeDate'])
    fields = ['tradeDate', 'ticker', 'wing', 'wing_rank', 'callskew30_rank', 'age',
        'intensity', 'peak_minus_wing', 'high_days20', 'peak20_minus_wing',
        'left_censored', 'rolling_over', 'expanding',
        'charlie_exhaustion', 'wing_acceleration', 'iv10_acceleration', 'rv30', 'rv60',
        'iv30d', 'iv60d', 'variance_premium30', 'variance_premium60', 'earnings_premium10',
        'rDrv30', 'return_2', 'iv10_change_2', 'wing_change_2', 'joint_down_2']
    calls = calls.merge(panel[fields], on=['tradeDate', 'ticker'], how='left', validate='one_to_one')
    calls['log_distance_atm_move_units'] = np.log(calls.strike/calls.stock)/(
        calls.atm_iv_pct/100*np.sqrt(calls.dte/365))
    calls['delta_bucket'] = pd.cut(calls.delta, [.019999, .06, .08, .1], labels=['2–6', '6–8', '8–10'])
    calls['otm_bucket'] = pd.cut(calls.otm_pct, [0, 5, 15, np.inf], labels=['0–5%', '5–15%', '>15%'])
    calls.to_csv(OUTPUT / 'recent_73_calls_with_journey.csv', index=False)
    reconciliation = calls[['tradeDate', 'ticker', 'call_wing_10_pct252', 'wing_rank']].copy()
    reconciliation['difference_points'] = reconciliation.wing_rank-reconciliation.call_wing_10_pct252
    reconciliation.to_csv(OUTPUT / 'recent_rank_reconciliation.csv', index=False)
    counts = calls.groupby(['delta_bucket', 'otm_bucket'], observed=False).size().unstack()
    counts.to_csv(OUTPUT / 'delta_otm_counts.csv')


def main() -> None:
    panel = build_panel()
    summarize(panel)
    bridge(panel)
    (OUTPUT / 'run_summary.json').write_text(json.dumps(dict(
        data_end=END, feature_rows=len(panel), observed_stocks=panel.ticker.nunique(),
        eligible_signal_days=int(panel.eligible.sum()),
        high_rank_signal_days=int((panel.eligible & panel.wing_rank.ge(85)).sum()),
        result_kind='daily spot/surface study; not exact-contract P&L or historical HIRO flow backtest'), indent=2)+'\n')


if __name__ == '__main__':
    main()

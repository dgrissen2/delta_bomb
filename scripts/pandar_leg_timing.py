"""Replay the frozen Pandar inventory using exact NBBO and causal HIRO observations."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pandar_quote_history import OUTPUT, SOURCE, quote_path

FEE = 0.65
FINANCING = 4 * FEE / 100
ZONE = 'America/New_York'
SESSIONS = [d.strftime('%Y-%m-%d') for d in pd.bdate_range('2026-08-11', '2026-09-15')
            if d.strftime('%Y-%m-%d') != '2026-09-07']
CUTOFF = '2026-09-04'


def at(day: str, time: str) -> pd.Timestamp:
    return pd.Timestamp(f'{day} {time}', tz=ZONE)


def shift(day: str, offset: int) -> str:
    return SESSIONS[SESSIONS.index(day) + offset]


def pnl(cash: float, liquidation: float, actions: int) -> float:
    """Return dollars per one-contract unit, including every transaction fee."""
    return 100 * (cash + liquidation) - actions * FEE


def action_price(quote: pd.Series | None, action: str, marking: bool = False) -> float | None:
    """Require non-crossed displayed quotes; zero bid is allowed only as a conservative mark."""
    if quote is None:
        return None
    bid, ask = float(quote.bid), float(quote.ask)
    if not np.isfinite(bid) or not np.isfinite(ask) or bid < 0 or ask <= 0 or bid > ask:
        return None
    if action == 'buy':
        return ask if quote.ask_size >= 1 else None
    if bid == 0 and marking:
        return 0.0
    return bid if bid > 0 and quote.bid_size >= 1 else None


def quote_at(frame: pd.DataFrame, timestamp: pd.Timestamp) -> pd.Series | None:
    """No backfill or nearest-time substitutions are permitted."""
    return frame.loc[timestamp] if timestamp in frame.index else None


@lru_cache(maxsize=120)
def quotes(ticker: str, expiry: str, strike: float, right: str) -> pd.DataFrame:
    path = quote_path(ticker, expiry, strike, right)
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_parquet(path)
    frame['timestamp'] = pd.to_datetime(frame.timestamp, utc=True).dt.tz_convert(ZONE)
    return frame.set_index('timestamp').sort_index()


def features(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute features within one RTH session, retaining missing observations as missing."""
    frame = frame.copy()
    for side in ('total', 'call', 'put'):
        frame[f'{side}15'] = frame[f'delta_{side}'].rolling(15, min_periods=15).sum()
        frame[f'cumulative_{side}'] = frame[f'delta_{side}'].cumsum()
    frame['price15'] = frame.stock_price / frame.stock_price.shift(15) - 1
    frame['prior_low15'] = frame.stock_price.shift(1).rolling(15, min_periods=15).min()
    frame['prior_low30'] = frame.stock_price.shift(1).rolling(30, min_periods=30).min()
    frame['calm_put'] = (frame.put15 > 0) & (frame.price15 >= 0)
    frame['put_reversal'] = (frame.put15 < 0) & (frame.stock_price < frame.prior_low30)
    frame['call_exhaustion'] = ((frame.call15 < 0) & (frame.call15.shift(15) > 0)
                                & (frame.stock_price < frame.prior_low15))
    return frame


def load_hiro(tickers: set[str]) -> tuple[dict, list[dict]]:
    """Choose the latest successful frozen capture per ticker/session and retain input hashes."""
    selected: dict = {}
    for manifest_path in sorted(SOURCE.parent.glob('*/hiro_ticker*/manifest.json')):
        manifest = json.loads(manifest_path.read_text())
        for ticker, record in manifest.get('tickers', {}).items():
            if ticker not in tickers:
                continue
            for day, item in record.get('sessions', {}).items():
                if item['status'] != 'success' or day > CUTOFF:
                    continue
                path = Path(item['series_csv'])
                key = (ticker, day)
                captured = record.get('captured_at_utc', manifest['created_at_utc'])
                if path.exists() and (key not in selected or selected[key][0] < captured):
                    selected[key] = (captured, path)
    data, provenance, combined = {}, [], []
    for (ticker, day), (captured, path) in sorted(selected.items()):
        frame = pd.read_csv(path)
        frame = frame[frame.series_group.eq('all')].copy()
        if frame.empty:
            continue
        frame.index = pd.to_datetime(frame.utc_iso, utc=True).dt.tz_convert(ZONE)
        frame = frame.loc[(frame.index >= at(day, '09:30')) & (frame.index <= at(day, '16:00'))]
        assert np.allclose(frame.delta_total, frame.delta_call + frame.delta_put, atol=0.01)
        assert not frame.index.duplicated().any(), str(path)
        delta = frame[['delta_total', 'delta_call', 'delta_put']].resample(
            '1min', closed='right', label='right').sum(min_count=1)
        price = frame.stock_price.resample('1min', closed='right', label='right').last()
        minute = features(delta.assign(stock_price=price))
        data[ticker, day] = minute
        combined.append(minute.assign(ticker=ticker, session_date=day).reset_index(names='timestamp'))
        provenance.append(dict(ticker=ticker, session_date=day, captured=captured, path=str(path),
                               sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                               points=len(frame), first=str(frame.index.min()),
                               last=str(frame.index.max())))
    pd.concat(combined, ignore_index=True).to_parquet(OUTPUT / 'data/hiro_minutes.parquet', index=False)
    pd.DataFrame(provenance).to_csv(OUTPUT / 'hiro_sources.csv', index=False)
    return data, provenance


def initial_prices(row: pd.Series, first: pd.DataFrame, second: pd.DataFrame,
                   timestamp: pd.Timestamp) -> tuple[float, float] | None:
    is_put = row.scenario.startswith('buy-first')
    a = action_price(quote_at(first, timestamp), 'buy' if is_put else 'sell')
    b = action_price(quote_at(second, timestamp), 'sell' if is_put else 'buy')
    if a is None or b is None:
        return None
    if is_put and not (0 < a - b <= 0.10000001):
        return None
    if not is_put and a < 0.20:
        return None
    return a, b


def choose_entry(row: pd.Series, hiro: dict, mode: str) -> tuple | None:
    day = shift(row.tradeDate, 1)
    is_put = row.scenario.startswith('buy-first')
    right = 'put' if is_put else 'call'
    first = quotes(row.ticker, row.expiry, row.leg1_strike, right)
    second = quotes(row.ticker, row.expiry, row.leg2_strike, right)
    if mode == 'clock':
        times = [at(day, '10:01')]
    else:
        flow = hiro.get((row.ticker, day))
        if flow is None:
            return None
        gate = 'calm_put' if is_put else 'call_exhaustion'
        times = [t + pd.Timedelta(minutes=1)
                 for t in pd.date_range(at(day, '10:00'), at(day, '14:30'), freq='5min')
                 if t in flow.index and flow.loc[t, gate]]
    for timestamp in times:
        prices = initial_prices(row, first, second, timestamp)
        if prices is not None:
            return timestamp, prices[0], prices[1], first, second
    return None


def liquidation(first: pd.DataFrame, second: pd.DataFrame, timestamp: pd.Timestamp,
                is_put: bool, paired: bool) -> float | None:
    a = action_price(quote_at(first, timestamp), 'sell' if is_put else 'buy', marking=True)
    if a is None:
        return None
    if not paired:
        return a if is_put else -a
    b = action_price(quote_at(second, timestamp), 'buy' if is_put else 'sell', marking=True)
    if b is None:
        return None
    return a - b if is_put else b - a


def marked_prices(frame: pd.DataFrame, buy: bool) -> pd.Series:
    """Vectorized equivalent of action_price(..., marking=True)."""
    valid = (np.isfinite(frame.bid) & np.isfinite(frame.ask)
             & (frame.bid >= 0) & (frame.ask > 0) & (frame.bid <= frame.ask))
    if buy:
        return frame.ask.where(valid & (frame.ask_size >= 1))
    return frame.bid.where(valid & ((frame.bid == 0) | (frame.bid_size >= 1)))


def simulate(row: pd.Series, entry: tuple, hiro: dict, method: str,
             horizon: int, financing_target: float = FINANCING) -> dict:
    """Execute a frozen one-unit strategy, including failed completion and deadline liquidation."""
    opened, first_px, second_px, first, second = entry
    is_put = row.scenario.startswith('buy-first')
    day = opened.strftime('%Y-%m-%d')
    planned_exit = min(shift(day, 3), row.expiry)
    exit_day = min(planned_exit, CUTOFF)
    exit_time = at(exit_day, '15:50')
    deadline_day = min(shift(day, horizon), row.expiry)
    deadline = at(min(deadline_day, CUTOFF), '15:50')
    first_cash = -first_px if is_put else first_px
    cash = first_cash
    result = dict(method=method, horizon=horizon, entry_time=opened.isoformat(),
                  leg1_price=first_px, entry_package_debit=first_px-second_px if is_put else second_px-first_px,
                  exit_time=exit_time.isoformat(), planned_exit=planned_exit,
                  exit_shortened=planned_exit > CUTOFF,
                  deadline_censored=deadline_day > CUTOFF, deadline=deadline.isoformat(),
                  status='uncompleted', paired=False, leg2_time=None, leg2_price=None,
                  financing_cash_after_all_fees=None, pnl_net=None, actions=None,
                  completion_benefit_vs_close=None)
    completion_time, completion_px = None, None
    if method == 'simultaneous':
        completion_time, completion_px = opened, second_px
    elif method == 'fixed_clock' and deadline_day <= CUTOFF:
        completion_time = deadline
        completion_px = action_price(quote_at(second, deadline), 'sell' if is_put else 'buy')
    elif method in ('price_finance', 'hiro_finance'):
        for timestamp, quote in second.loc[(second.index > opened) & (second.index <= deadline)].iterrows():
            if timestamp.strftime('%H:%M') < '09:31' or timestamp.strftime('%H:%M') > '15:50':
                continue
            price = action_price(quote, 'sell' if is_put else 'buy')
            if price is None:
                continue
            if (price - first_px if is_put else first_px - price) + 1e-9 < financing_target:
                continue
            if method == 'hiro_finance':
                observation = timestamp - pd.Timedelta(minutes=1)
                flow = hiro.get((row.ticker, timestamp.strftime('%Y-%m-%d')))
                gate = 'put_reversal' if is_put else 'call_exhaustion'
                if flow is None or observation not in flow.index or not flow.loc[observation, gate]:
                    continue
            completion_time, completion_px = timestamp, price
            break
    if completion_px is not None:
        result.update(paired=True, status='completed', leg2_time=completion_time.isoformat(),
                      leg2_price=completion_px)
        cash += completion_px if is_put else -completion_px
        result['financing_cash_after_all_fees'] = 100 * cash - 4 * FEE
        actions = 4
    elif method == 'standalone':
        actions = 2
        result['status'] = 'standalone'
    elif method == 'fixed_clock':
        result['status'] = 'unpriced_deadline' if deadline_day <= CUTOFF else 'censored'
        return result
    else:
        actions = 2
        exit_time = deadline
        result['exit_time'] = exit_time.isoformat()
        result['status'] = 'censored' if deadline_day > CUTOFF else 'aborted_uncompleted'
    mark = liquidation(first, second, exit_time, is_put, result['paired'])
    result['actions'] = actions
    if mark is None:
        result['status'] = 'unpriced_exit'
        return result
    result['pnl_net'] = pnl(cash, mark, actions)
    result['pnl_extra_1c_slippage'] = result['pnl_net'] - actions
    result['residual_liquidation'] = mark * 100
    if result['paired']:
        first_mark = liquidation(first, second, completion_time, is_put, False)
        if first_mark is not None:
            phase = pnl(first_cash, first_mark, 2)
            result['first_leg_pnl_at_completion'] = phase
            result['completion_benefit_vs_close'] = result['pnl_net'] - phase
    # Full-path minute liquidation stress; zero bids are conservative marks, not fills.
    held = first.loc[(first.index >= opened) & (first.index <= exit_time)].between_time('09:30', '16:00')
    first_value = marked_prices(held, buy=not is_put) * (1 if is_put else -1)
    first_phase = pnl(first_cash, first_value, 2)
    if result['paired']:
        paired_value = first_value + marked_prices(second, buy=is_put) * (-1 if is_put else 1)
        paired_phase = pnl(cash, paired_value.reindex(first_value.index), 4)
        path_values = first_phase.where(first_phase.index < completion_time, paired_phase)
        naked_values = first_phase[first_phase.index < completion_time]
    else:
        path_values, naked_values = first_phase, first_phase
    result['min_liquidation_pnl'] = path_values.min()
    result['max_liquidation_pnl'] = path_values.max()
    result['first_leg_min_pnl'] = naked_values.min()
    return result


def main() -> None:
    frame = pd.read_csv(SOURCE / 'pandar_approved_exact_confirmations.csv')
    frame = frame.sort_values(['tradeDate', 'ticker']).reset_index(drop=True)
    frame['row_id'] = frame.index
    frame['primary_episode'] = ~frame.duplicated(['ticker', 'expiry', 'leg1_strike', 'leg2_strike'])
    hiro, _ = load_hiro(set(frame.ticker))
    coverage, results = [], []
    for _, row in frame.iterrows():
        day = shift(row.tradeDate, 1)
        base = {k: row[k] for k in ('row_id', 'primary_episode', 'tradeDate', 'ticker', 'scenario',
                                    'expiry', 'leg1_strike', 'leg2_strike')}
        cov = dict(**base, entry_day=day, hiro_entry_day=(row.ticker, day) in hiro,
                   signal_day_hiro=(row.ticker, row.tradeDate) in hiro)
        for mode in ('clock', 'hiro'):
            entry = choose_entry(row, hiro, mode)
            cov[f'{mode}_entry'] = entry[0].isoformat() if entry else None
            if entry is None:
                continue
            for method in ('simultaneous', 'standalone', 'fixed_clock', 'price_finance', 'hiro_finance'):
                horizons = [-1] if method in ('simultaneous', 'standalone') else [0, 1, 2]
                for horizon in horizons:
                    result = simulate(row, entry, hiro, method, max(0, horizon))
                    result['horizon'] = horizon
                    results.append(dict(**base, entry_mode=mode, **result))
        coverage.append(cov)
        if len(coverage) % 10 == 0:
            print('replayed', len(coverage), '/', len(frame), flush=True)
    pd.DataFrame(coverage).to_csv(OUTPUT / 'coverage.csv', index=False)
    report = pd.DataFrame(results)
    report.to_csv(OUTPUT / 'all_attempts.csv', index=False)
    summary = []
    for primary in (False, True):
        cohort = report[report.primary_episode] if primary else report
        for key, group in cohort.groupby(['scenario', 'entry_mode', 'method', 'horizon']):
            priced = group[group.pnl_net.notna()]
            complete = priced[(~priced.deadline_censored) & (~priced.exit_shortened)]
            summary.append(dict(distinct_episodes=primary, scenario=key[0], entry_mode=key[1],
                                method=key[2], horizon=key[3], attempts=len(group), priced=len(priced),
                                paired=int(group.paired.sum()), winners=int((priced.pnl_net > 0).sum()),
                                pnl_sum=priced.pnl_net.sum(), pnl_mean=priced.pnl_net.mean(),
                                pnl_median=priced.pnl_net.median(), worst=priced.pnl_net.min(),
                                slippage_sum=priced.pnl_extra_1c_slippage.sum(),
                                complete_horizon=len(complete), complete_horizon_pnl=complete.pnl_net.sum()))
    pd.DataFrame(summary).to_csv(OUTPUT / 'summary.csv', index=False)
    print(pd.DataFrame(summary).query('distinct_episodes and entry_mode == "hiro"').to_string(index=False))


if __name__ == '__main__':
    main()

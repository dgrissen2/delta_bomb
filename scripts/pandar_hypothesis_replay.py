"""Pure fixed-contract call-leg replay; no network, substitutions or inferred fills.

Input minute rows have a unique, timezone-aware timestamp index and far_/near_ prefixed
bid, ask, bid_size, ask_size, bid_condition, ask_condition, delta and underlying_price
columns. Optional underlying_timestamp and greek_timestamp columns are checked against
each order; later observations cannot supply its Greeks. The caller must merge quote
and Greek snapshots on their exact timestamps, without forward filling.

All results remain quoted-price diagnostics. A minute sample is not event quote-age
evidence, and this module does not verify deliverables or simulate early assignment.
One-cent costs determine purchase times; two-cent costs stress those same timestamps.
Actual *_quote_timestamp means an event timestamp, never an interval sample label.
Supplied event quotes must be at most five seconds old. require_event_age additionally
makes absent event timestamps unavailable; the default retains minute-only diagnostics.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from typing import Any, Mapping

import numpy as np
import pandas as pd

ZONE = 'America/New_York'
FEE_PER_CONTRACT_ACTION = .65
PRIMARY_SLIPPAGE_PER_SHARE = .01
STRESS_SLIPPAGE_PER_SHARE = .02
NORMAL_QUOTE_CONDITIONS = frozenset({0, 50})
QUOTE_TIME_FIELDS = ('quote_timestamp', 'bid_timestamp', 'ask_timestamp')
GREEK_TIME_FIELDS = ('underlying_timestamp', 'greek_timestamp')
METHODS = ('immediate_spread', 'deferred_d0', 'deferred_d1', 'deferred_d2', 'short_only')


@dataclass(frozen=True)
class FrozenCase:
    """Contract and calendar choices fixed before outcomes; earnings statuses are supplied."""

    ticker: str
    signal_date: str
    entry_date: str
    expiry: str
    far_strike: float
    near_strike: float
    exchange_sessions: tuple[str, ...]
    earnings_status_by_date: Mapping[str, str]
    variant: str = 'original'
    far_delta_min: float = .02
    far_delta_max: float = .10
    far_otm_min_pct: float = 0.
    require_event_age: bool = False
    multiplier: float = 100.
    multiplier_verified: bool = False
    deliverables_verified: bool = False
    observation_cutoff: pd.Timestamp | None = None


def _at(day: str, clock: str) -> pd.Timestamp:
    return pd.Timestamp(f'{day} {clock}', tz=ZONE)


def _et(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError('timestamps must include a timezone')
    return timestamp.tz_convert(ZONE)


def _number(row: pd.Series, name: str) -> float:
    try:
        return float(row.get(name, np.nan))
    except (TypeError, ValueError):
        return np.nan


def _observations(row: pd.Series | None, leg: str, strike: float) -> dict[str, Any]:
    """Retain observed gate inputs for unsuccessful orders as well as admitted ones."""
    if row is None:
        return {}
    result: dict[str, Any] = {}
    for field in ('bid', 'ask', 'bid_size', 'ask_size', 'bid_condition', 'ask_condition',
                  'delta', 'underlying_price', 'iv_error', 'implied_vol'):
        value = _number(row, f'{leg}_{field}')
        result[field] = value if np.isfinite(value) else None
    spot, bid, ask = result['underlying_price'], result['bid'], result['ask']
    result['otm_pct'] = 100 * (strike / spot - 1) if spot and spot > 0 else None
    result['spread_pct'] = (200 * (ask - bid) / (ask + bid)
                            if ask is not None and bid is not None and ask + bid > 0 else None)
    for field in ('underlying_timestamp', 'greek_timestamp', 'quote_timestamp',
                  'bid_timestamp', 'ask_timestamp', 'greek_source_path', 'quote_source_path'):
        value = row.get(f'{leg}_{field}')
        if value is not None and pd.notna(value):
            result[field] = str(value)
    event_time = row.get(f'{leg}_quote_timestamp')
    result['quote_age_seconds'] = None
    if event_time is not None and pd.notna(event_time):
        try:
            result['quote_age_seconds'] = (row.name - _et(event_time)).total_seconds()
        except (ValueError, TypeError):
            pass
    return result


def _combine(checks: list[tuple[str, str]]) -> tuple[str, str]:
    """An observed failed conjunct establishes rejection even if another input is absent."""
    reasons = [reason for status, reason in checks if status != 'valid']
    status = ('rejected' if any(s == 'rejected' for s, _ in checks)
              else 'unavailable' if reasons else 'valid')
    return status, '|'.join(reasons)


def _causal_metadata(row: pd.Series, leg: str, fields: tuple[str, ...],
                     timestamp: pd.Timestamp) -> tuple[str, str]:
    """Validate temporal admissibility before a value can establish any decision gate."""
    for field in fields:
        value = row.get(f'{leg}_{field}')
        if value is None or pd.isna(value):
            continue
        try:
            source_time = _et(value)
        except (ValueError, TypeError):
            return 'unavailable', f'{leg}_invalid_{field}'
        if source_time > timestamp:
            return 'unavailable', f'{leg}_future_{field}'
    return 'valid', ''


def _quote_time(row: pd.Series, leg: str, require_event_age: bool) -> tuple[str, str]:
    """Use supplied actual event times; never substitute the interval's index label."""
    temporal = _causal_metadata(row, leg, QUOTE_TIME_FIELDS, row.name)
    if temporal[0] != 'valid':
        return temporal
    value = row.get(f'{leg}_quote_timestamp')
    if value is None or pd.isna(value):
        return (('unavailable', f'{leg}_quote_event_timestamp_missing')
                if require_event_age else ('valid', ''))
    if (row.name - _et(value)).total_seconds() > 5:
        return 'rejected', f'{leg}_stale_quote_age'
    return 'valid', ''


def _quote(row: pd.Series | None, leg: str, side: str, *, spread_gate: bool = False,
           allow_zero_mark: bool = False, require_event_age: bool = False) -> tuple[str, str]:
    if row is None:
        return 'unavailable', 'minute_quote_missing'
    temporal = _quote_time(row, leg, require_event_age)
    if temporal[0] != 'valid':
        return temporal
    names = ('bid', 'ask', 'bid_condition', 'ask_condition', f'{side}_size')
    values = {name: _number(row, f'{leg}_{name}') for name in names}
    if not all(np.isfinite(x) for x in values.values()):
        return 'unavailable', f'{leg}_quote_fields_missing'
    bid, ask = values['bid'], values['ask']
    checks = []
    if not (0 <= bid <= ask and ask > 0):
        checks.append(('rejected', f'{leg}_invalid_nbbo'))
    if any(values[name] not in NORMAL_QUOTE_CONDITIONS
           for name in ('bid_condition', 'ask_condition')):
        checks.append(('rejected', f'{leg}_quote_condition'))
    zero_mark = side == 'bid' and bid == 0 and allow_zero_mark
    if values[f'{side}_size'] < 1 and not zero_mark:
        checks.append(('rejected', f'{leg}_action_size'))
    if side == 'bid' and bid <= 0 and not zero_mark:
        checks.append(('rejected', f'{leg}_nonpositive_sale_bid'))
    if spread_gate and ask + bid > 0 and (ask - bid) / ((ask + bid) / 2) > .30 + 1e-12:
        checks.append(('rejected', f'{leg}_spread_above_30pct'))
    return _combine(checks)


def _greek(row: pd.Series, leg: str, strike: float, timestamp: pd.Timestamp,
           *, far_entry: bool = False, delta_bounds: tuple[float, float] = (.02, .10),
           minimum_otm_pct: float = 0.) -> tuple[str, str]:
    temporal = _causal_metadata(row, leg, GREEK_TIME_FIELDS, timestamp)
    if temporal[0] != 'valid':
        return temporal
    delta = _number(row, f'{leg}_delta')
    spot = _number(row, f'{leg}_underlying_price')
    checks = []
    if not np.isfinite(delta) or not np.isfinite(spot):
        checks.append(('unavailable', f'{leg}_greek_fields_missing'))
    else:
        if not 0 < delta <= 1:
            checks.append(('rejected', f'{leg}_invalid_call_delta'))
        if far_entry and not delta_bounds[0] <= delta <= delta_bounds[1]:
            checks.append(('rejected', f'far_delta_outside_{100*delta_bounds[0]:g}_{100*delta_bounds[1]:g}'))
        if spot <= 0:
            checks.append(('rejected', f'{leg}_invalid_underlying'))
        elif spot >= strike:
            checks.append(('rejected', f'{leg}_not_otm'))
        elif 100 * (strike / spot - 1) + 1e-10 < minimum_otm_pct:
            checks.append(('rejected', f'{leg}_otm_below_{minimum_otm_pct:g}pct'))
    return _combine(checks)


def _earnings(case: FrozenCase, day: str) -> tuple[str, str]:
    status = case.earnings_status_by_date.get(day, 'unknown')
    if status == 'clear':
        return 'valid', ''
    if status in {'event', 'event_in_next_30_days', 'earnings_event'}:
        return 'rejected', 'earnings_event'
    return 'unavailable', 'earnings_unknown'


def _row_at(minutes: pd.DataFrame, timestamp: pd.Timestamp) -> pd.Series | None:
    return minutes.loc[timestamp] if timestamp in minutes.index else None


def _initial_time(case: FrozenCase, hiro: pd.DataFrame, policy: str) -> tuple[str, str, Any]:
    if policy == 'clock':
        return 'valid', '', _at(case.entry_date, '10:01')
    if hiro.empty or not {'event_at', 'info_cutoff', 'action_at', 'data_status',
                           'trigger', 'series_group'}.issubset(hiro):
        return 'unavailable', 'hiro_decisions_missing', pd.NaT
    frame = hiro.copy()
    if 'ticker' in frame:
        frame = frame.loc[frame.ticker.eq(case.ticker)]
    if frame.empty:
        return 'unavailable', 'hiro_decisions_missing', pd.NaT
    frame['event_at'] = frame.event_at.map(_et)
    frame = frame.loc[frame.event_at.dt.strftime('%Y-%m-%d').eq(case.entry_date)]
    if frame.event_at.duplicated().any():
        raise ValueError('duplicate HIRO decision timestamps')
    frame = frame.set_index('event_at')
    earlier_missing = False
    for event in pd.date_range(_at(case.entry_date, '10:00'), _at(case.entry_date, '14:30'), freq='5min'):
        if event not in frame.index:
            earlier_missing = True
            continue
        row = frame.loc[event]
        if row.data_status != 'available' or row.series_group != 'all':
            earlier_missing = True
            continue
        if not isinstance(row.trigger, (bool, np.bool_)):
            earlier_missing = True
            continue
        action = _et(row.action_at)
        if _et(row.info_cutoff) != event or action != event + pd.Timedelta(minutes=1):
            earlier_missing = True
            continue
        if bool(row.trigger):
            if earlier_missing:
                return 'unavailable', 'earlier_hiro_decisions_unavailable', action
            return 'valid', '', action
    return (('unavailable', 'hiro_decisions_incomplete', pd.NaT) if earlier_missing
            else ('rejected', 'known_no_hiro_trigger', pd.NaT))


def _initial_gate(case: FrozenCase, minutes: pd.DataFrame,
                  timestamp: pd.Timestamp) -> tuple[str, str]:
    if case.observation_cutoff is not None and timestamp > _et(case.observation_cutoff):
        return 'unavailable', 'entry_beyond_observation_cutoff'
    row = _row_at(minutes, timestamp)
    if row is None:
        return 'unavailable', 'minute_quote_missing'
    times = [_quote_time(row, leg, case.require_event_age) for leg in ('far', 'near')]
    if case.require_event_age and any(status == 'unavailable' for status, _ in times):
        return 'unavailable', '|'.join(reason for status, reason in times if status == 'unavailable')
    checks = [_quote(row, 'far', 'bid', spread_gate=True, require_event_age=case.require_event_age),
              _quote(row, 'near', 'ask', spread_gate=True, require_event_age=case.require_event_age),
              _greek(row, 'far', case.far_strike, timestamp, far_entry=True,
                     delta_bounds=(case.far_delta_min, case.far_delta_max),
                     minimum_otm_pct=case.far_otm_min_pct),
              _earnings(case, timestamp.strftime('%Y-%m-%d'))]
    bid = _number(row, 'far_bid')
    if (_quote_time(row, 'far', case.require_event_age)[0] == 'valid'
            and np.isfinite(bid) and bid < .20):
        checks.append(('rejected', 'far_minimum_bid'))
    if timestamp >= _at(case.expiry, '16:00'):
        checks.append(('rejected', 'contract_expired'))
    return _combine(checks)


def _deadline(case: FrozenCase, horizon: int) -> pd.Timestamp | None:
    sessions = [day for day in case.exchange_sessions if day >= case.entry_date]
    if len(sessions) < horizon:
        expired = [day for day in sessions if day <= case.expiry]
        return (_at(expired[-1], '15:50')
                if expired and sessions[-1] >= case.expiry else None)
    scheduled = sessions[horizon - 1]
    # Expiry caps at the last supplied exchange session on or before expiry.
    choices = [day for day in sessions if day <= min(scheduled, case.expiry)]
    return _at(choices[-1], '15:50') if choices else None


def _purchase(case: FrozenCase, minutes: pd.DataFrame, opened: pd.Timestamp,
              exit_at: pd.Timestamp | None, method: str, sale_bid: float) -> dict[str, Any]:
    result = dict(completion_status='known_no_purchase', conversion_at=pd.NaT,
                  observed_financing_at=pd.NaT, purchase_ask=np.nan, purchase_delta=np.nan,
                  purchase_otm_pct=np.nan, purchase_rejections='{}',
                  purchase_rejection_observations='[]', purchase_observations='{}')
    if method == 'short_only':
        result['completion_status'] = 'short_only'
        return result
    if exit_at is None:
        result['completion_status'] = 'censored_purchase_path'
        return result
    if method == 'immediate_spread':
        times = pd.DatetimeIndex([opened])
    else:
        offset = int(method[-1])
        sessions = [day for day in case.exchange_sessions if day >= case.entry_date]
        if len(sessions) <= offset:
            result['completion_status'] = 'censored_purchase_path'
            return result
        day = sessions[offset]
        start = opened + pd.Timedelta(minutes=1) if offset == 0 else _at(day, '09:31')
        end = min(_at(day, '15:30'), exit_at)
        times = pd.date_range(start, end, freq='min') if start <= end else pd.DatetimeIndex([])
    missing = False
    rejections: Counter[str] = Counter()
    rejection_observations = []
    for timestamp in times:
        if case.observation_cutoff is not None and timestamp > _et(case.observation_cutoff):
            missing = True
            rejections['purchase_beyond_observation_cutoff'] += 1
            break
        row = _row_at(minutes, timestamp)
        checks = [_quote(row, 'near', 'ask', spread_gate=True, require_event_age=case.require_event_age),
                  _earnings(case, timestamp.strftime('%Y-%m-%d'))]
        if row is not None:
            checks.append(_greek(row, 'near', case.near_strike, timestamp))
            ask = _number(row, 'near_ask')
            if (method != 'immediate_spread' and np.isfinite(ask)
                    and _quote_time(row, 'near', case.require_event_age)[0] == 'valid'
                    and (sale_bid - ask - 2 * PRIMARY_SLIPPAGE_PER_SHARE) * case.multiplier
                    < 2 * FEE_PER_CONTRACT_ACTION - 1e-9):
                checks.append(('rejected', 'insufficient_financing'))
            time_check = _quote_time(row, 'near', case.require_event_age)
            if time_check[0] == 'unavailable':
                checks = [time_check]
        status, reason = _combine(checks)
        if status != 'valid':
            rejections[reason] += 1
            rejection_observations.append(dict(timestamp=timestamp.isoformat(), status=status,
                                               reason=reason,
                                               **_observations(row, 'near', case.near_strike)))
            missing |= status == 'unavailable'
            continue
        result['observed_financing_at'] = timestamp
        if missing:
            result['completion_status'] = 'censored_purchase_path'
        else:
            result.update(completion_status='completed', conversion_at=timestamp,
                          purchase_ask=float(row.near_ask), purchase_delta=float(row.near_delta),
                          purchase_otm_pct=100 * (case.near_strike / row.near_underlying_price - 1),
                          purchase_observations=json.dumps(_observations(row, 'near', case.near_strike)))
        break
    else:
        if missing:
            result['completion_status'] = 'censored_purchase_path'
    result['purchase_rejections'] = json.dumps(dict(rejections), sort_keys=True)
    result['purchase_rejection_observations'] = json.dumps(rejection_observations)
    if method == 'immediate_spread' and result['completion_status'] != 'completed':
        result['completion_status'] = 'immediate_spread_unavailable'
    return result


def _exposure(case: FrozenCase, minutes: pd.DataFrame, opened: pd.Timestamp,
              end: pd.Timestamp | None, sale_bid: float, slippage: float) -> dict[str, Any]:
    if end is None:
        return {}
    if case.observation_cutoff is not None:
        end = min(end, _et(case.observation_cutoff))
    phase = minutes.loc[(minutes.index >= opened) & (minutes.index <= end)].between_time('09:30', '16:00')
    losses = []
    for _, row in phase.iterrows():
        if _quote(row, 'far', 'ask', require_event_age=case.require_event_age)[0] == 'valid':
            losses.append((sale_bid - row.far_ask - 2 * slippage) * case.multiplier
                          - 2 * FEE_PER_CONTRACT_ACTION)
    initial_spot = _number(minutes.loc[opened], 'far_underlying_price')
    spot = pd.to_numeric(phase.get('far_underlying_price', pd.Series(dtype=float)), errors='coerce')
    causal_greeks = pd.Series([
        _causal_metadata(row, 'far', GREEK_TIME_FIELDS, timestamp)[0] == 'valid'
        for timestamp, row in phase.iterrows()
    ], index=phase.index, dtype=bool)
    spot = spot.where(np.isfinite(spot) & spot.gt(0) & causal_greeks)
    delta = pd.to_numeric(phase.get('far_delta', pd.Series(dtype=float)), errors='coerce')
    delta = delta.where(np.isfinite(delta) & delta.between(0, 1) & causal_greeks)
    expected = sum(len(pd.date_range(max(opened, _at(day, '09:30')),
                                     min(end, _at(day, '16:00')), freq='min'))
                   for day in case.exchange_sessions
                   if opened.strftime('%Y-%m-%d') <= day <= end.strftime('%Y-%m-%d'))
    worst = min(losses) if losses else np.nan
    return dict(
        naked_short_wall_minutes=(end - opened).total_seconds() / 60,
        short_phase_is_counterfactual=False,
        short_phase_expected_minutes=expected, short_phase_observed_minutes=len(phase),
        short_phase_valid_cover_marks=len(losses), worst_observed_short_cover_pnl=worst,
        largest_observed_cover_loss=max(0., -worst) if np.isfinite(worst) else np.nan,
        largest_observed_underlying_rally_pct=(100 * (spot.max() / initial_spot - 1)
                                               if initial_spot > 0 and len(spot) else np.nan),
        peak_observed_far_delta=delta.max() if len(delta) else np.nan,
        exposure_basis='Observed RTH minute snapshots; gaps and intraminute extremes not inferred',
    )


def _account(case: FrozenCase, minutes: pd.DataFrame, opened: pd.Timestamp,
             exit_at: pd.Timestamp | None, purchase: dict[str, Any],
             slippage: float) -> dict[str, Any]:
    sale_bid = float(minutes.loc[opened, 'far_bid'])
    paired = purchase['completion_status'] == 'completed'
    result: dict[str, Any] = dict(
        pnl_net=np.nan, financing_cash=np.nan, cover_at_conversion_pnl=np.nan,
        cover_at_conversion_status='not_applicable', cover_at_conversion_reason='',
        incremental_vs_conversion_cover=np.nan, exit_status='missing_exit',
        long_close_executed=False, executed_actions=1 + int(paired), reserved_actions=0,
        fees_charged=(1 + int(paired)) * FEE_PER_CONTRACT_ACTION, fee_reserve=0.,
        slippage_charged=(1 + int(paired)) * slippage * case.multiplier,
        slippage_reserve=0., quote_action_cash=np.nan,
        quote_event_age_verified=False,
    )
    if paired:
        conversion = purchase['conversion_at']
        result['financing_cash'] = ((sale_bid - purchase['purchase_ask'] - 2 * slippage)
                                    * case.multiplier - 2 * FEE_PER_CONTRACT_ACTION)
        cover = _row_at(minutes, conversion)
        cover_status, cover_reason = _quote(cover, 'far', 'ask', require_event_age=case.require_event_age)
        result['cover_at_conversion_status'] = 'quoted_cover' if cover_status == 'valid' else 'unpriced'
        result['cover_at_conversion_reason'] = cover_reason
        if cover_status == 'valid':
            result['cover_at_conversion_pnl'] = ((sale_bid - cover.far_ask - 2 * slippage)
                                                * case.multiplier - 2 * FEE_PER_CONTRACT_ACTION)
    phase_end = purchase['conversion_at'] if paired else exit_at
    result.update(_exposure(case, minutes, opened, phase_end, sale_bid, slippage))
    if purchase['completion_status'] in {'censored_purchase_path', 'immediate_spread_unavailable'}:
        result['observed_unconverted_scenario_wall_minutes'] = result.get('naked_short_wall_minutes')
        result['naked_short_wall_minutes'] = np.nan
        result['short_phase_is_counterfactual'] = True
        result['exposure_basis'] = ('Hypothetical unconverted-short minute scenario; actual conversion '
                                    'path or immediate spread unavailable, not actual phase duration')
    if exit_at is None:
        result['exit_status'] = 'exchange_calendar_incomplete'
        return result
    if case.observation_cutoff is not None and exit_at > _et(case.observation_cutoff):
        result['exit_status'] = 'future_deadline'
        return result
    if purchase['completion_status'] in {'censored_purchase_path', 'immediate_spread_unavailable'}:
        result['exit_status'] = purchase['completion_status']
        return result
    close = _row_at(minutes, exit_at)
    result['exit_quote_observations'] = json.dumps(dict(
        far=_observations(close, 'far', case.far_strike),
        near=_observations(close, 'near', case.near_strike)))
    status, reason = _quote(close, 'far', 'ask', require_event_age=case.require_event_age)
    if status != 'valid':
        result['exit_reason'] = reason
        return result
    gross = (sale_bid - close.far_ask) * case.multiplier
    result['executed_actions'] += 1
    result['fees_charged'] = result['executed_actions'] * FEE_PER_CONTRACT_ACTION
    result['slippage_charged'] = result['executed_actions'] * slippage * case.multiplier
    result['exit_status'] = 'quoted_short_close'
    if paired:
        status, reason = _quote(close, 'near', 'bid', allow_zero_mark=True,
                               require_event_age=case.require_event_age)
        if status != 'valid':
            result['exit_status'] = 'missing_long_exit'
            result['exit_reason'] = reason
            return result
        gross += (close.near_bid - purchase['purchase_ask']) * case.multiplier
        if close.near_bid == 0:
            result['reserved_actions'] = 1
            result['exit_status'] = 'zero_bid_long_mark'
        else:
            result['executed_actions'] += 1
            result['long_close_executed'] = True
            result['exit_status'] = 'quoted_spread_close'
    result['fees_charged'] = result['executed_actions'] * FEE_PER_CONTRACT_ACTION
    result['fee_reserve'] = result['reserved_actions'] * FEE_PER_CONTRACT_ACTION
    result['slippage_charged'] = result['executed_actions'] * slippage * case.multiplier
    result['slippage_reserve'] = result['reserved_actions'] * slippage * case.multiplier
    result['quote_action_cash'] = gross
    result['pnl_net'] = gross - sum(result[k] for k in
                                   ('fees_charged', 'fee_reserve', 'slippage_charged', 'slippage_reserve'))
    age_inputs = [(minutes.loc[opened], 'far'), (minutes.loc[opened], 'near'), (close, 'far')]
    if paired:
        age_inputs.extend([(minutes.loc[purchase['conversion_at']], 'near'), (close, 'near')])
    result['quote_event_age_verified'] = all(_quote_time(row, leg, True)[0] == 'valid'
                                              for row, leg in age_inputs)
    if purchase['completion_status'] == 'known_no_purchase':
        result['cover_at_conversion_pnl'] = result['pnl_net']
        result['cover_at_conversion_status'] = 'no_conversion_final_cover_fallback'
        result['cover_at_conversion_reason'] = 'Observed no-conversion path retains short to common final cover'
    result['incremental_vs_conversion_cover'] = result['pnl_net'] - result['cover_at_conversion_pnl']
    return result


def replay_case(case: FrozenCase, minutes: pd.DataFrame,
                hiro_decisions: pd.DataFrame) -> pd.DataFrame:
    """Replay two initial policies, five acquisition arms, two exits and fixed-time costs.

    Known no-entry rows have zero trading profit; missing inputs have NaN profit.
    Conversion-time short-cover control values hold cash through the same final deadline.
    A known no-purchase path covers at that final deadline in both policies. An immediate
    spread with an unavailable/ineligible nearer leg stays unavailable, not short-only.
    Neither raw residual marks nor positive construction cash establish an executed close.
    """
    if not isinstance(minutes.index, pd.DatetimeIndex) or minutes.index.tz is None:
        raise ValueError('minute index must be a timezone-aware DatetimeIndex')
    if minutes.index.duplicated().any():
        raise ValueError('duplicate minute timestamps')
    if not (0 < case.near_strike < case.far_strike and case.multiplier > 0):
        raise ValueError('invalid frozen strike identities or multiplier')
    if not (0 < case.far_delta_min <= case.far_delta_max <= 1 and case.far_otm_min_pct >= 0):
        raise ValueError('invalid frozen delta or OTM bounds')
    if list(case.exchange_sessions) != sorted(set(case.exchange_sessions)):
        raise ValueError('exchange sessions must be sorted and unique')
    if case.entry_date not in case.exchange_sessions or case.signal_date >= case.entry_date:
        raise ValueError('entry must follow the EOD signal and belong to the exchange calendar')
    minutes = minutes.copy()
    minutes.index = minutes.index.tz_convert(ZONE)
    minutes = minutes.sort_index()
    if case.observation_cutoff is not None:
        minutes = minutes.loc[minutes.index <= _et(case.observation_cutoff)]
    rows = []
    for policy in ('clock', 'hiro'):
        status, reason, opened = _initial_time(case, hiro_decisions, policy)
        if status == 'valid':
            status, reason = _initial_gate(case, minutes, opened)
        initial_status = {'valid': 'entered', 'rejected': 'known_no_entry',
                          'unavailable': 'censored_entry'}[status]
        for horizon in (4, 5):
            exit_at = _deadline(case, horizon)
            for method in METHODS:
                purchase = (_purchase(case, minutes, opened, exit_at, method,
                                      float(minutes.loc[opened, 'far_bid']))
                            if status == 'valid' else {})
                for slippage in (PRIMARY_SLIPPAGE_PER_SHARE, STRESS_SLIPPAGE_PER_SHARE):
                    row = dict(
                        ticker=case.ticker, signal_date=case.signal_date, entry_date=case.entry_date,
                        expiry=case.expiry, far_strike=case.far_strike, near_strike=case.near_strike,
                        variant=case.variant, far_delta_min=case.far_delta_min,
                        far_delta_max=case.far_delta_max, far_otm_min_pct=case.far_otm_min_pct,
                        require_event_age=case.require_event_age, quote_event_age_verified=False,
                        entry_policy=policy, method=method, holding_sessions=horizon,
                        entry_at=opened, exit_at=exit_at, initial_status=initial_status,
                        initial_reason=reason, multiplier=case.multiplier,
                        multiplier_verified=case.multiplier_verified,
                        deliverables_verified=case.deliverables_verified,
                        executable_inference_verified=False,
                        inference_basis='Quoted-price diagnostic; quote event age and deliverables require validation',
                        fee_per_contract_action=FEE_PER_CONTRACT_ACTION,
                        slippage_per_share=slippage, cost_units='USD per share and USD per contract-action',
                        cost_basis='Primary 0.01 timestamps; 0.02 is cost stress at fixed timestamps',
                        pnl_net=0. if status == 'rejected' else np.nan,
                        cover_at_conversion_pnl=0. if status == 'rejected' else np.nan,
                        incremental_vs_conversion_cover=0. if status == 'rejected' else np.nan,
                        cover_at_conversion_status=('no_entry_zero_policy' if status == 'rejected'
                                                    else 'not_applicable'),
                        executed_actions=0, reserved_actions=0,
                    )
                    if pd.notna(opened) and opened in minutes.index:
                        entry = minutes.loc[opened]
                        for leg in ('far', 'near'):
                            for name in ('bid', 'ask', 'bid_size', 'ask_size', 'bid_condition',
                                         'ask_condition', 'delta', 'underlying_price'):
                                row[f'entry_{leg}_{name}'] = _number(entry, f'{leg}_{name}')
                        observed = dict(far=_observations(entry, 'far', case.far_strike),
                                        near=_observations(entry, 'near', case.near_strike))
                        row['entry_quote_observations'] = json.dumps(observed)
                        row['entry_far_otm_pct'] = observed['far']['otm_pct']
                    if status == 'valid':
                        row.update(purchase)
                        row.update(_account(case, minutes, opened, exit_at, purchase, slippage))
                    rows.append(row)
    table = pd.DataFrame(rows)
    keys = ['entry_policy', 'holding_sessions', 'slippage_per_share']
    for method in ('immediate_spread', 'short_only'):
        controls = table.loc[table.method.eq(method), [*keys, 'pnl_net']]
        controls = controls.rename(columns={'pnl_net': f'{method}_pnl'})
        table = table.merge(controls, on=keys, how='left', validate='many_to_one')
        table[f'incremental_vs_{method}'] = table.pnl_net - table[f'{method}_pnl']
    return table

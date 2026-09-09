"""Guard frozen call identities, causal orders, financing and conservative accounting."""

from dataclasses import replace
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pandar_hypothesis_replay import FrozenCase, replay_case

ZONE = 'America/New_York'
SESSIONS = ('2026-06-12', '2026-06-15', '2026-06-16', '2026-06-17', '2026-06-18')


def inputs() -> tuple[FrozenCase, pd.DataFrame, pd.DataFrame]:
    case = FrozenCase(ticker='AAA', signal_date='2026-06-11', entry_date=SESSIONS[0],
                      expiry='2026-06-26', far_strike=120., near_strike=115.,
                      exchange_sessions=SESSIONS,
                      earnings_status_by_date=dict.fromkeys(SESSIONS, 'clear'))
    timestamps = pd.DatetimeIndex([])
    for day in SESSIONS:
        daily = pd.date_range(f'{day} 09:30', f'{day} 16:00', freq='min', tz=ZONE)
        timestamps = daily if timestamps.empty else timestamps.append(daily)
    minutes = pd.DataFrame(index=timestamps)
    for leg in ('far', 'near'):
        minutes[f'{leg}_bid'] = .29 if leg == 'far' else .39
        minutes[f'{leg}_ask'] = .31 if leg == 'far' else .41
        minutes[f'{leg}_bid_size'] = 2
        minutes[f'{leg}_ask_size'] = 2
        minutes[f'{leg}_bid_condition'] = 0
        minutes[f'{leg}_ask_condition'] = 50
        minutes[f'{leg}_delta'] = .05 if leg == 'far' else .10
        minutes[f'{leg}_underlying_price'] = 100.
    purchase = pd.Timestamp(f'{SESSIONS[0]} 10:03', tz=ZONE)
    minutes.loc[purchase:, ['near_bid', 'near_ask']] = [.19, .21]
    hiro = pd.DataFrame(dict(event_at=pd.date_range(f'{SESSIONS[0]} 10:00',
                                                   f'{SESSIONS[0]} 14:30', freq='5min', tz=ZONE)))
    hiro['info_cutoff'] = hiro.event_at
    hiro['action_at'] = hiro.event_at + pd.Timedelta(minutes=1)
    hiro['data_status'] = 'available'
    hiro['series_group'] = 'all'
    hiro['trigger'] = False
    hiro.loc[0, 'trigger'] = True
    return case, minutes, hiro


def result(table: pd.DataFrame, method: str = 'deferred_d0', *, policy: str = 'clock',
           slippage: float = .01, horizon: int = 4) -> pd.Series:
    return table.loc[table.method.eq(method) & table.entry_policy.eq(policy)
                     & table.slippage_per_share.eq(slippage)
                     & table.holding_sessions.eq(horizon)].iloc[0]


def test_financing_includes_sale_purchase_fees_and_fixed_stress_times() -> None:
    case, minutes, hiro = inputs()
    table = replay_case(case, minutes, hiro)
    assert len(table) == 40
    base = result(table)
    stress = result(table, slippage=.02)
    assert base.conversion_at == pd.Timestamp(f'{SESSIONS[0]} 10:03', tz=ZONE)
    assert stress.conversion_at == base.conversion_at
    assert base.financing_cash == pytest.approx(4.70)
    assert base.pnl_net == pytest.approx(-10.60)
    assert stress.pnl_net == pytest.approx(base.pnl_net - 4.)
    assert base.cover_at_conversion_pnl == pytest.approx(-5.30)
    assert base.incremental_vs_conversion_cover == pytest.approx(-5.30)
    assert base.incremental_vs_short_only == pytest.approx(-5.30)
    assert not base.executable_inference_verified
    assert not base.multiplier_verified


def test_narrow_credit_cannot_finance_two_opening_action_costs() -> None:
    case, minutes, hiro = inputs()
    minutes.loc[:, ['near_bid', 'near_ask']] = [.24, .26]
    row = result(replay_case(case, minutes, hiro))
    assert row.completion_status == 'known_no_purchase'
    assert pd.isna(row.conversion_at)
    assert row.pnl_net == pytest.approx(-5.30)
    assert row.cover_at_conversion_status == 'no_conversion_final_cover_fallback'
    assert row.cover_at_conversion_pnl == pytest.approx(-5.30)
    assert row.incremental_vs_conversion_cover == 0.


def test_first_hiro_quote_failure_does_not_search_later_trigger() -> None:
    case, minutes, hiro = inputs()
    hiro.loc[1, 'trigger'] = True
    minutes.loc[pd.Timestamp(f'{SESSIONS[0]} 10:01', tz=ZONE), 'far_bid'] = .19
    row = result(replay_case(case, minutes, hiro), policy='hiro')
    assert row.initial_status == 'known_no_entry'
    assert row.pnl_net == 0.
    assert 'far_minimum_bid' in row.initial_reason
    assert row.entry_far_bid == .19
    assert row.cover_at_conversion_pnl == 0.
    assert row.incremental_vs_conversion_cover == 0.


def test_missing_entry_quote_and_earlier_hiro_window_are_censored() -> None:
    case, minutes, hiro = inputs()
    missing = minutes.drop(pd.Timestamp(f'{SESSIONS[0]} 10:01', tz=ZONE))
    row = result(replay_case(case, missing, hiro))
    assert row.initial_status == 'censored_entry'
    assert pd.isna(row.pnl_net)
    hiro.loc[0, ['data_status', 'trigger']] = ['unavailable', False]
    hiro.loc[1, 'trigger'] = True
    row = result(replay_case(case, minutes, hiro), policy='hiro')
    assert row.initial_status == 'censored_entry'
    assert 'earlier_hiro' in row.initial_reason


def test_missing_purchase_minute_does_not_create_false_first_financing() -> None:
    case, minutes, hiro = inputs()
    minutes = minutes.drop(pd.Timestamp(f'{SESSIONS[0]} 10:02', tz=ZONE))
    row = result(replay_case(case, minutes, hiro))
    assert row.completion_status == 'censored_purchase_path'
    assert pd.isna(row.pnl_net)
    assert row.observed_financing_at == pd.Timestamp(f'{SESSIONS[0]} 10:03', tz=ZONE)
    assert pd.isna(row.cover_at_conversion_pnl)
    assert pd.isna(row.naked_short_wall_minutes)
    assert row.short_phase_is_counterfactual


def test_nearer_call_must_still_be_otm_at_purchase() -> None:
    case, minutes, hiro = inputs()
    minutes.loc[pd.Timestamp(f'{SESSIONS[0]} 10:03', tz=ZONE), 'near_underlying_price'] = 116.
    row = result(replay_case(case, minutes, hiro))
    assert row.conversion_at == pd.Timestamp(f'{SESSIONS[0]} 10:04', tz=ZONE)
    assert 'near_not_otm' in row.purchase_rejections
    rejections = json.loads(row.purchase_rejection_observations)
    observed_itm = [r for r in rejections if 'near_not_otm' in r['reason']][0]
    assert observed_itm['underlying_price'] == 116.
    assert observed_itm['otm_pct'] < 0
    assert row.purchase_delta == .10
    assert row.purchase_otm_pct == pytest.approx(15.)


def test_purchase_earnings_recheck_and_unchanged_final_deadline() -> None:
    case, minutes, hiro = inputs()
    case = replace(case, earnings_status_by_date={**case.earnings_status_by_date,
                                                SESSIONS[1]: 'event_in_next_30_days'})
    table = replay_case(case, minutes, hiro)
    deferred = result(table, method='deferred_d1')
    assert deferred.completion_status == 'known_no_purchase'
    assert 'earnings_event' in deferred.purchase_rejections
    assert deferred.exit_at == result(table).exit_at == pd.Timestamp(f'{SESSIONS[3]} 15:50', tz=ZONE)


def test_zero_bid_long_is_marked_with_reserves_not_falsely_sold() -> None:
    case, minutes, hiro = inputs()
    close = pd.Timestamp(f'{SESSIONS[3]} 15:50', tz=ZONE)
    minutes.loc[close, ['near_bid', 'near_bid_size']] = [0., 0]
    row = result(replay_case(case, minutes, hiro))
    assert row.exit_status == 'zero_bid_long_mark'
    assert not row.long_close_executed
    assert row.executed_actions == 3
    assert row.reserved_actions == 1
    assert row.fee_reserve == .65
    assert row.slippage_reserve == 1.
    assert row.pnl_net == pytest.approx(-29.60)


@pytest.mark.parametrize('field,value,reason', [
    ('far_delta', .019, 'far_delta_outside_2_10'),
    ('far_underlying_price', 121., 'far_not_otm'),
    ('near_bid', .10, 'near_spread'),
    ('far_bid_condition', 10, 'far_quote_condition'),
    ('near_ask_size', 0, 'near_action_size'),
])
def test_observed_initial_gate_failures_are_zero_policy_pnl(field: str, value: float,
                                                          reason: str) -> None:
    case, minutes, hiro = inputs()
    minutes.loc[pd.Timestamp(f'{SESSIONS[0]} 10:01', tz=ZONE), field] = value
    row = result(replay_case(case, minutes, hiro))
    assert row.initial_status == 'known_no_entry'
    assert row.pnl_net == 0.
    assert reason in row.initial_reason


def test_future_underlying_timestamp_cannot_supply_entry_greek() -> None:
    case, minutes, hiro = inputs()
    minutes['far_underlying_timestamp'] = minutes.index + pd.Timedelta(minutes=1)
    row = result(replay_case(case, minutes, hiro))
    assert row.initial_status == 'censored_entry'
    assert 'future_underlying_timestamp' in row.initial_reason


def test_expiry_caps_both_horizons_and_future_cutoff_is_censored() -> None:
    case, minutes, hiro = inputs()
    case = replace(case, expiry=SESSIONS[2])
    table = replay_case(case, minutes, hiro)
    assert result(table).exit_at == result(table, horizon=5).exit_at
    assert result(table).exit_at == pd.Timestamp(f'{SESSIONS[2]} 15:50', tz=ZONE)
    case = replace(case, observation_cutoff=pd.Timestamp(f'{SESSIONS[1]} 16:00', tz=ZONE))
    row = result(replay_case(case, minutes, hiro))
    assert row.exit_status == 'future_deadline'
    assert pd.isna(row.pnl_net)


def test_cutoff_prevents_future_exposure_values_from_leaking_into_diagnostics() -> None:
    case, minutes, hiro = inputs()
    cutoff = pd.Timestamp(f'{SESSIONS[1]} 16:00', tz=ZONE)
    case = replace(case, observation_cutoff=cutoff)
    minutes.loc[minutes.index > cutoff, 'far_underlying_price'] = 10000.
    row = result(replay_case(case, minutes, hiro), method='short_only')
    assert row.exit_status == 'future_deadline'
    assert row.largest_observed_underlying_rally_pct == 0.
    assert row.short_phase_observed_minutes <= row.short_phase_expected_minutes


def test_known_no_hiro_trigger_is_distinct_from_missing_data() -> None:
    case, minutes, hiro = inputs()
    hiro['trigger'] = False
    row = result(replay_case(case, minutes, hiro), policy='hiro')
    assert row.initial_status == 'known_no_entry'
    assert row.initial_reason == 'known_no_hiro_trigger'
    assert row.pnl_net == 0.
    row = result(replay_case(case, minutes, hiro.iloc[:-1]), policy='hiro')
    assert row.initial_status == 'censored_entry'
    assert pd.isna(row.pnl_net)


def test_minute_index_requires_timezone_and_unique_frozen_rows() -> None:
    case, minutes, hiro = inputs()
    with pytest.raises(ValueError, match='timezone'):
        replay_case(case, minutes.tz_localize(None), hiro)
    with pytest.raises(ValueError, match='duplicate'):
        replay_case(case, pd.concat([minutes, minutes.iloc[[0]]]), hiro)


def test_known_expiry_cap_does_not_require_unneeded_later_calendar_dates() -> None:
    case, minutes, hiro = inputs()
    case = replace(case, expiry=SESSIONS[2], exchange_sessions=SESSIONS[:3])
    row = result(replay_case(case, minutes, hiro))
    assert row.exit_at == pd.Timestamp(f'{SESSIONS[2]} 15:50', tz=ZONE)
    assert row.exit_status == 'quoted_spread_close'


def test_other_ticker_hiro_cannot_authorize_this_case() -> None:
    case, minutes, hiro = inputs()
    hiro['ticker'] = 'BBB'
    row = result(replay_case(case, minutes, hiro), policy='hiro')
    assert row.initial_status == 'censored_entry'
    assert row.initial_reason == 'hiro_decisions_missing'


def test_predeclared_variant_bounds_do_not_reselect_contracts() -> None:
    case, minutes, hiro = inputs()
    minutes['far_delta'] = .12
    assert result(replay_case(case, minutes, hiro)).initial_status == 'known_no_entry'
    variant = replace(case, variant='delta_5_15_otm5', far_delta_min=.05,
                      far_delta_max=.15, far_otm_min_pct=5.)
    row = result(replay_case(variant, minutes, hiro))
    assert row.initial_status == 'entered'
    assert row.variant == 'delta_5_15_otm5'
    assert row.far_strike == case.far_strike
    assert row.near_strike == case.near_strike
    minutes['far_underlying_price'] = 118.
    row = result(replay_case(variant, minutes, hiro))
    assert row.initial_status == 'known_no_entry'
    assert 'far_otm_below_5pct' in row.initial_reason


def test_future_invalid_greek_is_unknown_not_a_known_rejection() -> None:
    case, minutes, hiro = inputs()
    minutes['far_delta'] = .01
    minutes['far_underlying_timestamp'] = minutes.index + pd.Timedelta(minutes=1)
    row = result(replay_case(case, minutes, hiro))
    assert row.initial_status == 'censored_entry'
    assert pd.isna(row.pnl_net)


def test_future_low_bid_cannot_establish_a_known_failed_entry() -> None:
    case, minutes, hiro = inputs()
    minutes['far_bid'] = .19
    minutes['far_quote_timestamp'] = minutes.index + pd.Timedelta(minutes=1)
    row = result(replay_case(case, minutes, hiro))
    assert row.initial_status == 'censored_entry'
    assert pd.isna(row.pnl_net)


def test_future_unaffordable_ask_does_not_hide_a_missing_purchase_minute() -> None:
    case, minutes, hiro = inputs()
    minutes['near_quote_timestamp'] = minutes.index
    timestamp = pd.Timestamp(f'{SESSIONS[0]} 10:02', tz=ZONE)
    minutes.loc[timestamp, 'near_quote_timestamp'] = timestamp + pd.Timedelta(minutes=1)
    row = result(replay_case(case, minutes, hiro))
    assert row.completion_status == 'censored_purchase_path'
    assert pd.isna(row.pnl_net)


def test_future_stock_and_delta_do_not_contaminate_short_phase_extremes() -> None:
    case, minutes, hiro = inputs()
    minutes['far_underlying_timestamp'] = minutes.index
    timestamp = pd.Timestamp(f'{SESSIONS[0]} 10:02', tz=ZONE)
    minutes.loc[timestamp, 'far_underlying_timestamp'] = timestamp + pd.Timedelta(minutes=1)
    minutes.loc[timestamp, ['far_delta', 'far_underlying_price']] = [.99, 10000.]
    row = result(replay_case(case, minutes, hiro))
    assert row.peak_observed_far_delta == .05
    assert row.largest_observed_underlying_rally_pct == 0.


def test_immediate_control_cannot_silently_become_short_only_when_nearer_is_itm() -> None:
    case, minutes, hiro = inputs()
    minutes[['far_underlying_price', 'near_underlying_price']] = 116.
    table = replay_case(case, minutes, hiro)
    immediate = result(table, method='immediate_spread')
    assert immediate.completion_status == 'immediate_spread_unavailable'
    assert pd.isna(immediate.pnl_net)
    assert result(table).completion_status == 'known_no_purchase'
    assert pd.isna(result(table).incremental_vs_immediate_spread)


def test_missing_nearer_greek_keeps_immediate_control_unavailable() -> None:
    case, minutes, hiro = inputs()
    minutes['near_delta'] = float('nan')
    immediate = result(replay_case(case, minutes, hiro), method='immediate_spread')
    assert immediate.completion_status == 'immediate_spread_unavailable'
    assert pd.isna(immediate.pnl_net)


def test_required_missing_event_history_is_unavailable_even_with_low_sample_bid() -> None:
    case, minutes, hiro = inputs()
    case = replace(case, require_event_age=True)
    minutes['far_bid'] = .19
    row = result(replay_case(case, minutes, hiro))
    assert row.initial_status == 'censored_entry'
    assert 'event_timestamp_missing' in row.initial_reason
    assert pd.isna(row.pnl_net)


def test_age_gate_selects_first_fresh_purchase_and_accepts_exactly_five_seconds() -> None:
    case, minutes, hiro = inputs()
    case = replace(case, require_event_age=True)
    for leg in ('far', 'near'):
        minutes[f'{leg}_quote_timestamp'] = minutes.index - pd.Timedelta(seconds=5)
    stale = pd.Timestamp(f'{SESSIONS[0]} 10:03', tz=ZONE)
    minutes.loc[stale, 'near_quote_timestamp'] = stale - pd.Timedelta(seconds=6)
    row = result(replay_case(case, minutes, hiro))
    assert row.initial_status == 'entered'
    assert row.conversion_at == pd.Timestamp(f'{SESSIONS[0]} 10:04', tz=ZONE)
    assert 'stale_quote_age' in row.purchase_rejections
    assert row.quote_event_age_verified
    assert json.loads(row.purchase_observations)['quote_age_seconds'] == 5.


def test_supplied_stale_event_is_rejected_even_without_required_age_mode() -> None:
    case, minutes, hiro = inputs()
    minutes['far_quote_timestamp'] = minutes.index - pd.Timedelta(seconds=6)
    row = result(replay_case(case, minutes, hiro))
    assert row.initial_status == 'known_no_entry'
    assert 'far_stale_quote_age' in row.initial_reason
    assert row.pnl_net == 0.


def test_required_event_gap_cannot_be_hidden_by_an_unaffordable_interval_ask() -> None:
    case, minutes, hiro = inputs()
    case = replace(case, require_event_age=True)
    for leg in ('far', 'near'):
        minutes[f'{leg}_quote_timestamp'] = minutes.index
    missing = pd.Timestamp(f'{SESSIONS[0]} 10:02', tz=ZONE)
    minutes.loc[missing, 'near_quote_timestamp'] = pd.NaT
    row = result(replay_case(case, minutes, hiro))
    assert row.completion_status == 'censored_purchase_path'
    assert pd.isna(row.pnl_net)

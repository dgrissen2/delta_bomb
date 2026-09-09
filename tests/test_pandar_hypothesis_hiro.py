"""Protect causal call-flow decisions and explicitly unavailable archive windows."""

from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pandar_hypothesis_hiro import (
    build_trigger_table, capture_provenance, session_decisions, summarize_candidates,
)


ZONE = 'America/New_York'
DAY = '2026-06-12'


def archive() -> pd.DataFrame:
    """Observed five-second samples with a rollover and price break at 10:00."""
    ts = pd.date_range(f'{DAY} 09:30', f'{DAY} 14:30', freq='5s', tz=ZONE)
    cutoff = pd.Timestamp(f'{DAY} 09:45', tz=ZONE)
    flow = np.where(ts <= cutoff, 2., -1.)
    price = np.where(ts >= pd.Timestamp(f'{DAY} 10:00', tz=ZONE), 99., 100.)
    return pd.DataFrame(dict(series_group='all', utc_iso=ts.tz_convert('UTC').astype(str),
                             delta_call=flow, delta_put=0., delta_total=flow,
                             stock_price=price, row_count=2))


def first_decision(frame: pd.DataFrame) -> pd.Series:
    return session_decisions(frame, 'AAA', DAY).iloc[0]


def test_window_boundaries_and_next_minute_are_exact() -> None:
    decisions = session_decisions(archive(), 'AAA', DAY)
    row = decisions.iloc[0]
    assert len(decisions) == 55
    assert row.trigger
    assert row.prior_call_flow == 360.
    assert row.current_call_flow == -180.
    assert row.prior_samples == row.current_samples == 180
    assert row.prior_price_low == 100.
    assert row.stock_price == 99.
    assert row.event_at == row.info_cutoff == pd.Timestamp(f'{DAY} 10:00', tz=ZONE)
    assert row.action_at == pd.Timestamp(f'{DAY} 10:01', tz=ZONE)
    assert decisions.iloc[-1].event_at == pd.Timestamp(f'{DAY} 14:30', tz=ZONE)


def test_one_missing_subminute_sample_is_unavailable_without_filling() -> None:
    frame = archive().drop(index=5)
    row = first_decision(frame)
    assert not row.trigger
    assert row.data_status == 'unavailable'
    assert 'missing_5s_slots' in row.reason
    assert row.prior_samples == 179
    assert row.max_gap_seconds == 10.
    assert pd.isna(row.prior_call_flow)


def test_future_mutation_does_not_change_earlier_decisions() -> None:
    frame = archive()
    before = first_decision(frame)
    future = pd.to_datetime(frame.utc_iso, utc=True) > pd.Timestamp(f'{DAY} 10:00', tz=ZONE)
    frame.loc[future, ['delta_call', 'stock_price']] = np.nan
    pd.testing.assert_series_equal(before, first_decision(frame))


def test_expiry_scope_is_never_substituted_or_added() -> None:
    all_frame = archive()
    next_frame = all_frame.assign(series_group='nextExp', delta_call=1e9)
    expected = first_decision(all_frame)
    pd.testing.assert_series_equal(expected, first_decision(pd.concat([next_frame, all_frame])))
    row = first_decision(next_frame)
    assert row.reason == 'all_trades_unavailable'
    assert not row.trigger


@pytest.mark.parametrize('field,value,reason', [
    ('delta_call', np.nan, 'invalid_flow_or_price'),
    ('stock_price', 0., 'invalid_flow_or_price'),
    ('row_count', 0., 'invalid_flow_or_price'),
    ('delta_total', 99999., 'flow_identity_mismatch'),
])
def test_bad_source_values_never_become_zero_flow(field: str, value: float, reason: str) -> None:
    frame = archive()
    frame.loc[5, field] = value
    row = first_decision(frame)
    assert not row.trigger
    assert reason in row.reason


def test_duplicate_and_off_grid_points_remain_unavailable() -> None:
    frame = archive()
    row = first_decision(pd.concat([frame, frame.iloc[[5]]]))
    assert 'duplicate_timestamps' in row.reason
    frame.loc[5, 'utc_iso'] = str(pd.Timestamp(frame.loc[5, 'utc_iso']) + pd.Timedelta(seconds=1))
    assert 'off_grid_timestamps' in first_decision(frame).reason


def test_prior_low_uses_fifteen_completed_minute_prices() -> None:
    frame = archive()
    # An intraminute low is not the existing rule's minute closing-price low.
    frame.loc[frame.utc_iso.eq(str(pd.Timestamp(f'{DAY} 09:55:05', tz=ZONE).tz_convert('UTC'))),
              'stock_price'] = 95.
    assert first_decision(frame).trigger


def test_other_session_cannot_fill_missing_current_session() -> None:
    frame = archive()
    frame['utc_iso'] = (pd.to_datetime(frame.utc_iso, utc=True) - pd.Timedelta(days=1)).astype(str)
    assert first_decision(frame).reason == 'session_rth_unavailable'


def test_missing_archive_is_kept_and_candidate_join_is_explicit(tmp_path: Path) -> None:
    path = tmp_path / 'archive.csv'
    archive().to_csv(path, index=False)
    coverage = pd.DataFrame([dict(ticker='AAA', session_date=DAY, source_path=str(path))])
    requests = pd.DataFrame([dict(ticker='AAA', session_date=DAY),
                             dict(ticker='BBB', session_date=DAY)])
    decisions = build_trigger_table(coverage, requests)
    assert len(decisions) == 110
    assert decisions.loc[decisions.ticker.eq('BBB'), 'reason'].eq('archive_missing').all()
    assert decisions.loc[decisions.ticker.eq('AAA'), 'source_sha256'].str.len().eq(64).all()
    candidates = pd.DataFrame([dict(ticker='AAA', tradeDate='2026-06-11', entry_date=DAY),
                               dict(ticker='BBB', tradeDate='2026-06-11', entry_date=DAY)])
    summary = summarize_candidates(candidates, decisions)
    assert summary.iloc[0].trigger_count == 1
    assert summary.iloc[1].valid_decisions == 0
    assert summary.iloc[1].hiro_status == 'unavailable'
    assert 'selected' not in summary  # HIRO gaps cannot disqualify clock control.


def test_signal_close_cannot_authorize_earlier_same_day_entry() -> None:
    candidates = pd.DataFrame([dict(ticker='AAA', tradeDate=DAY, entry_date=DAY)])
    with pytest.raises(ValueError, match='after.*EOD'):
        summarize_candidates(candidates, session_decisions(archive(), 'AAA', DAY))


def test_first_observed_trigger_does_not_erase_earlier_gaps() -> None:
    frame = archive().drop(index=5)
    times = pd.to_datetime(frame.utc_iso, utc=True)
    frame['delta_call'] = np.where(times <= pd.Timestamp(f'{DAY} 09:55', tz=ZONE), 2., -1.)
    frame['delta_total'] = frame.delta_call
    frame['stock_price'] = np.where(times >= pd.Timestamp(f'{DAY} 10:10', tz=ZONE), 99., 100.)
    candidates = pd.DataFrame([dict(ticker='AAA', tradeDate='2026-06-11', entry_date=DAY)])
    summary = summarize_candidates(candidates, session_decisions(frame, 'AAA', DAY)).iloc[0]
    assert summary.trigger_count == 1
    assert summary.earlier_unavailable_decisions == 1
    assert not summary.first_trigger_history_complete


def test_complete_capture_matches_original_minute_rule() -> None:
    from pandar_leg_timing import features

    source = archive()
    source.index = pd.DatetimeIndex(pd.to_datetime(source.utc_iso, utc=True)).tz_convert(ZONE)
    delta = source[['delta_call', 'delta_put', 'delta_total']].resample(
        '1min', closed='right', label='right').sum(min_count=1)
    prices = source.stock_price.resample('1min', closed='right', label='right').last()
    original = features(delta.assign(stock_price=prices))
    decisions = session_decisions(source, 'AAA', DAY)
    assert decisions.data_status.eq('available').all()
    assert decisions.trigger.tolist() == original.loc[decisions.event_at, 'call_exhaustion'].tolist()


def test_empty_requests_remain_a_valid_empty_diagnostic() -> None:
    candidates = pd.DataFrame(columns=['ticker', 'tradeDate', 'entry_date'])
    assert summarize_candidates(candidates, pd.DataFrame()).empty


def test_relative_capture_path_preserves_capture_warning(tmp_path: Path) -> None:
    path = tmp_path / 'normalized/archive.csv'
    path.parent.mkdir()
    archive().to_csv(path, index=False)
    timestamp = '2026-06-18T10:31:44+00:00'
    (tmp_path / 'manifest.json').write_text(json.dumps(dict(captures=[dict(
        ticker='AAA', ok=False, files=dict(series_csv='normalized/archive.csv'),
        summary=dict(capture_utc=timestamp, error='other endpoint missing'),
    )])))
    provenance = capture_provenance(path, 'AAA', DAY)
    assert provenance['captured_at_utc'] == timestamp
    assert provenance['capture_warning'] == 'other endpoint missing'
    assert not provenance['receipt_time_verified']


def test_summary_only_capture_metadata_has_its_own_hash(tmp_path: Path) -> None:
    path = tmp_path / 'normalized/archive.csv'
    path.parent.mkdir()
    archive().to_csv(path, index=False)
    timestamp = '2026-06-18T10:31:44+00:00'
    pd.DataFrame([dict(ticker='AAA', capture_utc=timestamp, error='')]).to_csv(
        tmp_path / 'summary.csv', index=False)
    provenance = capture_provenance(path, 'AAA', DAY)
    assert provenance['captured_at_utc'] == timestamp
    assert provenance['capture_time_basis'] == 'summary_csv'
    assert len(provenance['capture_metadata_sha256']) == 64

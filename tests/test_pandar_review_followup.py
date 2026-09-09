"""Causal financing, earnings boundaries, and executable-close regression checks."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pandar_review_followup import earnings_gate, replay, session_deadline


def quotes(rows):
    return pd.DataFrame(rows, columns=['timestamp', 'bid', 'ask', 'bid_size', 'ask_size']).assign(
        timestamp=lambda f: pd.to_datetime(f.timestamp).dt.tz_localize('America/New_York')
    ).set_index('timestamp')


def test_earnings_day30_excluded_day31_clear_and_unknown_not_clear():
    assert earnings_gate('2026-08-20', '2026-09-19', '2026-08-20') == 'exclude_earnings_30d'
    assert earnings_gate('2026-08-20', '2026-09-20', '2026-08-20') == 'clear'
    assert earnings_gate('2026-08-20', '0000-00-00', '2026-08-20') == 'unknown'
    assert earnings_gate('2026-08-20', '2026-09-20', '2026-08-21') == 'unknown'
    assert earnings_gate('2026-08-20', '2026-08-19', '2026-08-20') == 'unknown'


def test_deadline_counts_entry_and_holiday_and_caps_at_expiry():
    assert session_deadline('2026-09-03', '2026-09-30', 4) == '2026-09-09'
    assert session_deadline('2026-08-27', '2026-08-31', 5) == '2026-08-31'


def test_first_valid_later_ask_is_used_and_round_trip_fees_counted():
    row = dict(ticker='TEST', tradeDate='2026-08-20', expiry='2026-08-28',
               strike=150., nearer_strike=145.)
    first = quotes([['2026-08-21 10:01', .60, .70, 1, 1],
                    ['2026-08-26 15:50', .01, .02, 1, 1]])
    second = quotes([['2026-08-21 10:01', .20, .30, 1, 1],
                     ['2026-08-21 10:02', .20, .30, 1, 0],
                     ['2026-08-21 10:03', .35, .40, 1, 1],
                     ['2026-08-21 10:04', .05, .10, 1, 1],
                     ['2026-08-26 15:50', .03, .05, 1, 1]])
    result = replay(row, first, second, 4)
    assert result['leg2_time'].endswith('10:03:00-04:00')
    assert abs(result['pnl_net'] - 18.4) < 1e-8
    assert result['status'] == 'completed_closed'


def test_zero_bid_long_is_not_called_fully_closed():
    row = dict(ticker='TEST', tradeDate='2026-08-20', expiry='2026-08-28',
               strike=150., nearer_strike=145.)
    first = quotes([['2026-08-21 10:01', .60, .70, 1, 1],
                    ['2026-08-26 15:50', .00, .01, 0, 1]])
    second = quotes([['2026-08-21 10:01', .70, .80, 1, 1],
                     ['2026-08-21 10:02', .35, .40, 1, 1],
                     ['2026-08-26 15:50', .00, .01, 0, 1]])
    result = replay(row, first, second, 4)
    assert result['status'] == 'completed_zero_bid_long_mark'
    assert result['fully_closed'] is False


def test_future_deadline_is_censored_even_with_available_mark():
    row = dict(ticker='TEST', tradeDate='2026-09-02', expiry='2026-09-09',
               strike=410., nearer_strike=405.)
    first = quotes([['2026-09-03 10:01', .60, .70, 1, 1]])
    second = quotes([['2026-09-03 10:01', .70, .80, 1, 1]])
    result = replay(row, first, second, 4)
    assert result['status'] == 'deadline_censored'
    assert 'pnl_net' not in result


def test_missing_deadline_quote_does_not_become_zero_pnl():
    row = dict(ticker='TEST', tradeDate='2026-08-20', expiry='2026-08-28',
               strike=150., nearer_strike=145.)
    first = quotes([['2026-08-21 10:01', .60, .70, 1, 1]])
    second = quotes([['2026-08-21 10:01', .70, .80, 1, 1]])
    result = replay(row, first, second, 4)
    assert result['status'] == 'exit_unpriced'
    assert 'pnl_net' not in result

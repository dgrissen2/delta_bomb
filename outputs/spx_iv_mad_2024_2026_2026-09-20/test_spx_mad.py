"""Boundary tests for the SPX transfer, retaining the established calculation."""
from datetime import date

import numpy as np
import pandas as pd

import spx_mad as p


def test_full_target_calendar_and_pre2024_warmup():
    sessions, targets = p.date_plan()
    assert len(targets) == 681 and len(sessions) == 741
    assert targets[0] == '2024-01-02' and targets[-1] == '2026-09-18'
    assert sessions[:60][0] == '2023-10-05' and sessions[59] == '2023-12-29'
    assert set(['2023-11-23', '2023-12-25', '2025-01-09']).isdisjoint(sessions)
    assert p.magnitude.prior_sessions(sessions, targets[0]) == sessions[:60]


def test_early_closes_and_clock_blocks():
    assert len(p.minute_grid('2023-11-24')) == 210
    assert len(p.minute_grid('2024-07-03')) == 210
    assert len(p.minute_grid('2024-01-02')) == 300
    assert p.minute_grid('2023-11-24')[-1].strftime('%H:%M') == '12:59'


def test_spxw_native_contract_and_unchanged_request_fields():
    params = p.input_params('SPXW', '2024-01-02', '2024-02-02')
    assert params['symbol'] == 'SPXW' and params['date'] == date(2024, 1, 2)
    assert params['strike_range'] == 30 and params['right'] == 'both'
    assert params['rate_type'] == 'sofr' and params['interval'] == '1m'
    assert params['start_time'] == '09:30:00' and params['end_time'] == '14:29:00'
    assert p.SYMBOLS == ['SPXW']


def test_expiry_bracket_keeps_exact_thirty_day_expiry():
    choose = p.legacy.calendar.selected_expiries
    assert choose('2024-01-02', ['2024-01-31', '2024-02-01', '2024-02-02']) == ['2024-02-01']
    assert choose('2024-01-02', ['2024-01-31', '2024-02-02']) == ['2024-01-31', '2024-02-02']
    assert choose('2024-01-02', ['2024-01-03', '2024-04-01']) == []


def test_equal_date_median_not_equal_window_median():
    values = np.array([0.] * 100 + [2.] * 9)
    dates = pd.Series(['busy'] * 100 + [str(i) for i in range(9)])
    assert p.exact.exact_median(values, dates) == 2.


def test_first_2024_baseline_excludes_current_and_later_data():
    sessions, targets = p.date_plan()
    rows = [{'date': d, 'block': 0, 'acceleration': float(i % 7), 'available': True}
            for i, d in enumerate(sessions[:60])]
    history = pd.DataFrame(rows)
    before = p.historical_baseline(history, sessions, targets[0], 0)
    extra = pd.DataFrame([{'date': targets[0], 'block': 0, 'acceleration': 1e9, 'available': True}])
    after = p.historical_baseline(pd.concat([history, extra]), sessions, targets[0], 0)
    assert before == after and before['history_days'] == 60
    assert before['scale'] == 1.4826 * before['mad']


def test_missing_history_stays_unknown():
    sample = pd.DataFrame({'date': [str(i) for i in range(9)],
                           'acceleration': np.arange(9.), 'available': True})
    result = p.exact.baseline(sample)
    assert result['status'] == 'insufficient_history' and np.isnan(result['scale'])

"""Boundary and selection checks for the calendar extension; no outcome tuning."""
import pandas as pd
import pytest

from periods import cohort, coverage_dates, half_year, history_sources


@pytest.mark.parametrize(('day', 'expected'), [
    ('2024-01-02', '2024_H1'), ('2024-06-28', '2024_H1'),
    ('2024-07-01', '2024_H2'), ('2024-12-31', '2024_H2'),
    ('2025-07-01', '2025_H2'), ('2026-09-18', '2026_H2'),
])
def test_half_year_boundaries(day, expected):
    assert half_year(day) == expected


def test_periods_exclude_development_without_losing_zero_event_dates():
    days = pd.DataFrame({'date': ['2024-01-02', '2026-08-12', '2026-08-13'],
                         'cohort': ['new_2024', 'development_10', 'original_50']})
    assert cohort(days, '2026_H2').date.tolist() == ['2026-08-13']
    assert cohort(days, 'combined_non_development').date.tolist() == ['2024-01-02', '2026-08-13']
    assert len(cohort(days, 'all_qualifying')) == 3


def test_coverage_includes_unknown_vt_for_warmup_but_not_short_sessions():
    ledger = pd.DataFrame({'date': ['2024-01-02', '2024-01-03', '2024-07-03', '2025-01-02'],
                           'complete_spx': [False, True, False, False],
                           'early_close': [False, False, True, False]})
    assert coverage_dates(ledger) == ['2024-01-02']


def test_new_complete_native_source_supersedes_partial_history_without_mutating_it():
    old = pd.DataFrame([{'date': '2024-12-30', 'path': '/old', 'sha256': 'a',
                        'included_5m': True, 'included_1m': False}])
    population = pd.DataFrame([{'date': '2024-12-30', 'source_path': '/new',
                               'source_sha256': 'b', 'complete_spx': True}])
    result = history_sources(old, population)
    assert result == [{'date': '2024-12-30', 'path': '/new', 'sha256': 'b'}]
    assert old.iloc[0].path == '/old'


def test_existing_history_and_its_warmup_flags_are_preserved():
    old = pd.DataFrame([{'date': '2023-12-29', 'path': '/old', 'sha256': 'a',
                        'included_5m': True, 'included_1m': False}])
    empty = pd.DataFrame(columns=['date', 'source_path', 'source_sha256', 'complete_spx'])
    assert history_sources(old, empty)[0]['included_in_rsi_warmup'] is False

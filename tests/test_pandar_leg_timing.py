"""Financial and causal invariants for the Pandar historical replay."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pandar_leg_timing import action_price, pnl, features, quote_at, simulate


def test_cash_is_not_spread_liquidation_profit():
    # A ten-cent financed credit can still lose when closing two illiquid tails.
    assert pnl(0.10, -0.20, 4) == pytest.approx(-12.60)


def test_zero_bid_is_mark_only_not_a_sale():
    quote = pd.Series(dict(bid=0.0, ask=0.10, bid_size=0, ask_size=1))
    assert action_price(quote, 'sell') is None
    assert action_price(quote, 'sell', marking=True) == 0
    assert action_price(quote, 'buy') == 0.10
    quote['bid'] = 0.2
    assert action_price(quote, 'buy') is None  # Crossed markets invalid on either side.


def test_no_future_quote_substitution():
    timestamp = pd.Timestamp('2026-08-25 10:01', tz='America/New_York')
    frame = pd.DataFrame([dict(bid=1, ask=2)], index=[timestamp + pd.Timedelta(minutes=1)])
    assert quote_at(frame, timestamp) is None


def test_hiro_features_are_causal_and_keep_put_sign():
    ix = pd.date_range('2026-08-25 09:30', periods=70, freq='min', tz='America/New_York')
    source = pd.DataFrame(dict(delta_total=2.0, delta_call=1.0, delta_put=1.0,
                               stock_price=100.0), index=ix)
    before = features(source.iloc[:40])
    source.loc[ix[40]:, 'delta_put'] = -1e9
    after = features(source)
    pd.testing.assert_series_equal(before.loc[ix[35]], after.loc[ix[35]])
    assert after.loc[ix[35], 'put15'] > 0  # Positive put HIRO is calm-side put selling.
    assert after.loc[ix[35], 'calm_put']


def test_failed_financing_is_closed_and_charged():
    entry = pd.Timestamp('2026-08-25 10:01', tz='America/New_York')
    deadline = pd.Timestamp('2026-08-25 15:50', tz='America/New_York')
    first = pd.DataFrame([dict(bid=.07, ask=.10, bid_size=2, ask_size=2),
                          dict(bid=.03, ask=.05, bid_size=2, ask_size=2)],
                         index=[entry, deadline])
    second = first.assign(bid=.01, ask=.03)
    row = pd.Series(dict(scenario='buy-first put-tail inventory', expiry='2026-09-18'))
    result = simulate(row, (entry, .10, .01, first, second), {}, 'price_finance', 0)
    assert result['status'] == 'aborted_uncompleted'
    assert result['actions'] == 2
    assert result['pnl_net'] == pytest.approx(-8.30)


def test_call_conversion_preserves_short_call_liability():
    entry = pd.Timestamp('2026-08-25 10:01', tz='America/New_York')
    exit_time = pd.Timestamp('2026-08-28 15:50', tz='America/New_York')
    short = pd.DataFrame([dict(bid=.30, ask=.35, bid_size=2, ask_size=2),
                          dict(bid=.02, ask=.04, bid_size=2, ask_size=2)],
                         index=[entry, exit_time])
    long = pd.DataFrame([dict(bid=.40, ask=.45, bid_size=2, ask_size=2),
                         dict(bid=.05, ask=.08, bid_size=2, ask_size=2)],
                        index=[entry, exit_time])
    row = pd.Series(dict(scenario='sell-first call grab', expiry='2026-08-28'))
    result = simulate(row, (entry, .30, .45, short, long), {}, 'simultaneous', 0)
    assert result['pnl_net'] == pytest.approx(-16.60)


def test_source_dime_target_is_stricter_than_fee_covering_target():
    entry = pd.Timestamp('2026-08-25 10:01', tz='America/New_York')
    deadline = pd.Timestamp('2026-08-25 15:50', tz='America/New_York')
    short = pd.DataFrame([dict(bid=.26, ask=.30, bid_size=2, ask_size=2),
                          dict(bid=.18, ask=.20, bid_size=2, ask_size=2)],
                         index=[entry, deadline])
    long = pd.DataFrame([dict(bid=.30, ask=.35, bid_size=2, ask_size=2),
                         dict(bid=.18, ask=.22, bid_size=2, ask_size=2)],
                        index=[entry, deadline])
    row = pd.Series(dict(scenario='sell-first call grab', expiry='2026-08-25'))
    opened = (entry, .26, .35, short, long)
    assert simulate(row, opened, {}, 'price_finance', 0)['paired']
    assert not simulate(row, opened, {}, 'price_finance', 0, financing_target=.10)['paired']

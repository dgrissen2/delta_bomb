"""Boundary tests for a lossless, explicitly recorded IV-superset alignment."""
import pandas as pd
import pytest

from repair_endpoint_superset import align_iv_superset
import spx_mad as p


def rows(strikes: list[int]) -> pd.DataFrame:
    stamp = pd.Timestamp('2026-06-09 10:00', tz='America/New_York')
    return pd.DataFrame([dict(symbol='SPXW', expiration='2026-07-09', strike=k,
                              right='CALL', timestamp=stamp, bid=10., ask=12.,
                              midpoint=11., underlying_price=6500., underlying_timestamp=stamp,
                              bid_implied_vol=.19, implied_vol=.20, ask_implied_vol=.21,
                              iv_error=0., delta=.5) for k in strikes])


def test_keeps_every_greek_key_and_native_iv_value() -> None:
    iv, greek = rows([6400, 6500, 6600]), rows([6500, 6600])
    result = align_iv_superset(iv, greek)
    pd.testing.assert_frame_equal(result, iv.iloc[1:].reset_index(drop=True))
    assert p.legacy.surface._prepare(result, greek).endpoint_match.all()


def test_missing_greek_counterpart_cannot_be_dropped() -> None:
    with pytest.raises(ValueError, match='Greek key lacks'):
        align_iv_superset(rows([6300, 6400, 6500]), rows([6500, 6600]))


@pytest.mark.parametrize('duplicate_side', ['iv', 'greek'])
def test_duplicates_are_rejected(duplicate_side: str) -> None:
    iv, greek = rows([6400, 6500, 6600]), rows([6500, 6600])
    if duplicate_side == 'iv':
        iv = pd.concat([iv, iv.iloc[:1]], ignore_index=True)
    else:
        greek = pd.concat([greek, greek.iloc[:1]], ignore_index=True)
    with pytest.raises(ValueError, match='duplicate'):
        align_iv_superset(iv, greek)


def test_equal_sets_are_not_a_superset_repair() -> None:
    with pytest.raises(ValueError, match='strict IV superset'):
        align_iv_superset(rows([6500]), rows([6500]))


def test_quote_mismatch_remains_rejected_by_unchanged_quality_check() -> None:
    iv, greek = rows([6400, 6500, 6600]), rows([6500, 6600])
    greek.loc[0, 'bid'] = 9.
    result = align_iv_superset(iv, greek)
    prepared = p.legacy.surface._prepare(result, greek)
    assert not prepared.loc[prepared.strike.eq(6500), 'endpoint_match'].item()
    assert not prepared.loc[prepared.strike.eq(6500), 'valid'].item()

"""Regression checks for the independent review's concrete failure cases."""
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import numpy as np
import pytest

from checkpoint import admission
from inputs import normalize_selection


def test_delayed_gate_rejects_missing_prefix_bar() -> None:
    prices = pd.DataFrame({'open':100.,'high':101.,'low':99.,'close':100.},index=range(570,650))
    assert admission(prices,620,90.)
    with pytest.raises(ValueError,match='Missing, duplicate or unordered'):
        admission(prices.drop(index=580),620,90.)


def test_normalize_both_legacy_expiration_meanings() -> None:
    all_expiries = ['2024-01-26','2024-02-16','2024-03-15']
    selected = all_expiries[:2]
    shared = dict(date='2024-01-10',symbol='XLC')
    cached = dict(shared,selection=dict(expirations=selected,listed_expirations=all_expiries))
    fresh = dict(shared,selected=selected,listing=dict(expirations=all_expiries))
    assert normalize_selection(cached) == normalize_selection(fresh)
    missing = dict(shared,selected=[],listing=dict(expirations=['2024-03-15']))
    assert normalize_selection(missing)['selected_expirations'] == []


def test_optimization_cannot_strip_integrity_gates() -> None:
    scope = str(Path(__file__).resolve().parent)
    result = subprocess.run([sys.executable,'-O','-c',f'import sys; sys.path.insert(0,{scope!r}); import inputs'],
                            capture_output=True,text=True)
    assert result.returncode != 0
    assert 'require Python without -O' in result.stderr


def test_feature_freeze_rejects_changed_receipt(tmp_path: Path,monkeypatch) -> None:
    import analyze
    from inputs import digest
    monkeypatch.setattr(analyze,'DATA',tmp_path)
    feature = tmp_path/'sector_features.parquet'
    feature.write_bytes(b'no outcome will be read')
    receipt = tmp_path/'receipt.json'
    receipt.write_text(json.dumps({'output_hashes':{},'native_hashes':{}}))
    (tmp_path/'feature_freeze.json').write_text(json.dumps({'sha256':digest(feature),
        'source_hashes':{str(receipt):'incorrect'},'code_sha256':'irrelevant'}))
    with pytest.raises(ValueError,match='receipt|Frozen feature changed'):
        analyze.load_inputs()


def test_rejected_weight_payload_can_be_revalidated_without_refetch(tmp_path: Path,monkeypatch) -> None:
    import weights
    from inputs import digest
    source = tmp_path/'response.json'
    source.write_text('{}')
    receipt = dict(status='unavailable',http_status=200,sha256=digest(source))
    def repaired_parser(payload,day):
        return None,pd.DataFrame({'symbol':['XLK'],'equity_weight':[1.]}),None
    monkeypatch.setattr(weights.legacy,'parse_holdings',repaired_parser)
    frame,ledger = weights.validate_cached(receipt,source,'2024-01-10','2024-01-09')
    assert ledger['retrieval_status'] == 'retrieved'
    assert ledger['validation_status'] == 'accepted'
    assert frame.date.iloc[0] == '2024-01-10'
    empty = weights.combine_validated([])
    assert empty.empty and {'date','symbol','equity_weight'} <= set(empty.columns)


def test_single_perfect_trade_is_not_reported_with_certain_accuracy() -> None:
    from analyze import rate_interval
    sample = pd.DataFrame({'date':['2024-01-10'],'hit':[1]})
    interval = rate_interval(sample,np.array([100.,100.]))
    assert np.isnan(interval['low']) and np.isnan(interval['high'])

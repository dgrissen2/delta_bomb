"""Failure-path regression checks from the final independent audit."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def test_delta_interval_rejects_single_day_qualifiers() -> None:
    from analyze import difference_interval
    one = pd.DataFrame({'date':['2024-01-02'],'hit':[1]})
    many = pd.DataFrame({'date':['2024-01-02','2024-01-03'],'hit':[1,0]})
    result = difference_interval(one,many,np.array([20.,40.]))
    assert np.isnan(result['low']) and np.isnan(result['high'])


def test_verified_outputs_cannot_be_replaced(tmp_path: Path) -> None:
    from provenance import check_hashes
    path = tmp_path/'comparison.csv'
    path.write_text('changed')
    with pytest.raises(ValueError,match='Changed'):
        check_hashes({str(path):'old'})


def test_orphan_weight_body_is_not_a_retrieved_response(tmp_path: Path) -> None:
    from weights import validate_cached
    source = tmp_path/'old.json'
    source.write_text('{}')
    frame,ledger = validate_cached({'status':'unavailable','reason':'network failure'},
                                  source,'2024-01-03','2024-01-02')
    assert frame is None and ledger['retrieval_status']=='not_retrieved'


def test_expiry_fallback_requires_native_listing_evidence(tmp_path: Path) -> None:
    from inputs import normalize_selection,digest
    path = tmp_path/'contracts.parquet'
    pd.DataFrame({'symbol':['XLC']*3,'expiration':['2024-01-26','2024-02-09','2024-02-16']}).to_parquet(path)
    row = dict(date='2024-01-10',symbol='XLC',selection=dict(
        expirations=['2024-01-26','2024-02-16'],listing_path=str(path),listing_sha256=digest(path)))
    with pytest.raises(ValueError,match='bracket'):
        normalize_selection(row)


def test_frozen_input_digest_checked(tmp_path: Path) -> None:
    from provenance import check_manifest
    source = tmp_path/'source'
    source.write_text('changed')
    manifest = tmp_path/'freeze.json'
    manifest.write_text(json.dumps({'inputs':{str(source):'old'},'output_hashes':{}}))
    with pytest.raises(ValueError,match='Changed'):
        check_manifest(manifest)
